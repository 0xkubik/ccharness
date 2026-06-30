#!/usr/bin/env bash
# musician worktree helper — the deterministic git bookkeeping for build isolation, extracted from
# SKILL.md so the exact, error-prone sequence is testable instead of hand-typed across re-fed turns.
#
# The musician CONDUCTS from the main repo on the `main` branch; every build (a cc-script:do /
# refactor-review-test subagent) is dispatched with worktree isolation so its work — and all of its
# nested agents — stays in one throwaway worktree under .claude/worktrees/, never leaking into the
# main tree. The harness creates that worktree and hands the conductor back its path + branch. THIS
# script lands the finished commit on the local `main` branch and removes the worktree, or discards
# an abandoned one.
#
# Usage:
#   worktree.sh prepare                       once at arm: make build isolation correct + clean
#   worktree.sh integrate <wt_path> <branch>  a build committed -> land it on local main
#   worktree.sh discard   <wt_path> <branch>  an abandoned build -> drop the worktree, keep nothing
#
# Output: KEY=VALUE lines for the skill to react to. Always exits 0 (the skill reads the keys).
set -u

cmd="${1:-}"

ensure_gitignore() {
  # Registered worktrees show up as `?? .claude/worktrees/` in the main repo — keep them out of
  # the tree so a stray `git add -A` (or the conductor) never commits the scaffolding.
  local gi=".gitignore"
  if [ ! -f "$gi" ] || ! grep -qxF ".claude/worktrees/" "$gi" 2>/dev/null; then
    printf '.claude/worktrees/\n' >> "$gi"
    printf 'GITIGNORE=added\n'
  fi
}

case "$cmd" in
  prepare)
    ensure_gitignore
    # A build worktree is cut from committed HEAD — an uncommitted North Star / roadmap (e.g.
    # /roadmap-management was just run) would be ABSENT in the worktree and fail do's grounding gate. Surface
    # it so the conductor commits the grounding before building.
    if [ -n "$(git status --porcelain .claude/ccharness/roadmap.md 2>/dev/null)" ]; then
      printf 'GROUNDING_DIRTY=1\n'
    fi
    git worktree prune 2>/dev/null || true
    printf 'PREPARED=1\n'
    ;;

  integrate)
    wt="${2:-}"; br="${3:-}"
    if [ -z "$wt" ] || [ -z "$br" ]; then printf 'ERROR=integrate-needs-path-and-branch\n'; exit 0; fi
    # The finished build lands on the LOCAL `main` branch — that is where the conductor builds toward.
    # Integration is therefore an ff-only merge of the build branch into `main`, so `main` has to be
    # the branch checked out here. If it isn't, REFUSE rather than touch `main` behind the scenes:
    # an off-main run is a misconfiguration, not a build to merge. Report it as STALE (kept worktree),
    # which the caller surfaces the same way as any can't-align case.
    cur="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo '')"
    if [ "$cur" != "main" ]; then
      printf 'STALE=%s\nWORKTREE_KEPT=%s\nREASON=not-on-main\n' "$br" "$wt"
      exit 0
    fi
    # ff-only is the load-bearing guarantee. The build reset its worktree to main's HEAD before
    # building, so its branch is main + the new commits and fast-forwards cleanly. If ff FAILS, the
    # build was NOT on main's HEAD (its reset was skipped, or main moved under a concurrent run)
    # — STALE work must NOT be merged into main silently. Keep the worktree and report; caller rebuilds.
    if ! git merge --ff-only "$br" 2>/dev/null; then
      printf 'STALE=%s\nWORKTREE_KEPT=%s\n' "$br" "$wt"
      exit 0
    fi
    sha="$(git rev-parse --short HEAD 2>/dev/null || echo '')"
    git worktree remove --force "$wt" 2>/dev/null || true
    git branch -D "$br" 2>/dev/null || true
    git worktree prune 2>/dev/null || true
    printf 'INTEGRATED=%s\n' "$sha"
    ;;

  discard)
    wt="${2:-}"; br="${3:-}"
    [ -n "$wt" ] && git worktree remove --force "$wt" 2>/dev/null || true
    [ -n "$br" ] && git branch -D "$br" 2>/dev/null || true
    git worktree prune 2>/dev/null || true
    printf 'DISCARDED=1\n'
    ;;

  *)
    printf 'ERROR=unknown-command:%s\n' "$cmd"
    ;;
esac
exit 0
