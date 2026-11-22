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


def package(output):
    # Only ship version-controlled plugin files, even from a local working tree.
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=PLUGIN)
    config = json.loads((PLUGIN / "mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["meshive"]
    openai = server.setdefault("extensions", {}).setdefault("com.openai", {})
    openai["auth"] = {"type": "mixed"}

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as staging:
        archive = Path(staging) / "submission.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for name in os.fsdecode(tracked).split("\0"):
                if name and name != "mcp.json":
                    bundle.write(PLUGIN / name, name)
            bundle.writestr("mcp.json", json.dumps(config, indent=2) + "\n")
            bundle.write(ROOT / "LICENSE", "LICENSE")
        archive.replace(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path for the submission ZIP")
    output = parser.parse_args().output
    if output.suffix.lower() != ".zip":
        parser.error("choose an output path ending in .zip")
    package(output)
    print(output.resolve())
