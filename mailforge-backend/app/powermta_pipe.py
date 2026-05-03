#!/usr/bin/env python3
"""
PowerMTA pipes incoming emails to this script.
Config in PowerMTA: command "/usr/bin/python3 /app/powermta_pipe.py"
"""
import sys
import json
import email
import requests

API_URL = "http://localhost:8000/internal/powermta/reply"

def parse_email(raw: bytes) -> dict:
    msg = email.message_from_bytes(raw)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

    return {
        "to":      msg.get("To", ""),
        "from":    msg.get("From", ""),
        "subject": msg.get("Subject", ""),
        "body":    body,
        "headers": dict(msg.items())
    }

if __name__ == "__main__":
    raw = sys.stdin.buffer.read()
    data = parse_email(raw)
    try:
        requests.post(API_URL, json=data, timeout=10)
    except Exception as e:
        print(f"Error posting reply: {e}", file=sys.stderr)