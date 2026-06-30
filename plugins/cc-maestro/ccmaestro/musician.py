import json, os
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


def _tail(p, n):
    try:
        lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
        return lines[-n:]
    except OSError:
        return []


def is_musician(cwd, session_id=None):
    _, st = _read_state(cwd, session_id)
    return bool(st and st.get("active"))


def _label(st):
    """The lifecycle label, derived (there is no stored status field)."""
    if not st.get("active"):
        return st.get("outcome") or "closed"
    if st.get("awaiting"):
        return "suspended"
    if st.get("phase") == "shaping":
        return "shaping"
    return "working"


def _task_progress(st):
    tasks = st.get("tasks") or []
    done = sum(1 for t in tasks if t.get("status") == "completed")
    return done, len(tasks)


def _current_task(st):
    """The subject of the task being worked (in_progress, else the next pending)."""
    tasks = st.get("tasks") or []
    for want in ("in_progress", "pending"):
        for t in tasks:
            if t.get("status") == want:
                return t.get("subject")
    return None


def task_progress(cwd, session_id=None):
    """(completed, total) tasks for this session's run, or (None, None) if there is none."""
    _, st = _read_state(cwd, session_id)
    return _task_progress(st) if st else (None, None)


def musician_info(cwd, session_id=None):
    """The rich per-run picture for a running musician, or None if this isn't one."""
    rd, st = _read_state(cwd, session_id)
    if not st or not st.get("active"):
        return None
    done, total = _task_progress(st)
    return {
        "run_id": st.get("run_id"),
        "active": True,
        "status": _label(st),
        "entry": st.get("entry"),
        "input": st.get("input"),
        "done": done,
        "total": total,
        "current": _current_task(st),
        "awaiting": st.get("awaiting"),
        "ultracode": bool(st.get("ultracode")),
        "started_at": st.get("started_at"),
        "last_action": (_tail(rd / "live.log", 1) or [None])[0],
    }


def live_tail(cwd, session_id=None, n=20):
    """The last n lines of the run's live action feed — what the musician is doing now."""
    rd = _resolve_run_dir(cwd, session_id)
    return _tail(rd / "live.log", n) if rd else []


def cancel_run(cwd, session_id=None):
    """Cancel this session's active musician run the way /musician-cancel does: mark its
    state.json active:false / outcome:cancelled and drop the by-session pointer so the Stop
    hook stops re-feeding. The run folder stays as the durable record. Returns the run dir on
    success, or None if there was no active run to cancel."""
    rd = _resolve_run_dir(cwd, session_id)
    if not rd:
        return None
    st_path = rd / "state.json"
    try:
        st = json.loads(st_path.read_text())
    except (json.JSONDecodeError, OSError):
        st = {}
    st.update(active=False, outcome="cancelled")
    tmp = st_path.with_name(st_path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(st, indent=2))
        os.replace(tmp, st_path)
    except OSError:
        return None
    if session_id:
        try:
            (_musician_dir(cwd) / "by-session" / session_id).unlink()
        except OSError:
            pass
    return rd
