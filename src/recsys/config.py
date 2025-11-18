from pathlib import Path
import os

# Paths
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROC = DATA / "processed"
ART = DATA / "artifacts"
SEEDS = DATA / "seeds"
for p in (RAW, PROC, ART):
    p.mkdir(parents=True, exist_ok=True)

# Feature columns used later for modeling
FEATURE_COLS = [
    "danceability","energy","loudness","speechiness",
    "acousticness","instrumentalness","liveness","valence","tempo"
]

# Defaults (you can override via CLI flags)
DEFAULT_MARKET = os.getenv("SPOTIFY_MARKET", "US")
DEFAULT_LIMIT_PER_QUERY = int(os.getenv("LIMIT_PER_QUERY", "150"))
