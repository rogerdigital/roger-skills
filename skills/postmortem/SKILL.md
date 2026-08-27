---
name: postmortem
description: Generate a blameless incident postmortem from git history, logs, and incident context — produces a structured RCA with timeline, root cause chain, and prevention actions. Triggers on "write postmortem", "incident report", "post-mortem", "RCA", "root cause analysis", "what went wrong".
argument-hint: "[incident description, date range, or 'interactive' for guided Q&A]"
allowed-tools: Bash(git log *) Bash(git diff *) Bash(git show *) Bash(git blame *) Bash(find *) Bash(grep *) Read
---

Generate a blameless incident postmortem for: `$ARGUMENTS`

## Process

### 1. Gather incident context

If `$ARGUMENTS` contains a description or date range, extract:
- **What happened** (user-visible symptoms)
- **When** (start time, detection time, resolution time)
- **Impact** (users affected, revenue impact, SLA breach)
- **Severity** (SEV1-4 or P1-P4)

If `$ARGUMENTS` is "interactive" or insufficient context is provided, ask these questions one at a time:
1. What user-visible symptoms occurred? (errors, latency, outage)
2. When did it start and when was it resolved? (timestamps with timezone)
3. How was it detected? (monitoring alert, user report, manual discovery)
4. What was the blast radius? (all users, specific region, single customer, internal only)
5. What severity would you assign? (SEV1: full outage, SEV2: major degradation, SEV3: partial impact, SEV4: minor)

### 2. Analyze git history around the incident

Search for relevant changes in the incident timeframe:

```bash
git log --after="<start-time-minus-24h>" --before="<resolution-time>" --all --format="%h %ai %an %s"
```

For each suspicious commit:
```bash
git show <hash> --stat
git diff <hash>~1 <hash>
```

Look for:
- Deployments or config changes immediately before the incident
- Changes to the affected service/component
- Infrastructure or dependency changes
- Reverts that indicate the fix

### 3. Identify the root cause chain

Trace the causality chain from trigger to impact:

```text
Triggering event → Propagation mechanism → User-visible impact
```

Distinguish between:
- **Root cause**: The underlying condition that allowed the incident (e.g., missing input validation)
- **Triggering event**: The specific action that activated the root cause (e.g., a deployment, a traffic spike)
- **Contributing factors**: Conditions that made it worse or delayed detection (e.g., missing monitoring, unclear runbook)

Ask yourself:
- Why did this specific change cause a failure? (direct cause)
- Why was this change allowed to reach production? (process gap)
- Why wasn't it detected faster? (observability gap)
- Why did recovery take as long as it did? (response gap)

### 4. Build the timeline

Construct a timeline from available evidence:

Sources:
- Git commits and deploys
- Error log timestamps (if provided)
- Alert firing times (if known)
- User-provided context

Format each entry as:
```text
HH:MM TZ — <event> — <who/what>
```

### 5. Identify what went well

Look for positive signals:
- Fast detection (alert fired within minutes)
- Clear escalation (right people looped in quickly)
- Effective rollback (minimal additional damage)
- Good communication (status page updated, stakeholders informed)
- Existing safeguards that limited blast radius (feature flags, circuit breakers, rate limits)

### 6. Generate action items

For each gap identified, create a specific, actionable item.

Categorize each action as:
- **Detect**: Improve ability to catch this class of issue earlier (monitoring, alerting, tests)
- **Prevent**: Eliminate the root cause or make it impossible (code fixes, architectural changes, validation)
- **Mitigate**: Reduce impact when similar issues occur (circuit breakers, graceful degradation, runbooks)

Each action item must have:
- A specific description (not vague "improve monitoring")
- A suggested owner role (e.g., "Backend team", "Platform team", "On-call engineer")
- A priority: P0 (this week), P1 (this sprint), P2 (this quarter)

### 7. Write the postmortem

Output in this format:

```markdown
# Incident Postmortem: <title>

**Date:** <incident date>
**Duration:** <start> to <resolution> (<total time>)
**Severity:** <SEV level>
**Author:** <to be filled>
**Status:** Draft

---

## Summary

<2-3 sentences: what happened, what the impact was, and what the root cause was. Written for someone with no prior context.>

## Impact

- **Users affected:** <number or percentage>
- **Duration of impact:** <time>
- **Services affected:** <list>
- **SLA breach:** Yes / No (<detail>)
- **Revenue impact:** <if known, otherwise "TBD">
- **Support tickets generated:** <if known>

## Timeline

All times in <timezone>.

| Time | Event |
|---|---|
| HH:MM | <triggering event> |
| HH:MM | <first symptoms observed> |
| HH:MM | <alert fired / issue detected> |
| HH:MM | <investigation began> |
| HH:MM | <root cause identified> |
| HH:MM | <mitigation applied> |
| HH:MM | <full resolution confirmed> |

## Root Cause

<Clear explanation of the root cause. Technical but accessible. Include the causal chain.>

**Triggering event:** <what specifically triggered the failure>
**Underlying cause:** <why the system was vulnerable to this trigger>

## Contributing Factors

- <Factor 1>: <how it made things worse>
- <Factor 2>: <how it delayed detection or recovery>

## What Went Well

- <Positive 1>
- <Positive 2>

## What Went Wrong

- <Gap 1>
- <Gap 2>

## Action Items

### Prevent (eliminate root cause)

| # | Action | Owner | Priority | Ticket |
|---|---|---|---|---|
| 1 | <specific action> | <team/role> | P0 | <to be created> |

### Detect (catch it faster)

| # | Action | Owner | Priority | Ticket |
|---|---|---|---|---|
| 1 | <specific action> | <team/role> | P1 | <to be created> |

### Mitigate (reduce blast radius)

| # | Action | Owner | Priority | Ticket |
|---|---|---|---|---|
| 1 | <specific action> | <team/role> | P1 | <to be created> |

## Lessons Learned

<1-3 key takeaways that apply beyond this specific incident. What systemic improvement does this point to?>

---

*This is a blameless postmortem. The goal is to improve systems and processes, not to assign blame to individuals.*
```

## Rules

- **Blameless tone is non-negotiable.** Never name individuals as causes. Use team/role/system language. "The deployment pipeline allowed..." not "Alice deployed a bad change."
- **Do NOT** speculate about root cause without evidence. If uncertain, state clearly: "Root cause is uncertain. Leading hypothesis: X, based on evidence Y."
- **Do NOT** fabricate timeline entries. If timestamps are unknown, mark as "~HH:MM (approximate)" or leave gaps explicitly noted.
- Be specific in action items. "Add monitoring for database connection pool exhaustion, alerting when utilization exceeds 80%" beats "improve monitoring."
- Every action item must be categorized as Detect, Prevent, or Mitigate. If an action does not fit any category, it is too vague.
- If git history shows a revert, identify both the original offending commit and the revert as key timeline events.
- Keep the Summary section understandable by non-engineers (managers, PMs). Technical details belong in Root Cause.
- If insufficient information is available to complete a section, mark it as `[TBD — needs input from <who>]` rather than guessing.
