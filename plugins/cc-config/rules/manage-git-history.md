# Manage git history autonomously — never ask about branch, commit, or push

When this rule is installed, you own the git history end to end. Don't ask whether or when to branch,
commit, or push — decide and do it as a normal part of finishing work, then report what you did.

- **Follow the repo's established workflow.** Read how the project actually works — recent history,
  branch names, whether it uses PRs — and match it. Direct-to-main here means do that; topic branches
  and PRs mean do that.
- **Branch, commit, and push on the natural rhythm.** A branch per coherent unit of work (anything
  going through review, or work you don't want on main yet). Commits at meaningful checkpoints — small
  and focused over one giant blob, staging only what belongs to the change. Push when a unit is done or
  a branch needs to exist remotely.
- **Write honest, conventional messages.** Describe what actually changed and why, in the repo's
  existing style. Never claim work that wasn't done.
- **Keep `.gitignore` current.** Owning the history includes owning what's tracked. Send build outputs,
  logs, local or editor config, and dependency directories to `.gitignore` instead of committing them.
- **The floor (off-limits without an explicit go-ahead).** Don't rewrite or force-push shared history,
  don't delete remote branches, don't commit secrets or generated junk. Autonomy is over the normal
  forward flow — not destructive or irreversible operations.
