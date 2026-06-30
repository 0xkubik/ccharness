import json
from datetime import datetime

_USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

def _parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None

def parse_transcript(path):
    summary = {k: 0 for k in _USAGE_KEYS}
    summary.update({"total_tokens": 0, "last_activity": None,
                    "tool_calls": [], "pending_tool": False, "assistant_turns": 0})
    if not path:
        return summary
    last_ts = None
    last_tool_use_id = None
    seen_result_ids = set()
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _parse_ts(o.get("timestamp"))
                if ts and (last_ts is None or ts > last_ts):
                    last_ts = ts
                t = o.get("type")
                msg = o.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if t == "assistant":
                    summary["assistant_turns"] += 1
                    usage = msg.get("usage") or {}
                    for k in _USAGE_KEYS:
                        summary[k] += int(usage.get(k) or 0)
                    if isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                sig = json.dumps(b.get("input"), sort_keys=True, default=str)
                                summary["tool_calls"].append((b.get("name"), sig))
                                last_tool_use_id = b.get("id")
                elif t == "user" and isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            rid = b.get("tool_use_id")
                            if rid:
                                seen_result_ids.add(rid)
    except OSError:
        return summary
    summary["total_tokens"] = sum(summary[k] for k in _USAGE_KEYS)
    summary["last_activity"] = last_ts
    summary["pending_tool"] = bool(last_tool_use_id and last_tool_use_id not in seen_result_ids)
    return summary
