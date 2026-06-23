import json, os, shlex, subprocess, uuid
from datetime import datetime, timezone
from . import paths

# Curated safe Bash subset for unattended-but-restricted runs (acceptEdits handles file edits).
DEFAULT_ALLOWED_TOOLS = "Read,Edit,Write,Glob,Grep,Bash(git status),Bash(git diff:*),Bash(git log:*),Bash(ls:*),Bash(cat:*)"

def build_spawn_command(argv, result_path):
    inner = shlex.join(argv)
    rp = shlex.quote(str(result_path))
    return ["sh", "-c", f'{inner}; ec=$?; printf \'{{"exit": %s}}\' "$ec" > {rp}']

def build_resume_argv(session_id, message, *, model=None, budget=None, yolo=False):
    argv = ["claude", "--resume", session_id, "-p", message,
            "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    if yolo:
        argv += ["--permission-mode", "bypassPermissions"]
    else:
        argv += ["--permission-mode", "acceptEdits", "--allowedTools", DEFAULT_ALLOWED_TOOLS]
    if model:
        argv += ["--model", model]
    if budget is not None:
        argv += ["--max-budget-usd", str(budget)]
    return argv

def build_launch_argv(session_id, task, *, model=None, budget=None, yolo=False):
    argv = ["claude", "-p", task,
            "--session-id", session_id,
            "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    if yolo:
        argv += ["--permission-mode", "bypassPermissions"]
    else:
        argv += ["--permission-mode", "acceptEdits", "--allowedTools", DEFAULT_ALLOWED_TOOLS]
    if model:
        argv += ["--model", model]
    if budget is not None:
        argv += ["--max-budget-usd", str(budget)]
    return argv

def start(task, *, repo=None, model=None, budget=None, name=None, yolo=False):
    paths.ensure_state_dir()
    session_id = str(uuid.uuid4())
    agent_id = session_id[:8]
    cwd = repo or os.getcwd()
    argv = build_launch_argv(session_id, task, model=model, budget=budget, yolo=yolo)
    adir = paths.agent_dir(agent_id)
    adir.mkdir(parents=True, exist_ok=True)
    meta = {"agent_id": agent_id, "sessionId": session_id, "task": name or task, "repo": cwd,
            "model": model, "budget": budget, "yolo": yolo, "kind": "task",
            "started_at": datetime.now(timezone.utc).isoformat()}
    paths.atomic_write(adir / "meta.json", json.dumps(meta, indent=2))
    result_path = adir / "result.json"
    log = open(adir / "stream.log", "w")
    proc = subprocess.Popen(build_spawn_command(argv, result_path), cwd=cwd,
                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    log.close()
    meta["pid"] = proc.pid
    paths.atomic_write(adir / "meta.json", json.dumps(meta, indent=2))
    return agent_id
