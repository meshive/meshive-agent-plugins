# Meshive for Claude Code

Use this plugin to compare GPU rental prices, find your workspaces, and check your pods from Claude Code.

## Try it

| Ask Claude | Expected result |
| --- | --- |
| “Which GPUs can I rent on Meshive, and what do they cost per hour?” | See public GPU offers and their hourly prices. You can run this before signing in. |
| “Which Meshive workspaces do I have access to?” | See the workspaces available to your Meshive account. |
| “List the pods in my Meshive workspaces.” | See your pods and their status, or an empty list if you have none. |

All three examples are read-only. You can try them with an empty workspace without renting a GPU. The workspace and pod examples require read access. Where OAuth is enabled, follow the Meshive sign-in prompt in your browser, approve read access, and repeat your request.

## Support

If the Meshive tools do not appear, open a new Claude Code session and run `/mcp` to check the connection. For manual access token setup and the tool reference, see the [Meshive MCP guide](https://docs.meshive.ai/sdk-cli/mcp/).

For technical support, see the [troubleshooting FAQ](https://docs.meshive.ai/getting-started/faq/#-troubleshooting) or email [admin@meshive.ai](mailto:admin@meshive.ai).
