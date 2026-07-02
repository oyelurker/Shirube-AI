"""Shirube AI — FastAPI application entrypoint.

Serves the JSON API under /api/v1 and the compiled React dashboard as a
single-page app, so the whole product ships as one Google Cloud Run service.
"""

import os
from pathlib import Path
import store

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.apps import App
from google.adk import Runner
import google.genai.types as genai_types
from agents.agent import root_agent
# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Shirube AI",
    description="Regional Tourism & Economic Decision Intelligence Platform",
    version="0.1.0",
)

# Compiled frontend lives alongside the backend (../frontend/dist locally and
# in the container, where the Docker build copies the Vite output there).
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", Path(__file__).parent.parent / "frontend" / "dist")
)

# ---------------------------------------------------------------------------
# ADK Engine Setup
# ---------------------------------------------------------------------------

adk_app = App(name="shirube_travel_assistant", root_agent=root_agent)
session_svc = InMemorySessionService()
artifact_svc = InMemoryArtifactService()
credential_svc = InMemoryCredentialService()

runner = Runner(
    app=adk_app,
    session_service=session_svc,
    artifact_service=artifact_svc,
    credential_service=credential_svc
)

# ---------------------------------------------------------------------------
# API routes (/api/v1)
# ---------------------------------------------------------------------------

api = APIRouter(prefix="/api/v1")


class TourismAnalysisRequest(BaseModel):
    """Kick off an Economic Data Harvester run for a region."""

    region: str
    query: str | None = None


@api.get("/health")
async def health() -> dict:
    """Liveness/readiness probe for Cloud Run."""
    return {"status": "ok", "service": "shirube-ai"}


@api.post("/analyze-tourism")
async def analyze_tourism(request: TourismAnalysisRequest) -> dict:
    """Dispatch the agent pipeline and return structured insights."""
    session = await session_svc.create_session(
        app_name="shirube_travel_assistant",
        user_id="demo_user",
    )
    
    prompt_text = f"Analyze tourism and economic insights for {request.region}."
    if request.query:
        prompt_text += f" {request.query}"
        
    message = genai_types.Content(
        role="user", 
        parts=[genai_types.Part.from_text(text=prompt_text)]
    )
    
    result_text = ""
    
    # Run the multi-agent system
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=message):
        if event.content and event.content.parts:
            text = "".join(part.text or "" for part in event.content.parts)
            if text:
                result_text += text
                
    # Temporarily we return text directly. Later we will parse it from the JSON store/BigQuery
    store.save_insight(request.region, "General Tourism", result_text)

    return {
        "region": request.region,
        "query": request.query,
        "status": "complete",
        "insights": result_text,
    }


@api.get("/insights")
async def get_insights() -> dict:
    """Return all harvested insights from the store."""
    data = store.load_all()
    # Return newest first
    return {"insights": list(reversed(data))}


@api.get("/telemetry")
async def telemetry() -> dict:
    """Harvester run stats surfaced on the dashboard."""
    data = store.load_all()
    return {
        "harvesters": 8,
        "records_ingested": len(data),
        "last_run": data[-1]["harvested_at"] if data else None,
    }


app.include_router(api)

# ---------------------------------------------------------------------------
# Static frontend (SPA) — mounted last so it never shadows /api routes
# ---------------------------------------------------------------------------

if FRONTEND_DIST.is_dir():
    # Serve hashed build assets (JS/CSS) from /assets.
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        """Serve index.html for any unmatched path (client-side routing)."""
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
