# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — build the Vite/React frontend
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /frontend

# Install deps first for better layer caching.
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build   # emits /frontend/dist

# ---------------------------------------------------------------------------
# Stage 2 — Python runtime serving the API + built frontend
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Node.js is required at runtime: the BrightData MCP toolset is launched via
# `npx @brightdata/mcp` from backend/agents/tools.py.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend source (imports resolve from this dir as the `agents.*` root).
COPY backend/ ./

# Bring the compiled frontend into the path FastAPI serves (../frontend/dist).
COPY --from=frontend /frontend/dist ./../frontend/dist

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Cloud Run injects PORT (defaults to 8080).
ENV PORT=8080
EXPOSE 8080

CMD ["/app/start.sh"]
