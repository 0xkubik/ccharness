# Keep the file tree clean — place each change where it belongs

A project's folder tree is a map of how it's built. Code that lands wherever was easiest blurs that
map: related things drift apart, the root fills with loose files, and the next person can't tell
from the layout where anything lives. Before adding to the tree, read it — then put the change where
it belongs, and keep the structure clean as you go.

- **Read the layout before you place a change.** Look at the folder tree and how the code is
  organised — module boundaries, naming, where similar things already live — and fit the change
  *into* that structure. Which module does it extend? What should it be named? Where do new files
  go? Decide by the existing conventions, not by what's nearest to hand.
- **Group what belongs together.** Don't scatter related modules across the root, and don't leave
  one concern split over unrelated places. When a lone file at the root gains a sibling, give the
  two their own folder. Keep each directory about one thing.
- **Make the small structural move the change warrants.** If placing the change well means moving or
  grouping a file or two, do it as part of the change — a tidy tree is part of doing the work, not a
  separate chore. Keep the move safe: the code still runs and does the same thing afterwards.
- **Bound it to this change — don't reorganise the repo.** The licence is to place *your* change
  well, not to reshape structure that has nothing to do with it. A repo-wide reshuffle is its own
  task; flag it and propose it separately.
- **A real structural fork is a decision, not a guess.** When there are materially different ways to
  lay it out, no clear winner, and the move would be costly to undo, that's a fork — surface it and
  let it be decided, don't silently pick one.
