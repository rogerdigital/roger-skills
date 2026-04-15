---
name: docstring
description: Add or improve docstrings and inline comments for functions, classes, and modules. Follows language-specific conventions. Triggers on "add docstrings", "document this code", "add comments", "write documentation for this file".
argument-hint: "[file path or function name]"
---

Add or improve documentation for: `$ARGUMENTS`

## Process

### 1. Read the target

Read the file or function fully. Understand:
- What it does and why it exists
- Its inputs, outputs, and side effects
- Any non-obvious logic or decisions

### 2. Determine documentation style

Follow the convention used in the existing codebase. If none exists, use the language default:

| Language | Style |
|---|---|
| Python | Google-style docstrings (or NumPy if the project uses NumPy) |
| TypeScript / JavaScript | JSDoc (`/** ... */`) |
| Go | GoDoc (`// FunctionName ...`) |
| Rust | rustdoc (`/// ...` for public, `//! ...` for modules) |
| Java | Javadoc (`/** ... */`) |
| Ruby | YARD (`# @param`, `# @return`) |

### 3. What to document

**Always document:**
- Public functions, methods, and classes
- Non-obvious parameters (type, constraints, meaning)
- Return values
- Errors/exceptions that can be raised/returned
- Side effects (I/O, state mutations, network calls)

**Add inline comments for:**
- Complex algorithms — explain the approach, not the syntax
- Non-obvious conditionals — explain why, not what
- Magic numbers or constants — explain their meaning
- Workarounds and known limitations — explain why they exist

**Do NOT add comments for:**
- Obvious code (`i++ // increment i`)
- Code that already has clear names
- Commented-out code (remove it instead)

### 4. Apply documentation

Write the docstrings and comments. Keep them:
- Accurate — if behavior changes, update the docs
- Concise — one sentence for simple functions, more for complex ones
- Up to date — don't document what the code doesn't do

### 5. Report

List each function/class that was documented and a one-line summary of what was added. If any logic was too unclear to document accurately, flag it as needing clarification.
