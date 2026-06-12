import os
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

_client = None


def _get_client():
    global _client
    if _client is None and NVIDIA_API_KEY:
        try:
            from openai import OpenAI
            _client = OpenAI(
                api_key=NVIDIA_API_KEY,
                base_url=NVIDIA_BASE_URL,
            )
            logger.info("NVIDIA NIM client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize NVIDIA client: {e}")
    return _client


def _build_context_prompt(lead: Any, intent_signals: List[Dict] = None, enrichment_data: Dict = None) -> str:
    signals = intent_signals or getattr(lead, "intent_signals", []) or []
    enrichment = enrichment_data or {}

    if not enrichment:
        fields = ["technologies", "funding_stage", "employee_count", "annual_revenue",
                   "industry_tags", "headquarters_location", "founded_year"]
        for f in fields:
            val = getattr(lead, f, None)
            if val is not None:
                enrichment[f] = val

    tech_stack = enrichment.get("technologies", [])
    tech_str = ", ".join(tech_stack[:5]) if isinstance(tech_stack, list) else str(tech_stack)
    industry_tags = enrichment.get("industry_tags", [])
    industry_str = ", ".join(industry_tags) if isinstance(industry_tags, list) else str(industry_tags)
    signal_str = "; ".join(
        f"{s.get('type', '').replace('_', ' ')} ({s.get('detail', '')})"
        for s in (signals or [])[:3]
    )

    name = getattr(lead, "name", "there")
    title = getattr(lead, "title", "")
    company = getattr(lead, "company", "their company")
    funding = enrichment.get("funding_stage", "")
    employees = enrichment.get("employee_count", "")
    revenue = enrichment.get("annual_revenue", "")
    hq = enrichment.get("headquarters_location", "")

    prompt = f"""You are a senior sales engineer writing a personalized cold email.

LEAD CONTEXT:
- Name: {name}
- Title: {title}
- Company: {company}
- Headquarters: {hq}

ENRICHMENT DATA:
- Tech Stack: {tech_str}
- Industry: {industry_str}
- Funding Stage: {funding}
- Employee Count: {employees}
- Annual Revenue: {revenue}

INTENT SIGNALS:
{signal_str if signal_str else "No specific recent signals detected."}

INSTRUCTIONS:
Write a personalized cold email that:
1. References the lead's company and role naturally
2. Leverages the enrichment data to show you've done research
3. Mentions relevant intent signals if available (e.g., recent funding, hiring)
4. Proposes a clear value proposition about improving their sales efficiency with AI-powered lead scoring
5. Ends with a specific, low-friction call to action

TONE: Professional, warm, concise (max 150 words).
OUTPUT FORMAT: Return a JSON object with keys "subject" and "body"."""
    return prompt


def _template_draft(lead: Any) -> Dict[str, str]:
    name = getattr(lead, "name", "there")
    company = getattr(lead, "company", "your company")
    title = getattr(lead, "title", "professional")
    funding = getattr(lead, "funding_stage", "")
    funding_line = f" I noticed {company} recently raised {funding} — congratulations on that milestone." if funding else ""
    tech = getattr(lead, "technologies", [])
    tech_line = f" I see you're using {', '.join(tech[:3])}." if isinstance(tech, list) and tech else ""

    body = f"""Hi {name},

I've been following {company}'s growth{funding_line}{tech_line}

At Clarity, we help sales teams like yours prioritize leads using AI-powered intent detection and predictive scoring — turning enriched data into actionable pipeline insights.

Would you be open to a brief 15-minute call next week to explore how this could fit into your workflow?

Best regards,
Sales Team
Clarity"""

    return {
        "subject": f"Quick idea for {company}'s sales pipeline",
        "body": body.strip(),
    }


async def generate_email_draft(lead: Any, intent_signals: List[Dict] = None, enrichment_data: Dict = None) -> Dict[str, Any]:
    client = _get_client()
    fallback = _template_draft(lead)

    if not client:
        logger.info("NVIDIA API key not configured, using template draft")
        return {
            "subject": fallback["subject"],
            "body": fallback["body"],
            "confidence_score": 0.5,
            "ai_model_used": "template",
        }

    prompt = _build_context_prompt(lead, intent_signals, enrichment_data)

    try:
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=[
                {"role": "system", "content": "You are a precise JSON generator. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            subject_match = re.search(r'"subject"\s*:\s*"([^"]+)"', content)
            body_match = re.search(r'"body"\s*:\s*"([^"]+)"', content)
            subject = subject_match.group(1) if subject_match else fallback["subject"]
            body = body_match.group(1) if body_match else fallback["body"]
            result = {"subject": subject, "body": body}

        confidence = 0.9 if result.get("subject") and result.get("body") and len(result.get("body", "")) > 50 else 0.6

        return {
            "subject": result.get("subject", fallback["subject"]),
            "body": result.get("body", fallback["body"]),
            "confidence_score": confidence,
            "ai_model_used": "nemotron-70b",
        }

    except Exception as e:
        logger.error(f"NVIDIA API call failed: {e}")
        return {
            "subject": fallback["subject"],
            "body": fallback["body"],
            "confidence_score": 0.5,
            "ai_model_used": "template-fallback",
        }


async def send_email(lead_id: int, subject: str, body: str, recipient_email: str, sender_email: str = None) -> Dict[str, Any]:
    try:
        import aiosmtplib
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if not smtp_user:
            logger.info(f"SMTP not configured, mocked send for lead {lead_id}")
            return {"status": "sent", "sent_at": datetime.utcnow().isoformat(), "mocked": True}

        message = f"Subject: {subject}\nTo: {recipient_email}\n\n{body}"
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        return {"status": "sent", "sent_at": datetime.utcnow().isoformat(), "mocked": False}

    except Exception as e:
        logger.error(f"Failed to send email for lead {lead_id}: {e}")
        return {"status": "failed", "error": str(e)}
