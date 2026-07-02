"""Shirube AI — FastAPI application entrypoint.

Serves the JSON API under /api/v1 and the compiled React dashboard as a
single-page app, so the whole product ships as one Google Cloud Run service.
"""

import os
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    """Placeholder: dispatch the agent pipeline and return structured insights.

    TODO: wire to agents.agent.root_agent and persist results to BigQuery.
    """
    return {
        "region": request.region,
        "query": request.query,
        "status": "pending",
        "insights": [],
    }


@api.get("/telemetry")
async def telemetry() -> dict:
    """Placeholder: harvester run stats surfaced on the dashboard."""
    return {
        "harvesters": 8,
        "records_ingested": 0,
        "last_run": None,
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
