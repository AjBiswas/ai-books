"""Chapter 5 lab: one conversation, translated into each provider's wire format."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import AnthropicProvider, Message, OpenAICompatProvider, ToolCall

conversation = [
    Message("user", "Weather in Pune?"),
    Message("assistant", "Checking.", [ToolCall("call_1", "get_weather", {"city": "Pune"})]),
    Message("tool", '{"temp_c": 24, "sky": "cloudy"}', tool_call_id="call_1"),
]
print("== Anthropic Messages API ==")
print(json.dumps(AnthropicProvider.to_wire(conversation), indent=1))
print("\n== OpenAI-compatible Chat Completions (OpenAI, vLLM, Ollama, Gemini compat) ==")
print(json.dumps(OpenAICompatProvider.to_wire("You are helpful.", conversation), indent=1))
