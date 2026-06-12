from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models import User, Lead, Conversation
from ..auth import get_current_user
from ..services.conversation_engine import generate_response, WELCOME_MESSAGE

router = APIRouter(prefix="/conversation", tags=["Conversation"])


def _get_or_create_conversation(lead_id: int, db: Session) -> Conversation:
    conv = db.query(Conversation).filter(
        Conversation.lead_id == lead_id,
        Conversation.status.in_(["active", "handed_off"]),
    ).order_by(Conversation.id.desc()).first()
    if not conv:
        conv = Conversation(
            lead_id=lead_id,
            channel="chat",
            messages=[WELCOME_MESSAGE],
            bant_scores={},
            status="active",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


@router.post("/send")
async def send_message(
    lead_id: int,
    message: str,
    channel: str = "chat",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    conv = _get_or_create_conversation(lead_id, db)
    if conv.status == "handed_off":
        return {
            "conversation_id": conv.id,
            "response": "This conversation has been handed off to a human agent. They will reach out shortly.",
            "bant": conv.bant_scores,
            "bant_total": sum(conv.bant_scores.values()) if isinstance(conv.bant_scores, dict) else 0,
            "handoff": True,
            "status": conv.status,
        }

    conv.messages = conv.messages or []
    conv.messages.append({"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()})

    lead_context = {
        "name": lead.name,
        "company": lead.company,
        "title": lead.title,
        "funding_stage": lead.funding_stage,
        "employee_count": lead.employee_count,
        "intent_score": lead.intent_score,
    }

    result = generate_response(conv.messages, lead_context)

    conv.messages.append({
        "role": "assistant",
        "content": result["response"],
        "timestamp": datetime.utcnow().isoformat(),
    })
    conv.bant_scores = result["bant"]

    if result["handoff"]:
        conv.status = "handed_off"

    db.commit()
    db.refresh(conv)

    return {
        "conversation_id": conv.id,
        "response": result["response"],
        "bant": result["bant"],
        "bant_total": result["bant_total"],
        "handoff": result["handoff"],
        "sentiment": result["sentiment"],
        "status": conv.status,
    }


@router.get("/{lead_id}")
async def get_conversation(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    conv = db.query(Conversation).filter(
        Conversation.lead_id == lead_id,
    ).order_by(Conversation.id.desc()).first()
    if not conv:
        return {"lead_id": lead_id, "conversation": None}
    return {
        "lead_id": lead_id,
        "conversation": {
            "id": conv.id,
            "channel": conv.channel,
            "messages": conv.messages,
            "bant_scores": conv.bant_scores,
            "status": conv.status,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        },
    }


@router.post("/handoff/{conversation_id}")
async def trigger_handoff(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = "handed_off"
    db.commit()
    return {"conversation_id": conversation_id, "status": "handed_off"}


@router.get("/")
async def list_conversations(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Conversation).join(Lead).filter(Lead.user_id == current_user.id)
    if status:
        query = query.filter(Conversation.status == status)
    conversations = query.order_by(Conversation.updated_at.desc()).limit(50).all()

    result = []
    for conv in conversations:
        lead = db.query(Lead).filter(Lead.id == conv.lead_id).first()
        result.append({
            "id": conv.id,
            "lead_id": conv.lead_id,
            "lead_name": lead.name if lead else "Unknown",
            "lead_company": lead.company if lead else "",
            "channel": conv.channel,
            "bant_scores": conv.bant_scores,
            "status": conv.status,
            "message_count": len(conv.messages) if conv.messages else 0,
            "last_message": conv.messages[-1]["content"][:100] if conv.messages else "",
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        })
    return {"conversations": result}
