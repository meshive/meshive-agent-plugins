"""Create the OpenAI directory submission ZIP from the Codex plugin."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/openai"


def package(output, version=None):
    # Only ship version-controlled plugin files, even from a local working tree.
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=PLUGIN)
    # The portable Codex loader rejects per-server OpenAI auth extensions.
    # Its compatibility loader and the submission portal both accept them.
    manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    manifest.pop("$schema", None)
    if version is not None:
        manifest["version"] = version
    openai_metadata = manifest["extensions"]["com.openai"]
    manifest["interface"] = openai_metadata.pop("interface")
    manifest["interface"].setdefault("capabilities", [])
    manifest.setdefault("keywords", [])
    manifest["mcpServers"] = "./.mcp.json"

    config = json.loads((PLUGIN / "mcp.json").read_text(encoding="utf-8"))
    config.pop("$schema", None)
    server = config["mcpServers"]["meshive"]
    openai = server.setdefault("extensions", {}).setdefault("com.openai", {})
    issuer = "https://api.meshive.ai"
    openai["auth"] = {
        "type": "mixed",
        # This public PKCE client is registered for the OpenAI directory callback.
        "client": {
            "mode": "provided",
            "clientId": "AbVJFaIq8S_GSGs4MqXNgUsVM66smT46Kj6Wp8jal3A",
            "tokenEndpointAuthMethod": "none",
        },
        "authorizationServerBase": issuer,
        "authorizationUrl": issuer + "/oauth/authorize",
        "tokenUrl": issuer + "/oauth/token",
        "resource": server["url"],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as staging:
        archive = Path(staging) / "submission.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for name in os.fsdecode(tracked).split("\0"):
                if name and name not in {"plugin.json", "mcp.json"}:
                    bundle.write(PLUGIN / name, name)
            bundle.writestr(".codex-plugin/plugin.json", json.dumps(manifest, indent=2) + "\n")
            bundle.writestr(".mcp.json", json.dumps(config, indent=2) + "\n")
            bundle.write(ROOT / "LICENSE", "LICENSE")
        archive.replace(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for the submission ZIP")
    parser.add_argument("--version", help="OpenAI directory release version, e.g. 0.1.2")
    args = parser.parse_args()
    output = args.output
    if output.suffix.lower() != ".zip":
        parser.error("choose an output path ending in .zip")
    package(output, args.version)
    print(output.resolve())
