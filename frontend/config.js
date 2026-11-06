// Deployment configuration for the rule-based Gnani helpline.
//
// Locally (`py backend/voice_server.py`) leave this empty: the backend serves
// the frontend itself, so the relative /api/... paths just work.
//
// When the frontend is deployed separately (Cloudflare Pages) and the backend
// runs elsewhere, set the backend's base URL here, e.g.:
//   window.GNANI_BACKEND_BASE = "https://gnani-api.example.com";
// The backend must list that origin in its WEB_ORIGINS env var so CORS allows
// the calls. No provider keys ever belong in this file — the browser never
// sees GNANI_API_KEY or FEATHERLESS_API_KEY.
window.GNANI_BACKEND_BASE = "";
