from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models import User, Lead, Deal, ContractLog
from ..auth import get_current_user
from ..services.closing_engine import generate_contract, send_for_signature, simulate_sign, process_payment

router = APIRouter(prefix="/closing", tags=["Closing"])


@router.post("/generate")
async def create_deal(
    lead_id: int,
    clv: Optional[float] = None,
    currency: str = "USD",
    scope: str = "AI Lead Scoring & Outreach Platform",
    duration_months: int = 12,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    terms = {"clv": clv, "currency": currency, "scope": scope, "duration_months": duration_months}
    result = await generate_contract(lead_id, db, terms)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    deal = Deal(
        lead_id=lead_id,
        value=result["clv"],
        currency=result["currency"],
        contract_content=result["contract_content"],
        status="draft",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)

    log = ContractLog(deal_id=deal.id, action="generated", details=f"Contract generated via AI ({scope})")
    db.add(log)
    db.commit()

    return {
        "deal_id": deal.id,
        "lead_id": lead_id,
        "value": result["clv"],
        "currency": result["currency"],
        "contract_content": result["contract_content"],
        "compliance_check": result["compliance_check"],
        "status": "draft",
    }


@router.post("/send/{deal_id}")
async def send_deal(
    deal_id: int,
    signer_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    result = send_for_signature(deal_id, signer_email)
    deal.status = "sent"
    deal.signing_url = result["signing_url"]
    db.commit()

    log = ContractLog(deal_id=deal.id, action="sent", details=f"Sent for signature to {signer_email}")
    db.add(log)
    db.commit()

    return {"deal_id": deal_id, "status": "sent", "signing_url": result["signing_url"]}


@router.get("/deals/{lead_id}")
async def get_lead_deals(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    deals = db.query(Deal).filter(Deal.lead_id == lead_id).order_by(Deal.id.desc()).all()
    return {
        "lead_id": lead_id,
        "deals": [
            {
                "id": d.id,
                "value": d.value,
                "currency": d.currency,
                "status": d.status,
                "signing_url": d.signing_url,
                "payment_link": d.payment_link,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "signed_at": d.signed_at.isoformat() if d.signed_at else None,
                "paid_at": d.paid_at.isoformat() if d.paid_at else None,
            }
            for d in deals
        ],
    }


@router.post("/sign/{deal_id}")
async def sign_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = simulate_sign(deal_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    log = ContractLog(deal_id=deal_id, action="signed", details="Contract signed by client")
    db.add(log)
    db.commit()

    return result


@router.post("/pay/{deal_id}")
async def pay_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = process_payment(deal_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    log = ContractLog(deal_id=deal_id, action="paid", details=f"Payment completed: {result.get('payment_intent_id', 'mocked')}")
    db.add(log)
    db.commit()

    return result


@router.get("/all")
async def list_all_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deals = db.query(Deal).join(Lead).filter(Lead.user_id == current_user.id).order_by(Deal.id.desc()).limit(50).all()
    return {
        "deals": [
            {
                "id": d.id,
                "lead_id": d.lead_id,
                "lead_name": (db.query(Lead).filter(Lead.id == d.lead_id).first().name if db.query(Lead).filter(Lead.id == d.lead_id).first() else "Unknown"),
                "value": d.value,
                "currency": d.currency,
                "status": d.status,
                "signing_url": d.signing_url,
                "payment_link": d.payment_link,
                "signed_at": d.signed_at.isoformat() if d.signed_at else None,
                "paid_at": d.paid_at.isoformat() if d.paid_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in deals
        ]
    }
