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
                self.assertNotIn("plugin.json", bundle.namelist())
                self.assertNotIn("mcp.json", bundle.namelist())
                manifest = json.loads(bundle.read(".codex-plugin/plugin.json"))
                source_manifest = json.loads((PLUGIN / "plugin.json").read_bytes())
                self.assertEqual(manifest["name"], source_manifest["name"])
                self.assertEqual(manifest["version"], source_manifest["version"])
                source_interface = source_manifest["extensions"]["com.openai"]["interface"]
                self.assertEqual(manifest["interface"], {"capabilities": [], **source_interface})
                self.assertEqual(manifest["keywords"], source_manifest.get("keywords", []))
                self.assertEqual(manifest["mcpServers"], "./.mcp.json")
                archived = json.loads(bundle.read(".mcp.json"))
                server = archived["mcpServers"]["meshive"]
                auth = server.pop("extensions")["com.openai"]["auth"]
                self.assertEqual(auth, {
                    "type": "mixed",
                    "client": {
                        "mode": "provided",
                        "clientId": "AbVJFaIq8S_GSGs4MqXNgUsVM66smT46Kj6Wp8jal3A",
                        "tokenEndpointAuthMethod": "none",
                    },
                    "authorizationServerBase": "https://api.meshive.ai",
                    "authorizationUrl": "https://api.meshive.ai/oauth/authorize",
                    "tokenUrl": "https://api.meshive.ai/oauth/token",
                    "resource": server["url"],
                })
                self.assertEqual(archived["mcpServers"], json.loads(original)["mcpServers"])
                self.assertNotIn("$schema", archived)
                self.assertEqual(bundle.read("LICENSE"), (ROOT / "LICENSE").read_bytes())

                tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=PLUGIN)
                package_files = [path for path in tracked.decode().split("\0") if path and path not in {"plugin.json", "mcp.json"}]
                self.assertCountEqual(bundle.namelist(), [*package_files, ".codex-plugin/plugin.json", ".mcp.json", "LICENSE"])
                for name in package_files:
                    with self.subTest(name=name):
                        self.assertEqual(bundle.read(name), (PLUGIN / name).read_bytes())

        self.assertEqual(source.read_bytes(), original)

    def test_directory_update_can_use_a_new_version_without_changing_git_installs(self):
        source = (PLUGIN / "plugin.json").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "meshive.zip"
            subprocess.run(
                [sys.executable, ROOT / "scripts/package_codex.py", "--version", "0.1.2", output],
                check=True, capture_output=True,
            )
            with ZipFile(output) as bundle:
                manifest = json.loads(bundle.read(".codex-plugin/plugin.json"))
                self.assertEqual(manifest["version"], "0.1.2")
        self.assertEqual((PLUGIN / "plugin.json").read_bytes(), source)
