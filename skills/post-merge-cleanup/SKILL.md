---
name: post-merge-cleanup
description: Use when cleaning up local or remote feature branches after their pull request has been verified as merged, including "post-merge cleanup", "delete merged branch", "已合并，清理分支", or "清理已合并分支".
argument-hint: "[PR number, URL, or branch name]"
allowed-tools: Bash(git status *) Bash(git branch *) Bash(git remote *) Bash(git symbolic-ref *) Bash(git fetch *) Bash(git switch *) Bash(git pull *) Bash(git merge-base *) Bash(git push *) Bash(gh pr view *)
---

Clean up the merged work for: `$ARGUMENTS`

## Process

### 1. Inspect the worktree

```bash
git status --short --branch
```

Stop if the worktree contains changes. Never delete branches while user work is
uncommitted.

### 2. Resolve and verify the pull request

For a PR number or URL:

```bash
gh pr view <PR> --json state,mergedAt,headRefName,baseRefName,headRepositoryOwner
```

Require `state` to be `MERGED` and `mergedAt` to be non-null. Record the head
branch and base branch from the result. If only a branch name is supplied, find
its PR and verify the same fields; stop if the result is missing or ambiguous.

### 3. Synchronize the base branch

```bash
git fetch --prune origin
git switch main
git pull --ff-only origin main
```

Use the verified base branch instead of assuming `main`.

### 4. Verify merge ancestry

```bash
git merge-base --is-ancestor feature-branch main
```

If ancestry cannot be verified, stop. Do not force-delete the branch merely
because GitHub reports a merged PR; squash and rebase merges may require the PR
merge result rather than commit ancestry, which must be reported explicitly.

### 5. Delete the local branch

```bash
git branch -d feature-branch
```

Use `-d`, never `-D`. Treat an already-absent local branch as success.

### 6. Delete the remote branch when requested

Check whether the remote ref remains:

```bash
git branch -r --list origin/feature-branch
```

Only when the user's request includes remote cleanup and the ref exists:

```bash
git push origin --delete feature-branch
```

If GitHub already deleted the branch, fetch with pruning and report successful,
idempotent cleanup.

### 7. Verify final state

```bash
git status --short --branch
git branch --list feature-branch
git branch -r --list origin/feature-branch
```

Report the merged PR, synchronized base branch, and which branch refs were
removed or already absent.

## Rules

- Never delete the current branch.
- Never use `git branch -D`.
- Never delete an unmerged or ambiguous branch.
- Never delete a remote branch unless the user requested remote cleanup.
- Missing local or remote refs are idempotent success after merge is verified.
