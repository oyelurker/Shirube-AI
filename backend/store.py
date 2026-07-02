import json
import pathlib
import datetime

STORE_FILE = pathlib.Path(__file__).parent / "insights_store.json"

def save_insight(region: str, category: str, text: str):
    """Save an insight to the JSON store, keeping the last 50."""
    data = load_all()
    data.append({
        "region": region,
        "category": category,
        "insight": text,
        "harvested_at": datetime.datetime.utcnow().isoformat() + "Z"
    })
    
    # Keep only the last 50 insights so it doesn't grow infinitely
    STORE_FILE.write_text(json.dumps(data[-50:], indent=2))

def load_all() -> list[dict]:
    """Load all insights from the JSON store."""
    if STORE_FILE.exists():
        try:
            return json.loads(STORE_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []
