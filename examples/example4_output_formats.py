"""
Example 4: Using output formats and additional arguments

This example demonstrates how to use different output formats and pass additional arguments.
"""

from codesys import Agent

# Initialize an agent
agent = Agent(working_dir="./")

# Run with custom output format and additional arguments
analysis = agent.run_with_structured_response(
    "hello",
    system_prompt="You are a senior software architect. Focus on code organization and dependencies.",
    verbose=True,
    max_turns_override=3,
    stream=True
)



print(f"✓ Analysis completed")
print(f"  Session ID: {analysis.session_id}")
print(f"  Messages: {len(analysis.messages)}")
print(f"  Tool calls: {len(analysis.tool_calls)}")

print(analysis.messages)