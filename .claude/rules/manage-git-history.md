# Manage git history autonomously — never ask about branch, commit, or push

When this rule is installed, you own the git history end to end. Don't ask the user whether or when
to branch, commit, or push — decide and do it yourself as a normal part of finishing work. The user
installed this rule precisely so they never have to answer "should I commit now?" again.

- **Never ask permission for routine git.** Branching, staging, committing, and pushing are your
  call. Don't pause to confirm them and don't offer them as a choice — do them at the right moment
  and report what you did afterward.
- **Follow the repo's established workflow.** Read how this project actually works — recent history,
  branch names, whether it uses pull requests — and match it. If work lands directly on the main
  branch here, do that; if it uses topic branches and PRs, do that.
- **When to branch.** Start a new branch for a distinct piece of work when the project's workflow
  calls for it — anything going through review, or work you don't want on the main branch yet. One
  branch per coherent unit of work.
- **When to commit.** Commit at meaningful checkpoints — a coherent, working step; tests green; a
  logical unit done. Prefer small, focused commits over one giant one. Stage only what belongs to
  the change; don't sweep in unrelated edits already sitting in the tree.
- **When to push.** Push when the work is ready to leave the machine — a unit is done, or a branch
  needs to exist remotely for a PR. Use your judgment on timing.
- **Write honest, conventional messages.** Describe what actually changed and why, in the style the
  repo already uses. Never claim work that wasn't done.
- **Keep `.gitignore` current.** Owning the history includes owning what's tracked. When build
  outputs, logs, local or editor config, dependency directories, or other generated junk show up in
  the tree, add them to `.gitignore` instead of committing them or leaving them as noise — and never
  let secrets near a commit. Match the patterns the repo already uses.
- **The floor (still off-limits without an explicit go-ahead).** Don't rewrite or force-push shared
  history, don't delete remote branches, and don't commit secrets or generated junk. Autonomy is
  over the normal forward flow — not destructive or irreversible operations.
