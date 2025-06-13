"""
Example 5: Error handling

This example demonstrates how to handle errors in the agent.
"""

from codesys import Agent

# Initialize an agent
agent = Agent(working_dir="./")

# Error handling example
try:
    # Attempt to use an invalid configuration
    agent.run(
        prompt="This should fail",
        additional_args={"invalid_param": True}  # Invalid parameter
    )  # Implementation in agent.py lines 119-130 (error handling in subprocess.run)
except Exception as e:
    print(f"Caught expected error: {str(e)}")