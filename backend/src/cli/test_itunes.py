"""
Quick probe to see if iTunes search is reachable and returning data.
"""

from __future__ import annotations

import argparse
from typing import Tuple

import requests

from src.recsys.etl_lastfm import ITUNES


def ping_itunes(title: str, artist: str, limit: int = 1, timeout: float = 15.0) -> Tuple[int, dict]:
    """
    Hit the iTunes search API directly (no cache) and return (status_code, payload or error text).
    """
    term = f"{title} {artist}".strip()
    resp = requests.get(
        ITUNES,
        params={"term": term, "media": "music", "limit": limit},
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except Exception as exc:
        return resp.status_code, {"error": str(exc), "body_snippet": resp.text[:300]}
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"error": "invalid json", "body_snippet": resp.text[:300]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test iTunes availability for a given title and artist.")
    parser.add_argument("--title", required=True, help="Track title to query.")
    parser.add_argument("--artist", required=True, help="Artist name to query.")
    parser.add_argument("--limit", type=int, default=1, help="Number of results to request.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status, payload = ping_itunes(args.title, args.artist, limit=args.limit)
    print(f"status={status}")
    if isinstance(payload, dict) and "results" in payload:
        items = payload.get("results", []) or []
        if not items:
            print("results: []")
        else:
            first = items[0]
            print(
                "first result:",
                {
                    "trackName": first.get("trackName"),
                    "artistName": first.get("artistName"),
                    "previewUrl": first.get("previewUrl"),
                    "artworkUrl100": first.get("artworkUrl100"),
                },
            )
            print(f"results returned: {len(items)}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
