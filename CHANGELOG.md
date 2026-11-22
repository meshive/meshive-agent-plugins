# Changelog

## 0.1.1

- Fixed an issue that prevented some Codex versions from loading Meshive tools when the MCP server configuration contained an `extensions` field. Both plugin versions were bumped so existing 0.1.0 installations can pick up the fix.
- Removed the distribution ZIP. Claude Code and Codex install directly from their respective plugin folders in this repository.
- Added installation and upgrade instructions for each client, checks for the marketplace configuration, and an upgrade test that verifies the MCP tools each client lists.

## 0.1.0

- Added Meshive marketplace packages for Claude Code and Codex. Installing either plugin registers the hosted Meshive MCP server.
