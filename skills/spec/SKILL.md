---
name: spec
description: Write a concise requirements specification before implementation — clarifies scope, acceptance criteria, and constraints. Triggers on "write spec", "define requirements", "spec this out", "what should this do", "requirements document".
argument-hint: "[feature or task description]"
allowed-tools: Read Write
---

Write a requirements specification for: `$ARGUMENTS`

## Process

### 1. Clarify requirements

Start by asking clarifying questions ONE AT A TIME to extract:
- Who is the user and what are they trying to accomplish?
- What is the core behavior (the minimum that must work)?
- What are the edge cases and error scenarios?
- What are the non-functional requirements (performance, scale, compatibility)?
- What is explicitly OUT of scope?

If `$ARGUMENTS` provides enough context, state your assumptions and proceed.

### 2. Write the specification

Structure:

```markdown
# <Feature Name>

## Problem
<1-2 sentences: what problem does this solve and for whom>

## Requirements
### Must have (P0)
- [ ] <requirement 1 — specific, testable>
- [ ] <requirement 2>

### Should have (P1)
- [ ] <requirement 3>

### Nice to have (P2)
- [ ] <requirement 4>

## Acceptance criteria
Given <context>, when <action>, then <expected result>.

- <criterion 1>
- <criterion 2>
- <criterion 3>

## Out of scope
- <explicitly excluded item 1>
- <explicitly excluded item 2>

## Technical considerations
- <constraint or implementation note 1>
- <constraint or implementation note 2>

## Open questions
- [ ] <question that needs resolution before implementation>
```

### 3. Validate the spec

Check for:
- Is each requirement specific enough to test? (No vague words like "fast", "better", "improved")
- Are acceptance criteria written as verifiable conditions?
- Is the scope bounded? (If it describes more than one feature, split it)
- Are edge cases covered? (Empty states, errors, concurrent access, large inputs)

### 4. Save

- Save to a location matching project conventions
- Common locations: `specs/`, `docs/specs/`, `requirements/`
- If no convention exists, use `specs/<feature-name>.md`

## Rules

- Prefer concrete over vague. "Response time under 200ms at P99" beats "fast response".
- Every P0 requirement must have at least one acceptance criterion.
- If you can't make a requirement testable, flag it as an open question.
- Don't design the solution in the spec — describe the problem and constraints.
- Keep it short. A good spec fits on one page. If it's longer, scope is probably too broad.
