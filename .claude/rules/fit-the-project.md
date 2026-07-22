# Fit the project — place each change where it belongs, in the style already there

A codebase is a map: its folder tree shows how it's built, its neighbours show how it's written. Code
that lands wherever was easiest, in whatever style came to hand, blurs both. Before adding, read the
surroundings — then fit the change into them, in place and in idiom.

- **Read the layout before you place a change.** Look at the folder tree and module boundaries — where
  similar things already live — and fit the change into that structure, by the existing conventions,
  not by what's nearest to hand.
- **Match the surrounding code.** Read the neighbours first — naming, layout, error style, idioms — and
  write code that looks like it was already there. Consistency with the codebase beats personal
  preference.
- **Group what belongs together.** Don't scatter related modules across the root or split one concern
  over unrelated places. When a lone file gains a sibling, give the two their own folder. Keep each
  directory about one thing.
- **Make the small structural move the change warrants — no more.** If placing the change well means
  moving or grouping a file or two, do it as part of the work, kept behaviour-preserving. The licence is
  to place *your* change well, not to reshape unrelated structure — a repo-wide reshuffle is its own
  task; flag it and propose it separately.
- **A real structural fork is a decision, not a guess.** When there are materially different ways to lay
  it out, no clear winner, and the move would be costly to undo, surface it and let it be decided.
