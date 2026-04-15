---
name: debug
description: Systematically diagnose a bug or failing test. Reads error output, traces the root cause, and proposes a fix. Triggers on "debug this", "why is this failing", "help me debug", "fix this error", "something is broken".
argument-hint: "[error message, test name, or file path]"
---

Debug the issue described in `$ARGUMENTS` (or the most recent error/failure if no argument given).

## Process

### 1. Gather evidence — read before acting

Collect all available signals:
- Full error message and stack trace
- Relevant log output
- Failing test output
- Recent changes (`git log --oneline -10`, `git diff HEAD~1`)

Do NOT start guessing or editing code yet.

### 2. Reproduce the failure

Identify the exact command or condition that triggers the bug. If you cannot reproduce it, say so clearly and ask for more context.

### 3. Trace the root cause

Follow the execution path from the error backward:
- What function/line is the immediate failure?
- What state or input caused it?
- Where was that state set?
- Is this a logic error, missing guard, wrong assumption, or environmental issue?

Use a hypothesis → evidence → conclusion loop. State your hypothesis, then find evidence to confirm or refute it. Keep going until you have a root cause, not just a symptom.

### 4. Propose and apply the fix

- Fix the root cause, not the symptom.
- Keep the change minimal and targeted.
- If there are multiple possible fixes, explain the tradeoffs and pick the best one.
- Do NOT comment out errors or add `try/catch` to swallow exceptions.

### 5. Verify

After applying the fix:
- Re-run the failing test or reproduce the original scenario.
- Check that no existing tests broke.
- Confirm the fix actually addresses the root cause.

## Output structure

```
## Root Cause
<1-2 sentences: what is broken and why>

## Evidence
- [file:line] What you found
- ...

## Fix
<code change with explanation>

## Verification
<what you ran and what it showed>
```

If you cannot determine the root cause, list what you've ruled out and what additional information is needed.
