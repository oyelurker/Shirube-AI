"""Centralized tool configurations for Shirube AI travel system.

Web scraping is powered by Firecrawl (free tier, no credit card required).
Sign up at https://firecrawl.dev to get your API key.

Fallback: if FIRECRAWL_API_KEY is not set, Jina AI Reader is used automatically
(zero-config, no API key needed) so the system never crashes on startup.

All 8 searcher agents import `toolset` from this module — that export is
intentionally preserved so no agent files need to be changed.
The `toolset` object is a proper BaseToolset subclass, matching the ADK
contract that LlmAgent.tools expects (callable | BaseTool | BaseToolset).
"""

import os
import logging
import requests
from typing import Optional

from dotenv import load_dotenv
from google.adk.tools import FunctionTool
from google.adk.tools.base_toolset import BaseToolset

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# FIRECRAWL CLIENT INITIALISATION
# ============================================================================

_FIRECRAWL_API_KEY: Optional[str] = os.getenv("FIRECRAWL_API_KEY")
_firecrawl_app = None

if _FIRECRAWL_API_KEY:
    try:
        from firecrawl import FirecrawlApp
        _firecrawl_app = FirecrawlApp(api_key=_FIRECRAWL_API_KEY)
        logger.info("Firecrawl initialised successfully.")
    except ImportError:
        logger.warning(
            "firecrawl-py is not installed. Run: pip install firecrawl-py"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Firecrawl init failed (%s) — falling back to Jina AI Reader.", exc
        )
else:
    logger.warning(
        "FIRECRAWL_API_KEY not set. "
        "Scraping will use Jina AI Reader (free, keyless fallback). "
        "Add FIRECRAWL_API_KEY to backend/.env for better results: "
        "https://firecrawl.dev"
    )


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _scrape_via_jina(url: str) -> str:
    """Zero-config fallback using Jina AI Reader — no API key required."""
    try:
        response = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain", "User-Agent": "ShirubeAI/1.0"},
            timeout=30,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        return f"[scrape_error] Jina AI fallback failed for {url}: {exc}"


def _scrape_via_firecrawl(url: str) -> str:
    """Scrape a URL and return clean Markdown via Firecrawl."""
    try:
        result = _firecrawl_app.scrape_url(url, formats=["markdown"])
        return result.markdown or "[scrape_warning] Page returned empty content."
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Firecrawl scrape failed for %s: %s — trying Jina fallback.", url, exc
        )
        return _scrape_via_jina(url)


# ============================================================================
# PUBLIC TOOL FUNCTIONS
# These are wrapped as FunctionTool so ADK can introspect their schema.
# ============================================================================

def scrape_url(url: str) -> str:
    """Scrape a web page and return its content as clean Markdown.

    Use this tool to retrieve real-time information from websites, booking
    platforms, travel blogs, government tourism portals, or any public URL.
    The returned Markdown is clean and ready to be processed by an LLM.

    Args:
        url: The full URL of the page to scrape (must start with http/https).

    Returns:
        Page content as clean Markdown text, suitable for LLM analysis.
    """
    if not url.startswith(("http://", "https://")):
        return (
            f"[scrape_error] Invalid URL — must start with http:// or https://: {url}"
        )

    logger.info("Scraping URL: %s", url)

    if _firecrawl_app:
        return _scrape_via_firecrawl(url)
    return _scrape_via_jina(url)


def scrape_url_json(url: str, extraction_prompt: str = "") -> str:
    """Scrape a web page and extract structured data as a JSON string.

    Use this tool when you need specific structured information from a page,
    such as hotel prices, flight schedules, restaurant menus, or activity
    listings. Returns a JSON string with extracted key-value data.

    Args:
        url: The full URL of the page to scrape.
        extraction_prompt: Natural language description of what data to extract
            (e.g. "Extract hotel name, price per night, star rating, amenities").

    Returns:
        A JSON-formatted string with the extracted structured data, or
        Markdown content as fallback if structured extraction is unavailable.
    """
    if not url.startswith(("http://", "https://")):
        return (
            f"[scrape_error] Invalid URL — must start with http:// or https://: {url}"
        )

    logger.info("Scraping structured data from: %s", url)

    if _firecrawl_app and extraction_prompt:
        try:
            result = _firecrawl_app.scrape_url(
                url,
                formats=["extract"],
                extract={"prompt": extraction_prompt},
            )
            import json
            return json.dumps(result.extract, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Firecrawl JSON extraction failed for %s: %s — falling back to Markdown.",
                url,
                exc,
            )

    # Fallback: return raw Markdown so the LLM can still parse it
    return scrape_url(url)


# ============================================================================
# FIRECRAWL TOOLSET — a proper BaseToolset subclass
#
# ADK's LlmAgent.tools field expects each element to be one of:
#   - a callable  (plain Python function)
#   - a BaseTool  (e.g. FunctionTool)
#   - a BaseToolset (e.g. MCPToolset)
#
# All 8 searcher agents write:  tools=[toolset]
# So `toolset` itself must be a BaseToolset instance.
# ============================================================================

class FirecrawlToolset(BaseToolset):
    """ADK-compatible toolset wrapping Firecrawl scraping tools.

    Exposes `scrape_url` and `scrape_url_json` as FunctionTool instances.
    Implements BaseToolset so agents can use it as: tools=[toolset].
    """

    def __init__(self) -> None:
        super().__init__()
        self._tools: list[FunctionTool] = [
            FunctionTool(func=scrape_url),
            FunctionTool(func=scrape_url_json),
        ]

    async def get_tools(self, readonly_context=None) -> list[FunctionTool]:  # type: ignore[override]
        """Return the list of FunctionTool instances for this toolset.

        Args:
            readonly_context: ADK context (unused for HTTP-based tools).

        Returns:
            List of FunctionTool instances available to agents.
        """
        return self._tools

    async def close(self) -> None:
        """No persistent connections to close for HTTP-based scraping."""
        pass


# ============================================================================
# EXPORTS — preserved for backward compatibility
# All 8 agent files do: `from agents.tools import toolset`
# ============================================================================

web_scraping_toolset = FirecrawlToolset()

# Alias — exactly the same name the agents already import
toolset = web_scraping_toolset
