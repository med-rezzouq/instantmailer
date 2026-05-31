from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.campaign import Campaign
from app.models.trackingdomain import TrackingDomain
from app.models.campaigntracking import CampaignTracking
from app.schemas.trackingdomain import (
    TrackingDomainCreate,
    TrackingDomainUpdate,
    TrackingDomainOut,
)

router = APIRouter(prefix="/tracking", tags=["tracking"])


# -------------------------
# Tracking domains CRUD
# -------------------------


@router.get("/domains", response_model=List[TrackingDomainOut])
async def list_tracking_domains(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TrackingDomain)
        .where(TrackingDomain.user_id == current_user.id)
        .order_by(TrackingDomain.id.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/domains",
    response_model=TrackingDomainOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_tracking_domain(
    payload: TrackingDomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_stmt = select(TrackingDomain).where(
        TrackingDomain.domain == str(payload.domain)
    )
    existing_res = await db.execute(existing_stmt)
    existing = existing_res.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking domain already exists",
        )

    domain = TrackingDomain(
        user_id=current_user.id,
        domain=str(payload.domain),
        campaign_ids=None,
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return domain


@router.put("/domains/{domain_id}", response_model=TrackingDomainOut)
async def update_tracking_domain(
    domain_id: int,
    payload: TrackingDomainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain = await db.get(TrackingDomain, domain_id)
    if not domain or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    existing_stmt = select(TrackingDomain).where(
        TrackingDomain.domain == str(payload.domain),
        TrackingDomain.id != domain_id,
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Another tracking domain already uses this URL",
        )

    domain.domain = str(payload.domain)
    await db.commit()
    await db.refresh(domain)
    return domain


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracking_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain = await db.get(TrackingDomain, domain_id)
    if not domain or domain.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    await db.delete(domain)
    await db.commit()
    return None


# -------------------------
# Unified /tracking endpoint
# -------------------------
@router.get("")
async def track(
    request: Request,
    response: Response,
    actiontype: str,
    campaign_id: int,
    contact_id: Optional[int] = None,
    url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    /tracking?actiontype=open&campaign_id=1&contact_id=2
    /tracking?actiontype=click&campaign_id=3&contact_id=5&url=...
    /tracking?actiontype=list&campaign_id=1
    """

    actiontype = actiontype.lower()
    if actiontype not in ("open", "click", "list"):
        raise HTTPException(status_code=400, detail="Invalid actiontype")

    # Check campaign exists
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # LIST mode: used by UI to show all events of a campaign
    if actiontype == "list":
        # If you want to enforce auth but not hide errors:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Optional ownership check
        # if campaign.user_id != current_user.id:
        #     raise HTTPException(status_code=404, detail="Not found")

        stmt = (
            select(CampaignTracking)
            .where(CampaignTracking.campaign_id == campaign_id)
            .order_by(CampaignTracking.id.desc())
        )
        res = await db.execute(stmt)
        events = list(res.scalars().all())
        return events

    # From here: open / click events (no auth required)
    if contact_id is None:
        raise HTTPException(status_code=400, detail="contact_id is required")

    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    country = None  # TODO: integrate GeoIP later

    tracking = CampaignTracking(
        campaign_id=campaign_id,
        contact_id=contact_id,
        action_type=actiontype,
        url=url,
        address_ip=client_host,
        country=country,
        browser=user_agent[:120] if user_agent else None,
    )
    db.add(tracking)

    # Increment counters
    if actiontype == "open":
        stmt = (
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(opens=Campaign.opens + 1)
        )
        await db.execute(stmt)
    elif actiontype == "click":
        stmt = (
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(clicks=Campaign.clicks + 1)
        )
        await db.execute(stmt)

    await db.commit()

    # Response for open/click
    if actiontype == "open":
        pixel = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT"
            b"\x08\xd7c```\x00\x00\x00\x05\x00\x01"
            b"\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return Response(content=pixel, media_type="image/png")
    else:
        return Response(content="OK", media_type="text/plain")
