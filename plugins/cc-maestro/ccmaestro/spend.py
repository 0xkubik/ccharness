"""--spend-weekly supervisor.

cc-agent owns the in-loop `--spend-session` flag (never self-stop; generate work instead of
idling). It lives in ONE session, so it dies when the 5-hour subscription window is exhausted.
This module is the cc-maestro half: it RELAUNCHES a `claude -p "/autopilot --spend-session"`
session each time it dies, spanning the 5-hour resets until a 7-day (weekly) wall-clock horizon —
turning "spend the session" into "spend the week".

A running session cannot read its own remaining subscription budget, and the reset timestamp is
exposed only to a status-line script (never to headless `claude -p`). So the supervisor does NOT
try to detect the limit. It classifies WHY the session died from two fully-knowable signals:

  - is `autopilot/state.json` still active?  gone/inactive => the user ran /autopilot-cancel => STOP
  - did it run a while then die, or die fast? sustained => presumed limit (relaunch after a blind
    probe wait); fast => crash (exponential backoff, give up after K consecutive fast deaths)

`spend_verdict` and `next_wait_s` are pure (no I/O), mirroring `watchdog.verdict`, so the safety
logic is unit-tested in isolation; `run_spend_weekly` is a thin side-effecting wrapper.
"""
import json
from pathlib import Path

# --- pure core (unit-tested in test_spend.py) -------------------------------------------------

def spend_verdict(*, state_active, run_duration_s, fast_death_streak, elapsed_total_s, config):
    """Decide what to do after a launched spend-session session has died.

    Returns {"action": one of STOP|RELAUNCH|BACKOFF|GIVE_UP, "reason": str}.
    Precedence: cancel (safety) > weekly horizon > death classification.
    """
    if not state_active:
        return {"action": "STOP", "reason": "autopilot inactive — /autopilot-cancel (the manual brake)"}
    if elapsed_total_s >= config["horizon_s"]:
        days = config["horizon_s"] / 86400.0
        return {"action": "STOP", "reason": f"weekly horizon reached ({days:.0f}d wall clock)"}
    if run_duration_s < config["fast_death_s"]:
        # too brief to have done real work -> a crash, not a limit hit
        if fast_death_streak + 1 >= config["max_fast_deaths"]:
            return {"action": "GIVE_UP",
                    "reason": f"{fast_death_streak + 1} consecutive fast deaths (<{config['fast_death_s']}s) — loop looks broken"}
        return {"action": "BACKOFF", "reason": f"fast death (<{config['fast_death_s']}s) — backing off, will retry"}
    # ran a sustained stretch then died -> presume the subscription window was exhausted
    return {"action": "RELAUNCH", "reason": "sustained run then died — presumed subscription limit; relaunch after wait"}


def next_wait_s(action, fast_death_streak, config):
    """Seconds to sleep before the next launch (0 for terminal actions)."""
    if action == "RELAUNCH":
        # blind probe interval: we can't read the reset time, so we re-probe periodically. If the
        # window hasn't reset the relaunch dies fast and the crash backoff takes over and climbs.
        return config["limit_wait_s"]
    if action == "BACKOFF":
        return min(config["crash_base_s"] * (2 ** fast_death_streak), config["crash_max_s"])
    return 0  # STOP / GIVE_UP


# --- side-effecting wrapper -------------------------------------------------------------------

def autopilot_state_active(repo):
    """True iff repo's autopilot/state.json exists and active:true (false => cancelled/absent)."""
    f = Path(repo) / ".claude" / "ccharness" / "autopilot" / "state.json"
    if not f.exists():
        return False
    try:
        return bool(json.loads(f.read_text()).get("active"))
    except (json.JSONDecodeError, OSError):
        return False


def spend_config(cfg):
    """Pull the spend-weekly knobs out of the loaded ccmaestro config (with defaults)."""
    return {
        "fast_death_s":   cfg.get("spend_fast_death_s", 120),
        "max_fast_deaths": cfg.get("spend_max_fast_deaths", 4),
        "horizon_s":      cfg.get("spend_horizon_s", 7 * 24 * 3600),
        "limit_wait_s":   cfg.get("spend_limit_wait_s", 1800),
        "crash_base_s":   cfg.get("spend_crash_base_s", 60),
        "crash_max_s":    cfg.get("spend_crash_max_s", 900),
    }


def run_spend_weekly(task, *, repo, model=None, yolo=False, horizon_days=None,
                     log=print, _launch=None, _now=None, _sleep=None):
    """Relaunch /autopilot --spend-session across 5-hour resets until the weekly horizon.

    Side effects are injectable (_launch/_now/_sleep) so the loop can be exercised in tests; in
    production they default to a real synchronous `claude -p` launch, monotonic clock, and sleep.
    `_launch(argv, repo) -> exit_code` must block until the session exits.
    """
    import os, time, subprocess
    from . import config, launcher

    cfg = config.load_config()
    sc = spend_config(cfg)
    if horizon_days is not None:
        sc["horizon_s"] = int(horizon_days * 86400)

    now = _now or time.monotonic
    sleep = _sleep or time.sleep

    def _default_launch(argv, cwd):
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                                start_new_session=True)
        return proc.wait()
    launch = _launch or _default_launch

    import uuid
    repo = repo or os.getcwd()
    started = now()
    fast_death_streak = 0
    launches = 0

    while True:
        # Fresh session id each relaunch so the autopilot skill re-arms cleanly — a dead
        # session's id must never be reused.
        argv = launcher.build_launch_argv(str(uuid.uuid4()), task, model=model, yolo=yolo)
        launches += 1
        log(f"[spend-weekly] launch #{launches}: {task}")
        t0 = now()
        try:
            code = launch(argv, repo)
        except Exception as e:  # a launch that can't even start is a fast death
            code = -1
            log(f"[spend-weekly] launch error: {e}")
        run_duration_s = now() - t0
        state_active = autopilot_state_active(repo)
        v = spend_verdict(state_active=state_active, run_duration_s=run_duration_s,
                          fast_death_streak=fast_death_streak, elapsed_total_s=now() - started, config=sc)
        log(f"[spend-weekly] session #{launches} ended (exit {code}, ran {run_duration_s/60:.1f}m) "
            f"-> {v['action']}: {v['reason']}")

        if v["action"] in ("STOP", "GIVE_UP"):
            log(f"[spend-weekly] stopping after {launches} launch(es): {v['reason']}")
            return {"launches": launches, "final": v}

        wait = next_wait_s(v["action"], fast_death_streak, sc)
        fast_death_streak = fast_death_streak + 1 if v["action"] == "BACKOFF" else 0
        if wait:
            log(f"[spend-weekly] sleeping {wait}s before relaunch")
            sleep(wait)
