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

ELIGIBILITY_MODES = {"off", "offered", "active", "done"}
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
            criteria.append({
                "id": criterion_id[:60], "question_te": question[:300], "answer_type": answer_type,
                "required": required_value, "source_id": source_id, "basis": basis[:600],
                "fail_message_te": fail_message[:300],
                "confidence": str(raw.get("confidence", "")).strip()[:20],
            })
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

_YES_WORDS = ["yes", " ok", "sare", "అవును", "ఉంది", "ఉన్నా", "చేస్తున్న", "సరే"]
_NO_WORDS = [" no", "nope", "లేదు", "ఉండదు", "వద్దు", "కాదు"]
_GREETING_WORDS = ["namaste", "namaskaram", "hello", "hai", "నమస్కారం", "నమస్తే", "హాయ్", "హలో"]
_ABOUT_WORDS = ["ఎవరు", "what can you do", "how do you work", "ఎలా పని", "who are you"]
_STOP_WORDS = ["ఆపు", "చాలు", "stop", "ఆపేయి", "తనిఖీ వద్దు"]


def _yes_no_fallback(question: str) -> str:
    text = f" {question.lower()} "
    hit_yes = any(word in text for word in _YES_WORDS)
    hit_no = any(word in text for word in _NO_WORDS)
    if hit_no and not hit_yes:
        return "no"
    if hit_yes and not hit_no:
        return "yes"
    return ""


def _word_hit(question: str, words: list[str]) -> bool:
    text = f" {question.lower()} "
    return any(word in text for word in words)


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
    cleaned = {
        "topic": str(state.get("topic", ""))[:160],
        "last_question": str(state.get("last_question", ""))[:MAX_TURN_TEXT],
        "active_scheme_id": str(state.get("active_scheme_id", "")).strip()[:60],
        "eligibility_mode": mode if mode in ELIGIBILITY_MODES else "off",
        "criteria_facts": facts,
        "pending_criterion": str(state.get("pending_criterion", "")).strip()[:60],
        "unknown_notices": [str(value).strip()[:60] for value in state.get("unknown_notices", [])[:8]
                            if isinstance(value, str) and value.strip()],
        "offer_declined": state.get("offer_declined") is True,
    }
    encoded = json.dumps(cleaned, ensure_ascii=False)
    if len(encoded.encode("utf-8")) <= MAX_STATE_BYTES:
        return cleaned
    crumbs = {"topic": cleaned["topic"][:80], "last_question": cleaned["last_question"][:300],
              "active_scheme_id": cleaned["active_scheme_id"], "eligibility_mode": "off",
              "criteria_facts": {}, "pending_criterion": "", "unknown_notices": [],
              "offer_declined": False}
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
                  "stop_check", "switch_scheme", "unrelated"}


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
    if entry is not None:
        allowed_ids = {criterion["id"] for criterion in entry["criteria"]}
        answers = data.get("answers", {})
        if not isinstance(answers, dict):
            raise ValueError("answers must be an object")
        for criterion_id, value in answers.items():
            key = str(criterion_id)
            if key not in allowed_ids:
                raise ValueError(f"Criterion {key!r} does not belong to the current scheme")
            criterion = next(criterion for criterion in entry["criteria"] if criterion["id"] == key)
            if criterion["answer_type"] == "yes_no":
                if str(value or "").strip().lower() not in YES_NO_VALUES:
                    raise ValueError(f"Value {value!r} outside the yes/no space")
            elif str(value or "").strip().lower() not in {str(item).strip().lower() for item in criterion["required"]}:
                raise ValueError(f"Value {value!r} outside the allowed values")
    answers_present = isinstance(data.get("answers", {}), dict) and bool(data.get("answers", {}))
    if entry is None and answers_present:
        raise ValueError("answers require a running check")


def _parse_turn(question: str, clean_state: dict[str, Any], clean_history: list[dict[str, str]],
                pack: dict[str, Any]) -> dict[str, Any]:
    """One tiny meaning-based call: utterance → intent + answer slots.

    The model only selects ids and values inside the pack's vocabulary; the
    eligibility decision itself stays pure Python (the evaluator below).
    """
    active = scheme_entry(pack, clean_state.get("active_scheme_id", ""))
    mode = clean_state.get("eligibility_mode", "off")
    if active is not None and mode in {"offered", "active", "done"}:
        criteria_lines = "\n".join(
            f'- {criterion["id"]}: {criterion["question_te"]}' for criterion in active["criteria"])
    else:
        criteria_lines = "(none — no check is running)"
    scheme_lines = "\n".join(
        f'- {scheme["scheme_id"]}: {scheme["name_en"]} / {scheme["name_te"]}' for scheme in pack["schemes"])

    system = (
        "You map one user utterance of a Telugu-first Telangana welfare-scheme helpline onto an "
        "intent and slots. Judge meaning only — informal Telugu, Telangana slang, coded or romanised "
        "words, code-mixed Telugu-English, greetings and partial sentences are all in scope; never "
        "rely on fixed expressions. Return JSON only with keys: intent, scheme_id, answers, fact_ids.\n"
        "intent is exactly one of:\n"
        "- greeting: a greeting, thanks or conversational filler.\n"
        "- about: asks what this assistant is or can do.\n"
        "- scheme_info: a question about a named scheme's facts — what it gives, launch date, who is "
        "covered, how to apply, documents, status.\n"
        "- start_check: agrees to the offered eligibility check, or asks for a check by name.\n"
        "- check_answer: answers the pending eligibility question or states facts about the user's "
        "own situation relevant to the running check.\n"
        "- stop_check: wants a running or offered check stopped.\n"
        "- switch_scheme: clearly moves to a different scheme.\n"
        "- unrelated: anything else (other government services, personal tasks, opinions).\n"
        "scheme_id: the exact scheme id listed below when one is named or clearly meant, else \"\".\n"
        "answers: only for check_answer turns — object {criterion_id: value} using EXACTLY the running "
        "check's allowed ids and allowed values below. One answer per mention, mapped from the user's "
        "own words to the value the criterion expects (yes_no → \"yes\" or \"no\"; list → one listed "
        "value). Never invent an id or a value.\n"
        "fact_ids: only for scheme_info — up to 3 fact ids of the named scheme whose topics match the "
        "question (launch, amount, coverage, documents, portal...). Else [].\n"
        "You never state scheme facts yourself; you only route and fill slots.\n"
        f"\nScheme ids:\n{scheme_lines}\n"
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
    value = _yes_no_fallback(question)
    if value and clean_state.get("eligibility_mode") == "active" and clean_state.get("pending_criterion"):
        return {"intent": "check_answer", "scheme_id": "",
                "answers": {clean_state["pending_criterion"]: value}, "fact_ids": []}
    scheme_id = _keyword_scheme(question)
    if scheme_id:
        if scheme_id != clean_state.get("active_scheme_id", ""):
            return {"intent": "switch_scheme", "scheme_id": scheme_id, "answers": {}, "fact_ids": []}
        return {"intent": "scheme_info", "scheme_id": scheme_id, "answers": {}, "fact_ids": []}
    return {"intent": "unrelated", "scheme_id": "", "answers": {}, "fact_ids": []}


# ---------------- deterministic replies (all text comes straight from the pack) ----------------

OFFER_TE = ("ఈ పథకం అవసరాలు మీకు సరిపోతాయేమో తేల్చడానికి, ఒక్క ప్రశ్న ఒక్క ప్రశ్నగా అడిగి చూడాలా? (సరే / కాదు అని చెప్పండి.)")
CHECK_STOPPED_TE = "సరే అన్నా, తనిఖీ ఇక్కడ ఆపేస్తాను. తర్వాత కావాలంటే చెప్పండి."
GREETING_TE = "నమస్కారం! తెలంగాణ ప్రభుత్వ పథకాల గురించి చెప్పగలను. ఏ పథకం గురించి ఒరిగెద్ది — పేరు చెప్పండి."
ABOUT_TE = ("నేను తెలంగాణ ప్రభుత్వ పథకాల సమాచారాన్ని ప్రచురించిన మూలాల ఆధారంగా మాత్రమే చెబుతాను; ప్రతి వాక్యం వెనుక మూలాన్ని చూపుతాను. "
            "నేను ప్రభుత్వ కార్యాలయం కాదు, డాక్యుమెంట్లు స్వీకరించలేను; తుది నిర్ణయం ఎల్లప్పుడూ అధికారులదే. "
            "Aadhaar, బ్యాంక్ ఖాతా లేదా OTP వంటి వివరాలు దయచేసి ఇక్కడ చెప్పవద్దు.")
UNRELATED_TE = ("అది నా సహాయం చేసే విషయం కాదు అన్నా — నేను తెలంగాణ ప్రభుత్వ పథకాల సమాచారం మాత్రమే చెబుతాను.")
UNKNOWN_SCHEME_TE = ("ఏ పథకం గురించి అడుగుతున్నారో నాకు ఖచ్చితంగా అర్థం కాలేదు. పథకం పేరు చెప్పండి — "
                     "అందుబాటులో ఉన్న పథకాల జాబితా తెరపై ఉంది.")
NOT_IN_SOURCES_TE = "ప్రచురించిన మూలాల్లో ఆ విషయం లేదు అన్నా; సోదేది అధికారిక కార్యాలయం దగ్గర మాత్రమే."
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
                        with_offer: bool, clean_state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic answer from the pack: selected facts (or the default pair),
    or the Telugu summary; how-to-apply and portal appended. No LLM prose."""
    by_id = {fact["id"]: fact for fact in entry["facts"]}
    selected = [by_id[fact_id] for fact_id in fact_ids if fact_id in by_id]
    prefix = _status_prefix(entry)
    if fact_ids and by_id and not selected:
        # Invalid selection: answer honestly, never with substitute facts.
        answer_text = f"{prefix}{NOT_IN_SOURCES_TE}"
        return {"decision": "abstain", "kind": "scheme", "answer_text": answer_text[:4000],
                "citations": [], "next_steps": [], "state": _clean_state(clean_state)}
    if not selected:
        ranked = sorted(entry["facts"], key=lambda fact: 0 if fact.get("confidence") == "high" else 1)
        selected = ranked[:2]
    citations, markers = _facts_evidence(pack, entry, selected)
    if selected:
        lines = [_status_prefix(entry)]
        for fact in selected:
            line = f"{fact['claim']}{_confidence_note(fact)} {markers.get(fact['id'], '')}".strip()
            lines.append(line)
        answer_text = " ".join(part for part in lines if part).strip()
        decision = "answer"
    else:
        answer_text = f"{prefix}{entry['summary_te']}".strip()
        decision = "answer"
    apply_text = entry.get("how_to_apply", "").strip()
    if apply_text:
        answer_text += f" దరఖాస్తు: {apply_text}"
    portal_match = re.match(r"https?://\S+", entry.get("portal", ""))
    if portal_match:
        answer_text += f" అధికారిక వెబ్‌సైటు: {portal_match.group(0).rstrip(').,')}"
    state = {**clean_state, "active_scheme_id": entry["scheme_id"], "last_question": ""}
    next_steps = []
    if with_offer and entry["criteria"]:
        answer_text += " " + OFFER_TE
        state["eligibility_mode"] = "offered"
        state["offer_declined"] = False
        next_steps.append("మొదలుపెట్టాలంటే 'సరే' అని చెప్పండి; కావాలంటే 'కాదు'.")
    return {
        "decision": decision, "kind": "scheme", "answer_text": answer_text[:4000],
        "citations": _dedupe_citations(citations), "next_steps": next_steps[:2],
        "state": _clean_state(state),
        "evidence": [],
    }


def _ask_criterion(pack: dict[str, Any], entry: dict[str, Any], clean_state: dict[str, Any],
                   pending: dict[str, Any], repeat_prefix: bool = False) -> dict[str, Any]:
    prefix = "అర్థం కాలేదు అన్నా, మళ్లీ అడుగుతాను — " if repeat_prefix else ""
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
    citations = _criteria_evidence(pack, entry, entry["criteria"])
    parts = []
    for index, criterion in enumerate(entry["criteria"], 1):
        parts.append(f"{criterion['question_te']} → [C{index}]")
    apply_text = entry.get("how_to_apply", "").strip()
    answer_text = ("మీరు చెప్పిన వివరాల ప్రకారం, ప్రచురించిన ప్రతి అవసరానికి మీరు సరిపోతున్నారు: "
                   + " · ".join(parts)
                   + f" కాబట్టి ఈ పథకానికి అర్హులు కావచ్చు. {FINAL_DECISION_TE}")
    if apply_text:
        answer_text += f" దరఖాస్తు: {apply_text}"
    portal_match = re.match(r"https?://\S+", entry.get("portal", ""))
    if portal_match:
        answer_text += f" అధికారిక వెబ్‌సైటు: {portal_match.group(0).rstrip(').,')}"
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
    answer_text = (f"{_status_prefix(entry)}{criterion['fail_message_te']} [C1] "
                   f"(నియమం: {criterion['basis']})")
    return {
        "decision": "answer", "kind": "scheme", "answer_text": answer_text[:4000],
        "citations": [citation], "next_steps": [],
        "state": _clean_state({**clean_state, "eligibility_mode": "done", "pending_criterion": ""}),
        "evidence": [],
    }


def _decline_check(clean_state: dict[str, Any]) -> dict[str, Any]:
    state = {**clean_state, "eligibility_mode": "off", "offer_declined": True, "pending_criterion": ""}
    return {
        "decision": "answer", "kind": "conversation", "answer_text": CHECK_STOPPED_TE,
        "citations": [], "next_steps": [], "state": _clean_state(state), "evidence": [],
    }


def _new_scheme_state(clean_state: dict[str, Any], scheme_id: str, question: str) -> dict[str, Any]:
    """A genuinely new scheme: eligibility facts from the old one must never leak."""
    return _clean_state({**clean_state, "active_scheme_id": scheme_id, "eligibility_mode": "off",
                         "criteria_facts": {}, "pending_criterion": "", "unknown_notices": [],
                         "offer_declined": False, "last_question": question})


def _attach_unknown_notice(entry: dict[str, Any], reply: dict[str, Any],
                           clean_state: dict[str, Any]) -> dict[str, Any]:
    """Topics the pack lists under unknown_in_sources get their honest notice
    exactly once, one per question turn; the flow keeps going either way."""
    already = set(clean_state.get("unknown_notices", []))
    unknown = next((item for item in entry["unknown_in_sources"] if item["id"] not in already), None)
    if unknown is None:
        return clean_state
    reply["answer_text"] = f"{reply['answer_text']} {unknown['notice_te']}".strip()
    reply["state"] = _clean_state({**reply["state"],
                                   "unknown_notices": list(clean_state.get("unknown_notices", [])) + [unknown["id"]]})
    return reply["state"]


# ---------------- pure-Python eligibility evaluator (ported from the tested legacy core) ----------------

def _criterion_allowed(criterion: dict[str, Any], value: Any) -> bool:
    text = str(value).strip().lower()
    if criterion["answer_type"] == "yes_no":
        return text in YES_NO_VALUES
    allowed = criterion["required"]
    return text in {str(item).strip().lower() for item in allowed}


def _criterion_failed(criterion: dict[str, Any], value: Any) -> bool:
    text = str(value).strip().lower()
    if criterion["answer_type"] == "yes_no":
        return text != str(criterion["required"]).strip().lower()
    return not _criterion_allowed(criterion, value)


def _first_failure(criteria: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any] | None:
    for criterion in criteria:
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
    return next((criterion for criterion in criteria if not _known(criterion)), None)


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
    if intent in {"start_check", "switch_scheme", "scheme_info"} and not parse["scheme_id"]:
        keyword_scheme = _keyword_scheme(question)
        parse = {**parse, "scheme_id": keyword_scheme or (active_id if intent in {"start_check", "scheme_info"} else "")}
    scheme_id = parse["scheme_id"]

    # — running-check lanes first: answers win, everything else waits politely —
    if mode == "active":
        entry = scheme_entry(pack, active_id)
        if entry is None:
            clean_state = _clean_state({**clean_state, "eligibility_mode": "off"})
        else:
            if intent == "stop_check":
                return _decline_check(clean_state)
            if intent == "switch_scheme" or (intent == "scheme_info" and scheme_id and scheme_id != active_id):
                other = scheme_entry(pack, scheme_id) if scheme_id else None
                if other is not None and other["scheme_id"] != active_id:
                    wiped = _new_scheme_state(clean_state, other["scheme_id"], question)
                    return _scheme_info_answer(pack, other, fact_ids, with_offer=True, clean_state=wiped)
            if intent in {"check_answer", "start_check", "scheme_info"}:
                previous_facts = clean_state.get("criteria_facts", {})
                facts = _apply_extracted_facts(previous_facts, answers, entry["criteria"])
                clean_state = {**clean_state, "criteria_facts": facts}
            else:
                previous_facts = clean_state.get("criteria_facts", {})
            if intent in {"greeting", "about", "unrelated"}:
                # Ordinary conversation while a check runs: fixed honest line,
                # the check simply waits (state and pending criterion untouched).
                reply = GREETING_TE if intent == "greeting" else (ABOUT_TE if intent == "about" else UNRELATED_TE)
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
                _attach_unknown_notice(entry, reply, clean_state)
                return reply
            return _pass_reply(pack, entry, clean_state)

    # — no check running —
    if intent == "stop_check":
        entry = scheme_entry(pack, active_id)
        if entry is not None and mode != "off":
            return _decline_check(clean_state)
        return {"decision": "answer", "kind": "conversation", "answer_text": CHECK_STOPPED_TE,
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
        _attach_unknown_notice(entry, reply, clean_state)
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
        with_offer = not (mode == "offered" and entry["scheme_id"] == active_id)
        return _scheme_info_answer(pack, entry, fact_ids, with_offer=with_offer, clean_state=fresh)

    if intent == "greeting":
        return {"decision": "answer", "kind": "conversation", "answer_text": GREETING_TE,
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}
    if intent == "about":
        return {"decision": "answer", "kind": "conversation", "answer_text": ABOUT_TE,
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}
    if intent == "unrelated":
        return {"decision": "abstain", "kind": "conversation", "answer_text": UNRELATED_TE,
                "citations": [], "next_steps": [], "state": _clean_state({**clean_state, "last_question": question}),
                "evidence": []}

    # Fall-through: unable to classify → the honest bridge, never a guess.
    return {"decision": "abstain", "kind": "conversation", "answer_text": UNKNOWN_SCHEME_TE,
            "citations": [], "next_steps": [scheme["name_te"] for scheme in pack["schemes"][:3]],
            "state": _clean_state({**clean_state, "last_question": question}), "evidence": []}


def answer(question: str, state: Any = None, history: Any = None, evidence: Any = None) -> dict[str, Any]:
    return route_turn(question, state, history, evidence)
