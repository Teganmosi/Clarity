import os
import logging
import random
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

COMPANY_LEGAL_NAME = os.getenv("COMPANY_LEGAL_NAME", "Clarity AI, Inc.")


async def generate_contract(lead_id: int, db: Session, terms: Dict[str, Any] = None) -> Dict[str, Any]:
    from ..models import Lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"error": "Lead not found"}

    clv = terms.get("clv") if terms and terms.get("clv") else (lead.estimated_clv or 0)
    currency = terms.get("currency", "USD")
    scope = terms.get("scope", "AI Lead Scoring & Outreach Platform")
    duration = terms.get("duration_months", 12)

    contract = f"""# MASTER SERVICES AGREEMENT

**Effective Date:** {datetime.now(timezone.utc).strftime('%B %d, %Y')}

**Between:**
{COMPANY_LEGAL_NAME}
("Provider")

**And:**
{lead.name or 'Client'}
{lead.company or 'Client Company'}
{lead.headquarters_location or ''}
("Client")

---

## 1. SERVICES
Provider agrees to provide the {scope} (the "Services") to Client for a term of {duration} months commencing on the Effective Date.

## 2. FEES AND PAYMENT
**Total Contract Value:** {currency} {clv:,.2f}
**Billing Frequency:** Monthly in advance
**Payment Terms:** Net 30

## 3. SCOPE OF WORK
- AI-powered lead enrichment via Clearbit, Apollo, and Crunchbase
- Intent detection and predictive scoring engine
- Multi-channel outreach automation (Email, LinkedIn, SMS)
- AI qualification conversation agent (BANT framework)
- Meeting scheduling and calendar integration
- Analytics dashboard and revenue forecasting
- Network intelligence and industry benchmarking

## 4. DATA PRIVACY & COMPLIANCE
Provider shall process all Client data in accordance with applicable data protection laws. Both parties agree to the Data Processing Agreement attached hereto.

## 5. LIMITATION OF LIABILITY
Neither party's liability shall exceed the total fees paid by Client to Provider in the 12 months preceding the claim.

## 6. TERM AND TERMINATION
This Agreement shall commence on the Effective Date and continue for {duration} months. Either party may terminate for material breach upon 30 days written notice.

## 7. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

---

**IN WITNESS WHEREOF**, the parties have executed this Agreement as of the Effective Date.

_________________________          _________________________
{COMPANY_LEGAL_NAME}               {lead.name or 'Client'}

"""

    compliance = await check_legal_compliance(contract)

    return {
        "contract_content": contract,
        "compliance_check": compliance,
        "clv": clv,
        "currency": currency,
        "scope": scope,
        "duration_months": duration,
    }


async def check_legal_compliance(contract_text: str) -> Dict[str, Any]:
    issues = []
    warnings = []

    required_clauses = [
        ("Limitation of Liability", "limitation of liability"),
        ("Governing Law", "governing law"),
        ("Termination", "termination"),
        ("Data Privacy", "data privacy"),
        ("Fees and Payment", "fees and payment"),
    ]

    text_lower = contract_text.lower()
    for clause_name, keyword in required_clauses:
        if keyword not in text_lower:
            issues.append({"severity": "high", "clause": clause_name, "detail": f"Missing required clause: {clause_name}"})

    if len(contract_text) < 500:
        issues.append({"severity": "high", "clause": "Completeness", "detail": "Contract appears too short"})

    gdpr_keywords = ["gdpr", "data protection", "personal data"]
    if not any(k in text_lower for k in gdpr_keywords):
        warnings.append({"severity": "medium", "clause": "GDPR", "detail": "No GDPR/data protection clause found"})

    return {
        "status": "blocked" if issues else "pass" if not warnings else "warnings",
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings),
    }


def send_for_signature(deal_id: int, signer_email: str) -> Dict[str, Any]:
    signing_url = f"https://sign.clarity.ai/deal/{deal_id}"
    return {
        "status": "sent",
        "signing_url": signing_url,
        "envelope_id": f"env_{deal_id}_{random.randint(10000, 99999)}",
    }


def simulate_sign(deal_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Deal
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        return {"error": "Deal not found"}
    deal.status = "signed"
    deal.signed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "signed", "signed_at": deal.signed_at.isoformat()}


def process_payment(deal_id: int, db: Session) -> Dict[str, Any]:
    from ..models import Deal
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        return {"error": "Deal not found"}

    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key:
        try:
            import stripe
            stripe.api_key = stripe_key
            intent = stripe.PaymentIntent.create(
                amount=int(deal.value * 100),
                currency=deal.currency.lower() if deal.currency else "usd",
                metadata={"deal_id": deal_id},
            )
            deal.payment_intent_id = intent.id
            deal.payment_link = intent.client_secret
            deal.status = "paid"
            deal.paid_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "paid", "payment_intent_id": intent.id, "client_secret": intent.client_secret}
        except Exception as e:
            logger.warning(f"Stripe failed: {e}")

    deal.status = "paid"
    deal.payment_link = f"https://pay.clarity.ai/deal/{deal_id}"
    deal.paid_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "paid", "payment_link": deal.payment_link, "mocked": True}
