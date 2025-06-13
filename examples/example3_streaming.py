"""
Example 3: Manual handling of streaming output

This example demonstrates how to manually handle streaming output from the agent.
"""

from codesys import Agent
import json
import time

# Initialize an agent
agent = Agent(working_dir="./")

# Get a process for streaming manually
process = agent.run(
    prompt="Explain what an LLM Agent is in 3 sentences",
    stream=True,
    output_format="stream-json",  # Explicitly set the output format
    auto_print=False  # Don't auto-print, we'll handle the output manually
)

print("Streaming output manually, processing each line:")
for i, line in enumerate(process.stdout):
    # Skip empty lines
    if not line.strip():
        continue

    # Parse the JSON line
    try:
        data = json.loads(line)
        # Extract content if available
        content = data.get('content', '')
        if content:
            print(f"Line {i+1}: {content}")
        else:
            # Handle other message types (like 'init' or 'result')
            msg_type = data.get('type', 'unknown')
            print(f"Line {i+1} [type={msg_type}]: {data.get('message', '')}")
    except json.JSONDecodeError:
        print(f"Raw line: {line.strip()}")

    # Simulate processing time
    time.sleep(0.1)
    # Compare with agent.py lines 98-116 (auto-handling of streaming)