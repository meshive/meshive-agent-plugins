# Meshive plugins

Use Meshive in Claude Code or Codex to compare GPU rental prices and list pods across your workspaces. Both plugins connect to the Meshive MCP server at `https://mcp.meshive.ai/mcp`.

## Installation

Run the commands for your client in a terminal. Both clients install from the public repository's default release branch, `real`, without a GitHub sign-in. Installing the plugin registers the `meshive` MCP server.

### Claude Code

```sh
claude plugin marketplace add https://github.com/meshive/meshive-agent-plugins.git
claude plugin install meshive@meshive-plugins
claude plugin list
```

Open a new Claude Code session and run `/mcp` to check the Meshive connection.

### Codex

```sh
codex plugin marketplace add https://github.com/meshive/meshive-agent-plugins.git
codex plugin add meshive@meshive-plugins
codex plugin list
```

Open a new Codex session and try one of the prompts below.

## First requests

| Example prompt | Tool | Sign-in |
| --- | --- | --- |
| “Which GPUs can I rent on Meshive, and how much do they cost per hour?” | `gpus` | Public prices are available without signing in. |
| “List my Meshive pods across all my workspaces.” | `pods` | Where OAuth is enabled, follow your client's Meshive sign-in prompt, approve read access in your browser, and repeat the request. |

Sign in to Meshive to access your own resources. For instructions on connecting with a manual MCP access token and the full tool reference, see the [Meshive MCP guide](https://docs.meshive.ai/sdk-cli/mcp/).

## Update an existing installation

Run the commands in the same profile you used to install the plugin. Check the installed version with `plugin list`, then open a **new session**.

**Claude Code**

```sh
claude plugin marketplace update meshive-plugins
claude plugin update meshive@meshive-plugins
claude plugin list
```

**Codex**

```sh
codex plugin marketplace upgrade meshive-plugins
codex plugin list
```

If Codex has version 0.1.0 installed and shows no Meshive tools, update to 0.1.1 or later. See the [changelog](CHANGELOG.md) for details.

## Package the Codex plugin for the OpenAI directory

Run the packager from the repository root with a local output path.

```sh
python3 scripts/package_codex.py --version 0.1.2 /tmp/meshive-codex.zip
```

OpenAI requires a higher version for updates. Use `--version` to set the directory release version independently of the Git installs. The submission ZIP uses the Codex compatibility layout. The packager writes the listing to `.codex-plugin/plugin.json` and the production MCP server and mixed OAuth configuration to `.mcp.json`. It also includes the plugin assets and the Apache 2.0 `LICENSE`. Users can check public GPU prices anonymously and sign in to access their Meshive resources. Git marketplace installs use the portable configuration in `plugins/openai/mcp.json`.

## Compatibility tests

From the repository root, run the following command to check the marketplace paths, package versions, and MCP connection settings. The same checks run on pull requests.

```sh
python3 -B -m unittest discover -s tests -v
```

To test an upgrade, you need Git with a configured author, both client CLIs, and network access to the public Meshive MCP server. The original 0.1.0 marketplace and plugin manifests are included in `tests/fixtures/0.1.0/`. The revised 0.1.0 package differed only in its Codex MCP configuration.

From a fresh public clone, run either command below. Each creates temporary client profiles, installs the selected 0.1.0 package from a local Git marketplace, and upgrades to the version in your working tree. The test checks that each client lists `gpus` and `pods` on the public server. It does not call either tool or require GitHub credentials, a Meshive login, or model calls.

```sh
python3 -B tests/check_upgrade.py                     # Original 0.1.0 release
python3 -B tests/check_upgrade.py --baseline revised  # Revised 0.1.0 release
```

To check the dev server from a network that can reach it, add `--dev-mcp` to either command. The test uses `claude` and `codex` from your path by default. To test a specific executable, set `CLAUDE_BIN` or `CODEX_BIN` to its path.
