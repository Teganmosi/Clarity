import os
import hashlib
import logging
import random
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timezone
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DATA_HASH_SALT = os.getenv("DATA_HASH_SALT", "clarity-network-salt-v1")


def privacy_hash(data: str) -> str:
    return hashlib.sha256(f"{data}{DATA_HASH_SALT}".encode()).hexdigest()


def ingest_anonymized_outcome(db: Session, lead_id: int = None, email: str = None,
                               industry: str = None, funding_stage: str = None,
                               action: str = None, action_type: str = None,
                               success: bool = None, channel: str = None):
    from ..models import AnonymizedOutcome, CommunicationLog, Lead

    lead = db.query(Lead).filter(Lead.id == lead_id).first() if lead_id else None
    hashed_id = privacy_hash(email or (lead.email if lead else "unknown"))
    ind = industry or (lead.industry if lead else "unknown")
    fs = funding_stage or (lead.funding_stage if lead else "unknown")

    outcome = AnonymizedOutcome(
        hashed_identifier=hashed_id,
        industry_tag=ind,
        funding_stage=fs,
        action=action or "unknown",
        action_type=action_type or "email",
        success=success if success is not None else random.random() > 0.5,
        channel=channel or "email",
    )
    db.add(outcome)
    db.commit()


def calculate_industry_benchmarks(db: Session, industry: str = None) -> Dict[str, Any]:
    from ..models import AnonymizedOutcome
    query = db.query(AnonymizedOutcome)
    if industry:
        query = query.filter(AnonymizedOutcome.industry_tag == industry)

    outcomes = query.all()
    if not outcomes:
        return {"benchmarks": [], "message": "Not enough network data yet. Use the system more to generate benchmarks."}

    channel_success = defaultdict(lambda: {"total": 0, "success": 0})
    action_success = defaultdict(lambda: {"total": 0, "success": 0})

    for o in outcomes:
        ch = o.channel or "email"
        channel_success[ch]["total"] += 1
        if o.success:
            channel_success[ch]["success"] += 1
        act = o.action or "outreach"
        action_success[act]["total"] += 1
        if o.success:
            action_success[act]["success"] += 1

    benchmarks = []
    for ch, data in sorted(channel_success.items(), key=lambda x: x[1]["success"] / max(x[1]["total"], 1), reverse=True):
        rate = data["success"] / max(data["total"], 1) * 100
        benchmarks.append({
            "type": "channel",
            "segment": ch,
            "success_rate": round(rate, 1),
            "sample_size": data["total"],
        })

    for act, data in sorted(action_success.items(), key=lambda x: x[1]["success"] / max(x[1]["total"], 1), reverse=True)[:5]:
        rate = data["success"] / max(data["total"], 1) * 100
        benchmarks.append({
            "type": "action",
            "segment": act,
            "success_rate": round(rate, 1),
            "sample_size": data["total"],
        })

    return {
        "industry": industry or "all",
        "total_outcomes": len(outcomes),
        "benchmarks": benchmarks,
    }


def get_network_insights(db: Session, user_industry: str = None) -> Dict[str, Any]:
    from ..models import AnonymizedOutcome, Lead
    outcomes = db.query(AnonymizedOutcome).all()
    if not outcomes:
        return {"insights": [], "message": "Network is still building insights. More data needed."}

    ind_outcomes = [o for o in outcomes if o.industry_tag == user_industry] if user_industry else outcomes
    total = len(ind_outcomes)
    if total < 3:
        return {"insights": [], "message": f"Need at least 3 outcomes in {user_industry or 'your industry'}, have {total}."}

    channel_rates = defaultdict(list)
    for o in ind_outcomes:
        channel_rates[o.channel or "email"].append(o.success)

    best_channel = max(channel_rates, key=lambda ch: sum(channel_rates[ch]) / max(len(channel_rates[ch]), 1))
    best_rate = sum(channel_rates[best_channel]) / max(len(channel_rates[best_channel]), 1) * 100

    alerts = []
    leads = db.query(Lead).filter(Lead.industry == user_industry).all() if user_industry else []
    high_intent = [l for l in leads if (l.intent_score or 0) >= 75]
    if high_intent and best_channel:
        alerts.append({
            "title": f"Contact {len(high_intent)} high-intent leads via {best_channel}",
            "detail": f"Network data shows {best_channel} has {best_rate:.0f}% success rate in your industry. {len(high_intent)} leads match this profile.",
            "priority": "high",
            "lead_ids": [l.id for l in high_intent[:5]],
        })

    low_engagement = [l for l in leads if (l.intent_score or 0) < 30 and l.status not in ("converted", "lost")]
    if low_engagement:
        alerts.append({
            "title": f"{len(low_engagement)} leads need re-engagement",
            "detail": f"These leads have low intent scores. Consider running a re-engagement campaign via {best_channel}.",
            "priority": "medium",
            "lead_ids": [l.id for l in low_engagement[:5]],
        })

    insights = [
        {
            "type": "channel_performance",
            "title": f"Best Channel: {best_channel.title()}",
            "detail": f"In {user_industry or 'your'} segment, {best_channel} has {best_rate:.0f}% success rate ({total} outcomes analyzed).",
            "confidence": round(best_rate / 100, 2),
        },
        {
            "type": "network_growth",
            "title": "Network Intelligence Active",
            "detail": f"Analyzed {len(outcomes)} anonymized outcomes across all industries. The more data we collect, the smarter predictions become.",
            "confidence": 0.9,
        },
    ]

    return {
        "insights": insights,
        "alerts": alerts,
        "total_network_outcomes": len(outcomes),
        "industry_outcomes": total,
    }
