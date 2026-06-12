import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SIGNAL_WEIGHTS = {
    "funding_round": 20,
    "hiring_spree": 15,
    "tech_stack_change": 10,
    "revenue_growth": 15,
    "leadership_change": 12,
    "expansion": 10,
    "ipo_rumor": 18,
}

SIGNAL_DESCRIPTIONS = {
    "funding_round": "Recently raised funding round ({detail})",
    "hiring_spree": "Significant hiring activity ({detail} new positions)",
    "tech_stack_change": "New technology adopted: {detail}",
    "revenue_growth": "Revenue growth detected ({detail})",
    "leadership_change": "Key leadership hire: {detail}",
    "expansion": "Geographic or office expansion ({detail})",
    "ipo_rumor": "IPO or acquisition rumors ({detail})",
}


def calculate_intent_score(lead: Any) -> Dict[str, Any]:
    signals = detect_signals(lead)
    base_score = sum(SIGNAL_WEIGHTS.get(s["type"], 0) for s in signals)
    score = min(base_score, 100)
    return {
        "intent_score": score,
        "intent_signals": signals,
        "last_intent_check": datetime.utcnow(),
    }


def detect_signals(lead: Any) -> List[Dict[str, Any]]:
    signals = []
    enrichment = _get_enrichment_dict(lead)

    funding = enrichment.get("funding_stage")
    if funding and funding.lower() not in ("none", "", "bootstrapped"):
        signals.append({
            "type": "funding_round",
            "severity": "high",
            "detail": funding,
            "detected_at": datetime.utcnow().isoformat(),
        })

    employees = enrichment.get("employee_count")
    if employees and isinstance(employees, (int, float)) and employees > 200:
        growth_indicator = "rapid" if employees > 1000 else "moderate"
        signals.append({
            "type": "hiring_spree",
            "severity": "medium" if employees > 1000 else "low",
            "detail": str(employees),
            "detected_at": datetime.utcnow().isoformat(),
        })

    tech = enrichment.get("technologies")
    if tech and isinstance(tech, list) and len(tech) > 5:
        signals.append({
            "type": "tech_stack_change",
            "severity": "medium",
            "detail": ", ".join(tech[:3]),
            "detected_at": datetime.utcnow().isoformat(),
        })

    revenue = enrichment.get("annual_revenue")
    if revenue and revenue not in ("", "unknown"):
        signals.append({
            "type": "revenue_growth",
            "severity": "medium",
            "detail": revenue,
            "detected_at": datetime.utcnow().isoformat(),
        })

    industry_tags = enrichment.get("industry_tags")
    if industry_tags and isinstance(industry_tags, list):
        growth_keywords = ["saas", "fintech", "healthtech", "ai", "ml", "enterprise"]
        matched = [t for t in industry_tags if any(kw in t.lower() for kw in growth_keywords)]
        if matched:
            signals.append({
                "type": "expansion",
                "severity": "low",
                "detail": ", ".join(matched),
                "detected_at": datetime.utcnow().isoformat(),
            })

    return signals


def _get_enrichment_dict(lead: Any) -> Dict[str, Any]:
    fields = [
        "technologies", "funding_stage", "employee_count", "annual_revenue",
        "industry_tags", "headquarters_location", "founded_year", "logo_url",
        "linkedin_url", "twitter_handle",
    ]
    result = {}
    for field in fields:
        val = getattr(lead, field, None)
        if val is not None:
            result[field] = val
    return result
