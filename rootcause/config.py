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

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("ROOTCAUSE_MODEL", "claude-opus-5")

REQUIRED_VARIABLES = ["soil_organic_carbon", "rainfall_level", "land_use"]

DOMAINS = [
    "soil_health",
    "land_use_land_cover",
    "biodiversity",
    "climate",
    "human_impact",
]
