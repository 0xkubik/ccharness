import os, signal
from pathlib import Path
from . import registry, musician as mus

def resolve(ident, *, native_runner=None):
    entries = registry.merge(registry.native_agents(runner=native_runner), registry.load_meta_records())
    for e in entries:
        sid = e.get("sessionId") or ""
        meta = e.get("meta") or {}
        native = e.get("native") or {}
        aid = meta.get("agent_id") or (sid[:8] if sid else None)
        if ident == sid or (aid and ident == aid) or (sid and sid.startswith(ident)):
            cwd = native.get("cwd") or meta.get("repo")
            pid = meta.get("pid") or native.get("pid")
            return {
                "agent_id": aid, "sessionId": sid or None, "pid": pid, "cwd": cwd,
                "is_musician": mus.is_musician(cwd),
                "native": e.get("native"), "meta": meta or None,
                "launched_by_ccmaestro": e.get("launched_by_ccmaestro", False),
            }
    return None

def send_signal(pid, sig, sender=os.killpg):
    if not pid:
        return False
    try:
        sender(int(pid), sig)
        return True
    except (ProcessLookupError, PermissionError, OSError, ValueError):
        return False

def stop_agent(info, *, sender=os.killpg):
    if info.get("is_musician"):
        # The musician is a single bounded, self-closing loop — graceful cancel just
        # removes its own state file so the Stop hook stops re-feeding it.
        f = Path(info["cwd"]) / ".claude" / "ccharness" / "musician" / "state.json"
        try:
            f.unlink()
        except FileNotFoundError:
            return ("musician-cancelled", "state already gone")
        except OSError as e:
            return ("not-found", str(e))
        return ("musician-cancelled", str(f))
    pid = info.get("pid")
    if not pid:
        return ("no-pid", "no recorded pid")
    # NOTE: a SIGTERM'd agent reads back as "died" in ls — the sh wrapper is killed
    # before it can write result.json, so there's no exit-code marker. That's expected
    # for an operator-stopped agent (the process is genuinely gone), not a bug.
    if send_signal(pid, signal.SIGTERM, sender=sender):
        return ("stopped", str(pid))
    return ("not-found", "signal failed (process gone?)")

def pause_agent(info, *, sender=os.killpg):
    return ("paused", str(info.get("pid"))) if send_signal(info.get("pid"), signal.SIGSTOP, sender=sender) else ("no-pid", "")

def resume_agent(info, *, sender=os.killpg):
    return ("resumed", str(info.get("pid"))) if send_signal(info.get("pid"), signal.SIGCONT, sender=sender) else ("no-pid", "")

def steer_agent(info, message, *, sender=os.killpg, spawn=None):
    if info.get("is_musician"):
        return ("refused-musician", "redirect a musician via its own funnel / /musician-cancel, not steer")
    sid = info.get("sessionId")
    if not sid:
        return ("no-session", "no sessionId to resume")
    send_signal(info.get("pid"), signal.SIGTERM, sender=sender)  # stop the live run first
    from . import launcher
    meta = info.get("meta") or {}
    argv = launcher.build_resume_argv(sid, message, model=meta.get("model"),
                                      budget=meta.get("budget"), yolo=meta.get("yolo", False))
    spawn = spawn or launcher.spawn_resume
    pid = spawn(argv, info.get("cwd"))
    return ("steered", str(pid))
