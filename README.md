# roger-skills

> A curated collection of reusable skills for AI coding agents, distilled from real-world development and engineering workflows.

## What is a skill?

A skill is a reusable prompt playbook stored as `SKILL.md` that an agent executes on demand. Skills follow the [agentskills.io](https://agentskills.io) open standard and are compatible with **Claude Code** and **OpenAI Codex CLI**.

Invoke with a slash command: `/commit`, `/debug my-file.go`, `/pr-review 42`

## Skills

| Skill | Trigger | Description |
|---|---|---|
| [commit](skills/commit/SKILL.md) | `/commit` | Stage changes and write a Conventional Commit message |
| [create-pr](skills/create-pr/SKILL.md) | `/create-pr` | Create a PR with title, description, and test plan |
| [pr-review](skills/pr-review/SKILL.md) | `/pr-review [PR]` | Review a PR for correctness, security, tests, and style |
| [security-review](skills/security-review/SKILL.md) | `/security-review` | Audit code for OWASP Top 10, secret leaks, and insecure patterns |
| [debug](skills/debug/SKILL.md) | `/debug` | Systematically diagnose a bug and fix the root cause |
| [refactor](skills/refactor/SKILL.md) | `/refactor [file]` | Improve code clarity without changing behavior |
| [simplify](skills/simplify/SKILL.md) | `/simplify [file]` | Remove unnecessary complexity — dead code, over-abstraction, YAGNI |
| [test-gen](skills/test-gen/SKILL.md) | `/test-gen [file]` | Generate unit tests covering happy path, edges, and errors |
| [docstring](skills/docstring/SKILL.md) | `/docstring [file]` | Add or improve docstrings and inline comments |
| [changelog](skills/changelog/SKILL.md) | `/changelog [tag]` | Generate a Keep a Changelog entry from recent commits |
| [migrate](skills/migrate/SKILL.md) | `/migrate [path]` | Audit database migrations for lock risks, data loss, and zero-downtime safety |
| [dep-update](skills/dep-update/SKILL.md) | `/dep-update` | Analyze outdated dependencies and produce a prioritized batch upgrade plan |
| [postmortem](skills/postmortem/SKILL.md) | `/postmortem` | Generate a blameless incident postmortem with timeline, RCA, and action items |
| [adr](skills/adr/SKILL.md) | `/adr` | Create an Architecture Decision Record |
| [spec](skills/spec/SKILL.md) | `/spec` | Write a requirements specification with acceptance criteria |
| [release-notes](skills/release-notes/SKILL.md) | `/release-notes [ver]` | Generate user-facing release notes grouped by impact, with breaking-change prominence |
| [hotfix](skills/hotfix/SKILL.md) | `/hotfix` | Ship an urgent production fix safely — triage, minimal fix, verify, PR |
| [revert](skills/revert/SKILL.md) | `/revert [commit]` | Safely revert a commit or range — checks downstream dependencies before acting |

## Installation

Copy only the skills you want to install.

### Claude Code

```bash
# Project-level
mkdir -p .claude/skills
cp -R skills/commit .claude/skills/commit

# User-level
mkdir -p ~/.claude/skills
cp -R skills/commit ~/.claude/skills/commit
```

### Codex

```bash
# User-level
mkdir -p ~/.codex/skills
cp -R skills/commit ~/.codex/skills/commit
```

For project-level Codex installation, follow the discovery path documented by
your installed Codex version. This repository does not assume an unverified
project-level path.

### Update or remove a skill

Run the copy command again to update an installed copy:

```bash
cp -R skills/commit ~/.codex/skills/commit
```

Before removal, verify that the target is the exact installed skill directory.
Then remove that copy:

```bash
rm -rf ~/.codex/skills/commit
```

## Permission impact

`allowed-tools` declares the maximum capability a skill may request. The
workflow rules inside each skill still determine whether an action is
appropriate in the current repository and when user confirmation is required.

| Level | Skills | Impact |
|---|---|---|
| Read-only | dep-update, migrate, postmortem, pr-review, security-review | Inspect files, repository state, dependencies, or GitHub metadata without writing project or remote state |
| Local files | adr, changelog, debug, docstring, refactor, release-notes, simplify, spec, test-gen | May edit files in the current worktree and run local checks |
| Local Git | commit | May stage and commit local changes without updating remote refs |
| Remote Git or GitHub | create-pr, hotfix, revert | May create or update remote Git/GitHub state as defined by the workflow |

## Contributing

Install the validation dependency, run the regression suite, and validate the
real skill collection before submitting changes:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills.py
```

No reuse license has been selected yet. Public source visibility does not by
itself grant permission to copy, modify, or redistribute this repository.

## Design guidelines

Follow these principles when adding or editing a skill:

- **Process-driven, not prompt-driven.** Each skill defines an explicit step-by-step workflow, not a vague "help me do X". Steps are ordered and checkable.
- **Constraints first.** Hard limits (what the skill must never do) belong in the skill itself, not in a separate global config. This makes skills portable.
- **Minimal tool permissions.** `allowed-tools` grants only the specific commands the skill needs — not broad `Bash(*)`.
- **Triggerable by natural language.** The `description` field covers realistic phrasings a developer would actually use, so the agent can auto-invoke without a slash command.
- **Single responsibility.** One skill, one workflow. If a skill is doing two separate things, split it.
- **Language-agnostic where possible.** Skills that work across multiple languages (debug, refactor, docstring) should detect the project's language rather than hardcode one.
