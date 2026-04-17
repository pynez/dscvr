from src.recsys.etl_lastfm import _lastfm

def main():
    # Simple ping: should return JSON with a 'results' key
    res = _lastfm({"method":"track.search", "track":"Snooze", "limit":1, "autocorrect":1})
    print("OK keys:", list(res.keys())[:5])

if __name__ == "__main__":
    main()
