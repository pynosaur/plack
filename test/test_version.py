#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import __version__

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_program_field(field):
    text = (REPO_ROOT / ".program").read_text()
    for line in text.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


class TestVersionConsistency(unittest.TestCase):
    """All version references must match. CI catches drift."""

    def _read_doc_version(self):
        name = _read_program_field("name")
        self.assertIsNotNone(name, ".program has no name field")
        doc_file = REPO_ROOT / "doc" / f"{name}.yaml"
        self.assertTrue(doc_file.exists(), f"doc/{name}.yaml not found")
        text = doc_file.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("VERSION:"):
                val = stripped.split(":", 1)[1].strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                return val
        self.fail(f"doc/{name}.yaml has no VERSION field")

    def _read_readme_version(self):
        readme = REPO_ROOT / "README.md"
        if not readme.exists():
            return None
        text = readme.read_text()
        match = re.search(r'^Version:\s*(.+)$', text, re.MULTILINE)
        return match.group(1).strip() if match else None

    def test_all_versions_match(self):
        program_v = _read_program_field("version")
        self.assertIsNotNone(program_v, ".program has no version field")
        doc_v = self._read_doc_version()
        readme_v = self._read_readme_version()
        init_v = __version__

        self.assertEqual(
            init_v, program_v,
            f"__init__.py ({init_v}) != .program ({program_v})",
        )
        self.assertEqual(
            init_v, doc_v,
            f"__init__.py ({init_v}) != doc yaml ({doc_v})",
        )
        if readme_v is not None:
            self.assertEqual(
                init_v, readme_v,
                f"__init__.py ({init_v}) != README.md ({readme_v})",
            )


if __name__ == "__main__":
    unittest.main()
