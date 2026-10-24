"""Book 1, Chapter 18 lab: an MCP server written from scratch, so you can see the protocol.

MCP over stdio = JSON-RPC 2.0 messages, one per line, on stdin/stdout.
For real projects use the official SDK (pip install mcp):

    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("leave-server")
    @mcp.tool()
    def leave_balance(employee_id: str) -> str: ...
    mcp.run()
"""
import json
import sys

LEAVE = {"E100": 12, "E200": 3}

TOOLS = [{
    "name": "leave_balance",
    "description": "Get the remaining paid-leave days for an employee ID like E100.",
    "inputSchema": {"type": "object", "properties": {"employee_id": {"type": "string"}},
                    "required": ["employee_id"]},
}]


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": msg["params"].get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "leave-server", "version": "0.1.0"}}}
    if method == "notifications/initialized":
        return None                                   # notifications get no reply
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name, args = msg["params"]["name"], msg["params"].get("arguments", {})
        if name != "leave_balance":
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
        emp = args.get("employee_id", "")
        if emp not in LEAVE:
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": f"No employee {emp}"}], "isError": True}}
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "content": [{"type": "text", "text": f"{emp} has {LEAVE[emp]} leave days left"}], "isError": False}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    reply = handle(json.loads(line))
    if reply is not None:
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()
