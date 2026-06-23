import json
from datetime import datetime, timezone
from . import watchdog, autopilot as ap, paths

def _completed_exit(meta):
    if not meta or not meta.get("agent_id"):
        return None
    f = paths.agent_dir(meta["agent_id"]) / "result.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text()).get("exit")
    except (json.JSONDecodeError, OSError):
        return None

def _humanize_age(last, now):
    if last is None:
        return "-"
    secs = (now - last).total_seconds()
    if secs < 90:
        return f"{int(secs)}s"
    if secs < 5400:
        return f"{int(secs // 60)}m"
    return f"{int(secs // 3600)}h"

def _fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n//1000}k"
    return str(n)

def build_rows(entries, now, *, summarizer, config):
    rows = []
    for e in entries:
        native = e.get("native") or {}
        meta = e.get("meta") or {}
        sid = e.get("sessionId")
        cwd = native.get("cwd") or meta.get("repo")
        summary = summarizer(sid)
        is_ap = ap.is_autopilot(cwd)
        v = watchdog.verdict(summary, {**e, "is_autopilot": is_ap, "completed_exit": _completed_exit(meta)}, config, now)
        rows.append({
            "id": (sid or "")[:8],
            "sessionId": sid,
            "kind": "autopilot" if is_ap else (meta.get("kind") or native.get("kind") or "?"),
            "status": native.get("status") or native.get("state") or ("gone" if native == {} else "?"),
            "tokens": summary.get("total_tokens", 0),
            "last_activity": summary.get("last_activity"),
            "verdict": v["status"],
            "reason": v["reason"],
            "cwd": cwd,
            "name": meta.get("task") or native.get("name") or "",
            "autopilot": is_ap,
            "cycles": ap.cycle_count(cwd) if is_ap else None,
        })
    return rows

def render_json(rows):
    def default(o):
        return o.isoformat() if hasattr(o, "isoformat") else str(o)
    return json.dumps(rows, default=default, indent=2)

def render_table(rows, now=None):
    now = now or datetime.now(timezone.utc)
    header = f"{'ID':8} {'KIND':10} {'STATUS':7} {'TOKENS':>7} {'LAST':>5}  {'VERDICT':10} NAME"
    lines = [header]
    for r in rows:
        lines.append("{id:8} {kind:10} {status:7} {tok:>7} {age:>5}  {verdict:10} {name}".format(
            id=r["id"], kind=str(r["kind"])[:10], status=str(r.get("status", ""))[:7],
            tok=_fmt_tokens(r["tokens"]), age=_humanize_age(r["last_activity"], now),
            verdict=r["verdict"], name=(r["name"] or "")[:40]))
        if r["verdict"] != "ok" and r["reason"]:
            lines.append(f"{'':8} └─ {r['reason']}")
    return "\n".join(lines)
