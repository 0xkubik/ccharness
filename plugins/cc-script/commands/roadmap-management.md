---
description: "Create or maintain the product's roadmap — the North Star goal + ordered feature list in docs/ccharness/roadmap.md. First run charters it (goal → features → review); a re-run rethinks it freely; given one concrete feature it helps you think it through and records a line (with --force, it formulates and writes after one confirm). Every other cc-instruments skill routes here when no North Star exists; what-to-do biases its menu toward the current frontier."
argument-hint: "[optional: a feature to add · --force to write it after one confirm]"
---

Invoke the `roadmap-management` skill with this scope:

> $ARGUMENTS

roadmap-management is the harness's **grounding front door** and the roadmap's keeper across its life.
It picks one of **four modes**: on a fresh repo it **charters** the roadmap — captures the product's
**North Star** (vision · core problem · level) at the top of `docs/ccharness/roadmap.md`, then lays
out a **flat, ordered list of features** below it, built top to bottom; on a re-run it **rethinks** the
roadmap freely, or **folds in a single feature** you bring (with `--force`, it formulates and writes
that feature after one confirm — never silently). Other product skills (`what-to-do`, `how-to-do`,
`do`, `musician`) route here when no North Star exists. Re-run any time — it reads what exists and
adapts, no flag needed.
