import argparse, json, sys
from datetime import datetime, timezone
from . import config, registry, transcript, paths, render, control, report

def _ls(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    rows.sort(key=lambda r: (r["verdict"] == "ok", r["id"]))  # problems first
    print(render.render_json(rows) if args.json else render.render_table(rows, now))
    return 0

def _start(args):
    from . import launcher
    try:
        agent_id = launcher.start(args.task, repo=args.repo, model=args.model,
                                  budget=args.budget, name=args.name, yolo=args.yolo)
    except launcher.FleetFull as e:
        print(str(e), file=sys.stderr); return 1
    print(agent_id); return 0

def _logs(args):
    from . import paths, registry
    meta = registry.load_meta_records().get(args.id)
    sid = meta.get("sessionId") if meta else args.id
    tp = paths.find_transcript(sid)
    if not tp:
        print(f"no transcript found for {args.id}", file=sys.stderr)
        return 1
    lines = tp.read_text().splitlines()
    for line in lines[-args.tail:] if args.tail > 0 else []:
        print(line)
    return 0

def _stop(args):
    info = control.resolve(args.id)
    if not info:
        print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, detail = control.stop_agent(info)
    print(f"{args.id}: {result}" + (f" ({detail})" if detail else ""))
    return 0 if result in ("stopped", "musician-cancelled") else 1

def _steer(args):
    info = control.resolve(args.id)
    if not info:
        print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, detail = control.steer_agent(info, args.message)
    print(f"{args.id}: {result}" + (f" ({detail})" if detail else ""))
    return 0 if result == "steered" else 1

def _check(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    cur = report.snapshot(rows)
    snap_file = config.STATE_DIR / "last_snapshot.json"
    prev = {}
    if snap_file.exists():
        try: prev = json.loads(snap_file.read_text())
        except (json.JSONDecodeError, OSError): prev = {}
    events = report.diff(prev, cur)
    for e in events:
        report.record(e)
        if args.notify and cfg.get("report_endpoint"):
            report.post(cfg["report_endpoint"], e)
    paths.atomic_write(snap_file, json.dumps(cur))
    print(json.dumps(events, indent=2) if args.json else f"{len(events)} new event(s)")
    return 0

def _musician(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    musicians = [r for r in rows if r.get("musician")]
    if args.id:
        musicians = [r for r in musicians
                     if r["id"].startswith(args.id) or (r["sessionId"] or "").startswith(args.id)]
        if not musicians:
            print(f"no musician matching {args.id}", file=sys.stderr)
            return 1
    if args.json:
        print(render.render_json(musicians))
    elif args.id:
        print(render.render_musician_detail(musicians[0], now))
    else:
        print(render.render_musician_list(musicians, now))
    return 0

def _pause(args):
    info = control.resolve(args.id)
    if not info: print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, _ = control.pause_agent(info); print(f"{args.id}: {result}"); return 0 if result == "paused" else 1

def _resume(args):
    info = control.resolve(args.id)
    if not info: print(f"no agent matching {args.id}", file=sys.stderr); return 1
    result, _ = control.resume_agent(info); print(f"{args.id}: {result}"); return 0 if result == "resumed" else 1

def build_parser():
    p = argparse.ArgumentParser(prog="ccconductorctl", description="Watch and control Claude Code agents.")
    sub = p.add_subparsers(dest="cmd")
    ls = sub.add_parser("ls", help="list all agents with tokens + watchdog verdict")
    ls.add_argument("--json", action="store_true", help="machine-readable output")
    ls.set_defaults(func=_ls)
    st = sub.add_parser("start", help="launch a new managed agent")
    st.add_argument("task")
    st.add_argument("--repo"); st.add_argument("--model"); st.add_argument("--name")
    st.add_argument("--budget", type=float)
    st.add_argument("--yolo", action="store_true", help="bypass ALL permissions (unattended, dangerous)")
    st.set_defaults(func=_start)
    lg = sub.add_parser("logs", help="print an agent's recent transcript lines")
    lg.add_argument("id")
    lg.add_argument("--tail", type=int, default=40)
    lg.set_defaults(func=_logs)
    mu = sub.add_parser("musician", help="rich view of running musicians (status, goal, live feed)")
    mu.add_argument("id", nargs="?", help="a musician id / sessionId prefix; omit to list all")
    mu.add_argument("--json", action="store_true", help="machine-readable output")
    mu.set_defaults(func=_musician)
    sp = sub.add_parser("stop", help="stop an agent (musician -> graceful cancel)")
    sp.add_argument("id")
    sp.set_defaults(func=_stop)
    se = sub.add_parser("steer", help="stop an agent and resume it with a new instruction")
    se.add_argument("id"); se.add_argument("message"); se.set_defaults(func=_steer)
    pa = sub.add_parser("pause", help="pause an agent (SIGSTOP)"); pa.add_argument("id"); pa.set_defaults(func=_pause)
    re_ = sub.add_parser("resume", help="resume a paused agent (SIGCONT)"); re_.add_argument("id"); re_.set_defaults(func=_resume)
    ck = sub.add_parser("check", help="detect agent state changes; record + optionally notify")
    ck.add_argument("--notify", action="store_true", help="POST new events to report_endpoint")
    ck.add_argument("--json", action="store_true")
    ck.set_defaults(func=_check)
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 2
    return args.func(args)
