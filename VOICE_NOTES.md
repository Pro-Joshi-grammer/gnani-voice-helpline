# Voice-mode notes — useful context and honest limitations (updated 6 Nov 2026, rule-based pivot)

## Supported interaction loop (implemented)

1. User taps the microphone (landing or conversation screen) → the browser asks
   for mic access and the orb state begins breathing.
2. End-of-turn detection: Silero VAD (`@ricky0123/vad-web` v0.0.31, model v5,
   fully vendored under `frontend/vendor/vad/` and served by the adapter — from
   github.com/ricky0123/vad). The vad-web bundle carries ONNX Runtime Web 1.22
   internally (`window.ort` is not used) and loads its wasm backend from
   `/vendor/vad/ort/ort-wasm-simd-threaded.mjs` plus `ort-wasm-simd-threaded.wasm`
   (the 1.22 file layout; older flat-layout ORT files such as `ort-wasm-simd.wasm`
   will not work and produce a model-load failure). Speech end = ~1.4 s of
   non-speech after speech,
   with 800 ms pre-speech padding; sub-400 ms blips are discarded as misfires.
   Tapping the orb while listening pauses the detector and submits the buffered
   speech immediately; `submitUserSpeechOnPause` makes that buffer available.
3. `onSpeechEnd` receives a 16 kHz mono Float32 segment, which the browser
   encodes as a PCM16 WAV in-page (no MediaRecorder, no webm, no resampling)
   and sends to `POST /api/voice/transcribe` with `language_code=te-IN`.
4. The transcript goes to `POST /api/assistant/query` together with the session's
   bounded `state` (this is where the progressive eligibility key-pairs
   accumulate between turns) and recent `history`; the rule engine answers
   deterministically from the JSON pack, with one tiny LLM parse call per turn.
5. The response is added to a persistent transcript and, inside a voice session,
   auto-played through `POST /api/voice/synthesize` (Timbre `timbre-v2.5`, voice
   `Suhana`, `te-IN` from `backend/.env`); streaming PCM
   (`/api/voice/synthesize_stream`) is the preferred path with whole-file WAV
   as fallback.
6. If hands-free is on (default within a voice session), the mic re-arms ~0.45 s
   after playback ends, so the user can simply keep talking.
7. The pink "Stop" pill (waveform icon) interrupts playback; "New conversation" in the
   "⋯" menu clears all transient
   session state (nothing is stored server-side).

Autoplay only ever happens after a user-initiated gesture (mic tap or an explicit
"Read this aloud" tap), consistent with browser autoplay policies.

## Honest limitations

- **Barge-in / interruption is manual.** The assistant cannot detect the user
  speaking over its own answer and duck immediately: the VAD is deliberately
  paused while Gnani speaks, so laptop speakers cannot trigger false speech
  ends. The user interrupts with the pink "Stop" pill or by tapping the orb,
  which stops playback and starts listening.
- **Streaming STT is available in the SDK but not used.** `gnani.stt.GnaniSTTStreamClient`
  supports a WebSocket with server-side VAD for streaming transcription, but the
  stdlib HTTP adapter would need a WebSocket proxy plus raw-PCM piping from the
  browser (AudioWorklet). The REST turn-based workflow above is used instead.
- **STT language is fixed** via `GNANI_LANGUAGE=te-IN`. Code-mixed Telugu-English
  and Telangana slang go to Prisma's Telugu model; real-recording behaviour must
  still be validated with the live API.
- **STT has not been verified end-to-end live** (no Telugu audio sample exists in
  the repo). TTS, the LLM parse call of the rule engine and the Silero VAD
  asset pipeline (verified 27 Oct 2026 in a real browser via automation: model
  load, ORT wasm init, mic start, reaching the Listening state) are verified;
  one spoken mic→Silero→Prisma sanity pass with real audio is still outstanding.
- **Session state lives in the browser only** (`state` — including
  `criteria_facts`, the progressive eligibility key-pairs — plus recent turns,
  rewritten every request by the server's bounded cleaner). Refreshing the page
  resets the conversation; nothing is persisted by design.
- Transient provider (LLM/STT/TTS) failures surface as an honest "I will not
  guess" fallback rather than a fabricated answer; the UI shows a retry path.

## Important before a public demo

The knowledge now lives entirely in `data/telangana_schemes_all.json`. Facts
marked `medium`/`low` confidence carry their caveat wording in answers
automatically; statuses other than `active` get a status note before benefits.
Still verify the pack's medium/low claims against current official pages
before demoing (the pack itself asks for this).

## Run

```
py backend/voice_server.py         # serves UI + API at http://127.0.0.1:8000
py -m unittest discover -s tests   # active suite (LLM/HTTP mocked)
py -m unittest discover -s legacy\tests  # frozen legacy suite
```

Secrets stay in `backend/.env` and are only read by server-side processes; the
browser never receives them, and no request bodies, transcripts, or audio are
logged or stored. `frontend/config.js` holds only the backend base URL for
the Cloudflare Pages deployment.
