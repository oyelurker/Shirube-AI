"""Centralized configuration for Shirube AI travel system."""

import os
from dotenv import load_dotenv
from google.genai.types import GenerateContentConfig

load_dotenv()

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Centralized model configuration - change once, applies everywhere
DEFAULT_MODEL = "gemini-2.0-flash"

# Alternative: Load from environment variable with fallback
# DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ============================================================================
# SHARED GENERATION CONFIG
# ============================================================================

# Standard generation config used across most agents
DEFAULT_GENERATION_CONFIG = GenerateContentConfig(
    temperature=0.0,
    top_p=0.5
)

# ============================================================================
# ENVIRONMENT SETTINGS
# ============================================================================

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Vertex AI Configuration
USE_VERTEX_AI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "") 