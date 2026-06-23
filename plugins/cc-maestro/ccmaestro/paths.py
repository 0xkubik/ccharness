import os
from pathlib import Path
from . import config

def _claude_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))

def transcript_path(session_id):
    """Locate a session's transcript by sessionId (robust to cwd path encoding)."""
    projects = _claude_dir() / "projects"
    if not projects.exists():
        return None
    matches = sorted(projects.glob(f"*/{session_id}.jsonl"))
    return matches[0] if matches else None

def agent_dir(agent_id):
    return config.STATE_DIR / "agents" / agent_id

def ensure_state_dir():
    (config.STATE_DIR / "agents").mkdir(parents=True, exist_ok=True)

def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)
