---
name: hotfix
description: Ship an urgent production fix safely — triage severity, branch from production, apply the smallest possible fix, verify it, and open a PR for rapid review. Triggers on "hotfix", "urgent fix", "production bug", "ship a hotfix", "emergency fix", "p0 fix".
argument-hint: "[bug description, failing test, or issue reference]"
allowed-tools: Bash(git status *) Bash(git branch *) Bash(git checkout *) Bash(git fetch *) Bash(git pull *) Bash(git log *) Bash(git diff *) Bash(git add *) Bash(git commit *) Bash(git push *) Bash(git tag *) Bash(gh pr create *) Bash(npm test *) Bash(yarn test *) Bash(pnpm test *) Bash(make test *) Bash(cargo test *) Bash(go test *) Bash(pytest *) Bash(python -m pytest *) Bash(python3 -m pytest *) Bash(rspec *) Bash(bundle exec rspec *) Bash(mvn test *) Bash(gradle test *) Read Edit Write
---

Ship a hotfix for: `$ARGUMENTS`

## Principles

A hotfix trades polish for speed, but never trades correctness for speed. The fix must be:
- **Minimal** — touch the fewest lines possible.
- **Verifiable** — proven to fix the issue before it ships.
- **Traceable** — leaves a paper trail (branch, PR, postmortem trigger).

## Process

### 1. Triage — confirm this is actually a hotfix

Before starting, confirm the situation warrants the hotfix path. Ask the user (or infer from context) only what is necessary:

- **Severity**: Is this SEV1/P0 (production down, data loss, security) or recoverable through normal flow?
- **Scope**: Is the blast radius known, or still expanding?
- **Workaround**: Does an existing mitigation (rollback, feature flag, config) avoid the need for new code?

If a rollback or flag flip resolves the issue faster than new code, **stop and recommend that path**. Do not write code when a faster, safer option exists.

Only proceed with code if: new code is required AND the user has confirmed urgency.

### 2. Isolate the root cause — read before editing

Gather evidence:
- Error message, stack trace, failing test
- Logs around the failure
- Recent changes to the affected area:
  ```bash
  git log --oneline -20 -- <affected-path>
  git log --oneline -20
  ```

Identify the **smallest change** that resolves the root cause, not the symptom. If the root cause is unclear after 5 minutes of investigation, stop and tell the user — shipping a speculative fix during an incident makes things worse.

### 3. Create a hotfix branch

Branch from the production/release branch, not from `main` (which may contain unreleased work):
```bash
git fetch origin
git checkout <production-branch>   # often `main`, `master`, `release`, or `prod`
git pull
git checkout -b hotfix/<short-description>
```

If unsure which branch represents production, ask the user. Do not assume.

### 4. Apply the minimal fix

Constraints on the change:
- **Smallest possible diff.** No refactors, no "while I'm here" cleanups, no cosmetic edits.
- **No new features**, even ones that would prevent recurrence — those belong in a follow-up.
- **Match surrounding style** exactly to minimize review friction.
- **Prefer a guard or revert over a rewrite.** Reverting the offending commit is often the safest hotfix.

### 5. Verify before pushing

This step is non-negotiable. A hotfix that isn't verified is a guess.

Run, in order of priority (whichever apply):
1. The exact reproduction that exposed the bug — confirm it no longer fails.
2. The focused unit/integration test for the changed code.
3. The broader test suite for the affected module.

```bash
# language-agnostic examples — run whatever the project uses
npm test -- <path>   # or: pytest <path>, go test ./..., cargo test <pkg>
```

If the bug cannot be reproduced locally, say so explicitly and explain how you verified the fix instead (static reasoning, type check, targeted test).

### 6. Commit

Write a conventional commit with a `fix` type and a scope indicating the area. Reference the incident or issue:

```text
fix(<scope>): <one-line description of the user-visible bug>

<2-3 lines: what was broken, root cause, why this fix is minimal and safe.>

Fixes #<issue>
```

Rules:
- Imperative mood, ≤72 char subject.
- No AI attribution, no co-author trailers.
- Do NOT use `--no-verify`. If pre-commit hooks fail, fix the cause — a hotfix is precisely when you want every check to pass.

### 7. Push and open a PR

```bash
git push -u origin hotfix/<short-description>
```

Open a PR targeting the production branch:
```bash
gh pr create --base <production-branch> --title "fix(<scope>): <subject>" --body "<see template>"
```

PR body template — flag urgency and verification clearly:

```markdown
## 🔥 Hotfix

**Severity:** <SEV1 / P0 / urgent>
**Incident:** <link or description>

## Problem
<1-3 sentences: user-visible symptom and impact>

## Root cause
<1-3 sentences: the underlying cause, not the symptom>

## Fix
<what changed and why it is minimal>

## Verification
- [ ] Reproduction no longer fails: <how>
- [ ] Targeted tests pass: <command run>
- [ ] No regressions in <module>: <command run>

## Post-merge
- [ ] Cherry-pick to `main` (if hotfix branched from release)
- [ ] Create follow-up issue for the systemic fix: <link>
- [ ] Trigger postmortem if SEV1/SEV2: /postmortem

/cc <on-call or team handle>
```

### 8. Hand off and recommend follow-ups

After opening the PR, tell the user:
- The PR URL.
- That the fix has been verified locally and how.
- The two follow-ups that belong in normal flow, not the hotfix:
  1. **Cherry-pick to `main`** if the hotfix branched from a release tag/branch, so the fix isn't lost in the next release.
  2. **A systemic follow-up** (real fix, guard, test, or architectural change) tracked as a separate issue — the hotfix closed the wound, not the underlying risk.
  3. **Postmortem** if the incident warrants it — offer to run `/postmortem`.

## Rules

- **Speed is not an excuse for unverified code.** The fastest path to resolution is a fix that actually works; a broken hotfix doubles the incident.
- **Never branch a hotfix from an unmerged feature branch.** Always from the production branch.
- **Never bundle.** If a second issue surfaces while fixing the first, open a separate branch/PR. Mixed concerns slow review.
- **Never skip the reproduction/verification step**, even under pressure. If you can't verify, say so loudly and let the user decide whether to proceed.
- **Do not close the loop silently.** Always report: what was broken, what you changed, how you verified, what remains.
- If at any point the fix grows beyond a few lines, stop and reconsider — you may be fixing more than the bug, which belongs in normal flow, not a hotfix.
