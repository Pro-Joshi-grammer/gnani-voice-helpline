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


def parsed(intent="", scheme_id="", answers=None, fact_ids=None, reply_text=""):
    return json_parse(intent, scheme_id, answers, fact_ids, reply_text)


def json_parse(intent, scheme_id, answers, fact_ids, reply_text=""):
    return {
        "intent": intent,
        "scheme_id": scheme_id,
        "answers": answers or {},
        "fact_ids": fact_ids or [],
        "reply_text": reply_text,
    }


def mock_parse(intent="", scheme_id="", answers=None, fact_ids=None, reply_text=""):
    return patch.object(engine, "_chat_parse", return_value=json_parse(intent, scheme_id, answers, fact_ids, reply_text))


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
    def test_greeting_uses_llm_wording_without_citations(self):
        reply = "నమస్కారం! ఏ పథకం గురించి తెలుసుకోవాలి?"
        result = self.turn("నమస్కారం", mock=mock_parse("greeting", reply_text=reply))
        self.assertEqual(result["decision"], "answer")
        self.assertEqual(result["kind"], "conversation")
        self.assertEqual(result["answer_text"], reply)
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["state"]["eligibility_mode"], "off")

    def test_about_uses_llm_wording_and_keeps_privacy_guard(self):
        result = self.turn("నువ్వు ఎవరు?", mock=mock_parse("about", reply_text="నేను పథకాల సమాచారం అందిస్తాను."))
        self.assertTrue(result["answer_text"].startswith("నేను పథకాల సమాచారం అందిస్తాను."))
        self.assertIn("ప్రభుత్వ కార్యాలయం కాదు", result["answer_text"])
        self.assertIn("Aadhaar", result["answer_text"])
        self.assertEqual(result["citations"], [])

    def test_missing_llm_reply_uses_fixed_fallback(self):
        result = self.turn("నమస్కారం", mock=mock_parse("greeting"))
        self.assertEqual(result["answer_text"], engine.GREETING_TE)

    def test_unrelated_turn_uses_llm_wording_and_keeps_scope_guard(self):
        result = self.turn("ఇంకో ఊరి బస్సు టైం చెప్పు",
                           mock=mock_parse("unrelated", reply_text="క్షమించండి, దానిలో సహాయం చేయలేను."))
        self.assertEqual(result["decision"], "abstain")
        self.assertIn("క్షమించండి", result["answer_text"])
        self.assertIn(engine.UNRELATED_SCOPE_TE, result["answer_text"])
        self.assertEqual(result["citations"], [])

    def test_empty_question_asks_back(self):
        with mock_parse_failing():
            result = engine.route_turn("", None, None, [])
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["citations"], [])

    def test_conversation_waits_politely_while_a_check_is_active(self):
        state = active_state(INDIRAMMA, "owns_house")
        result = self.turn("నమస్కారం", state=state,
                           mock=mock_parse("greeting", reply_text="నమస్కారం!"))
        self.assertEqual(result["answer_text"], "నమస్కారం!")
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
        self.assertEqual(engine.OFFER_TE, "ఈ పథకానికి మీ అర్హతను కూడా చూసుకోవాలా?")
        self.assertNotIn("ప్రచురిత ప్రమాణాలతో", text)
        self.assertNotIn("ఒక్క ప్రశ్న ఒక్క ప్రశ్నగా", text)
        citation = result["citations"][0]
        self.assertEqual(citation["scheme_id"], INDIRAMMA)
        self.assertTrue(citation["source_url"].startswith("http"),
                        "citation must carry the pack's source URL")
        self.assertEqual(result["state"]["eligibility_mode"], "offered")
        self.assertEqual(result["state"]["active_scheme_id"], INDIRAMMA)

    def test_completed_check_does_not_offer_the_same_check_again(self):
        state = {
            "active_scheme_id": INDIRAMMA,
            "eligibility_mode": "done",
            "pending_criterion": "",
            "criteria_facts": {"low_income": {"value": "no", "source": "user_stated"}},
        }
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["priority_groups"],
                        reply_text="SC, ST వర్గాలకు ప్రాధాన్యత ఉంటుంది."):
            result = engine.route_turn("SC ST వారికి ప్రాధాన్యత ఉందా?", state, None, [])
        self.assertNotIn(engine.OFFER_TE, result["answer_text"])
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_application_guidance_asks_user_to_choose_online_or_offline(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["application_process"],
                        reply_text="ఆన్‌లైన్, ఆఫ్‌లైన్ దరఖాస్తు విధానాలు ఇవి."):
            result = engine.route_turn("దరఖాస్తు ఎలా చేయాలి?", None, None, [])
        self.assertIn("మీరు ఆన్‌లైన్‌లో దరఖాస్తు చేయాలనుకుంటున్నారా, లేక ఆఫ్‌లైన్‌లోనా?",
                      result["answer_text"])
        self.assertTrue(result["citations"])

    def test_application_guidance_skips_channel_choice_when_user_already_chose(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["application_process"],
                        reply_text="ఆన్‌లైన్‌లో దరఖాస్తు చేయండి."):
            result = engine.route_turn("ఆన్‌లైన్‌లో ఎలా దరఖాస్తు చేయాలి?", None, None, [])
        self.assertNotIn("మీరు ఆన్‌లైన్‌లో దరఖాస్తు చేయాలనుకుంటున్నారా", result["answer_text"])

    def test_document_question_uses_the_scheme_checklist_even_if_parser_misses_it(self):
        cases = [
            ("rythu_bharosa", "రైతు భరోసా", "required_documents", "పట్టాదారు పాస్‌బుక్"),
            ("gruha_jyothi", "గృహ జ్యోతి", "required_documents", "విద్యుత్ బిల్లు"),
            ("mahalakshmi_lpg_500", "మహాలక్ష్మి", "required_documents", "గ్యాస్ వినియోగదారు వివరాలు"),
        ]
        for scheme_id, prompt, fact_id, expected in cases:
            with self.subTest(scheme=scheme_id), mock_parse("scheme_info", scheme_id, fact_ids=[]):
                result = engine.route_turn(f"{prompt} పథకానికి ఏ డాక్యుమెంట్లు కావాలి?", None, None, [])
            self.assertIn(expected, result["answer_text"])
            self.assertTrue(result["citations"])
            self.assertEqual(result["citations"][0]["id"], "user-provided-verified-info")
            self.assertEqual(result["citations"][0]["source_url"], "")
            self.assertNotIn("upload", result["answer_text"].lower())

    def test_gruha_jyothi_info_covers_tenants_with_parenthetical_glosses(self):
        with mock_parse("scheme_info", "gruha_jyothi", fact_ids=[]):
            result = engine.route_turn("అద్దె ఇంట్లో ఉండేవారికి గృహ జ్యోతి వస్తుందా?", None, None, [])
        self.assertIn("అద్దె ఇంట్లో ఉండేవారూ అర్హులు", result["answer_text"])
        with mock_parse("scheme_info", "rythu_bharosa", fact_ids=[]):
            bank = engine.route_turn("బ్యాంక్ సీడింగ్ అంటే ఏమిటి?", None, None, [])
        self.assertIn("(బ్యాంకు ఖాతాను ఆధార్‌తో లింక్ చేయడం)", bank["answer_text"])

    def test_completed_check_followed_by_application_steps_does_not_reoffer(self):
        state = {"active_scheme_id": "gruha_jyothi", "eligibility_mode": "done"}
        with mock_parse("scheme_info", "gruha_jyothi", fact_ids=[]):
            result = engine.route_turn("దరఖాస్తు ఎలా చేయాలి?", state, None, [])
        self.assertIn("ఆఫ్‌లైన్‌:", result["answer_text"])
        self.assertIn("మీరు ఆన్‌లైన్‌లో దరఖాస్తు చేయాలనుకుంటున్నారా", result["answer_text"])
        self.assertNotIn(engine.OFFER_TE, result["answer_text"])
        self.assertTrue(result["citations"])

    def test_scheme_info_without_fact_ids_falls_back_to_best_facts(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=[]):
            result = engine.route_turn("ఇందిరమ్మ పథకం చెప్పు", None, None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertTrue(result["answer_text"])
        self.assertTrue(result["citations"], "default facts must still cite sources")

    def test_scheme_answer_uses_llm_wording_without_appended_english_or_links(self):
        reply = "ఈ పథకం అర్హులైన కుటుంబాలకు ఇల్లు నిర్మించుకునే సహాయం అందిస్తుంది."
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=["amount"],
                        reply_text=reply + " [మూలం](https://example.gov) https://example.gov [C9]"):
            result = engine.route_turn("ఇందిరమ్మలో ఎంత సహాయం వస్తుంది?", None, None, [])
        text = result["answer_text"]
        self.assertTrue(text.startswith(reply))
        self.assertIn("[C1]", text)
        self.assertNotIn("[C9]", text)
        self.assertNotIn("https://", text)
        self.assertNotIn(engine.scheme_entry(engine.load_pack(), INDIRAMMA)["how_to_apply"], text)
        self.assertEqual(result["citations"][0]["scheme_id"], INDIRAMMA)
        self.assertTrue(result["citations"][0]["source_url"].startswith("http"))

    def test_uncoverable_generated_answer_abstains_without_substituting_facts(self):
        with mock_parse("scheme_info", INDIRAMMA, fact_ids=[], reply_text="మూలాల్లో ఈ విషయం లేదు."):
            result = engine.route_turn("ఇందిరమ్మలో నాకు తెలియని విషయం?", None, None, [])
        self.assertEqual(result["decision"], "abstain")
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["answer_text"], engine.NOT_IN_SOURCES_TE)

    def test_llm_prompt_is_telugu_first_grounded_and_does_not_solicit_personal_data(self):
        with patch.object(engine, "_chat_parse", return_value=json_parse("greeting", "", [], [])) as call:
            engine.route_turn("నమస్కారం", None, None, [])
        prompt = call.call_args.args[0]
        self.assertIn("Telugu-first", prompt)
        self.assertIn("rural listener can understand", prompt)
        self.assertIn("Pack context (the only source of scheme claims)", prompt)
        self.assertIn("Do not ask for caste or income unless", prompt)
        self.assertIn("answer the user's question directly", prompt)
        self.assertIn("Do not introduce yourself by the name Gnani", prompt)
        self.assertIn("generic preambles, filler", prompt)
        self.assertIn("Never request Aadhaar, bank, or OTP details", prompt)
        self.assertIn("never ask users to upload or share documents in chat", prompt)
        self.assertIn("finish by asking whether they prefer online or offline", prompt)

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

    def test_short_colloquial_negative_answer_advances_the_pending_check(self):
        state = active_state(INDIRAMMA, "other_property", facts={
            "owns_house": {"value": "no", "source": "user_stated"},
            "telangana_family": {"value": "yes", "source": "user_stated"},
            "low_income": {"value": "yes", "source": "user_stated"},
        })
        with mock_parse("unrelated", reply_text="సరేనండి, ఇంకేదైనా అడగండి."):
            result = engine.route_turn("ఆహా ఏం లేదు", state, None, [])
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["state"]["criteria_facts"]["other_property"]["value"], "no")
        self.assertEqual(result["state"]["pending_criterion"], "prior_housing_benefit")

    def test_criterion_clarification_explains_and_keeps_the_pending_question(self):
        state = active_state(INDIRAMMA, "other_property", facts={
            "owns_house": {"value": "no", "source": "user_stated"},
            "telangana_family": {"value": "yes", "source": "user_stated"},
            "low_income": {"value": "yes", "source": "user_stated"},
        })
        clarification = "అవును, వ్యవసాయ భూమి లేదా ప్లాట్ వంటి ఇతర స్థిరాస్తి ఉందా అని అడుగుతున్నాను."
        with mock_parse("check_clarification", reply_text=clarification):
            result = engine.route_turn("ఇది వ్యవసాయ భూమి లాంటిదా?", state, None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertIn("వ్యవసాయ భూమి", result["answer_text"])
        self.assertIn("[C1]", result["answer_text"])
        self.assertEqual(result["state"]["pending_criterion"], "other_property")
        self.assertEqual(result["state"]["eligibility_mode"], "active")
        self.assertNotIn("other_property", result["state"]["criteria_facts"])

    def test_failed_criterion_stops_the_flow_with_its_own_source(self):
        with mock_parse("check_answer", "", answers={"owns_house": "yes"}):
            result = engine.route_turn("మా ఇంట్లో ఉంది అక్కడే", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["decision"], "answer")
        entry = engine.scheme_entry(engine.load_pack(), INDIRAMMA)
        criterion = entry["criteria"][0]
        self.assertIn(criterion["fail_message_te"], result["answer_text"])
        self.assertNotIn(criterion["basis"], result["answer_text"])
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["citations"][0]["id"], criterion["source_id"])
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_all_base_criteria_pass_and_cure_questions_are_skipped_outside_cure(self):
        facts = {
            "owns_house": {"value": "no", "source": "user_stated"},
            "telangana_family": {"value": "yes", "source": "user_stated"},
            "low_income": {"value": "yes", "source": "user_stated"},
            "other_property": {"value": "no", "source": "user_stated"},
            "prior_housing_benefit": {"value": "no", "source": "user_stated"},
        }
        answers = {"cure_area": "no"}
        state = active_state(INDIRAMMA, "cure_area", facts=facts)
        with mock_parse("check_answer", "", answers=answers):
            result = engine.route_turn("హైదరాబాద్ పరిధిలో కాదు", state, None, [])
        self.assertEqual(result["decision"], "answer")
        for marker in ("[C1]", "[C2]", "[C3]", "[C4]", "[C5]"):
            self.assertIn(marker, result["answer_text"])
        self.assertNotIn("[C6]", result["answer_text"])
        self.assertEqual(len(result["citations"]), 5)
        self.assertIn(engine.FINAL_DECISION_TE, result["answer_text"])
        self.assertIn("దరఖాస్తు చేసుకోవడానికి అర్హత ఉన్నట్లు కనిపిస్తోంది", result["answer_text"])
        self.assertIn("దరఖాస్తు విధానం చెప్పనా", result["answer_text"])
        self.assertIn("ఇంకేదైనా సహాయం కావాలా", result["answer_text"])
        self.assertEqual(result["state"]["eligibility_mode"], "done")

    def test_cure_criteria_are_asked_only_after_cure_area_is_confirmed(self):
        facts = {
            "owns_house": {"value": "no", "source": "user_stated"},
            "telangana_family": {"value": "yes", "source": "user_stated"},
            "low_income": {"value": "yes", "source": "user_stated"},
            "other_property": {"value": "no", "source": "user_stated"},
            "prior_housing_benefit": {"value": "no", "source": "user_stated"},
        }
        state = active_state(INDIRAMMA, "cure_area", facts=facts)
        with mock_parse("check_answer", "", answers={"cure_area": "yes"}):
            result = engine.route_turn("అవును, హైదరాబాద్ CUREలోనే", state, None, [])
        self.assertEqual(result["decision"], "ask")
        self.assertEqual(result["state"]["pending_criterion"], "cure_residence_years")

    def test_stop_check_uses_llm_wording_but_code_resets_the_check(self):
        with mock_parse("stop_check", reply_text="సరే, తనిఖీ ఆపాను."):
            result = engine.route_turn("చాలు ఆపెయ్", active_state(INDIRAMMA, "owns_house"), None, [])
        self.assertEqual(result["decision"], "answer")
        self.assertEqual(result["answer_text"], "సరే, తనిఖీ ఆపాను.")
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
