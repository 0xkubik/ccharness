import json
from pathlib import Path

def _state_dir(cwd):
    return Path(cwd) / ".claude" / "ccharness" / "musician"

def is_musician(cwd):
    if not cwd:
        return False
    f = _state_dir(cwd) / "state.json"
    if not f.exists():
        return False
    try:
        return bool(json.loads(f.read_text()).get("active"))
    except (json.JSONDecodeError, OSError):
        return False

def cycle_count(cwd):
    if not cwd:
        return None
    f = _state_dir(cwd) / "state.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text()).get("cycle")
    except (json.JSONDecodeError, OSError):
        return None
