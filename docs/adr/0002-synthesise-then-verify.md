# `restructure` synthesises root-cause moves, then verifies the combined ones

Grouping findings by concept (ADR-0001) produced one move per concept, with little more value than the lens reports themselves. `restructure` now runs a synthesis sub-agent that clusters findings by shared code and cause, finds the root cause behind each cluster, designs two or three options, and picks the one that removes the most smells for its cost, accounting for every finding as removed, partly, untouched or worse. Moves that claim to remove two or more findings are then checked by adversarial verify sub-agents (top five, skipped for single-lens reviews), because the claim comes from a model agreeing with reports from the same model. Moves are ranked by value, not by strength then convergence. Lens reports, moves and check results pass through files in a temporary work folder, so the main conversation holds only the final moves.

## Considered options

- **Grouping only (ADR-0001).** Cheap, but it merges by name and can't find one fix behind smells the lenses named differently.
- **Synthesis without verification.** About 1.3× cheaper per review, but the headline claim, "one move removes six smells", would go unchecked.
- **Verify every move.** Local moves rest on one finding the lens already evidenced; checking them costs more than a wrong one does.

Which model each sub-agent runs on: lens and verify on Sonnet, synthesis on the session model, overridable per review.

## Addendum: every review verifies what can change the verdict

A Factory reads a review's verdict, and `change` sends it back to work, so an unchecked single-finding move now costs more than checking it. Every review therefore verifies every candidate for a **necessary move** (defined in `shared/CONTRACT.md`), single-finding ones included, as well as the top five other combined moves. To keep the cost down, single-finding candidates are checked in groups of about five per verify sub-agent, verify is the stage to put on a cheaper model, and an optional `max-moves N` stops verifying necessary-move candidates once N are confirmed; candidates past it are not pursued. This replaces "skipped for single-lens reviews" and "local moves aren't verified" above.
