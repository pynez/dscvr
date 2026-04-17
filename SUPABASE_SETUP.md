# Supabase Setup

## 1. Create Project
1. Go to https://supabase.com and sign in
2. Click **New project**
3. Choose a name (e.g. `dscvr`), set a database password, pick a region close to your Fly.io region (Chicago → US East)
4. Wait ~2 minutes for provisioning

## 2. Run Migration
1. In your Supabase project, go to **SQL Editor → New query**
2. Paste the contents of `supabase/migrations/001_init.sql`
3. Click **Run**

## 3. Get Credentials
1. Go to **Project Settings → API**
2. Copy **Project URL** → this is `SUPABASE_URL`
3. Copy **anon public** key → this is `SUPABASE_ANON_KEY`

## 4. Set Environment Variables

### Backend (local dev)
Add to `backend/.env`:
```
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
```

### Backend (Fly.io)
```bash
fly secrets set SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
fly secrets set SUPABASE_ANON_KEY=eyJhbGci...
```

### Frontend (local dev)
Add to `frontend/.env`:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```
(No Supabase keys go to the frontend — all DB access goes through the backend.)

## 5. Disable Row Level Security (for anonymous access)
By default Supabase enables RLS. For anonymous user UUIDs, either:
- Disable RLS on all three tables (simplest for this project), or
- Add RLS policies that allow anonymous inserts/selects by user_id

To disable RLS (quickest):
```sql
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE interactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE taste_profile DISABLE ROW LEVEL SECURITY;
```

Run this in the SQL Editor after the migration.
