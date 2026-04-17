# src/recsys/service/api.py
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

# Load .env before anything reads os.environ — no-op in production (Fly.io injects secrets directly)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[3] / ".env")  # backend/.env

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.recsys.config import PROC
from src.recsys.recommenders.cosine import CosineRecommender
from src.recsys.search import SearchIndex, norm, EM_DASH
from src.recsys.service.schemas import (
    # existing
    RecommendRequest,
    RecommendResponse,
    Recommendation,
    InteractionRequest,
    # features
    SoundtrackRequest,
    SoundtrackResponse,
    BlindTasteTestResponse,
    BlindRevealRequest,
    BlindRevealResponse,
    TimeMachineRequest,
    TimeMachineResponse,
    AlgorithmicCaptureResponse,
    SeanceRequest,
    SeanceResponse,
)

log = logging.getLogger(__name__)

app = FastAPI(
    title="DSCVR API",
    version="2.0.0",
    description="Music self-discovery platform — recommendations, soundtrack, blind taste test, time machine, algorithmic capture, séance.",
)

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://dscvr.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRACKS_PARQUET = Path(PROC / "tracks_lastfm.parquet")
AMBIGUITY_THRESHOLD = 88.0
SEARCH_LIMIT = 8


def load_tracks_dataframe(parquet_path: Path = TRACKS_PARQUET) -> pd.DataFrame:
    if not parquet_path.exists():
        raise RuntimeError(f"Missing parquet file at {parquet_path}")
    df = pd.read_parquet(parquet_path)
    required = {"title", "artist"}
    if not required.issubset(df.columns):
        raise RuntimeError(f"Parquet missing required columns: {required}")
    return df


def build_track_key(title: str, artist: str) -> str:
    return f"{title} {EM_DASH} {artist}"


# ── Load artifacts once at startup ────────────────────────────────────────────
recommender = CosineRecommender()
try:
    tracks_df = load_tracks_dataframe()
    if len(tracks_df) != len(recommender.id_map):
        tracks_df = pd.DataFrame(recommender.id_map)
except Exception:
    tracks_df = pd.DataFrame(recommender.id_map)

SEARCH_INDEX = SearchIndex(tracks_df)


# ─── Helpers ──────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    row_index: int
    title: str
    artist: str
    artwork_url: str | None = None
    preview_url: str | None = None
    score: float
    track_key: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


def serialize_match(match: dict) -> SearchResult:
    return SearchResult(
        row_index=match["row_index"],
        title=match["title"],
        artist=match["artist"],
        artwork_url=match.get("artwork_url"),
        preview_url=match.get("preview_url"),
        score=float(match["score"]),
        track_key=build_track_key(match["title"], match["artist"]),
    )


def resolve_track(req: RecommendRequest) -> tuple[int, float]:
    if req.row_index is not None:
        if req.row_index < 0 or req.row_index >= len(tracks_df):
            raise HTTPException(status_code=404, detail="Song not found in catalog.")
        return req.row_index, 100.0

    if req.track_key:
        idx = SEARCH_INDEX.exact_index.get(norm(req.track_key))
        if idx is not None:
            return idx, 100.0
        if not req.query:
            raise HTTPException(status_code=404, detail="Song not found in catalog.")

    if not req.query:
        raise HTTPException(status_code=400, detail="Missing query or track identifier.")

    best_idx, best_score, candidate_idxs = SEARCH_INDEX.match(
        req.query, limit=SEARCH_LIMIT
    )
    if best_idx is None:
        raise HTTPException(status_code=404, detail="Song not found in catalog.")

    if best_score < AMBIGUITY_THRESHOLD:
        matches = SEARCH_INDEX.top_matches(req.query, limit=SEARCH_LIMIT)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "AMBIGUOUS_QUERY",
                "candidates": [serialize_match(m).model_dump() for m in matches],
            },
        )

    return best_idx, float(best_score)


async def _register_user_if_present(x_user_id: str | None) -> None:
    """Fire-and-forget user registration — never blocks response."""
    if not x_user_id:
        return
    from src.recsys.service import db
    try:
        await asyncio.to_thread(db.register_user, x_user_id)
    except Exception as exc:
        log.debug("User registration silently failed: %s", exc)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"ok": True, "tracks": len(tracks_df)}


# ─── Search ───────────────────────────────────────────────────────────────────

@app.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., alias="q"), limit: int = SEARCH_LIMIT):
    if not q.strip():
        return SearchResponse(query=q, results=[])
    matches = SEARCH_INDEX.top_matches(q, limit=limit)
    return SearchResponse(
        query=q,
        results=[serialize_match(m) for m in matches],
    )


# ─── Classic Recommendation ───────────────────────────────────────────────────

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    idx, _score = resolve_track(req)
    try:
        recs = recommender.similar_by_index(idx, top_k=req.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to compute recommendations.") from exc

    # preview_resolver strips DRM iTunes URLs and replaces them with Deezer MP3s
    from src.recsys.service.preview_resolver import resolve_batch
    enriched = await resolve_batch(recs)

    resolved = tracks_df.iloc[idx]
    resolved_name = resolved.get("title") or recommender.id_map[idx].get("title")
    resolved_artist = resolved.get("artist") or recommender.id_map[idx].get("artist")

    return RecommendResponse(
        query=req.query or req.track_key or "",
        resolved_index=idx,
        resolved_name=resolved_name,
        resolved_artist=resolved_artist,
        recommendations=[Recommendation(**r) for r in enriched],
    )


# ─── Interactions ─────────────────────────────────────────────────────────────

@app.post("/interactions", status_code=204)
async def log_interaction(req: InteractionRequest):
    """Log a user interaction and update taste profile. Fire-and-forget."""
    from src.recsys.service import db

    async def _persist():
        await asyncio.to_thread(
            db.log_interaction,
            req.user_id,
            req.track_id,
            req.interaction_type,
            req.feature,
        )
        if req.tags:
            await asyncio.to_thread(
                db.update_taste_profile,
                req.user_id,
                req.tags,
                req.interaction_type,
            )

    asyncio.create_task(_persist())


# ─── Feature 1: Soundtrack Your Life ──────────────────────────────────────────

@app.post("/soundtrack", response_model=SoundtrackResponse)
async def soundtrack(
    req: SoundtrackRequest,
    x_user_id: str | None = Header(default=None),
):
    await _register_user_if_present(x_user_id or req.user_id)
    from src.recsys.service.features import soundtrack as feat

    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")

    result = await feat.run(
        description=req.description,
        recommender=recommender,
        user_id=x_user_id or req.user_id,
    )
    return SoundtrackResponse(**result)


# ─── Feature 2: Blind Taste Test ──────────────────────────────────────────────

@app.get("/blind-taste-test", response_model=BlindTasteTestResponse)
async def blind_taste_test(x_user_id: str | None = Header(default=None)):
    await _register_user_if_present(x_user_id)
    from src.recsys.service.features import blind_taste_test as feat
    from src.recsys.service.preview_resolver import resolve_batch

    result = feat.get_session(recommender)

    # Resolve previews using full catalog metadata (name/artist needed for Deezer).
    # We temporarily enrich with name/artist for the resolver, then strip them
    # from the response so the session remains blind.
    resolve_input = []
    for t in result["tracks"]:
        idx = t["row_index"]
        row = recommender.id_map[idx]
        meta = recommender.meta_df.iloc[idx] if recommender.meta_df is not None else None
        name = (meta.get("title") if hasattr(meta, "get") else None) or row.get("title", "")
        artist = (meta.get("artist") if hasattr(meta, "get") else None) or row.get("artist", "")
        resolve_input.append({
            "row_index": idx,
            "name": name,
            "artist": artist,
            "preview_url": t.get("preview_url"),
            "artwork_url": None,
        })

    enriched = await resolve_batch(resolve_input)

    # Return only blind fields — name, artist, tags, artwork intentionally omitted
    result["tracks"] = [
        {
            "row_index": t["row_index"],
            "preview_url": t.get("preview_url"),
            "youtube_id": t.get("youtube_id"),
        }
        for t in enriched
    ]

    return BlindTasteTestResponse(**result)


@app.post("/blind-taste-test/reveal", response_model=BlindRevealResponse)
async def blind_reveal(req: BlindRevealRequest):
    from src.recsys.service.features import blind_taste_test as feat

    result = feat.reveal(req.track_indices, recommender)
    return BlindRevealResponse(**result)


# ─── Feature 3: Time Machine ──────────────────────────────────────────────────

@app.post("/time-machine", response_model=TimeMachineResponse)
async def time_machine(
    req: TimeMachineRequest,
    x_user_id: str | None = Header(default=None),
):
    await _register_user_if_present(x_user_id or req.user_id)
    from src.recsys.service.features import time_machine as feat

    valid_eras = {"60s", "70s", "80s", "90s", "00s"}
    if req.era not in valid_eras:
        raise HTTPException(
            status_code=400,
            detail=f"era must be one of: {', '.join(sorted(valid_eras))}",
        )

    result = await feat.run(
        seed_track=req.seed_track,
        seed_artist=req.seed_artist,
        era=req.era,
        recommender=recommender,
        search_index=SEARCH_INDEX,
    )
    return TimeMachineResponse(**result)


# ─── Feature 4: Algorithmic Capture ───────────────────────────────────────────

@app.get("/algorithmic-capture", response_model=AlgorithmicCaptureResponse)
async def algorithmic_capture(
    user_id: str = Query(...),
    x_user_id: str | None = Header(default=None),
):
    uid = x_user_id or user_id
    await _register_user_if_present(uid)
    from src.recsys.service.features import algorithmic_capture as feat

    result = await feat.run(user_id=uid, recommender=recommender)
    return AlgorithmicCaptureResponse(**result)


# ─── Feature 5: The Séance ────────────────────────────────────────────────────

@app.post("/seance", response_model=SeanceResponse)
async def seance(
    req: SeanceRequest,
    x_user_id: str | None = Header(default=None),
):
    await _register_user_if_present(x_user_id or req.user_id)
    from src.recsys.service.features import seance as feat

    if not req.artist.strip():
        raise HTTPException(status_code=400, detail="Artist name cannot be empty.")

    result = await feat.run(artist=req.artist, recommender=recommender)
    return SeanceResponse(**result)
