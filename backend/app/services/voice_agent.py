import os
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

MOCK_CALL_SCRIPTS = {
    "en": "Hi {name}, this is an AI assistant from Clarity. I'm calling because we noticed {company} has shown strong interest in AI-powered lead scoring. I'd love to learn more about your current process. Do you have a few minutes to chat?",
    "es": "Hola {name}, soy un asistente de Clarity. Lo llamo porque notamos que {company} ha mostrado gran interés en la puntuación de leads con IA. ¿Tiene unos minutos para conversar?",
    "fr": "Bonjour {name}, je suis un assistant de Clarity. Je vous appelle car {company} a montré un fort intérêt pour le scoring de leads IA. Avez-vous quelques minutes pour discuter?",
    "de": "Hallo {name}, ich bin ein KI-Assistent von Clarity. Ich rufe an, weil {company} starkes Interesse an KI-gestütztem Lead-Scoring gezeigt hat. Haben Sie ein paar Minuten Zeit?",
}

MOCK_TRANSCRIPTS = [
    "Hi, thanks for calling. I'm interested in learning more about your platform.",
    "We've been looking for a better way to score our leads. What makes you different?",
    "Our team is currently using manual processes. How quickly can you get us set up?",
    "I'm not the decision maker, but I can connect you with our VP of Sales.",
    "This sounds interesting. Can you send me some more information?",
]


async def initiate_call(lead_id: int, phone_number: str, lead_name: str = "",
                        company: str = "", language: str = "en") -> Dict[str, Any]:
    call_id = random.randint(100000, 999999)

    script = MOCK_CALL_SCRIPTS.get(language, MOCK_CALL_SCRIPTS["en"])
    script = script.format(name=lead_name or "there", company=company or "your company")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    if account_sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            call = client.calls.create(
                to=phone_number,
                from_=from_number,
                twiml=f"<Response><Say>{script}</Say></Response>",
            )
            return {
                "call_id": call_id,
                "twilio_sid": call.sid,
                "status": "initiated",
                "script": script,
                "mocked": False,
            }
        except Exception as e:
            logger.warning(f"Twilio call failed (will mock): {e}")

    logger.info(f"[Voice Mock] Call {call_id} to {phone_number} for lead {lead_id}")
    return {
        "call_id": call_id,
        "status": "initiated",
        "script": script,
        "mocked": True,
    }


async def process_voice_transcript(transcript: str) -> Dict[str, Any]:
    from ..services.conversation_engine import analyze_sentiment, extract_bant_scores

    sentiment = analyze_sentiment(transcript)
    messages = [{"role": "user", "content": transcript}]
    bant = extract_bant_scores(messages)

    return {
        "sentiment": sentiment,
        "bant": bant,
        "transcript": transcript,
        "summary": _summarize_transcript(transcript, bant, sentiment),
    }


async def generate_voice_response(text: str) -> str:
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")

    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=nvidia_key, base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"))
            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=[{"role": "user", "content": f"Convert this to a short, natural-sounding voice response (max 2 sentences): {text}"}],
                max_tokens=100,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    return text[:200]


def _summarize_transcript(transcript: str, bant: dict, sentiment: dict) -> str:
    intent = "interested" if bant.get("need", 5) >= 7 else "moderately interested" if bant.get("need", 5) >= 4 else "not very interested"
    authority = "decision maker" if bant.get("authority") == "DM" else "influencer" if bant.get("authority") == "Influencer" else "unknown role"
    return f"Lead appears {intent} ({authority}). Sentiment: {sentiment.get('label', 'neutral')}."
