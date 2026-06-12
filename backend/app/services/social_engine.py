import os
import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def generate_linkedin_message(lead: Any) -> Dict[str, str]:
    name = getattr(lead, "name", "there")
    company = getattr(lead, "company", "your company")
    title = getattr(lead, "title", "professional")
    funding = getattr(lead, "funding_stage", "")
    funding_line = f" Saw you recently raised {funding} — impressive!" if funding else ""

    message = f"""Hi {name},

Love what {company} is doing in the {title} space.{funding_line}

We help sales teams turn enriched data into pipeline. Worth a quick chat?

Best,
Sales Team"""

    return {
        "subject": f"Quick thought for {name}",
        "body": message.strip(),
    }


async def send_linkedin(lead_id: int, message: str) -> Dict[str, Any]:
    logger.info(f"[LinkedIn Mock] Connection request queued for lead {lead_id}")
    return {
        "status": "sent",
        "channel": "linkedin",
        "sent_at": datetime.utcnow().isoformat(),
        "mocked": True,
    }


async def send_sms(lead_id: int, message: str, to_phone: str) -> Dict[str, Any]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    if not account_sid or not auth_token:
        logger.info(f"[SMS Mock] SMS queued for lead {lead_id} to {to_phone}")
        return {
            "status": "sent",
            "channel": "sms",
            "to": to_phone,
            "sent_at": datetime.utcnow().isoformat(),
            "mocked": True,
        }

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        twilio_msg = client.messages.create(
            body=message[:1600],
            from_=from_number,
            to=to_phone,
        )
        return {
            "status": "sent",
            "channel": "sms",
            "to": to_phone,
            "sid": twilio_msg.sid,
            "sent_at": datetime.utcnow().isoformat(),
            "mocked": False,
        }
    except Exception as e:
        logger.error(f"Twilio SMS failed for lead {lead_id}: {e}")
        return {
            "status": "failed",
            "channel": "sms",
            "error": str(e),
        }


async def generate_sms_alert(lead: Any) -> str:
    name = getattr(lead, "name", "Lead")
    company = getattr(lead, "company", "a company")
    intent = getattr(lead, "intent_score", 0)
    return f"Alert: {name} at {company} has high intent ({intent}/100). Recommended action: contact within 24h."
