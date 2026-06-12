import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CHANNEL_COOLDOWN_HOURS = {
    "email": 48,
    "linkedin": 72,
    "sms": 24,
}

CHANNEL_PRIORITY = ["sms", "email", "linkedin"]


def is_suppressed(db: Session, email: str = None, phone: str = None) -> bool:
    if not email and not phone:
        return False
    from ..models import GlobalSuppression
    query = db.query(GlobalSuppression)
    if email:
        query = query.filter(GlobalSuppression.email == email)
    if phone:
        query = query.filter(GlobalSuppression.phone == phone)
    return query.first() is not None


def get_last_contact(db: Session, lead_id: int, channel: str = None) -> Optional[datetime]:
    from ..models import CommunicationLog
    query = db.query(CommunicationLog).filter(
        CommunicationLog.lead_id == lead_id,
        CommunicationLog.status.in_(["sent", "opened", "replied"]),
    )
    if channel:
        query = query.filter(CommunicationLog.channel == channel)
    record = query.order_by(CommunicationLog.sent_at.desc()).first()
    return record.sent_at if record else None


def get_best_channel(lead_id: int, db: Session, preferred_channel: str = None) -> Dict[str, Any]:
    from ..models import Lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"channel": "email", "reason": "Lead not found, defaulting to email"}

    if is_suppressed(db, email=lead.email, phone=getattr(lead, "phone", None)):
        return {"channel": None, "reason": "Lead is on suppression list"}

    now = datetime.utcnow()
    available = []

    for ch in CHANNEL_PRIORITY:
        if preferred_channel and ch != preferred_channel:
            continue
        last = get_last_contact(db, lead_id, ch)
        cooldown = CHANNEL_COOLDOWN_HOURS.get(ch, 48)
        if last is None or (now - last).total_seconds() >= cooldown * 3600:
            hours_remaining = 0
            if last:
                elapsed = (now - last).total_seconds() / 3600
                hours_remaining = max(0, int(cooldown - elapsed))
            available.append((ch, hours_remaining))

    if not available:
        last_any = get_last_contact(db, lead_id)
        if last_any:
            next_at = last_any + timedelta(hours=min(CHANNEL_COOLDOWN_HOURS.values()))
            return {
                "channel": None,
                "reason": f"All channels on cooldown. Next available at {next_at.strftime('%Y-%m-%d %H:%M')}",
            }
        return {"channel": "email", "reason": "No previous contact, defaulting to email"}

    intent = getattr(lead, "intent_score", 0) or 0
    if intent >= 75:
        best = next((ch for ch in ["sms", "email"] if ch in [a[0] for a in available]), available[0][0])
    elif intent >= 40:
        best = next((ch for ch in ["email", "linkedin"] if ch in [a[0] for a in available]), available[0][0])
    else:
        best = next((ch for ch in ["linkedin", "email"] if ch in [a[0] for a in available]), available[0][0])

    return {
        "channel": best,
        "reason": f"Intent score {intent} → recommended {best}",
    }


def record_communication(db: Session, lead_id: int, channel: str, status: str,
                         subject: str = None, body: str = None, message_id: str = None):
    from ..models import CommunicationLog
    log = CommunicationLog(
        lead_id=lead_id,
        channel=channel,
        status=status,
        subject=subject,
        body=body,
        message_id=message_id,
    )
    db.add(log)
    db.commit()


def add_suppression(db: Session, email: str = None, phone: str = None,
                    reason: str = "user_request", added_by: str = None):
    from ..models import GlobalSuppression
    existing = db.query(GlobalSuppression).filter(
        (GlobalSuppression.email == email) | (GlobalSuppression.phone == phone)
    ).first()
    if existing:
        return existing
    suppress = GlobalSuppression(
        email=email,
        phone=phone,
        reason=reason,
        added_by=added_by,
    )
    db.add(suppress)
    db.commit()
    db.refresh(suppress)
    return suppress
