import os
from typing import Optional, Dict, Any
from .base_client import BaseAPIClient


class ClearbitService(BaseAPIClient):
    def __init__(self):
        api_key = os.getenv("CLEARBIT_API_KEY", "")
        super().__init__("https://company.clearbit.com/v2", api_key, rate_limit=100)

    async def enrich_company(self, domain: str) -> Optional[Dict[str, Any]]:
        result = await self.request("GET", f"/companies/find?domain={domain}")
        return self._normalize_company_data(result) if result else None

    async def enrich_person(self, email: str) -> Optional[Dict[str, Any]]:
        result = await self.request("GET", f"/people/find?email={email}")
        return self._normalize_person_data(result) if result else None

    def _normalize_company_data(self, data: Dict) -> Dict[str, Any]:
        return {
            "technologies": data.get("tech", []),
            "funding_stage": data.get("metrics", {}).get("fundingStage"),
            "employee_count": data.get("metrics", {}).get("employees"),
            "logo_url": data.get("logo"),
            "linkedin_url": data.get("site", {}).get("linkedin", {}).get("handle"),
            "twitter_handle": data.get("site", {}).get("twitter", {}).get("handle"),
            "annual_revenue": data.get("metrics", {}).get("annualRevenue"),
            "headquarters_location": data.get("geo", {}).get("city"),
            "founded_year": data.get("foundedYear"),
            "industry_tags": [data.get("category", {}).get("industry")] if data.get("category", {}).get("industry") else [],
        }

    def _normalize_person_data(self, data: Dict) -> Dict[str, Any]:
        return {
            "full_name": data.get("name", {}).get("fullName"),
            "title": data.get("employment", {}).get("title"),
            "role": data.get("employment", {}).get("role"),
            "seniority": data.get("employment", {}).get("seniority"),
            "department": data.get("employment", {}).get("department"),
            "linkedin_url": data.get("bio", {}).get("site"),
            "phone": data.get("phone"),
        }
