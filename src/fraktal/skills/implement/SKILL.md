# Implement Skill — Code → Review → Fix Loop

description: Implementer writes code → reviewer finds issues → implementer fixes → repeat until clean.

## Workflow
1. **Implementer** writes code following existing patterns.
2. **Reviewer** audits for correctness, security, performance, style, architecture.
3. If open issues remain, **Implementer** addresses them.
4. Repeat until 0 open issues or max rounds exhausted.

## Effort Levels
- **low**: 1 reviewer, max 2 rounds (quick fixes).
- **medium**: 2 reviewers, max 4 rounds (standard features).
- **high**: 3 reviewers (including security auditor), max 6 rounds (critical changes).

## Output Files
- `IMPLEMENT_SUMMARY.md` — what was implemented and why.
- `IMPLEMENT_REVIEW.md` — reviewer findings with severity.

## Rules
- Implementer must read existing code before writing.
- Match existing patterns exactly: naming, error handling, imports.
- Make the smallest change that solves the problem.
- Reviewer must cite specific file:line for each finding.
- Security auditor runs on high effort only.
