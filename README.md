# Meshive plugins

Use Meshive in Claude Code or Codex to compare GPU rental prices and list pods across your workspaces. Both plugins connect to the Meshive MCP server at `https://mcp.meshive.ai/mcp`.

## Installation

Run the commands for your client in a terminal. While this repository is private, Git needs to be authenticated with a GitHub account that has read access. Installing the plugin registers the `meshive` MCP server.

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

GitHub sign-in gives you access to this plugin repository. Meshive sign-in gives you access to your own resources. For instructions on connecting with a manual MCP access token and the full tool reference, see the [Meshive MCP guide](https://docs.meshive.ai/sdk-cli/mcp/).

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
python3 scripts/package_codex.py /tmp/meshive-codex.zip
```

The ZIP contains the tracked Codex plugin files and a copy of the repository's Apache 2.0 `LICENSE` at its root. The packager adds `mixed` authentication to the archived `mcp.json` so users can check public GPU prices anonymously and sign in with OAuth to access their Meshive resources. Git marketplace installs read `plugins/openai/mcp.json` directly.

## Compatibility tests

From the repository root, run the following command to check the marketplace paths, package versions, and MCP connection settings. The same checks run on pull requests.

```sh
python3 -B -m unittest discover -s tests -v
```

To test an upgrade in both clients, you need a configured Git author, `tar`, both client CLIs, and network access to the dev MCP server. The test creates a local Git marketplace and a fresh profile for each client. It points the test copies at the dev server, installs 0.1.0 in each profile, and upgrades to the version in your working tree. It then checks that each client lists the `gpus` and `pods` tools. This check runs without model calls or a Meshive login.

```sh
python3 -B tests/check_upgrade.py                     # Original 0.1.0 release
python3 -B tests/check_upgrade.py --from-ref 304a593  # 0.1.0 with the revised Codex configuration
```

The test uses `claude` and `codex` from your path by default. To test a specific executable, set `CLAUDE_BIN` or `CODEX_BIN` to its path.
