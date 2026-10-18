# `restructure` synthesises root-cause moves, then verifies the combined ones

Grouping findings by concept (ADR-0001) produced one move per concept, with little more value than the lens reports themselves. `restructure` now runs a synthesis sub-agent that clusters findings by shared code and cause, finds the root cause behind each cluster, designs two or three candidate moves, and picks the one that removes the most smells for its cost, accounting for every finding as removed, partly, untouched or worse. Moves that claim to remove two or more findings are then checked by adversarial verify sub-agents (top five, skipped for single-lens runs), because the claim comes from a model agreeing with reports from the same model. Moves are ranked by value, not by strength then convergence. Lens reports, moves and verdicts pass through files in a temporary run folder, so the main conversation holds only the final moves.

## Considered options

- **Grouping only (ADR-0001).** Cheap, but it merges by name and can't find one fix behind smells the lenses named differently.
- **Synthesis without verification.** About 1.3× cheaper per run, but the headline claim, "one move removes six smells", would go unchecked.
- **Verify every move.** Local moves rest on one finding the lens already evidenced; checking them costs more than a wrong one does.

Which model each sub-agent runs on is open: `.scratch/restructure-lenses/issues/01-model-choice.md`.
