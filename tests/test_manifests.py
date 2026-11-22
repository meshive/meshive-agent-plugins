import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = "https://mcp.meshive.ai/mcp"


def manifest(path):
    return json.loads(path.read_text(encoding="utf-8"))


def marketplace_entry(path):
    catalog = manifest(ROOT / path)
    if catalog["name"] != "meshive-plugins":
        raise ValueError("Existing installations use the meshive-plugins marketplace")
    (entry,) = [plugin for plugin in catalog["plugins"] if plugin["name"] == "meshive"]
    return entry


class PluginCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        claude = marketplace_entry(".claude-plugin/marketplace.json")
        cls.codex = marketplace_entry(".agents/plugins/marketplace.json")
        cls.claude_root = ROOT / claude["source"]
        cls.codex_root = ROOT / cls.codex["source"]["path"]

    def test_both_marketplaces_offer_the_same_upgrade_from_010(self):
        claude = manifest(self.claude_root / ".claude-plugin/plugin.json")
        codex = manifest(self.codex_root / "plugin.json")
        self.assertEqual((claude["name"], codex["name"]), ("meshive", "meshive"))
        self.assertEqual(claude["version"], codex["version"])
        version = tuple(int(field) for field in codex["version"].split("."))
        self.assertEqual(len(version), 3)
        self.assertGreater(version, (0, 1, 0))

    def test_claude_registers_the_hosted_http_server(self):
        servers = manifest(self.claude_root / ".mcp.json")["mcpServers"]
        self.assertEqual(servers["meshive"]["type"], "http")
        self.assertEqual(servers["meshive"]["url"], PRODUCTION)
        self.assertNotIn("Authorization", servers["meshive"].get("headers", {}))

    def test_claude_directory_includes_icon_and_privacy_policy(self):
        plugin = manifest(self.claude_root / ".claude-plugin/plugin.json")
        self.assertTrue((self.claude_root / plugin["icon"]).is_file())
        self.assertEqual(plugin["privacyPolicyUrl"], "https://meshive.ai/privacy-policy")

    def test_codex_directory_includes_listing_details_and_icons(self):
        plugin = manifest(self.codex_root / "plugin.json")
        listing = plugin["extensions"]["com.openai"]["interface"]
        self.assertTrue(listing["shortDescription"].strip())
        self.assertLessEqual(len(listing["shortDescription"]), 30)
        self.assertTrue(listing["longDescription"].strip())
        self.assertEqual(listing["developerName"], plugin["author"]["name"])
        self.assertEqual(listing["category"], self.codex["category"])
        self.assertTrue(listing["supportURL"].startswith("https://"))
        for field in ("logo", "composerIcon"):
            with self.subTest(field=field):
                self.assertTrue((self.codex_root / listing[field]).is_file())

    def test_codex_registers_the_public_server_with_on_use_auth(self):
        self.assertEqual(self.codex["source"]["source"], "local")
        self.assertEqual(self.codex["policy"]["authentication"], "ON_USE")
        server = manifest(self.codex_root / "mcp.json")["mcpServers"]["meshive"]
        self.assertEqual(server["type"], "streamable-http")
        self.assertEqual(server["url"], PRODUCTION)
        self.assertNotIn("extensions", server, "Codex drops the entire server with this field")
        self.assertNotIn("Authorization", server.get("headers", {}))
