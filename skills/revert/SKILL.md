---
name: revert
description: Safely revert a commit or range of commits — confirms scope, checks for downstream dependencies, performs the revert, and verifies the result. Use when a change broke something and needs to be rolled back cleanly. Triggers on "revert this", "roll back this commit", "undo this change", "revert PR", "undo last commit".
argument-hint: "[commit hash, PR number, or range A..B]"
allowed-tools: Bash(git status *) Bash(git log *) Bash(git show *) Bash(git diff *) Bash(git revert *) Bash(git checkout *) Bash(git branch *) Bash(git push *) Bash(git commit *) Bash(gh pr view *) Bash(gh pr create *) Bash(npm test *) Bash(yarn test *) Bash(pnpm test *) Bash(make test *) Bash(cargo test *) Bash(go test *) Bash(pytest *) Bash(python -m pytest *) Bash(python3 -m pytest *) Bash(rspec *) Bash(bundle exec rspec *) Bash(mvn test *) Bash(gradle test *) Read
---

Safely revert: `$ARGUMENTS`

## When to revert vs. fix-forward

Revert is the right tool when:
- A change is actively breaking production or tests, and fix-forward would take longer than rolling back.
- The change introduced a regression whose root cause isn't yet understood.
- The change was merged by mistake (wrong branch, unfinished work).

Prefer **fix-forward** (a new commit that fixes the bug) when:
- The root cause is understood and the fix is small.
- Reverting would lose other valuable changes bundled in the same commit.
- The breaking change is already in the hands of users and a follow-up fix is less disruptive than a revert.

If fix-forward is clearly better, **stop and recommend it** instead of reverting.

## Process

### 1. Identify the target

Resolve `$ARGUMENTS` to a concrete commit or range:
- A single hash: `git show <hash> --stat`
- A PR number: resolve to its merge commit first
  ```bash
  gh pr view <number> --json mergeCommit -q .mergeCommit.oid
  ```
- A range `A..B`: list the commits
  ```bash
  git log A..B --oneline
  ```

If no argument is given, show recent commits and ask the user to confirm the target:
```bash
git log --oneline -10
```

**Never revert blindly.** Always confirm the exact commit(s) with the user before acting if there is any ambiguity.

### 2. Inspect what will be reverted

```bash
git show <hash> --stat
git show <hash>
```

For a range, inspect each commit. Understand:
- What files change.
- Whether the commit is a merge commit (needs `-m` flag to revert).
- Whether later commits depend on it.

### 3. Check for downstream dependencies — the critical step

Reverts silently break when later code builds on the reverted change. Before reverting, check:

```bash
# Commits that touched the same files after the target
git log <target-hash>..HEAD --oneline -- <paths-from-target-diff>

# Any commits that reference the target's PR/issue
git log <target-hash>..HEAD --oneline --grep="<PR number>"
```

If later commits depend on the target:
- **Stop.** Do not revert mechanically. Report the dependency and present options:
  1. Revert the dependent commits too (in reverse order).
  2. Fix-forward instead.
  3. Manually craft a revert that preserves the dependent work.
- Let the user choose. A naive revert of commit N while commits N+1, N+2 depend on it will leave the tree broken.

### 4. Ensure a clean working tree

```bash
git status
```

If there are uncommitted changes, **stop and ask** the user whether to stash, commit, or abort. Do not revert on top of dirty state.

### 5. Create a branch for the revert

```bash
git checkout -b revert/<short-description>
```

Do not revert directly on `main`/`master`. Always isolate the revert for review.

### 6. Perform the revert

Single commit:
```bash
git revert <hash> --no-edit
```

Range (reverts in reverse chronological order, latest first):
```bash
git revert A..B --no-edit
```

Merge commit — must specify the parent to revert against:
```bash
git revert -m 1 <merge-hash> --no-edit
```

If a revert produces conflicts:
- **Do not force.** Read the conflicts carefully.
- If the conflict is because later code legitimately depends on the reverted change, stop and go back to step 3's options.
- If the conflict is mechanical (e.g., surrounding lines shifted), resolve it minimally and explain the resolution in the commit message.
- Never use `git revert --abort` silently — report what happened.

### 7. Write a clear revert commit message

If `--no-edit` produced a generic `Revert "..."` message, rewrite it to explain **why**:

```bash
git commit --amend -m "revert(<scope>): roll back <description>" -m "Reverting because: <reason>. Original commit: <hash>. Original PR: #<number>. Verification: <check>."
```

Rules:
- Subject uses `revert(<scope>):` prefix.
- Body explains **why** the revert is needed, not just what is being reverted.
- Reference the original commit hash and PR for traceability.
- No AI attribution.

### 8. Verify

This is non-negotiable. A revert that doesn't build or breaks tests is worse than the original bug.

1. **Build/type-check** the affected module.
2. **Run targeted tests** for the files touched by the revert.
3. **Run the broader suite** if the revert touches shared code or APIs.

```bash
# examples — run whatever the project uses
npm test       # pytest, go test ./..., cargo test, etc.
```

If verification fails, the revert itself is broken — do not push. Go back to step 3 and reconsider.

### 9. Push and open a PR

```bash
git push -u origin revert/<short-description>
gh pr create --title "revert(<scope>): <subject>" --body "<see template>"
```

PR body template:

```markdown
## Revert: <original change>

**Original commit:** <hash>
**Original PR:** #<number>

## Why revert
<2-4 sentences: what broke, impact, why revert is better than fix-forward here>

## What this changes
Rolls back the changes from <hash>. After this revert, <affected-area> behaves as it did before the original PR.

## Downstream dependencies checked
- [ ] No later commits depended on the reverted change (verified via `git log <hash>..HEAD`)
- [ ] Or: dependent commits <list> also reverted / handled

## Verification
- [ ] Build passes: <command>
- [ ] Targeted tests pass: <command>
- [ ] No new regressions in: <area>
```

### 10. Hand off

After opening the PR, tell the user:
- The PR URL.
- What was reverted and why.
- How it was verified.
- Whether any follow-up is needed (e.g., a fresh fix for the underlying problem the reverted change was trying to solve, if applicable).

## Rules

- **Never revert without confirming the exact target commit(s).** Ambiguity here causes outages.
- **Never revert on a dirty working tree.** Stash or commit first.
- **Never revert directly on `main`.** Always use a branch and open a PR.
- **The dependency check (step 3) is the most important step.** Skipping it is the #1 cause of broken reverts. If later commits depend on the target, stop and surface options.
- **Always verify after reverting.** A revert that breaks the build is not a fix.
- **Explain why, not just what.** A revert commit that says only `Revert "feat: add X"` is useless six months later. Always amend to include the reason.
- If the target is a merge commit, always use `-m` with the correct parent number. Reverting a merge without `-m` will fail or produce a broken tree.
- For a multi-commit range, reverts happen in **reverse chronological order** (latest first) so each revert applies cleanly.
- If conflicts arise because later code depends on the reverted change, this is a signal to **stop and reconsider**, not to force a resolution.
