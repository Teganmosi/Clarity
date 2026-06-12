import logging
import math
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter, defaultdict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def record_outcome(db: Session, lead_id: int, action_id: str, outcome_type: str, value: float = 1.0, extra_data: dict = None):
    from ..models import OutcomeLog
    log = OutcomeLog(
        lead_id=lead_id,
        action_id=action_id,
        outcome_type=outcome_type,
        value=value,
        extra_data=extra_data or {},
    )
    db.add(log)
    db.commit()
    return log


def analyze_success_patterns(db: Session) -> Dict[str, Any]:
    from ..models import OutcomeLog, Lead, CommunicationLog
    logs = db.query(OutcomeLog).all()
    if not logs:
        return {"insights": [], "message": "Not enough outcome data yet. Use the outreach and conversation tools to generate data."}

    outcomes_by_type = Counter(l.outcome_type for l in logs)
    total = sum(outcomes_by_type.values())

    channel_performance = defaultdict(lambda: {"count": 0, "positive": 0})
    comm_logs = db.query(CommunicationLog).all()
    for cl in comm_logs:
        channel_performance[cl.channel]["count"] += 1
    for log in logs:
        if log.outcome_type in ("meeting", "opened", "replied", "closed"):
            lead = db.query(Lead).filter(Lead.id == log.lead_id).first()
            if lead:
                comms = db.query(CommunicationLog).filter(
                    CommunicationLog.lead_id == log.lead_id,
                    CommunicationLog.status == "sent",
                ).all()
                for c in comms:
                    channel_performance[c.channel]["positive"] += 1

    best_channel = max(channel_performance, key=lambda ch: channel_performance[ch]["positive"] / max(channel_performance[ch]["count"], 1)) if channel_performance else "email"

    funding_conversion = defaultdict(lambda: {"total": 0, "converted": 0})
    for log in logs:
        if log.outcome_type in ("meeting", "closed"):
            lead = db.query(Lead).filter(Lead.id == log.lead_id).first()
            if lead and lead.funding_stage:
                funding_conversion[lead.funding_stage]["total"] += 1
                funding_conversion[lead.funding_stage]["converted"] += 1

    best_funding = max(funding_conversion, key=lambda f: funding_conversion[f]["converted"] / max(funding_conversion[f]["total"], 1)) if funding_conversion else None

    insights = []

    channel_rate = channel_performance[best_channel]["positive"] / max(channel_performance[best_channel]["count"], 1) * 100 if channel_performance else 0
    insights.append({
        "type": "channel",
        "title": f"Best Channel: {best_channel.title()}",
        "detail": f"{best_channel.title()} has the highest positive outcome rate ({channel_rate:.0f}%). Prioritize {best_channel} for high-intent leads.",
        "confidence": round(channel_rate / 100, 2),
        "recommendation": f"Increase {best_channel} outreach frequency",
    })

    if best_funding:
        f_rate = funding_conversion[best_funding]["converted"] / max(funding_conversion[best_funding]["total"], 1) * 100
        insights.append({
            "type": "funding",
            "title": f"Best Segment: {best_funding}",
            "detail": f"Leads with {best_funding} funding convert at {f_rate:.0f}%. Prioritize similar profiles.",
            "confidence": round(f_rate / 100, 2),
            "recommendation": f"Increase targeting of {best_funding} leads",
        })

    intent_leads = db.query(Lead).filter(Lead.intent_score.isnot(None)).all()
    if intent_leads:
        high_intent_convert = sum(1 for l in intent_leads if l.intent_score >= 75 and l.status == "converted")
        high_intent_total = sum(1 for l in intent_leads if l.intent_score >= 75)
        high_rate = high_intent_convert / max(high_intent_total, 1) * 100
        insights.append({
            "type": "intent",
            "title": "Intent Score Correlation",
            "detail": f"Leads with Intent Score >= 75 convert at {high_rate:.0f}%. Intent detection is a strong signal.",
            "confidence": round(high_rate / 100, 2),
            "recommendation": "Maintain current intent thresholds",
        })

    return {
        "insights": insights,
        "total_outcomes": total,
        "outcomes_by_type": dict(outcomes_by_type),
    }


def optimize_intent_weights(db: Session) -> Dict[str, Any]:
    from ..models import OutcomeLog, Lead
    logs = db.query(OutcomeLog).filter(
        OutcomeLog.outcome_type.in_(["meeting", "closed", "replied"])
    ).all()
    if len(logs) < 5:
        return {"status": "skipped", "reason": f"Need at least 5 positive outcomes, have {len(logs)}", "suggested_weights": None}

    from ..services.intent_engine import SIGNAL_WEIGHTS
    original_weights = dict(SIGNAL_WEIGHTS)
    adjustments = {}

    signal_types = ["funding_round", "hiring_spree", "tech_stack_change", "revenue_growth", "leadership_change", "expansion", "ipo_rumor"]
    for signal in signal_types:
        matched = 0
        total = 0
        for log in logs:
            lead = db.query(Lead).filter(Lead.id == log.lead_id).first()
            if lead:
                total += 1
                signals = getattr(lead, "intent_signals", []) or []
                if any(s.get("type") == signal for s in signals):
                    matched += 1
        rate = matched / max(total, 1)
        adjustment = round((rate - 0.5) * 20)
        adjustments[signal] = adjustment
        if signal in SIGNAL_WEIGHTS:
            new_weight = max(5, min(30, SIGNAL_WEIGHTS[signal] + adjustment))
            SIGNAL_WEIGHTS[signal] = new_weight

    return {
        "status": "optimized",
        "original_weights": original_weights,
        "suggested_weights": dict(SIGNAL_WEIGHTS),
        "adjustments": adjustments,
        "samples_analyzed": len(logs),
    }


def create_ab_test(db: Session, name: str, variant_a: dict, variant_b: dict, metric: str = "reply_rate") -> Dict[str, Any]:
    from ..models import ABTest
    test = ABTest(
        name=name,
        variant_a=variant_a,
        variant_b=variant_b,
        metric=metric,
        status="running",
        winner=None,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return {
        "id": test.id,
        "name": test.name,
        "variant_a": test.variant_a,
        "variant_b": test.variant_b,
        "metric": test.metric,
        "status": test.status,
    }


def get_ab_test_winner(test_id: int, db: Session) -> Dict[str, Any]:
    from ..models import ABTest, OutcomeLog
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        return {"error": "Test not found"}

    a_logs = db.query(OutcomeLog).filter(
        OutcomeLog.action_id == f"ab_{test_id}_a"
    ).all()
    b_logs = db.query(OutcomeLog).filter(
        OutcomeLog.action_id == f"ab_{test_id}_b"
    ).all()

    a_positive = sum(1 for l in a_logs if l.outcome_type in ("opened", "replied", "meeting"))
    b_positive = sum(1 for l in b_logs if l.outcome_type in ("opened", "replied", "meeting"))
    a_total = len(a_logs) or 1
    b_total = len(b_logs) or 1
    a_rate = a_positive / a_total
    b_rate = b_positive / b_total

    confidence = 0.0
    if a_total + b_total > 10:
        z = (a_rate - b_rate) / math.sqrt((a_rate * (1 - a_rate) / a_total) + (b_rate * (1 - b_rate) / b_total) + 0.0001)
        confidence = min(0.99, max(0.0, 0.5 + abs(z) * 0.1))

    winner = None
    if confidence > 0.8 and a_rate != b_rate:
        winner = "A" if a_rate > b_rate else "B"
        test.winner = winner
        test.status = "completed"
        db.commit()

    return {
        "test_id": test_id,
        "test_name": test.name,
        "status": test.status,
        "winner": winner,
        "variant_a_rate": round(a_rate, 4),
        "variant_b_rate": round(b_rate, 4),
        "confidence": round(confidence, 4),
        "samples_a": len(a_logs),
        "samples_b": len(b_logs),
    }
