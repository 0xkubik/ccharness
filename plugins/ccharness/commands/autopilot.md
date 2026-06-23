---
description: "Run the ccharness funnel autonomously in a continuous loop — point-it → grill-it → implement-it, one committed improvement per cycle, re-surveying as it goes. Never stops on its own; only /autopilot-cancel stops it. Needs a North Star (run /point-it once first)."
argument-hint: "[optional focus — a theme to scope each survey]"
---

Invoke the `autopilot` skill to **arm and run** the never-stop funnel loop, with this focus:

> $ARGUMENTS

autopilot fuses the funnel (point-it → grill-it → implement-it, with slap) into one continuous
loop: each cycle auto-picks the top direction toward the product's **North Star**, decides *how*,
builds it to a **local commit**, then re-surveys and goes again. It **converts the funnel's
human-handbacks into skip-and-log** — an unresolvable or twice-slapped task is written to a review
queue and skipped, never waited on.

**It cannot stop on its own.** A `Stop` hook re-feeds the loop every turn; the only way it ends is
you running **`/autopilot-cancel`** (you can also interrupt at any time to redirect). On its first
run it **refuses to arm without a North Star** — run `/point-it` once to set one, then `/autopilot`.
