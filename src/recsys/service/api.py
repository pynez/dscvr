# src/recsys/service/api.py
from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.recsys.recommenders.cosine import CosineRecommender
from src.recsys.io import load_id_map, fuzzy_row_index, build_search_index, search_tracks
from src.recsys.service.schemas import (
    RecommendRequest,
    RecommendResponse,
    Recommendation,
)

app = FastAPI(
    title="Music Recommendation API",
    version="0.1.0",
    description="Text/tag-based music recommender built on Last.fm + iTunes data.",
)

origins = [
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load artifacts once at startup
recommender = CosineRecommender()
ID_MAP = load_id_map()
SEARCH_INDEX = build_search_index(ID_MAP)


@app.get("/health")
def health():
    return {"ok": True, "tracks": len(ID_MAP)}


class SearchResult(BaseModel):
    row_index: int
    title: str
    artist: str
    score: float

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@app.get("/search", response_model=SearchResponse)
def search(query: str, limit: int = 5):
    if not query.strip():
        return SearchResponse(query=query, results=[])
    matches = search_tracks(query, SEARCH_INDEX, limit=limit)
    return SearchResponse(
        query=query,
        results=[SearchResult(**m) for m in matches],
    )


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """
    Given a query string (e.g., 'Snooze — SZA'), fuzzy match it to a track
    in the catalog, then return top-k similar tracks based on cosine similarity.
    """
    idx, row = fuzzy_row_index(req.query, ID_MAP)
    if idx is None:
        raise HTTPException(status_code=404, detail="Song not found in catalog.")

    recs = recommender.similar_by_index(idx, top_k=req.top_k)

    return RecommendResponse(
        query=req.query,
        resolved_index=idx,
        resolved_name=row["title"],
        resolved_artist=row["artist"],
        recommendations=[Recommendation(**r) for r in recs],
    )
