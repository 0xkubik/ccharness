import json
from pathlib import Path


def _musician_dir(cwd):
    return Path(cwd) / ".claude" / "ccharness" / "musician"


def _resolve_run_dir(cwd, session_id=None):
    """Find this agent's active musician run folder.

    Precise: the session's pointer by-session/<session_id> -> runs/<run-id>/.
    Fallback (no/unmatched session): the newest active run in the repo.
    """
    if not cwd:
        return None
    base = _musician_dir(cwd)
    runs = base / "runs"
    if session_id:
        ptr = base / "by-session" / session_id
        if ptr.is_file():
            try:
                rid = ptr.read_text().strip()
            except OSError:
                rid = ""
            if rid and (runs / rid / "state.json").is_file():
                return runs / rid
    if runs.is_dir():
        for d in sorted(runs.iterdir(), reverse=True):
            st = d / "state.json"
            if st.is_file():
                try:
                    if json.loads(st.read_text()).get("active"):
                        return d
                except (json.JSONDecodeError, OSError):
                    continue
    return None


def _read_state(cwd, session_id=None):
    rd = _resolve_run_dir(cwd, session_id)
    if not rd:
        return None, None
    try:
        return rd, json.loads((rd / "state.json").read_text())
    except (json.JSONDecodeError, OSError):
        return rd, None


def _count_lines(p):
    try:
        return sum(1 for ln in p.read_text().splitlines() if ln.strip())
    except OSError:
        return 0


def _tail(p, n):
    try:
        lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
        return lines[-n:]
    except OSError:
        return []


def is_musician(cwd, session_id=None):
    _, st = _read_state(cwd, session_id)
    return bool(st and st.get("active"))


def cycle_count(cwd, session_id=None):
    _, st = _read_state(cwd, session_id)
    return st.get("cycle") if st else None


def musician_info(cwd, session_id=None):
    """The rich per-run picture for a running musician, or None if this isn't one."""
    rd, st = _read_state(cwd, session_id)
    if not st or not st.get("active"):
        return None
    return {
        "run_id": st.get("run_id"),
        "active": True,
        "status": st.get("status"),
        "entry": st.get("entry"),
        "input": st.get("input"),
        "done_when": st.get("done_when"),
        "cycle": st.get("cycle"),
        "no_progress_streak": st.get("no_progress_streak"),
        "awaiting": st.get("awaiting"),
        "ultracode": bool(st.get("ultracode")),
        "started_at": st.get("started_at"),
        "blocked_count": _count_lines(rd / "blocked.jsonl"),
        "last_action": (_tail(rd / "live.log", 1) or [None])[0],
    }


def live_tail(cwd, session_id=None, n=20):
    """The last n lines of the run's live action feed — what the musician is doing now."""
    rd = _resolve_run_dir(cwd, session_id)
    return _tail(rd / "live.log", n) if rd else []
