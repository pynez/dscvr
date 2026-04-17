import argparse
from datetime import datetime
import pandas as pd

from src.recsys.config import PROC
from src.recsys.etl_spotify import build_dataset

def main():
    parser = argparse.ArgumentParser(description="Build Spotify tracks dataset.")
    parser.add_argument("--playlist", action="append", default=[], help="Playlist ID (can pass multiple)")
    parser.add_argument("--query", action="append", default=[], help="Search term (can pass multiple)")
    parser.add_argument("--artist", action="append", default=[], help="Artist ID (can pass multiple)")
    parser.add_argument("--out", default=str(PROC / "tracks.parquet"), help="Output parquet path")
    args = parser.parse_args()

    df = build_dataset(playlists=args.playlist, queries=args.query, artists=args.artist)
    if df.empty:
        print("No data produced.")
        return

    out = args.out
    pd.set_option("display.max_columns", 50)
    print(df.head(3))
    df.to_parquet(out, index=False)
    print(f"✅ Wrote {len(df)} rows to {out}")

if __name__ == "__main__":
    main()
