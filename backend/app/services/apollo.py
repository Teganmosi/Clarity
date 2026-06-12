import os
from typing import Optional, Dict, Any, List
from .base_client import BaseAPIClient


class ApolloService(BaseAPIClient):
    def __init__(self):
        api_key = os.getenv("APOLLO_API_KEY", "")
        super().__init__("https://api.apollo.io/v1", api_key, rate_limit=50)

    async def search_people(
        self,
        organization_domains: List[str] = None,
        person_titles: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        payload = {
            "organization_domains": organization_domains or [],
            "person_titles": person_titles or [],
            "per_page": min(limit, 50)
        }
        result = await self.request("POST", "/mixed_people/search", json=payload)
        if result and "people" in result:
            return [self._normalize_person(p) for p in result["people"]]
        return []

    async def get_organization(self, domain: str) -> Optional[Dict[str, Any]]:
        result = await self.request("GET", f"/organizations/{domain}")
        return self._normalize_organization(result) if result else None

    def _normalize_person(self, data: Dict) -> Dict[str, Any]:
        return {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "title": data.get("title"),
            "linkedin_url": data.get("linkedin_url"),
            "phone_numbers": data.get("phone_numbers", []),
            "organization_name": data.get("organization", {}).get("name"),
        }

    def _normalize_organization(self, data: Dict) -> Dict[str, Any]:
        return {
            "name": data.get("name"),
            "domain": data.get("website_url"),
            "industry": data.get("industry"),
            "employee_count": data.get("employee_count"),
            "revenue": data.get("revenue"),
            "headquarters_location": data.get("city"),
            "country": data.get("country"),
            "linkedin_url": data.get("linkedin_url"),
        }
