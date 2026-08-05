---
name: release-notes
description: Generate user-facing release notes for a new version — translates commits since the last tag into a concise, non-technical summary grouped by audience impact. Triggers on "write release notes", "generate release notes", "draft release", "publish notes", "what to tell users".
argument-hint: "[version or since-tag, e.g. v1.2.0 or v1.1.0..v1.2.0]"
allowed-tools: Bash(git log *) Bash(git tag *) Bash(git diff *) Read Write
---

Generate user-facing release notes for: `$ARGUMENTS`

## Purpose

Unlike a CHANGELOG (developer-facing, commit-derived, comprehensive), release notes are **user-facing**: they explain what changed in language a user of the product cares about. They are selective (highlight notable changes, skip noise) and structured by impact, not by commit type.

## Process

### 1. Determine the version and range

If `$ARGUMENTS` looks like a range (`A..B`), use it directly:
```bash
git log <start>..<end> --oneline
```

If `$ARGUMENTS` is a tag or version (`v1.2.0`), treat it as the release being cut, and find the previous tag to compute the range:
```bash
git tag --sort=-v:refname | head -10
git log <previous-tag>..<target> --oneline
```

If no argument is given, compute from the most recent tag to HEAD:
```bash
git describe --tags --abbrev=0
git log <last-tag>..HEAD --oneline
```

Determine the target version string (e.g. `v1.2.0`). If it cannot be inferred, ask the user.

### 2. Gather commit context

```bash
git log <range> --pretty=format:"%h %s (%an)" --no-merges
git diff <range> --stat
```

For commits with vague subjects, inspect the diff for real impact:
```bash
git show <hash> --stat
```

### 3. Classify each change by user impact

Apply this filter — this is the core difference from a changelog:

| Impact | Include? | Examples |
|---|---|---|
| **New capability** | ✅ Always | New command, new API endpoint, new config option |
| **Behavior change** | ✅ Always, flag as breaking | Default changed, removed option, renamed flag |
| **Bug fix** | ✅ If user-visible | Crashes, wrong output, broken workflow |
| **Performance** | ✅ If measurable | "50% faster cold start" |
| **Security** | ✅ Always, with severity | CVE fix, auth bypass |
| **Deprecation** | ✅ Always | "Will be removed in v2.0" |
| **Internal refactor** | ❌ Skip unless user-visible | Code cleanup, test additions |
| **CI/chore** | ❌ Skip | Build config, dependency bumps with no API change |
| **Docs** | ❌ Skip unless new guide | README tweaks |

When in doubt, ask: *Would a user of this product change their behavior because of this?* If no, drop it.

### 4. Draft the notes

Group by audience-relevant sections, not by commit type. Common structure (omit empty sections):

```markdown
# Release v1.2.0 — <YYYY-MM-DD>

## Highlights

<2-4 sentences. The one thing users should know. Lead with the most impactful change.>

## New

- **Feature name** — one-sentence description of what it does and why it matters. (#PR)
- <next feature>

## Improvements

- <what got better, in user terms>. (#PR)

## Fixes

- <what was broken and is now correct>. (#PR)

## Breaking Changes

⚠️ **Action required.**

- **<change>** — what the user must do to adapt. Old behavior: X. New behavior: Y. Migration: Z. (#PR)

## Security

- <vulnerability summary and severity>. Users should upgrade immediately. (#PR)

## Deprecations

- `<thing>` is deprecated and will be removed in <version>. Use <alternative> instead.

---

[Full changelog](<compare-url>)
```

Writing rules:
- Lead with the **impact** (what the user can now do, or what stopped breaking), not the implementation.
- Each bullet: one sentence, plain language, no internal jargon.
- Include a PR or commit reference at the end of each line for traceability.
- If a breaking change, explain the **migration** explicitly — don't just say "we changed X".
- For security fixes, state severity and whether upgrading is urgent.

### 5. Sanity check before writing

Ask yourself:
- Could a non-contributor understand every line?
- Is the Highlights section accurate to the single most important change?
- Did I drop pure-internal changes?
- Are breaking changes impossible to miss?
- Did I avoid duplicating a CHANGELOG entry verbatim (release notes should be reworded for users)?

### 6. Write the file

- If a `RELEASE_NOTES.md` exists, append a new section at the top (below any header), newest version first.
- If a `CHANGELOG.md` exists but no `RELEASE_NOTES.md`, prefer creating `RELEASE_NOTES.md` rather than mixing audiences in one file. Note this to the user.
- If neither exists, create `RELEASE_NOTES.md`.

## Rules

- **Audience is the user, not the developer.** Translate implementation detail into user impact. "Refactored query planner" → "Complex queries now run up to 40% faster."
- **Selectivity over completeness.** A release note that buries the headline under 30 minor fixes is worse than none. If there are many minor fixes, summarize: "15 bug fixes, see changelog for details."
- **Never invent impact.** If a commit's user-visible effect is unclear, say so or drop it. Do not fabricate performance numbers or feature claims.
- **Breaking changes are non-negotiable to include.** If unsure whether something is breaking, include it with "Potentially breaking:" rather than omit.
- **Do not copy commit subjects.** "fix: handle nil in foo" is a commit subject; the release note is "Fixed a crash when processing empty input to `foo`."
- Keep the Highlights section to at most 4 sentences. Force a choice about what matters most.
