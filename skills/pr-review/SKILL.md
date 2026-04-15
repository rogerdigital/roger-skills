---
name: pr-review
description: Review a pull request thoroughly — code quality, logic, security, test coverage, and style. Triggers on "review PR", "review pull request", "review this PR", "code review", "/pr-review [PR number or URL]".
argument-hint: "[PR number or URL]"
allowed-tools: Bash(gh pr *) Bash(git diff *) Bash(git log *)
---

Perform a thorough code review of the pull request: `$ARGUMENTS`

## Process

### 1. Fetch PR context
```bash
gh pr view $ARGUMENTS
gh pr diff $ARGUMENTS
```
If `$ARGUMENTS` is empty, use the current branch's open PR.

### 2. Understand intent
- Read the PR title, description, and linked issues.
- Identify what problem is being solved and the expected behavior change.

### 3. Review the diff across these dimensions

#### Correctness
- Does the logic achieve what the description claims?
- Are edge cases handled (empty input, nulls, concurrency, error paths)?
- Are there off-by-one errors, incorrect conditionals, or missed returns?

#### Security
- Is user input validated and sanitized?
- Any SQL injection, XSS, path traversal, or command injection risks?
- Are secrets hardcoded or exposed in logs?
- Are permissions and authorization checks correct?

#### Performance
- Any N+1 queries, unbounded loops, or unnecessary re-computation?
- Large allocations or memory leaks?

#### Test coverage
- Are new behaviors covered by tests?
- Are tests testing behavior, not implementation details?
- Are failure/error cases tested?

#### Maintainability
- Is the code readable and consistently styled?
- Are functions/classes doing too much (SRP)?
- Are names clear and accurate?
- Is there unnecessary duplication that should be extracted?

#### Breaking changes
- Does this change any public API, DB schema, or config format?
- Is backward compatibility handled?

### 4. Output format

Structure the review as:

```
## Summary
<2-3 sentence overall assessment>

## Must Fix (blocking)
- [file:line] Issue description. Suggested fix.

## Suggestions (non-blocking)
- [file:line] Improvement idea.

## Nitpicks
- [file:line] Minor style/naming preference.

## Positive notes
- What was done well.
```

Only include sections that have content. Be specific — always reference file and line number.
