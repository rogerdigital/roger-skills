# Skill Quality and Distribution Hardening

## Status

Proposed for implementation after review.

## Problem

The repository has a clear collection of 18 workflow skills, but its current
validation only checks basic frontmatter, non-empty bodies, and a small set of
security patterns. It does not prove that a skill can execute with its declared
`allowed-tools`, that the README inventory matches the filesystem, or that
high-risk workflows stop at the right safety boundaries.

Distribution is also incomplete: the README claims Claude Code and Codex
compatibility but only shows Claude Code installation, and the repository has
no explicit license or release/versioning guidance.

## Goals

1. Make every existing skill's declared tools sufficient for its documented
   workflow while keeping permissions as narrow as practical.
2. Replace the inline CI validator with a locally runnable, tested validator.
3. Validate repository-wide invariants, not only individual Markdown files.
4. Document installation, update, removal, permission impact, and compatibility
   boundaries for supported agents.
5. Add two narrowly scoped Git lifecycle skills only after the existing
   collection is reliable:
   - `sync-main`
   - `post-merge-cleanup`

## Non-goals

- Building a GUI, registry, package manager, or hosted service.
- Creating a generic LLM evaluation platform.
- Rewriting existing skills for style alone.
- Combining PR creation, merge, and cleanup into one long-running workflow.
- Adding unrelated skills while the quality work is in progress.

## Delivery order

### Phase 1: Repair existing tool contracts

Audit every fenced shell command and every required action against the skill's
`allowed-tools`. Change only the declaration or command necessary to make the
workflow executable.

Known mismatches include:

- `create-pr`: uses `git status` without declaring it.
- `release-notes`: uses `git show` without declaring it.
- `hotfix`: uses `git fetch`, `git pull`, and project test commands without
  declaring them.
- `revert`: uses `git commit --amend` and project test commands without
  declaring them.

Broad declarations such as `Bash(npm *)` and `Bash(gh pr *)` must be narrowed
where the workflow only needs read-only subcommands. Skills that intentionally
write Git state or remote state must keep those permissions explicit.

Verification:

- Manual command-to-permission audit for all 18 skills.
- The validator introduced in Phase 2 passes against the repaired collection.

### Phase 2: Extract and strengthen validation

Move validation from the GitHub Actions heredoc into
`scripts/validate_skills.py`. The workflow will invoke this script so local and
CI behavior are identical.

Keep YAML parsing explicit and reproducible by adding a development-only
`requirements-dev.txt` pinned to the locally verified PyYAML 6.0.3. The
repository still has no runtime dependency; the workflow installs this file
only for validation.

The validator will check:

- frontmatter is present, closed, and valid YAML;
- required `name` and `description` fields are non-empty;
- `name` matches the containing directory;
- skill names are unique;
- the Markdown body is non-empty;
- `allowed-tools` does not contain known dangerous command patterns;
- non-audit skills do not instruct collection of sensitive information or
  exfiltration;
- shell commands in executable code blocks are covered by `allowed-tools`;
- unlabelled code blocks that begin with a known shell command are rejected so
  executable examples cannot silently bypass tool-contract validation;
- the README skill inventory matches `skills/*/SKILL.md` exactly.

Some code blocks are illustrative output or templates rather than executable
commands. Executable blocks must use `bash` or `sh`; non-executable blocks must
use an appropriate language such as `text` or `markdown`. An exceptional shell
example can skip only tool-coverage validation by placing this marker directly
before the fence:

```markdown
<!-- skill-validator: ignore-shell reason="illustrative output only" -->
```

The marker requires a non-empty reason and does not bypass dangerous-command or
exfiltration checks. The initial implementation will stay intentionally
conservative: when command parsing is ambiguous, it will report a precise
validation error instead of trying to emulate a shell.

Tests will use Python's standard `unittest` framework with temporary fixture
repositories. Required cases:

- valid skill collection;
- missing or malformed frontmatter;
- duplicate or directory-mismatched name;
- empty body;
- dangerous permission;
- executable command missing its permission;
- unlabelled executable command block;
- valid and invalid ignore markers;
- stale README inventory;
- security-audit exemption for legitimate secret scanning.

Verification:

- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/validate_skills.py`
- GitHub Actions passes with the same entrypoint.

### Phase 3: Complete distribution documentation

Update the README with:

- separate Claude Code and Codex installation examples;
- project-level and user-level installation where supported;
- update and removal instructions;
- a capability table identifying read-only, local-write, Git-write, and
  remote-write skills;
- a concise contributor checklist that includes local validation.

Add an explicit license only after the owner selects its terms. License choice
is a legal/product decision and will not be inferred from the repository being
public. The implementation must pause before creating `LICENSE` if no choice
has been recorded.

Introduce lightweight versioning only after the quality and documentation
changes are merged. This means a semantic version tag and changelog entry, not
a package registry or installer.

Verification:

- README commands and paths match the current repository layout.
- README inventory validation passes.
- No unsupported compatibility claim is added.

### Phase 4: Add `sync-main`

Purpose: safely synchronize a local primary branch with its remote counterpart.

Behavior:

1. Detect the primary branch from repository context; ask only if ambiguous.
2. Stop on a dirty worktree unless the changes are already safely isolated.
3. Fetch the remote.
4. Switch to the primary branch.
5. Update using fast-forward only.
6. Report the final local/remote relationship.

Safety rules:

- Never use `reset --hard` to make branches match.
- Never overwrite or stash user changes implicitly.
- Never create merge commits during synchronization.

### Phase 5: Add `post-merge-cleanup`

Purpose: clean up a feature branch after its pull request has been merged.

Behavior:

1. Resolve and verify the merged PR or merged branch.
2. Stop if the PR is not merged.
3. Switch to and fast-forward the primary branch.
4. Fetch with pruning.
5. Delete the local feature branch only after merge ancestry is verified.
6. Delete the remote branch only if it still exists and the user's request
   includes remote cleanup.
7. Treat an already-deleted remote branch as an idempotent success.

Safety rules:

- Never force-delete an unmerged branch.
- Never delete the current branch.
- Never treat a missing remote ref as failure after a confirmed merge.

## Commit structure

Keep changes reviewable in this order:

1. `fix(skills): align workflow commands with tool permissions`
2. `test(validation): add executable skill contract checks`
3. `ci: run the repository skill validator`
4. `docs: document installation and permission boundaries`
5. `feat: add safe main branch synchronization skill`
6. `feat: add post-merge branch cleanup skill`

The license and first version tag are separate owner-approved delivery actions,
not bundled into an unrelated commit.

## Success criteria

- All 18 existing skills pass the new validator.
- Every executable shell command is permitted by its skill declaration.
- CI runs the same validator and tests available locally.
- README inventory cannot silently drift from the filesystem.
- Claude Code and Codex installation paths are documented without unsupported
  claims.
- New Git lifecycle skills fail safely on dirty, divergent, unmerged, or
  already-cleaned-up states.
- No package runtime, installer service, or unrelated skill is introduced.
