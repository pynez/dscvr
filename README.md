# dscvr
[dscvr.vercel.app](https://dscvr.vercel.app) — built by [victor pyne jr](https://pyne.dev)

*"No great discovery was ever made without a bold guess."*

---

dscvr is a music self-discovery platform. not a playlist generator. not a "what's popular" feed. six distinct tools designed to help you understand your relationship with music — why you listen, not just what to listen to next.

---

## the six tools

### explore *(start here)*
classic recommendation mode. enter a song or artist you love and dscvr surfaces 12 tracks with similar sonic and emotional DNA — pulled from a catalog of 17,000+ songs and scored via cosine similarity over audio feature embeddings. heart tracks you want to remember; they're saved to your session in a dedicated saved tracks area.

### soundtrack your life
describe a moment, mood, or scene in plain language — *"a late drive home after something goes wrong"*, *"the feeling right before everything changes"* — and dscvr interprets it through Gemini and returns a curated set of tracks that fit the scene. heart the ones that land. a summary card at the end collects everything you saved.

### blind taste test
a listening identity test. tracks play with all identifying information hidden — no artist, no title, no album art. just sound. you rate each one, and at the end dscvr reveals who made what. it's a direct confrontation with the gap between what you think you like and what you actually respond to.

### the time machine
explore the intersection of music history and your taste. pick a song or era and dscvr contextualizes it historically — surfacing what was happening in the world when it was made, and what else was being created in that same moment.

### algorithmic capture
a diagnostic tool. dscvr analyzes your inputs and measures how homogenized your taste has become — how much of what you listen to sounds the same, sits in the same corner of genre space. then it finds your escape routes: tracks that are adjacent enough to feel familiar but different enough to matter.

### the séance
pick a deceased artist. dscvr summons their living successors — artists making music today that carries the same spirit, technique, or emotional register. powered by Gemini's understanding of lineage and influence, not just metadata similarity. a summary card names the original artist and the threads connecting them to what came after.

---

## how it works

dscvr is built on a catalog of ~17,500 songs sourced from Last.fm and processed into a 50-dimensional audio feature space. recommendations are generated using cosine similarity over that space via a `CosineRecommender` model trained on the full catalog.

preview audio is resolved in real-time via the Deezer API (with YouTube fallback), so every track in every feature is playable — no expired links, no silent cards.

the more context-dependent features (soundtrack, séance, algorithmic capture) layer Google Gemini on top of the similarity engine to interpret natural language, reason about history and influence, and generate the summaries you see on results cards.

---

## stack

**frontend** — React + Vite, custom CSS (no component library), TikTok-style vertical scroll for track previews

**backend** — Python / FastAPI, deployed on Fly.io

**ML** — cosine similarity over Last.fm audio feature embeddings; `SearchIndex` for fast ANN lookup

**AI** — Google Gemini for natural language interpretation, historical context, and artist lineage reasoning

**audio** — Deezer API for real-time preview resolution; YouTube as fallback

---

## system architecture

```
frontend/          React app (Vite)
backend/
  src/recsys/
    service/
      api.py                   FastAPI endpoints
      features/                one module per dscvr tool
        explore.py
        soundtrack.py
        blind_taste_test.py
        time_machine.py
        algorithmic_capture.py
        seance.py
      preview_resolver.py      real-time audio URL resolution
    recommenders/
      cosine.py                similarity model
    data/
      artifacts/               trained model + feature matrix
      processed/               catalog metadata
```

---

*© victor pyne jr. all rights reserved.*
