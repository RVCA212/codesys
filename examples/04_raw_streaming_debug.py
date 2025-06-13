#!/usr/bin/env python3
"""
Debug: Raw Streaming Output
Shows the actual JSON chunks that come from Claude CLI streaming.
"""

from codesys import Agent
import json

# Initialize with a working directory
agent = Agent(working_dir="/Users/seansullivan/codesys/")

print("=== Raw Streaming Debug ===")
print("This shows the actual JSON chunks from Claude CLI:")
print()

# Get the raw process for manual streaming
process = agent.run(
    "Say hello and write a simple Python script",
    stream=True,
    auto_print=False  # Don't auto-print, we'll process manually
)

try:
    for line in process.stdout:
        print(f"RAW JSON: {line.rstrip()}")
        try:
            # Try to parse each JSON line
            data = json.loads(line)
            print(f"PARSED: type={data.get('type')}, keys={list(data.keys())}")
            if data.get('type') == 'assistant':
                print(f"CONTENT: {data.get('message', {}).get('content', [])}")
            print("-" * 50)
        except json.JSONDecodeError as e:
            print(f"JSON PARSE ERROR: {e}")
            print("-" * 50)
except KeyboardInterrupt:
    print("\nStreaming interrupted")
    process.terminate()

process.wait()
print("Debug complete!")