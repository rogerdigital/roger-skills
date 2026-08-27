---
name: sync-main
description: Use when safely synchronizing a repository's primary branch with its remote, including requests such as "sync main", "update main branch", "pull latest main", "同步 main", or "同步主分支".
argument-hint: "[optional remote or primary branch]"
allowed-tools: Bash(git status *) Bash(git branch *) Bash(git remote *) Bash(git symbolic-ref *) Bash(git fetch *) Bash(git switch *) Bash(git pull *) Bash(git rev-list *)
---

Synchronize the primary branch for: `$ARGUMENTS`

## Process

### 1. Inspect the worktree

```bash
git status --short --branch
```

If tracked or untracked changes are present, stop. Do not stash, commit, reset,
or overwrite them implicitly.

### 2. Resolve branch and remote

Use an explicit argument when supplied. Otherwise inspect repository context:

```bash
git symbolic-ref refs/remotes/origin/HEAD
git remote -v
git branch --show-current
```

Default to the remote HEAD branch only when it resolves unambiguously. Ask the
user if the production or primary branch cannot be determined.

### 3. Fetch and inspect divergence

```bash
git fetch --prune origin
git rev-list --left-right --count main...origin/main
```

Replace `origin` and `main` with the resolved values. If the local branch is
ahead or diverged, stop and report the counts; do not rewrite history.

### 4. Fast-forward the primary branch

```bash
git switch main
git pull --ff-only origin main
```

### 5. Verify

```bash
git status --short --branch
git rev-list --left-right --count main...origin/main
```

Report the final branch, remote, and ahead/behind counts.

## Rules

- Never use `git reset --hard` to synchronize branches.
- Never create a merge commit.
- Never stash or discard user changes implicitly.
- Never assume `main` when the remote HEAD points elsewhere.
- A clean `0 0` result is an idempotent success.
