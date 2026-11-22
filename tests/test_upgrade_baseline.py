import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_upgrade


class UpgradeBaseline(unittest.TestCase):
    def test_bundled_packages_work_without_git_history(self):
        for baseline in ("original", "revised", "cd730f0", "304a593"):
            with self.subTest(baseline=baseline), tempfile.TemporaryDirectory() as directory:
                market = Path(directory)
                # Inspect the package before the two local Git commands publish it to the test clients.
                with patch.object(check_upgrade, "run"):
                    check_upgrade.package_baseline(market, baseline, check_upgrade.PUBLISHED_MCP)
                for plugin_path in ("plugins/claude/.claude-plugin/plugin.json", "plugins/openai/plugin.json"):
                    plugin = json.loads((market / plugin_path).read_text())
                    self.assertEqual((plugin["name"], plugin["version"]), ("meshive", "0.1.0"))
                server = json.loads((market / "plugins/openai/mcp.json").read_text())["mcpServers"]["meshive"]
                self.assertEqual(server["url"], check_upgrade.PUBLISHED_MCP)
                self.assertEqual("extensions" in server, baseline in ("original", "cd730f0"))
