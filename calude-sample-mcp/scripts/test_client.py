"""
Minimal MCP client used only to smoke-test server.py over stdio.
Spawns the server as a subprocess and exchanges JSON-RPC messages with it,
exactly like a real MCP client would.
"""
import json
import subprocess
import sys
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parent.parent / "server.py"


class MCPTestClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, str(SERVER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._id = 0

    def _next_id(self):
        self._id += 1
        return self._id

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _read(self):
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read()
            raise RuntimeError(f"Server closed stdout unexpectedly. stderr:\n{err}")
        return json.loads(line)

    def request(self, method, params=None):
        msg_id = self._next_id()
        self._send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})
        return self._read()

    def notify(self, method, params=None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def call_tool(self, name, arguments=None):
        resp = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        content = resp["result"]["content"][0]["text"]
        return json.loads(content)

    def close(self):
        self.proc.terminate()
        self.proc.wait(timeout=5)


def main():
    client = MCPTestClient()
    try:
        init = client.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.1.0"},
        })
        print("initialize ->", json.dumps(init["result"], indent=2))
        client.notify("notifications/initialized")

        tools = client.request("tools/list")
        print("\ntools/list ->", [t["name"] for t in tools["result"]["tools"]])

        print("\nQ: How many Samsung accounts are there?")
        result = client.call_tool("count_accounts", {"filters": {"brand": "Samsung"}})
        print("A:", json.dumps(result, indent=2))

        print("\nQ: Break down accounts by brand")
        result = client.call_tool("group_by_stats", {"group_by": "brand"})
        print("A:", json.dumps(result, indent=2))

        print("\nQ: How many active Samsung accounts are on the premium plan?")
        result = client.call_tool("count_accounts", {
            "filters": {"brand": "Samsung", "status": "active", "plan": "premium"}
        })
        print("A:", json.dumps(result, indent=2))

        print("\nQ: List 3 Samsung accounts")
        result = client.call_tool("list_accounts", {"filters": {"brand": "Samsung"}, "limit": 3})
        print("A:", json.dumps(result, indent=2))

        print("\nQ: Fetch account acct_00001")
        result = client.call_tool("get_account", {"account_id": "acct_00001"})
        print("A:", json.dumps(result, indent=2))

        print("\nQ: Unknown tool should produce a clean JSON-RPC error")
        bad = client.request("tools/call", {"name": "nope", "arguments": {}})
        print("A:", json.dumps(bad, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
