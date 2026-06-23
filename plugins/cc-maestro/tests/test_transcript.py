import os, sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ccmaestro.transcript import parse_transcript

def _line(**kw): return json.dumps(kw)

def _assistant(ts, usage=None, tool=None):
    content = []
    if tool:
        content.append({"type": "tool_use", "id": tool["id"], "name": tool["name"], "input": tool["input"]})
    msg = {"role": "assistant", "content": content}
    if usage: msg["usage"] = usage
    return _line(type="assistant", timestamp=ts, message=msg)

def _tool_result(ts, tool_use_id):
    return _line(type="user", timestamp=ts,
                 message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "ok"}]})

class TestTranscript(unittest.TestCase):
    def _write(self, lines):
        fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
        Path(p).write_text("\n".join(lines) + "\n")
        return p

    def test_missing_file_returns_zero_summary(self):
        s = parse_transcript(None)
        self.assertEqual(s["total_tokens"], 0)
        self.assertIsNone(s["last_activity"])
        self.assertEqual(s["tool_calls"], [])

    def test_sums_usage_across_assistant_turns(self):
        u = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 2, "cache_read_input_tokens": 100}
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", usage=u),
                         _assistant("2026-06-23T10:01:00.000Z", usage=u)])
        s = parse_transcript(p)
        self.assertEqual(s["output_tokens"], 10)
        self.assertEqual(s["total_tokens"], (10+5+2+100)*2)
        self.assertEqual(s["assistant_turns"], 2)

    def test_last_activity_is_latest_timestamp(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", usage={"output_tokens": 1}),
                         _tool_result("2026-06-23T10:05:00.000Z", "t1")])
        s = parse_transcript(p)
        self.assertEqual(s["last_activity"].hour, 10)
        self.assertEqual(s["last_activity"].minute, 5)

    def test_tool_calls_recorded_in_order(self):
        p = self._write([
            _assistant("2026-06-23T10:00:00.000Z", tool={"id": "a", "name": "Bash", "input": {"command": "ls"}}),
            _assistant("2026-06-23T10:00:10.000Z", tool={"id": "b", "name": "Bash", "input": {"command": "ls"}}),
        ])
        s = parse_transcript(p)
        self.assertEqual([n for n, _ in s["tool_calls"]], ["Bash", "Bash"])
        self.assertEqual(s["tool_calls"][0][1], s["tool_calls"][1][1])  # identical signature

    def test_pending_tool_true_when_no_result(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", tool={"id": "x", "name": "Bash", "input": {}})])
        self.assertTrue(parse_transcript(p)["pending_tool"])

    def test_pending_tool_false_when_result_present(self):
        p = self._write([_assistant("2026-06-23T10:00:00.000Z", tool={"id": "x", "name": "Bash", "input": {}}),
                         _tool_result("2026-06-23T10:00:30.000Z", "x")])
        self.assertFalse(parse_transcript(p)["pending_tool"])

    def test_skips_malformed_lines(self):
        p = self._write(["{not json", _assistant("2026-06-23T10:00:00.000Z", usage={"output_tokens": 7})])
        self.assertEqual(parse_transcript(p)["output_tokens"], 7)

if __name__ == "__main__":
    unittest.main()
