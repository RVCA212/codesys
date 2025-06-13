#!/usr/bin/env python3
"""
Simple Enhanced Streaming Example
Shows how to use custom handlers for streaming output.
"""

from codesys import Agent

# Initialize with a working directory
agent = Agent(working_dir="/Users/seansullivan/codesys/")

# Define simple handlers
def on_text(text):
    print(f"📝 {text}", end="", flush=True)

def on_tool(tool_call):
    print(f"\n🔧 Tool used: {tool_call.get('name', 'unknown')}")

def on_error(error):
    print(f"\n❌ Error: {error}")

# Use enhanced streaming with custom handlers
print("=== Enhanced Streaming with Handlers ===")
result = agent.run_streaming_with_handlers(
    "Write a simple hello world script",
    text_handler=on_text,
    tool_handler=on_tool,
    error_handler=on_error
)

print(f"\n\n✅ Streaming completed! Collected {len(result)} characters of text.")