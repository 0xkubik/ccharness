import argparse, sys
from datetime import datetime, timezone
from . import config, registry, transcript, paths, render

def _ls(args):
    cfg = config.load_config()
    now = datetime.now(timezone.utc)
    entries = registry.merge(registry.native_agents(), registry.load_meta_records())
    summarizer = lambda sid: transcript.parse_transcript(paths.transcript_path(sid)) if sid else transcript.parse_transcript(None)
    rows = render.build_rows(entries, now, summarizer=summarizer, config=cfg)
    rows.sort(key=lambda r: (r["verdict"] == "ok", r["id"]))  # problems first
    print(render.render_json(rows) if args.json else render.render_table(rows))
    return 0

def _start(args):
    from . import launcher
    agent_id = launcher.start(args.task, repo=args.repo, model=args.model,
                              budget=args.budget, name=args.name, yolo=args.yolo)
    print(agent_id)
    return 0

def _logs(args):
    from . import paths, registry
    meta = registry.load_meta_records().get(args.id)
    sid = meta.get("sessionId") if meta else args.id
    tp = paths.transcript_path(sid)
    if not tp:
        print(f"no transcript found for {args.id}", file=sys.stderr)
        return 1
    lines = tp.read_text().splitlines()
    for line in lines[-args.tail:]:
        print(line)
    return 0

def build_parser():
    p = argparse.ArgumentParser(prog="ccmaestro", description="Watch and control Claude Code agents.")
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
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 2
    return args.func(args)
