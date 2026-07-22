# Bump a plugin's version when you change it — it's the only "you're stale" signal

This repo is a Claude Code plugin marketplace. The `version` in each plugin's
`.claude-plugin/plugin.json` is **load-bearing**: it's how Claude Code decides an installed copy is
stale and pulls the new code. Push commits without changing it and every installed instance stays on
the cached copy — the changes never arrive, and the only escape is a full uninstall/reinstall. So a
version bump isn't bookkeeping here; it's the thing that actually ships the work.

- **Touch a plugin → bump that plugin's version, in the same commit.** If your change edits any file
  under `plugins/<name>/`, raise `version` in `plugins/<name>/.claude-plugin/plugin.json` before you
  commit. Bump only the plugins you actually changed — leave the others alone.
- **Use semver, pre-1.0 as it stands.** A bugfix or doc/path correction → **patch** (`0.9.1` →
  `0.9.2`). A new command/skill/behavior → **minor** (`0.9.x` → `0.10.0`). Reserve **major** for a
  breaking change to how the plugin is used.
- **Version order Claude Code resolves:** plugin's `plugin.json` version → the plugin's entry in
  `marketplace.json` → the git commit SHA. We pin it in `plugin.json`, so that's the one to move.
- **The marketplace entry has no version of its own** — don't add one to `.claude-plugin/marketplace.json`
  just to bump it; move the plugin's `plugin.json` instead.
- **A pure-meta commit may not need a bump.** Changes to nothing under any `plugins/<name>/` (root
  README, this rule, repo tooling) ship no plugin code — skip the bump rather than inventing one.
