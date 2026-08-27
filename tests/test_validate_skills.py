import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.validate_skills import validate_repository


VALID_SKILL = """\
---
name: demo
description: A valid test skill.
allowed-tools: Bash(git status)
---

# Demo

```bash
git status
```
"""


class ValidateSkillsTest(unittest.TestCase):
    def make_repository(self, files: dict[str, str]) -> tempfile.TemporaryDirectory[str]:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        for relative_path, content in files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        self.addCleanup(temp_dir.cleanup)
        return temp_dir

    def valid_repository(self, skill: str = VALID_SKILL) -> Path:
        temp_dir = self.make_repository(
            {
                "skills/demo/SKILL.md": skill,
                "README.md": "# Skills\n\n[demo](skills/demo/SKILL.md)\n",
            }
        )
        return Path(temp_dir.name)

    def test_accepts_a_valid_one_skill_repository(self) -> None:
        self.assertEqual(validate_repository(self.valid_repository()), [])

    def test_rejects_missing_or_malformed_frontmatter(self) -> None:
        root = self.valid_repository("# Not frontmatter\n")
        errors = validate_repository(root)
        self.assertTrue(any("missing frontmatter" in error for error in errors))

        malformed = self.valid_repository("---\nname: [bad\n---\nbody\n")
        errors = validate_repository(malformed)
        self.assertTrue(any("invalid YAML" in error for error in errors))

    def test_rejects_duplicate_skill_names(self) -> None:
        temp_dir = self.make_repository(
            {
                "skills/first/SKILL.md": VALID_SKILL.replace("name: demo", "name: duplicate"),
                "skills/second/SKILL.md": VALID_SKILL.replace(
                    "name: demo", "name: duplicate"
                ),
                "README.md": "[first](skills/first/SKILL.md)\n[second](skills/second/SKILL.md)\n",
            }
        )
        errors = validate_repository(Path(temp_dir.name))
        self.assertTrue(any("duplicate skill name 'duplicate'" in error for error in errors))

    def test_rejects_name_directory_mismatch(self) -> None:
        errors = validate_repository(
            self.valid_repository(VALID_SKILL.replace("name: demo", "name: other"))
        )
        self.assertTrue(any("name 'other' does not match directory 'demo'" in error for error in errors))

    def test_rejects_empty_body(self) -> None:
        errors = validate_repository(
            self.valid_repository("---\nname: demo\ndescription: Test.\n---\n")
        )
        self.assertTrue(any("skill body is empty" in error for error in errors))

    def test_rejects_dangerous_allowed_tool(self) -> None:
        errors = validate_repository(
            self.valid_repository(VALID_SKILL.replace("Bash(git status)", "Bash(git push --force)"))
        )
        self.assertTrue(any("dangerous command in allowed-tools" in error for error in errors))

    def test_rejects_command_without_permission(self) -> None:
        errors = validate_repository(
            self.valid_repository(VALID_SKILL.replace("git status", "git log", 1))
        )
        self.assertTrue(any("not covered by allowed-tools" in error for error in errors))

    def test_requires_permission_for_each_pipeline_command(self) -> None:
        skill = VALID_SKILL.replace("Bash(git status)", "Bash(git tag *)").replace(
            "git status\n```", "git tag --list | head -10\n```"
        )
        errors = validate_repository(self.valid_repository(skill))
        self.assertTrue(any("head -10" in error and "not covered" in error for error in errors))

    def test_rejects_shell_command_in_unlabelled_fence(self) -> None:
        skill = VALID_SKILL.replace("```bash\ngit status", "```\ngit status")
        errors = validate_repository(self.valid_repository(skill))
        self.assertTrue(any("must be labelled bash or sh" in error for error in errors))

    def test_accepts_reasoned_ignore_marker_for_following_shell_block(self) -> None:
        skill = VALID_SKILL.replace(
            "```bash\ngit status",
            '<!-- skill-validator: ignore-shell reason="illustrative only" -->\n```bash\ngit log',
        )
        self.assertEqual(validate_repository(self.valid_repository(skill)), [])

    def test_rejects_empty_or_malformed_ignore_reason(self) -> None:
        empty = VALID_SKILL.replace(
            "```bash\ngit status",
            '<!-- skill-validator: ignore-shell reason="" -->\n```bash\ngit log',
        )
        errors = validate_repository(self.valid_repository(empty))
        self.assertTrue(any("invalid ignore-shell marker" in error for error in errors))

        malformed = VALID_SKILL.replace(
            "```bash\ngit status", "<!-- skill-validator: ignore-shell -->\n```bash\ngit log"
        )
        errors = validate_repository(self.valid_repository(malformed))
        self.assertTrue(any("invalid ignore-shell marker" in error for error in errors))

    def test_rejects_stale_or_missing_readme_inventory(self) -> None:
        temp_dir = self.make_repository(
            {
                "skills/demo/SKILL.md": VALID_SKILL,
                "README.md": "[stale](skills/stale/SKILL.md)\n",
            }
        )
        errors = validate_repository(Path(temp_dir.name))
        self.assertTrue(any("README missing skill links: demo" in error for error in errors))
        self.assertTrue(any("README stale skill links: stale" in error for error in errors))

    def test_allows_credential_scanning_for_security_audit(self) -> None:
        skill = VALID_SKILL.replace("description: A valid test skill.", "description: Audit secrets.")
        skill = skill.replace(
            "allowed-tools: Bash(git status)", "security-audit: true\nallowed-tools: Bash(grep *)"
        ).replace("git status\n```", "grep -R 'api key' .\n```")
        self.assertEqual(validate_repository(self.valid_repository(skill)), [])

    def test_rejects_overbroad_bash_permission_pattern(self) -> None:
        errors = validate_repository(
            self.valid_repository(VALID_SKILL.replace("Bash(git status)", "Bash(* status)"))
        )
        self.assertTrue(any("must not begin with '*'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
