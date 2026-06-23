# Design: cc-maestro (agent console) + 3-layer plugin split

**Date:** 2026-06-23
**Status:** Draft for review

## Bottom line

The user wants to *watch and control* the coding agents this harness runs — from
two hands at once: themselves (by hand, in a separate terminal) and a separate
external agent called **hermes** (a non–Claude-Code agent at
`hermes-agent.nousresearch.com`). "Control" means: launch new agents, get a
report when they finish, and watch them live — how many tokens they burn, whether
they got stuck or are looping, and whether they quietly died.

Key finding from checking this machine: **Claude Code already does ~70% of this
natively.** So this is a *thin wrapper over existing primitives* plus one genuinely new piece (a stuck-detector), not a system built from scratch. Everything runs locally — there is no cross-machine networking requirement

Alongside the new console, the plugin layout is reshaped so the structure itself
shows the control hierarchy:

```
cc-maestro        (layer 3) — supervises MANY agents & autopilots (the new agent console)
      │ controls
cc-agent          (layer 2) — ONE self-driving agent (autopilot, extracted)
      │ uses
cc-tools          (layer 1) — single-purpose skills (chart-it / point-it / grill-it / implement-it / slap)
```

Control flows top-down; usage flows bottom-up. `cc-tools` is today's `ccharness`
plugin, renamed. `cc-agent` is the autopilot pulled out into its own plugin.
`cc-maestro` is the new build.

---

## 1. What already exists natively (verified on this machine, 2026-06-23)

These are confirmed by running the real CLI here — not from memory or the
(unreliable) doc dump.

- **A ccmaestro registry is built in.** `claude agents --json --all` prints a JSON
array of every session — both `kind: "background"` (dispatched agents) and
`kind: "interactive"` (normal sessions). For each: `sessionId`, `pid`
(interactive), `cwd`, `kind`, `state`/`status` (`idle` / `busy` / `blocked`),
`startedAt` (epoch ms), and `name`. Runs without a TTY, exits immediately.
**Verified (2026-06-23): a `claude -p` headless run DOES appear** — as
`kind: "interactive"` with a `pid` and its `sessionId` — so the agents `ccmaestro start` launches are natively visible. Caveat also verified: a live `-p` run has
**no `status` field** (idle/busy is absent while it runs), so liveness/activity
for ccmaestro-launched agents must come from `pid` + transcript growth, not from
native status. **Therefore: ccmaestro keeps its own launch record (pid + sessionId +
metadata) as the authoritative source for what it spawned, and treats `claude agents --json` as the supplementary view for externally-started sessions.** It is
NOT a custom *process* registry (we never track PIDs we didn't launch) — it is a
record of ccmaestro's own launches merged with the native list.
- **Per-agent token usage is in the transcript.** Each session writes
`~/.claude/projects/<cwd-with-slashes-as-dashes>/<sessionId>.jsonl`. The path is
the working directory with `/` → `-` (NOT an md5 hash — the doc dump was wrong).
Every assistant entry carries a `usage` block:
`input_tokens`, `output_tokens`, `cache_creation_input_tokens`,
`cache_read_input_tokens`. So counting an agent's tokens = read its file and sum.
No telemetry collector, no stream interception needed.
- **Control primitives exist:** `pid` → OS signal (stop/pause); `sessionId` →
`claude --resume <id>` (optionally `--fork-session`) to re-task; `--max-budget-usd`
→ hard spend cap at launch; `--remote-control [name]` → a native external-control
mode (candidate for live steering — to be spiked, not assumed).
- **Launch flags (verified):** `-p/--print`, `--output-format text|json|stream-json`,
`--input-format text|stream-json`, `--include-partial-messages`,
`--include-hook-events`, `--session-id <uuid>`, `--name`, `--permission-mode`,
`--no-session-persistence`, `--max-budget-usd` (print only), `--fork-session`.

What is **not** native, and must be built:

1. **Stuck / loop / silent-death detection** — native `state` gives idle/busy/blocked,
  but not "busy-but-looping", "idle-but-should-be-working", or "process gone, task
   not done". This is the one real piece of new logic.
2. **A unified set of verbs both a human and hermes use** over those primitives.
3. **Proactive reporting** ("tell me when it's done/stuck") and an all-agents token
  roll-up.
4. **Autopilot-awareness** — the never-stop loop has a different "done" and a
  different "stop".

---

## 2. Approach (decided): thin wrapper, no daemon

Chosen over an always-on supervisor daemon because everything is local and the
native registry already exists — a daemon would duplicate it and add a process to
keep alive. The shared truth both controllers read is the same: `claude agents --json` + the transcript files + ccmaestro's own launch records (merged by `sessionId`,
see 3.4). Both controllers call the same verbs against the same data, so "hybrid
co-management" is automatic — neither party keeps a private list the other can't see.

**Load-bearing rule:** both the human and hermes launch agents **through `ccmaestro`,
not raw `claude`**. An agent started in another way is invisible to the registry's
extra metadata and harder for the other party to manage. (Raw interactive sessions
still appear in `claude agents --json`, so they are *visible*; they just lack the
ccmaestro's launch metadata and clean control hooks.)

If true live mid-turn steering of *another controller's* agent ever becomes
essential, that is the trigger to grow into a small daemon — explicitly out of
scope now.

---

## 3. cc-maestro (the agent console) — design

`cc-maestro` ships **two things**:

- a **standalone CLI** (`ccmaestro`) — the real interface, runnable *outside* a Claude
Code session, used by the human in a terminal and by hermes by shelling out;
- a **thin plugin layer** (slash commands + the reporting/watchdog hook wiring) —
convenience wrappers for when you are *inside* a Claude Code session.

The CLI is primary because hermes is not Claude Code and the human wants a separate
terminal — neither can use slash commands. Slash commands just call the same CLI.

**Language:** Python 3, standard library only (`json`, `subprocess`, `pathlib`,
`os`, `signal`, `time`). Python is already present and is far better than bash for
JSON + transcript parsing + loop detection. The tiny reporting hook stays in bash
(`curl`). Zero third-party dependencies.

### 3.1 Components (each a focused unit)

**a) Registry view — `ccmaestro ls` / `ccmaestro ls --json*`*

- Calls `claude agents --json --all`.
- For each agent, locates its transcript, sums `usage` → tokens (in/out/cache),
reads the last entry's timestamp → "last activity".
- Attaches the watchdog verdict (3.1c).
- Tags autopilot agents (3.3).
- Human view: a table (id, kind, state, tokens, last-activity, verdict, cwd, name).
`--json`: the same as a machine-readable array for hermes.

**b) Launcher — `ccmaestro start "<task>" [--repo PATH] [--budget USD] [--model M] [--name N] [--autopilot] [--yolo]`**

- Generates a `sessionId`, launches `claude -p --output-format stream-json --include-partial-messages --session-id <id> [--max-budget-usd ...] [--model ...]`
in the target repo, tees the stream to `ccmaestro/<id>/stream.log`, records launch
metadata (3.4), and returns the id.
- **Permission posture (must be set, or the agent hangs).** A headless `-p` agent
with no TTY cannot answer a permission prompt — on the first Edit/Bash it would
block forever, and the watchdog would mis-flag it "stalled". So `ccmaestro start` must
pass a permission mode. **Default: `acceptEdits` plus a curated `--allowedTools`
allowlist** for the common safe Bash subset (read-only git, build, test) — enough
to do real work without a prompt, while still refusing un-allowlisted dangerous
commands (a refusal ends the turn cleanly; it does not hang). Full
`--dangerously-skip-permissions` (`bypassPermissions`) is **opt-in only** via
`--yolo`. **Safety note:** an autonomous hermes spawning `--yolo` coding agents is
a loaded gun (unattended, unrestricted shell). Default stays restricted; `--yolo`
is a deliberate, logged choice. (Exact allowlist contents → open question 7a.4.)
- `--autopilot` launches a cc-agent autopilot run instead of a one-shot task and
tags it accordingly.
- One-shot `-p` runs give a clean final result message (cost, usage, exit code) the
wrapper records on completion.

**c) Watchdog — the one real new logic**

- Computed **on demand** when `ccmaestro ls` runs (no background process needed for the
pull path), and **optionally** on a schedule for proactive alerts (3.1d).
- Per agent, derives a verdict beyond native idle/busy/blocked:
  - **stalled** — alive/busy but transcript has no new line for > `STALL_MIN`
  (default 5 min). Refinement to limit false positives: if the last transcript
  entry is a `tool_use` still awaiting its result, treat as "long tool, not
  stalled" up to a higher threshold (a big build/test legitimately takes minutes).
  Verdict is "maybe stuck", tunable, never a hard kill on its own.
  - **looping** — in the last `M` tool calls, the same `(tool_name, normalized input)`
  repeats ≥ `LOOP_N` times (default 4). Normalize: same Bash command string, same
  edited file+string, etc.
  - **died** — was running, now absent from `claude agents --json` / PID gone, and no
  clean completion marker. For `ccmaestro start` one-shots the wrapper knows the exit
  code → distinguishes clean exit from crash.
  - **over-budget** — summed tokens (or `total_cost_usd` when captured) over a
  threshold. Tracked primarily in **tokens** (no model-pricing table needed); cost
  used when the final result message provides it.
- Thresholds live in one config file (3.4); all have sane defaults.
- Honesty requirement: the watchdog reports *suspicion with evidence* (e.g. "no
output for 9 min; last action was Edit ×5 on the same file"), not false certainty.

**d) Reporting — pull by default, push optional**

- **Pull (default):** hermes runs `ccmaestro ls --json` (or `claude agents --json`)
whenever it wants. Simplest, no moving parts, fits "everything local".
- **Push (optional):** a bash reporting hook on `Stop`, `SubagentStop`, and
`Notification` `curl`s a small JSON event to a configurable endpoint (hermes, or a
local file/log). Off unless an endpoint is configured. Multiple Stop hooks stack
(verified), so this coexists with cc-agent's re-feed hook on the same agent.
**Autopilot caveat:** an autopilot "stops" and gets re-fed every cycle, so a raw
`Stop` report would fire once per cycle (noisy). On autopilot agents the reporter
emits a *cycle-completed* event keyed off the new `log.jsonl` line (one per real
cycle), not the raw Stop — or suppresses Stop entirely and relies on the periodic
check. Decided per config; default is one event per real cycle.
- **Proactive stuck-alerts (optional):** a launchd timer runs `ccmaestro check --notify`
every N minutes; if any agent flips to stalled/looping/died/over-budget it fires
the same push event. This keeps the "no daemon" promise (a periodic timer, not a
resident service) while still alerting without being asked.

**e) Intervention**

- `**ccmaestro stop <id>`** — graceful: SIGTERM the pid (or the native stop path for
background agents); SIGKILL fallback. Autopilot agents stop via cancel, not raw
kill (3.3).
- `**ccmaestro steer <id> "<correction>"**` — re-task via `claude --resume <id> -p "<correction>"`. **On a still-running agent this is stop-then-resume, never
resume-alongside:** resuming a live session spawns a second process writing the
same transcript (two writers, corruption). So `steer` first stops the running
agent (3.1e stop), *then* resumes from its `sessionId` with the correction. (The
existence of `--fork-session` is the tell that reusing a live session id is
unsafe.) Covers ~90% of "redirect it"; truly-live injection without stopping is
deferred to the `--remote-control` spike.
- `**ccmaestro pause <id>` / `ccmaestro resume <id>`** — SIGSTOP / SIGCONT on the process
group for a crude immediate freeze; documented as blunt (freezes mid-call).
- **Live mid-turn steering** — a `--remote-control` spike is the path to true live
control; treated as **verify-first**, not promised in v1.

**f) Inspect — `ccmaestro logs <id> [--tail] [--follow]`**

- Streams/prints the agent's transcript (or the captured `stream.log`) for a human
to read or hermes to scrape.

### 3.2 The two front-ends, one core

```
  human terminal ─┐                        ┌─ claude agents --json   (native registry)
                  ├─►  ccmaestro (CLI)  ───────►├─ transcript .jsonl      (tokens, activity)
  hermes (shell) ─┘        │                ├─ os signals / claude --resume (control)
                           │                └─ ccmaestro/ state dir       (launch meta, verdicts)
  inside a CC session ─────┘ (slash-command wrappers call the same CLI)
```

### 3.3 Autopilot-awareness (cc-agent special case)

The autopilot loop is deliberately un-stoppable on its own (a Stop hook re-feeds
it; only `/autopilot-cancel` stops it). So the console treats it specially:

- **Detect:** an agent whose cwd has an armed autopilot state file
(`active: true`) is tagged `kind: autopilot`.
- **"Done"/progress:** not a process exit — it is a new line appended to the
autopilot `log.jsonl`. Stall = no new *cycle* for > `AUTOPILOT_STALL_MIN`.
- **"Stop":** `ccmaestro stop` on an autopilot runs the cancel path (set
`active: false` / remove state) *then* lets it end — a raw SIGTERM would leave
the loop armed.
- The blocked-task review queue (`blocked.jsonl`) surfaces in `ccmaestro ls` as a
count so the human/hermes sees skipped work.

### 3.4 State & files

A single gitignored dir holds only what is NOT already in native sources:

```
<repo>/.ccmaestro/                 (or ~/.ccmaestro/ for a global view — see open questions)
  agents/<id>/meta.json        launch metadata: task, repo, budget, model, pid, sessionId, startedAt, launchedBy(human|hermes)
  agents/<id>/stream.log       tee of the launch stream (one-shots)
  agents/<id>/result.json      final cost/usage/exit for completed one-shots
  config.json                  thresholds (STALL_MIN, LOOP_N, AUTOPILOT_STALL_MIN, budget caps), push endpoint
  events.jsonl                 append-only audit of ccmaestro actions (start/stop/steer/alerts)
```

Writes that two controllers may race on use atomic temp-file + rename (the same
pattern the autopilot already uses). Tokens and transcripts are **read from native
sources every time** — not cached here. The live list is ccmaestro's own launch records
(`agents/<id>/meta.json`) **merged by `sessionId`** with `claude agents --json`;
ccmaestro's records are authoritative for what it launched (it owns the pid), the native
list supplies externally-started sessions. Because the heavy data (tokens, activity)
is always re-read from transcripts, the views cannot drift.

---

## 4. cc-agent — autopilot extracted (layer 2)

Moves out of today's `ccharness` into its own plugin:

- commands: `autopilot`, `autopilot-cancel`
- skill: `autopilot`
- hook: `autopilot-stop.sh` + its `hooks.json` (the never-stop Stop hook travels
with the thing it serves — a cleaner separation than today)

Dependencies and ripples:

- The autopilot skill drives the funnel, so it calls the layer-1 skills by their
new namespace: `cc-tools:point-it`, `cc-tools:grill-it`, `cc-tools:implement-it`,
`cc-tools:chart-it`. Cross-plugin skill invocation by qualified name must be
verified to still work after the split.
- `ccharness-init` (the installer) must learn to install all three plugins.
- **Runtime state path stays stable.** The autopilot state lives under
`.claude/ccharness/autopilot/` today and is shared-namespace with chart-it/point-it
state. Recommendation: **do not move it** — the plugin rename is cosmetic; the
hidden, gitignored state dir can keep its path (or move once to a neutral
`.claude/cc/`). Moving it risks orphaning an in-flight loop for zero user-visible
gain. Decide in review (see open questions).

---

## 5. cc-tools — the renamed tools layer (layer 1)

Today's `ccharness` plugin minus autopilot: `chart-it`, `point-it`, `grill-it`,
`implement-it`, `slap`, and the installer.

**Rename ripple (measured in this repo, so the cost is known, not guessed):**

- 10 namespaced refs `ccharness:<skill>` across 4 SKILL files → become `cc-tools:<skill>`.
- `name` fields in `marketplace.json` and `plugins/*/.claude-plugin/plugin.json`.
- ~80 plain-word `ccharness` mentions across README + skill prose (historical spec
files under `docs/specs/` can be left as-is — they are dated records).
- The auto-memory index entry (`MEMORY.md`) and the pivot note go stale → update.

This is the **highest-churn, most error-prone** item. It is mechanical but touches
many files; it gets its own phase and its own verification (every skill still loads
and resolves cross-plugin). The user may, in review, choose to keep the directory/
namespace `ccharness` and only *relabel* it conceptually — that would cut most of
this churn. Flagged for the review gate.

---

## 6. Explicitly NOT building (YAGNI)

- No always-on supervisor daemon / HTTP server (native registry + files suffice locally).
- No OpenTelemetry collector / metrics backend (tokens are already in transcripts).
- No cross-machine networking, SSH/VPN transport (everything is local).
- No custom process registry (use `claude agents --json`).
- No model-pricing table in v1 (track tokens; use native cost when handed to us).

---

## 7. Risks & verify-first items

- `**--remote-control` reality** — spike before promising any live mid-turn steer;
it may be tied to Anthropic's cloud control rather than a local socket.
- `**claude agents --json` coverage** — RESOLVED (2026-06-23): `-p` one-shots DO
appear (`kind: interactive`, with pid + sessionId), but without a live `status`
field — so the launcher's own record + transcript activity, not native status,
drive liveness for ccmaestro-launched agents.
- **Stall false-positives** — long legit tool calls look stalled; the
pending-tool-result refinement + tunable thresholds + "maybe stuck" wording
mitigate, but tune against real runs.
- **Cross-plugin skill calls after the split** — verify `cc-tools:foo` resolves from
`cc-agent`.
- **Rename churn** — the largest source of breakage; isolated to its own phase.
- **Two writers racing** — atomic temp+rename on every `.ccmaestro/` write.

---

## 7a. Open questions for review (pick before implementation)

These are genuine forks left for the user to settle at the review gate:

1. **`ccmaestro` state dir location:** per-repo `<repo>/.ccmaestro/` vs global `~/.ccmaestro/`.
  **Recommendation: global `~/.ccmaestro/`** — the native registry (`claude agents --json --all`) is already machine-wide, hermes wants one machine-wide view, and agents run
   across many repos. Per-repo would fragment the view.
2. **Autopilot runtime state path:** keep `.claude/ccharness/autopilot/` as-is vs move
  to a neutral `.claude/cc/`. **Recommendation: keep as-is** (cosmetic plugin rename
   should not touch live state).
3. **Rename depth:** **DECIDED (2026-06-23): full rename** — `ccharness` → `cc-tools`
   everywhere (plugin directory, the `ccharness:` skill namespace, the installer,
   README, and the auto-memory index). The lighter "keep `ccharness` under the hood"
   option was rejected. This is the highest-churn step (Phase 0) and gets its own
   verification that every skill still loads and cross-plugin refs resolve.
4. **Default permission allowlist for `ccmaestro start`:** what exactly goes in the
  `acceptEdits` + `--allowedTools` safe set (e.g. `Read`, `Edit`, `Bash(git status)`,
   `Bash(git diff)`, build/test commands). Too tight → agents stall on safe work; too
   loose → unattended risk. Needs a concrete starter list.
5. **Global (all-agents) ceilings (the user's core fear is token burn):** per-agent
  `--max-budget-usd` is the per-agent half. Do we also want a **max-concurrent-agents**
   cap and/or a **global spend/token ceiling** that blocks new `ccmaestro start`s once
   crossed? Especially relevant since hermes is an autonomous launcher and some agents
   are never-stop autopilots. Recommendation: include at least a concurrency cap in v1.

## 8. Build sequence (one effort, ordered to contain risk)

Even though we do it all at once, ordering limits blast radius:

- **Phase 0 — rename** `ccharness` → `cc-tools` (cosmetic; verify everything loads
and cross-plugin refs resolve). Runtime state path left stable.
- **Phase 1 — extract** `cc-agent` (autopilot + cancel + Stop hook) into its own
plugin; update the installer; verify the never-stop loop still works end-to-end.
- **Phase 2 — `cc-maestro` core (observe):** `ccmaestro ls [--json]`, `ccmaestro start`,
the watchdog (stuck/loop/died/over-budget), `ccmaestro logs`. Pull reporting. This
alone delivers "I see every agent, its tokens, and who's stuck/dead."
- **Phase 3 — `cc-maestro` control:** `ccmaestro stop` / `steer` / `pause` /
`resume`, push + proactive-alert reporting, autopilot-aware stop, the
`--remote-control` spike.

---

## 9. Testing approach

- **Watchdog (the risky logic):** unit-test the verdict functions against captured
transcript fixtures — a stalled fixture, a looping fixture, a healthy fixture, a
crashed one. This is pure-function logic over JSONL, so it tests cleanly without
launching real agents.
- **CLI plumbing:** integration-test `ccmaestro ls --json` against a real
`claude agents --json` snapshot; `ccmaestro start` on a trivial throwaway task and
assert it appears, accrues tokens, and reports done.
- **Rename/extract:** the test is "everything still loads and resolves" — launch a
session, invoke each skill, run an autopilot cycle, run cancel.
- **Intervention:** start a long throwaway agent, `ccmaestro stop` it, assert it ends;
`ccmaestro steer` it, assert the new instruction lands.

```

```

