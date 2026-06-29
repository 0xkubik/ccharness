---
name: cheatsheet-management
description: Build or refresh the reminder cheat-sheet (.claude/ccharness/cheatsheet.md) that a UserPromptSubmit hook re-surfaces every few prompts — a short list of the always-loaded tooling (plugins, skills, agents, MCP) so the model doesn't drift back to its habits mid-session. Runs standalone or as a step of /cc-init.
---

# cheatsheet-management — keep the reminder cheat-sheet current

**Explain as you go — don't just execute.** Open by telling the human what this does and why: over a
long session the model's attention to the capabilities it loaded at startup fades — it drifts back to
raw `grep`/`Read` instead of an indexed search, or forgets a skill or agent it could dispatch. This
skill writes a short cheat-sheet that a shipped `UserPromptSubmit` hook re-prints **every third prompt**,
near the end of the context where it's most visible. The hook is dumb — it just prints this file; all
the thinking happens here, once. Narrate each step and its reason as you go.

**Scope — always-loaded tooling only.** The sheet reminds **only** of the plugins, skills, agents, and
MCP servers that come into *every* session automatically. **Nothing project-specific** — not the
project's rules, code, conventions, or roadmap (those live elsewhere; what the model forgets is the
*capabilities* it has). Tell the human this up front so they know what the sheet is and isn't.

1. **Inventory the always-loaded capabilities.** **Plugins:** `claude plugin list < /dev/null`.
   **Skills:** the slash-skills this session exposes (`/crux`, `/slap`, the funnel, …). **Agents:** the
   subagent types you can dispatch (`Explore`, `Plan`, …). **MCP servers:** `claude mcp list < /dev/null`
   — flag the ones worth preferring over a built-in (an indexed code search over raw `grep`, a docs
   fetcher over memory). Do **not** read `.claude/rules`, the codebase, or the roadmap — project
   specifics never belong here.
2. **Turn each into a candidate line** — shape *situation → preferred move*, plain, one capability per
   line. Keep the pool tight; a long sheet becomes wallpaper the model also learns to skip.
3. **Enforce the width limit — strictly ≤ 80 characters per line.** Models miscount, so check the
   candidates mechanically and fix any offender — re-run until it prints nothing:
   `printf '%s\n' "<each candidate line>" | awk 'length > 80 {print NR": "length" chars"}'`
4. **Let the human pick the lines** — `AskUserQuestion`, `multiSelect: true`, **paginated** (≤4 options
   per question; more candidates → more questions, page by page). One option per candidate line; its
   **description carries the justification** — *what you saw* (which plugin / skill / agent / MCP) and
   *why it earned a line*. **Only the ticked lines are written**; `Other` lets the user add a line you
   didn't list.
5. **Write the picked lines** to `.claude/ccharness/cheatsheet.md` (create `.claude/ccharness/` if
   needed), in this fixed structure — the `<cheatsheet>` / `</cheatsheet>` markers frame the block the
   hook injects, one line per line between them:

   ```
   <cheatsheet>
   Search code: use the codegraph MCP, not raw grep/Read
   Lib/API docs: use the context7 MCP, not memory
   Stuck on a fix: /slap; murkier doubt: /crux
   Broad multi-file search: dispatch the Explore agent
   </cheatsheet>
   ```

6. **Report** what you wrote and how it behaves: active from the **next** session, injected every third
   prompt; to turn it off, delete or rename `.claude/ccharness/cheatsheet.md` (the hook is a no-op
   without it).
