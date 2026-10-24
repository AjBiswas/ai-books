"""A small, provider-agnostic agent harness built chapter by chapter in "Building the Harness".

Every module runs offline with MockProvider, so the whole book can be followed without an API key.
"""
from .types import Message, ToolCall, Usage, Response
from .providers import Provider, MockProvider, AnthropicProvider, OpenAICompatProvider
from .tools import Tool, ToolRegistry
from .loop import Agent, AgentConfig, RunResult

__all__ = [
    "Message", "ToolCall", "Usage", "Response",
    "Provider", "MockProvider", "AnthropicProvider", "OpenAICompatProvider",
    "Tool", "ToolRegistry", "Agent", "AgentConfig", "RunResult",
]
