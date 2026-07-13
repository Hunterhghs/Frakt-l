# Build Skill — Full Pipeline Orchestration

description: Complete Grok Build pipeline: plan → design → implement → review.

## Pipeline Phases

### Phase 1: Plan
Read-only architecture exploration. Architect produces step-by-step implementation plan.

### Phase 2: Design
Design-doc-writer produces DESIGN.md. Design-doc-reviewer audits it. Writer revises until clean.

### Phase 3: Implement
Implementer writes code. Reviewer finds issues. Implementer fixes them. Loop until clean.

### Phase 4: Review
Final code review against the diff. Security audit on high effort.

## Options
- `--effort low|medium|high`: Controls review thoroughness (default: medium).
- `--skip-design`: Skip Phase 2 for small/incremental changes.

## Rules
- Each phase must complete before the next begins.
- Plan and Design phases are read-only (except design doc writing).
- Implement phase executes real code changes.
- Review is the final gate before declaring done.
