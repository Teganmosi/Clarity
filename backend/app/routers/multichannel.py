from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models import User, Lead, CommunicationLog, GlobalSuppression
from ..auth import get_current_user
from ..services.channel_coordinator import (
    get_best_channel, record_communication, add_suppression, is_suppressed
)
from ..services.social_engine import (
    generate_linkedin_message, send_linkedin, send_sms, generate_sms_alert
)
from ..services.outreach_engine import generate_email_draft, send_email

router = APIRouter(prefix="/multichannel", tags=["Multi-Channel"])


@router.post("/suggest")
async def suggest_channel(
    lead_id: int,
    preferred_channel: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    recommendation = get_best_channel(lead_id, db, preferred_channel)
    channel = recommendation["channel"]

    draft = None
    if channel == "email":
        result = await generate_email_draft(lead)
        draft = {"subject": result["subject"], "body": result["body"], "ai_model_used": result.get("ai_model_used")}
    elif channel == "linkedin":
        result = await generate_linkedin_message(lead)
        draft = {"subject": result["subject"], "body": result["body"], "ai_model_used": "template"}
    elif channel == "sms":
        result = await generate_sms_alert(lead)
        draft = {"subject": "SMS Alert", "body": result, "ai_model_used": "template"}

    return {
        "lead_id": lead_id,
        "lead_name": lead.name,
        "lead_company": lead.company,
        "recommended_channel": channel,
        "reason": recommendation["reason"],
        "draft": draft,
    }


@router.post("/send")
async def send_multichannel(
    lead_id: int,
    channel: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if is_suppressed(db, email=lead.email, phone=getattr(lead, "phone", None)):
        raise HTTPException(status_code=400, detail="Lead is on global suppression list")

    recommendation = get_best_channel(lead_id, db, channel)
    if recommendation["channel"] is None:
        raise HTTPException(status_code=429, detail=recommendation["reason"])

    result = None
    if channel == "email":
        if not body:
            draft = await generate_email_draft(lead)
            body = draft["body"]
            subject = subject or draft["subject"]
        result = await send_email(lead_id, subject or "", body, recipient or lead.email)
    elif channel == "linkedin":
        result = await send_linkedin(lead_id, body or f"Hi {lead.name}, let's connect!")
    elif channel == "sms":
        result = await send_sms(lead_id, body or "Check your inbox!", recipient or getattr(lead, "phone", ""))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")

    status = result.get("status", "failed")
    record_communication(db, lead_id, channel, status, subject, body)

    return {
        "lead_id": lead_id,
        "channel": channel,
        "status": status,
        "result": result,
    }


@router.post("/suppressions/add")
async def add_suppression(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    reason: str = "user_request",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Either email or phone is required")
    suppress = add_suppression(db, email, phone, reason, current_user.username)
    return {
        "id": suppress.id,
        "email": suppress.email,
        "phone": suppress.phone,
        "reason": suppress.reason,
    }


@router.get("/suppressions")
async def list_suppressions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = db.query(GlobalSuppression).order_by(GlobalSuppression.created_at.desc()).all()
    return {
        "suppressions": [
            {
                "id": r.id,
                "email": r.email,
                "phone": r.phone,
                "reason": r.reason,
                "added_by": r.added_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }


@router.delete("/suppressions/{suppression_id}")
async def remove_suppression(
    suppression_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(GlobalSuppression).filter(GlobalSuppression.id == suppression_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suppression not found")
    db.delete(record)
    db.commit()
    return {"deleted": True}


@router.get("/history/{lead_id}")
async def get_omnichannel_history(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    logs = db.query(CommunicationLog).filter(
        CommunicationLog.lead_id == lead_id
    ).order_by(CommunicationLog.sent_at.desc()).all()
    return {
        "lead_id": lead_id,
        "history": [log.to_dict() for log in logs],
    }
