# Review Skill — Code Review Against Diff

description: Review code changes against local diff, branch, or PR.

## Targets
- **local**: Uncommitted changes in working tree (`git diff HEAD`).
- **branch:<name>**: Diff between main and named branch (`git diff main...<name>`).
- **pr:<number>**: GitHub PR diff (requires `gh` CLI).

## Output Files
- `REVIEW.md` — detailed findings with severity, category, recommendation.
- `REVIEW_SUMMARY.md` — executive summary.

## Review Axes
1. Correctness: Does the code do what it claims?
2. Security: Injection, auth, secrets, data exposure.
3. Performance: N+1 queries, blocking calls, memory.
4. Style: Matches existing patterns?
5. Architecture: Right place, right abstraction level?

## Rules
- Be specific: cite file:line for every finding.
- Prioritize by severity: critical issues first.
- If code is clean, say so — don't invent issues.
