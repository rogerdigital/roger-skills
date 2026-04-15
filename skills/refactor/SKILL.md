---
name: refactor
description: Refactor a specific file or function for clarity, maintainability, and simplicity — without changing behavior. Triggers on "refactor this", "clean up this code", "simplify this function", "make this more readable".
argument-hint: "[file path or function name]"
---

Refactor `$ARGUMENTS` to improve code quality without changing external behavior.

## Constraints

- **No behavior changes.** All existing tests must still pass after the refactor.
- **Minimal footprint.** Only change what needs changing. Do not refactor adjacent code.
- **No new features.** Do not add functionality, error handling, or logging that wasn't there before.
- **Preserve public API.** Function signatures, return types, and exported names stay the same unless explicitly asked to change them.

## Process

### 1. Understand before changing

Read the target code fully. Identify:
- What it does (behavior)
- What it should do (intent, from context/tests/docs)
- Where it's hard to understand or unnecessarily complex

### 2. Run existing tests

Confirm tests pass before you change anything. If there are no tests, note that — the refactor risk is higher.

### 3. Identify refactoring opportunities (pick relevant ones)

**Naming**
- Rename variables, functions, and types to accurately reflect their purpose.

**Extract / Inline**
- Extract duplicated logic into a shared function.
- Inline trivially small helpers that obscure rather than clarify.

**Simplify conditionals**
- Remove double negatives.
- Collapse nested `if`s using early returns.
- Replace complex boolean chains with named predicates.

**Reduce complexity**
- Break up functions doing too many things (> ~30 lines is a signal, not a rule).
- Remove dead code, unused parameters, unnecessary state.

**Consistency**
- Align with surrounding code style and patterns.

### 4. Apply changes incrementally

Make one logical change at a time. After each change, verify tests still pass if possible.

### 5. Report

```
## Changes made
- [file:line] What was changed and why

## Before / After (for non-obvious changes)
// before
...
// after
...

## Tests
<result of running tests>
```

If you found larger structural issues outside the scope of this refactor, mention them as follow-up suggestions — don't fix them in this task.
