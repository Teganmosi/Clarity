import os
import logging
import json
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

COMPETITOR_BATTLE_CARDS = {
    "hubspot": {
        "strengths": ["Strong CRM ecosystem", "Large marketplace", "Brand recognition"],
        "weaknesses": ["Expensive per-seat pricing", "Limited native AI lead scoring", "Complex setup"],
        "our_advantage": "Clarity's intent detection and predictive scoring are purpose-built for SMB sales, not bolted onto a CRM. We deliver actionable insights in days, not months.",
        "objection_handling": "HubSpot is great for CRM, but their lead scoring is basic. Clarity gives you AI-powered intent signals, BANT qualification, and automated outreach natively.",
    },
    "salesforce": {
        "strengths": ["Enterprise grade", "Massive ecosystem", "Deep customization"],
        "weaknesses": ["Extremely expensive", "Requires admin team", "6+ month deployment"],
        "our_advantage": "Clarity delivers 80% of the value at 20% of the cost. No admin needed — set up in under a week.",
        "objection_handling": "Salesforce is for enterprises with dedicated admins. Clarity is built for teams that need AI-powered sales acceleration without the overhead.",
    },
    "zoominfo": {
        "strengths": ["Large B2B database", "Good contact data"],
        "weaknesses": ["No scoring intelligence", "Just data, no action", "Static profiles"],
        "our_advantage": "ZoomInfo gives you data. Clarity gives you intelligence — intent signals, predictive scoring, and automated multi-channel outreach on top of enriched data.",
        "objection_handling": "ZoomInfo is a data source. Clarity is an AI sales agent that enriches, scores, and reaches out automatically. We complement each other.",
    },
    "outreach": {
        "strengths": ["Sales engagement leader", "Sequences and cadences", "Analytics"],
        "weaknesses": ["No lead scoring", "Requires manual list building", "No intent data"],
        "our_advantage": "Outreach sequences the outreach. Clarity decides who to reach out to, when, and with what message — powered by real-time intent signals.",
        "objection_handling": "Outreach is great once you know who to contact. Clarity tells you exactly which leads are hot right now and why.",
    },
}


def get_battle_card(competitor_name: str) -> Dict[str, Any]:
    name_lower = competitor_name.lower().strip()
    for key, card in COMPETITOR_BATTLE_CARDS.items():
        if key in name_lower or name_lower in key:
            return {"competitor": key, **card}
    return {
        "competitor": competitor_name,
        "strengths": [],
        "weaknesses": ["Not specifically profiled"],
        "our_advantage": "Clarity's unique advantage is our end-to-end AI pipeline: enrichment → intent detection → predictive scoring → automated outreach → meeting scheduling.",
        "objection_handling": f"While I'm not intimately familiar with every detail of {competitor_name}, I know Clarity's core differentiator is our unified AI approach that connects data to action.",
    }


async def generate_one_pager(lead_context: Dict[str, Any]) -> Dict[str, str]:
    client = None
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=nvidia_key, base_url=nvidia_base)
        except Exception:
            pass

    if client:
        try:
            prompt = f"""Generate a concise one-page sales summary for {lead_context.get('name', 'a prospect')} at {lead_context.get('company', 'their company')}.

Context:
- Role: {lead_context.get('title', 'Unknown')}
- Tech Stack: {lead_context.get('tech_stack', 'Unknown')}
- Funding: {lead_context.get('funding_stage', 'Unknown')}
- Employees: {lead_context.get('employee_count', 'Unknown')}
- Industry: {lead_context.get('industry', 'Unknown')}

Format as markdown with sections:
1. Executive Summary
2. Why They Need AI Lead Scoring
3. How Clarity Fits Their Stack
4. Recommended Approach
5. Expected Outcomes

Keep it to one page, professional, and specific to their context."""

            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            return {"markdown": content, "source": "ai"}
        except Exception as e:
            logger.warning(f"AI content generation failed: {e}")

    return {"markdown": _template_one_pager(lead_context), "source": "template"}


def _template_one_pager(ctx: Dict) -> str:
    name = ctx.get("name", "Prospect")
    company = ctx.get("company", "the Company")
    title = ctx.get("title", "their role")
    tech = ctx.get("tech_stack", "various technologies")
    funding = ctx.get("funding_stage", "current stage")
    employees = ctx.get("employee_count", "a growing team")
    industry = ctx.get("industry", "their industry")

    return f"""# Clarity Opportunity Summary: {company}

## 1. Executive Summary
{name}, {title} at {company} ({industry}, {employees} employees, {funding}) represents a strong fit for Clarity's AI-powered sales platform.

## 2. Why They Need AI Lead Scoring
With a team of {employees} and operating in the {industry} space, {company} likely faces challenges prioritizing leads and identifying the highest-value opportunities. Our platform addresses this with intent detection and predictive scoring.

## 3. How Clarity Fits Their Stack
Their current tech stack includes {tech}. Clarity integrates seamlessly via API and enriches existing CRM data without requiring a migration.

## 4. Recommended Approach
Start with a pilot focused on their top-priority accounts. Our onboarding takes less than a week and delivers actionable insights immediately.

## 5. Expected Outcomes
- 3x increase in lead-to-meeting conversion
- 60% reduction in time spent scoring leads manually
- Clear visibility into buying intent across the pipeline
"""
