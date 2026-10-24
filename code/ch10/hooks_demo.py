"""Chapter 10 lab: hooks enforce rules the model cannot talk its way around."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import Agent, AgentConfig, MockProvider, ToolRegistry
from harness.hooks import Deny, HookBus, Modify
from harness.providers import tool_call

reg = ToolRegistry()


@reg.tool("run_shell", "Run a shell command", {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]},
          risk="write")
def run_shell(cmd):
    return f"(pretend) ran: {cmd}"


hooks = HookBus()


@hooks.on("pre_tool")
def no_force_push(call, messages):
    if call.name == "run_shell" and "push --force" in call.input["cmd"]:
        return Deny("force-push to shared branches is not allowed")


@hooks.on("pre_tool")
def always_dry_run_deploys(call, messages):
    if call.name == "run_shell" and call.input["cmd"].startswith("deploy") and "--dry-run" not in call.input["cmd"]:
        return Modify({"cmd": call.input["cmd"] + " --dry-run"})


audit = []
hooks.on("post_tool", lambda call, content, is_error: audit.append((call.input["cmd"], "BLOCKED" if is_error else "ok")))

plan = iter([tool_call("run_shell", {"cmd": "pytest -q"}, id="a"),
             tool_call("run_shell", {"cmd": "git push --force origin main"}, id="b"),
             tool_call("run_shell", {"cmd": "deploy prod"}, id="c"),
             "All done."])
Agent(MockProvider(lambda s, m, t: next(plan)), reg, AgentConfig(model="mock-small"), hooks=hooks).run("Ship it")
for cmd, outcome in audit:
    print(f"{outcome:8s} {cmd}")
