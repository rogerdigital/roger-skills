# Skill Quality and Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing skill collection executable under its declared permissions, enforce that contract locally and in CI, complete distribution documentation, and add safe main-sync and post-merge cleanup workflows.

**Architecture:** Keep skills as portable Markdown playbooks and add one repository-level Python validator as the quality boundary. The validator parses skill metadata, checks shell examples against `allowed-tools`, enforces README inventory consistency, and exposes the same entrypoint to local developers, unit tests, and GitHub Actions.

**Tech Stack:** Markdown, Python 3, PyYAML 6.0.3, `unittest`, Git, GitHub Actions.

---

## File map

- Modify `skills/*/SKILL.md`: align executable commands, fence labels, and tool permissions.
- Create `requirements-dev.txt`: pin the validator's only development dependency.
- Create `scripts/validate_skills.py`: repository validation entrypoint and reusable validation functions.
- Create `tests/test_validate_skills.py`: temporary-repository unit tests for validator behavior.
- Modify `.github/workflows/validate.yml`: install the development dependency and run tests plus the validator.
- Modify `README.md`: document installation, updates, removal, permission impact, contribution checks, and new skills.
- Create `skills/sync-main/SKILL.md`: safe fast-forward synchronization workflow.
- Create `skills/post-merge-cleanup/SKILL.md`: verified, idempotent cleanup after merge.
- Do not create `LICENSE` until the repository owner explicitly chooses license terms.

### Task 1: Repair existing skill tool contracts

**Files:**
- Modify: `skills/changelog/SKILL.md`
- Modify: `skills/commit/SKILL.md`
- Modify: `skills/create-pr/SKILL.md`
- Modify: `skills/debug/SKILL.md`
- Modify: `skills/dep-update/SKILL.md`
- Modify: `skills/hotfix/SKILL.md`
- Modify: `skills/migrate/SKILL.md`
- Modify: `skills/postmortem/SKILL.md`
- Modify: `skills/pr-review/SKILL.md`
- Modify: `skills/refactor/SKILL.md`
- Modify: `skills/release-notes/SKILL.md`
- Modify: `skills/revert/SKILL.md`
- Modify: `skills/security-review/SKILL.md`
- Modify: `skills/simplify/SKILL.md`

- [ ] **Step 1: Record the current command and permission inventory**

Run:

```bash
rg -n '^allowed-tools:|^```(bash|sh)?$|^(git|gh|npm|yarn|pnpm|pip|poetry|go|cargo|composer|bundle|mvn|gradle|make|pytest|python)[[:space:]]' skills/*/SKILL.md
```

Expected: output includes the known mismatches in `create-pr`, `hotfix`, `release-notes`, and `revert`.

- [ ] **Step 2: Align existing declarations with required commands**

Apply these exact contract changes:

```text
changelog:
  add Bash(git describe *)

create-pr:
  add Bash(git status *)

debug:
  add the explicit shared test set below

Shared test permissions for workflows that run project tests:
  Bash(npm test *) Bash(yarn test *) Bash(pnpm test *) Bash(make test *)
  Bash(cargo test *) Bash(go test *) Bash(pytest *) Bash(python -m pytest *)
  Bash(python3 -m pytest *) Bash(rspec *) Bash(bundle exec rspec *)
  Bash(mvn test *) Bash(gradle test *)

dep-update:
  replace broad package-manager permissions with the read-only commands used
  by the workflow: outdated, audit, list, show, and dependencyUpdates

hotfix:
  add Bash(git fetch *) Bash(git pull *) and the explicit shared test set;
  remove Bash(gh issue *) because issue creation is not an automatic step of
  the workflow

pr-review:
  replace Bash(gh pr *), Bash(gh pr comment *), and Bash(gh pr review *) with
  Bash(gh pr view *) Bash(gh pr diff *) Bash(gh pr checks *)

release-notes:
  add Bash(git describe *) Bash(git show *) Bash(head *)

revert:
  add Bash(git commit *) and the explicit shared test set;
  replace Bash(gh pr *) with Bash(gh pr view *) Bash(gh pr create *)

simplify, refactor, and test-gen:
  replace Bash(*test*) and Bash(*spec*) with the explicit shared test set

migrate:
  add Bash(grep -i migrat) for the documented migration-file filters

security-review:
  replace Bash(gh pr *) with Bash(gh pr diff *)
```

For `dep-update`, use this complete `allowed-tools` value:

```yaml
allowed-tools: Bash(npm outdated *) Bash(npm audit *) Bash(yarn outdated *) Bash(yarn audit *) Bash(pnpm outdated *) Bash(pnpm audit *) Bash(pip list *) Bash(pip-audit *) Bash(poetry show *) Bash(go list *) Bash(cargo outdated *) Bash(cargo audit *) Bash(composer outdated *) Bash(composer audit *) Bash(bundle outdated *) Bash(bundle audit *) Bash(mvn versions:display-dependency-updates *) Bash(gradle dependencyUpdates *) Bash(cat *) Bash(find *) Bash(grep *) Bash(git log *) Read WebFetch
```

- [ ] **Step 3: Make executable and illustrative fences unambiguous**

Change every executable shell example to `bash`. Label every previously
unlabelled commit-message, Markdown-template, and output example as `text` or
`markdown`. In `dep-update`, use a four-backtick `markdown` outer fence so its
three-backtick command examples remain valid nested Markdown. Replace the
heredoc commit examples in `commit` and `revert` with commands that stay inside
the declared Git permission:

```bash
git commit -m "<type>(<scope>): <summary>"
git commit -m "<type>(<scope>): <summary>" -m "<body>"
git commit --amend -m "revert(<scope>): roll back <description>" -m "Reverting because: <reason>. Original commit: <hash>. Original PR: #<number>. Verification: <check>."
```

The second `-m "<body>"` on the regular commit is optional for non-obvious
changes.

- [ ] **Step 4: Verify the repaired Markdown manually**

Run:

```bash
git diff --check
rg -n '^allowed-tools:' skills/*/SKILL.md
git diff -- skills
```

Expected: no whitespace errors; every permission change is traceable to a
documented command; review skills no longer have remote-write permissions.

- [ ] **Step 5: Commit the contract repair**

```bash
git add skills
git commit -m "fix(skills): align workflow commands with tool permissions"
```

### Task 2: Add failing validator tests

**Files:**
- Create: `requirements-dev.txt`
- Create: `tests/test_validate_skills.py`
- Test: `tests/test_validate_skills.py`

- [ ] **Step 1: Pin the development dependency**

Create `requirements-dev.txt`:

```text
PyYAML==6.0.3
```

- [ ] **Step 2: Write temporary-repository test helpers**

Create `tests/test_validate_skills.py` with these imports and helpers:

```python
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_skills import validate_repository


def write_skill(
    root: Path,
    directory: str,
    *,
    name: str | None = None,
    description: str = "Run a safe repository check.",
    allowed_tools: str = "Bash(git status *) Read",
    body: str = "## Process\n\n```bash\ngit status\n```\n",
    security_audit: bool = False,
) -> None:
    skill_dir = root / "skills" / directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    audit_line = "security-audit: true\n" if security_audit else ""
    content = (
        "---\n"
        f"name: {name or directory}\n"
        f"description: {description}\n"
        f"allowed-tools: {allowed_tools}\n"
        f"{audit_line}"
        "---\n\n"
        f"{body}"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def write_readme(root: Path, *names: str) -> None:
    rows = "\n".join(
        f"| [{name}](skills/{name}/SKILL.md) | `/{name}` | Test skill |"
        for name in names
    )
    (root / "README.md").write_text(
        "# Skills\n\n| Skill | Trigger | Description |\n"
        "|---|---|---|\n"
        f"{rows}\n",
        encoding="utf-8",
    )
```

- [ ] **Step 3: Add contract and repository-invariant tests**

Add this test class below the helpers:

```python
class ValidateRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def errors(self) -> list[str]:
        return validate_repository(self.root)

    def test_accepts_valid_repository(self) -> None:
        write_skill(self.root, "status")
        write_readme(self.root, "status")
        self.assertEqual([], self.errors())

    def test_rejects_missing_frontmatter(self) -> None:
        path = self.root / "skills" / "broken" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("## Process\n", encoding="utf-8")
        write_readme(self.root, "broken")
        self.assertTrue(any("frontmatter" in error for error in self.errors()))

    def test_rejects_duplicate_names(self) -> None:
        write_skill(self.root, "first", name="duplicate")
        write_skill(self.root, "second", name="duplicate")
        write_readme(self.root, "first", "second")
        self.assertTrue(any("duplicate skill name" in error for error in self.errors()))

    def test_rejects_directory_name_mismatch(self) -> None:
        write_skill(self.root, "status", name="different")
        write_readme(self.root, "status")
        self.assertTrue(any("must match directory" in error for error in self.errors()))

    def test_rejects_empty_body(self) -> None:
        write_skill(self.root, "empty", body="\n")
        write_readme(self.root, "empty")
        self.assertTrue(any("body is empty" in error for error in self.errors()))

    def test_rejects_dangerous_permission(self) -> None:
        write_skill(self.root, "danger", allowed_tools="Bash(git push --force *)")
        write_readme(self.root, "danger")
        self.assertTrue(any("dangerous command" in error for error in self.errors()))

    def test_rejects_leading_wildcard_permission(self) -> None:
        write_skill(self.root, "broad", allowed_tools="Bash(*test*) Read")
        write_readme(self.root, "broad")
        self.assertTrue(any("leading wildcard" in error for error in self.errors()))

    def test_rejects_missing_shell_permission(self) -> None:
        write_skill(self.root, "status", allowed_tools="Read")
        write_readme(self.root, "status")
        self.assertTrue(any("not covered by allowed-tools" in error for error in self.errors()))

    def test_requires_permission_for_each_pipeline_command(self) -> None:
        body = "## Process\n\n```bash\ngit tag --list | head -10\n```\n"
        write_skill(
            self.root,
            "tags",
            allowed_tools="Bash(git tag *)",
            body=body,
        )
        write_readme(self.root, "tags")
        self.assertTrue(any("head -10" in error for error in self.errors()))

    def test_rejects_unlabelled_shell_block(self) -> None:
        write_skill(self.root, "status", body="## Process\n\n```\ngit status\n```\n")
        write_readme(self.root, "status")
        self.assertTrue(any("shell block must be labelled" in error for error in self.errors()))

    def test_accepts_reasoned_ignore_marker(self) -> None:
        body = (
            "## Example\n\n"
            '<!-- skill-validator: ignore-shell reason="illustrative only" -->\n'
            "```bash\ngit status\n```\n"
        )
        write_skill(self.root, "status", allowed_tools="Read", body=body)
        write_readme(self.root, "status")
        self.assertEqual([], self.errors())

    def test_rejects_empty_ignore_reason(self) -> None:
        body = (
            "## Example\n\n"
            '<!-- skill-validator: ignore-shell reason="" -->\n'
            "```bash\ngit status\n```\n"
        )
        write_skill(self.root, "status", body=body)
        write_readme(self.root, "status")
        self.assertTrue(any("ignore-shell reason" in error for error in self.errors()))

    def test_rejects_stale_readme_inventory(self) -> None:
        write_skill(self.root, "status")
        write_readme(self.root)
        self.assertTrue(any("README skill inventory" in error for error in self.errors()))

    def test_allows_security_audit_secret_scan(self) -> None:
        write_skill(
            self.root,
            "security",
            description="Search for API keys and passwords in changed files.",
            security_audit=True,
        )
        write_readme(self.root, "security")
        self.assertEqual([], self.errors())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests to verify the validator is not implemented**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validate_skills'`.

### Task 3: Implement the repository validator

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/validate_skills.py`
- Modify: `tests/test_validate_skills.py`
- Test: `tests/test_validate_skills.py`

#### Validator contract refinements

Keep the validator focused on executable Skill contracts; do not expand it into
a general Markdown or shell parser. The parser must apply these rules:

- A present `allowed-tools` value must be a string. `Bash(...)` permissions are
  literal command prefixes, optionally followed by one final ` *` argument
  wildcard. Reject empty patterns, leading, embedded, or multiple `*`, plus
  `?`, `[`, and `]`; compare commands exactly or to the literal prefix followed
  by a space.
- Validate every command segment in labelled `bash` and `sh` blocks. The fixed
  command-name list is only for identifying executable shell examples in
  unlabelled fences. Use a small character scanner to split only unquoted,
  unescaped command connectors (`&&`, `||`, `|`, `|&`, `;`, and background
  `&`) while preserving original redirection adjacency and stopping at
  comments. A `#` starts a comment only at a shell word boundary (line start or
  after whitespace/control separator); it is literal mid-word. Since the
  scanner owns comments, later `shlex` tokenization uses `comments=False`.
  An unterminated quote is a validation error, never a whitespace-split
  fallback. For each labelled
  command, parse and normalize first, always inspect dangerous behavior next,
  and only then let a reasoned ignore marker skip permission coverage.
- Parse CommonMark fences with up to three leading spaces, backticks or tildes,
  an opening length of at least three, and a same-character closing fence at
  least as long. Report unclosed fences and retain original `SKILL.md` line
  numbers in errors. This preserves four-backtick Markdown templates that
  include triple-backtick examples.
- Restrict sensitive-intent matching to sentence/clause-local spans that never
  cross `.`, `!`, `?`, `;`, `,`, or newlines. Apply a negation only when it
  directly precedes the matched action in that clause; it must not suppress an
  unrelated later collection or exfiltration action. ACTION alternatives use
  word boundaries to avoid substring false positives. `security-audit: true`
  only exempts those content-intent checks.
- Treat `chmod` modes with a final numeric digit of `2`, `3`, `6`, or `7` as
  world-writable, while allowing `755`. Derive the mode from parsed `chmod`
  tokens after skipping common recursive, force, verbosity, and `--` options;
  this includes combined short flags such as `-Rv`; do not rely on a raw
  command regex. Reject symbolic `+`/`=` clauses with `w` when who is omitted
  or any valid who-class `[ugoa]+` contains `o` or `a`, but allow owner/group-
  only clauses such as `u+w` and `ug+w`.
- Inspect dangerous behavior in normalized body commands as well as declared
  permissions: force pushes include `--force`, `-f`, and later force options;
  dangerous checks survive wildcard permissions and ignore markers. Unwrap
  leading environment assignments plus `command` and `env` wrappers before
  inspection. Detect recursive `rm` from long, short, and combined flags.
  Treat `&` as a separator only when it is not immediately adjacent to a
  redirection character; whitespace in `& >` therefore makes it a separator,
  unlike `>&`, `&>`, `2>&1`, or `<&`.
- Read inventory links only from the `## Skills` README section. Require each
  link label to equal its directory, reject duplicates, and compare the linked
  directory set exactly with `skills/*`.

The regression suite contains 40 tests total: the original repository,
frontmatter, dangerous-tool, pipeline, ignore-marker, inventory, audit, and
leading-wildcard cases; plus labelled unknown-command coverage; indented,
tilde, longer-close, and unclosed fences; character-class and question-mark
permission patterns; invalid shell syntax; protective sensitive text; genuine
credential collection and exfiltration; real line numbers; safe and unsafe
`chmod` modes (including options and combined who-classes that grant
other/all write access); non-string and empty `allowed-tools` Bash patterns;
match-scoped negation and ACTION-boundary cases; dangerous body commands under
wildcards and ignore markers; standalone background separators and preserved
redirections; quoted/escaped connectors; wrapper force pushes; recursive rm;
combined chmod flags; shell comment boundaries; and duplicate and mismatched
README entries.

- [ ] **Step 1: Add the validator module and data model**

Create an empty `scripts/__init__.py`. Start `scripts/validate_skills.py` with:

```python
from __future__ import annotations

import fnmatch
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
BASH_PERMISSION_RE = re.compile(r"Bash\(([^)]*)\)")
README_SKILL_RE = re.compile(r"\[([^]]+)]\(skills/([^/]+)/SKILL\.md\)")
IGNORE_RE = re.compile(
    r'^<!-- skill-validator: ignore-shell reason="([^"]*)" -->$'
)
KNOWN_SHELL_COMMANDS = {
    "bundle", "cargo", "cat", "composer", "find", "gh", "git", "go",
    "gradle", "grep", "head", "ls", "make", "mvn", "npm", "pip",
    "pip-audit", "pnpm", "poetry", "pytest", "python", "python3", "sed",
    "wc", "yarn",
}
DANGEROUS_TOOLS = (
    r"rm\s+-[rf]{1,2}f?",
    r"--no-verify",
    r"curl\b.*\|\s*(?:bash|sh)",
    r"wget\b.*\|\s*(?:bash|sh)",
    r"sudo\s+rm",
    r":\s*\(\)\s*\{.*\}\s*;",
    r"mkfs\b",
    r"dd\s+if=",
)
ACTION = (
    r"\b(?:search(?:\s+for)?|find|locate|read|extract|collect|gather|grep|scan|"
    r"look\s+for|retrieve|fetch|access|dump|list|cat|harvest)\b"
)
SENSITIVE_TARGETS = (
    (r"(?:api[\s_-]*key|access[\s_-]*key|secret[\s_-]*key|private[\s_-]*key|auth(?:entication)?[\s_-]*token|bearer[\s_-]*token|\.env\b|credential|password|passwd|passphrase)", "credentials/secrets"),
    (r"(?:personal[\s_-]*info(?:rmation)?|id[\s_-]*card|passport\b|date[\s_-]*of[\s_-]*birth|\bssn\b|social[\s_-]*security|home[\s_-]*address|phone[\s_-]*number|mobile[\s_-]*number)", "personal information"),
    (r"(?:account[\s_-]*number|credit[\s_-]*card|bank[\s_-]*account|billing[\s_-]*info(?:rmation)?|payment[\s_-]*info(?:rmation)?|card[\s_-]*number|cvv\b|routing[\s_-]*number)", "account/financial information"),
    (r"(?:confidential|proprietary|internal[\s_-]*doc(?:ument)?|client[\s_-]*data|employee[\s_-]*record|salary\b|payroll\b|trade[\s_-]*secret|nda\b)", "company/work information"),
)
EXFILTRATION = (
    (r"(?:send|upload|post|transmit|exfiltrate|forward)\s+(?:\w+\s+)*?to\s+https?://", "exfiltration to external URL"),
    (r"curl\b[^`\n]*-[xX]\s*POST[^`\n]*https?://", "curl POST to external URL"),
    (r"wget\b[^`\n]*--post[^`\n]*https?://", "wget POST to external URL"),
)


@dataclass(frozen=True)
class Skill:
    path: Path
    metadata: dict[str, Any]
    body: str
    content: str
```

- [ ] **Step 2: Implement metadata and repository validation**

Add these functions:

```python
def load_skill(path: Path, errors: list[str]) -> Skill | None:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        errors.append(f"{path}: missing or malformed frontmatter")
        return None
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        errors.append(f"{path}: invalid YAML frontmatter: {error}")
        return None
    if not isinstance(metadata, dict):
        errors.append(f"{path}: frontmatter must be a YAML mapping")
        return None
    body = content[match.end():].strip()
    if not metadata.get("name"):
        errors.append(f"{path}: missing required field 'name'")
    if not metadata.get("description"):
        errors.append(f"{path}: missing required field 'description'")
    if metadata.get("name") and metadata["name"] != path.parent.name:
        errors.append(
            f"{path}: skill name '{metadata['name']}' must match directory "
            f"'{path.parent.name}'"
        )
    if not body:
        errors.append(f"{path}: skill body is empty")
    return Skill(path=path, metadata=metadata, body=body, content=content)


def validate_names(skills: list[Skill], errors: list[str]) -> None:
    by_name: dict[str, list[Path]] = {}
    for skill in skills:
        name = skill.metadata.get("name")
        if isinstance(name, str) and name:
            by_name.setdefault(name, []).append(skill.path)
    for name, paths in sorted(by_name.items()):
        if len(paths) > 1:
            errors.append(
                f"duplicate skill name '{name}': "
                + ", ".join(str(path) for path in paths)
            )


def validate_readme(root: Path, skills: list[Skill], errors: list[str]) -> None:
    readme = root / "README.md"
    if not readme.exists():
        errors.append(f"{readme}: missing README skill inventory")
        return
    entries = README_SKILL_RE.findall(readme.read_text(encoding="utf-8"))
    linked_names = {directory for _, directory in entries}
    actual_names = {skill.path.parent.name for skill in skills}
    if linked_names != actual_names:
        missing = sorted(actual_names - linked_names)
        stale = sorted(linked_names - actual_names)
        errors.append(
            "README skill inventory does not match skills directory; "
            f"missing={missing}, stale={stale}"
        )
```

- [ ] **Step 3: Implement permission and shell-block validation**

Add these functions:

```python
def bash_permissions(skill: Skill) -> list[str]:
    return BASH_PERMISSION_RE.findall(str(skill.metadata.get("allowed-tools", "")))


def command_is_allowed(command: str, permissions: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(command, pattern)
        or fnmatch.fnmatchcase(f"{command} ", pattern)
        for pattern in permissions
    )


def command_segments(line: str) -> list[str]:
    segments = re.split(r"\s*(?:&&|\|\||\||;)\s*", line)
    commands: list[str] = []
    for segment in segments:
        stripped = segment.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            tokens = stripped.split()
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens.pop(0)
        if tokens and tokens[0] in KNOWN_SHELL_COMMANDS:
            commands.append(" ".join(tokens))
    return commands


def fenced_blocks(body: str) -> list[tuple[str, str, str | None]]:
    lines = body.splitlines()
    blocks: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(`{3,})([A-Za-z0-9_-]*)\s*$", lines[index])
        if not match:
            index += 1
            continue
        fence = match.group(1)
        language = match.group(2)
        previous = lines[index - 1].strip() if index else ""
        ignore_reason: str | None = None
        if previous.startswith("<!-- skill-validator: ignore-shell"):
            ignore = IGNORE_RE.match(previous)
            ignore_reason = ignore.group(1) if ignore else ""
        block_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index] != fence:
            block_lines.append(lines[index])
            index += 1
        blocks.append((language, "\n".join(block_lines), ignore_reason))
        index += 1
    return blocks


def validate_shell_contract(skill: Skill, errors: list[str]) -> None:
    permissions = bash_permissions(skill)
    for permission in permissions:
        if permission.startswith("*"):
            errors.append(
                f"{skill.path}: leading wildcard permission is not allowed: "
                f"'{permission}'"
            )
    for pattern in DANGEROUS_TOOLS:
        if re.search(pattern, " ".join(permissions), re.IGNORECASE):
            errors.append(
                f"{skill.path}: dangerous command in allowed-tools matched "
                f"'{pattern}'"
            )
    for language, block, ignore_reason in fenced_blocks(skill.body):
        commands = [
            command
            for line in block.splitlines()
            for command in command_segments(line)
        ]
        if language == "" and commands:
            errors.append(f"{skill.path}: shell block must be labelled bash or sh")
            continue
        if ignore_reason == "":
            errors.append(f"{skill.path}: ignore-shell reason must be non-empty")
            continue
        if language not in {"bash", "sh"} or ignore_reason is not None:
            continue
        for command in commands:
            if not command_is_allowed(command, permissions):
                errors.append(
                    f"{skill.path}: command '{command}' is not covered by allowed-tools"
                )
```

- [ ] **Step 4: Preserve malicious-intent and exfiltration checks**

Add:

```python
def validate_content_security(skill: Skill, errors: list[str]) -> None:
    if skill.metadata.get("security-audit"):
        return
    check_text = skill.content.lower()
    for target_pattern, category in SENSITIVE_TARGETS:
        combined = rf"{ACTION}.{{0,120}}{target_pattern}"
        if re.search(combined, check_text, re.IGNORECASE | re.DOTALL):
            errors.append(
                f"{skill.path}: suspicious intent to collect {category}"
            )
    for pattern, label in EXFILTRATION:
        if re.search(pattern, check_text, re.IGNORECASE):
            errors.append(f"{skill.path}: suspicious intent: {label}")


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    paths = sorted((root / "skills").glob("*/SKILL.md"))
    if not paths:
        return [f"{root / 'skills'}: no SKILL.md files found"]
    skills = [
        skill
        for path in paths
        if (skill := load_skill(path, errors)) is not None
    ]
    validate_names(skills, errors)
    for skill in skills:
        validate_shell_contract(skill, errors)
        validate_content_security(skill, errors)
    validate_readme(root, skills, errors)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        print("Validation failed:\n")
        for error in errors:
            print(f"  x {error}")
        return 1
    count = len(list((root / "skills").glob("*/SKILL.md")))
    print(f"All {count} SKILL.md files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run focused tests and repair only implementation defects**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: 40 tests pass.

- [ ] **Step 6: Run the validator on the real repository**

Run:

```bash
python3 scripts/validate_skills.py
```

Expected: `All 18 SKILL.md files passed validation.`

- [ ] **Step 7: Commit tests and validator**

```bash
git add requirements-dev.txt scripts tests
git commit -m "test(validation): add executable skill contract checks"
```

### Task 4: Make CI use the local validator

**Files:**
- Modify: `.github/workflows/validate.yml`
- Test: `tests/test_validate_skills.py`

- [ ] **Step 1: Replace the inline validator with explicit setup and checks**

Keep the existing workflow triggers and replace the job steps with:

```yaml
steps:
  - uses: actions/checkout@v4

  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
      cache: pip

  - name: Install validation dependencies
    run: python -m pip install -r requirements-dev.txt

  - name: Run validator tests
    run: python -m unittest discover -s tests -p 'test_*.py' -v

  - name: Validate skills
    run: python scripts/validate_skills.py
```

- [ ] **Step 2: Run the same commands locally**

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills.py
```

Expected: dependency installation succeeds, 40 tests pass, and all 18 skills
pass repository validation.

- [ ] **Step 3: Commit the CI entrypoint**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: run the repository skill validator"
```

### Task 5: Complete installation and permission documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the single installation example with platform sections**

Document these concrete copy-based workflows:

```bash
# Claude Code, project-level
mkdir -p .claude/skills
cp -R skills/commit .claude/skills/commit

# Claude Code, user-level
mkdir -p ~/.claude/skills
cp -R skills/commit ~/.claude/skills/commit

# Codex, user-level
mkdir -p ~/.codex/skills
cp -R skills/commit ~/.codex/skills/commit
```

State that project-level Codex installation must follow the Codex version's
documented discovery path; do not invent a path that has not been verified.

- [ ] **Step 2: Add update and removal instructions**

Add:

```bash
# Update an installed copy
cp -R skills/commit ~/.codex/skills/commit

# Remove an installed copy
rm -rf ~/.codex/skills/commit
```

Precede removal with an explicit warning to verify the exact target directory.

- [ ] **Step 3: Add a permission-impact table**

Classify every skill into one of these explicit levels:

```text
Read-only:
  dep-update, migrate, postmortem, pr-review, security-review

Local files:
  adr, changelog, debug, docstring, refactor, release-notes, simplify, spec,
  test-gen

Local Git:
  commit

Remote Git or GitHub:
  create-pr, hotfix, revert
```

Explain that a Skill's `allowed-tools` is a maximum capability declaration;
the workflow rules still determine when the action is appropriate.

- [ ] **Step 4: Add contributor validation instructions and licensing status**

Add:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills.py
```

State plainly that no reuse license has been selected yet. Do not add license
terms or imply that public source automatically grants redistribution rights.

- [ ] **Step 5: Verify documentation and commit**

Run:

```bash
python3 scripts/validate_skills.py
git diff --check
```

Expected: all 18 skills pass and Markdown has no whitespace errors.

Commit:

```bash
git add README.md
git commit -m "docs: document installation and permission boundaries"
```

### Task 6: Add safe main branch synchronization

**Files:**
- Create: `skills/sync-main/SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Add the new skill to README before creating it**

Add this row to the Skills table:

```markdown
| [sync-main](skills/sync-main/SKILL.md) | `/sync-main` | Safely fast-forward the primary branch from its remote |
```

Also add `sync-main` to the `Local Git` permission-impact group because it
fetches and fast-forwards local refs but does not write remote refs.

- [ ] **Step 2: Run validation to prove inventory drift is caught**

Run:

```bash
python3 scripts/validate_skills.py
```

Expected: FAIL with a README inventory mismatch showing stale `sync-main`.

- [ ] **Step 3: Create the synchronization workflow**

Create `skills/sync-main/SKILL.md`:

```markdown
---
name: sync-main
description: Safely synchronize a repository's primary branch with its remote using fast-forward only. Triggers on "sync main", "update main branch", "pull latest main", "同步 main", "同步主分支".
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
```

- [ ] **Step 4: Validate and commit**

Run:

```bash
python3 scripts/validate_skills.py
git diff --check
```

Expected: all 19 skills pass validation.

Commit:

```bash
git add README.md skills/sync-main/SKILL.md
git commit -m "feat: add safe main branch synchronization skill"
```

### Task 7: Add verified post-merge cleanup

**Files:**
- Create: `skills/post-merge-cleanup/SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Add the new skill to README before creating it**

Add:

```markdown
| [post-merge-cleanup](skills/post-merge-cleanup/SKILL.md) | `/post-merge-cleanup [PR]` | Safely remove merged local and remote branches |
```

Also add `post-merge-cleanup` to the `Remote Git or GitHub` permission-impact
group because it may delete a remote branch when explicitly requested.

- [ ] **Step 2: Run validation to prove inventory drift is caught**

Run:

```bash
python3 scripts/validate_skills.py
```

Expected: FAIL with a README inventory mismatch showing stale
`post-merge-cleanup`.

- [ ] **Step 3: Create the cleanup workflow**

Create `skills/post-merge-cleanup/SKILL.md`:

```markdown
---
name: post-merge-cleanup
description: Clean up local and remote feature branches only after verifying their pull request was merged. Triggers on "clean up merged branch", "post-merge cleanup", "delete merged branch", "已合并，清理分支", "清理已合并分支".
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
```

- [ ] **Step 4: Validate and commit**

Run:

```bash
python3 scripts/validate_skills.py
git diff --check
```

Expected: all 20 skills pass validation.

Commit:

```bash
git add README.md skills/post-merge-cleanup/SKILL.md
git commit -m "feat: add post-merge branch cleanup skill"
```

### Task 8: Final verification and owner decisions

**Files:**
- Verify: all changed files
- Optional after explicit owner choice: `LICENSE`

- [ ] **Step 1: Run the complete local verification suite**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills.py
git diff --check main...HEAD
git status --short --branch
```

Expected: 40 tests pass, all 20 skills pass, no whitespace errors, and the
worktree is clean.

- [ ] **Step 2: Review the commit series**

```bash
git log --oneline main..HEAD
git diff --stat main...HEAD
```

Expected: the design commit plus the six implementation commits appear in
dependency order; only the documented files changed.

- [ ] **Step 3: Request the license decision**

Present these choices without creating a file:

```text
MIT: short and permissive.
Apache-2.0: permissive with an explicit patent grant.
No redistribution license: source remains visible but reuse rights stay reserved.
```

Create and commit `LICENSE` only after the owner explicitly selects one.

- [ ] **Step 4: Defer version tagging until merge**

Do not create a tag on the feature branch. After the changes are merged, select
a semantic version based on repository policy, generate the changelog, and tag
the merge commit as a separate release action.
