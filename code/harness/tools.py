"""Tools: schemas, validation, permissions, timeouts (Chapter 7)."""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .types import ToolCall

RISK_LEVELS = ("read", "write", "dangerous")
MODE_ALLOWS = {
    "read-only": {"read"},
    "default": {"read", "write"},          # dangerous tools need an approver
    "full": {"read", "write", "dangerous"},
}


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    fn: Callable[..., Any]
    risk: str = "read"
    timeout_s: float = 10.0

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description, "schema": self.schema}


def validate(schema: dict, data: Any, path: str = "$") -> list[str]:
    """A small JSON-Schema subset: type, properties, required, additionalProperties,
    items, enum, minimum, maximum, maxLength, pattern."""
    errs: list[str] = []
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool,
             "integer": int, "number": (int, float)}
    if t:
        ok = isinstance(data, types[t]) and not (t in ("integer", "number") and isinstance(data, bool))
        if not ok:
            return [f"{path}: expected {t}, got {type(data).__name__}"]
    if "enum" in schema and data not in schema["enum"]:
        errs.append(f"{path}: {data!r} not in {schema['enum']}")
    if t == "object":
        props = schema.get("properties", {})
        for r in schema.get("required", []):
            if r not in data:
                errs.append(f"{path}.{r}: required")
        for k, v in data.items():
            if k in props:
                errs += validate(props[k], v, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}.{k}: unexpected field")
    if t == "array" and "items" in schema:
        for i, v in enumerate(data):
            errs += validate(schema["items"], v, f"{path}[{i}]")
    if t in ("integer", "number"):
        if "minimum" in schema and data < schema["minimum"]:
            errs.append(f"{path}: {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errs.append(f"{path}: {data} > maximum {schema['maximum']}")
    if t == "string":
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errs.append(f"{path}: does not match {schema['pattern']}")
    return errs


class ToolRegistry:
    def __init__(self, max_output_chars: int = 4000):
        self._tools: dict[str, Tool] = {}
        self.max_output_chars = max_output_chars

    def register(self, tool: Tool) -> Tool:
        assert tool.risk in RISK_LEVELS, tool.risk
        self._tools[tool.name] = tool
        return tool

    def tool(self, name: str, description: str, schema: dict, risk: str = "read", timeout_s: float = 10.0):
        def deco(fn):
            self.register(Tool(name, description, schema, fn, risk, timeout_s))
            return fn
        return deco

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self, exclude: set[str] | None = None) -> list[dict]:
        # Sorted by name: a stable order keeps the prompt-cache prefix identical across requests.
        return [self._tools[n].spec() for n in self.names() if not exclude or n not in exclude]

    def execute(self, call: ToolCall, mode: str = "default",
                approver: Callable[[ToolCall], bool] | None = None) -> tuple[str, bool]:
        """Run one call. Returns (content, is_error). Errors are returned, never raised,
        so the model can read them and correct itself."""
        tool = self._tools.get(call.name)
        if tool is None:
            return f"Unknown tool {call.name!r}. Available tools: {', '.join(self.names())}", True
        errs = validate(tool.schema, call.input)
        if errs:
            return "Invalid input: " + "; ".join(errs), True
        if tool.risk not in MODE_ALLOWS[mode]:
            if not (approver and approver(call)):
                return f"Permission denied: {call.name} is a {tool.risk} tool and mode is {mode!r}", True
        with cf.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(tool.fn, **call.input)
            try:
                result = fut.result(timeout=tool.timeout_s)
            except cf.TimeoutError:
                return f"Tool {call.name} timed out after {tool.timeout_s}s", True
            except Exception as e:  # noqa: BLE001 - tool errors go back to the model
                return f"Tool {call.name} failed: {type(e).__name__}: {e}", True
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, sort_keys=True)
        if len(text) > self.max_output_chars:
            text = text[: self.max_output_chars] + f"\n[truncated {len(text) - self.max_output_chars} chars]"
        return text, False
