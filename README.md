# Gnani: Telugu Voice Helpline for Telangana Government Schemes

**Ask in Telugu. Hear the answer in Telugu. Find out if you're eligible without making repeated trips to a government office.**

| | |
|---|---|
| **Live demo** | `https://gnani-helpline.joshisankarsh.tech` |
| **Demo video** | `https://drive.google.com/file/d/1_IA0Yf4ThfiGYiMfhw9xn6qg6Uh9rc-o/view` |
| **LinkedIn post** | `https://lnkd.in/p/dvFUY9Ms` |
| **Author** | Joshi Sankarsh |

Built for the Great Indian AI Internship Challenge, using Gnani.ai's Vachana speech models (Prisma STT and Timbre TTS).

---

## 1. The problem and the idea

In Telangana, finding out whether a welfare scheme applies to you often means several trips to the tehsildar or MeeSeva office: *Am I eligible? What documents do I need? What did I miss?* Official information is written in formal language, and many users, especially older people in villages, are more comfortable speaking Telugu than reading or typing.

Gnani lets a citizen **speak in Telugu** and **hear the answer in Telugu**. It explains a scheme, then runs a short interview, **one simple question at a time**, and tells the user whether they appear to meet the published criteria. Every claim comes from a curated, cited source pack. When the sources don't cover something, Gnani says so and points to the right office instead of guessing.

It was shown to a real user: a farmer from my village, checking his eligibility for Rythu Bharosa, speaking in his own dialect (see the LinkedIn post).

> **Not an official government service.** Gnani is an informational project. Final eligibility decisions rest with government officials.

<p align="center">
  <sub><b>Home screen</b></sub><br>
  <img src="https://github.com/user-attachments/assets/d6d6e4f9-16f4-4b3d-aadd-775903c28291" width="450">
</p>

<p align="center">
  <sub><b>Architecture and interview flow</b></sub><br>
  <img src="https://github.com/user-attachments/assets/5fa353d5-2858-486e-ae5f-c723ed02341c" width="1150">
</p>

---

## 2. How a turn works

```
Mic → Silero VAD → Gnani Prisma (STT) → Gemma (understands the utterance)
    → Python rule engine + cited JSON pack → Gnani Timbre (streaming TTS) → Speaker
```

1. **End-of-speech detection.** Silero VAD runs in the browser (vendored ONNX/wasm assets, no CDN) and decides when the user has finished speaking.
2. **Speech to text.** The browser sends a 16 kHz WAV to the backend, which calls **Gnani Prisma** (`te-IN`).
3. **Understanding.** One strict-JSON call to **Gemma** (hosted on Featherless) returns `{intent, scheme_id, answers, fact_ids}`: which scheme the user means, and which interview answers they just gave, even if out of order or several at once. The output is schema-checked against the pack's own vocabulary. If the call is malformed or the provider is down, one bounded re-ask runs, then a deterministic keyword fallback keeps the turn alive.
4. **Decision and reply, in Python.** The rule engine merges the facts, picks the next unanswered criterion, stops at the first failed one (citing its source), or passes citing every criterion. Scheme answers are assembled from the pack with status notes, confidence caveats and citations.
5. **Text to speech.** Citation markers and URLs are stripped from the spoken text only. **Gnani Timbre** streams audio back as chunks, so playback starts before synthesis finishes. A whole-file WAV path is the fallback if streaming fails.
6. **On screen.** Citation cards (title, issuer, date, excerpt, link) are shown, never spoken.

---

## 3. Key design decisions

### Python decides, the model understands
Every eligibility verdict and every reply comes from deterministic Python over the source pack. The language model never makes a decision. It cannot change a verdict because it never makes one.

### Why I dropped RAG
The project started as a RAG system, where the model retrieved documents and wrote the full answer. I removed it because:

- **No single source of truth.** Each scheme's rules are spread over government orders, amendments and circulars. I curated my own cited pack instead.
- **Eligibility needs a firm yes or no,** not a probabilistic answer.
- **A hallucination I could not take back.** In a test with a tricky eligibility question, the model explained the scheme at length and then ended with *"sorry, I made a mistake, you're not eligible."* With streamed audio, the user has already heard the first answer. Spoken text cannot be retracted, so decisions had to leave the model.

The old RAG code is archived in `legacy/` for reference and is not part of the running app.

### Streaming audio, not whole files
Timbre's streaming API (`synthesize_stream`) sends audio as it is generated. The first sound plays in **under one second**, even while the rest is still being produced.

### Honesty is built into the code
- Facts carry a confidence level (`high`, `medium`, `low`). `medium` facts get a "verify before trusting" caveat, and `low` facts are never stated as fact.
- Topics the sources don't cover (`unknown_in_sources`) get a fixed, honest notice and a pointer to the official office, once.
- Schemes that are disputed, not yet launched or one-time get a status notice *before* any benefit is described.
- The final-decision line always credits the officials.

### Privacy
No audio, transcripts or request bodies are logged or stored. Session state lives in the browser and is size-bounded on every turn (12 KB). The UI warns users not to share Aadhaar numbers, bank details or OTPs.

---

## 4. Performance

| Stage of the project | Typical response time |
|---|---|
| Early RAG version (cold model, three serial services, whole-file TTS) | ~40 s average |
| After switching to a warm Gemma model | ~20-25 s average |
| Time to first audio with streaming TTS (Timbre) | **~0.97 s** |
| **Current version** | **~4-6 s typical, 10 s worst case** |

What drove the improvement:

1. **A cold model was the main cause.** Models on Featherless that aren't warm are loaded onto GPUs per request. A reasoning model added further delay. A warm Gemma model removed most of it.
2. **Streaming TTS.** Switching from `synthesize()` to `synthesize_stream()` made audio start in about a second.
3. **Removing the generation call.** Replies are now assembled by Python from the pack, so the model only runs one short classification call (about 2.1-3.3 s warm).

Numbers come from the project's own timing instrumentation on the deployed app, not a formal benchmark. The first request after the provider has been idle can be slower (one cold start reached ~18 s).

---

## 5. Knowledge pack: 13 schemes

`data/telangana_schemes_all.json` is the single source of truth: 13 schemes and 55 sources, each with facts, interview criteria and a list of topics the sources do not cover. It is hot-reloaded on file change. Last verified **28 Oct 2026**. A narrative version with confidence rules is in `data/telangana_schemes_all.md`.

| Scheme | Status in the pack |
|---|---|
| Mahalakshmi: free bus travel for women | Active |
| Mahalakshmi: Rs 500 gas cylinder | Active |
| Mahalakshmi: Rs 2,500 monthly aid | **Not confirmed as launched** |
| Gruha Jyothi (200 free units) | Active |
| Rajiv Aarogyasri (health cover) | Active |
| Indiramma Indlu (housing) | Active |
| Rythu Bharosa | Active |
| Rythu Bima | **Disputed** (premium payment reports) |
| Rythu Runa Mafi (loan waiver) | **Completed, one-time** |
| Cheyutha / Aasara pensions | Active (Rs 4,000 hike not implemented) |
| Kalyana Lakshmi / Shaadi Mubarak | Active |
| Rajiv Yuva Vikasam | Active, implementation unclear |
| New ration cards and fine rice | Active |

Sources are a mix of government pages and established news reports of government orders, each tagged with a tier and a confidence level.

---

## 6. Tech stack

| Layer | Technology |
|---|---|
| Speech to text | **Gnani Vachana Prisma** (Telugu, `te-IN`) |
| Text to speech | **Gnani Vachana Timbre** v2.5, voice `Suhana`, streaming PCM with WAV fallback |
| Language model | **Gemma** on Featherless (OpenAI-compatible API), temperature 0, strict JSON |
| Backend | Python 3.11, standard library only (`http.server.ThreadingHTTPServer`) |
| Hosting | AWS EC2 |
| Frontend | Single-file vanilla JS, WebAudio, vendored `@ricky0123/vad-web` (Silero VAD v5, ONNX Runtime Web). No framework, no build step, no CDN |
| Data | Plain JSON source pack |
| Tests | `unittest` with LLM and TTS mocked |

The only pip dependency is `gnani-vachana==0.8.1`.

---

## 6a. Gnani.ai technology used

- **Prisma (STT).** Understands Telugu speech from real users, including a village farmer speaking in his own dialect.
- **Timbre (TTS).** Natural Telugu voice, and its streaming API is what brought time to first audio under a second.

Telugu speech in and out is the core of the product, and these two models are what make it usable by people who have never used an app like this.

---

## 7. Repository layout

```
gnani/
├── backend/
│   ├── engine.py            Rule engine: parsing gate, evaluator, replies, citations
│   ├── voice_server.py      HTTP adapter: static files, STT, TTS (stream + WAV), query API
│   └── .env                 Secrets (never committed)
├── frontend/
│   ├── index.html           Voice UI, transcript, sources sheet
│   ├── config.js            Backend base URL (empty = same origin)
│   └── vendor/vad/          Vendored VAD runtime assets
├── data/
│   ├── telangana_schemes_all.json    Source pack (13 schemes, 55 sources)
│   └── telangana_schemes_all.md      Narrative pack with confidence rules
├── tests/                   Active test suite
├── tools/                   Live developer checks (scripted interview)
├── legacy/                  Archived RAG implementation (not used at runtime)
├── agents.md, Deployment.md, VOICE_NOTES.md
└── requirements.txt
```

---

## 8. Run it locally

```bash
pip install -r requirements.txt
cp .env.example backend/.env          # fill in your keys
python backend/voice_server.py        # http://127.0.0.1:8000
```

Required settings in `backend/.env`:

| Variable | Purpose |
|---|---|
| `GNANI_API_KEY` | Gnani Prisma and Timbre |
| `GNANI_LANGUAGE`, `GNANI_TTS_MODEL`, `GNANI_TTS_VOICE` | `te-IN`, `timbre-v2.5`, `Suhana` |
| `FEATHERLESS_API_KEY`, `FEATHERLESS_BASE_URL`, `FEATHERLESS_LLM_MODEL` | Gemma parsing call |
| `HOST`, `PORT` | Server bind (defaults `127.0.0.1:8000`) |
| `WEB_ORIGINS` | Allowed browser origins, only if the frontend is hosted separately |

Open the page, tap the orb (or type), and try:
*"ఇందిరమ్మ ఇల్లు పథకం చెప్పు"* → a cited scheme answer and an offer to check eligibility → one question per turn → an early "not eligible" (with its source) or a pass that cites every criterion.

**Tests**

```bash
python -m unittest discover -s tests            # no network needed
python -X utf8 tools/check_rule_flow.py         # live scripted interview (server running)
```

The tests cover: replies carry no model-written prose; out-of-vocabulary model output is never stored or judged; an early fail cites the failing criterion's own source; a full pass cites every criterion and leaves the decision to officials; switching schemes wipes collected facts; uncovered topics are noticed exactly once; speech cleaning strips citation markers and URLs.

---

## 9. Deployment

The backend serves the frontend, so one process on one HTTPS host is enough (the app runs on AWS EC2 behind HTTPS; microphone access requires HTTPS). Use Python 3.11. Set the secrets as environment variables on the host and check `GET /health`.

---

## 10. Limitations and next steps

- **Speech accuracy is not formally measured.** The voice loop works end to end and has been used by a real village speaker, but accuracy on noisy or code-mixed Telugu has not been benchmarked.
- **Source verification.** Some sources are news reports of government orders, marked `medium` or `low`. Official-source re-verification is the main next step. The pack reflects what could be found on 28 Oct 2026, and schemes change.
- **Closed-domain by design.** Gnani only answers from its pack and cannot handle free-form questions outside it. Someone has to keep the pack verified.
- **English fact lines.** Fact claims in the pack are in English; Telugu comes from scheme summaries, interview questions and notices.
- **Cold starts.** The first request after the model provider has been idle can be slower.
- **Deprecated module.** The server uses `cgi`, which is removed in Python 3.13, so it is pinned to 3.11.
- **Next:** more schemes, more dialect testing, a phone-call interface.

---

## 11. AI tool disclosure

AI coding assistants were used during development to write, debug and document code. An independent agent performed a read-only architecture audit before submission. All behaviour described here was run and verified by the author.
