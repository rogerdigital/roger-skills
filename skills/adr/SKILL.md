---
name: adr
description: Create an Architecture Decision Record documenting a significant technical decision — the context, decision, and consequences. Triggers on "write ADR", "document this decision", "architecture decision", "record this choice", "why did we decide".
argument-hint: "[decision title or topic]"
allowed-tools: Read Write Bash(git log *)
---

Create an Architecture Decision Record for: `$ARGUMENTS`

## Process

### 1. Gather context

If `$ARGUMENTS` is provided, use it as the decision topic. If not, analyze recent changes:
```bash
git log --oneline -20
```
Identify significant decisions from recent work.

### 2. Determine ADR number

Check for existing ADRs:
- Look for `docs/adr/`, `adr/`, or `architecture/decisions/` directory
- If ADRs exist, increment the highest number
- If no ADR directory exists, create `docs/adr/`

### 3. Write the ADR

Use the Michael Nygard format:

```markdown
# ADR-NNNN: <title>

## Status
<Proposed | Accepted | Deprecated | Superseded by ADR-NNNN>

## Date
YYYY-MM-DD

## Context
<What is the technical or business circumstance that motivates this decision? What is the problem we're solving? What constraints exist?>

## Decision
<What is the change that we're proposing or have made? Be specific about the chosen approach.>

## Consequences
<What becomes easier or harder because of this decision? Include both positive and negative outcomes. Consider: performance, maintainability, team productivity, operational complexity.>

### Positive
- <benefit 1>
- <benefit 2>

### Negative
- <tradeoff 1>
- <tradeoff 2>

### Risks
- <risk and mitigation>

## Alternatives considered
- <alternative 1>: <why not chosen>
- <alternative 2>: <why not chosen>
```

### 4. Validate

- Does the Context section explain WHY this decision was needed, not just WHAT was decided?
- Does the Decision section name a specific approach, not a vague direction?
- Does the Consequences section include negatives, not just positives?
- Are alternatives documented with reasons for rejection?

## Rules

- Write for a future team member who wasn't in the room. Include the reasoning, not just the outcome.
- ADRs are immutable once Accepted — if the decision changes, create a new ADR that supersedes the old one.
- Keep each ADR focused on one decision. Split if necessary.
- Use plain language. Avoid jargon without explanation.
