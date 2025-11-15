# src/recsys/preprocess.py
from __future__ import annotations
import json, joblib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Paths
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROC = DATA / "processed"
ART = DATA / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

def _join_tags(tags):
    # None / NaN
    if tags is None or (isinstance(tags, float) and pd.isna(tags)):
        return ""
    # Common cases
    if isinstance(tags, (list, tuple)):
        return " ".join(str(t) for t in tags if t is not None)
    if isinstance(tags, np.ndarray):
        return " ".join(str(t) for t in tags.tolist() if t is not None)
    # Already a string
    if isinstance(tags, str):
        return tags
    # Fallback: try to iterate, else str()
    try:
        return " ".join(str(t) for t in tags if t is not None)
    except Exception:
        return str(tags)

def build_text_features(parquet_path: str | Path = PROC / "tracks_lastfm.parquet",
                        n_components: int = 200):
    df = pd.read_parquet(parquet_path).copy()
    if df.empty:
        raise RuntimeError("No rows in dataset. Build your Last.fm dataset first.")

    # Combine tags + title + artist into a single text field
    df["text"] = (
        df["tags"].apply(_join_tags) + " " +
        df["title"].fillna("") + " " +
        df["artist"].fillna("")
    ).str.lower()

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            min_df=2, max_df=0.95, ngram_range=(1,2), stop_words="english"
        )),
        ("svd", TruncatedSVD(n_components=n_components, random_state=42)),
        ("scale", StandardScaler(with_mean=False))
    ])

    X = pipe.fit_transform(df["text"])
    X = np.asarray(X)  # ensure dense ndarray after SVD (+ StandardScaler)

    # Persist artifacts
    joblib.dump(pipe, ART / "text_svd.pkl")
    np.save(ART / "features.npy", X)

    id_map = df[["title","artist","preview_url","artwork_url"]].to_dict(orient="records")
    with open(ART / "id_map.json","w") as f:
        json.dump(id_map, f)

    print(f"✅ Saved: {ART/'text_svd.pkl'}, {ART/'features.npy'}, {ART/'id_map.json'}")
    print("   features shape:", X.shape)
