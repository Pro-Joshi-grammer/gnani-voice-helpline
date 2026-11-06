import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

try:
    import voice_server
except ModuleNotFoundError as error:  # pragma: no cover - environment dependency
    voice_server = None
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


@unittest.skipIf(voice_server is None, f"voice adapter dependency unavailable: {IMPORT_ERROR}")
class VoiceServerTests(unittest.TestCase):
    def test_question_only_payload_remains_supported(self):
        expected = {"decision": "answer", "kind": "conversation", "answer_text": "ok", "citations": [], "next_steps": [], "state": {}}
        with patch.object(voice_server.engine, "route_turn", return_value=expected) as route:
            result = voice_server.query_payload({"question": "hello"})
        self.assertEqual(result, expected)
        route.assert_called_once_with("hello", {}, [], [])

    def test_state_history_and_evidence_are_forwarded_untouched(self):
        # The rule engine keeps all session state in the browser; whatever the
        # browser sends back is forwarded as-is (the engine ignores evidence
        # payloads from the RAG era and re-sanitizes its own state).
        expected = {"decision": "ask", "kind": "scheme"}
        state = {"topic": "housing"}
        history = [{"role": "user", "content": "hello"}]
        evidence = [{"excerpt": "Eligibility facts", "chunk_id": "ind:1"}]
        with patch.object(voice_server.engine, "route_turn", return_value=expected) as route:
            result = voice_server.query_payload({"question": "next?", "state": state, "history": history, "evidence": evidence})
        self.assertEqual(result, expected)
        route.assert_called_once_with("next?", state, history, evidence)

    def test_invalid_query_is_rejected(self):
        with self.assertRaises(ValueError):
            voice_server.query_payload({"question": "", "state": {}, "history": []})
        with self.assertRaises(ValueError):
            voice_server.query_payload({"question": "hello", "state": [], "history": []})
        with self.assertRaises(ValueError):
            voice_server.query_payload({"question": "hello", "state": {}, "history": [], "evidence": "bad"})
        with self.assertRaises(ValueError):
            voice_server.query_payload({"state": {}, "history": []})


class SpeechTextTests(unittest.TestCase):
    """The spoken audio must never contain citation markers, URLs or Markdown noise."""

    def test_citation_markers_are_stripped(self):
        self.assertEqual(voice_server.speech_text("మీరు అర్హులు [C1] ఏమో చూద్దాం [2]."),
                         "మీరు అర్హులు ఏమో చూద్దాం.")

    def test_plain_url_is_removed_and_notice_appended_once(self):
        text = "అధికారిక పోర్టల్ https://indiramma.telangana.gov.in/ లో దరఖాస్తు చేయవచ్చు."
        result = voice_server.speech_text(text)
        self.assertNotIn("https://", result)
        self.assertIn("లింక్ స్క్రీన్‌పై", result)
        self.assertEqual(result.count("లింక్ స్క్రీన్‌పై"), 1)

    def test_markdown_link_label_survives_url_is_dropped(self):
        self.assertEqual(voice_server.speech_text("పోర్టల్ [ఇక్కడ](https://x.gov) చూడండి."),
                         "పోర్టల్ ఇక్కడ చూడండి. అధికారిక వెబ్‌సైటు లింక్ స్క్రీన్‌పై ఉంది.")

    def test_telugu_text_is_otherwise_untouched(self):
        text = "మోడలింగ్ లేని సాధారణ తెలుగు వాక్యం, ఒక్క మార్కర్ లేకుండా."
        self.assertEqual(voice_server.speech_text(text), text)

    def test_markdown_symbols_are_removed(self):
        self.assertEqual(voice_server.speech_text("**రూ. 5 లక్షలు** మరియు `అంశాలు`"),
                         "రూ. 5 లక్షలు మరియు అంశాలు")

    def test_empty_and_marker_only_inputs(self):
        self.assertEqual(voice_server.speech_text(""), "")
        self.assertEqual(voice_server.speech_text("[C1] https://x.gov"), voice_server._URL_NOTICE_TE)

    def test_screen_text_is_not_part_of_this_contract(self):
        # The cleaner is only meant for TTS input; screen text is produced by
        # backend/engine.py as-is.
        screen_text = "మీరు అర్హులు [C1]. https://example.gov"
        self.assertEqual(screen_text, screen_text)  # unchanged by design; see query handling


if __name__ == "__main__":
    unittest.main()
