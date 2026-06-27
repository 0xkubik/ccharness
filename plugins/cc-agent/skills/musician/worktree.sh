#!/usr/bin/env bash
# musician worktree helper — the deterministic git bookkeeping for build isolation, extracted from
# SKILL.md so the exact, error-prone sequence is testable instead of hand-typed across re-fed turns.
#
# The musician CONDUCTS from the main repo; every build (a cc-tools:do / refactor-review-test
# subagent) is dispatched with worktree isolation so its work — and all of its nested agents —
# stays in one throwaway worktree under .claude/worktrees/, never leaking into the main tree. The
# harness creates that worktree and hands the conductor back its path + branch. THIS script lands
# the finished commit on the current branch and removes the worktree, or discards an abandoned one.
#
# Usage:
#   worktree.sh prepare                       once at arm: make build isolation correct + clean
#   worktree.sh integrate <wt_path> <branch>  a build committed -> land it on the current branch
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

ensure_baseref() {
  # Build worktrees must branch from the LOCAL HEAD (the musician commits locally, never pushes, so
  # local is routinely ahead of origin). Without this the default ("fresh") branches from origin and
  # the build runs against stale code. Written to the PERSONAL settings.local.json (gitignored, takes
  # precedence over project settings) so it's durable for this user without being imposed on the team.
  command -v jq >/dev/null 2>&1 || { printf 'BASEREF=no-jq\n'; return; }
  local s=".claude/settings.local.json" tmp
  mkdir -p .claude 2>/dev/null || true
  if [ -f "$s" ]; then
    [ "$(jq -r '.worktree.baseRef // ""' "$s" 2>/dev/null)" = "head" ] && return
    tmp="$s.tmp.$$"
    jq '.worktree.baseRef="head"' "$s" > "$tmp" 2>/dev/null && mv "$tmp" "$s" && printf 'BASEREF=set\n'
  else
    jq -n '{worktree:{baseRef:"head"}}' > "$s" && printf 'BASEREF=created\n'
  fi
}

case "$cmd" in
  prepare)
    ensure_gitignore
    ensure_baseref
    # A build worktree is cut from committed HEAD — an uncommitted North Star (e.g. /find-goal was
    # just run) would be ABSENT in the worktree and fail do's grounding gate. Surface it so the
    # conductor commits the grounding before building.
    if [ -n "$(git status --porcelain CLAUDE.md 2>/dev/null)" ]; then
      printf 'GROUNDING_DIRTY=1\n'
    fi
    git worktree prune 2>/dev/null || true
    printf 'PREPARED=1\n'
    ;;

  integrate)
    wt="${2:-}"; br="${3:-}"
    if [ -z "$wt" ] || [ -z "$br" ]; then printf 'ERROR=integrate-needs-path-and-branch\n'; exit 0; fi
    # Land the build commits on the current branch. baseRef=head means the build branched from this
    # HEAD, so a fast-forward is the clean path; fall back to a real merge if HEAD moved; on a true
    # conflict, abort and KEEP the worktree so the work is never lost — the conductor surfaces it.
    if git merge --ff-only "$br" 2>/dev/null; then
      :
    elif git merge --no-edit "$br" 2>/dev/null; then
      :
    else
      git merge --abort 2>/dev/null || true
      printf 'CONFLICT=%s\nWORKTREE_KEPT=%s\n' "$br" "$wt"
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
