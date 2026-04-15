---
name: test-gen
description: Generate comprehensive unit tests for a function, class, or module. Covers happy path, edge cases, and error handling. Triggers on "write tests for", "generate tests", "add unit tests", "test this function".
argument-hint: "[file path or function/class name]"
---

Generate thorough unit tests for: `$ARGUMENTS`

## Process

### 1. Read and understand the target

Read the source file completely. Identify:
- What the function/class is supposed to do
- Input types, constraints, and valid ranges
- Return values and side effects
- Error conditions and how they're signaled (throw, return null, error code, etc.)
- Any existing tests (avoid duplication, follow existing patterns)

### 2. Identify test cases

For each function/method, cover:

**Happy path**
- Typical inputs with expected outputs
- Multiple representative examples if behavior varies

**Boundary conditions**
- Empty string, empty array, zero, null/undefined/nil
- Single-element collections
- Maximum/minimum values
- First and last items

**Error cases**
- Invalid input types
- Out-of-range values
- Missing required fields
- Network/IO failures (mock as needed)

**State/side effects** (if applicable)
- Verify state changes
- Verify calls to dependencies (use mocks/spies)
- Verify cleanup happens

### 3. Write the tests

Follow the existing test framework and conventions in the project. If no tests exist, use the most common framework for the language:
- TypeScript/JS → Vitest or Jest
- Python → pytest
- Go → `testing` package
- Rust → built-in `#[test]`

Each test should:
- Have a descriptive name: `should <behavior> when <condition>`
- Follow Arrange–Act–Assert structure
- Test one behavior per test
- Not depend on other tests (no shared mutable state)
- Be deterministic (no flakiness from timing, randomness, or external services)

Use mocks/stubs for external dependencies (network, DB, filesystem, time).

### 4. Verify

Run the generated tests and confirm they pass. If any fail, fix the test (wrong expectation) or flag a bug (implementation is wrong).

## Output

Place tests in the appropriate location following project conventions (e.g., `__tests__/`, `_test.go`, `*.spec.ts`). Report:
- Number of test cases generated
- Test run result
- Any uncovered behaviors you couldn't test (and why)
