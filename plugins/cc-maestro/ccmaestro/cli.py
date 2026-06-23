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

def build_parser():
    p = argparse.ArgumentParser(prog="ccmaestro", description="Watch and control Claude Code agents.")
    sub = p.add_subparsers(dest="cmd")
    ls = sub.add_parser("ls", help="list all agents with tokens + watchdog verdict")
    ls.add_argument("--json", action="store_true", help="machine-readable output")
    ls.set_defaults(func=_ls)
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 2
    return args.func(args)
