# Environment Variables

## Backend (`backend/.env` / Fly.io secrets)

| Variable | Required | Description |
|---|---|---|
| `LASTFM_API_KEY` | ✅ | Last.fm API key — already set in Fly.io |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key for Soundtrack + Séance LLM calls |
| `YOUTUBE_DATA_API_KEY` | ✅ | YouTube Data API v3 key for audio preview fallback |
| `SUPABASE_URL` | ✅ | Supabase project URL (from Project Settings → API) |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon public key |

### Set Fly.io secrets (run once per new variable)
```bash
fly secrets set GEMINI_API_KEY=...
fly secrets set YOUTUBE_DATA_API_KEY=...
fly secrets set SUPABASE_URL=https://xxxx.supabase.co
fly secrets set SUPABASE_ANON_KEY=eyJhbGci...
```

## Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | ✅ | Backend URL — `http://127.0.0.1:8000` locally, `https://dscvr.fly.dev` in production |

> No Supabase keys go to the frontend. All DB access is proxied through the FastAPI backend.
