---
name: dep-update
description: Analyze outdated dependencies and produce a prioritized batch upgrade plan — groups safe updates, isolates risky ones, and includes verification steps. Triggers on "update dependencies", "upgrade deps", "outdated packages", "dependency audit", "update packages".
argument-hint: "[package manager or directory path]"
allowed-tools: Bash(npm outdated *) Bash(npm audit *) Bash(yarn outdated *) Bash(yarn audit *) Bash(pnpm outdated *) Bash(pnpm audit *) Bash(pip list *) Bash(pip-audit *) Bash(poetry show *) Bash(go list *) Bash(cargo outdated *) Bash(cargo audit *) Bash(composer outdated *) Bash(composer audit *) Bash(bundle outdated *) Bash(bundle audit *) Bash(mvn versions:display-dependency-updates *) Bash(gradle dependencyUpdates *) Bash(cat *) Bash(find *) Bash(grep *) Bash(git log *) Read WebFetch
---

Analyze outdated dependencies and generate a strategic upgrade plan for `$ARGUMENTS` (or auto-detect from the current project).

## Process

### 1. Detect package manager

Identify the package manager by checking for manifest files:

| File | Package Manager |
|---|---|
| `package.json` + `package-lock.json` | npm |
| `package.json` + `yarn.lock` | yarn |
| `package.json` + `pnpm-lock.yaml` | pnpm |
| `requirements.txt` / `setup.py` / `pyproject.toml` (setuptools) | pip |
| `pyproject.toml` (poetry) + `poetry.lock` | poetry |
| `go.mod` | go mod |
| `Cargo.toml` | cargo |
| `composer.json` | composer |
| `Gemfile` | bundler |
| `pom.xml` | maven |
| `build.gradle` / `build.gradle.kts` | gradle |

If `$ARGUMENTS` specifies a package manager, use that. If multiple manifests exist, report all and ask which to process.

### 2. List outdated dependencies

Run the appropriate outdated command:

- **npm**: `npm outdated --json`
- **yarn**: `yarn outdated --json`
- **pnpm**: `pnpm outdated --format json`
- **pip**: `pip list --outdated --format json`
- **poetry**: `poetry show --outdated`
- **go**: `go list -m -u all`
- **cargo**: `cargo outdated --format json` (if installed) or parse `Cargo.toml` vs crates.io
- **composer**: `composer outdated --format json`
- **bundler**: `bundle outdated`
- **maven**: `mvn versions:display-dependency-updates -q`
- **gradle**: `gradle dependencyUpdates`

If the command is unavailable, fall back to manual comparison of lockfile versions against latest.

### 3. Categorize by risk and urgency

Classify each outdated dependency:

**Tier 1 — Security patches (urgent, do immediately)**
- Any update flagged by `npm audit`, `pip-audit`, `cargo audit`, or equivalent
- Dependencies with known CVEs in the current version
- Mark with severity: Critical / High / Medium / Low

**Tier 2 — Patch and minor updates (low risk, batch together)**
- Patch versions (1.2.3 → 1.2.4): bug fixes only
- Minor versions (1.2.x → 1.3.0): new features, backward-compatible
- Group these for a single batch upgrade

**Tier 3 — Major updates (breaking changes, isolate)**
- Major version bumps (1.x → 2.x)
- Requires changelog review and possibly code changes
- Each gets its own upgrade step

**Tier 4 — Deprecated packages (needs replacement)**
- Packages marked as deprecated in the registry
- Packages with no updates in 2+ years and known alternatives
- Requires migration to a replacement package

### 4. Research breaking changes for major updates

For each Tier 3 dependency:

- Check the package's CHANGELOG or release notes for breaking changes
- Identify migration guides if available
- List specific breaking changes that affect this project (check usage in codebase):
  ```bash
  grep -r "<package-name>" --include="*.{ts,js,py,go,rs,rb,java}" -l
  ```
- Estimate effort: **trivial** (rename/config change), **moderate** (API changes, some code updates), **significant** (architecture changes, major rewrite)

### 5. Identify deprecated packages needing replacement

For Tier 4 packages:
- Identify the recommended replacement
- Estimate migration effort
- Note if the deprecated package still receives security patches

### 6. Generate batch upgrade plan

Output in this format:

````markdown
## Dependency Upgrade Plan

**Project:** <name>
**Package Manager:** <detected>
**Total outdated:** <count>
**Generated:** <date>

---

## Batch 1: Security Patches (Priority: IMMEDIATE)

| Package | Current | Target | CVE/Advisory | Severity |
|---|---|---|---|---|
| <pkg> | <ver> | <ver> | <link> | Critical |

**Commands:**
```bash
<exact commands to run>
```

**Verify:**
- [ ] Run full test suite
- [ ] Check for runtime errors in <affected area>
- [ ] Confirm vulnerability is resolved: `<audit command>`

**Rollback:**
```bash
git checkout -- <lockfile> <manifest>
```

---

## Batch 2: Safe Updates (Priority: This Sprint)

| Package | Current | Target | Type |
|---|---|---|---|
| <pkg> | <ver> | <ver> | patch |
| <pkg> | <ver> | <ver> | minor |

**Commands:**
```bash
<exact commands to run>
```

**Verify:**
- [ ] Run full test suite
- [ ] Smoke-test: <specific feature that uses these deps>

**Rollback:**
```bash
git checkout -- <lockfile> <manifest>
```

---

## Batch 3: Major Update — <package name> (Priority: Plan & Schedule)

| Package | Current | Target | Breaking Changes |
|---|---|---|---|
| <pkg> | <ver> | <ver> | <summary> |

**Breaking changes that affect this project:**
- <specific change 1>: affects `<file>`
- <specific change 2>: affects `<file>`

**Migration steps:**
1. <step>
2. <step>

**Commands:**
```bash
<exact commands>
```

**Verify:**
- [ ] Run full test suite
- [ ] Manually test: <affected feature>
- [ ] Review: <specific behavior change>

---

## Batch 4: Package Replacements (Priority: Backlog)

| Deprecated | Replacement | Effort |
|---|---|---|
| <pkg> | <new-pkg> | moderate |

**Migration notes:**
- <guidance>

---

## Summary

| Tier | Count | Effort | Recommended Timeline |
|---|---|---|---|
| Security patches | <n> | <time> | Immediately |
| Safe updates | <n> | <time> | This sprint |
| Major updates | <n> | <time> | Next sprint |
| Replacements | <n> | <time> | Backlog |
````

## Rules

- **Do NOT** run upgrade commands. This skill produces a plan only — the user decides when to execute.
- **Do NOT** modify `package.json`, lockfiles, or any manifest. Read-only analysis only.
- Always provide exact, copy-pasteable commands for each batch.
- Group safe updates together to minimize CI cycles, but isolate anything that could break.
- If outdated information cannot be obtained (command not available, no network), state clearly what is missing and provide a partial plan.
- For monorepos, identify which workspace/module each dependency belongs to.
- Include rollback instructions for every batch.
- Flag any dependency that is pinned to an exact version with a comment explaining why — do not suggest upgrading pinned deps without noting the pin.
- When security patches are found, mark the overall plan as **URGENT** in the header.
