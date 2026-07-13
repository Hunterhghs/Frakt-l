# Design Skill — Write → Review → Revise Loop

description: Writer produces DESIGN.md → reviewer audits → writer revises → repeat until clean.

## Workflow
1. **Writer** produces initial DESIGN.md + DESIGN_SUMMARY.md.
2. **Reviewer** audits for completeness, feasibility, risk, clarity, tradeoffs.
3. If open issues remain, **Writer** revises the design document.
4. Repeat until 0 open issues or max rounds exhausted.

## Design Document Structure
- Overview: What we're building and why.
- Current State: What exists today.
- Proposed Design: Architecture, data flow, components.
- Implementation Plan: Numbered steps with file paths.
- Tradeoffs: What we're trading off.
- Alternatives Considered: What we rejected.
- Risks & Mitigations: What could go wrong.
- Migration Plan: How to roll out safely.

## Output Files
- `DESIGN.md` — full design document.
- `DESIGN_SUMMARY.md` — executive summary.
- `DESIGN_REVIEW.md` — reviewer audit findings.

## Rules
- Writer and Reviewer are separate personas with separate system prompts.
- Reviewer must find 0 open issues before the skill completes.
- Max 5 review rounds.
