"""
Backfill missing iTunes preview and artwork URLs into an existing parquet.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.src.recsys.config import PROC
from backend.src.recsys.etl_lastfm import _cached_itunes_preview


def _missing(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def backfill_itunes(
    parquet_path: Path,
    out_path: Optional[Path] = None,
    batch_size: int = 500,
    sleep_s: float = 0.2,
    save_every: int = 200,
    only_missing: bool = True,
    overwrite: bool = False,
    max_updates: Optional[int] = None,
    refresh_cache: bool = False,
) -> None:
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    required = {"title", "artist", "preview_url", "artwork_url"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise RuntimeError(f"Parquet missing columns: {missing_cols}")

    mask_missing = _missing(df["preview_url"]) | _missing(df["artwork_url"])
    work_df = df[mask_missing] if only_missing else df
    if batch_size and batch_size > 0:
        work_df = work_df.head(batch_size)

    if work_df.empty:
        print("No rows to process.")
        return

    out_path = out_path or parquet_path
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    filled_prev = 0
    filled_art = 0
    skipped = 0
    updates_since_save = 0
    total_updates = 0
    total_rows = len(work_df)

    for processed, (idx, row) in enumerate(work_df.iterrows(), start=1):
        title = str(row["title"])
        artist = str(row["artist"])

        has_prev = not _missing(pd.Series([row["preview_url"]])).iloc[0]
        has_art = not _missing(pd.Series([row["artwork_url"]])).iloc[0]

        if not overwrite and has_prev and has_art:
            skipped += 1
            continue

        try:
            prev, art = _cached_itunes_preview(
                title, artist, refresh_if_empty=refresh_cache
            )
        except Exception as exc:  # keep going on request errors
            print(f"[warn] request failed for {title} - {artist}: {exc}")
            skipped += 1
            continue

        updated = False
        if overwrite or not has_prev:
            if prev:
                df.at[idx, "preview_url"] = prev
                filled_prev += 1
                updated = True
        if overwrite or not has_art:
            if art:
                df.at[idx, "artwork_url"] = art
                filled_art += 1
                updated = True

        if not updated:
            skipped += 1
        else:
            updates_since_save += 1
            total_updates += 1

        print(
            f"processed {processed}/{total_rows}; "
            f"filled preview: {filled_prev}; "
            f"filled artwork: {filled_art}; "
            f"skipped: {skipped}",
            flush=True,
        )

        if updates_since_save >= save_every:
            df.to_parquet(out_path, index=False)
            print(f"checkpoint saved to {out_path}")
            updates_since_save = 0

        if max_updates is not None and total_updates >= max_updates:
            print(f"Reached max-updates={max_updates}, stopping early.")
            break

        time.sleep(sleep_s)

    df.to_parquet(out_path, index=False)
    print(
        f"Done. wrote {len(df)} rows to {out_path}. "
        f"filled preview: {filled_prev}; filled artwork: {filled_art}; skipped: {skipped}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill iTunes preview and artwork URLs into a parquet."
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=PROC / "tracks_lastfm.parquet",
        help="Input parquet path.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output parquet path. Defaults to in-place overwrite.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Max rows to process this run.",
    )
    parser.add_argument(
        "--sleep",
        dest="sleep_s",
        type=float,
        default=0.2,
        help="Seconds to sleep between requests.",
    )
    parser.add_argument(
        "--save-every",
        dest="save_every",
        type=int,
        default=200,
        help="Save a checkpoint every N updates.",
    )
    parser.add_argument(
        "--only-missing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="If true, limit processing to rows missing preview or artwork.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Replace existing preview_url and artwork_url values.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        default=False,
        help="If cached iTunes entries are empty, hit the API again and refresh them.",
    )
    parser.add_argument(
        "--max-updates",
        type=int,
        default=None,
        help="Stop after this many successful updates (for dry runs).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backfill_itunes(
        parquet_path=args.parquet,
        out_path=args.out,
        batch_size=args.batch_size,
        sleep_s=args.sleep_s,
        save_every=args.save_every,
        only_missing=args.only_missing,
        overwrite=args.overwrite,
        max_updates=args.max_updates,
        refresh_cache=args.refresh_cache,
    )


if __name__ == "__main__":
    main()
