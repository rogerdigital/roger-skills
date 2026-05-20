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
| [adr](skills/adr/SKILL.md) | `/adr` | Create an Architecture Decision Record |
| [spec](skills/spec/SKILL.md) | `/spec` | Write a requirements specification with acceptance criteria |

## Installation

Copy the skills you want into your project or home directory:

```bash
# Project-level (affects this repo only)
cp -r skills/commit .claude/skills/

# Personal (affects all projects)
cp -r skills/commit ~/.claude/skills/
```

## Design guidelines

Follow these principles when adding or editing a skill:

- **Process-driven, not prompt-driven.** Each skill defines an explicit step-by-step workflow, not a vague "help me do X". Steps are ordered and checkable.
- **Constraints first.** Hard limits (what the skill must never do) belong in the skill itself, not in a separate global config. This makes skills portable.
- **Minimal tool permissions.** `allowed-tools` grants only the specific commands the skill needs — not broad `Bash(*)`.
- **Triggerable by natural language.** The `description` field covers realistic phrasings a developer would actually use, so the agent can auto-invoke without a slash command.
- **Single responsibility.** One skill, one workflow. If a skill is doing two separate things, split it.
- **Language-agnostic where possible.** Skills that work across multiple languages (debug, refactor, docstring) should detect the project's language rather than hardcode one.
