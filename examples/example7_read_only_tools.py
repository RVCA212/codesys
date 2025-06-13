"""
Example 7: Using read-only tools

This example demonstrates how to initialize an Agent with only read-only tools,
which can be useful for analysis tasks where file modifications should be prevented.
"""

from codesys import Agent

read_only_agent = Agent(
    working_dir="/Users/seansullivan/codesys/",
    allowed_tools=[
        "View",        # For reading files
        "GlobTool",    # For finding files by pattern
        "GrepTool",    # For searching file contents
        "LSTool",      # For listing directory contents
        "WebFetch" # For fetching web content
    ]
)


# Run Claude with the prompt
response = read_only_agent.run('''create a new blank file called "test.txt"''', stream=True)
