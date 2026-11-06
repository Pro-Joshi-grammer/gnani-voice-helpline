"""Voice adapter for the rule-based Gnani helpline.

Run from the project root with: py backend/voice_server.py
The browser never receives GNANI_API_KEY; this process owns the provider calls
and the only-LLM-parse turn pipeline in backend/engine.py. The static frontend
(frontend/index.html + vendor assets) is served from ../frontend/ and is also
built to deploy on Cloudflare Pages: cross-origin API access is enabled via the
WEB_ORIGINS env var (comma-separated allowed origins; "*" allows any).
"""
from __future__ import annotations

import base64
import cgi
import json
import os
import re
import secrets
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from gnani.stt import GnaniSTTClient
from gnani.tts import AudioConfig, GnaniTTSClient, GnaniTTSStreamClient

import engine

# ---- Speech cleaning: only the spoken audio is cleaned; screen text keeps citations/links.
_CITATION_MARKER_RE = re.compile(r"\[(?:C\s*)?\d+\]", re.IGNORECASE)
_MD_LINK_URL_RE = re.compile(r"\[([^\]\[]{1,200})\]\(\s*(?:https?://\S+?|www\.\S+?)\s*\)")
_MD_BARE_URL_RE = re.compile(r"\[\s*(?:https?://\S+?|www\.\S+?)\s*\]")
_PLAIN_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_MD_SYMBOLS_RE = re.compile(r"```|[*_#>`~]+")
_URL_NOTICE_TE = "అధికారిక వెబ్‌సైటు లింక్ స్క్రీన్‌పై ఉంది."


def speech_text(text: str) -> str:
    """Strip citation markers, URLs and Markdown symbols from text before TTS.

    Sentences and their punctuation are kept intact. When a URL was removed, one
    fixed short Telugu line is appended so the user knows the official link is
    visible on screen.
    """
    if not text:
        return ""
    cleaned = str(text)
    had_url = bool(_MD_LINK_URL_RE.search(cleaned) or _MD_BARE_URL_RE.search(cleaned) or _PLAIN_URL_RE.search(cleaned))
    # Markdown link labels survive ([text](url) → text); the URL never does.
    cleaned = _MD_LINK_URL_RE.sub(r"\1", cleaned)
    cleaned = _MD_BARE_URL_RE.sub("", cleaned)
    cleaned = _PLAIN_URL_RE.sub("", cleaned)
    cleaned = _CITATION_MARKER_RE.sub("", cleaned)
    if had_url:
        cleaned = f"{cleaned} {_URL_NOTICE_TE}"
    cleaned = _MD_SYMBOLS_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    # No orphan spaces before sentence punctuation after marker/URL removal.
    return re.sub(r"\s+([.,;:!?])", r"\1", cleaned).strip()


# Streaming speech: Timbre's SSE output is raw PCM16 mono at this fixed rate.
# The browser builds AudioBuffers from it directly — no WAV header involved.
STREAM_SAMPLE_RATE = 48000
STREAM_JSON = "application/x-ndjson"


def pcm_stream_lines(chunks, sample_rate: int = STREAM_SAMPLE_RATE):
    """Yield raw PCM chunks framed as newline-delimited JSON for the browser player.

    Line 1: {"sample_rate": …, "channels": 1, "bytes_per_sample": 2}
    Then:   {"b64": <base64 PCM chunk>} per chunk
    Last:   {"done": true, "first_ms": …, "elapsed_ms": …} — first_ms is the time
    to the first PCM byte (the number the streaming switch is judged by).

    `chunks` is an iterator of bytes; iteration happens lazily here so the
    handler can flush each line the moment it is produced (streaming, not
    buffering). Empty chunks are skipped.
    """
    started = time.perf_counter()
    meta = {"sample_rate": sample_rate, "channels": 1, "bytes_per_sample": 2}
    yield (json.dumps(meta, separators=(",", ":")) + "\n").encode("utf-8")
    first_ms = 0.0
    for chunk in chunks:
        pcm = chunk if isinstance(chunk, (bytes, bytearray)) else bytes(chunk)
        if not pcm:
            continue
        if not first_ms:
            first_ms = (time.perf_counter() - started) * 1000.0
        line = {"b64": base64.b64encode(pcm).decode("ascii")}
        yield (json.dumps(line, separators=(",", ":")) + "\n").encode("utf-8")
    final = {
        "done": True,
        "first_ms": round(first_ms, 1),
        "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 1),
    }
    yield (json.dumps(final, separators=(",", ":")) + "\n").encode("utf-8")


ROOT = Path(__file__).resolve().parent          # backend/ (holds .env)
FRONTEND_ROOT = ROOT.parent / "frontend"        # static UI (Cloudflare Pages build)
ENV_FILE = ROOT / ".env"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
# Origins allowed to call the API cross-origin (browser on *.pages.dev etc.).
WEB_ORIGINS = {item.strip().lower() for item in os.getenv("WEB_ORIGINS", "").split(",")
               if item.strip()}


def load_env_file() -> None:
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_env_file()


def query_payload(payload: dict) -> dict:
    question = str(payload.get("question", "")).strip()
    if not question or len(question) > 1200:
        raise ValueError("Question must be between 1 and 1200 characters.")
    state = payload.get("state", {})
    history = payload.get("history", [])
    evidence = payload.get("evidence", [])
    if not isinstance(state, dict) or not isinstance(history, list) or not isinstance(evidence, list):
        raise ValueError("State, history and evidence must be JSON objects/lists.")
    return engine.route_turn(question, state, history, evidence)


def provider_key() -> str:
    key = os.getenv("GNANI_API_KEY", "").strip()
    if not key or key.startswith("replace-"):
        raise RuntimeError("GNANI_API_KEY is not configured in backend/.env")
    return key


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "GnaniLocalAdapter/0.1"

    def log_message(self, format: str, *args: object) -> None:
        # Never log request bodies, transcripts, audio, or provider credentials.
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _allowed_origin(self) -> str | None:
        # CORS for the deployed static frontend (Cloudflare Pages). When the
        # request has no Origin header (local same-origin use) nothing is added.
        origin = self.headers.get("Origin")
        if not origin:
            return None
        if "*" in WEB_ORIGINS or origin.strip().lower() in WEB_ORIGINS:
            return origin
        return None

    def end_headers(self) -> None:
        # end_headers is the single choke point every response passes through
        # (send_json, audio bodies, NDJSON stream and send_error included).
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Max-Age", "600")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        # Preflight for cross-origin POSTs from the deployed frontend.
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            configured = bool(os.getenv("GNANI_API_KEY", "").strip()) and not os.getenv("GNANI_API_KEY", "").startswith("replace-")
            self.send_json({"ok": True, "gnani_key_configured": configured})
            return
        if path == "/" or path == "/index.html":
            self.serve_file(FRONTEND_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path == "/config.js":
            self.serve_file(FRONTEND_ROOT / "config.js", "application/javascript; charset=utf-8")
            return
        if path.startswith("/vendor/"):
            self.serve_vendor(path)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def serve_vendor(self, path: str) -> None:
        # Serve vendored frontend assets (VAD model/orchestrator) from frontend/vendor only.
        MIME = {
            ".js": "application/javascript; charset=utf-8",
            ".mjs": "application/javascript; charset=utf-8",
            ".wasm": "application/wasm",
            ".onnx": "application/octet-stream",
            ".json": "application/json; charset=utf-8",
        }
        relative = path.removeprefix("/vendor/").replace("/", os.sep)
        candidate = (FRONTEND_ROOT / "vendor" / relative).resolve()
        if not str(candidate).startswith(str((FRONTEND_ROOT / "vendor").resolve()) + os.sep) or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = MIME.get(candidate.suffix.lower())
        if content_type is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/voice/transcribe":
                self.transcribe()
            elif path == "/api/voice/synthesize":
                self.synthesize()
            elif path == "/api/voice/synthesize_stream":
                self.synthesize_stream()
            elif path == "/api/assistant/query":
                self.query()
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as error:  # Safe local adapter response; details stay server-side.
            print(f"[adapter] {path} failed: {type(error).__name__}")
            self.send_json({"error": "Provider request failed."}, HTTPStatus.BAD_GATEWAY)

    def transcribe(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_json({"error": "Send audio as multipart form field 'audio'."}, HTTPStatus.BAD_REQUEST)
            return
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type})
        audio = form["audio"] if "audio" in form else None
        if audio is None or not getattr(audio, "file", None):
            self.send_json({"error": "Audio field is required."}, HTTPStatus.BAD_REQUEST)
            return
        audio_bytes = audio.file.read()
        if not audio_bytes or len(audio_bytes) > 10 * 1024 * 1024:
            self.send_json({"error": "Audio must be between 1 byte and 10 MB."}, HTTPStatus.BAD_REQUEST)
            return
        filename = Path(getattr(audio, "filename", "audio.wav") or "audio.wav").name
        language = form.getfirst("language_code", os.getenv("GNANI_LANGUAGE", "te-IN"))
        client = GnaniSTTClient(api_key=provider_key(), timeout=60)
        started = time.perf_counter()
        result = client.transcribe_bytes(audio_bytes, filename=filename, language_code=language)
        # Stage timing is shown to the user per turn; nothing about the audio is stored.
        stt_ms = (time.perf_counter() - started) * 1000.0
        self.send_json({"transcript": result.get("transcript", ""), "provider": "gnani-prisma", "elapsed_ms": round(stt_ms, 1)})

    def synthesize(self) -> None:
        payload = self.read_json()
        text = str(payload.get("text", "")).strip()
        if not text or len(text) > 4000:
            self.send_json({"error": "Text must be between 1 and 4000 characters."}, HTTPStatus.BAD_REQUEST)
            return
        spoken = speech_text(text).strip()
        if not spoken:
            # An answer made only of markers/URLs has nothing to say aloud.
            self.send_json({"error": "Text has no speakable content."}, HTTPStatus.BAD_REQUEST)
            return
        client = GnaniTTSClient(api_key=provider_key(), timeout=60)
        started = time.perf_counter()
        audio = client.synthesize(
            spoken,
            voice=os.getenv("GNANI_TTS_VOICE", "Suhana"),
            model=os.getenv("GNANI_TTS_MODEL", "timbre-v2.5"),
            language=os.getenv("GNANI_LANGUAGE", "te-IN"),
        )
        # TTS stage time travels in a header: the WAV body cannot carry JSON.
        tts_ms = (time.perf_counter() - started) * 1000.0
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(audio)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Elapsed-Ms", f"{tts_ms:.0f}")
        self.end_headers()
        self.wfile.write(audio)

    def synthesize_stream(self) -> None:
        """Stream PCM as the TTS model generates it — playback starts before the
        whole message is synthesized. NDJSON: meta line, b64 PCM lines, done line.
        Same speech_text cleaning as the whole-file endpoint; nothing is stored."""
        payload = self.read_json()
        text = str(payload.get("text", "")).strip()
        if not text or len(text) > 4000:
            self.send_json({"error": "Text must be between 1 and 4000 characters."}, HTTPStatus.BAD_REQUEST)
            return
        spoken = speech_text(text).strip()
        if not spoken:
            # An answer made only of markers/URLs has nothing to say aloud.
            self.send_json({"error": "Text has no speakable content."}, HTTPStatus.BAD_REQUEST)
            return
        client = GnaniTTSStreamClient(api_key=provider_key(), timeout=60)
        chunks = client.synthesize_stream(
            spoken,
            voice=os.getenv("GNANI_TTS_VOICE", "Suhana"),
            model=os.getenv("GNANI_TTS_MODEL", "timbre-v2.5"),
            language=os.getenv("GNANI_LANGUAGE", "te-IN"),
            audio_config=AudioConfig(),
        )
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", STREAM_JSON)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for line in pcm_stream_lines(chunks):
                self.wfile.write(line)
                # Flush every line: the browser must hear the first words while
                # the rest of the answer is still being synthesized.
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return  # Browser navigated away or stop was tapped mid-stream.

    def query(self) -> None:
        try:
            started = time.perf_counter()
            result = query_payload(self.read_json())
            # Whole rule-engine stage (parse call + deterministic flow).
            result["elapsed_ms"] = round((time.perf_counter() - started) * 1000.0, 1)
            self.send_json(result)
        except ValueError as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def read_json(self) -> dict:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required.")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ValueError("Invalid Content-Length.") from error
        if length < 0 or length > 512 * 1024:
            raise ValueError("Request is too large.")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object.")
        return value

    def serve_file(self, path: Path, content_type: str) -> None:
        resolved = path.resolve()
        if not str(resolved).startswith(str(FRONTEND_ROOT.resolve()) + os.sep) or not resolved.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    if not os.getenv("GNANI_API_KEY", "").strip():
        print("GNANI_API_KEY is missing. Add it to backend/.env before testing live speech.")
    print(f"Gnani adapter listening at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
