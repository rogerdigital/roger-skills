---
name: migrate
description: Audit database migration files for production safety — checks for full-table locks, data-loss risks, missing rollbacks, and zero-downtime violations. Triggers on "review migration", "check migration", "audit migration", "is this migration safe", "migration review".
argument-hint: "[migration file path, directory, or glob pattern]"
allowed-tools: Bash(find *) Bash(ls *) Bash(wc *) Bash(git log *) Bash(git diff *) Bash(grep -i migrat) Read
---

Audit the database migration(s) in `$ARGUMENTS` for production safety risks.

## Process

### 1. Identify migration files

- If `$ARGUMENTS` is a file path, audit that file directly.
- If `$ARGUMENTS` is a directory, scan for migration files using common patterns:
  - Django: `*/migrations/*.py` (exclude `__init__.py`)
  - Rails: `db/migrate/*.rb`
  - Alembic: `alembic/versions/*.py` or `migrations/versions/*.py`
  - Prisma: `prisma/migrations/*/migration.sql`
  - TypeORM: `src/migrations/*.ts` or `migrations/*.ts`
  - Flyway: `db/migration/V*.sql` or `sql/V*.sql`
  - golang-migrate: `migrations/*.up.sql` and `migrations/*.down.sql`
  - Knex: `migrations/*.js` or `migrations/*.ts`
- If `$ARGUMENTS` is empty, check for uncommitted or recently added migration files:
  ```bash
  git diff --name-only HEAD | grep -i migrat
  git diff --staged --name-only | grep -i migrat
  ```
- If no migrations found, report clearly and stop.

### 2. Detect ORM and dialect

Identify the migration framework and database dialect from:
- File naming patterns and structure
- Import statements (`from django.db`, `ActiveRecord::Migration`, `sqlalchemy`, etc.)
- Project config files (`database.yml`, `alembic.ini`, `prisma/schema.prisma`, `ormconfig.ts`)
- SQL dialect keywords (`IF NOT EXISTS`, `CONCURRENTLY`, `ALGORITHM=INPLACE`)

This determines which safety rules apply (e.g., PostgreSQL supports `CONCURRENTLY`, MySQL does not).

### 3. Analyze lock risk

For each DDL operation, assess table-lock severity:

| Operation | Risk Level | Reason |
|---|---|---|
| `ADD COLUMN` (nullable, no default) | **Low** | No rewrite, minimal lock |
| `ADD COLUMN ... NOT NULL DEFAULT` | **High** (MySQL <8.0), **Low** (Pg/MySQL 8+) | May rewrite table |
| `ADD COLUMN ... NOT NULL` (no default) | **Critical** | Fails on existing rows OR rewrites table |
| `DROP COLUMN` | **Medium** | Brief exclusive lock, but irreversible |
| `ALTER COLUMN` / `MODIFY COLUMN` (type change) | **Critical** | Full table rewrite, long lock |
| `ADD INDEX` (without CONCURRENTLY) | **High** | Blocks writes for duration |
| `ADD INDEX CONCURRENTLY` | **Low** | Online, but can fail silently |
| `RENAME TABLE` / `RENAME COLUMN` | **High** | Breaks running queries |
| `DROP TABLE` | **Critical** | Irreversible data loss |
| `CREATE TABLE` | **None** | New table, no contention |

Flag any operation that holds an **exclusive lock** on a table likely to be large (check for hints in comments, table name conventions like `users`, `events`, `logs`, `orders`).

### 4. Check for data-loss risks

Flag these patterns as **Critical** or **High**:

- `DROP TABLE` or `DROP COLUMN` without a prior data backup step
- `TRUNCATE TABLE`
- `DELETE FROM` without a `WHERE` clause
- Changing a column type that could lose precision (e.g., `BIGINT` to `INT`, `TEXT` to `VARCHAR(50)`)
- Removing a `NOT NULL` constraint (silent null introduction)
- Adding `NOT NULL` without a `DEFAULT` on a populated table (migration will fail or corrupt)

### 5. Assess backward compatibility

Check whether the migration is **safe for rolling deployments** (old code + new schema):

- **Column renames**: Old code references old name — will break. Require a multi-step approach (add new, backfill, deploy new code, drop old).
- **Column drops**: Old code may still SELECT/INSERT it — will break. Require code deployment first.
- **NOT NULL additions**: Old code not setting the field will fail on INSERT.
- **Enum value removals**: Existing rows or in-flight inserts may reference the removed value.
- **Foreign key additions**: Existing orphan rows will cause the migration to fail.

### 6. Verify rollback strategy

Check for the existence and correctness of a rollback:

- **Reversible migration file exists** (e.g., `*.down.sql`, `down()` method, `RunSQL` with `reverse_sql`)
- **Rollback is actually reversible**: A `DROP TABLE` rollback that recreates the table is only useful if data is not lost. Flag rollbacks that cannot restore data.
- **Rollback won't cause a second outage**: Dropping an index in rollback that took 30 minutes to build is problematic.

If no rollback exists, flag as **High** severity finding.

### 7. Estimate impact

Where possible, infer table size impact:

- Check migration comments for row counts or table names
- Flag operations on tables with names suggesting high volume: `users`, `events`, `logs`, `sessions`, `messages`, `orders`, `transactions`, `audit_*`
- If the project has seed data or a schema dump, check for row-count hints
- Report estimated lock duration category: **seconds**, **minutes**, **hours** (based on operation type)

### 8. Generate safety report

Output the report in this format:

```markdown
## Migration Safety Report

**Files reviewed:** <list>
**Framework:** <detected ORM/tool>
**Database dialect:** <detected or assumed>
**Overall risk:** Critical / High / Medium / Low / Safe

---

## Critical Findings (block deployment)

### [file:line] <finding title>
- **Operation:** `<SQL or ORM statement>`
- **Risk:** <what will happen in production>
- **Impact:** <lock duration, data loss, downtime>
- **Remediation:** <specific fix with code example>

---

## High Findings (requires mitigation)

### [file:line] <finding title>
- **Operation:** `<SQL or ORM statement>`
- **Risk:** <what could happen>
- **Remediation:** <specific fix>

---

## Medium Findings (review recommended)

- [file:line] <description>. Suggestion: <fix>.

---

## Low / Informational

- [file:line] <observation>

---

## Rollback Assessment
- **Rollback exists:** Yes / No / Partial
- **Rollback is data-safe:** Yes / No
- **Rollback estimated duration:** <time>

## Zero-Downtime Checklist
- [ ] All operations are backward-compatible with current running code
- [ ] No exclusive table locks exceeding 1 second expected
- [ ] Rollback plan exists and is tested
- [ ] Large table operations use online DDL (CONCURRENTLY, ALGORITHM=INPLACE, pt-osc)
```

## Rules

- Be specific: always reference file paths, line numbers, and exact SQL/ORM statements.
- **Do NOT** approve a migration as "safe" if it contains any Critical findings.
- **Do NOT** assume table sizes — flag uncertainty and recommend checking production metrics.
- If the migration is clean, say so clearly with a brief explanation of why it is safe.
- Provide concrete remediation code for every Critical and High finding, not just a description of the problem.
- For ORM-based migrations, show both the ORM fix AND the equivalent raw SQL for clarity.
- **Do NOT** modify migration files. This skill is read-only audit only.
- When multiple migrations are reviewed, assess their **combined** effect (e.g., one adds a column, another makes it NOT NULL — safe individually, but the ordering matters).
