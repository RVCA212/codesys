"""
Example 6: Working with different project directories

This example demonstrates how to create an agent that works with a specific project directory.
"""

from codesys import Agent
import os

# Create an agent for a specific project
project_agent = Agent(working_dir=os.path.expanduser("~/my-project"))  # Implementation in agent.py lines 19-27 (working_dir parameter)

# Run a prompt related to that project
print("Running agent in a specific project directory...")
# Commented out to avoid actual execution:
# project_agent.run("Summarize this project", stream=True)  # Implementation in agent.py line 91 (cwd=self.working_dir)

print("Project directory example completed!")