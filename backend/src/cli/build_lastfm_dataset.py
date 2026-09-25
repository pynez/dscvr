import argparse
import json

from src.recsys.config import PROC, SEEDS
from src.recsys.etl_lastfm import build_lastfm_dataset


def main():
    parser = argparse.ArgumentParser(description="Build/refresh the Last.fm tracks catalog.")
    parser.add_argument("--out", default=str(PROC / "tracks_lastfm2.parquet"))
    parser.add_argument("--chart-pages", type=int, default=200, help="chart.getTopTracks caps at 200")
    parser.add_argument("--geo-pages", type=int, default=5)
    parser.add_argument("--country", action="append", default=[], dest="countries")
    parser.add_argument(
        "--tag-pages",
        default=None,
        help='JSON dict of genre tag -> page count, e.g. {"jazz":3,"metal":9}',
    )
    parser.add_argument("--no-seeds", action="store_true", help="Skip data/seeds/*.json")
    parser.add_argument("--no-expand-similar", action="store_true")
    parser.add_argument("--similar-per-track", type=int, default=3)
    parser.add_argument("--similar-max-new", type=int, default=3000)
    parser.add_argument("--sleep", type=float, default=0.05, dest="sleep_s")
    parser.add_argument("--no-itunes", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=1000)
    args = parser.parse_args()

    tag_pages = json.loads(args.tag_pages) if args.tag_pages else None

    build_lastfm_dataset(
        out_path=args.out,
        chart_pages=args.chart_pages,
        geo_pages=args.geo_pages,
        countries=args.countries or None,
        seed_dir=None if args.no_seeds else SEEDS,
        tag_pages=tag_pages,
        expand_similar=not args.no_expand_similar,
        similar_per_track=args.similar_per_track,
        similar_max_new=args.similar_max_new,
        sleep_s=args.sleep_s,
        itunes=not args.no_itunes,
        checkpoint_every=args.checkpoint_every,
    )


if __name__ == "__main__":
    main()
