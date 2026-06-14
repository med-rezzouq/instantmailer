import asyncio
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.contact import Contact, ContactTag, ContactGroup
from app.models.template import EmailTemplate
from app.models.smtp_config import SMTPConfig
from app.models.campaign import Campaign, CampaignStatus, CampaignRecipient, EmailProvider
from app.models.campaign_step import CampaignStep, StepType, DelayFrom, DelayUnit
from app.models.campaign_sender import CampaignSender, SenderType
from app.models.mailbox import Mailbox


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_or_create_mock_mailboxes(session, user_id: int):
    seed_mailboxes = [
        ("google", "warmup1@gmail.com", "Warmup Gmail 1"),
        ("google", "warmup2@gmail.com", "Warmup Gmail 2"),
        ("microsoft", "warmup1@yourtenant.onmicrosoft.com", "Warmup O365 1"),
        ("microsoft", "warmup2@yourtenant.onmicrosoft.com", "Warmup O365 2"),
    ]

    created = []

    for provider, email, display_name in seed_mailboxes:
        result = await session.execute(
            select(Mailbox).where(
                Mailbox.user_id == user_id,
                Mailbox.provider == provider,
                Mailbox.email == email,
            )
        )
        mailbox = result.scalar_one_or_none()
        if mailbox:
            created.append(mailbox)
            continue

        mailbox = Mailbox(
            user_id=user_id,
            provider=provider,
            email=email,
            display_name=display_name,
            access_token="FAKE_ACCESS_TOKEN_FOR_SEEDING",
            refresh_token="FAKE_REFRESH_TOKEN_FOR_SEEDING",
            token_expiry=utc_now_naive() + timedelta(hours=1),
            scope="gmail.modify userinfo.email" if provider == "google" else "Mail.ReadWrite",
            warmup_enabled=True,
            last_sync_at=None,
        )
        session.add(mailbox)
        await session.flush()
        created.append(mailbox)

    return created


async def get_or_create_user(session):
    result = await session.execute(select(User).order_by(User.id))
    user = result.scalars().first()
    if user:
        return user

    user = User(
        email="med.rezzouq@gmail.com",
        name="Dev User",
        hashed_password="$2b$12$7Gdd98iuua/LGPEs0I7wfuGIrSxQ59vBawgYqAwW0E8y7znM3mSne",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_default_group(session, user_id: int) -> ContactGroup:
    result = await session.execute(
        select(ContactGroup).where(
            ContactGroup.user_id == user_id,
            ContactGroup.name == "Default",
        )
    )
    group = result.scalar_one_or_none()
    if group:
        return group

    group = ContactGroup(
        user_id=user_id,
        name="Default",
    )
    session.add(group)
    await session.flush()
    return group


async def get_or_create_tags(session, user_id):
    tags_data = ["Lead", "Customer", "Trial", "VIP"]
    tags = []

    for name in tags_data:
        result = await session.execute(
            select(ContactTag).where(
                ContactTag.user_id == user_id,
                ContactTag.name == name,
            )
        )
        tag = result.scalar_one_or_none()
        if not tag:
            tag = ContactTag(user_id=user_id, name=name)
            session.add(tag)
            await session.flush()
        tags.append(tag)

    return tags


async def get_or_create_contacts(session, user_id, default_group: ContactGroup):
    contacts_data = [
        ("medrezzouq9@gmail.com", "Medrezzouq9", ""),
        ("kora4yo@gmail.com", "Kora4yo", ""),
        ("seriefilm@gmail.com", "Seriefilm", ""),
        ("medelenx@gmail.com", "Medelenx", ""),
    ]

    contacts = []
    for email, first_name, last_name in contacts_data:
        result = await session.execute(
            select(Contact).where(Contact.user_id == user_id, Contact.email == email)
        )
        contact = result.scalar_one_or_none()
        if not contact:
            contact = Contact(
                user_id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_subscribed=True,
                open_count=0,
                click_count=0,
                group_id=default_group.id,
            )
            session.add(contact)
            await session.flush()
        elif getattr(contact, "group_id", None) is None:
            contact.group_id = default_group.id

        contacts.append(contact)

    return contacts


async def get_or_create_template(session, user_id: int):
    result = await session.execute(
        select(EmailTemplate).where(
            EmailTemplate.user_id == user_id,
            EmailTemplate.name == "Welcome Template",
        )
    )
    template = result.scalars().first()
    if template:
        return template

    template = EmailTemplate(
        user_id=user_id,
        name="Welcome Template",
        category="welcome",
        html_content="""
            <p>Hi {{ firstname }},</p>
            <p>Welcome to MailForge! This is a demo template.</p>
        """,
        thumbnail=None,
    )
    session.add(template)
    await session.flush()
    return template


async def get_or_create_smtp_config(session, user_id):
    result = await session.execute(
        select(SMTPConfig).where(SMTPConfig.user_id == user_id)
    )
    smtp_config = result.scalar_one_or_none()
    if smtp_config:
        return smtp_config

    smtp_config = SMTPConfig(
        user_id=user_id,
        name="Demo SMTP",
        host="smtp.example.com",
        port=587,
        username="root",
        password="demo-password",
        use_tls=True,
        use_ssl=False,
        from_email="demo@example.com",
        from_name="Demo User",
        is_active=True,
    )
    session.add(smtp_config)
    await session.flush()
    return smtp_config


async def get_or_create_campaign(session, user, contacts, smtp_config):
    result = await session.execute(
        select(Campaign).where(
            Campaign.user_id == user.id,
            Campaign.name == "Demo Campaign",
        )
    )
    campaign = result.scalar_one_or_none()

    if campaign:
        return campaign

    campaign = Campaign(
        user_id=user.id,
        name="Demo Campaign",
        status=CampaignStatus.draft,
        segment_tags=[],
        from_name="admin",
        reply_to="admin@academicsights.com",
        track_opens=True,
        track_clicks=True,
        is_followup=False,
        total_contacts=len(contacts),
        new_contacts_since_send=0,
        scheduled_at=utc_now_naive() + timedelta(hours=1),
        provider_id=smtp_config.id,
    )
    session.add(campaign)
    await session.flush()

    sender = CampaignSender(
        campaign_id=campaign.id,
        sender_type=SenderType.smtp,
        sender_id=smtp_config.id,
        sender_label=f"{smtp_config.from_name} <{smtp_config.from_email}>",
        quota=len(contacts),
        sent_count=0,
    )
    session.add(sender)

    step = CampaignStep(
        campaign_id=campaign.id,
        step_number=1,
        step_type=StepType.initial,
        name="Initial Outreach",
        subject="Quick introduction",
        html_body="<p>Hello {{first_name}}, just reaching out to introduce MailForge.</p>",
        plain_body="Hello {{first_name}}, just reaching out to introduce MailForge.",
        delay_value=0,
        delay_unit=DelayUnit.days,
        delay_from=DelayFrom.most_recent,
        stop_on_reply=True,
        is_active=True,
    )
    session.add(step)

    for contact in contacts:
        recipient = CampaignRecipient(
            campaign_id=campaign.id,
            contact_id=contact.id,
            status="pending",
            provider=EmailProvider.smtp,
            sent_at=None,
            error=None,
        )
        session.add(recipient)

    await session.flush()
    return campaign


async def main(seed_part: str = "all"):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session)
        default_group = await get_or_create_default_group(session, user.id)

        if seed_part in ("all", "tags"):
            await get_or_create_tags(session, user.id)

        contacts = []
        if seed_part in ("all", "contacts", "campaign"):
            contacts = await get_or_create_contacts(session, user.id, default_group)

        if seed_part in ("all", "template"):
            await get_or_create_template(session, user.id)

        smtp_config = None
        if seed_part in ("all", "smtp", "campaign"):
            smtp_config = await get_or_create_smtp_config(session, user.id)

        if seed_part in ("all", "mailboxes"):
            await get_or_create_mock_mailboxes(session, user.id)

        if seed_part in ("all", "campaign"):
            if not contacts:
                contacts = await get_or_create_contacts(session, user.id, default_group)
            if not smtp_config:
                smtp_config = await get_or_create_smtp_config(session, user.id)

            campaign = await get_or_create_campaign(session, user, contacts, smtp_config)
            print(f"Campaign seed complete. Campaign ID: {campaign.id}")

        await session.commit()
        print(f"Seed complete. Mode: {seed_part}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        choices=["all", "mailboxes", "tags", "contacts", "template", "smtp", "campaign"],
        default="all",
    )
    args = parser.parse_args()
    asyncio.run(main(args.only))