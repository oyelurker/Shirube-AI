# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**Shirube AI** is a *Regional Tourism & Economic Decision Intelligence Platform* built for the Google Cloud Hackathon. It repurposes a multi-agent travel-planning system into a **decision-intelligence engine for city stakeholders**: instead of booking trips for individuals, the agents act as **Economic Data Harvesters** that continuously scrape and structure real-world tourism supply/demand signals — flights, hotels, activities, dining, and local experiences — and feed them into **BigQuery** and a **Neo4j GraphRAG** knowledge graph.

The result is a dashboard that helps municipalities, tourism boards, and infrastructure planners answer questions like *"Where is inbound demand outpacing lodging capacity?"* or *"Which neighborhoods should we prioritize for transit investment?"*

The system is a **monorepo**: a FastAPI backend (Google Agent Development Kit + Gemini 2.0 Flash) and a React + Vite single-page dashboard, packaged as a single container for **Google Cloud Run**.

> **Note:** `full-agent-copy/` is the untouched legacy `ai_wanderize` codebase, kept as a reference backup only. Do not import from it or edit it — all active code lives in `backend/agents/`.

## Repository Layout

```
shirube-ai/
├── CLAUDE.md                 # This file
├── Dockerfile                # Multi-stage: build frontend → serve via FastAPI
├── backend/                  # Python import root (imports are `agents.*`)
│   ├── main.py               # FastAPI entrypoint (serves API + static frontend build)
│   ├── requirements.txt
│   └── agents/               # Google ADK multi-agent system
│       ├── agent.py          # root_agent — orchestrator
│       ├── config.py         # Model + env configuration
│       ├── tools.py          # Firecrawl web-scraping toolset (free tier)
│       ├── prompt.py         # Root orchestrator instructions
│       ├── flight_agent/     # Economic Data Harvester: air-travel supply/demand
│       ├── hotel_agent/      # Economic Data Harvester: lodging capacity & pricing
│       ├── activity_agent/   # Economic Data Harvester: attractions & tours
│       ├── local_experiences_agent/  # Harvester: local/experiential economy
│       ├── dining_agent/     # Harvester: food & beverage sector
│       ├── booking_agent/    # Harvester: conversion & booking signals
│       ├── support_agent/    # Harvester: services & accessibility signals
│       └── logistics_agent/  # Harvester: transit & mobility signals
└── frontend/                 # React + Vite + Tailwind dashboard SPA
    ├── index.html
    ├── package.json
    └── src/
```

## Commands

### Backend (from `backend/`)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI dev server (hot reload)
uvicorn main:app --reload --port 8080

# Inspect/iterate on agents with the ADK dev UI
adk web agents
```

> Imports use `backend/` as the Python root, so always run backend commands **from inside `backend/`** (e.g. `agents.config`, not `backend.agents.config`).

### Frontend (from `frontend/`)

```bash
# Install dependencies
npm install

# Run the Vite dev server
npm run dev

# Production build (emits static assets served by FastAPI)
npm run build

# Lint
npm run lint
```

### Docker (from repo root)

```bash
# Build the single deployable image (frontend build + backend)
docker build -t shirube-ai .

# Run locally
docker run -p 8080:8080 --env-file backend/.env shirube-ai
```

## Required Environment Variables

Defined and consumed in `backend/agents/config.py` and `backend/agents/tools.py`. Provide them via `backend/.env` locally, or as Cloud Run service variables / Secret Manager in production.

| Variable | Purpose |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini API key (used when not on Vertex AI). |
| `GOOGLE_GENAI_USE_VERTEXAI` | `True`/`False` — route model calls through Vertex AI. |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (Vertex AI, BigQuery, Cloud Run). |
| `GOOGLE_CLOUD_LOCATION` | GCP region (e.g. `us-central1`). |
| `FIRECRAWL_API_KEY` | Firecrawl API key for web scraping. Free tier at firecrawl.dev (no credit card). If unset, Jina AI Reader is used as a zero-config fallback. |
| `BIGQUERY_DATASET` | Target dataset for harvested tourism/economic insights. |
| `NEO4J_URI` | Neo4j connection URI for the GraphRAG knowledge graph. |
| `NEO4J_USERNAME` | Neo4j username. |
| `NEO4J_PASSWORD` | Neo4j password. |

## Architecture

Shirube AI is a **hierarchical multi-agent system** built on the **Google Agent Development Kit (ADK)**. A single `root_agent` orchestrates eight specialized coordinator agents. Each coordinator wraps its own sub-agents (planner / searcher / advisor style) and calls out to the web via the **Firecrawl** scraping toolset (free tier — no credit card required).

```
                        ┌─────────────────────────┐
                        │   root_agent (ADK)      │
                        │  "shirube_travel_...    │
                        │   assistant" orchestrator│
                        └───────────┬─────────────┘
                                    │ sub_agents
   ┌──────────┬──────────┬─────────┼─────────┬──────────┬──────────┬──────────┐
 flight     hotel     activity   local     dining    support   booking   logistics
 agent      agent     agent      exp.      agent     agent     agent     agent
   │          │          │       agent       │          │         │          │
   └──────────┴──────────┴─────────┴─────────┴──────────┴─────────┴──────────┘
                                    │
                          Firecrawl / Jina AI (scraping)
                                    │
                     ┌──────────────┴───────────────┐
              ┌──────▼──────┐               ┌────────▼────────┐
              │  BigQuery   │               │  Neo4j GraphRAG │
              │ (structured │               │  (entity graph, │
              │  insights)  │               │  relationships) │
              └──────┬──────┘               └────────┬────────┘
                     └──────────────┬────────────────┘
                                    │
                          FastAPI insights API
                                    │
                        React glassmorphism dashboard
```

**Data flow (harvest → structure → decide):**
1. The orchestrator dispatches harvesting tasks to the relevant coordinator agents.
2. Coordinators scrape live tourism-market data through the **Firecrawl** toolset (`scrape_url` / `scrape_url_json`). Falls back to Jina AI Reader if the API key is absent.
3. **Gemini 2.0 Flash** normalizes raw results into structured economic records.
4. Records land in **BigQuery** (analytics) and entities/relationships are written to **Neo4j** for **GraphRAG** retrieval.
5. FastAPI exposes query + insight endpoints that the React dashboard renders for stakeholders.

**Model configuration** is centralized in `backend/agents/config.py` (`DEFAULT_MODEL = "gemini-2.0-flash"`, deterministic `temperature=0.0`). Change it once; it applies to every agent.

## Agents

All agents live under `backend/agents/`. Each coordinator is defined in its package's `agent.py`, with instructions in the sibling `prompt.py`. Though the underlying code retains its travel-domain vocabulary, each agent now functions as an **Economic Data Harvester** whose output is structured insight for BigQuery, not consumer bookings.

| Package | Coordinator (`agent.py`) | Harvests |
| --- | --- | --- |
| `flight_agent/` | `flight_booking_system` | Air connectivity, routes, fares, inbound demand |
| `hotel_agent/` | `hotel_booking_system` | Lodging inventory, occupancy, pricing pressure |
| `activity_agent/` | `activity_booking_system` | Attractions, tours, seasonal activity demand |
| `local_experiences_agent/` | `local_experiences_system` | Experiential / creator economy signals |
| `dining_agent/` | `dining_coordinator_system` | Food & beverage sector density and trends |
| `booking_agent/` | `booking_coordinator_system` | Conversion, availability, booking-funnel signals |
| `support_agent/` | `support_coordinator_system` | Visitor services, accessibility, language support |
| `logistics_agent/` | `logistics_coordinator_system` | Transit, mobility, itinerary/logistics load |

**Conventions when editing agents:**
- Shared config comes from `agents.config` (`DEFAULT_MODEL`, `DEFAULT_GENERATION_CONFIG`).
- The scraping toolset comes from `agents.tools` (`toolset` / `web_scraping_toolset`). Backed by Firecrawl with a Jina AI zero-config fallback.
- Cross-package imports are **absolute** from the `agents.` root (e.g. `from agents.flight_agent.agent import flight_booking_system`); intra-package imports are **relative** (e.g. `from .prompt import ...`).
- Add a new harvester by creating `agents/<name>_agent/{__init__.py,agent.py,prompt.py}` and registering its coordinator in `agents/agent.py`'s `sub_agents` list.

## Backend API

The FastAPI app in `backend/main.py`:
- Mounts the agent orchestrator and exposes endpoints to run harvesting jobs and query stored insights.
- Serves the compiled React app (`frontend/dist`) as static files so the whole product ships as one Cloud Run service.
- Listens on `PORT` (default `8080`) to match Cloud Run's contract.

Suggested endpoint surface:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness/readiness probe. |
| `POST` | `/api/harvest` | Trigger the agent pipeline for a region/query. |
| `GET` | `/api/insights` | Query structured tourism/economic insights from BigQuery. |
| `POST` | `/api/graph/query` | GraphRAG query against the Neo4j knowledge graph. |
| `GET` | `/*` | Serve the React dashboard (SPA fallback). |

## Frontend

A **React + Vite** single-page app styled with **Tailwind CSS**. The UI is a **dark-themed glassmorphism decision dashboard**: frosted translucent panels, soft glows, and layered blur over a dark background, presenting harvested insights as charts, maps, and KPI cards for city stakeholders.

- **Stack:** React, Vite, Tailwind CSS (dark mode enabled), glassmorphism component styling (`backdrop-blur`, translucent `bg-white/5`, subtle borders/shadows).
- **Data:** fetches from the FastAPI `/api/*` endpoints.
- **Build:** `npm run build` outputs to `frontend/dist`, which the backend serves in production.
- **Focus:** infrastructure-decision views — demand-vs-capacity, sector heatmaps, and GraphRAG-driven relationship exploration — not consumer travel booking.

## Deployment

Deployed as a **single container to Google Cloud Run** via a root **multi-stage `Dockerfile`**:

1. **Stage 1 (frontend build):** Node image runs `npm ci && npm run build` in `frontend/`, producing static assets.
2. **Stage 2 (runtime):** Python image installs `backend/requirements.txt`, copies `backend/`, and copies the frontend build from Stage 1 into the path FastAPI serves.
3. The container runs `uvicorn main:app --host 0.0.0.0 --port 8080`; FastAPI serves both the API and the dashboard.

```bash
# Build & push to Artifact Registry, then deploy
gcloud run deploy shirube-ai \
  --source . \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --allow-unauthenticated
```

Provide secrets (`GOOGLE_API_KEY`, `FIRECRAWL_API_KEY`, Neo4j credentials) via Cloud Run environment variables or Secret Manager. Grant the service account BigQuery and Vertex AI permissions.
