"""
Example 2: Using run_with_tools for temporary tool changes

This example demonstrates how to temporarily override allowed tools for a single operation.
"""

from codesys import Agent

# Initialize with default tools
agent = Agent(working_dir="./")  # Implementation in agent.py lines 19-39
print(f"Default tools: {agent.allowed_tools}")

# Run with only specific tools for one operation
bash_only_response = agent.run_with_tools(
    prompt="List files in the current directory",
    tools=["Bash"],  # Only allow Bash for this specific run
    stream=False
)  # Implementation in agent.py lines 132-155

print(f"Tools after run_with_tools: {agent.allowed_tools}  # Original tools are restored")