import os
from . import registry, autopilot as ap

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
                "is_autopilot": ap.is_autopilot(cwd),
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
