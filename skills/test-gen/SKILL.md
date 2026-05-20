---
name: test-gen
description: Generate comprehensive unit tests for a function, class, or module. Covers happy path, edge cases, and error handling. Triggers on "write tests for", "generate tests", "add unit tests", "test this function".
argument-hint: "[file path or function/class name]"
allowed-tools: Read Edit Write Bash(*test*) Bash(*spec*) Bash(npm test *) Bash(make test *) Bash(cargo test *) Bash(go test *) Bash(pytest *) Bash(python -m pytest *)
---

Generate thorough unit tests for: `$ARGUMENTS`

## Mock philosophy

Prefer real dependencies over mocks for integration-critical code. Only mock:
- External services (network calls, APIs)
- Database connections
- Filesystem operations
- Time-dependent behavior

Over-mocking creates tests that pass but don't catch real issues. If a dependency is part of your own codebase and fast to run, use the real thing. Mocks should be a last resort, not a default.

## Process

### 1. Run existing tests first

Before adding any new tests, run the existing test suite to confirm the baseline passes. If existing tests are already failing, fix or flag those before generating new ones. You need a green baseline to verify that new tests are testing the right thing.

### 2. Read and understand the target

Read the source file completely. Identify:
- What the function/class is supposed to do
- Input types, constraints, and valid ranges
- Return values and side effects
- Error conditions and how they're signaled (throw, return null, error code, etc.)
- Any existing tests (avoid duplication, follow existing patterns)

### 3. Identify test cases

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

### 4. Write the tests

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

### 5. Verify

Run the generated tests and confirm they pass. If any fail, fix the test (wrong expectation) or flag a bug (implementation is wrong).

## Output

Place tests in the appropriate location following project conventions (e.g., `__tests__/`, `_test.go`, `*.spec.ts`). Report:
- Number of test cases generated
- Test run result
- Any uncovered behaviors you couldn't test (and why)
