# agents.md — Gnani, Telangana Scheme Helpline (rule-based edition)

Orientation document for AI agents and humans working in `C:\Projects\gnani`.
Read this before changing anything: the project's value depends on a few
non-negotiable invariants that are easy to break accidentally.

- **Repo root:** `C:\Projects\gnani` (git; the pre-pivot RAG state was tagged
  `rag-legacy-pre-pivot` in the OLD history — 6 Nov restructure moved
  `legacy/`, root `vendor/` and `build.md` to `_archive/` and re-initialised
  git for GitHub, so that tag no longer exists in the active repo and the
  **leaked old key is no longer in pushable history**. It survives only in the
  local `.git_backup/` — still rotate it.)
- **Run from root:** `py backend/voice_server.py`;
  tests: `py -m unittest discover -s tests` (active). The frozen legacy suite
  lives in `_archive/` and is no longer run from the active tree.
- **Core stack:** Python 3.11 stdlib backend + one tiny LLM parse call
  (Featherless), single-file vanilla-JS frontend, JSON data pack
- **Deployment target:** Cloudflare Pages for `frontend/` (static); the Python
  backend runs on an owner-managed box and is reachable cross-origin via
  `WEB_ORIGINS`
- **Timeline:** hackathon challenge; submission deadline is **10 Nov 2026**

## 1. Aim (6 Nov 2026 pivot)

**Gnani** is a voice-first, source-grounded informational assistant for
Telangana government welfare schemes. On 6 Nov the owner replaced the RAG
pipeline with a **rule-based progressive interview**: the whole conversation is
a walk through `data/telangana_schemes_all.json` (13 schemes / 55 sources) —
scheme facts answered straight from the pack, and an eligibility check that
fills **one key-pair per question turn** until an early fail (cited) or a full
pass (citing every criterion). The only LLM work left is **one tiny parse call
per turn** that maps the user's freeform Telugu utterance to an intent and
answer slots. The LLM never decides eligibility and never composes prose.

The product is deliberately **NOT**: a chatbot with a microphone bolted on, an
official government channel, a document drop, or a system that guesses. Where
the pack's sources do not cover something, the honest behaviour is to say so
and point at the official portal.

## 2. Non-negotiable rules (break these = project failure)

1. **Never fabricate** scheme facts, amounts, dates, documents, procedures,
   contacts or URLs — not in answers, not in parse replies, not in citations.
   Everything shown or spoken comes from the JSON pack verbatim (with its
   `source_ids`) or from honest fixed replies (`GREETING_TE`, `UNRELATED_TE`,
   `NOT_IN_SOURCES_TE`, …).
2. **Pack confidence rules are enforced in replies:** facts with `medium`
   confidence carry `MEDIUM_NOTE_TE`, `low` facts carry `LOW_NOTE_TE`
   ("sources disagree — don't rely"), and any scheme whose `status` ∉ {active}
   gets `status_note` **before** benefits (`STATUSES_NEEDING_A_NOTE`).
3. **Topics under `unknown_in_sources` get their honest notice once**, then the
   flow continues. They are never turned into criteria.
4. **The parse contract is never loosened:** `_check_parse_shape` validates the
   model's intent/scheme_id/answers/fact_ids against the pack's vocabulary;
   invalid or unreachable ⇒ one bounded re-ask, then `_fallback_parse`
   (deterministic keyword lexicon) keeps the turn alive honestly.
5. **The LLM never decides eligibility.** Evaluation is pure Python
   (`_first_failure`/`_first_pending`/`_apply_extracted_facts`), verdicts come
   from the pack's `criteria[].required` values, and the final decision is
   always explicitly left to officials (`FINAL_DECISION_TE`).
6. **Cross-scheme isolation:** moving to a different scheme wipes criteria
   facts (`_new_scheme_state`). Facts never leak between schemes.
7. **No secrets in the browser.** `GNANI_API_KEY` / `FEATHERLESS_API_KEY` are
   read only by server processes from `backend/.env`; `frontend/config.js`
   holds only a base URL.
8. **No persistence of user data.** No audio, transcripts, or request bodies in
   storage or logs; session state is transient, lives in the browser between
   turns, and is bounded (`_clean_state`, ≤12 KB) inside it.
9. **Do not request/collect** Aadhaar numbers, bank details, OTPs — the UI
   warns users not to share them (`ABOUT_TE` says so too).

## 3. System architecture

```
                                Browser (frontend/index.html)
   ┌────────────────────────────────────────────────────────────────────┐
   │  Meta AI-style voice UI: orb / transcript / composer / sheet       │
   │  - end-of-turn detection: vendored Silero VAD (/vendor/vad/)       │
   │  - onSpeechEnd → 16 kHz PCM16 WAV → POST /api/voice/transcribe     │
   │  - session state: serverState + history; criteria_facts accumulate │
   │    the progressive key-pairs between turns (state, transient)      │
   │  - fetch base from /config.js (window.GNANI_BACKEND_BASE)          │
   └──────────────┬─────────────────────────┬───────────────────────────┘
                  │ multipart WAV           │ JSON (question/state/history)
                  ▼                         ▼
        backend/voice_server.py — stdlib ThreadingHTTPServer :8000
        .env loaded here; keys never leave this process
   ┌────────────────────────────────────────────────────────────────────┐
   │ GET  /               → frontend/index.html                         │
   │ GET  /config.js      → frontend/config.js (deploy target)          │
   │ GET  /vendor/*       → frontend/vendor (path-safe, MIME-typed)     │
   │ GET  /health         → {ok, gnani_key_configured}                  │
   │ OPTIONS *            → preflight (CORS via WEB_ORIGINS)            │
   │ POST /api/voice/transcribe  → Gnani Prisma STT (te-IN)             │
   │ POST /api/voice/synthesize    → Gnani Timbre TTS (WAV; fallback)   │
   │ POST /api/voice/synthesize_stream → streaming PCM as NDJSON        │
   │ POST /api/assistant/query     → engine.route_turn(...)             │
   └───────────────────────────────┬────────────────────────────────────┘
                                   ▼
        backend/engine.py — the rule core (one tiny LLM call + pure Python)
        1. _parse_turn   tiny strict-JSON call: utterance → intent +
                         scheme_id + answers + fact_ids (`_chat_parse`,
                         one bounded re-ask; reasoning-channel fallback)
        2. _check_parse_shape  schema/vocabulary gate (never loosened);
                         failure ⇒ _fallback_parse keyword lexicon
        3. deterministic lanes: scheme info from facts/summary (+status
                         prefix + confidence notes + offer), progressive
                         interview (one question per turn), stop/switch,
                         fixed conversation replies
        4. evaluator: _first_failure (early fail, cited) →
                         _first_pending (next unfilled key-pair) → pass
                         reply citing every criterion + FINAL_DECISION_TE
        5. citations built straight from pack sources →
                         `_pack_citation` (id/title/issuer/published_date/
                         section/excerpt/source_url/scheme_id/tier)
        fail-safe: any exception ⇒ honest non-guessing replies

   External providers (server side only):
   - Featherless: the tiny parse LLM call (model from FEATHERLESS_LLM_MODEL;
     self-hosted OpenAI-compatible fallback via LLM_* / SELF_HOSTED_*)
   - Gnani Vachana SDK: Prisma STT + Timbre TTS (api.vachana.ai)
```

**Key design points:**

- `engine.py` is UI-independent and provider-neutral (env-config switches
  between Featherless and a self-hosted endpoint). Frontends call
  `route_turn()`; no other entry point should be added.
- The pack is the single source of truth; `load_pack()` re-reads when the file
  changes on disk (no index build step any more) and `_sanitize_pack` drops
  malformed criteria/facts rather than ever inventing a rule.
- Fixed honest Telugu reply blocks (greeting/about/unrelated/unknown/
  not-in-sources/status/confidence notes) — no LLM prose composition anywhere.
- `stage_timings` (`parse_llm`, `parse_retry_llm`, `retry_wait`, `total`,
  `other`) rides on every `route_turn` result; the browser's timing chip shows
  `parse`/`parse↻`.

## 4. Conversation policy (implemented)

| Intent (from the parse call) | Retrieval? | LLM? | Result |
|---|---|---|---|
| `greeting`/`about` | no | parse only | fixed honest lines, no citations |
| `scheme_info` | no | parse only | deterministic facts answer (+confidence notes, how-to-apply, portal, **offer** of the check when criteria exist) |
| `start_check` | no | parse only | first criterion question `[C1]` |
| `check_answer` | no | parse only | fills the pending key-pair → next question, or early fail (cited), or full pass (cited) |
| `stop_check` | no | parse only | honest stop; check resets without sticking |
| `switch_scheme` | no | parse only | new scheme info + fresh state (old facts wiped) |
| `unrelated` | no | parse only | honest decline + privacy warning |

**Progressive interview flow:** `offered → active → done`. While a check runs,
ordinary conversation (greeting/about/unrelated) answers politely and lets the
check wait (pending criterion untouched). Facts volunteered out of order are
merged; the first failed criterion stops with a result citing that criterion's
source; all criteria passing produces an "appears eligible" summary citing
every criterion, with the final decision explicitly left to officials.
Malformed or out-of-value-space values are re-asked, never judged.

## 5. File-by-file guide

### Root
| File | What it is |
|---|---|
| `agents.md` | This document. |
| `build.md` | The pre-pivot plan (§1–15). **Architecture sections are superseded by this file**; §evaluation is still useful before the demo. (6 Nov: moved to `_archive/`.) |
| `VOICE_NOTES.md` | Voice interaction loop + honest limitations (STT unverified with real Telugu audio; REST STT not streaming). |
| `requirements.txt` | `gnani-vachana==0.8.1` — the only pip dependency. |

### backend/
| File | What it is |
|---|---|
| `engine.py` | **The rule core** (see §3). Also loads `backend/.env`. |
| `voice_server.py` | Stdlib `ThreadingHTTPServer` adapter on 127.0.0.1:8000. Serves frontend/index.html at `/`, `/config.js`, `/vendor/*` (path-safe, MIME-typed); `/health`; CORS via `WEB_ORIGINS` on every response plus `do_OPTIONS` preflight; `/api/voice/transcribe` (multipart, ≤10 MB, Prisma STT, `elapsed_ms`); `/api/voice/synthesize` + `/synthesize_stream` (Timbre TTS; `speech_text()` strips citation markers/URLs/markdown from spoken text only, one fixed Telugu "link is on screen" line when a URL was removed; `pcm_stream_lines` NDJSON framing with meta/b64/done lines); `/api/assistant/query` (validates payload, forwards to `engine.route_turn`, attaches `elapsed_ms`). Logs request type only — never bodies, transcripts, audio, or keys. Still uses deprecated `cgi` (fine on 3.11; replace when convenient). |
| `.env` | Local-only config: `GNANI_API_KEY`, `GNANI_LANGUAGE=te-IN`, `GNANI_TTS_MODEL=timbre-v2.5`, `GNANI_TTS_VOICE=Suhana`, `HOST/PORT`, `FEATHERLESS_BASE_URL/API_KEY/EMBEDDING_MODEL/LLM_MODEL` (the parse call model is `FEATHERLESS_LLM_MODEL`; `FEATHERLESS_MODEL`/`LLM_MODEL` accepted as aliases), self-hosted fallbacks (`SELF_HOSTED_*`/`LLM_*`/`EMBEDDING_*`), and `WEB_ORIGINS` (comma-separated origins allowed to call the API from the browser; add the Cloudflare Pages origin here). **Secrets: never commit, never log, never send to the client. Rotate the Featherless key (it leaked in the local git snapshot).** |

### frontend/
| File | What it is |
|---|---|
| `index.html` | Single-file Meta-AI-style voice UI (unchanged design; VAD end-of-turn detection; streaming TTS playback; per-turn timing chip with `parse` labels; sources bottom-sheet with citation cards). All API calls are prefixed with `API_BASE` from `config.js` — deploy to Cloudflare Pages as-is. |
| `config.js` | `window.GNANI_BACKEND_BASE` — empty locally (the backend serves this page), set to the deployed backend URL for Cloudflare Pages. **The only file to edit at deploy time; never put keys here.** |
| `vendor/vad/` | Vendored `@ricky0123/vad-web` v0.0.31 runtime assets (bundle + worklet + Silero v5 ONNX + ORT 1.22 wasm glue); served from `/vendor/` so the demo needs no CDN. |

### data/
| File | What it is |
|---|---|
| `telangana_schemes_all.json` | **The single source of truth** (13 schemes, 55 sources). Keys: `meta`, `schemes[{scheme_id, name_en, name_te, category, status, status_note, summary_en, summary_te, facts[{id, claim, confidence, source_ids}], criteria[{id, question_te, answer_type, required, source_id, basis, fail_message_te, confidence}], unknown_in_sources, how_to_apply, portal}]`, `sources{source_id → {title, publisher, url, date, tier}}`. Confidence rules live in `meta.confidence_levels`. Any change here needs no rebuild — `load_pack()` picks it up by mtime. |
| `telangana_schemes_all.md` | The owner's narrative source pack + confidence/tier rules (human reference; `re-check medium/low claims` warnings). |

### tests/ (active suite; LLM and TTS fully mocked)
| File | What it covers |
|---|---|
| `test_engine.py` | The rule engine: fixed conversation replies with no citations and no LLM prose; scheme-info answers built from pack facts + citation integrity (source_url present, `[C1]` markers); uncoverable fact requests abstain instead of substituting; zero-criteria schemes never offer a check; status-note-before-benefits for non-active statuses; the full interview (accept → one criterion question per turn → facts merged, early fail stops with the criterion's own source, full pass cites every criterion + final decision left to officials, stop without sticking, cross-scheme wipe, `unknown_in_sources` noticed once); answer-slot safety (out-of-space parse values trigger the deterministic fallback and are never stored or judged; LLM-down lexicon fallback routes schemes and judges honest answers). |
| `test_voice_server.py` | `query_payload` forwarding contract (question/state/history/evidence as-is to `engine.route_turn`), invalid payloads rejected; `speech_text` tests (markers/URLs stripped, markdown labels kept, Telugu untouched, URL notice exactly once). |
| `test_voice_stream.py` | `pcm_stream_lines` NDJSON framing (meta line, lazily-yielding b64 lines, `done` last). |

Run: `py -m unittest discover -s tests` (40 cases, LLM/TTS fully mocked).
`test_benchmark_stats.py` and the legacy suite moved to `_archive/` with the
rest of the RAG era.

### legacy/ (frozen, not deleted — reference for semantics; 6 Nov: moved to `_archive/legacy/`)
`rag.py`, `index_kb.py`, `KB/`, plus its own green test suite (now under
`_archive/` too; not run from the active tree). The evaluator in
`engine.py` is a verbatim port of legacy's tested `_first_failure`/
`_first_pending`/`_apply_extracted_facts`; the response schema
(`decision/kind/answer_text/citations/next_steps/state`) is the legacy schema,
so the frontend needed minimal changes.

### tools/
`check_rule_flow.py` — the one developer check that targets the rule engine:
scripted greeting → scheme info → running interview against a running adapter
(live against real providers, **not** part of unittest). The legacy-core
checks (`benchmark_stages.py`, `check_ttft.py`, `check_stream_*.py`,
`check_flow_*.py`, `check_parallel_turn.py`, `check_llm_model.py`,
`check_turn5_route.py`) moved to `_archive/tools/` with the RAG era.

## 6. Status (as of 6 Nov 2026)

- Restructure complete: `backend/` + `frontend/` + `data/`; RAG era, root
  `vendor/` reference clone and `build.md` archived to `_archive/` (6 Nov
  fresh-init: not in pushable history, legacy 60-case suite green at freeze).
- Rule engine live-verified against Featherless: scheme match, offer, accept,
  first criterion question, answer applied and flow advanced (unknown notices
  shown once each).
- 40 active tests green (fresh layout).
- CORS + static serving verified over HTTP (index, config.js, vendor,
  preflight, allowed/disallowed origins, two fallback turns).
- Cloudflare Pages deploy path defined (`frontend/config.js` + `WEB_ORIGINS`);
  nothing deployed yet.

## 7. Not yet done (owner + agent, before the 10 Nov deadline)

1. **Featherless key rotation** (user-only dashboard) — the leaked key is in
   `backend/.env` AND in the local snapshot history; rotate before any push.
2. **Verification of pack claims** — several facts are `medium`/`low`
   confidence from their own definition; the pack instructs re-checking before
   public demo. Criteria answer spaces in particular should be spot-checked
   against current official pages.
3. **`facts[].claim` lines are English** (per the pack's language note). The
   info answer currently shows the English claims; consider an owner decision:
   (a) keep English claims with sources, or (b) author Telugu claim lines in
   the pack. `summary_te` is usually more speech-friendly for the default.
4. **Parse-call latency** — observed 2.6–18 s on Featherless (cold start?). If
   it stays >5 s per answer turn, consider a shorter parse prompt, a smaller
   model, or moving the granular yes/no answers to the lexicon-confirmed
   fingerprint. Measure a full turn before deciding.
5. **STT still unverified with real Telugu audio** (no sample in repo).
6. **Cloudflare Pages deployment** (backend on an owner box; set
   `window.GNANI_BACKEND_BASE` in `frontend/config.js` and `WEB_ORIGINS` in
   `backend/.env` accordingly).
7. **Evaluation set** for the hackathon submission: fixed scripted Q&A runs
   through `tools/check_rule_flow.py` plus measured results.
8. `cgi` deprecation (3.13); repo hygiene: none pending except key rotation.

## 8. Known issues & agent quick-workbook

**Common agent tasks:**
- **Extend a scheme:** edit `data/telangana_schemes_all.json` only — add
  facts/criteria/`unknown_in_sources` with real `source_ids`; no rebuild step.
  The engine enforces every criterion carries a source; malformed entries are
  dropped silently (verify by running tests after big edits).
- **Tune the flow:** OFFER flow lives in `_scheme_info_answer` + `route_turn`
  lanes; evaluator semantics in the pure-Python section of `engine.py`.
- **Tune the parser:** prompts live in `_parse_turn` (system message) and the
  gate in `_check_parse_shape` — keep the strict-JSON contract; the fallback
  lexicons in `_fallback_parse` are only for provider-down turns.
- **Debug a failed turn:** failures collapse to the honest replies; reproduce
  in-process (`py -X utf8 -c "import sys; sys.path.insert(0,'backend');` +
  `import engine; engine.route_turn(...)"`); cp1252 consoles garble Telugu, so
  write UTF-8 explicitly or run with `-X utf8`.
- **Frontend:** single file, no build step; keep citation-card keys in sync
  (`renderSources` expects id/title/issuer/published_date/section/excerpt/
  source_url/scheme_id; `stage_timings` short map currently keys on
  `parse_llm`/`parse_retry_llm`).

**Style conventions:** stdlib-first (no new deps), bounded/sanitised inputs
everywhere (state/history/evidence are each capped), honest failure over
fabrication, Telugu-first responses fed from the pack, comments explain *why*
invariants exist.
