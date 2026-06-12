import os
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
HANDOFF_THRESHOLD = float(os.getenv("CONVERSATION_HANDOFF_THRESHOLD", "7.0"))

_client = None

BANT_SYSTEM_PROMPT = """You are a senior B2B sales qualification bot. Your job is to qualify a lead using the BANT framework:
- **Budget**: What is their approximate budget? (High/Medium/Low/Unknown)
- **Authority**: Are they a decision-maker or influencer? (DM/Influencer/Unknown)
- **Need**: How strong is their need for a lead scoring / sales AI solution? (Score 1-10)
- **Timeline**: How soon do they plan to make a decision? (Days/Weeks/Months/Unknown)

RULES:
1. Ask ONE question at a time. Do not overwhelm the lead.
2. Probe naturally — weave BANT questions into the conversation.
3. Keep responses warm and professional (2-3 sentences max).
4. After every response, output a JSON BANT update inside <bant> tags.
5. If the lead seems frustrated or angry, flag it.
6. If BANT total score >= {} indicate handoff is recommended.

Format your response as:
<response>Your friendly message here.</response>
<bant>{{"budget": "High|Medium|Low|Unknown", "authority": "DM|Influencer|Unknown", "need": 0-10, "timeline": "Days|Weeks|Months|Unknown", "sentiment": "Positive|Neutral|Negative", "handoff": true|false}}</bant>
""".format(HANDOFF_THRESHOLD)

WELCOME_MESSAGE = {
    "role": "assistant",
    "content": "Hi there! Thanks for your interest in Clarity. I'd love to learn a bit more about your team to see if we're a good fit. What does your sales process look like right now?",
}


def _get_client():
    global _client
    if _client is None and NVIDIA_API_KEY:
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
        except Exception as e:
            logger.warning(f"Failed to init NVIDIA client: {e}")
    return _client


def analyze_sentiment(text: str) -> Dict[str, Any]:
    neg_words = ["angry", "frustrated", "terrible", "bad", "poor", "annoyed", "unhappy",
                 "disappointed", "useless", "waste", "hate", "awful", "horrible"]
    pos_words = ["great", "excellent", "interested", "love", "perfect", "amazing",
                 "helpful", "good", "fantastic", "wonderful", "yes", "sure", "thanks"]
    text_lower = text.lower()
    neg_count = sum(1 for w in neg_words if w in text_lower)
    pos_count = sum(1 for w in pos_words if w in text_lower)
    score = (pos_count - neg_count) / max(len(text.split()), 1) * 10
    score = max(-1.0, min(1.0, score))
    if score > 0.3:
        label = "Positive"
    elif score < -0.3:
        label = "Negative"
    else:
        label = "Neutral"
    return {"score": round(score, 2), "label": label}


def extract_bant_scores(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    all_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "assistant")
    bant_pattern = re.search(r'<bant>(.*?)</bant>', all_text, re.DOTALL)
    if bant_pattern:
        try:
            return json.loads(bant_pattern.group(1))
        except json.JSONDecodeError:
            pass

    text_lower = " ".join(m.get("content", "").lower() for m in messages)
    budget = "Unknown"
    if any(w in text_lower for w in ["budget is", "budget of", "spending", "$", "thousand", "million"]):
        budget = "High" if any(w in text_lower for w in ["million", "large", "significant"]) else "Medium"

    authority = "Unknown"
    if any(w in text_lower for w in ["i decide", "i'm the", "my team", "i am the", "ceo", "cto", "vp", "director", "head of"]):
        authority = "DM"
    elif any(w in text_lower for w in ["i'll check", "need to talk to", "my manager", "my boss"]):
        authority = "Influencer"

    need_score = 5
    if any(w in text_lower for w in ["need this", "urgent", "critical", "struggling", "problem", "challenge"]):
        need_score = 8
    if any(w in text_lower for w in ["not interested", "no need", "not a priority"]):
        need_score = 2

    timeline = "Unknown"
    if any(w in text_lower for w in ["this month", "this week", "asap", "urgent", "immediately", "right away"]):
        timeline = "Days"
    elif any(w in text_lower for w in ["next month", "few weeks", "coming weeks"]):
        timeline = "Weeks"
    elif any(w in text_lower for w in ["next quarter", "few months", "later this year"]):
        timeline = "Months"

    sentiment = analyze_sentiment(text_lower).get("label", "Neutral")

    return {
        "budget": budget,
        "authority": authority,
        "need": need_score,
        "timeline": timeline,
        "sentiment": sentiment,
        "handoff": False,
    }


def _calculate_bant_total(bant: Dict) -> float:
    budget_scores = {"High": 3, "Medium": 2, "Low": 1, "Unknown": 0}
    authority_scores = {"DM": 3, "Influencer": 2, "Unknown": 0}
    timeline_scores = {"Days": 3, "Weeks": 2, "Months": 1, "Unknown": 0}

    total = budget_scores.get(bant.get("budget", "Unknown"), 0)
    total += authority_scores.get(bant.get("authority", "Unknown"), 0)
    total += bant.get("need", 0)
    total += timeline_scores.get(bant.get("timeline", "Unknown"), 0)
    return total


def decide_handoff(bant: Dict) -> bool:
    total = _calculate_bant_total(bant)
    if total >= HANDOFF_THRESHOLD:
        return True
    if bant.get("sentiment") == "Negative":
        return True
    return False


def generate_response(messages: List[Dict[str, str]], lead_context: Dict) -> Dict[str, Any]:
    client = _get_client()
    system_prompt = BANT_SYSTEM_PROMPT

    context_lines = []
    if lead_context.get("name"):
        context_lines.append(f"Lead Name: {lead_context['name']}")
    if lead_context.get("company"):
        context_lines.append(f"Company: {lead_context['company']}")
    if lead_context.get("funding_stage"):
        context_lines.append(f"Funding: {lead_context['funding_stage']}")
    if lead_context.get("intent_score") is not None:
        context_lines.append(f"Intent Score: {lead_context['intent_score']}/100")
    if context_lines:
        system_prompt += "\n\nLEAD CONTEXT:\n" + "\n".join(context_lines)

    ai_messages = [{"role": "system", "content": system_prompt}]
    for m in messages[-10:]:
        ai_messages.append({"role": m["role"], "content": m["content"]})

    if client and NVIDIA_API_KEY:
        try:
            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=ai_messages,
                temperature=0.7,
                max_tokens=400,
            )
            content = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"NVIDIA call failed: {e}")
            content = _fallback_response(messages, lead_context)
    else:
        content = _fallback_response(messages, lead_context)

    response_text = ""
    bant_raw = "{}"
    resp_match = re.search(r'<response>(.*?)</response>', content, re.DOTALL)
    if resp_match:
        response_text = resp_match.group(1).strip()
    bant_match = re.search(r'<bant>(.*?)</bant>', content, re.DOTALL)
    if bant_match:
        bant_raw = bant_match.group(1).strip()

    try:
        bant = json.loads(bant_raw)
    except json.JSONDecodeError:
        bant = extract_bant_scores(messages + [{"role": "assistant", "content": content}])

    if not response_text:
        response_text = content.replace(bant_raw, "").replace("<bant>", "").replace("</bant>", "").replace("<response>", "").replace("</response>", "").strip()
        if not response_text:
            response_text = _fallback_response(messages, lead_context)

    handoff = decide_handoff(bant)
    total = _calculate_bant_total(bant)

    return {
        "response": response_text,
        "bant": bant,
        "bant_total": total,
        "handoff": handoff,
        "sentiment": bant.get("sentiment", "Neutral"),
    }


def _fallback_response(messages: List[Dict[str, str]], lead_context: Dict) -> str:
    user_msgs = [m for m in messages if m["role"] == "user"]
    last = user_msgs[-1]["content"].lower() if user_msgs else ""

    if any(w in last for w in ["budget", "cost", "price", "pricing"]):
        resp = "Our pricing is tiered based on team size and features. For a team of your size, I'd recommend starting with our Growth plan. Would you like me to walk you through the options?"
    elif any(w in last for w in ["who", "decision", "authority", "approve"]):
        resp = "That's a great question. Typically we work with sales leaders or revenue ops. Are you the primary decision-maker for sales tools at {company}?"
    elif any(w in last for w in ["need", "problem", "challenge", "struggling"]):
        resp = "I understand. Many teams face similar challenges with lead prioritization. What would solving this mean for your quarterly targets?"
    elif any(w in last for w in ["time", "timeline", "when", "how soon"]):
        resp = "Great question! Implementation typically takes 1-2 weeks. What timeline were you hoping for?"
    elif any(w in last for w in ["no", "not interested", "stop", "unsubscribe"]):
        resp = "No problem at all! I appreciate your time. If you ever want to revisit, feel free to reach out. Have a great day!"
    else:
        name = lead_context.get("name", "there")
        company = lead_context.get("company", "your company")
        resp = f"Thanks for sharing, {name}! At {company}, what does your current lead qualification process look like? Are you using any tools to score or prioritize leads?"

    bant = extract_bant_scores(messages + [{"role": "assistant", "content": resp}])
    handoff = "true" if decide_handoff(bant) else "false"
    return f"<response>{resp}</response>\n<bant>{json.dumps(bant)}</bant>"
