# Technical Specification: Sprint 1 - Agentic Core & Data Enrichment

## 1. Objective
Establish the foundational architecture for the multi-agent sales system. This includes creating the base agent framework, setting up the event-driven communication backbone, and implementing the first data enrichment integration (Apollo/Clearbit).

## 2. Architecture Overview
- **Pattern**: Event-Driven Microservices with a Central Orchestrator.
- **Language**: Python 3.10+
- **Core Libraries**: 
  - `langchain` (for agent reasoning and tool binding)
  - `celery` + `redis` (for asynchronous task queues)
  - `pydantic` (for strict data validation)
  - `httpx` (for async API calls)
- **Database**: PostgreSQL (relational data) + Pinecone/Weaviate (vector memory for agents).

## 3. Directory Structure
Create the following structure in `/workspace`:
```
sales_agentic_core/
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point & FastAPI app
│   ├── config.py              # Environment variables & settings
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Abstract Base Class for all agents
│   │   ├── orchestrator.py    # Central brain for task delegation
│   │   └── memory.py          # Vector store interface for long-term memory
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── researcher.py      # Specific implementation: Data Enrichment Agent
│   │   └── outreach.py        # Placeholder: Future Outreach Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── apollo_api.py      # Apollo Integration Tool
│   │   └── clearbit_api.py    # Clearbit Integration Tool (Placeholder)
│   ├── models/
│   │   ├── __init__.py
│   │   └── lead.py            # Pydantic models for Lead data
│   └── tasks/
│       ├── __init__.py
│       └── celery_worker.py   # Celery configuration
├── tests/
│   ├── __init__.py
│   └── test_researcher_agent.py
├── .env.example
├── requirements.txt
└── README.md
```

## 4. Implementation Details

### A. Configuration (`app/config.py`)
- Load environment variables: `APOLLO_API_KEY`, `CLEARBIT_API_KEY`, `REDIS_URL`, `DATABASE_URL`, `LLM_MODEL_NAME`.
- Use `pydantic-settings` for validation.

### B. Base Agent Class (`app/core/base_agent.py`)
- Define an abstract class `BaseAgent`.
- Must include methods: `plan()`, `act()`, `observe()`, and `execute_tool()`.
- Integrate with LangChain's `AgentExecutor` pattern but allow for custom state management.
- Include a `memory` attribute to store conversation history and context.

### C. Data Models (`app/models/lead.py`)
- Create a `Lead` Pydantic model with fields:
  - `id`: UUID
  - `email`: str
  - `full_name`: str
  - `company_name`: str
  - `job_title`: str
  - `enriched_data`: dict (JSON for flexible API responses)
  - `intent_score`: float (0.0 - 1.0)
  - `last_updated`: datetime

### D. Tool Implementation: Apollo API (`app/tools/apollo_api.py`)
- Create a class `ApolloTool`.
- Method `search_people(keywords: str, limit: int) -> List[Lead]`:
  - Construct HTTP GET request to Apollo's `/people/search` endpoint.
  - Handle pagination and rate limiting (429 errors).
  - Map raw JSON response to the `Lead` Pydantic model.
- Method `get_person_details(person_id: str) -> Lead`:
  - Fetch detailed profile data.

### E. Researcher Agent (`app/agents/researcher.py`)
- Inherit from `BaseAgent`.
- Bind the `ApolloTool` to this agent.
- Define a specific prompt: "You are a Sales Researcher. Your goal is to find high-quality leads based on user criteria and enrich their profiles with firmographic data."
- Implement logic to:
  1. Accept a search query (e.g., "CTOs in Fintech startups").
  2. Call `ApolloTool.search_people`.
  3. Iterate through results and call `ApolloTool.get_person_details` for deep enrichment.
  4. Save enriched leads to the database (mock this for now if DB isn't ready).

### F. Orchestrator (`app/core/orchestrator.py`)
- Create a simple `Orchestrator` class.
- Method `assign_task(task_description: str)`:
  - Parse intent (use a simple LLM call to route to 'researcher' or 'outreach').
  - Instantiate the correct agent.
  - Return the agent's result.

### G. Async Task Queue (`app/tasks/celery_worker.py`)
- Configure Celery with Redis as the broker.
- Create a task `run_research_agent(query: str)` that wraps the Researcher Agent's execution.
- This ensures long-running searches don't block the API.

## 5. Deliverables Checklist
- [ ] Complete directory structure created.
- [ ] `requirements.txt` with all necessary dependencies.
- [ ] `.env.example` with placeholder keys.
- [ ] Functional `BaseAgent` class.
- [ ] Functional `ApolloTool` with error handling.
- [ ] `ResearcherAgent` capable of executing a search and returning structured `Lead` objects.
- [ ] Basic unit tests for the `ApolloTool` and `Lead` model.
- [ ] A `main.py` script that demonstrates: "User inputs query -> Orchestrator routes to Researcher -> Apollo API called -> Enriched Leads printed."

## 6. Constraints & Best Practices
- **Type Safety**: Strict typing using Python type hints everywhere.
- **Error Handling**: All API calls must have `try/except` blocks with specific logging.
- **Secrets Management**: Never hardcode API keys; use `os.getenv`.
- **Modularity**: Tools must be decoupled from Agents so they can be swapped easily later.

---
**Instruction to Coding Agent:**
Please generate the code files according to this specification. Start with the directory structure and `requirements.txt`, then move to the core classes, tools, and finally the agent implementation. Ensure all code is production-ready with docstrings and error handling. Report back once the initial scaffold and the `ResearcherAgent` demonstration script are complete.
