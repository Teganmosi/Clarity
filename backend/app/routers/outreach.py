from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..models import User, Lead, EmailOutreach
from ..auth import get_current_user
from ..services.outreach_engine import generate_email_draft, send_email

router = APIRouter(prefix="/outreach", tags=["Outreach"])

TEMPLATES = [
    {
        "id": 1,
        "name": "Cold Outreach - Tech",
        "subject": "Quick idea for {company}'s pipeline",
        "body": "Hi {name},\n\nI've been following {company}'s growth. At Clarity, we help teams like yours prioritize leads using AI.\n\nWould you be open to a quick call?\n\nBest,\nSales Team",
    },
    {
        "id": 2,
        "name": "Funding Congrats",
        "subject": "Congrats on the {funding_stage} round, {company}!",
        "body": "Hi {name},\n\nCongrats on the {funding_stage}! With this growth, having a solid lead scoring system becomes critical.\n\nClarity uses AI to detect intent signals and predict deal closures.\n\nWould 15 min next week work?\n\nBest,\nSales Team",
    },
    {
        "id": 3,
        "name": "Re-engagement",
        "subject": "Circling back, {name}",
        "body": "Hi {name},\n\nJust circling back. We've added new AI features including intent detection and predictive revenue modeling.\n\nWorth a fresh look?\n\nBest,\nSales Team",
    },
]


@router.post("/generate-draft")
async def create_draft(
    lead_id: int,
    template_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if template_id:
        tpl = next((t for t in TEMPLATES if t["id"] == template_id), None)
        if not tpl:
            raise HTTPException(status_code=404, detail="Template not found")
        subject = tpl["subject"].format(name=lead.name, company=lead.company, funding_stage=lead.funding_stage or "")
        body = tpl["body"].format(name=lead.name, company=lead.company, funding_stage=lead.funding_stage or "")
        result = {"subject": subject, "body": body, "confidence_score": 0.7, "ai_model_used": "template"}
    else:
        result = await generate_email_draft(lead)

    outreach = EmailOutreach(
        lead_id=lead_id,
        subject=result["subject"],
        body=result["body"],
        status="draft",
        ai_model_used=result.get("ai_model_used", "template"),
    )
    db.add(outreach)
    db.commit()
    db.refresh(outreach)

    return {
        "id": outreach.id,
        "subject": result["subject"],
        "body": result["body"],
        "confidence_score": result.get("confidence_score", 0.5),
        "ai_model_used": result.get("ai_model_used", "template"),
        "status": outreach.status,
    }


@router.post("/send")
async def send_outreach(
    outreach_id: int,
    recipient_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    outreach = db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")

    lead = db.query(Lead).filter(Lead.id == outreach.lead_id).first()
    send_result = await send_email(outreach.lead_id, outreach.subject, outreach.body, recipient_email)

    if send_result.get("status") == "sent":
        outreach.status = "sent"
        outreach.sent_at = datetime.utcnow()

    db.commit()
    return {
        "id": outreach.id,
        "status": outreach.status,
        "sent_at": outreach.sent_at.isoformat() if outreach.sent_at else None,
        "send_result": send_result,
    }


@router.get("/templates")
async def list_templates():
    return {"templates": TEMPLATES}


@router.get("/history/{lead_id}")
async def get_outreach_history(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    records = db.query(EmailOutreach).filter(EmailOutreach.lead_id == lead_id).order_by(EmailOutreach.created_at.desc()).all()
    return {
        "lead_id": lead_id,
        "history": [
            {
                "id": r.id,
                "subject": r.subject,
                "body": r.body,
                "status": r.status,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "opened_at": r.opened_at.isoformat() if r.opened_at else None,
                "ai_model_used": r.ai_model_used,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }
