# src/recsys/service/schemas.py
from pydantic import BaseModel


class RecommendRequest(BaseModel):
    query: str          # "Snooze — SZA"
    top_k: int = 10     # number of recs to return


class Recommendation(BaseModel):
    row_index: int
    name: str
    artist: str
    score: float
    preview_url: str | None = None
    artwork_url: str | None = None


class RecommendResponse(BaseModel):
    query: str
    matched: dict | None
    recommendations: list[Recommendation]
