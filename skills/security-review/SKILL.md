---
name: security-review
description: Security audit of code changes — checks for OWASP Top 10 vulnerabilities, dependency risks, secret leaks, and insecure patterns. Triggers on "security review", "check security", "audit security", "find vulnerabilities", "security audit".
argument-hint: "[file path, directory, or PR number]"
allowed-tools: Bash(git diff *) Bash(git log *) Bash(gh pr *) Read Grep
security-audit: true
---

Security review of: `$ARGUMENTS`

## Process

### 1. Determine scope

- If `$ARGUMENTS` is a PR number/URL, fetch the diff: `gh pr diff $ARGUMENTS`
- If it's a file/directory path, review those files
- If empty, review unstaged and staged changes: `git diff HEAD` and `git diff --staged`
- If reviewing a whole project, focus on entry points (API routes, controllers, middleware, config)

### 2. Scan for hardcoded secrets

Check for patterns in the diff/files:
- API keys, tokens, passwords, private keys
- `.env` files with real values (not placeholders)
- Connection strings with embedded credentials
- AWS/GCP/Azure credentials
- `BEGIN PRIVATE KEY`, `BEGIN RSA PRIVATE KEY`

### 3. Check OWASP Top 10

#### Injection (SQL, command, LDAP)
- String concatenation in queries/commands
- `eval()`, `exec()`, `system()`, `os.popen()`
- Unparameterized database queries
- Shell commands with user input

#### Broken Authentication
- Weak password policies
- Missing rate limiting on auth endpoints
- Plaintext password storage
- Session fixation vulnerabilities

#### Sensitive Data Exposure
- Missing encryption for data at rest/transit
- Verbose error messages leaking internals
- PII in logs
- Missing HTTPS enforcement

#### XXE
- XML parsing with external entity processing enabled
- Unvalidated XML input

#### Broken Access Control
- Missing authorization checks
- IDOR (Insecure Direct Object Reference)
- Privilege escalation paths

#### Security Misconfiguration
- Default credentials
- Unnecessary services enabled
- Missing security headers (CSP, HSTS, X-Frame-Options)
- Debug mode enabled in production

#### XSS
- Unescaped user input in HTML output
- `innerHTML`, `dangerouslySetInnerHTML`, `v-html`
- Missing output encoding

#### Insecure Deserialization
- `pickle`, `yaml.load()` without SafeLoader, `unserialize()` with user input
- Object deserialization without type checking

#### Known Vulnerabilities
- Outdated dependencies with known CVEs
- Check `package-lock.json`, `yarn.lock`, `Pipfile.lock`, `go.sum` for known vulnerable versions

#### Insufficient Logging
- Missing audit trails for security events
- Login failures not logged
- Sensitive operations not recorded

### 4. Check dependency security

- Flag any suspicious or known-vulnerable package versions
- Check for typosquatting in package names (e.g., `lodassh` vs `lodash`)
- Verify lockfiles are present and committed

### 5. Review security patterns

- **Input validation**: is user input validated at system boundaries?
- **Error handling**: do errors leak sensitive info?
- **File uploads**: are upload paths validated and sandboxed?
- **CORS**: are origins properly restricted?
- **Rate limiting**: are sensitive endpoints protected?

### 6. Output format

```
## Security Review Summary
<overall risk level: Critical / High / Medium / Low / Info>
<2-3 sentences summarizing findings>

## Critical (must fix)
- [file:line] Vulnerability description. Risk: <what could happen>. Fix: <how to fix>.

## High
- [file:line] Issue description. Risk: <impact>. Fix: <recommendation>.

## Medium
- [file:line] Issue description.

## Low / Info
- [file:line] Informational finding.

## Clean areas
- <areas checked with no issues found>
```

## Rules

- Be specific: always reference file paths and line numbers.
- Prioritize real risks over theoretical ones. Don't flag everything — focus on what's actually exploitable in context.
- If no issues are found, say so clearly rather than inventing problems.
- For each finding, explain the risk (what an attacker could do) and a concrete fix.
- Do not report false positives as findings. If unsure, flag as "Info" with the uncertainty noted.
