---
name: simplify
description: Simplify code by removing unnecessary complexity — dead code, over-abstraction, redundant indirection, and speculative generality. Triggers on "simplify this", "this is overengineered", "too complex", "reduce complexity", "YAGNI".
argument-hint: "[file path or function name]"
allowed-tools: Read Edit Write Bash(*test*) Bash(*spec*)
---

Simplify the code in `$ARGUMENTS` by removing unnecessary complexity without changing behavior.

## Process

### 1. Understand what exists

Read the target code fully. Identify:
- What it does (actual behavior)
- What it was designed to do (intent, from names/docs)
- The gap between the two (unused flexibility, speculative abstraction)

### 2. Apply Chesterton's Fence

Before removing anything, understand WHY it exists:
- Check git history: `git log -p -- <file>` — was this added for a reason?
- Check callers: who uses this and how?
- If you don't understand why something exists, DO NOT remove it — flag it instead.

### 3. Identify simplification opportunities

**Dead code**
- Unreachable branches, unused functions, unreferenced variables
- Commented-out code (remove it — git has history)
- Unused imports/dependencies

**Over-abstraction**
- Interfaces/traits with a single implementation
- Factory patterns for a single variant
- Strategy patterns that never vary
- Generics/type parameters used with only one concrete type

**Unnecessary indirection**
- Wrapper functions that add no logic
- Proxy classes that delegate everything
- Trivial getter/setter pairs in languages that support public fields

**Speculative generality (YAGNI)**
- Configurable parameters always used with the same value
- Extension points never extended
- Feature flags always on (or always off)
- Generalized solutions for a specific problem

**Excessive ceremony**
- Nested conditionals that can be flattened with early returns
- Redundant type annotations the compiler can infer
- Overly verbose patterns when simpler alternatives exist

### 4. Simplify (Rule of 500)

- If a function exceeds ~50 lines, consider breaking it up
- If a file exceeds ~500 lines, consider splitting it
- These are signals, not hard limits — use judgment

### 5. Apply changes incrementally

One simplification at a time. After each:
- Run tests to verify nothing broke
- If tests fail, revert and reassess

### 6. Report

```
## Simplifications
- [file:line] What was removed/simplified and why

## Flagged (not simplified — needs investigation)
- [file:line] What looks unnecessary but reason is unclear

## Metrics
- Lines removed: N
- Functions simplified: N
- Tests: passing/failed
```

## Rules

- Every removal must be justified. "I don't see why this is needed" is NOT justification — check history first.
- Do NOT simplify tests — tests should be descriptive even if verbose.
- Do NOT change behavior. If simplification changes output, it's a refactor, not a simplification.
- When in doubt, flag rather than remove.
