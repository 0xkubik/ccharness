def looping(tool_calls, loop_n, window):
    recent = tool_calls[-window:] if window else tool_calls
    if len(recent) < loop_n:
        return None
    last = recent[-1]
    count = 0
    for sig in reversed(recent):
        if sig == last:
            count += 1
        else:
            break
    if count >= loop_n:
        return f"same tool call x{count}: {last[0]}"
    return None

def verdict(summary, entry, config, now):
    if entry.get("launched_by_ccmaestro") and entry.get("native") is None:
        ec = entry.get("completed_exit")
        if ec == 0:
            return {"status": "done", "reason": "completed (exit 0)"}
        if ec is not None:
            return {"status": "crashed", "reason": f"exit {ec}"}
        return {"status": "died", "reason": "gone from the agents registry"}
    loop = looping(summary.get("tool_calls", []), config["loop_n"], config["loop_window"])
    if loop:
        return {"status": "looping", "reason": loop}
    budget = config.get("token_budget") or 0
    if budget > 0 and summary.get("total_tokens", 0) > budget:
        return {"status": "over-budget", "reason": f"{summary['total_tokens']} tokens > {budget}"}
    la = summary.get("last_activity")
    if la is not None:
        idle_min = (now - la).total_seconds() / 60.0
        if entry.get("is_autopilot"):
            limit = config["autopilot_stall_min"]
            kind = "no new cycle"
        elif summary.get("pending_tool"):
            limit = config["tool_stall_min"]
            kind = "on a tool"
        else:
            limit = config["stall_min"]
            kind = "idle"
        if idle_min > limit:
            return {"status": "stalled", "reason": f"no activity {idle_min:.0f}m ({kind}, limit {limit}m)"}
    return {"status": "ok", "reason": ""}
