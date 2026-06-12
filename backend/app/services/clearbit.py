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
            "name": data.get("name"),
            "domain": data.get("domain"),
            "industry": data.get("category", {}).get("industry"),
            "employee_count": data.get("metrics", {}).get("employees"),
            "revenue": data.get("metrics", {}).get("annualRevenue"),
            "founded_year": data.get("foundedYear"),
            "location": data.get("geo", {}).get("city"),
            "country": data.get("geo", {}).get("country"),
            "technologies": data.get("tech", []),
            "description": data.get("bio"),
            "logo_url": data.get("logo"),
            "linkedin_url": data.get("site", {}).get("googleAnalyticsAccount"),
            "twitter_url": data.get("site", {}).get("twitterHandle"),
        }

    def _normalize_person_data(self, data: Dict) -> Dict[str, Any]:
        return {
            "full_name": data.get("name", {}).get("fullName"),
            "title": data.get("employment", {}).get("title"),
            "role": data.get("employment", {}).get("role"),
            "seniority": data.get("employment", {}).get("seniority"),
            "department": data.get("employment", {}).get("department"),
            "linkedin_url": data.get("bio", {}).get("site"),
            "twitter_url": data.get("bio", {}).get("twitterHandle"),
            "phone": data.get("phone"),
        }
