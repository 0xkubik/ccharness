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
    "max_concurrent": 0,       # max agents start will launch concurrently (0 = unlimited)
    # --spend-weekly supervisor (see spend.py). Relaunches /autopilot --spend-session across
    # 5-hour resets until the weekly horizon; classifies each death blind (no limit detection).
    "spend_fast_death_s": 120,        # a session dying under this ran too briefly to be a limit hit -> crash
    "spend_max_fast_deaths": 4,       # this many consecutive fast deaths -> give up
    "spend_horizon_s": 604800,        # 7 days wall clock -> the weekly stop
    "spend_limit_wait_s": 1800,       # blind probe interval after a presumed limit hit
    "spend_crash_base_s": 60,         # crash backoff base
    "spend_crash_max_s": 900,         # crash backoff ceiling
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
