# Gnani — Telangana Welfare Scheme Voice Helpline

A voice-first, source-grounded Telugu informational assistant for Telangana government welfare schemes. Every spoken answer carries a visible citation from a curated source pack, and eligibility is decided by a progressive one-question-at-a-time interview in pure Python — the LLM never composes prose and never decides eligibility.

## Images

<!-- Screenshot 1: paste the GitHub-uploaded image URL here after first push
<img width="925" height="623" alt="voice UI" src="PASTE-URL-1" />
Main voice UI (orb idle state, transcript, composer)
-->

<!-- Screenshot 2:
<img width="981" height="1013" alt="citations" src="PASTE-URL-2" />
Answers screen with citation cards in the sources sheet
-->

## System

|                   |                                                              |
| ----------------- | ------------------------------------------------------------ |
| Engine model      | **Rule-based progressive interview** — deterministic Python lanes; 1 tiny strict-JSON parse call per turn |
| Knowledge base    | JSON source pack — **13 schemes, 55 sources**, facts / criteria / unknown-topics with confidence levels |
| Backend           | Python 3.11 **stdlib only** (`http.server.ThreadingHTTPServer`), single pip dependency |
| Parse LLM         | Featherless, OpenAI-compatible, temperature 0, strict-JSON output, schema-gated |
| STT               | Gnani Vachana **Prisma** (te-IN) |
| TTS               | Gnani Vachana **Timbre** v2.5 (voice `Suhana`), streaming PCM + whole-file WAV fallback |
| Frontend          | Single-file vanilla JS, zero build step, vendored Silero VAD v5 (no CDN) |
| Eligibility logic | Pure-Python evaluator ported verbatim from the tested legacy core — verdicts come from the pack's own `criteria[].required` values |
| Tests             | **40 active cases** (LLM/TTS fully mocked, no network) |
| State             | Transient, browser-held, bounded ≤ 12 KB; nothing about users is logged or stored |

## Knowledge Base

- **`data/telangana_schemes_all.json`** — the single source of truth. Hot-reloaded on file change; no rebuild step, no restart.
- **Facts** carry a confidence level (`high` / `medium` / `low`); `medium` facts get an explicit "verify before trusting" caveat appended, `low` facts are never stated as fact.
- **Criteria** are the interview questions: yes/no or list answer space, a required value, a Telugu question line, a Telugu fail message, and the source that justifies the rule.
- **`unknown_in_sources`** topics (quotas, income limits, document lists, GO numbers…) are answered honestly once with a pointer to the official portal — never guessed, never invented.
- **Non-active scheme statuses** (`disputed`, `not_confirmed_launched`, `completed_one_time`, …) produce a status notice *before* any benefits are mentioned.
- A narrative source pack (`telangana_schemes_all.md`) documents every confidence/tier decision.

All 13 scheme entries and all 55 sources follow this schema. The final pack was last verified on **2026-10-28**.

## How a Turn Works

- **End-of-speech detection:** Silero VAD (ONNX Runtime wasm, 0.3/0.25 thresholds, 1.4 s redemption pause, sub-400 ms blip rejection) runs fully in-browser from vendored assets.
- **Speech → text:** 16 kHz PCM16 WAV → Gnani Prisma STT (`te-IN`).
- **One tiny LLM call:** the utterance → `{intent, scheme_id, answers, fact_ids}` — intent from a closed 8-value set; scheme ids and answer values must exist in the pack's own vocabulary, enforced by a schema gate that is never loosened. Invalid output → one bounded re-ask → deterministic keyword fallback. The turn is alive and honest even while the provider is down.
- **Deterministic lane:** scheme facts are assembled verbatim from the pack (+status prefix, +confidence notes, +how-to-apply, +portal, +citation cards); the interview asks one criterion question per turn, merges out-of-order answers, stops at the earliest failed criterion (citing its own source), or passes citing **every** criterion.
- **Text → speech:** `[Cn]` markers, URLs and markdown are stripped for speech only (one fixed "the link is on screen" line is appended); Gnani Timbre streams PCM back as NDJSON and playback starts gapless before synthesis finishes, abortable mid-stream with a whole-file WAV fallback.
- **Citations** are shown as on-screen source cards (title / issuer / published date / section / excerpt / URL) and are never spoken.

Measured warm turn: parse call **2.1–3.3 s** (provider cold starts up to ~18 s once); STT/TTS timings per stage surfaced live in the UI timing chip (`STT · parse · parse↻`).

## Evaluation

| Check                                             |      Result |
| ------------------------------------------------- | ----------: |
| Active unit suite (`unittest`, mocked providers) | **40 / 40 OK** |
| Frozen legacy suite (pre-pivot RAG core)          | **60 / 60 OK** (archived) |
| Live scripted interview (`tools/check_rule_flow.py`) | scheme match → offer → accept → progressive questions → pass citing every criterion |
| STT/TTS production turn                           | 7/7 completed voice turns in a live session (one STT 504 auto-retried) |
| Static + `/health` + CORS (allow **and** deny) + preflight | verified over HTTP |

The unit tests prove: fixed conversation replies carry **no** citations and no LLM prose; out-of-space parse values are never stored or judged; an early fail cites the failing criterion's own source; a full pass cites every criterion and leaves the final decision to officials; cross-scheme switches wipe all collected facts; `unknown_in_sources` topics are noticed exactly once.

## Design Choices

- **The LLM only routes.** It classifies the utterance and fills answer slots inside the pack's vocabulary. It never writes the answer, never cites, never judges eligibility — that is pure Python comparing the collected yes/no slots against the pack's `required` values.
- **Schema gate before use.** Every parse result is validated (intent set, scheme existence, value spaces). A malformed, unreachable, or invented model output is retried once, then replaced by a deterministic keyword lexicon.
- **Honesty is mechanical.** No-answer-without-a-source lives in code, not in prompting: uncovered topics get a fixed honest notice; `medium` confidence facts carry a caveat line; non-active statuses get a status note before benefits; the final decision line always credits the relevant officials.
- **Privacy by construction.** No microphone audio, transcripts, or request bodies are ever logged or persisted; session state is transient, browser-held, and size-bounded. The UI actively warns users not to share Aadhaar, bank details or OTPs.
- **Stdlib-first, vendor-in-scope.** One pip dependency, zero CDN calls, zero build steps — the whole voice loop runs from one Python file and one HTML file.

## How to Run

```bash
pip install -r requirements.txt        # only gnani-vachana==0.8.1

cp .env.example backend/.env           # then fill in your Gnani + Featherless keys

python backend/voice_server.py         # → http://127.0.0.1:8000

python -m unittest discover -s tests   # 40 cases, no network needed
python -X utf8 tools/check_rule_flow.py  # live interview vs a running server
```

Open the page, tap the orb (or type), and ask e.g. *"ఇందిరమ్మ ఇల్లు పథకం చెప్పు"* → a cited scheme answer with an offered eligibility check → one question per turn → early fail (cited) or full pass (citing every criterion, decision left to officials).

## Built With

Python 3.11 stdlib (`http.server`, `unittest`), Gnani Vachana SDK (Prisma STT, Timbre TTS), Featherless (parse-LLM), vendored `@ricky0123/vad-web` v0.0.31 + Silero v5 ONNX + ONNX Runtime Web, Vanilla JS / WebAudio.

## AI Tool Disclosure

AI coding agents were used during development to build, debug and document the codebase, and an independent agent performed a full read-only architecture audit before submission. All functionality was run and verified on the local environment as described above.

## Limitations

- **STT is unverified with real Telugu audio samples** — the voice loop was verified end-to-end mechanically, but recognition accuracy on noisy/code-mixed Telugu speech is not yet measured.
- The pack's **fact claim lines are English** (per the pack's own language note); Telugu framing comes from the pack's `summary_te` and criteria — a language-review decision is still open.
- **Nothing is deployed yet** — the frontend targets Cloudflare Pages and the backend an owner-managed HTTPS box; everything currently runs locally.
- The parse-LLM call adds **~2–3 s** warm latency per turn, with occasional cold-start spikes; the fallback path degrades gracefully but more coarsely (yes/no criteria only).
- The server uses the deprecated `cgi` module (fine on Python 3.11, removed in 3.13).
