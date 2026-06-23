import json, os
from pathlib import Path

STATE_DIR = Path(os.environ.get("CCMAESTRO_HOME") or (Path.home() / ".ccmaestro"))

DEFAULTS = {
    "stall_min": 5,            # minutes with no new transcript line -> stalled
    "tool_stall_min": 20,      # higher threshold when a tool call is in flight
    "loop_n": 4,               # same (tool, input) repeated this many times -> looping
    "loop_window": 8,          # only consider the last N tool calls
    "token_budget": 0,         # gross tokens over this -> over-budget (0 = disabled)
    "autopilot_stall_min": 30, # autopilot: no new cycle in this many minutes -> stalled
    "report_endpoint": "",     # optional webhook URL (used in Phase 3)
}

def load_config():
    cfg = dict(DEFAULTS)
    f = STATE_DIR / "config.json"
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                cfg.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg
