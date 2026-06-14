from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Lead, VoiceCallLog
from ..auth import get_current_user
from ..services.global_engine import detect_language, check_compliance, format_currency, detect_region_from_phone, get_region_currency
from ..services.voice_agent import initiate_call, process_voice_transcript

router = APIRouter(prefix="/global", tags=["Global"])


@router.post("/detect")
async def detect_lead_context(
    lead_id: int,
    text_sample: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    sample = text_sample or lead.name or lead.company or ""
    language = detect_language(sample)
    region = detect_region_from_phone(lead.phone or "")
    compliance = check_compliance(region)
    currency = get_region_currency(region)

    lead.preferred_language = language
    lead.region = region
    lead.compliance_flags = compliance
    db.commit()

    return {
        "lead_id": lead_id,
        "detected_language": language,
        "region": region,
        "currency": currency,
        "compliance": compliance,
    }


@router.post("/voice/call")
async def voice_call(
    lead_id: int,
    phone_number: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    language = lead.preferred_language or detect_language(lead.name or "")
    result = await initiate_call(lead_id, phone_number, lead.name, lead.company, language)

    call_log = VoiceCallLog(
        lead_id=lead_id,
        status=result["status"],
        phone_number=phone_number,
        language=language,
        recording_url="",
        call_summary="",
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)

    return {
        "call_id": call_log.id,
        "lead_id": lead_id,
        "status": result["status"],
        "script": result["script"],
        "mocked": result.get("mocked", False),
    }


@router.post("/voice/transcribe")
async def transcribe_call(
    call_id: int,
    transcript: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    call_log = db.query(VoiceCallLog).filter(VoiceCallLog.id == call_id).first()
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")

    result = await process_voice_transcript(transcript)
    call_log.transcript = transcript
    call_log.call_summary = result["summary"]
    call_log.status = "completed"
    db.commit()

    return {
        "call_id": call_id,
        "sentiment": result["sentiment"],
        "bant": result["bant"],
        "summary": result["summary"],
    }


@router.get("/voice/logs/{lead_id}")
async def get_voice_logs(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    logs = db.query(VoiceCallLog).filter(VoiceCallLog.lead_id == lead_id).order_by(VoiceCallLog.id.desc()).all()
    return {
        "lead_id": lead_id,
        "calls": [
            {
                "id": l.id,
                "status": l.status,
                "phone_number": l.phone_number,
                "language": l.language,
                "transcript": l.transcript,
                "call_summary": l.call_summary,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }
