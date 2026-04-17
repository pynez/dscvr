# src/recsys/service/schemas.py
from __future__ import annotations
from pydantic import BaseModel, model_validator


# ─── Existing recommendation schemas ──────────────────────────────────────────

class RecommendRequest(BaseModel):
    query: str | None = None
    track_key: str | None = None
    row_index: int | None = None
    top_k: int = 10

    @model_validator(mode="after")
    def ensure_target(self):
        if self.query or self.track_key or self.row_index is not None:
            return self
        raise ValueError("Provide at least one of query, track_key, or row_index.")


class Recommendation(BaseModel):
    row_index: int
    name: str
    artist: str
    score: float
    preview_url: str | None = None
    artwork_url: str | None = None


class RecommendResponse(BaseModel):
    query: str
    resolved_index: int
    resolved_name: str
    resolved_artist: str
    recommendations: list[Recommendation]


# ─── Interaction tracking ──────────────────────────────────────────────────────

class InteractionRequest(BaseModel):
    user_id: str
    track_id: str               # row_index as string
    interaction_type: str       # 'heart' | 'skip' | 'complete'
    feature: str | None = None
    tags: list[str] = []        # track tags for taste profile update


# ─── Feature: Soundtrack Your Life ────────────────────────────────────────────

class SoundtrackRequest(BaseModel):
    description: str
    user_id: str | None = None


class SoundtrackTrack(BaseModel):
    row_index: int | None = None
    name: str
    artist: str
    reasoning: str = ""
    preview_url: str | None = None
    artwork_url: str | None = None
    youtube_id: str | None = None


class SoundtrackResponse(BaseModel):
    tracks: list[SoundtrackTrack]
    summary: str


# ─── Feature: Blind Taste Test ────────────────────────────────────────────────

class BlindTrack(BaseModel):
    row_index: int
    preview_url: str | None = None
    youtube_id: str | None = None


class BlindTasteTestResponse(BaseModel):
    tracks: list[BlindTrack]


class BlindRevealRequest(BaseModel):
    track_indices: list[int]


class RevealedTrack(BaseModel):
    row_index: int
    name: str
    artist: str
    artwork_url: str | None = None
    preview_url: str | None = None
    tags: list[str] = []


class BlindRevealResponse(BaseModel):
    tracks: list[RevealedTrack]


# ─── Feature: Time Machine ────────────────────────────────────────────────────

class TimeMachineRequest(BaseModel):
    seed_track: str
    seed_artist: str
    era: str        # '60s' | '70s' | '80s' | '90s' | '00s'
    user_id: str | None = None


class TimeMachineTrack(BaseModel):
    row_index: int | None = None
    name: str
    artist: str
    score: float = 0.0
    preview_url: str | None = None
    artwork_url: str | None = None
    youtube_id: str | None = None
    tags: list[str] = []


class TimeMachineResponse(BaseModel):
    tracks: list[TimeMachineTrack]
    era: str
    seed_track: str
    seed_artist: str
    summary: str


# ─── Feature: Algorithmic Capture ─────────────────────────────────────────────

class TagScore(BaseModel):
    tag: str
    score: float


class EscapeTrack(BaseModel):
    row_index: int | None = None
    name: str
    artist: str
    score: float = 0.0
    preview_url: str | None = None
    artwork_url: str | None = None
    youtube_id: str | None = None
    escape_tag: str | None = None


class AlgorithmicCaptureResponse(BaseModel):
    capture_score: float | None
    capture_percent: int | None = None
    dominant_tags: list[str]
    secondary_tags: list[str] = []
    underexplored_tags: list[str]
    tag_distribution: list[TagScore] = []
    escape_tracks: list[EscapeTrack]
    insufficient_data: bool = False
    interactions_needed: int | None = None
    total_interactions: int | None = None


# ─── Feature: The Séance ──────────────────────────────────────────────────────

class SeanceRequest(BaseModel):
    artist: str
    user_id: str | None = None


class SeanceTrack(BaseModel):
    row_index: int | None = None
    name: str
    artist: str
    connection: str = ""
    preview_url: str | None = None
    artwork_url: str | None = None
    youtube_id: str | None = None


class SeanceResponse(BaseModel):
    original_artist: str
    tracks: list[SeanceTrack]
    summary: str
