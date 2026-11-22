"""Enumerate a plugin's actual tools using the client's control protocol."""

import asyncio
import json


async def list_tools(client, executable, profile_env, project):
    if client == "claude":
        args = ["-p", "--input-format", "stream-json", "--output-format", "stream-json",
                "--verbose", "--no-session-persistence"]
    else:
        args = ["-c", f'projects.{json.dumps(str(project))}.trust_level="trusted"',
                "-c", 'mcp_oauth_credentials_store="file"', "app-server", "--stdio"]
    proc = await asyncio.create_subprocess_exec(
        executable, *args, cwd=project, env=profile_env, stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, limit=8 * 1024 * 1024,
    )

    async def send(message):
        proc.stdin.write((json.dumps(message) + "\n").encode())
        await proc.stdin.drain()

    async def request(number, method, params=None):
        if client == "claude":
            await send({"type": "control_request", "request_id": str(number),
                        "request": {"subtype": method}})
        else:
            await send({"id": number, "method": method, "params": params})
        while True:
            line = await proc.stdout.readline()
            if not line:
                raise RuntimeError(f"{client} closed before replying to {method}")
            reply = json.loads(line)
            if client == "claude":
                result = reply.get("response", {})
                if reply.get("type") == "control_response" and result.get("request_id") == str(number):
                    if result["subtype"] != "success":
                        raise RuntimeError(f"Claude Code rejected {method}")
                    return result["response"]
            elif reply.get("id") == number:
                if "error" in reply:
                    raise RuntimeError(f"Codex rejected {method}: {reply['error'].get('code')}")
                return reply["result"]

    async def discover():
        if client == "claude":
            await request(1, "initialize")
            number = 2
            while True:
                result = await request(number, "mcp_status")
                for server in result["mcpServers"]:
                    if server["name"] == "plugin:meshive:meshive" and server["status"] == "connected":
                        return {tool["name"] for tool in server["tools"]}
                number += 1
                await asyncio.sleep(0.4)
        await request(1, "initialize", {"clientInfo": {"name": "meshive-test", "version": "1"},
                                        "capabilities": {"experimentalApi": True}})
        await send({"method": "initialized"})
        session = await request(2, "thread/start", {"ephemeral": True, "cwd": str(project),
                                                    "approvalPolicy": "never", "sandbox": "read-only"})
        params = {"threadId": session["thread"]["id"]}
        number = 3
        while True:
            result = await request(number, "mcpServerStatus/list", params)
            for server in result["data"]:
                if server["name"] == "meshive" and server.get("tools"):
                    return set(server["tools"])
            if result.get("nextCursor"):
                params["cursor"] = result["nextCursor"]
            else:
                params.pop("cursor", None)
                await asyncio.sleep(0.4)
            number += 1

    try:
        return await asyncio.wait_for(discover(), timeout=45)
    finally:
        if proc.returncode is None:
            proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=4)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
