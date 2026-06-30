import json, subprocess
from . import config

def _run_claude_agents():
    return subprocess.run(
        ["claude", "agents", "--json", "--all"],
        capture_output=True, text=True, timeout=30, check=True,
    ).stdout

def native_agents(runner=None):
    runner = runner or _run_claude_agents
    try:
        data = json.loads(runner())
        return data if isinstance(data, list) else []
    except (subprocess.SubprocessError, OSError, ValueError):
        return []

def load_meta_records():
    records = {}
    adir = config.STATE_DIR / "agents"
    if not adir.exists():
        return records
    for d in adir.iterdir():
        f = d / "meta.json"
        if f.exists():
            try:
                records[d.name] = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                pass
    return records

def merge(native, meta_records):
    by_sid = {}
    for a in native:
        sid = a.get("sessionId")
        if sid:
            by_sid[sid] = {"sessionId": sid, "native": a, "meta": None, "launched_by_ccconductorctl": False}
    for aid, m in meta_records.items():
        sid = m.get("sessionId") or aid
        entry = by_sid.get(sid)
        if entry:
            entry["meta"] = m
            entry["launched_by_ccconductorctl"] = True
        else:
            by_sid[sid] = {"sessionId": sid, "native": None, "meta": m, "launched_by_ccconductorctl": True}
    return list(by_sid.values())
