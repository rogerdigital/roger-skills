---
name: changelog
description: Generate a CHANGELOG entry for recent changes since the last release or tag. Groups commits by type, filters noise, and formats as Keep a Changelog markdown. Triggers on "generate changelog", "write changelog", "update CHANGELOG", "what changed since last release".
argument-hint: "[since-tag or commit range, e.g. v1.2.0 or v1.2.0..HEAD]"
allowed-tools: Bash(git log *) Bash(git tag *) Bash(git diff *)
---

Generate a CHANGELOG entry for the changes in: `$ARGUMENTS`

## Process

### 1. Determine the range

If `$ARGUMENTS` is provided, use it as the base ref:
```bash
git log $ARGUMENTS..HEAD --oneline
```

If not provided, find the most recent tag:
```bash
git describe --tags --abbrev=0
git log <last-tag>..HEAD --oneline
```

If there are no tags, use the full history:
```bash
git log --oneline
```

### 2. Get detailed commit info

```bash
git log <range> --pretty=format:"%h %s (%an)" --no-merges
```

Also look at the actual diff for context on significant changes:
```bash
git diff <range> --stat
```

### 3. Categorize and filter

Group commits using [Keep a Changelog](https://keepachangelog.com/) categories:

| Category | When to use |
|---|---|
| `Added` | New features, new APIs, new config options |
| `Changed` | Modified behavior, updated defaults, renamed things |
| `Deprecated` | Features that will be removed in a future version |
| `Removed` | Deleted features or APIs |
| `Fixed` | Bug fixes |
| `Security` | Vulnerability patches |

**Filter out** commits that don't belong in a user-facing changelog:
- `chore:`, `ci:`, `build:`, `test:` commits (unless they have user-visible impact)
- Merge commits
- Version bumps
- Minor refactors with no behavior change

### 4. Write the entry

Format:

```markdown
## [Unreleased] — YYYY-MM-DD

### Added
- Description of new feature. (#PR or commit hash)

### Fixed
- Description of bug fix. (#PR or commit hash)

### Changed
- Description of behavior change, including what changed and why.
```

Rules:
- Write in plain language for the end user, not the developer.
- Each line starts with a verb: "Add", "Fix", "Remove", "Update".
- Include PR or commit reference at the end of each line.
- If a change is breaking, prepend **BREAKING:** in bold.

### 5. Update CHANGELOG.md

If a `CHANGELOG.md` already exists, insert the new section below the `# Changelog` header (or at the top if no header). Do not overwrite existing entries.

If no `CHANGELOG.md` exists, create one with the standard Keep a Changelog header.
