"""Run both installed clients against a private, temporary Git marketplace and dev MCP."""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from discover_tools import list_tools

ROOT = Path(__file__).resolve().parents[1]
MARKET_URL = "https://github.com/meshive/meshive-agent-plugins.git"
PLUGIN = "meshive@meshive-plugins"
PUBLISHED_MCP = "https://mcp.meshive.ai/mcp"
DEV_MCP = "https://mcp.dev.meshive.ai/mcp"
PACKAGE_DIRS = (".agents", ".claude-plugin", "plugins")


def run(*args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True,
                          stdout=subprocess.PIPE, timeout=90).stdout


def package_snapshot(market, checkout, ref=None):
    """Only the endpoint changes in these copies. Each revision is served through Git."""
    for name in PACKAGE_DIRS:
        target = market / name
        if target.exists():
            shutil.rmtree(target)
    if ref is None:
        for name in PACKAGE_DIRS:
            shutil.copytree(checkout / name, market / name)
    else:
        archive = subprocess.check_output(["git", "archive", ref, "--", *PACKAGE_DIRS], cwd=checkout)
        subprocess.run(["tar", "-xf", "-", "-C", market], input=archive, check=True)
    for path in ("plugins/claude/.mcp.json", "plugins/openai/mcp.json"):
        config = market / path
        value = json.loads(config.read_text())
        server = value["mcpServers"]["meshive"]
        if server["url"] != PUBLISHED_MCP:
            raise ValueError(f"Unexpected endpoint in {path}")
        server["url"] = DEV_MCP
        config.write_text(json.dumps(value, indent=2) + "\n")
    run("git", "add", "--all", cwd=market)
    run("git", "-c", "commit.gpgSign=false", "commit", "-qm", "Snapshot plugin packages for upgrade test", cwd=market)


def installed_version(client, executable, project, env):
    result = json.loads(run(executable, "plugin", "list", "--json", cwd=project, env=env))
    if client == "claude":
        (entry,) = [p for p in result if p["id"] == PLUGIN and p["enabled"]]
    else:
        (entry,) = [p for p in result["installed"] if p["pluginId"] == PLUGIN and p["enabled"]]
    return entry["version"]


def check_upgrade(tmp, baseline):
    market = tmp / "market"
    project = tmp / "project"
    market.mkdir()
    project.mkdir()
    run("git", "init", "-qb", "dev", cwd=market)
    package_snapshot(market, ROOT, baseline)

    env = os.environ.copy()
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
                "MESHIVE_ACCESS_TOKEN", "CODEX_API_KEY", "OPENAI_API_KEY"):
        env.pop(key, None)
    for folder in ("claude-home", "codex-home"):
        (tmp / folder).mkdir(mode=0o700)
    env.update(CLAUDE_CONFIG_DIR=str(tmp / "claude-home"), CODEX_HOME=str(tmp / "codex-home"),
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", GIT_TERMINAL_PROMPT="0",
               GIT_ALLOW_PROTOCOL="file")
    # Git can only fetch the temporary repo. No credentials or remote push are needed.
    index = int(env.get("GIT_CONFIG_COUNT", 0))
    env[f"GIT_CONFIG_KEY_{index}"] = f"url.{market.as_uri()}.insteadOf"
    env[f"GIT_CONFIG_VALUE_{index}"] = MARKET_URL
    env["GIT_CONFIG_COUNT"] = str(index + 1)
    clients = {"claude": os.environ.get("CLAUDE_BIN", "claude"),
               "codex": os.environ.get("CODEX_BIN", "codex")}
    for client, exe in clients.items():
        run(exe, "plugin", "marketplace", "add", MARKET_URL, cwd=project, env=env)
        verb = "install" if client == "claude" else "add"
        run(exe, "plugin", verb, PLUGIN, cwd=project, env=env)
        version = installed_version(client, exe, project, env)
        if version != "0.1.0":
            raise AssertionError(f"{client}: expected initial installation 0.1.0, got {version}")
        print(f"{client}: installed {version}", flush=True)

    expected = json.loads((ROOT / "plugins/openai/plugin.json").read_text())["version"]
    if expected == "0.1.0":
        raise AssertionError("Candidate must offer an upgrade from 0.1.0")
    package_snapshot(market, ROOT)
    for client, exe in clients.items():
        if client == "claude":
            run(exe, "plugin", "marketplace", "update", "meshive-plugins", cwd=project, env=env)
            run(exe, "plugin", "update", PLUGIN, cwd=project, env=env)
        else:
            run(exe, "plugin", "marketplace", "upgrade", "meshive-plugins", cwd=project, env=env)
        version = installed_version(client, exe, project, env)
        if version != expected:
            raise AssertionError(f"{client}: expected installed {expected}, got {version}")
        tools = asyncio.run(list_tools(client, exe, env, project))
        missing = {"gpus", "pods"} - tools
        if missing:
            raise AssertionError(f"{client}: missing tools {sorted(missing)}")
        print(f"{client}: updated to {version}; {len(tools)} dev tools, including gpus and pods", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-ref", default="cd730f0", help="Git revision of the installed 0.1.0")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="meshive-upgrade-") as directory:
        check_upgrade(Path(directory).resolve(), args.from_ref)
