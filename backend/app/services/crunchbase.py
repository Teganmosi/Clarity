import os
from typing import Optional, Dict, Any
from .base_client import BaseAPIClient


class CrunchbaseService(BaseAPIClient):
    def __init__(self):
        api_key = os.getenv("CRUNCHBASE_API_KEY", "")
        super().__init__("https://api.crunchbase.com/v3.1", api_key, rate_limit=30)

    async def get_organization(self, domain: str) -> Optional[Dict[str, Any]]:
        result = await self.request("GET", f"/odm-organizations?domain={domain}")
        return self._normalize_organization(result) if result else None

    async def get_funding_rounds(self, organization_id: str) -> Optional[Dict[str, Any]]:
        result = await self.request("GET", f"/odm-funding-rounds?organization_id={organization_id}")
        return result

    def _normalize_organization(self, data: Dict) -> Dict[str, Any]:
        properties = data.get("properties", {})
        return {
            "name": properties.get("name"),
            "domain": properties.get("domain"),
            "founded_year": properties.get("founded_on", "").split("-")[0] if properties.get("founded_on") else None,
            "employee_count": properties.get("num_employees_min"),
            "funding_stage": properties.get("went_public_on") and "Public" or properties.get("last_funding_type"),
            "headquarters_location": properties.get("city"),
            "linkedin_url": properties.get("linkedin_url"),
            "twitter_handle": properties.get("twitter_url", "").split("/")[-1] if properties.get("twitter_url") else None,
        }
