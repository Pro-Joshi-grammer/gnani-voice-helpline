# -*- coding: utf-8 -*-
"""Rule-based Telangana welfare-scheme core (rule-based pivot, 6 Nov 2026).

The whole conversation is a progressive interview driven by the scheme pack in
``data/telangana_schemes_all.json``: one questionnaire item at a time, each user
answer filling a key-pair in the session's eligibility state, until an early
fail (cited) or a full pass (every criterion cited). The ONLY LLM call per turn
is a tiny parser that maps the user's freeform utterance to intent + answer
slots; it never decides eligibility, never composes prose, and every fact shown
or spoken comes from the pack with its sources attached.

Provider-neutral and stdlib-only apart from `requests` (pulled in by the Gnani
SDK); the same env switches as the legacy core (Featherless vs self-hosted).
"""
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
MAX_TURN_TEXT = 1200
MAX_HISTORY = 8
MAX_STATE_BYTES = 12 * 1024

ELIGIBILITY_MODES = {"off", "offered", "active", "paused", "done"}
YES_NO_VALUES = {"yes", "no"}
STATUSES_NEEDING_A_NOTE = {
    "disputed", "not_confirmed_launched", "completed_one_time",
    "active_amount_hike_not_implemented", "active_implementation_unclear",
}


def load_env_file() -> None:
    """Read backend/.env into the process (never logged, never sent to client)."""
    path = Path(__file__).resolve().parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, _, value = text.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()


def _truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def _provider(kind: str) -> str:
    explicit = os.getenv(f"{kind}_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    return "featherless" if _truthy(f"{kind}_USE_FEATHERLESS", True) else "self_hosted"


def _config(kind: str) -> tuple[str, str, str]:
    provider = _provider(kind)
    if provider == "featherless":
        base = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
        # The backend .env names the model FEATHERLESS_LLM_MODEL (legacy rag.py
        # convention); FEATHERLESS_MODEL/LLM_MODEL stay accepted as aliases.
        model = (os.getenv("FEATHERLESS_LLM_MODEL") or os.getenv("FEATHERLESS_MODEL")
                 or os.getenv("LLM_MODEL") or "")
        key = os.getenv("FEATHERLESS_API_KEY", "")
        if not key and not _truthy("LLM_ALLOW_KEYLESS", False):
            key = os.getenv("SELF_HOSTED_API_KEY", "")
        return base, model, key
    base = os.getenv(f"{kind}_BASE_URL") or (os.getenv("SELF_HOSTED_BASE_URL", "") if kind == "LLM" else "")
    model = os.getenv(f"{kind}_MODEL") or (os.getenv("SELF_HOSTED_LLM_MODEL", "") if kind == "LLM" else "")
    key = os.getenv(f"{kind}_API_KEY") or (os.getenv("SELF_HOSTED_API_KEY", "") if kind == "LLM" else "")
    return base, model, key


def _post_json(url: str, payload: dict[str, Any], key: str, timeout: float = 60.0) -> dict[str, Any]:
    """POST JSON with one bounded retry on transient 5xx/network blips."""
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.status_code >= 500 and attempt == 0:
                last_error = RuntimeError(f"provider 5xx: {response.status_code}")
                time.sleep(0.7)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as error:
            last_error = error
            if attempt == 0 and not isinstance(error, requests.HTTPError):
                time.sleep(0.7)
    assert last_error is not None
    raise last_error


def _parse_model_json(content: str) -> dict[str, Any]:
    """Extract the JSON object from a model reply (plain/JSON fence/prose)."""
    text = (content or "").strip()
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    snippet = match.group(0) if match else text
    return json.loads(snippet)


def _chat_parse(system: str, payload: str) -> dict[str, Any]:
    """The turn's single tiny LLM call: utterance → intent + answer slots."""
    base, model, key = _config("LLM")
    if not model:
        raise RuntimeError("FEATHERLESS_MODEL is not configured")
    if not key and _provider("LLM") == "featherless":
        raise RuntimeError("FEATHERLESS_API_KEY is not configured")
    result = _post_json(
        f"{base}/chat/completions",
        {"model": model, "temperature": 0, "messages": [{"role": "system", "content": f"{system}\n\n{payload}"}]},
        key,
    )
    message = result.get("choices", [{}])[0].get("message", {}) or {}
    content = str(message.get("content") or "")
    if not content.strip():
        # Reasoning-mode serving can put the whole reply in the reasoning channel.
        content = str(message.get("reasoning") or "")
    return _parse_model_json(content)


# ---------------- per-phase turn timing (same contract as the legacy core) ----------------

_PROFILE = threading.local()


def _timings() -> dict[str, float]:
    if not hasattr(_PROFILE, "timings"):
        _PROFILE.timings = {}
    return _PROFILE.timings


class _timed:
    """Accumulate wall-seconds under a phase label for the current turn."""

    __slots__ = ("label", "start")

    def __init__(self, label: str) -> None:
        self.label = label

    def __enter__(self) -> None:
        self.start = time.perf_counter()

    def __exit__(self, *args: Any) -> None:
        box = _timings()
        box[self.label] = box.get(self.label, 0.0) + (time.perf_counter() - self.start)


def _profile_turn(function):
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        _PROFILE.timings = {}
        result = None
        try:
            result = function(*args, **kwargs)
        finally:
            # Timing bookkeeping runs even on failure; the original error
            # propagates untouched (never masked by this decorator).
            box = _timings()
            accounted = sum(value for key, value in box.items())
            box["total"] = time.perf_counter() - started
            box["other"] = max(0.0, box["total"] - accounted)
            timings = {key: round(value, 3) for key, value in box.items()}
            _PROFILE.timings = {}
            if isinstance(result, dict):  # attach AFTER the return value is captured
                result = {**result, "stage_timings": timings}
        return result
    return wrapper


# ---------------- scheme pack ----------------

_PACK_LOCK = threading.Lock()
_PACK_CACHE: dict[str, Any] = {"mtime": None, "data": None}


def pack_path() -> Path:
    configured = os.getenv("GNANI_PACK_PATH", "")
    return Path(configured) if configured else ROOT / "data" / "telangana_schemes_all.json"


def load_pack() -> dict[str, Any]:
    """Load the JSON source pack; re-reads when the file changes on disk."""
    path = pack_path()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {"meta": {}, "schemes": [], "sources": {}}
    with _PACK_LOCK:
        if _PACK_CACHE["mtime"] == mtime and _PACK_CACHE["data"] is not None:
            return _PACK_CACHE["data"]
        data = json.loads(path.read_text(encoding="utf-8"))
        data = _sanitize_pack(data)
        _PACK_CACHE["mtime"] = mtime
        _PACK_CACHE["data"] = data
        return data


def _sanitize_pack(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the pack structure; a scheme with malformed criteria keeps its
    facts and only loses the broken criteria — never an invented rule."""
    schemes: list[dict[str, Any]] = []
    for scheme in data.get("schemes", []):
        if not isinstance(scheme, dict) or not str(scheme.get("scheme_id", "")).strip():
            continue
        entry = dict(scheme)
        criteria: list[dict[str, Any]] = []
        for raw in list(entry.get("criteria", []))[:12]:
            if not isinstance(raw, dict):
                continue
            criterion_id = str(raw.get("id", "")).strip()
            answer_type = str(raw.get("answer_type", "")).strip().lower()
            required = raw.get("required")
            source_id = str(raw.get("source_id", "")).strip()
            question = str(raw.get("question_te", "")).strip()
            basis = str(raw.get("basis", "")).strip()
            fail_message = str(raw.get("fail_message_te", "")).strip()
            if not (criterion_id and question and basis and fail_message and source_id):
                continue
            if answer_type == "yes_no":
                required_value = str(required or "").strip().lower()
                if required_value not in YES_NO_VALUES:
                    continue
            elif answer_type == "list" and isinstance(required, list):
                required_value = [str(item).strip() for item in required if str(item).strip()]
                if not required_value:
                    continue
            else:
                continue
            gate = raw.get("gate", True)
            if not isinstance(gate, bool):
                continue
            condition = None
            raw_condition = raw.get("condition")
            if raw_condition is not None:
                if not isinstance(raw_condition, dict):
                    continue
                condition_id = str(raw_condition.get("id", "")).strip()
                condition_value = str(raw_condition.get("value", "")).strip().lower()
                parent = next((item for item in criteria if item["id"] == condition_id), None)
                if parent is None:
                    continue
                parent_values = (YES_NO_VALUES if parent["answer_type"] == "yes_no" else
                                 {str(item).strip().lower() for item in parent["required"]})
                if condition_value not in parent_values:
                    continue
                condition = {"id": condition_id, "value": condition_value}
            clean_criterion = {
                "id": criterion_id[:60], "question_te": question[:300], "answer_type": answer_type,
                "required": required_value, "source_id": source_id, "basis": basis[:600],
                "fail_message_te": fail_message[:300], "confidence": str(raw.get("confidence", "")).strip()[:20],
                "gate": gate,
            }
            if condition is not None:
                clean_criterion["condition"] = condition
            criteria.append(clean_criterion)
        facts: list[dict[str, Any]] = []
        for raw in list(entry.get("facts", []))[:12]:
            if not isinstance(raw, dict):
                continue
            fact_id = str(raw.get("id", "")).strip()
            claim = str(raw.get("claim", "")).strip()
            if not fact_id or not claim:
                continue
            facts.append({
                "id": fact_id[:60], "claim": claim[:400],
                "answer_te": str(raw.get("answer_te", "")).strip()[:1200],
                "confidence": str(raw.get("confidence", "")).strip()[:20],
                "source_ids": [str(item).strip()[:60] for item in raw.get("source_ids", [])[:4]
                               if str(item).strip()],
            })
        unknowns: list[dict[str, str]] = []
        for raw in list(entry.get("unknown_in_sources", []))[:8]:
            if isinstance(raw, dict):
                unknown_id = str(raw.get("id", "")).strip()
                topic = str(raw.get("topic", "")).strip()
                notice = str(raw.get("notice_te", "")).strip()
                if unknown_id and topic and notice:
                    unknowns.append({"id": unknown_id[:60], "topic": topic[:200], "notice_te": notice[:300]})
        entry["criteria"] = criteria
        entry["facts"] = facts
        entry["unknown_in_sources"] = unknowns
        entry["summary_te"] = str(entry.get("summary_te", ""))[:1200]
        entry["how_to_apply"] = str(entry.get("how_to_apply", ""))[:800]
        entry["status"] = str(entry.get("status", "")).strip()[:60]
        entry["status_note"] = str(entry.get("status_note", ""))[:400]
        entry["name_en"] = str(entry.get("name_en", "") or "")[:200]
        entry["name_te"] = str(entry.get("name_te", "") or "")[:200]
        entry["portal"] = str(entry.get("portal") or "")[:400]
        schemes.append(entry)
    sources: dict[str, dict[str, str]] = {}
    raw_sources = data.get("sources", {})
    if isinstance(raw_sources, dict):
        for source_id, source in raw_sources.items():
            if isinstance(source, dict):
                sources[str(source_id).strip()[:60]] = {
                    "title": str(source.get("title", ""))[:200],
                    "publisher": str(source.get("publisher", ""))[:120],
                    "url": str(source.get("url", ""))[:400],
                    "date": str(source.get("date", ""))[:40],
                    "tier": str(source.get("tier", ""))[:40],
                }
    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    return {"meta": meta, "schemes": schemes, "sources": sources}


def scheme_entry(pack: dict[str, Any], scheme_id: str) -> dict[str, Any] | None:
    return next((scheme for scheme in pack["schemes"] if scheme["scheme_id"] == scheme_id), None)


# ---------------- deterministic scheme routing (routing structure only) ----------------
# Name tokens (English + Telugu) per scheme. Three Mahalakshmi variants share a
# name, so they carry distinguishing second tokens. Matching the pack's own
# scheme names is routing structure — ordinary conversation is never taxonomised.

SCHEME_KEYWORDS: dict[str, list[str]] = {
    "mahalakshmi_free_bus": [
        "free bus", "bus pass", "bus travel", "మహాలక్ష్మి బస్", "ఉచిత బస్సు", "బస్సు",
    ],
    "mahalakshmi_monthly_aid_2500": [
        "2500", "2500 రూపాయలు", "monthly aid", "నెలకు 2500", "మహాలక్ష్మి నెలకు",
    ],
    "mahalakshmi_lpg_500": [
        "lpg", "gas cylinder", " గ్యాస్ సిలిండర్", "సిలిండర్", "గ్యాస్",
    ],
    "gruha_jyothi": [
        "gruha jyothi", "gruha jyoti", "electricity bill", "గృహ జ్యోతి", "గృహజ్యోతి", "కరెంట్",
    ],
    "rajiv_aarogyasri": [
        "aarogyasri", "arogyasri", "health insurance", "అరోగ్యశ్రీ", "అరోగ్య శ్రీ", "ten lakh",
    ],
    "indiramma_indlu": [
        "indiramma", "housing", "house scheme", "ఇందిరమ్మ", "ఇల్లు",
    ],
    "rythu_bharosa": [
        "rythu bharosa", "investment support", "రైతు భరోసా", "రైతుభరోసా", "farmer investmen",
    ],
    "rythu_bima": [
        "rythu bima", "రైతు బీమా", "రైతుబీమా", "life insurance",
    ],
    "rythu_runa_mafi": [
        "runa mafi", "loan waiver", "రుణ మాఫీ", "రుణమాఫీ", "అప్పు రద్దు",
    ],
    "cheyutha_aasara_pensions": [
        "aasara", "cheyutha", "pension", "ఆసరా", "పెంషన్", "చేయుత",
    ],
    "kalyana_lakshmi_shaadi_mubarak": [
        "kalyana lakshmi", "shaadi mubarak", "కల్యాణ లక్ష్మి", "షాదీ ముబారక్", " marriage",
    ],
    "rajiv_yuva_vikasam": [
        "yuva vikasam", "rajiv yuva", "self employment", "యువ వికాసం", "యువవికాసం",
    ],
    "ration_cards_fine_rice": [
        "ration card", "fine rice", "రేషన్ కార్డు", "రేషన్", "ಬಿಯ್ಯಂ", "బిಯ్యం",
    ],
}


def _keyword_scheme(question: str) -> str:
    """Deterministic scheme match by the pack's own names/tokens; '' if none."""
    text = f" {question.lower()} "
    best: tuple[int, str] = (0, "")
    for scheme_id, keywords in SCHEME_KEYWORDS.items():
        scored = len({keyword for keyword in keywords if keyword.lower() in text})
        if scored > best[0]:
            best = (scored, scheme_id)
    return best[1] if best[0] else ""


# Lexicons below are ONLY the deterministic fallback when the tiny LLM parser is
# unreachable — the primary interpretation of every turn is the LLM by meaning.

_YES_WORDS = ["yes", "yeah", "yep", "correct", "avunu", "avunandi", "ounu", "sare", "okay",
              "అవును", "అవునండి", "ఔను", "సరే", "ఉంది", "ఉన్నాయి"]
_NO_WORDS = ["no", "nope", "nah", "ledu", "ledandi", "kaadu", "kadhu", "kaadhu", "కాదు", "కాదండి",
             "లేదు", "లేదండి", "ఉండదు", "వద్దు"]
_UNSURE_WORDS = ["తెలియదు", "తెలీదు", "చెప్పలేను", "కచ్చితంగా చెప్పలేను", "నిర్ధారించలేను",
                 "not sure", "unsure", "don't know", "dont know", "maybe", "కావచ్చు"]
_GREETING_WORDS = ["namaste", "namaskaram", "hello", "hai", "నమస్కారం", "నమస్తే", "హాయ్", "హలో"]
_ABOUT_WORDS = ["ఎవరు", "what can you do", "how do you work", "ఎలా పని", "who are you"]
_STOP_WORDS = ["ఆపు", "చాలు", "stop", "ఆపేయి", "తనిఖీ వద్దు", "cancel check", "cancel eligibility"]
_PAUSE_WORDS = ["pause", "later", "తర్వాత", "ఆగు", "ఇప్పుడు వద్దు", "తర్వాత చూద్దాం"]
_RESUME_WORDS = ["resume", "continue check", "మళ్లీ మొదలు", "తనిఖీ కొనసాగించు", "అర్హత చెక్ కొనసాగించు"]
_CHECK_CLARIFICATION_WORDS = ["అంటే ఏంటి", "అంటే ఏమిటి", "అర్థం ఏమిటి", "ఏమిటి", "ఏంటి", "లాంటిదా",
                               "what does", "what do you mean", "meaning of", "explain"]
_SCHEME_QUESTION_WORDS = ["document", "పత్ర", "డాక్యుమెంట్", "apply", "application", "దరఖాస్తు", "అప్లై",
                          "ఎక్కడ", "ఎలా", "ఏమిటి", "ఎంత", "ఎవరు", "అర్హత", "benefit", "దొరుకుతుందా"]


def _yes_no_fallback(question: str) -> str:
    text = re.sub(r"[.,!?;:]+", " ", str(question).lower())
    text = re.sub(r"\s+", " ", text).strip()
    if any(word in text for word in _UNSURE_WORDS):
        return ""
    hit_yes = any(word in text for word in _YES_WORDS)
    hit_no = any(word in text for word in _NO_WORDS)
    if hit_yes == hit_no:
        return ""
    # The fallback is intentionally limited to short, direct confirmations. A
    # longer statement needs the structured parser to map its criterion safely.
    if len(text.split()) > 8 or "?" in question:
        return ""
    return "yes" if hit_yes else "no"


def _word_hit(question: str, words: list[str]) -> bool:
    text = f" {question.lower()} "
    return any(word in text for word in words)


def _looks_like_check_clarification(question: str) -> bool:
    return _word_hit(question, _CHECK_CLARIFICATION_WORDS)


def _accepts_check_offer(question: str) -> bool:
    text = str(question).lower()
    if _word_hit(text, _STOP_WORDS + ["వద్దు", "అక్కర్లేదు", "ఇప్పుడు కాదు", "not now", "no thanks"]):
        return False
    if _yes_no_fallback(text) == "yes":
        return True
    return _word_hit(text, [
        "చూడాలనుకుంటున్నా", "చెక్ చేయండి", "చెక్ చేద్దాం", "అర్హత చెక్", "అడగండి",
        "ప్రశ్నలు అడగండి", "తెలుసుకోవాలనుకుంటున్నా", "ask me", "go ahead", "let's check",
        "check my eligibility",
    ])


# ---------------- session state (transient; lives only in the browser) ----------------

def _clean_state(state: Any) -> dict[str, Any]:
    """Bound + sanitize the session state the browser sends back every turn."""
    if not isinstance(state, dict):
        state = {}
    facts: dict[str, Any] = {}
    raw_facts = state.get("criteria_facts") if isinstance(state.get("criteria_facts"), dict) else {}
    for key, value in list(raw_facts.items())[:12]:
        clean_key = str(key).strip()[:60]
        if not clean_key:
            continue
        if isinstance(value, dict) and "value" in value:
            facts[clean_key] = {"value": str(value.get("value", ""))[:80], "source": "user_stated"}
        else:
            facts[clean_key] = {"value": str(value)[:80], "source": "user_stated"}
    mode = str(state.get("eligibility_mode", "off")).strip().lower()
    method = str(state.get("application_method", "")).strip().lower()
    paused_checks = {}
    raw_paused = state.get("paused_checks") if isinstance(state.get("paused_checks"), dict) else {}
    for scheme_id, checkpoint in list(raw_paused.items())[:4]:
        if not isinstance(checkpoint, dict):
            continue
        checkpoint_facts = checkpoint.get("criteria_facts") if isinstance(checkpoint.get("criteria_facts"), dict) else {}
        paused_checks[str(scheme_id).strip()[:60]] = {
            "criteria_facts": {str(key)[:60]: {"value": str(value.get("value", ""))[:80], "source": "user_stated"}
                               for key, value in list(checkpoint_facts.items())[:12] if isinstance(value, dict)},
            "pending_criterion": str(checkpoint.get("pending_criterion", ""))[:60],
            "unknown_notices": [str(value)[:60] for value in checkpoint.get("unknown_notices", [])[:8]
                                if isinstance(value, str)],
        }
    cleaned = {
        "topic": str(state.get("topic", ""))[:160],
        "last_question": str(state.get("last_question", ""))[:MAX_TURN_TEXT],
        "active_scheme_id": str(state.get("active_scheme_id", "")).strip()[:60],
        "eligibility_mode": mode if mode in ELIGIBILITY_MODES else "off",
        "criteria_facts": facts,
        "pending_criterion": str(state.get("pending_criterion", "")).strip()[:60],
        "unknown_notices": [str(value).strip()[:60] for value in state.get("unknown_notices", [])[:8]
                            if isinstance(value, str) and value.strip()],
        "application_method": method if method in {"online", "offline"} else "",
        "application_choice_pending": state.get("application_choice_pending") is True,
        "paused_checks": paused_checks,
        "offer_declined": state.get("offer_declined") is True,
    }
    encoded = json.dumps(cleaned, ensure_ascii=False)
    if len(encoded.encode("utf-8")) <= MAX_STATE_BYTES:
        return cleaned
    crumbs = {"topic": cleaned["topic"][:80], "last_question": cleaned["last_question"][:300],
              "active_scheme_id": cleaned["active_scheme_id"], "eligibility_mode": "off",
              "criteria_facts": {}, "pending_criterion": "", "unknown_notices": [],
              "application_method": "", "application_choice_pending": False,
              "paused_checks": {}, "offer_declined": False}
    return crumbs


def _clean_history(history: Any) -> list[dict[str, str]]:
    if not isinstance(history, list):
        return []
    output = []
    for turn in history[-MAX_HISTORY:]:
        if isinstance(turn, dict) and turn.get("role") in {"user", "assistant"} and str(turn.get("content", "")).strip():
            output.append({"role": str(turn.get("role")), "content": str(turn.get("content"))[:600]})
    return output


# ---------------- citations built straight from the pack ----------------

def _pack_citation(pack: dict[str, Any], source_id: str, excerpt: str, scheme_id: str,
                   section: str) -> dict[str, Any]:
    source = pack["sources"].get(source_id, {})
    return {
        "id": source_id, "title": source.get("title") or source_id,
        "issuer": source.get("publisher") or "To be verified",
        "published_date": source.get("date"), "effective_date": None,
        "last_verified_date": (pack.get("meta", {}) or {}).get("last_verified_date"),
        "section": section, "excerpt": excerpt[:600], "source_url": source.get("url", ""),
        "scheme_id": scheme_id, "verification_status": source.get("tier", ""),
    }


def _criteria_evidence(pack: dict[str, Any], entry: dict[str, Any],
                       criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_pack_citation(pack, criterion["source_id"], criterion["basis"],
                           entry["scheme_id"], "criteria") for criterion in criteria]


def _facts_evidence(pack: dict[str, Any], entry: dict[str, Any],
                    facts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Citations for the selected facts; returns (citations, fact_id → [Cn] marker)."""
    used: list[dict[str, Any]] = []
    marker_by_fact: dict[str, str] = {}
    for fact in facts:
        markers = []
        for source_id in fact["source_ids"][:2]:
            citation = _pack_citation(pack, source_id, fact["claim"], entry["scheme_id"], f"fact:{fact['id']}")
            known = next((item for item in used
                          if item["id"] == citation["id"] and item["excerpt"] == citation["excerpt"]), None)
            if known is not None:
                markers.append(f"[C{used.index(known) + 1}]")
                continue
            used.append(citation)
            markers.append(f"[C{len(used)}]")
        if markers:
            marker_by_fact[fact["id"]] = " ".join(markers)
    return used, marker_by_fact


def _dedupe_citations(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output = []
    for citation in citations:
        key = (citation["id"], citation["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        output.append(citation)
    return output


# ---------------- the tiny turn parser (the only LLM call; judged by meaning) ----------------

_PARSE_INTENTS = {"greeting", "about", "scheme_info", "start_check", "check_answer",
                  "check_clarification", "pause_check", "resume_check", "stop_check",
                  "switch_scheme", "unrelated"}


def _check_parse_shape(data: Any, pack: dict[str, Any], entry: dict[str, Any] | None) -> None:
    """Schema gate for the parser's strict-JSON contract — never loosened."""
    if not isinstance(data, dict):
        raise ValueError("Parse call did not return a JSON object")
    intent = str(data.get("intent", "")).strip().lower()
    if intent not in _PARSE_INTENTS:
        raise ValueError(f"Unknown parse intent {intent!r}")
    scheme_id = str(data.get("scheme_id", "") or "").strip()
    if scheme_id and scheme_entry(pack, scheme_id) is None:
        raise ValueError(f"Unknown scheme id {scheme_id!r}")
    selected_entry = scheme_entry(pack, str(data.get("scheme_id", "") or "").strip()) or entry
    if selected_entry is not None:
        allowed_ids = {criterion["id"] for criterion in selected_entry["criteria"]}
        answers = data.get("answers", {})
        if not isinstance(answers, dict):
            raise ValueError("answers must be an object")
        for criterion_id, value in answers.items():
            key = str(criterion_id)
            if key not in allowed_ids:
                raise ValueError(f"Criterion {key!r} does not belong to the current scheme")
            criterion = next(criterion for criterion in selected_entry["criteria"] if criterion["id"] == key)
            if criterion["answer_type"] == "yes_no":
                if str(value or "").strip().lower() not in YES_NO_VALUES:
                    raise ValueError(f"Value {value!r} outside the yes/no space")
            elif str(value or "").strip().lower() not in {str(item).strip().lower() for item in criterion["required"]}:
                raise ValueError(f"Value {value!r} outside the allowed values")
    answers_present = isinstance(data.get("answers", {}), dict) and bool(data.get("answers", {}))
    if entry is None and answers_present:
        raise ValueError("answers require a running check")
    fact_ids = data.get("fact_ids", [])
    if not isinstance(fact_ids, list) or len(fact_ids) > 3 or any(not isinstance(item, str) for item in fact_ids):
        raise ValueError("fact_ids must be a list of up to three ids")
    if not isinstance(data.get("reply_text", ""), str):
        raise ValueError("reply_text must be a string")


def _parse_turn(question: str, clean_state: dict[str, Any], clean_history: list[dict[str, str]],
                pack: dict[str, Any]) -> dict[str, Any]:
    """One tiny meaning-based call: utterance → intent + answer slots.

    The model only selects ids and values inside the pack's vocabulary; the
    eligibility decision itself stays pure Python (the evaluator below).
    """
    active = scheme_entry(pack, clean_state.get("active_scheme_id", ""))
    mode = clean_state.get("eligibility_mode", "off")
    if active is not None and mode in {"offered", "active", "paused", "done"}:
        criteria_lines = "\n".join(
            f'- {criterion["id"]}: {criterion["question_te"]} '
            f'(allowed: {"yes, no" if criterion["answer_type"] == "yes_no" else ", ".join(criterion["required"])})'
            + (" (routing only; not an eligibility requirement)" if not criterion.get("gate", True) else "")
            + (f' (only when {criterion["condition"]["id"]}={criterion["condition"]["value"]})'
               if criterion.get("condition") else "")
            for criterion in active["criteria"])
    else:
        criteria_lines = "(none — no check is running)"
    scheme_lines = "\n".join(
        f'- {scheme["scheme_id"]}: {scheme["name_en"]} / {scheme["name_te"]}' for scheme in pack["schemes"])
    scheme_context = []
    for scheme in pack["schemes"]:
        facts = "; ".join(
            f'{fact["id"]} ({fact["confidence"]}; sources {", ".join(fact["source_ids"])}): {fact["claim"]}'
            for fact in scheme["facts"])
        details = (f'{scheme["scheme_id"]} | {scheme["name_te"]} | status: {scheme["status"]} '
                   f'{scheme["status_note"]} | summary: {scheme["summary_te"]} | facts: {facts} '
                   f'| apply: {scheme["how_to_apply"]} | portal: {scheme["portal"]}')
        scheme_context.append(details[:1800])
    context_text = "\n".join(scheme_context)[:24000]

    system = (
        "You are Gnani, a warm, respectful Telugu-first Telangana welfare-scheme voice assistant. "
        "Understand informal or romanised Telugu and code-mixed speech. Do not introduce yourself by the name Gnani "
        "unless the user explicitly asks your name. Return JSON only with keys: "
        "intent, scheme_id, answers, fact_ids, reply_text.\n"
        "intent is exactly one of:\n"
        "- greeting: a greeting, thanks or conversational filler.\n"
        "- about: asks what this assistant is or can do.\n"
        "- scheme_info: asks about or seeks a recommendation for a scheme — benefits, who is covered, "
        "application steps, documents, status, or a scheme fitting the user's stated need.\n"
        "- start_check: agrees to the offered eligibility check, or asks for a check by name.\n"
        "- check_answer: directly answers the pending question, corrects a previous answer, or clearly states "
        "one or more facts about the user's own situation relevant to this check. Extract every clearly supported "
        "criterion answer in the utterance; leave uncertain or conflicting answers out. Never infer land ownership "
        "from cultivation or confuse leased land with owned/registered land.\n"
        "- check_clarification: asks what the pending eligibility question means or asks for an example; "
        "briefly explain it in simple Telugu without answering for the user.\n"
        "- pause_check: asks to pause, wait, or come back to the eligibility check later.\n"
        "- resume_check: explicitly asks to continue a paused eligibility check.\n"
        "- stop_check: explicitly cancels a running or offered check.\n"
        "- switch_scheme: clearly moves to a different scheme.\n"
        "- unrelated: anything else (other government services, personal tasks, opinions).\n"
        "scheme_id: the exact scheme id listed below when one is named or clearly meant, else \"\".\n"
        "answers: for check_answer turns, return an object {criterion_id: value} using EXACTLY the running "
        "check's allowed ids and values below. Extract multiple clearly stated facts and corrections from one "
        "utterance. Map yes_no only to \"yes\" or \"no\"; map list answers to one allowed value. Omit uncertain, "
        "ambiguous, or conflicting answers; never invent an id or value. For any other intent, answers must be {}.\n"
        "fact_ids: for scheme_info, select up to 3 exact fact ids from the selected scheme that support "
        "your response; else []. Never cite facts from another scheme.\n"
        "reply_text: for scheme_info, answer the user's question directly in one concise (ideally 1-3 short "
        "sentences), natural Telugu-first answer in everyday, simple language a rural listener can understand; "
        "avoid jargon, ambiguity, generic preambles, filler, and restating the question (for example, do not say "
        "'Sure, I will tell you about this scheme'). When using a technical term, add its short common meaning "
        "in parentheses the first time (e.g. bank seeding (linking the bank account with Aadhaar), DBT "
        "(government aid deposited directly into the bank account), IFSC (bank branch code), CSC "
        "(authorized public-service center)). Use ONLY the selected scheme's supplied summary, facts, status, "
        "and application guidance. Do not include "
        "URLs, citation markers, source names, or explain where the information came from; citations appear "
        "separately on screen. Do not infer eligibility, invent missing details, or claim an official decision. If the pack "
        "does not answer the question, say so honestly. For check_clarification, explain only the pending "
        "criterion in brief, simple Telugu; do not judge or answer it for the user. For other intents, write a brief "
        "Telugu-first reply (max 240 characters) only for greeting/about/unrelated/stop_check; otherwise empty. Do not ask for "
        "caste or income unless the user asks for personalized guidance or a supplied criterion requires it. "
        "Never request Aadhaar, bank, or OTP details, and never ask users to upload or share documents in chat. "
        "A document checklist is preparation guidance only; tell users to submit documents only through the official channel.\n"
        "For application questions, use only the supplied application guidance. If both online and offline paths "
        "are supplied and the user has not chosen one, finish by asking whether they prefer online or offline; "
        "if they have chosen, explain only that path.\n"
        "For scheme_info, a scheme_id may be chosen from the ids below based on the user's need, but only "
        "recommend it as a possible match when pack facts support that match; do not claim the user is eligible.\n"
        f"\nScheme ids:\n{scheme_lines}\n"
        f"Pack context (the only source of scheme claims):\n{context_text}\n"
        f"Running-check criteria ({active['scheme_id'] if active else 'none'}):\n{criteria_lines}"
    )
    if active is not None:
        system += ("\nFact ids of the scheme in play:\n" + "\n".join(
            f'- {fact["id"]}: {fact["claim"][:100]}' for fact in active["facts"]))
    payload = (f"Question:\n{question}\n\nState: scheme={clean_state.get('active_scheme_id', '')}, "
               f"mode={mode}, pending={clean_state.get('pending_criterion', '')}\n"
               f"Recent turns:\n{json.dumps(clean_history[-4:], ensure_ascii=False)}")
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            with _timed("parse_llm" if attempt == 0 else "parse_retry_llm"):
                parsed = _chat_parse(system, payload)
            _check_parse_shape(parsed, pack, active)
            return {
                "intent": str(parsed.get("intent", "")).strip().lower(),
                "scheme_id": str(parsed.get("scheme_id", "") or "").strip(),
                "answers": parsed.get("answers", {}) if isinstance(parsed.get("answers", {}), dict) else {},
                "fact_ids": [str(item).strip() for item in parsed.get("fact_ids", [])[:3]
                             if isinstance(item, str) and str(item).strip()] if isinstance(parsed.get("fact_ids"), list) else [],
                "reply_text": parsed.get("reply_text", "").strip()[:1200]
                if isinstance(parsed.get("reply_text"), str) else "",
            }
        except (ValueError, TypeError, KeyError) as error:
            last_error = error
            if attempt == 0:
                with _timed("retry_wait"):
                    time.sleep(0.7)
    assert last_error is not None
    raise last_error


def _fallback_parse(question: str, clean_state: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """LLM down → deterministic keywords keep the flow alive, honestly."""
    if _word_hit(question, _GREETING_WORDS) and len(question) < 60:
        return {"intent": "greeting", "scheme_id": "", "answers": {}, "fact_ids": []}
    if _word_hit(question, _ABOUT_WORDS):
        return {"intent": "about", "scheme_id": "", "answers": {}, "fact_ids": []}
    if _word_hit(question, _STOP_WORDS):
        return {"intent": "stop_check", "scheme_id": "", "answers": {}, "fact_ids": []}
    if _word_hit(question, _PAUSE_WORDS):
        return {"intent": "pause_check", "scheme_id": "", "answers": {}, "fact_ids": []}
    if _word_hit(question, _RESUME_WORDS):
        return {"intent": "resume_check", "scheme_id": "", "answers": {}, "fact_ids": []}
    if (clean_state.get("eligibility_mode") in {"active", "paused"}
            and _looks_like_check_clarification(question)):
        return {"intent": "check_clarification", "scheme_id": "", "answers": {}, "fact_ids": []}
    if clean_state.get("eligibility_mode") in {"active", "paused"} and _word_hit(
            question, ["తెలియదు", "తెలీదు", "గుర్తులేదు", "not sure", "don't know", "dont know", "unsure"]):
        return {"intent": "unrelated", "scheme_id": "", "answers": {}, "fact_ids": []}
    scheme_id = _keyword_scheme(question)
    active_id = clean_state.get("active_scheme_id", "")
    if scheme_id and scheme_id != active_id:
        return {"intent": "switch_scheme", "scheme_id": scheme_id, "answers": {}, "fact_ids": []}
    if scheme_id or (active_id and _word_hit(question, _SCHEME_QUESTION_WORDS)):
        return {"intent": "scheme_info", "scheme_id": scheme_id or active_id,
                "answers": {}, "fact_ids": []}
    value = _yes_no_fallback(question)
    if value and clean_state.get("eligibility_mode") == "active" and clean_state.get("pending_criterion"):
        return {"intent": "check_answer", "scheme_id": "",
                "answers": {clean_state["pending_criterion"]: value}, "fact_ids": []}
    return {"intent": "unrelated", "scheme_id": "", "answers": {}, "fact_ids": []}


# ---------------- deterministic replies (all text comes straight from the pack) ----------------

OFFER_TE = "ఈ పథకానికి మీ అర్హతను కూడా చూసుకోవాలా?"
CHECK_STOPPED_TE = "సరే అన్నా, తనిఖీ ఇక్కడ ఆపేస్తాను. తర్వాత కావాలంటే చెప్పండి."
GREETING_TE = "నమస్కారం! తెలంగాణ ప్రభుత్వ పథకాల గురించి చెప్పగలను. ఏ పథకం గురించి ఒరిగెద్ది — పేరు చెప్పండి."
ABOUT_TE = ("తెలంగాణ ప్రభుత్వ పథకాల సమాచారాన్ని ప్రచురించిన మూలాల ఆధారంగా చెబుతాను; సమాధానాల్లో మూలాలను చూపుతాను. "
            "ఇది ప్రభుత్వ కార్యాలయం కాదు, డాక్యుమెంట్లు స్వీకరించదు; తుది నిర్ణయం ఎల్లప్పుడూ అధికారులదే. "
            "Aadhaar, బ్యాంక్ ఖాతా లేదా OTP వంటి వివరాలు దయచేసి ఇక్కడ చెప్పవద్దు.")
ABOUT_GUARD_TE = ("ప్రచురించిన మూలాల సమాచారమే అందిస్తాను; నేను ప్రభుత్వ కార్యాలయం కాదు, డాక్యుమెంట్లు స్వీకరించను, "
                  "తుది నిర్ణయం అధికారులదే. Aadhaar, బ్యాంక్ లేదా OTP వివరాలు చెప్పవద్దు.")
UNRELATED_TE = "అది నా సహాయం చేసే విషయం కాదు అన్నా — నేను తెలంగాణ ప్రభుత్వ పథకాల సమాచారం మాత్రమే చెబుతాను."
UNRELATED_SCOPE_TE = "నేను తెలంగాణ ప్రభుత్వ పథకాల సమాచారంలో మాత్రమే సహాయం చేయగలను."
UNKNOWN_SCHEME_TE = ("ఏ పథకం గురించి అడుగుతున్నారో నాకు ఖచ్చితంగా అర్థం కాలేదు. పథకం పేరు చెప్పండి — "
                     "అందుబాటులో ఉన్న పథకాల జాబితా తెరపై ఉంది.")
NOT_IN_SOURCES_TE = "ఈ వివరంపై నా మూలాల్లో సమాచారం లేదు. దయచేసి సంబంధిత అధికారిక కార్యాలయంలో ధృవీకరించండి."
MEDIUM_NOTE_TE = "ఈ సమాచారం ఒకే నివేదికలో మాత్రమే — అధికారికంగా తనిఖీ చేసి నమ్మదగింది."
LOW_NOTE_TE = "మూలాలు విభేదిస్తున్నట్లున్నాయి, కాబట్టి దీన్ని సమాచారంగా మేట్టవద్దు."
FINAL_DECISION_TE = "తుది నిర్ణయం సంబంధిత అధికారులదే అవుతుంది."


def _status_prefix(entry: dict[str, Any]) -> str:
    """Pack rule 2: statuses other than active get mentioned before benefits."""
    if entry.get("status") in STATUSES_NEEDING_A_NOTE:
        note = str(entry.get("status_note") or "").strip()
        if not note:
            note = f"ప్రస్తుత స్థితి: {entry.get('status')}"
        return f"ముఖ్యమైన విషయం: {note} "
    return ""


def _confidence_note(fact: dict[str, Any]) -> str:
    if fact.get("confidence") == "medium":
        return f" ({MEDIUM_NOTE_TE})"
    if fact.get("confidence") == "low":
        return f" ({LOW_NOTE_TE})"
    return ""


def _scheme_info_answer(pack: dict[str, Any], entry: dict[str, Any], fact_ids: list[str],
                        with_offer: bool, clean_state: dict[str, Any], reply_text: str = "",
                        ask_application_mode: bool = False) -> dict[str, Any]:
    """Use model wording only alongside validated pack facts; Python owns citations and safeguards."""
    by_id = {fact["id"]: fact for fact in entry["facts"]}
    selected = [by_id[fact_id] for fact_id in fact_ids if fact_id in by_id]
    prefix = _status_prefix(entry)
    if fact_ids and (not selected or any(fact_id not in by_id for fact_id in fact_ids)):
        # Invalid selection: answer honestly, never with substitute facts.
        answer_text = f"{prefix}{NOT_IN_SOURCES_TE}"
        return {"decision": "abstain", "kind": "scheme", "answer_text": answer_text[:4000],
                "citations": [], "next_steps": [], "state": _clean_state(clean_state)}
    if reply_text and not selected and fact_ids == []:
        return {"decision": "abstain", "kind": "scheme", "answer_text": f"{prefix}{NOT_IN_SOURCES_TE}",
                "citations": [], "next_steps": [], "state": _clean_state(clean_state)}
    if not selected:
        ranked = sorted(entry["facts"], key=lambda fact: 0 if fact.get("confidence") == "high" else 1)
        selected = ranked[:2]
    citations, markers = _facts_evidence(pack, entry, selected)
    if selected:
        if reply_text:
            reply_text = re.sub(r"\[[^\]]*\]\((?:https?://|www\.)[^)]*\)", "", reply_text)
            reply_text = re.sub(r"(?:https?://|www\.)\S+", "", reply_text, flags=re.IGNORECASE)
            reply_text = re.sub(r"\[(?:C\s*)?\d+\]", "", reply_text, flags=re.IGNORECASE)
            reply_text = re.sub(r"\s+", " ", reply_text).strip() or entry["summary_te"]
            citation_markers = " ".join(dict.fromkeys(
                marker for fact in selected for marker in markers.get(fact["id"], "").split()))
            confidence_notes = " ".join(dict.fromkeys(
                _confidence_note(fact).strip(" ()") for fact in selected if _confidence_note(fact)))
            answer_text = " ".join(part for part in (
                _status_prefix(entry), reply_text, citation_markers, confidence_notes) if part).strip()
        else:
            citation_markers = " ".join(dict.fromkeys(
                marker for fact in selected for marker in markers.get(fact["id"], "").split()))
            confidence_notes = " ".join(dict.fromkeys(
                _confidence_note(fact).strip(" ()") for fact in selected if _confidence_note(fact)))
            answer_body = " ".join(fact["answer_te"] for fact in selected if fact.get("answer_te"))
            answer_text = " ".join(part for part in (
                _status_prefix(entry), answer_body or entry["summary_te"], citation_markers, confidence_notes) if part).strip()
        decision = "answer"
    else:
        answer_text = f"{prefix}{entry['summary_te']}".strip()
        decision = "answer"
    already_asked_channel = ("ఆన్‌లైన్" in answer_text and "ఆఫ్‌లైన్" in answer_text
                             and ("?" in answer_text or "చేయాలనుకుంటున్నారా" in answer_text))
    state = {**clean_state, "active_scheme_id": entry["scheme_id"], "last_question": ""}
    if ask_application_mode and not already_asked_channel:
        answer_text += " మీరు ఆన్‌లైన్‌లో దరఖాస్తు చేయాలనుకుంటున్నారా, లేక ఆఫ్‌లైన్‌లోనా?"
        state["application_choice_pending"] = True
    next_steps = []
    if with_offer and entry["criteria"]:
        answer_text += " " + OFFER_TE
        state["eligibility_mode"] = "offered"
        state["offer_declined"] = False
        next_steps.append("అవును అంటే మొదలుపెడతాను.")
    return {
        "decision": decision, "kind": "scheme", "answer_text": answer_text[:4000],
        "citations": _dedupe_citations(citations), "next_steps": next_steps[:2],
        "state": _clean_state(state),
        "evidence": [],
    }


_CRITERION_CLARIFICATIONS_TE = {
    "owns_house": "మీ కుటుంబంలో ఎవరి పేరుపైనా భారతదేశంలో ఎక్కడైనా శాశ్వత ఇల్లు ఉందా అని అడుగుతున్నాను.",
    "telangana_family": "మీ కుటుంబం శాశ్వతంగా తెలంగాణలోనే నివసిస్తుందా అని అడుగుతున్నాను.",
    "low_income": "మీ కుటుంబం తక్కువ ఆదాయం లేదా EWS వర్గానికి చెందుతుందా అని అడుగుతున్నాను; ఆదాయం మొత్తం చెప్పాల్సిన అవసరం లేదు.",
    "other_property": "ఇల్లు కట్టుకునే స్థలం కాకుండా మీ కుటుంబానికి వ్యవసాయ భూమి, మరో ప్లాట్ లేదా ఇంకో ఇల్లు వంటి స్థిరాస్తి ఉందా అని అడుగుతున్నాను.",
    "prior_housing_benefit": "మరో ప్రభుత్వ గృహ పథకం ద్వారా మీ కుటుంబం ఇంతకుముందు ఇల్లు లేదా సహాయం పొందిందా అని అడుగుతున్నాను.",
    "cure_area": "మీరు హైదరాబాద్ CURE/ORR పరిధిలోని ప్రాంతంలో నివసిస్తున్నారా అని అడుగుతున్నాను.",
    "cure_residence_years": "CURE/ORR పరిధిలో మీ నివాసం కనీసం 10 సంవత్సరాలుగా ఉందా అని అడుగుతున్నాను.",
    "cure_income": "మీ కుటుంబ వార్షిక ఆదాయం ₹6 లక్షల లోపేనా అని అడుగుతున్నాను; ఆదాయం మొత్తం చెప్పాల్సిన అవసరం లేదు.",
    "cure_property": "ORR/CURE పరిధిలో మీ కుటుంబానికి ఇల్లు లేదా ఇతర స్థిరాస్తి ఉందా అని అడుగుతున్నాను.",
}


def _clarify_criterion(pack: dict[str, Any], entry: dict[str, Any], clean_state: dict[str, Any],
                       criterion: dict[str, Any], question: str) -> dict[str, Any]:
    explanation = _CRITERION_CLARIFICATIONS_TE.get(
        criterion["id"], "ఈ ప్రశ్నలో మీ కుటుంబ పరిస్థితి గురించి అడుగుతున్నాను.")
    return {
        "decision": "answer", "kind": "scheme",
        "answer_text": f"{explanation} {criterion['question_te']} [C1]"[:2000],
        "citations": _criteria_evidence(pack, entry, [criterion]), "next_steps": [],
        "state": _clean_state({**clean_state, "last_question": question}), "evidence": [],
    }


def _ask_criterion(pack: dict[str, Any], entry: dict[str, Any], clean_state: dict[str, Any],
                   pending: dict[str, Any], repeat_prefix: bool = False) -> dict[str, Any]:
    prefix = "సరైన సమాధానం ఏదో ఒక్కసారి స్పష్టంగా చెప్పగలరా? " if repeat_prefix else ""
    value_hint = ""
    if pending["answer_type"] == "list":
        value_hint = " (" + ", ".join(pending["required"]) + ")"
    answer_text = f"{prefix}{pending['question_te']}{value_hint} [C1]".strip()
    state = {**clean_state, "active_scheme_id": entry["scheme_id"], "eligibility_mode": "active",
             "pending_criterion": pending["id"], "last_question": ""}
    return {
        "decision": "ask", "kind": "scheme", "answer_text": answer_text[:2000],
        "citations": _criteria_evidence(pack, entry, [pending]),
        "next_steps": [], "state": _clean_state(state), "evidence": [],
    }


def _pass_reply(pack: dict[str, Any], entry: dict[str, Any], clean_state: dict[str, Any]) -> dict[str, Any]:
    facts = clean_state.get("criteria_facts", {})
    criteria = [criterion for criterion in entry["criteria"]
                if criterion.get("gate", True) and _criterion_applies(criterion, facts)]
    citations = _criteria_evidence(pack, entry, criteria)
    markers = " ".join(f"[C{index}]" for index in range(1, len(criteria) + 1))
    answer_text = ("మీరు చెప్పిన వివరాల ప్రకారం, ఈ పథకానికి దరఖాస్తు చేసుకోవడానికి అర్హత ఉన్నట్లు కనిపిస్తోంది. "
                   f"{markers} {FINAL_DECISION_TE} దరఖాస్తు విధానం చెప్పనా, లేక ఇంకేదైనా సహాయం కావాలా?")
    return {
        "decision": "answer", "kind": "scheme", "answer_text": answer_text[:4000],
        "citations": citations, "next_steps": [],
        "state": _clean_state({**clean_state, "eligibility_mode": "done", "pending_criterion": ""}),
        "evidence": [],
    }


def _fail_reply(pack: dict[str, Any], entry: dict[str, Any], clean_state: dict[str, Any],
                criterion: dict[str, Any]) -> dict[str, Any]:
    citation = _pack_citation(pack, criterion["source_id"], criterion["basis"],
                              entry["scheme_id"], "criteria")
    answer_text = f"{_status_prefix(entry)}{criterion['fail_message_te']} [C1]"
    return {
        "decision": "answer", "kind": "scheme", "answer_text": answer_text[:4000],
        "citations": [citation], "next_steps": [],
        "state": _clean_state({**clean_state, "eligibility_mode": "done", "pending_criterion": ""}),
        "evidence": [],
    }


def _conversation_text(parse: dict[str, Any], intent: str) -> str:
    fallback = {"greeting": GREETING_TE, "about": ABOUT_TE, "unrelated": UNRELATED_TE,
                "stop_check": CHECK_STOPPED_TE}.get(intent, "")
    text = parse.get("reply_text", "").strip()[:240]
    if not text:
        return fallback
    if intent == "about":
        return f"{text} {ABOUT_GUARD_TE}"
    if intent == "unrelated":
        return f"{text} {UNRELATED_SCOPE_TE}"
    return text


def _decline_check(clean_state: dict[str, Any], reply_text: str = "") -> dict[str, Any]:
    paused = dict(clean_state.get("paused_checks", {}))
    paused.pop(clean_state.get("active_scheme_id", ""), None)
    state = {**clean_state, "eligibility_mode": "off", "offer_declined": True, "pending_criterion": "",
             "criteria_facts": {}, "paused_checks": paused, "application_choice_pending": False}
    return {
        "decision": "answer", "kind": "conversation", "answer_text": reply_text or CHECK_STOPPED_TE,
        "citations": [], "next_steps": [], "state": _clean_state(state), "evidence": [],
    }


def _new_scheme_state(clean_state: dict[str, Any], scheme_id: str, question: str) -> dict[str, Any]:
    """A genuinely new scheme: eligibility facts from the old one must never leak."""
    return _clean_state({**clean_state, "active_scheme_id": scheme_id, "eligibility_mode": "off",
                         "criteria_facts": {}, "pending_criterion": "", "unknown_notices": [],
                         "application_method": "", "application_choice_pending": False,
                         "offer_declined": False, "last_question": question})


def _save_paused_check(state: dict[str, Any]) -> dict[str, Any]:
    paused = dict(state.get("paused_checks", {}))
    scheme_id = state.get("active_scheme_id", "")
    if scheme_id and state.get("eligibility_mode") in {"active", "paused"}:
        paused[scheme_id] = {"criteria_facts": state.get("criteria_facts", {}),
                             "pending_criterion": state.get("pending_criterion", ""),
                             "unknown_notices": state.get("unknown_notices", [])}
    return _clean_state({**state, "paused_checks": paused})


def _restore_paused_check(state: dict[str, Any], scheme_id: str) -> dict[str, Any] | None:
    checkpoint = state.get("paused_checks", {}).get(scheme_id)
    if not isinstance(checkpoint, dict):
        return None
    paused = dict(state.get("paused_checks", {}))
    paused.pop(scheme_id, None)
    return _clean_state({**state, "active_scheme_id": scheme_id, "eligibility_mode": "active",
                         "criteria_facts": checkpoint.get("criteria_facts", {}),
                         "pending_criterion": checkpoint.get("pending_criterion", ""),
                         "unknown_notices": checkpoint.get("unknown_notices", []),
                         "paused_checks": paused, "application_method": "",
                         "application_choice_pending": False, "offer_declined": False})


# ---------------- pure-Python eligibility evaluator (ported from the tested legacy core) ----------------

def _criterion_allowed(criterion: dict[str, Any], value: Any) -> bool:
    text = str(value).strip().lower()
    if criterion["answer_type"] == "yes_no":
        return text in YES_NO_VALUES
    allowed = criterion["required"]
    return text in {str(item).strip().lower() for item in allowed}


def _criterion_applies(criterion: dict[str, Any], facts: dict[str, Any]) -> bool:
    condition = criterion.get("condition")
    if not condition:
        return True
    entry = facts.get(condition["id"])
    value = entry.get("value") if isinstance(entry, dict) else entry
    return isinstance(value, str) and value.strip().lower() == condition["value"]


def _criterion_failed(criterion: dict[str, Any], value: Any) -> bool:
    text = str(value).strip().lower()
    if criterion["answer_type"] == "yes_no":
        return text != str(criterion["required"]).strip().lower()
    return not _criterion_allowed(criterion, value)


def _first_failure(criteria: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any] | None:
    for criterion in criteria:
        if not criterion.get("gate", True) or not _criterion_applies(criterion, facts):
            continue
        entry = facts.get(criterion["id"])
        if not entry:
            continue
        value = entry.get("value") if isinstance(entry, dict) else entry
        if not isinstance(value, str) or not value.strip():
            continue  # malformed stored value: ignore it and re-ask instead of judging
        if criterion["answer_type"] == "yes_no" and not _criterion_allowed(criterion, value):
            continue  # unknowable yes/no value: re-ask rather than guess
        if _criterion_failed(criterion, value):
            return criterion
    return None


def _first_pending(criteria: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any] | None:
    # Deterministic: always the first criterion in data order with no known answer,
    # so facts volunteered out of order simply shorten the remaining queue. A
    # malformed or out-of-value-space stored value counts as unasked — re-asked,
    # never judged.
    def _known(criterion: dict[str, Any]) -> bool:
        entry = facts.get(criterion["id"])
        if not entry:
            return False
        value = entry.get("value") if isinstance(entry, dict) else entry
        return _criterion_allowed(criterion, value)
    return next((criterion for criterion in criteria
                 if _criterion_applies(criterion, facts) and not _known(criterion)), None)


def _apply_extracted_facts(facts: dict[str, Any], extracted: Any,
                           criteria: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(extracted, dict):
        return dict(facts)
    by_id = {criterion["id"]: criterion for criterion in criteria}
    merged = dict(facts)
    for criterion_id, value in extracted.items():
        criterion = by_id.get(str(criterion_id).strip())
        if criterion is None or value is None:
            continue
        text = str(value).strip().lower()
        if _criterion_allowed(criterion, text):
            merged[criterion["id"]] = {"value": text, "source": "user_stated"}
    return merged


# ---------------- the turn pipeline ----------------

def _application_method(question: str) -> str:
    text = str(question).lower().replace("ఆన్లైన్", "ఆన్‌లైన్").replace("ఆఫ్లైన్", "ఆఫ్‌లైన్")
    online = any(token in text for token in ("online", "on-line", "ఆన్‌లైన్", "ఆన్లైన్లో"))
    offline = any(token in text for token in ("offline", "off-line", "ఆఫ్‌లైన్", "ఆఫ్లైన్లో"))
    return "online" if online and not offline else "offline" if offline and not online else ""


def _looks_like_application_question(question: str) -> bool:
    text = str(question).lower()
    return any(token in text for token in (
        "how to apply", "where to apply", "application process", "application steps", "application procedure",
        "apply online", "apply offline", "దరఖాస్తు విధానం", "దరఖాస్తు ప్రక్రియ", "దరఖాస్తు ఎలా",
        "ఎలా దరఖాస్తు", "ఎక్కడ దరఖాస్తు", "ఎలా అప్లై", "అప్లై ఎలా", "ఎక్కడ అప్లై",
        "అప్లికేషన్ ప్రాసెస్", "ఎక్కడ సమర్ప"))


def _facts_for_question(question: str, entry: dict[str, Any], fact_ids: list[str],
                        reply_text: str, state: dict[str, Any] | None = None) -> tuple[list[str], str]:
    """Choose dedicated pack facts for document, eligibility, and apply questions."""
    text = question.lower()
    state = state or {}
    available = {fact["id"] for fact in entry["facts"]}
    selected = ""
    method = _application_method(question) or state.get("application_method", "")
    document_question = any(word in text for word in ("document", "documents", "డాక్యుమెంట్", "పత్ర", "ఏవి తీసుకెళ్ల"))
    eligibility_question = any(word in text for word in (
        "eligible", "eligibility", "who qualifies", "who is eligible", "who gets", "అర్హత", "ఎవరు అర్హులు",
        "ఎవరికి వస్త", "ఎవరికీ వస్త", "ఎవరికి ఇస్తారు", "ఎవరికి అందుతుంది", "అద్దె", "tenant", "rented",
        "సీడింగ్", "అనుసంధానం"))
    application_question = _looks_like_application_question(question) or bool(
        method and (state.get("application_choice_pending") or state.get("application_method")))
    if document_question:
        selected = "required_documents"
    elif eligibility_question:
        selected = "eligibility_details"
    elif application_question or (state.get("application_choice_pending") and method):
        if method and f"application_{method}" in available:
            selected = f"application_{method}"
        elif "application_process" in available:
            selected = "application_process"
        else:
            paths = [item for item in ("application_offline", "application_online") if item in available]
            if paths:
                return ([f"application_{method}"] if method else paths), ""
    if selected in available:
        return [selected], ""
    return fact_ids, reply_text


def _needs_application_choice(question: str, fact_ids: list[str], state: dict[str, Any] | None = None) -> bool:
    state = state or {}
    if state.get("application_method") or _application_method(question):
        return False
    if not any(fact_id in {"application_process", "application_online", "application_offline"}
               for fact_id in fact_ids):
        return False
    return ("application_process" in fact_ids or
            ("application_offline" in fact_ids and "application_online" in fact_ids))


@_profile_turn
def route_turn(question: str, state: Any = None, history: Any = None, evidence: Any = None) -> dict[str, Any]:
    """One turn: interpret (tiny LLM, deterministic fallback) → pure-Python flow."""
    question = str(question or "").strip()[:MAX_TURN_TEXT]
    if not question:
        return {"decision": "ask", "kind": "conversation", "answer_text": "చెప్పండి, ఏ సహాయం కావాలి?",
                "citations": [], "next_steps": [], "state": _clean_state(state)}
    clean_state = _clean_state(state)
    clean_history = _clean_history(history)
    pack = load_pack()
    try:
        parse = _parse_turn(question, clean_state, clean_history, pack)
    except Exception:
        parse = _fallback_parse(question, clean_state, pack)
    intent = parse["intent"]
    mode = clean_state["eligibility_mode"]
    active_id = clean_state["active_scheme_id"]
    answers = parse.get("answers", {}) if isinstance(parse.get("answers"), dict) else {}
    fact_ids = parse.get("fact_ids", [])[:3]
    active_entry = scheme_entry(pack, active_id) if mode in {"active", "paused"} else None
    offered_entry = scheme_entry(pack, active_id) if mode == "offered" else None
    accepted_offer = bool(
        offered_entry and offered_entry["criteria"] and _accepts_check_offer(question)
        and intent not in {"stop_check", "switch_scheme"}
        and not (parse.get("scheme_id") and parse.get("scheme_id") != active_id)
    )
    if accepted_offer and intent != "scheme_info":
        parse = {**parse, "intent": "start_check", "scheme_id": active_id, "answers": {}, "fact_ids": []}
    elif accepted_offer and not parse.get("scheme_id"):
        parse = {**parse, "scheme_id": active_id}
    start_after_info = accepted_offer and parse["intent"] == "scheme_info"
    chosen_method = _application_method(question)
    is_method_choice = bool(chosen_method and (
        clean_state.get("application_choice_pending") or
        (active_entry and clean_state.get("application_method"))
    ))
    if is_method_choice:
        parse = {**parse, "intent": "scheme_info", "scheme_id": active_id, "answers": {}, "fact_ids": []}
        clean_state = _clean_state({**clean_state, "application_method": chosen_method,
                                    "application_choice_pending": False})
    intent = parse["intent"]
    answers = parse.get("answers", {}) if isinstance(parse.get("answers"), dict) else {}
    fact_ids = parse.get("fact_ids", [])[:3]
    if active_entry is not None:
        if not is_method_choice and _looks_like_check_clarification(question):
            parse = {**parse, "intent": "check_clarification", "answers": {}}
        elif mode == "active" and intent in {"greeting", "about", "unrelated", "check_answer"} and not answers:
            pending = next((item for item in active_entry["criteria"]
                            if item["id"] == clean_state.get("pending_criterion")), None)
            value = _yes_no_fallback(question)
            if (pending is not None and value and not _looks_like_application_question(question)
                    and not _keyword_scheme(question) and _criterion_allowed(pending, value)):
                parse = {**parse, "intent": "check_answer", "answers": {pending["id"]: value}}
        intent = parse["intent"]
        answers = parse.get("answers", {}) if isinstance(parse.get("answers"), dict) else {}
    if intent in {"start_check", "switch_scheme", "scheme_info"} and not parse["scheme_id"]:
        keyword_scheme = _keyword_scheme(question)
        parse = {**parse, "scheme_id": keyword_scheme or (active_id if intent in {"start_check", "scheme_info"} else "")}
    scheme_id = parse["scheme_id"]

    # — running-check lanes first: answers win, everything else waits politely —
    if mode in {"active", "paused"}:
        entry = scheme_entry(pack, active_id)
        if entry is None:
            clean_state = _clean_state({**clean_state, "eligibility_mode": "off"})
        else:
            if intent == "stop_check":
                return _decline_check(clean_state, _conversation_text(parse, intent))
            if intent == "pause_check":
                paused = _clean_state({**clean_state, "eligibility_mode": "paused",
                                       "pending_criterion": clean_state.get("pending_criterion", "")})
                return {"decision": "answer", "kind": "conversation",
                        "answer_text": _conversation_text(parse, intent), "citations": [], "next_steps": [],
                        "state": paused, "evidence": []}
            if intent == "resume_check" or (mode == "paused" and intent == "start_check"):
                clean_state = _clean_state({**clean_state, "eligibility_mode": "active"})
                mode = "active"
            if mode == "paused" and intent in {"greeting", "about", "unrelated"}:
                return {"decision": "answer" if intent != "unrelated" else "abstain", "kind": "conversation",
                        "answer_text": _conversation_text(parse, intent), "citations": [], "next_steps": [],
                        "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}
            if intent == "check_clarification":
                pending = next((item for item in entry["criteria"]
                                if item["id"] == clean_state.get("pending_criterion")), None)
                if pending is None:
                    pending = _first_pending(entry["criteria"], clean_state.get("criteria_facts", {}))
                if pending is not None:
                    return _clarify_criterion(pack, entry, clean_state, pending, question)
            if intent == "switch_scheme" or (intent == "scheme_info" and scheme_id and scheme_id != active_id):
                other = scheme_entry(pack, scheme_id) if scheme_id else None
                if other is not None and other["scheme_id"] != active_id:
                    paused = _save_paused_check(clean_state)
                    wiped = _new_scheme_state(paused, other["scheme_id"], question)
                    requested_ids, reply_text = _facts_for_question(
                        question, other, fact_ids, parse.get("reply_text", ""), wiped)
                    return _scheme_info_answer(
                        pack, other, requested_ids, with_offer=True, clean_state=wiped,
                        reply_text=reply_text,
                        ask_application_mode=_needs_application_choice(question, requested_ids, wiped))
            if mode == "active" and intent == "scheme_info":
                paused = _clean_state({**clean_state, "eligibility_mode": "paused",
                                       "pending_criterion": clean_state.get("pending_criterion", "")})
                requested_ids, reply_text = _facts_for_question(
                    question, entry, fact_ids, parse.get("reply_text", ""), paused)
                return _scheme_info_answer(
                    pack, entry, requested_ids, with_offer=False, clean_state=paused,
                    reply_text=reply_text,
                    ask_application_mode=_needs_application_choice(question, requested_ids, paused))
            if mode == "paused" and intent == "scheme_info":
                requested_ids, reply_text = _facts_for_question(
                    question, entry, fact_ids, parse.get("reply_text", ""), clean_state)
                return _scheme_info_answer(
                    pack, entry, requested_ids, with_offer=False, clean_state=clean_state,
                    reply_text=reply_text,
                    ask_application_mode=_needs_application_choice(question, requested_ids, clean_state))
            if mode == "paused" and intent == "check_answer" and answers:
                clean_state = _clean_state({**clean_state, "eligibility_mode": "active"})
                mode = "active"
            if intent in {"check_answer", "start_check", "scheme_info"}:
                previous_facts = clean_state.get("criteria_facts", {})
                facts = _apply_extracted_facts(previous_facts, answers, entry["criteria"])
                clean_state = {**clean_state, "criteria_facts": facts}
            else:
                previous_facts = clean_state.get("criteria_facts", {})
            if intent in {"greeting", "about", "unrelated"}:
                if intent == "unrelated" and mode == "active":
                    pending = next((item for item in entry["criteria"]
                                    if item["id"] == clean_state.get("pending_criterion")), None)
                    if pending is None:
                        pending = _first_pending(entry["criteria"], clean_state.get("criteria_facts", {}))
                    if pending is not None:
                        reply = _ask_criterion(pack, entry, clean_state, pending, repeat_prefix=True)
                        return reply
                # Ordinary conversation must leave the pending check untouched.
                reply = _conversation_text(parse, intent)
                return {"decision": "answer" if intent != "unrelated" else "abstain", "kind": "conversation",
                        "answer_text": reply, "citations": [], "next_steps": [],
                        "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}
            failed = _first_failure(entry["criteria"], clean_state.get("criteria_facts", {}))
            if failed is not None:
                return _fail_reply(pack, entry, clean_state, failed)
            pending = _first_pending(entry["criteria"], clean_state.get("criteria_facts", {}))
            if pending is not None:
                # The honest re-ask prefix belongs only to turns where nothing new
                # was understood; a successfully filled key-pair is acknowledged
                # by simply moving to the next question.
                nothing_new = clean_state.get("criteria_facts", {}) == previous_facts
                reply = _ask_criterion(pack, entry, clean_state, pending,
                                       repeat_prefix=(intent == "start_check" and nothing_new))
                return reply
            return _pass_reply(pack, entry, clean_state)

    # — no check running —
    if intent == "resume_check":
        resume_id = scheme_id or _keyword_scheme(question) or active_id
        restored = _restore_paused_check(clean_state, resume_id) if resume_id else None
        entry = scheme_entry(pack, resume_id) if restored else None
        if restored is not None and entry is not None:
            pending = _first_pending(entry["criteria"], restored.get("criteria_facts", {}))
            if pending is not None:
                return _ask_criterion(pack, entry, restored, pending)
            return _pass_reply(pack, entry, restored)

    if intent == "stop_check":
        entry = scheme_entry(pack, active_id)
        if entry is not None and mode != "off":
            return _decline_check(clean_state, _conversation_text(parse, intent))
        return {"decision": "answer", "kind": "conversation", "answer_text": _conversation_text(parse, intent),
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}

    if intent == "start_check":
        target = scheme_id or (active_id if mode == "offered" and not clean_state.get("offer_declined") else "")
        entry = scheme_entry(pack, target) if target else None
        if entry is None or not entry["criteria"]:
            return {"decision": "abstain", "kind": "conversation", "answer_text": UNKNOWN_SCHEME_TE,
                    "citations": [], "next_steps": [scheme["name_te"] for scheme in pack["schemes"][:3]],
                    "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}
        pending = _first_pending(entry["criteria"], clean_state.get("criteria_facts", {})) or entry["criteria"][0]
        reply = _ask_criterion(pack, entry, clean_state, pending)
        return reply

    if intent in {"switch_scheme", "scheme_info"}:
        info_scheme_id = scheme_id or _keyword_scheme(question)
        entry = scheme_entry(pack, info_scheme_id) if info_scheme_id else None
        if entry is None:
            return {"decision": "abstain", "kind": "conversation", "answer_text": UNKNOWN_SCHEME_TE,
                    "citations": [], "next_steps": [scheme["name_te"] for scheme in pack["schemes"][:3]],
                    "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}
        if entry["scheme_id"] != active_id:
            fresh = _new_scheme_state(clean_state, entry["scheme_id"], question)
        else:
            fresh = clean_state
        method = _application_method(question)
        if method and _looks_like_application_question(question):
            fresh = _clean_state({**fresh, "application_method": method,
                                  "application_choice_pending": False})
        requested_ids, reply_text = _facts_for_question(
            question, entry, fact_ids, parse.get("reply_text", ""), fresh)
        with_offer = not (mode in {"offered", "done"} and entry["scheme_id"] == active_id)
        info_result = _scheme_info_answer(
            pack, entry, requested_ids, with_offer=with_offer, clean_state=fresh,
            reply_text=reply_text,
            ask_application_mode=_needs_application_choice(question, requested_ids, fresh))
        if start_after_info:
            pending = _first_pending(entry["criteria"], info_result["state"].get("criteria_facts", {}))
            if pending is not None:
                ask_state = _clean_state({**info_result["state"], "eligibility_mode": "active"})
                ask = _ask_criterion(pack, entry, ask_state, pending)
                marker = f"[C{len(info_result['citations']) + 1}]"
                return {**info_result, "decision": "ask",
                        "answer_text": f"{info_result['answer_text']} {ask['answer_text'].replace('[C1]', marker)}"[:4000],
                        "citations": info_result["citations"] + ask["citations"],
                        "next_steps": [], "state": ask["state"]}
        return info_result

    if intent == "greeting":
        return {"decision": "answer", "kind": "conversation", "answer_text": _conversation_text(parse, intent),
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}
    if intent == "about":
        return {"decision": "answer", "kind": "conversation", "answer_text": _conversation_text(parse, intent),
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}
    if intent == "unrelated":
        return {"decision": "abstain", "kind": "conversation", "answer_text": _conversation_text(parse, intent),
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}

    # Fall-through: unable to classify → the honest bridge, never a guess.
    return {"decision": "abstain", "kind": "conversation", "answer_text": UNKNOWN_SCHEME_TE,
            "citations": [], "next_steps": [scheme["name_te"] for scheme in pack["schemes"][:3]],
            "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}


def answer(question: str, state: Any = None, history: Any = None, evidence: Any = None) -> dict[str, Any]:
    return route_turn(question, state, history, evidence)
