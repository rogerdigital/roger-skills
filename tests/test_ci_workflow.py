from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ValidateWorkflowTest(unittest.TestCase):
    def test_pip_cache_tracks_dev_requirements(self) -> None:
        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / "validate.yml").read_text(
                encoding="utf-8"
            )
        )
        steps = workflow["jobs"]["validate"]["steps"]
        setup_python = next(
            step for step in steps if step.get("uses") == "actions/setup-python@v5"
        )

        self.assertEqual(
            "requirements-dev.txt",
            setup_python["with"].get("cache-dependency-path"),
        )


if __name__ == "__main__":
    unittest.main()
