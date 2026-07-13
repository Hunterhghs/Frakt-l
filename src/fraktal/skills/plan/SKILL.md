# Plan Skill — Read-Only Architecture Exploration

description: Read-only exploration → step-by-step implementation plan.

## Workflow
1. Explore the codebase to understand existing architecture and patterns.
2. Identify all files, functions, and dependencies relevant to the task.
3. Assess complexity: what's straightforward, what's risky.
4. Produce a numbered, step-by-step implementation plan.

## Output Format
```markdown
# Implementation Plan: [Goal]

## Context
[What exists today — key files, patterns, constraints.]

## Steps
1. **[Step name]** — `file.py`: what to change, exact function/class.
2. **[Step name]** — ...
...

## Risks
- **[Risk]**: likelihood, impact, mitigation.

## Critical Files
- `path/to/file.py` — why it matters.
```

## Rules
- Read-only. Do not create, modify, or delete files.
- Be specific: name exact files, functions, classes.
- Each step should be independently verifiable.
- Match existing code patterns — don't reinvent conventions.
