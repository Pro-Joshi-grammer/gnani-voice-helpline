# Deployment.md — Gnani, Telangana Scheme Helpline

Current project condition, module map, tech stack, dependencies and deployment
steps. Written 6 Nov 2026 after the rule-based pivot.

> **Layout update (6 Nov, fresh-init for GitHub):** the frozen RAG era
> (`legacy/`), the repo-root `vendor/` reference clone, `build.md` and old
> benchmark artifacts were moved to `_archive/` (gitignored, not pushed).
> History was re-initialised (`main`); the pre-pivot state is no longer in this
> repo's pushable history — the old `.git` is preserved locally as `.git_backup/`
> only. The legacy test suite therefore does not exist in the active tree.
> The runtime path `frontend/vendor/vad/` is unrelated and stays tracked.
>
> **Key note:** the old Featherless key value still exists in `.git_backup/`
> history and in the local `backend/.env` — rotate it when convenient. The
> fresh repo's history contains **no keys** (`.env` is ignored; only
> `.env.example` with placeholders is tracked), so pushing this repo is safe
> from the earlier local-history leak.

---

## 1. Product snapshot

| | |
|---|---|
| **What it is** | Voice-first, source-grounded informational assistant for Telangana government welfare schemes. Telugu/Telugu-English in, Telugu out; every scheme claim carries a visible citation; eligibility is judged by a progressive one-question-at-a-time interview over a curated JSON source pack. |
| **Engine model** | **Rule-based (since 6 Nov 2026).** The only LLM work per turn is one tiny strict-JSON parse call (utterance → intent + answer slots). Eligibility evaluation, replies, citations and flow control are pure Python. |
| **Knowledge** | `data/telangana_schemes_all.json` — 13 schemes, 55 sources, facts/criteria/unknown-topics with confidence levels. Hot-reloaded on file change; no build step. |
| **State** | Transient, lives in the browser (`serverState.criteria_facts` accumulates the interview key-pairs). Bounded server-side to ≤12 KB per turn. Nothing about users is logged or stored. |
| **Status** | Feature-complete for a local demo; **not yet deployed**. Deadline-driven: submission 10 Nov 2026. |

## 2. Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, stdlib only (`http.server.ThreadingHTTPServer`, `json`, `re`, `threading`) — no framework |
| LLM (parse call) | Featherless API (OpenAI-compatible `/chat/completions`), model `FEATHERLESS_LLM_MODEL`; temperature 0, strict JSON out; self-hosted OpenAI-compatible endpoint supported as fallback |
| Speech | Gnani Vachana SDK (`gnani-vachana==0.8.1`): Prisma STT (te-IN) + Timbre TTS v2.5 (voice `Suhana`, streaming PCM + whole-file WAV fallback) |
| Frontend | Single-file vanilla JS (`frontend/index.html`), no build step; WebAudio playback; vendored `@ricky0123/vad-web` v0.0.31 (Silero VAD v5 + ONNX Runtime Web 1.22 wasm, zero CDN) |
| Data | Plain JSON pack (`data/telangana_schemes_all.json`) + narrative MD reference |
| Tests | stdlib `unittest`, fully mocked LLM/TTS (no network in unit runs) |
| Hosting | **Frontend: Cloudflare Pages (static)** · Backend: owner-managed Python box (any VM/pipenv), reachable under HTTPS |

## 3. Repository layout / modules

```
gnani/
├── backend/                  ← runs only on the server box
│   ├── engine.py             CORE — rule engine (§3.1)
│   ├── voice_server.py       HTTP adapter: static + STT/TTS + /api/assistant/query (§3.2)
│   └── .env                  SECRETS (never committed, never shipped to browser)
├── frontend/                 ← deploy this folder to Cloudflare Pages
│   ├── index.html            whole UI (orb voice mode, transcript, sources sheet)
│   ├── config.js             deploy-time config: window.GNANI_BACKEND_BASE
│   └── vendor/vad/           VAD runtime assets (bundle, worklet, ONNX, ORT wasm)
├── data/
│   ├── telangana_schemes_all.json   single source of truth (13 schemes)
│   └── telangana_schemes_all.md     owner's narrative pack + confidence rules
├── legacy/                   frozen pre-pivot RAG code + its own 60-test suite
│   ├── rag.py, index_kb.py, KB/
│   └── tests/                still green; kept for semantics reference
├── tests/                    active suite (40 cases): engine + adapter + stream framing
├── tools/                    live developer checks (not part of unittest)
│   └── check_rule_flow.py    scripted full interview against a running adapter
├── vendor/                   reference clone of github.com/ricky0123/vad (NOT runtime; gitignored)
├── agents.md                 agent orientation + invariants
├── build.md                  pre-pivot plan (architecture sections superseded)
├── VOICE_NOTES.md            voice loop + honest limitations
└── requirements.txt          gnani-vachana==0.8.1 (the only pip dependency)
```

### 3.1 `backend/engine.py` — the rule core

- `_parse_turn` / `_chat_parse`: the turn's single tiny LLM call (strict JSON:
  `{intent, scheme_id, answers, fact_ids}`), one bounded re-ask on malformed
  output; reasoning-channel fallback for reasoning-mode serving.
- `_check_parse_shape`: schema gate — intent ∈ fixed set, scheme ids must exist
  in the pack, answer values must be inside the criterion's value space.
  **Never loosened**; failure ⇒ `_fallback_parse` (deterministic keyword
  lexicon) keeps the turn alive so the flow never breaks when the provider is
  down.
- `SCHEME_KEYWORDS` + `_keyword_scheme`: deterministic scheme routing by the
  pack's own names/tokens (Telugu + English; disambiguates the three
  Mahalakshmi variants).
- Pure-Python evaluator (ported verbatim from the tested legacy core):
  `_criterion_allowed`, `_criterion_failed`, `_first_failure` (early fail),
  `_first_pending` (next unfilled key-pair), `_apply_extracted_facts` (merges
  facts volunteered out of order; malformed values are re-asked, never judged).
- Honesty machinery: `_status_prefix` (non-active statuses get `status_note`
  before benefits), `_confidence_note` (medium/low caveats),
  `_attach_unknown_notice` (`unknown_in_sources` topics noticed exactly once),
  `NOT_IN_SOURCES_TE`, `FINAL_DECISION_TE` (final decision always left to
  officials).
- Citations from the pack: `_pack_citation` / `_facts_evidence` /
  `_criteria_evidence` / `_dedupe_citations` → cards with
  `id/title/issuer/published_date/section/excerpt/source_url/scheme_id/tier`.
- Turn timing: `_profile_turn`/`_timed` → `stage_timings`
  (`parse_llm/parse_retry_llm/retry_wait/total/other`) on every result.
- Cross-scheme isolation: `_new_scheme_state` wipes criteria facts on switch.
- Entry points: `route_turn(question, state, history, evidence)` and alias
  `answer()`. `load_pack()` re-reads the JSON when its mtime changes.

### 3.2 `backend/voice_server.py` — the adapter

- Stdlib `ThreadingHTTPServer` on `HOST:PORT` (default `127.0.0.1:8000`),
  threaded; logs request **type only** — never bodies, transcripts, audio, keys.
- Static: `/` → `frontend/index.html`, `/config.js` → `frontend/config.js`,
  `/vendor/*` → `frontend/vendor/vad/**` (path-safe, MIME-typed).
- `GET /health` → `{ok, gnani_key_configured}`.
- CORS: every response passes through a header choke point honouring the
  `WEB_ORIGINS` env var (comma-separated allowed origins; `*` = any) +
  `do_OPTIONS` preflight (204). Requests without an `Origin` header (local
  same-origin use) get no CORS headers; disallowed origins get none either.
- `POST /api/voice/transcribe` — multipart WAV (≤10 MB) → Gnani Prisma STT;
  returns `{transcript, provider, elapsed_ms}`.
- `POST /api/voice/synthesize` — text → `speech_text()` cleaning (strips
  `[Cn]` markers, URLs and markdown **from speech only**; appends one fixed
  Telugu "link is on screen" line when a URL was removed) → Timbre WAV;
  TTS time in `X-Elapsed-Ms` header. (Fallback path.)
- `POST /api/voice/synthesize_stream` — same cleaning → Gnani Timbre SSE
  raw-PCM re-framed as NDJSON (`meta` → `b64` chunk lines → `done` with
  `first_ms/elapsed_ms`), flushed line-by-line; playback starts before
  synthesis finishes. `pcm_stream_lines` is unit-tested for framing/laziness.
- `POST /api/assistant/query` — payload validation (question ≤1200 chars,
  state/history/evidence types) → `engine.route_turn(...)`; attaches
  `elapsed_ms` (whole rule-engine stage).
- Known wart: uses the deprecated `cgi` module (removed in Python 3.13;
  fine on the current 3.11 runtime — replace when convenient).

### 3.3 `frontend/` — static UI (Cloudflare Pages target)

- Meta-AI-style voice mode: gradient orb (breathing = listening, waveform =
  speaking), transcript turns with citation buttons, live recognised-speech
  line, Stop pill, hands-free auto re-arm, sources bottom-sheet (side panel
  ≥1100 px), error/retry states, reduced-motion support, mobile layout.
- End-of-turn: Silero VAD (`window.vad.MicVAD`, model v5, `startOnLoad:false`),
  assets all vendored under `/vendor/vad/`; `onSpeechEnd` → 16 kHz PCM16 WAV
  → `/api/voice/transcribe`.
- Session state in the browser: `serverState` (topic/scheme/mode/
  `criteria_facts` key-pairs/pending criterion/notice list) + recent history;
  rewritten by the server's bounded cleaner every turn; a page refresh resets
  everything.
- Streaming speech: `/api/voice/synthesize_stream` NDJSON → AudioBuffers →
  gapless scheduled playback; abortable mid-stream (Stop); falls back to the
  whole-file WAV endpoint on stream failure.
- Per-turn timing chip: `⏱ STT · LLM · TTS` with the server's
  `stage_timings` breakdown (`parse`, `parse↻`, `sleep`).
- `config.js`: the **only** deploy-time file —
  `window.GNANI_BACKEND_BASE = "https://<backend-host>"` (empty locally).

## 4. Dependencies

Runtime (single pip dependency, install via `pip install -r requirements.txt`):

| Package | Why |
|---|---|
| `gnani-vachana==0.8.1` | Prisma STT + Timbre TTS SDK (pulls in `requests`, `websockets`) |

Everything else is stdlib. No DB, no vector store, no task queue, no CDN at
runtime. `requests` is also used directly by `engine.py` for the parse call
via the already-present dependency.

External services (server-side only, keys in `backend/.env`):

| Service | Used for | Env names |
|---|---|---|
| Featherless API | the tiny parse LLM call | `FEATHERLESS_BASE_URL`, `FEATHERLESS_API_KEY`, `FEATHERLESS_LLM_MODEL` (aliases `FEATHERLESS_MODEL`/`LLM_MODEL`) |
| Gnani Vachana (api.vachana.ai) | STT + TTS | `GNANI_API_KEY`, `GNANI_LANGUAGE=te-IN`, `GNANI_TTS_MODEL`, `GNANI_TTS_VOICE` |
| (optional) self-hosted OpenAI-compatible endpoint | parse-call fallback | `SELF_HOSTED_*` / `LLM_*` |

## 5. Configuration (backend/.env)

```
GNANI_API_KEY=…            # StT/TTS key (required for voice)
GNANI_LANGUAGE=te-IN
GNANI_TTS_MODEL=timbre-v2.5
GNANI_TTS_VOICE=Suhana
HOST=127.0.0.1
PORT=8000
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
FEATHERLESS_API_KEY=…      # ROTATE before any push (leaked in local snapshot history)
FEATHERLESS_LLM_MODEL=…
WEB_ORIGINS=               # comma-separated browser origins allowed cross-origin,
                           # e.g. http://localhost:3000,https://gnani.pages.dev
# optional provider switches/fallbacks: LLM_USE_FEATHERLESS, SELF_HOSTED_*, LLM_*, EMBEDDING_*
```

Rules: secrets never leave server processes; never logged; never sent to the
client; `frontend/config.js` contains **no** keys, only a base URL.

## 6. How to run locally

```
py -m pip install -r requirements.txt
py backend/voice_server.py                  → http://127.0.0.1:8000
py -m unittest discover -s tests            # active suite, 40 cases, mocked
py -X utf8 tools\check_rule_flow.py         # live scripted interview (needs running adapter)
py -X utf8 tools\check_rule_flow.py         # live scripted interview (needs running adapter)
```

First use: open the page, tap the orb, ask e.g. "ఇందిరమ్మ ఇల్లు పథకం చెప్పు" →
info answer with `[C1]` citations and an offered eligibility check → accept →
one question per turn → early fail (cited) or full pass (citing every
criterion, decision left to officials).

## 7. Deployment (target: Cloudflare Pages + owner-run backend)

**Frontend (Cloudflare Pages):**
1. Pages project → **Upload assets** or connect the repo, prod dir = `frontend/`. No
   build step, no framework preset.
2. At deploy time edit `frontend/config.js` →
   `window.GNANI_BACKEND_BASE = "https://<your-backend-host>"`.
3. Ensure the backend's `WEB_ORIGINS` includes the Pages origin(s)
   (`*.pages.dev` plus any custom domain), otherwise the browser's calls are
   blocked by CORS.

**Backend (any Python box with HTTPS):**
1. Extract this repo (backend/, data/), `pip install -r requirements.txt`,
   fill `backend/.env` (rotate the Featherless key first).
2. Run behind a TLS terminator or set `HOST=0.0.0.0` and reverse-proxy
   (`https://<host>` → `127.0.0.1:8000`). CORS is already per-origin.
3. Health: `GET /health` → `{"ok": true, "gnani_key_configured": true}`.
4. Keep `data/telangana_schemes_all.json` next to the backend (or point
   `GNANI_PACK_PATH` at it); content updates need no restart — mtime re-read.

Split-hosting note: the engine stays in Python by owner decision; Cloudflare
runs only the static frontend. If the owner later wants edge-only, `legacy/`
and the JSON pack are portable, but that is a different project decision.

## 8. Current condition / gaps before submission (10 Nov 2026)

Verified working (6 Nov):
- Full scripted interview live end-to-end: scheme info + citations → offer →
  accept → progressive questions → pass reply citing every criterion;
  cross-scheme switch wipes facts; stop resets without sticking.
- HTTP verified: static + config + vendor, `/health`, CORS allow **and deny**,
  preflight, two fallback turns with the LLM key empty.
- Both test suites were green at restructure time (40 active; legacy 60 green in `_archive/`, no longer run from the active tree).

Open items:
1. **Rotate the Featherless API key** (user-only dashboard) — leaked in
   `backend/.env` and in the local git snapshot history; rotate before push.
2. **Deploy** (§7) — nothing is deployed yet; all runs currently local.
3. **Pack verification** — spot-check medium/low-confidence claims and criteria
   answer spaces against current official pages before a public demo.
4. **Language review (owner decision)** — `facts[].claim` lines are English
   (per the pack's own note); info answers show English claim lines with
   Telugu framing. Either accept or author Telugu claim lines in the JSON.
5. **STT with real Telugu audio** — not yet verified end-to-end (no sample in
   repo); code-mixing behaviour untested.
6. **Parse-call latency** — ~2.4–2.9 s per turn warm (first calls up to ~18 s,
   provider cold start). Acceptable, but measure a full demo turn; if slower
   than expected, shorten the parse prompt or switch model.
7. `cgi` deprecation (Python 3.13 removal; fine on 3.11).
8. Demo recording + measured results for the submission.
