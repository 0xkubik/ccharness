import json
from datetime import datetime, timezone
from . import watchdog, musician as mus, paths

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
        minfo = mus.musician_info(cwd, sid)
        is_mus = minfo is not None
        v = watchdog.verdict(summary, {**e, "is_musician": is_mus, "completed_exit": _completed_exit(meta)}, config, now)
        rows.append({
            "id": (sid or "")[:8],
            "sessionId": sid,
            "kind": "musician" if is_mus else (meta.get("kind") or native.get("kind") or "?"),
            "status": native.get("status") or native.get("state") or ("gone" if native == {} else "?"),
            "tokens": summary.get("total_tokens", 0),
            "last_activity": summary.get("last_activity"),
            "verdict": v["status"],
            "reason": v["reason"],
            "cwd": cwd,
            "name": meta.get("task") or native.get("name") or "",
            "musician": minfo,
            "cycles": minfo["cycle"] if is_mus else None,
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
        m = r.get("musician")
        if m:
            act = m.get("last_action") or "(starting)"
            goal = m.get("done_when") or "(forging done-contract)"
            lines.append(f"{'':8} ▸ cycle {m.get('cycle')} · {m.get('status')} · {act}")
            lines.append(f"{'':8}   goal: {goal[:60]}")
    return "\n".join(lines)


def render_musician_list(rows, now=None):
    if not rows:
        return "No active musicians."
    out = [f"MUSICIANS ({len(rows)})"]
    for r in rows:
        m = r["musician"]
        out.append("{id:8} cycle {cyc} · {status} · {act}".format(
            id=r["id"], cyc=m.get("cycle"), status=m.get("status") or "?",
            act=(m.get("last_action") or "(starting)")))
        out.append(f"         asked: {(m.get('input') or '(open mode)')[:72]}")
        if m.get("done_when"):
            out.append(f"         goal:  {m['done_when'][:72]}")
    return "\n".join(out)


def render_musician_detail(row, now=None):
    m = row["musician"]
    extra = ""
    if m.get("ultracode"):
        extra += ", ultracode"
    if m.get("awaiting"):
        extra += ", awaiting (suspended)"
    lines = [
        f"musician {row['id']}  ({row.get('cwd') or '?'})",
        f"  run_id   {m.get('run_id')}",
        f"  status   {m.get('status')}  (cycle {m.get('cycle')}{extra})",
        f"  entry    {m.get('entry')}",
        f"  asked    {m.get('input') or '(open mode — found its own direction)'}",
        f"  goal     {m.get('done_when') or '(not forged yet)'}",
        f"  blocked  {m.get('blocked_count')} handed back",
        f"  verdict  {row.get('verdict')}" + (f" — {row['reason']}" if row.get("reason") else ""),
    ]
    tail = mus.live_tail(row.get("cwd"), row.get("sessionId"), 20)
    lines.append(f"  live feed (last {len(tail)}):" if tail else "  live feed: (none yet)")
    lines += [f"    {t}" for t in tail]
    return "\n".join(lines)
