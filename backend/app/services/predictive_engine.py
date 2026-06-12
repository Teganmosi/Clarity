import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models", "closure_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models", "closure_scaler.pkl")

_model = None
_scaler = None

INDUSTRY_MULTIPLIERS = {
    "saas": 1.4, "fintech": 1.5, "healthtech": 1.3, "ai": 1.6,
    "ml": 1.6, "enterprise": 1.3, "ecommerce": 1.1, "biotech": 1.4,
    "cybersecurity": 1.5, "cleantech": 1.2,
}

FUNDING_WEIGHTS = {
    "seed": 0.6, "series a": 0.8, "series b": 1.2, "series c": 1.5,
    "series d": 1.8, "growth": 2.0, "ipo": 2.5,
}


def _get_model():
    global _model, _scaler
    if _model is None:
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            _model = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
            logger.info("Loaded pre-trained closure prediction model")
        else:
            _model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
            _scaler = StandardScaler()
            logger.info("Initialized untrained closure prediction model")
    return _model, _scaler


def _extract_features(lead: Any) -> np.ndarray:
    features = []
    features.append(getattr(lead, "intent_score", 0) or 0)
    features.append(getattr(lead, "employee_count", 0) or 0)
    funding = (getattr(lead, "funding_stage", "") or "").lower()
    funding_weight = max(FUNDING_WEIGHTS.get(funding, 0.3), 0.3)
    features.append(funding_weight)
    tech = getattr(lead, "technologies", []) or []
    features.append(min(len(tech) / 20.0, 1.0))
    score = getattr(lead, "score", 0) or 0
    features.append(score / 100.0)
    interactions = getattr(lead, "past_interactions", 0) or 0
    features.append(min(interactions / 20.0, 1.0))
    features.append(1.0 if getattr(lead, "converted", False) else 0.0)
    return np.array(features).reshape(1, -1)


def calculate_closure_probability(lead: Any) -> float:
    model, scaler = _get_model()
    features = _extract_features(lead)
    try:
        if hasattr(model, "classes_") and len(model.classes_) > 1:
            features_scaled = scaler.transform(features) if hasattr(scaler, "mean_") else features
            prob = model.predict_proba(features_scaled)[0][1]
        else:
            prob = _fallback_probability(features)
        return round(float(prob), 4)
    except Exception as e:
        logger.warning(f"ML prediction failed, using fallback: {e}")
        return _fallback_probability(features)


def _fallback_probability(features: np.ndarray) -> float:
    intent, employees, funding, tech, score, interactions, converted = features[0]
    base = 0.15
    base += intent * 0.004
    base += funding * 0.08
    base += tech * 0.1
    base += score * 0.3
    base += interactions * 0.05
    if converted > 0:
        base += 0.2
    return min(max(base, 0.02), 0.98)


def calculate_clv(lead: Any) -> float:
    revenue = str(getattr(lead, "annual_revenue", "") or "")
    revenue_value = _parse_revenue(revenue)
    industry_tags = getattr(lead, "industry_tags", []) or []
    multiplier = 1.0
    for tag in industry_tags:
        tag_lower = tag.lower()
        for key, val in INDUSTRY_MULTIPLIERS.items():
            if key in tag_lower:
                multiplier = max(multiplier, val)
    intent_score = getattr(lead, "intent_score", 0) or 0
    intent_mult = 1.0 + (intent_score / 100.0) * 0.5
    clv = revenue_value * multiplier * intent_mult
    return round(clv, 2)


def _parse_revenue(revenue: str) -> float:
    if not revenue:
        return 50000.0
    revenue = revenue.lower().replace(",", "").replace("$", "").strip()
    ranges = {
        "under 1m": 500000, "<1m": 500000, "< $1m": 500000,
        "1m-5m": 3000000, "1-5m": 3000000, "$1m - $5m": 3000000,
        "5m-10m": 7500000, "5-10m": 7500000, "$5m - $10m": 7500000,
        "10m-50m": 30000000, "10-50m": 30000000, "$10m - $50m": 30000000,
        "50m-100m": 75000000, "50-100m": 75000000,
        "100m+": 150000000, ">100m": 150000000, "over 100m": 150000000,
    }
    if revenue in ranges:
        return ranges[revenue]
    for key, val in ranges.items():
        if key in revenue:
            return val
    try:
        return float(revenue)
    except ValueError:
        return 50000.0


def predict_forecast_close_date(lead: Any) -> Optional[str]:
    prob = calculate_closure_probability(lead)
    if prob < 0.1:
        return None
    days = int((1 - prob) * 180)
    forecast_date = datetime.utcnow() + timedelta(days=days)
    return forecast_date.strftime("%Y-%m-%d")


def train_model(leads: list) -> Dict[str, Any]:
    model, scaler = _get_model()
    X_list = []
    y_list = []
    for lead in leads:
        features = _extract_features(lead).flatten()
        X_list.append(features)
        y_list.append(1 if getattr(lead, "converted", False) else 0)
    if len(set(y_list)) < 2:
        return {"status": "skipped", "reason": "need both converted and unconverted leads", "samples": len(y_list)}
    X = np.array(X_list)
    y = np.array(y_list)
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    accuracy = model.score(X_scaled, y)
    return {"status": "trained", "samples": len(y), "accuracy": round(float(accuracy), 4)}
