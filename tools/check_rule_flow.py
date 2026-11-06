# -*- coding: utf-8 -*-
"""Live check of the rule-based interview against a running adapter.

Start the backend first (from the repo root):
    py backend/voice_server.py
then run:
    py -X utf8 tools\check_rule_flow.py

Walks one scripted conversation (greeting → scheme info → offered check →
interview answers → pass) through /api/assistant/query, printing each turn's
decision, citations and timings. Uses only real provider calls; no user data
is stored — the conversation exists only in this process.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
STATE = {}

CONVERSATION = [
    "ఇందిరమ్మ ఇల్లు పథకం గురించి చెప్పు",          # scheme info + offer
    "సరే మొదలుపెడిద్దాం",                             # accept → first criterion
    "ఇల్లు లేదు అన్నా",                               # answer 1
    "తెలంగాణలోనే ఉన్నా అన్నా",                      # answer 2 → pass
]


def ask(question: str) -> dict:
    body = json.dumps({"question": question, "state": STATE, "history": [], "evidence": []},
                      ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE + "/api/assistant/query", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    print(f"[{time.perf_counter() - started:.2f}s] Q: {question}")
    print(f"  decision={result.get('decision')} kind={result.get('kind')}")
    print(f"  text: {result.get('answer_text', '')[:300]}")
    for index, citation in enumerate(result.get("citations", []), 1):
        print(f"  [C{index}] {citation.get('title', '')} — {citation.get('source_url', '')[:80]}")
    timings = result.get("stage_timings", {})
    if timings:
        print(f"  timings: parse {timings.get('parse_llm', 0) + timings.get('parse_retry_llm', 0):.2f}s"
              f"  retry-wait {timings.get('retry_wait', 0):.2f}s  total {timings.get('total', 0):.2f}s")
    STATE.clear()
    STATE.update(result.get("state", {}))
    print(f"  state: mode={STATE.get('eligibility_mode')} scheme={STATE.get('active_scheme_id')}"
          f" pending={STATE.get('pending_criterion')} facts={list(STATE.get('criteria_facts', {}).keys())}")
    print()
    return result


def main() -> None:
    for question in CONVERSATION:
        result = ask(question)
    print("final state:", json.dumps(STATE, ensure_ascii=False)[:300])
    expected_mode = {"decision": "answer"}
    if result.get("decision") not in {"answer"}:
        print("UNEXPECTED final turn:", result.get("decision"))
        sys.exit(1)
    print("OK: scripted flow completed.")


if __name__ == "__main__":
    sys.exit(main())
