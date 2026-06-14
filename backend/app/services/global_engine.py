import os
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

LANG_KEYWORDS = {
    "es": ["hola", "gracias", "por favor", "buenos días", "español", "señor", "señora", "muchas gracias", "adiós", "qué tal", "estoy", "somos", "empresa"],
    "fr": ["bonjour", "merci", "s'il vous plaît", "monsieur", "madame", "entreprise", "nous sommes", "je suis", "très bien", "d'accord"],
    "de": ["hallo", "danke", "bitte", "herr", "frau", "unternehmen", "wir sind", "ich bin", "sehr gut", "natürlich", "guten tag"],
    "ja": ["ありがとう", "こんにちは", "お願いします", "さん", "様", "株式会社", "弊社", "です", "ます", "よろしく"],
    "pt": ["olá", "obrigado", "por favor", "senhor", "senhora", "empresa", "nós somos", "eu sou", "muito bom", "obrigada"],
    "it": ["ciao", "grazie", "per favore", "signore", "signora", "azienda", "noi siamo", "io sono", "molto bene", "d'accordo"],
    "nl": ["hallo", "dank u", "alsjeblieft", "meneer", "mevrouw", "bedrijf", "wij zijn", "ik ben", "heel goed", "akkoord"],
    "zh": ["你好", "谢谢", "请", "先生", "女士", "公司", "我们", "我是", "很好", "好的"],
}

COMPLIANCE_RULES = {
    "EU": {"gdpr": True, "ccpa": False, "lgpd": False, "opt_out_required": True, "data_retention_days": 365, "requires_consent": True},
    "GB": {"gdpr": True, "ccpa": False, "lgpd": False, "opt_out_required": True, "data_retention_days": 365, "requires_consent": True},
    "US-CA": {"gdpr": False, "ccpa": True, "lgpd": False, "opt_out_required": True, "data_retention_days": 730, "requires_consent": False},
    "BR": {"gdpr": False, "ccpa": False, "lgpd": True, "opt_out_required": True, "data_retention_days": 365, "requires_consent": True},
    "default": {"gdpr": False, "ccpa": False, "lgpd": False, "opt_out_required": False, "data_retention_days": 730, "requires_consent": False},
}

CURRENCY_FORMATS = {
    "USD": {"symbol": "$", "code": "USD", "locale": "en-US"},
    "EUR": {"symbol": "€", "code": "EUR", "locale": "de-DE"},
    "GBP": {"symbol": "£", "code": "GBP", "locale": "en-GB"},
    "JPY": {"symbol": "¥", "code": "JPY", "locale": "ja-JP"},
    "BRL": {"symbol": "R$", "code": "BRL", "locale": "pt-BR"},
    "CAD": {"symbol": "C$", "code": "CAD", "locale": "en-CA"},
    "AUD": {"symbol": "A$", "code": "AUD", "locale": "en-AU"},
    "MXN": {"symbol": "MX$", "code": "MXN", "locale": "es-MX"},
}

REGION_CURRENCIES = {
    "US": "USD", "CA": "CAD", "GB": "GBP", "DE": "EUR", "FR": "EUR", "IT": "EUR",
    "ES": "EUR", "NL": "EUR", "BR": "BRL", "JP": "JPY", "AU": "AUD", "MX": "MXN",
    "IN": "INR", "CN": "CNY", "KR": "KRW", "SG": "SGD",
}


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "en"
    text_lower = text.lower().strip()
    scores = {}
    for lang, keywords in LANG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[lang] = score
    if not scores:
        return "en"
    return max(scores, key=scores.get)


async def translate_text(text: str, target_lang: str) -> str:
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=nvidia_key, base_url=nvidia_base)
            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=[
                    {"role": "system", "content": f"Translate the following text to {target_lang}. Return only the translated text, no explanations."},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Translation failed: {e}")

    fallback_translations = {
        "es": {"Hello": "Hola", "Thank you": "Gracias", "How are you?": "¿Cómo está?", "Best regards": "Saludos cordiales"},
        "fr": {"Hello": "Bonjour", "Thank you": "Merci", "How are you?": "Comment allez-vous?", "Best regards": "Cordialement"},
        "de": {"Hello": "Hallo", "Thank you": "Danke", "How are you?": "Wie geht es Ihnen?", "Best regards": "Mit freundlichen Grüßen"},
    }
    if target_lang in fallback_translations:
        for en, translated in fallback_translations[target_lang].items():
            text = text.replace(en, translated)
    return text + f" [{target_lang}]"


def check_compliance(location: str) -> Dict[str, Any]:
    if not location:
        return COMPLIANCE_RULES["default"]
    loc_upper = location.upper().strip()

    for region_key in ["EU", "GB", "US-CA", "BR"]:
        if region_key in loc_upper or (region_key == "EU" and any(c in loc_upper for c in ["EU", "FR", "DE", "IT", "ES", "NL", "BE", "AT", "PT", "IE", "DK", "SE", "FI", "PL", "CZ", "HU", "RO", "GR", "SK", "BG", "HR", "LT", "SI", "LV", "EE", "MT", "LU", "CY"])):
            return COMPLIANCE_RULES[region_key]
        if region_key == "US-CA" and ("CA" in loc_upper or "CALIFORNIA" in loc_upper):
            return COMPLIANCE_RULES["US-CA"]

    return COMPLIANCE_RULES["default"]


def detect_region_from_phone(phone: str) -> str:
    if not phone:
        return "US"
    phone = phone.strip()
    prefix_map = {"+1": "US", "+44": "GB", "+49": "DE", "+33": "FR", "+39": "IT",
                  "+34": "ES", "+31": "NL", "+55": "BR", "+81": "JP", "+61": "AU",
                  "+52": "MX", "+91": "IN", "+86": "CN", "+82": "KR", "+65": "SG"}
    for prefix, region in prefix_map.items():
        if phone.startswith(prefix):
            return region
    return "US"


def format_currency(amount: float, currency_code: str = "USD") -> str:
    fmt = CURRENCY_FORMATS.get(currency_code.upper(), CURRENCY_FORMATS["USD"])
    if currency_code.upper() == "JPY":
        return f"{fmt['symbol']}{int(amount):,}"
    return f"{fmt['symbol']}{amount:,.2f}"


def get_region_currency(region: str) -> str:
    return REGION_CURRENCIES.get(region.upper(), "USD")
