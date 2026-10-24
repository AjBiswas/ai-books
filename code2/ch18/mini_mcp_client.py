"""Book 2, Chapter 18 lab: an MCP client (the harness side) talking to mini_mcp_server.py.

Run:  python mini_mcp_client.py
"""
import json
import os
import subprocess
import sys

server = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "mini_mcp_server.py")],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def send(msg, expect_reply=True):
    print(">>", json.dumps(msg))
    server.stdin.write(json.dumps(msg) + "\n")
    server.stdin.flush()
    if expect_reply:
        reply = json.loads(server.stdout.readline())
        print("<<", json.dumps(reply))
        return reply


send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                 "clientInfo": {"name": "book-client", "version": "1.0"}}})
send({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_reply=False)
tools = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
print(f"\nThe harness now shows the model {len(tools)} tool(s): {[t['name'] for t in tools]}\n")
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "leave_balance", "arguments": {"employee_id": "E100"}}})
send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "leave_balance", "arguments": {"employee_id": "E999"}}})
server.stdin.close()
server.wait()
