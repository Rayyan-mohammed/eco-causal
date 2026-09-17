import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CAUSAL_MAP_PATH = DATA_DIR / "causal_map.json"
REFERENCE_RANGES_PATH = DATA_DIR / "reference_ranges.json"
CHROMA_DIR = ROOT_DIR / "chroma_db"

def _load_gemini_api_keys() -> list[str]:
    """Collects every Gemini key in .env: a plain GEMINI_API_KEY plus any
    numbered GEMINI_API_KEY_1, GEMINI_API_KEY_2, ... (stops at the first gap),
    so multiple free-tier accounts can be rotated for higher effective throughput."""
    keys = []
    single = os.environ.get("GEMINI_API_KEY")
    if single:
        keys.append(single)
    i = 1
    while True:
        key = os.environ.get(f"GEMINI_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    return keys


GEMINI_API_KEYS = _load_gemini_api_keys()
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None
MODEL = os.environ.get("ROOTCAUSE_MODEL", "gemini-3.1-flash-lite")

REQUIRED_VARIABLES = ["soil_organic_carbon", "rainfall_level", "land_use"]

DOMAINS = [
    "soil_health",
    "land_use_land_cover",
    "biodiversity",
    "climate",
    "human_impact",
]
