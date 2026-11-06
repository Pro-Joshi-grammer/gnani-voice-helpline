# Gnani — Telangana Scheme Helpline (rule-based edition)

Voice-first, source-grounded informational assistant for Telangana government
welfare schemes. Telugu in, Telugu out — every scheme claim carries a visible
citation from a curated JSON source pack, and eligibility is judged by a
progressive one-question-at-a-time interview. **The LLM never composes prose
and never decides eligibility** — it only parses the user's utterance into an
intent and answer slots; everything else is deterministic Python.

⚠️ Final official decisions always belong to government officials; the app
never issues one and never asks for Aadhaar/bank/OTP details.

## Structure

```
backend/    engine.py (rule core) + voice_server.py (stdlib HTTP adapter)
frontend/   index.html (single-file UI) + config.js (deploy knob) + vendored Silero VAD
data/       telangana_schemes_all.json — the single source of truth (13 schemes, 55 sources)
tests/      active unit suite (LLM/TTS mocked, no network)
tools/      live developer checks against a running server (not part of unittest)
_archive/   frozen pre-pivot RAG era + reference clone (NOT deployed, not pushed)
```

## Run locally

```bash
pip install -r requirements.txt      # only gnani-vachana==0.8.1
cp .env.example backend/.env         # then fill in your keys
python backend/voice_server.py       # → http://127.0.0.1:8000
```

Test: `python -m unittest discover -s tests` — no network needed.

## Deploy

See **[Deployment.md](Deployment.md)** — frontend → Cloudflare Pages (static
folder `frontend/`, set `window.GNANI_BACKEND_BASE` in `frontend/config.js`),
backend → any Python box behind HTTPS, and pair the origins via `WEB_ORIGINS`.

Configuration reference: [`backend/.env`](.env.example) (template; real file is
never committed). Architecture and agent-facing invariants: [`agents.md`](agents.md).
