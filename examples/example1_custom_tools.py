"""
Example 1: Customizing tools during initialization

This example demonstrates how to initialize an Agent with only specific tools.
"""

from codesys import Agent

# Initialize with only specific tools
restricted_agent = Agent(
    working_dir="./",
    allowed_tools=["Edit", "Write", "View"]  # Only allow editing, writing files and viewing
)  # Implementation in agent.py lines 19-39

print(f"Agent initialized with tools: {restricted_agent.allowed_tools}")