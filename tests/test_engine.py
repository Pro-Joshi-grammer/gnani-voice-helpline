# -*- coding: utf-8 -*-
"""Rule-engine tests: the progressive eligibility interview over the pack.

The suite is fully hermetic: the turn's only LLM call (`engine._chat_parse`)
is patched everywhere — eligibility itself is pure Python and runs for real.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

import engine  # noqa: E402

INDIRAMMA = "indiramma_indlu"
RYTHU = "rythu_bharosa"

PARSE_OK = {"intent": "unrelated", "scheme_id": "", "answers": {}, "fact_ids": []}


def parsed(intent="", scheme_id="", answers=None, fact_ids=None):
    return json_parse(intent, scheme_id, answers, fact_ids)


def json_parse(intent, scheme_id, answers, fact_ids):
    return {
        "intent": intent,
        "scheme_id": scheme_id,
        "answers": answers or {},
        "fact_ids": fact_ids or [],
    }


def mock_parse(intent="", scheme_id="", answers=None, fact_ids=None):
    return patch.object(engine, "_chat_parse", return_value=json_parse(intent, scheme_id, answers, fact_ids))


def mock_parse_failing():
    def boom(*args, **kwargs):
        raise RuntimeError("provider down")
    return patch.object(engine, "_chat_parse", side_effect=boom)


def active_state(scheme_id, pending, facts=None, notices=None):
    return {
        "active_scheme_id": scheme_id,
        "eligibility_mode": "active",
        "pending_criterion": pending,
        "criteria_facts": facts or {},
        "unknown_notices": notices or [],
        "offer_declined": False,
    }


class RouteTurnBase(unittest.TestCase):
    def turn(self, question="x", state=None, history=None, mock=None):
        ctx = mock or mock_parse()
        with ctx:
            result = engine.route_turn(question, state, history, [])
        self.assertIn("stage_timings", result)
        self.assertIn("parse_llm", result["stage_timings"])
        self.assertIn("total", result["stage_timings"])
        return result


class ConversationTurns(RouteTurnBase):
    def test_greeting_gets_fixed_reply_without_citations_or_llm_prose(self):
        result = self.turn("నమస్కారం", mock=mock_parse("greeting"))
        self.assertEqual(result["decision"], "answer")
        self.assertEqual(result["kind"], "conversation")
        self.assertEqual(result["answer_text"], engine.GREETING_TE)
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["state"]["eligibility_mode"], "off")

    def test_about_describes_capabilities_honestly(self):
        result = self.turn("నువ్వు ఎవరు?", mock=mock_parse("about"))
        self.assertEqual(result["answer_text"], engine.ABOUT_TE)
        self.assertEqual(result["citations"], [])

    def test_unrelated_turn_abstains_and_never_invents(self):
        result = self.turn("ఇంకో ఊరి బస్సు టైం చెప్పు", mock=mock_parse("unrelated"))
        self.assertEqual(result["decision"], "abstain")
        self.assertEqual(result["answer_text"], engine.UNRELATED_TE)
        self.assertEqual(result["citations"], [])

    def test_empty_question_asks_back(self):
        with mock_parse_failing():
            result = engine.route_turn("", None, None, [])
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["citations"], [])

    def test_conversation_waits_politely_while_a_check_is_active(self):
        state = active_state(INDIRAMMA, "owns_house")
        result = self.turn("నమస్కారం", state=state, mock=mock_parse("greeting"))
        self.assertEqual(result["answer_text"], engine.GREETING_TE)
        # The check must NOT be reset just because of a greeting.
        self.assertEqual(result["state"]["eligibility_mode"], "active")
        self.assertEqual(result["state"]["pending_criterion"], "owns_house")


class SchemeInfoTurns(RouteTurnBase):
    def test_scheme_facts_answered_from_pack_with_citation_and_offer(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["amount"]):
            result = engine.route_turn("ఇందిరమ్మ ఇంట్లు ఎక్కువ డబ్బు ఇస్తాయి మరి", None, None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertEqual(result["kind"], "scheme")
        text = result["answer_text"]
        self.assertTrue(text, "answer must not be empty")
        self.assertIn("[C1]", text)
        self.assertIn(engine.OFFER_TE, text, "an offered check must be mentioned")
        citation = result["citations"][0]
        self.assertEqual(citation["scheme_id"], INDIRAMMA)
        self.assertTrue(citation["source_url"].startswith("http"),
                        "citation must carry the pack's source URL")
        self.assertEqual(result["state"]["eligibility_mode"], "offered")
        self.assertEqual(result["state"]["active_scheme_id"], INDIRAMMA)

    def test_scheme_info_without_fact_ids_falls_back_to_best_facts(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=[]):
            result = engine.route_turn("ఇందిరమ్మ పథకం చెప్పు", None, None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertTrue(result["answer_text"])
        self.assertTrue(result["citations"], "default facts must still cite sources")

    def test_uncoverable_fact_request_abstains_instead_of_substituting(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["made_up_topic"]):
            result = engine.route_turn("అంతర్జాతీయ ఏదో విషయం", None, None, [])
        self.assertEqual(result["decision"], "abstain")
        self.assertEqual(result["citations"], [])
        self.assertIn(engine.NOT_IN_SOURCES_TE, result["answer_text"])

    def test_scheme_with_zero_criteria_offers_no_check(self):
        # mahalakshmi_monthly_aid_2500 currently has no sourced criteria.
        with mock_parse("scheme_info", "mahalakshmi_monthly_aid_2500", fact_ids=[]):
            result = engine.route_turn("2500 పథకం", None, None, [])
        self.assertNotEqual(result["state"]["eligibility_mode"], "offered")
        self.assertNotIn(engine.OFFER_TE, result["answer_text"])

    def test_non_active_status_gets_its_note_before_benefits(self):
        with mock_parse("scheme_info", "mahalakshmi_monthly_aid_2500", fact_ids=[]):
            result = engine.route_turn("2500 ఎప్పుడు ఇస్తారు", None, None, [])
        self.assertIn("ముఖ్యమైన విషయం", result["answer_text"],
                      "pack rule: non-active statuses are stated before benefits")
        self.assertTrue(result["state"]["eligibility_mode"] != "offered")


class EligibilityFlowTurns(RouteTurnBase):
    def start_check(self):
        with mock_parse("scheme_info", INDIRAMMA):
            return engine.route_turn("ఇందిరమ్మ చెప్పు", None, None, [])

    def accept_check(self, offered_state):
        with mock_parse("start_check", ""):
            return engine.route_turn("సరే మొదలుపెడిద్దాం", offered_state, None, [])

    def test_accepting_the_offer_asks_the_first_criterion(self):
        offered = self.start_check()["state"]
        result = self.accept_check(offered)
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["kind"], "scheme")
        self.assertIn("[C1]", result["answer_text"])
        self.assertEqual(result["state"]["eligibility_mode"], "active")
        criteria = {c["id"] for c in engine.scheme_entry(engine.load_pack(), INDIRAMMA)["criteria"]}
        self.assertIn(result["state"]["pending_criterion"], criteria)

    def test_check_answer_advances_to_next_criterion_and_cites_it(self):
        with mock_parse("check_answer", "", answers={"owns_house": "no"}):
            result = engine.route_turn("ఇల్లు లేదు", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["state"]["pending_criterion"], "telangana_family",
                         "the first filled key-pair is remembered; only the next is asked")
        self.assertEqual(result["state"]["criteria_facts"]["owns_house"]["value"], "no")
        self.assertEqual(result["state"]["criteria_facts"]["owns_house"]["source"], "user_stated")
        self.assertIn("[C1]", result["answer_text"])
        citation = result["citations"][0]
        self.assertEqual(citation["scheme_id"], INDIRAMMA)

    def test_failed_criterion_stops_the_flow_with_its_own_source(self):
        with mock_parse("check_answer", "", answers={"owns_house": "yes"}):
            result = engine.route_turn("మా ఇంట్లో ఉంది అక్కడే", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["decision"], "answer")
        entry = engine.scheme_entry(engine.load_pack(), INDIRAMMA)
        criterion = entry["criteria"][0]
        self.assertIn(criterion["fail_message_te"], result["answer_text"])
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["citations"][0]["id"], criterion["source_id"])
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_all_criteria_pass_cites_every_criterion_and_leaves_the_decision_to_officials(self):
        state = active_state(INDIRAMMA, "telangana_family", facts={"owns_house": {"value": "no", "source": "user_stated"}})
        with mock_parse("check_answer", "", answers={"telangana_family": "yes"}):
            result = engine.route_turn("తెలంగాణలోనే ఉన్నా", state, None, [])
        self.assertEqual(result["decision"], "answer")
        text = result["answer_text"]
        for marker in ("[C1]", "[C2]"):
            self.assertIn(marker, text)
        self.assertEqual(len(result["citations"]), 2)
        self.assertIn(engine.FINAL_DECISION_TE, text)
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_stop_check_during_a_running_check_stops_without_sticking(self):
        with mock_parse("stop_check"):
            result = engine.route_turn("చాలు ఆపెయ్", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertEqual(result["answer_text"], engine.CHECK_STOPPED_TE)
        self.assertEqual(result["state"]["eligibility_mode"], "off")
        self.assertEqual(result["state"]["criteria_facts"], {})
        self.assertTrue(result["state"]["offer_declined"])

    def test_switch_scheme_wipes_previous_scheme_facts(self):
        state = active_state(INDIRAMMA, "telangana_family",
                             facts={"owns_house": {"value": "no", "source": "user_stated"}})
        with mock_parse("switch_scheme", RYTHU):
            result = engine.route_turn("ఇప్పుడు రైతు భరోసా చెప్పు", state, None, [])
        self.assertEqual(result["state"]["active_scheme_id"], RYTHU)
        self.assertEqual(result["state"]["criteria_facts"], {},
                         "eligibility facts must never leak across schemes")
        self.assertEqual(result["state"]["eligibility_mode"], "offered")
        self.assertNotIn("owns_house", result["answer_text"], "old scheme results must not be summarized into the new scheme")

    def test_unknown_in_sources_topic_is_noticed_once_and_flow_continues(self):
        with mock_parse("start_check", RYTHU):
            first = engine.route_turn("రైతు తనిఖీ మొదలుపెడ్డాం", None, None, [])
        self.assertEqual(first["decision"], "ask")
        notices = [u["notice_te"] for u in engine.scheme_entry(engine.load_pack(), RYTHU)["unknown_in_sources"]]
        shown = next((n for n in notices if n in first["answer_text"]), None)
        self.assertIsNotNone(shown, "a topic missing from sources must be honestly noticed")
        with mock_parse("check_answer", "", answers={"telangana_resident": "yes"}):
            second = engine.route_turn("అవును ఇక్కడే ఉన్నా", first["state"], None, [])
        self.assertEqual(second["decision"], "ask")
        self.assertNotIn(shown, second["answer_text"], "the unknown notice must appear exactly once")


class AnswerSlotSafety(RouteTurnBase):
    def test_out_of_space_parse_value_triggers_deterministic_fallback_not_a_judgement(self):
        # The parser must fill slots strictly inside the criterion's value space;
        # a fabricated value breaks the strict contract, and the turn survives
        # over the deterministic fallback (a polite wait) — never judged.
        state = active_state(INDIRAMMA, "owns_house")
        with mock_parse("check_answer", "", answers={"owns_house": "maybe"}):
            result = engine.route_turn("ఎలా చెప్పనో తెలియదు", state, None, [])
        self.assertNotIn("owns_house", result["state"]["criteria_facts"],
                         "an out-of-space value must never be stored")
        self.assertEqual(result["state"]["eligibility_mode"], "active")

    def test_llm_down_falls_back_to_the_keyword_lexicon_and_judges_the_answer(self):
        with mock_parse_failing():
            result = engine.route_turn("అవును", active_state(INDIRAMMA, "owns_house"), None, [])
        # owns_house requires "no" — a "yes" is a genuine early fail, cited.
        self.assertEqual(result["decision"], "answer")
        entry = engine.scheme_entry(engine.load_pack(), INDIRAMMA)
        self.assertIn(entry["criteria"][0]["fail_message_te"], result["answer_text"])
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_llm_down_falls_back_to_the_keyword_lexicon_for_no_answers(self):
        with mock_parse_failing():
            result = engine.route_turn("లేదు అన్నా", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["state"]["criteria_facts"]["owns_house"]["value"], "no")

    def test_llm_down_falls_back_to_scheme_keyword_routing(self):
        with mock_parse_failing():
            result = engine.route_turn("ఇందిరమ్మ ఇల్లు పథకం చెప్పు", None, None, [])
        self.assertEqual(result["kind"], "scheme")
        self.assertEqual(result["state"]["active_scheme_id"], INDIRAMMA)

    def test_out_of_space_stored_value_is_reasked_never_judged(self):
        entry = engine.scheme_entry(engine.load_pack(), INDIRAMMA)
        criterion = entry["criteria"][0]
        self.assertIsNone(engine._first_failure(
            entry["criteria"], {criterion["id"]: {"value": ""}}))
        self.assertIsNone(engine._first_failure(
            entry["criteria"], {criterion["id"]: {"value": "maybe"}}),
            "an out-of-value-space stored value is in-askable, never judged")

    def test_current_criterion_semantics_pass_only_on_the_expected_value(self):
        self.assertTrue(engine._criterion_failed({"answer_type": "yes_no", "required": "no"}, "yes"))
        self.assertFalse(engine._criterion_failed({"answer_type": "yes_no", "required": "no"}, "no"))


class PackSafety(unittest.TestCase):
    def test_missing_pack_reads_empty_but_never_crashes(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.json"
            path.write_text("{}", encoding="utf-8")
            previous = os.environ.get("GNANI_PACK_PATH")
            os.environ["GNANI_PACK_PATH"] = str(path)
            engine._PACK_CACHE["mtime"] = None
            try:
                with patch.object(engine, "_chat_parse", return_value=json_parse("greeting", "", [], [])):
                    result = engine.route_turn("నమస్కారం", None, None, [])
                self.assertEqual(result["answer_text"], engine.GREETING_TE)
            finally:
                if previous is None:
                    os.environ.pop("GNANI_PACK_PATH", None)
                else:
                    os.environ["GNANI_PACK_PATH"] = previous
                engine._PACK_CACHE["mtime"] = None  # restore real pack for later tests

    def test_pack_cache_is_bounded_and_sources_carry_urls(self):
        pack = engine.load_pack()
        self.assertLessEqual(len(pack["schemes"]), 20)
        for source in list(pack["sources"].values())[:5]:
            self.assertIn("url", source)
            self.assertIn("title", source)


if __name__ == "__main__":
    unittest.main()
