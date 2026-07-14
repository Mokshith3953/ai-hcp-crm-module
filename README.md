# AI-First HCP CRM Module — Log Interaction Screen

An AI-first CRM module for pharmaceutical field representatives to log,
edit, search, and summarize interactions with Healthcare Professionals
(HCPs) — either through a structured form or a conversational AI assistant.

## Live deployment

- **Frontend:** https://ai-hcp-crm-frontend.onrender.com
- **Backend API:** https://ai-hcp-crm-backend-y82n.onrender.com

Hosted on Render (free tier) from `render.yaml` — a Postgres database, the
FastAPI backend, and the React static site. The backend spins down after 15
minutes idle on the free tier, so the first request after inactivity can
take 30–50s to wake up.

## Tech stack

- **Frontend:** React + Redux Toolkit + Vite, Google Inter font
- **Backend:** Python + FastAPI
- **AI agent framework:** LangGraph (a `StateGraph` ReAct-style agent loop
  with tool-calling and per-conversation memory via `MemorySaver`)
- **LLM:** Groq — `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL`) using
  `langchain-groq`. The assignment's specified `gemma2-9b-it` model has since been
  **decommissioned by Groq** (confirmed against the live `/models` endpoint), so this
  project defaults to `llama-3.3-70b-versatile`, the alternative explicitly named in
  the assignment doc. Verified end-to-end against the real Groq API.
- **Database:** PostgreSQL via SQLAlchemy ORM (works unmodified against
  MySQL too by swapping the `DATABASE_URL` driver)

## Architecture

```
frontend/               React + Redux UI
backend/
  app/
    main.py             FastAPI app, CORS, router registration
    config.py            Settings (DATABASE_URL, GROQ_API_KEY, GROQ_MODEL)
    database.py          SQLAlchemy engine/session
    models.py             Interaction ORM model
    schemas.py            Pydantic request/response models
    crud.py                DB access helpers
    llm.py                  Groq ChatGroq client factory
    agent/
      tools.py             The 5 LangGraph tools
      graph.py              LangGraph StateGraph wiring the LLM + tools
    routes/
      interactions.py       REST CRUD for the structured form
      agent.py                Chat endpoint that invokes the LangGraph agent
docker-compose.yml        Local PostgreSQL for development
```

### The Log Interaction Screen

The screen exposes two ways to capture the same underlying data:

1. **Structured form** — HCP name, interaction type, date/time, attendees,
   topics discussed, materials shared, samples distributed, observed
   sentiment, outcomes, and follow-up actions (with an "AI Suggested
   Follow-ups" button backed by `POST /api/interactions/suggest-followups`).
   Saved via `POST /api/interactions` / edited via `PATCH
   /api/interactions/{id}`.
2. **Conversational chat** — a free-text box where a rep can type things like
   *"log a follow-up with Dr. Rao about the new cardiology trial"*. The
   message is sent to `POST /api/agent`, which runs the LangGraph agent.

Both paths write to the same `interactions` table, so anything logged via
chat immediately shows up in the "Recent interactions" list (and vice
versa). Clicking a recent interaction loads it into the form for editing.

### LangGraph agent

The agent is a small `StateGraph` with two nodes:

- **`agent`** — a Groq LLM (`llama-3.3-70b-versatile`) with the 5 tools bound via
  `bind_tools`, given a system prompt describing its role as the CRM
  assistant for a field rep.
- **`tools`** — a `ToolNode` that executes whichever tool(s) the LLM decided
  to call.

`tools_condition` routes between them until the LLM responds without a tool
call, at which point the graph ends. Conversation history is preserved
per `thread_id` using `MemorySaver`, so the assistant remembers earlier
turns in the same chat session (the frontend generates and reuses a
`thread_id` for its session).

### The 5 tools

| Tool | Purpose |
|---|---|
| **`log_interaction`** | Captures a new interaction. Runs the free-text notes through the LLM for entity extraction (HCP name, specialty, topic, sentiment) and a cleaned-up summary, then writes an `Interaction` row. |
| **`edit_interaction`** | Modifies an existing logged interaction. Takes a natural-language instruction (e.g. "set status to closed"), asks the LLM to turn it into structured field updates, then applies them. |
| **`summarize_interactions`** | Pulls recent interactions (optionally filtered by HCP) and asks the LLM to produce a short briefing covering themes, sentiment trends, and open follow-ups. |
| **`schedule_follow_up`** | Sets a follow-up date and status on a given interaction. |
| **`search_interactions`** | Keyword search across HCP name, topic, and notes. |

## Running locally

### 1. Database

```bash
docker compose up -d
```

This starts PostgreSQL on `localhost:5432` with the credentials already
wired into `backend/.env.example` (`hcp` / `hcp`, database `hcp_crm`).

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
copy .env.example .env       # then fill in GROQ_API_KEY
python app.py
```

The API runs at `http://127.0.0.1:8000`. Get a free Groq API key at
https://console.groq.com.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to the backend.

## Environment variables (`backend/.env`)

```
DATABASE_URL=postgresql+psycopg2://hcp:hcp@localhost:5432/hcp_crm
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:5173
```

## API reference

- `GET /api/interactions` — list recent interactions
- `POST /api/interactions` — create one (structured form)
- `PATCH /api/interactions/{id}` — update one (structured form edit)
- `POST /api/interactions/suggest-followups` — LLM-generated follow-up
  suggestions from `{ topic, notes, outcomes }`
- `POST /api/agent` — send a chat message to the LangGraph agent
  - Request: `{ "message": "...", "thread_id": "optional-existing-thread" }`
  - Response: `{ "reply": "...", "thread_id": "...", "tools_used": [...], "tools": [...] }`

## Deploying (Render)

`render.yaml` provisions a Postgres database, the FastAPI backend, and the
React static site together. Click **New → Blueprint** on Render, point it at
this repo, and it reads `render.yaml` automatically. You'll be prompted for
the `GROQ_API_KEY` secret since that's intentionally not in the file.

Render service names are globally unique across *all* Render accounts, not
just your own — if `ai-hcp-crm-backend` is already taken, Render silently
suffixes yours (e.g. `ai-hcp-crm-backend-y82n`). After the first deploy,
check the actual assigned URLs and update `CORS_ORIGINS` (backend) and
`VITE_API_BASE_URL` (frontend) in `render.yaml` to match if they were
suffixed, then push — both services auto-deploy on push.
