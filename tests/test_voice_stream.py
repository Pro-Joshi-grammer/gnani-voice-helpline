import base64
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "Source"))

try:
    import voice_server
except ModuleNotFoundError as error:  # pragma: no cover - environment dependency
    voice_server = None
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


@unittest.skipIf(voice_server is None, f"voice adapter dependency unavailable: {IMPORT_ERROR}")
class PcmStreamFramingTests(unittest.TestCase):
    def test_meta_comes_first_with_pcm_layout(self):
        lines = list(voice_server.pcm_stream_lines(iter([b"\x01\x02", b"\x03\x04"])))
        meta = json.loads(lines[0].decode("utf-8"))
        self.assertEqual(meta["sample_rate"], 48000)
        self.assertEqual(meta["channels"], 1)
        self.assertEqual(meta["bytes_per_sample"], 2)

    def test_every_pcm_chunk_is_base64_encoded_one_per_line(self):
        chunks = [bytes([1, 2, 3]), bytes([4, 5, 6])]
        lines = list(voice_server.pcm_stream_lines(iter(chunks)))
        self.assertEqual(len(lines), 4)  # meta + 2 chunks + done
        decoded = [json.loads(line.decode("utf-8")) for line in lines[1:3]]
        self.assertEqual(decoded[0]["b64"], base64.b64encode(chunks[0]).decode("ascii"))
        self.assertEqual(decoded[1]["b64"], base64.b64encode(chunks[1]).decode("ascii"))
        self.assertTrue(all(set(item.keys()) == {"b64"} for item in decoded))

    def test_done_line_is_last_and_reports_first_timing(self):
        lines = list(voice_server.pcm_stream_lines(iter([b"\x01\x02"])))
        final = json.loads(lines[-1].decode("utf-8"))
        self.assertTrue(final["done"])
        self.assertGreaterEqual(final["first_ms"], 0.0)
        self.assertGreaterEqual(final["elapsed_ms"], final["first_ms"])

    def test_empty_chunks_are_skipped_but_first_timing_skips_them_too(self):
        # A truly empty stream: meta + done only.
        lines = list(voice_server.pcm_stream_lines(iter([])))
        self.assertEqual(len(lines), 2)
        final = json.loads(lines[-1].decode("utf-8"))
        self.assertEqual(final["first_ms"], 0.0)

    def test_streaming_is_lazy_not_buffered(self):
        # The generator must yield the meta line WITHOUT consuming the chunk
        # iterator, so the browser gets bytes before synthesis continues.
        pulled = []

        def slow_chunks():
            pulled.append("first-chunk")
            yield b"\x01\x02"

        gen = voice_server.pcm_stream_lines(slow_chunks())
        meta_line = next(gen)
        self.assertTrue(json.loads(meta_line.decode("utf-8")).get("sample_rate"))
        # Laziness proof: the chunk source ran only when we asked for more.
        self.assertEqual(pulled, [])
        pcm_line = next(gen)
        self.assertIn("b64", json.loads(pcm_line.decode("utf-8")))
        self.assertEqual(pulled, ["first-chunk"])
        self.assertIsNotNone(next(gen))


if __name__ == "__main__":
    unittest.main()
