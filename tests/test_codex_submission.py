import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/openai"


class CodexSubmission(unittest.TestCase):
    def test_submission_zip_preserves_the_direct_install_config(self):
        source = PLUGIN / "mcp.json"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "meshive-codex.zip"
            subprocess.run(
                [sys.executable, ROOT / "scripts/package_codex.py", output],
                check=True, stdout=subprocess.PIPE, cwd=directory,
            )
            with ZipFile(output) as bundle:
                self.assertIsNone(bundle.testzip())
                archived = json.loads(bundle.read("mcp.json"))
                auth = archived["mcpServers"]["meshive"].pop("extensions")
                self.assertEqual(auth, {"com.openai": {"auth": {"type": "mixed"}}})
                self.assertEqual(archived, json.loads(original))
                self.assertEqual(bundle.read("LICENSE"), (ROOT / "LICENSE").read_bytes())

                tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=PLUGIN)
                package_files = tracked.decode().split("\0")[:-1]
                self.assertCountEqual(bundle.namelist(), [*package_files, "LICENSE"])
                for name in package_files:
                    if name != "mcp.json":
                        with self.subTest(name=name):
                            self.assertEqual(bundle.read(name), (PLUGIN / name).read_bytes())

        self.assertEqual(source.read_bytes(), original)
