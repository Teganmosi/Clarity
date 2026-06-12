# 🏃 Sprint 1 Quick-Start Guide
## API Integration Framework - Implementation Checklist

**Duration:** 2 weeks  
**Goal:** Build scalable API integration layer with Clearbit/Apollo enrichment

---

## 📁 Step 1: Project Structure Setup

### Create New Directories
```bash
cd /workspace/backend
mkdir -p app/services
mkdir -p app/agents
mkdir -p app/tasks
touch app/services/__init__.py
touch app/agents/__init__.py
touch app/tasks/__init__.py
```

### Updated Backend Structure
```
backend/
├── app/
│   ├── services/           # NEW: External API integrations
│   │   ├── __init__.py
│   │   ├── base_client.py  # Base API client with retry/rate-limiting
│   │   ├── clearbit.py     # Clearbit integration
│   │   ├── apollo.py       # Apollo integration
│   │   └── crunchbase.py   # Crunchbase integration
│   ├── agents/             # NEW: Future agent framework
│   │   └── __init__.py
│   ├── tasks/              # NEW: Celery tasks
│   │   └── __init__.py
│   ├── routers/
│   ├── models.py           # Will add new fields
│   ├── schemas.py          # Will add new schemas
│   └── main.py
├── requirements.txt        # Will add new dependencies
└── .env                    # Will add API keys
```

---

## 📦 Step 2: Install Dependencies

### Update requirements.txt
Add these lines to `/workspace/backend/requirements.txt`:

```txt
# API Clients
httpx==0.25.2
tenacity==8.2.3
redis==5.0.1
celery==5.3.4

# Data Enrichment
clearbit==0.2.2

# Environment
python-dotenv==1.0.0
```

### Install
```bash
cd /workspace/backend
pip install -r requirements.txt
```

---

## 🔧 Step 3: Environment Configuration

### Update .env File
Add to your backend `.env` file:

```env
# Data Enrichment APIs
CLEARBIT_API_KEY=your_clearbit_key_here
APOLLO_API_KEY=your_apollo_key_here
CRUNCHBASE_API_KEY=your_crunchbase_key_here

# Job Queue
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Rate Limiting (requests per minute)
CLEARBIT_RATE_LIMIT=100
APOLLO_RATE_LIMIT=50
CRUNCHBASE_RATE_LIMIT=30
```

---

## 💻 Step 4: Core Implementation Files

### File 1: Base API Client (`app/services/base_client.py`)

```python
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, Any
import time
from collections import deque

class RateLimiter:
    def __init__(self, rate_limit: int):
        self.rate_limit = rate_limit
        self.calls = deque()
    
    async def acquire(self):
        now = time.time()
        # Remove calls older than 1 minute
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        
        if len(self.calls) >= self.rate_limit:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.calls.append(time.time())

class BaseAPIClient:
    def __init__(self, base_url: str, api_key: str, rate_limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        await self.rate_limiter.acquire()
        
        try:
            response = await self.client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Clarity-Sales-Platform/1.0"
        }
    
    async def close(self):
        await self.client.aclose()
```

### File 2: Clearbit Service (`app/services/clearbit.py`)

```python
from typing import Optional, Dict, Any
from .base_client import BaseAPIClient
import os

class ClearbitService(BaseAPIClient):
    def __init__(self):
        api_key = os.getenv("CLEARBIT_API_KEY")
        super().__init__("https://company.clearbit.com/v2", api_key, rate_limit=100)
    
    async def enrich_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich company data by domain"""
        result = await self.request("GET", f"/companies/find?domain={domain}")
        return self._normalize_company_data(result) if result else None
    
    async def enrich_person(self, email: str) -> Optional[Dict[str, Any]]:
        """Enrich person data by email"""
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
```

### File 3: Apollo Service (`app/services/apollo.py`)

```python
from typing import Optional, Dict, Any, List
from .base_client import BaseAPIClient
import os

class ApolloService(BaseAPIClient):
    def __init__(self):
        api_key = os.getenv("APOLLO_API_KEY")
        super().__init__("https://api.apollo.io/v1", api_key, rate_limit=50)
    
    async def search_people(self, 
                           organization_domains: List[str] = None,
                           person_titles: List[str] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Search for people based on criteria"""
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
        """Get organization details"""
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
            "location": data.get("city"),
            "country": data.get("country"),
            "linkedin_url": data.get("linkedin_url"),
        }
```

### File 4: Update Database Models (`app/models.py`)

Add these fields to the Lead model:

```python
# Add to existing Lead model in models.py

# Enrichment Data
technologies = Column(JSON, default=list)  # Tech stack
funding_stage = Column(String)  # Seed, Series A, etc.
funding_amount = Column(Integer)  # Total funding
employee_count = Column(Integer)
industry = Column(String)
company_description = Column(Text)
logo_url = Column(String)
linkedin_url = Column(String)
twitter_url = Column(String)

# Intent Signals
intent_score = Column(Integer, default=0)
intent_signals = Column(JSON, default=list)  # List of detected signals
last_intent_update = Column(DateTime)

# Enrichment Metadata
enriched_at = Column(DateTime)
enrichment_source = Column(String)  # clearbit, apollo, etc.
enrichment_data = Column(JSON, default=dict)  # Raw enrichment data
```

### File 5: Update Schemas (`app/schemas.py`)

Add new schemas:

```python
# Add to schemas.py

class LeadEnrichmentBase(BaseModel):
    technologies: Optional[List[str]] = []
    funding_stage: Optional[str] = None
    funding_amount: Optional[int] = None
    employee_count: Optional[int] = None
    industry: Optional[str] = None
    company_description: Optional[str] = None
    logo_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    intent_score: Optional[int] = 0
    intent_signals: Optional[List[dict]] = []

class LeadEnrichmentCreate(LeadEnrichmentBase):
    pass

class LeadWithEnrichment(LeadBase, LeadEnrichmentBase):
    id: int
    score: float
    category: str
    enriched_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

### File 6: Enrichment Router (`app/routers/enrichment.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Lead
from ..schemas import LeadWithEnrichment
from ..services.clearbit import ClearbitService
from ..services.apollo import ApolloService

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

@router.post("/{lead_id}/enrich")
async def enrich_lead(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger enrichment for a specific lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Run enrichment in background
    background_tasks.add_task(run_enrichment, lead_id, db)
    
    return {"message": "Enrichment started", "lead_id": lead_id}

@router.post("/bulk/enrich")
async def bulk_enrich(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Enrich all leads that haven't been enriched yet"""
    leads = db.query(Lead).filter(Lead.enriched_at == None).limit(100).all()
    
    for lead in leads:
        background_tasks.add_task(run_enrichment, lead.id, db)
    
    return {"message": f"Started enrichment for {len(leads)} leads"}

async def run_enrichment(lead_id: int, db: Session):
    """Actual enrichment logic"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return
    
    clearbit = ClearbitService()
    apollo = ApolloService()
    
    # Extract domain from email
    domain = lead.email.split("@")[1] if "@" in lead.email else None
    if not domain:
        return
    
    # Enrich company data
    company_data = await clearbit.enrich_company(domain)
    if company_data:
        for key, value in company_data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
    
    # Enrich person data
    if lead.email:
        person_data = await clearbit.enrich_person(lead.email)
        if person_data:
            # Update lead with person data
            if person_data.get("title") and not lead.job_title:
                lead.job_title = person_data["title"]
    
    # Mark as enriched
    from datetime import datetime
    lead.enriched_at = datetime.utcnow()
    lead.enrichment_source = "clearbit"
    
    db.commit()
    
    await clearbit.close()
    await apollo.close()
```

### File 7: Register Router in main.py

```python
# Add to app/main.py
from .routers import enrichment

app.include_router(enrichment.router)
```

---

## 🧪 Step 5: Testing

### Create Test File (`test_enrichment.py`)

```python
import asyncio
from app.services.clearbit import ClearbitService
from app.services.apollo import ApolloService

async def test_clearbit():
    service = ClearbitService()
    
    # Test company enrichment
    company = await service.enrich_company("stripe.com")
    print("Company:", company)
    
    # Test person enrichment
    person = await service.enrich_person("patrick@stripe.com")
    print("Person:", person)
    
    await service.close()

async def test_apollo():
    service = ApolloService()
    
    # Search people
    people = await service.search_people(
        organization_domains=["stripe.com"],
        person_titles=["CEO", "CTO"],
        limit=5
    )
    print("People:", people)
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_clearbit())
    asyncio.run(test_apollo())
```

---

## ✅ Step 6: Sprint 1 Acceptance Criteria

- [ ] Clearbit API integration working
- [ ] Apollo API integration working
- [ ] Rate limiting implemented correctly
- [ ] Retry logic with exponential backoff
- [ ] New database fields added and migrated
- [ ] Enrichment endpoint functional
- [ ] Background task processing setup
- [ ] Frontend displays enriched data
- [ ] Manual enrichment trigger works
- [ ] Auto-enrichment on upload works

---

## 🚀 Quick Commands

### Start Redis (for job queue)
```bash
docker run -d -p 6379:6379 redis:latest
```

### Run Backend
```bash
cd /workspace/backend
python -m uvicorn app.main:app --reload
```

### Test Enrichment
```bash
curl -X POST http://localhost:8000/enrichment/1/enrich
```

### Check API Docs
Visit: http://localhost:8000/docs

---

## 📚 Resources

- **Clearbit API Docs:** https://dashboard.clearbit.com/docs
- **Apollo API Docs:** https://www.apollo.io/api-documentation
- **FastAPI Background Tasks:** https://fastapi.tiangolo.com/tutorial/background-tasks/
- **HTTPX Documentation:** https://www.python-httpx.org/

---

## 🎯 Next Steps After Sprint 1

1. Monitor API usage and costs
2. Collect feedback on data quality
3. Plan Sprint 2 (Intent Detection)
4. Set up analytics dashboard for enrichment metrics
5. Document learnings and best practices

**Good luck with Sprint 1! 🚀**
