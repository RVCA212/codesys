#!/usr/bin/env python3

import os
from codesys import Agent

# Configuration - modify these values as needed
WORKING_DIR = os.getcwd()  # Use the current working directory

USER_MESSAGE = """
make me a million dollars
"""

def generate_plan_and_execute():
    """Generate a plan and then execute it using the same conversation session."""
    agent = Agent(working_dir=WORKING_DIR)

    prompt1 = f'''
    /init
    '''
    agent.run(prompt1, stream=True)

    # Step 1: Generate the plan
    print("Generating plan...")
    prompt2 = f'''
generate a plan into plan.md file given the following task:
<task>
{USER_MESSAGE}
</task>
Given this task, explore the codebase and create a plan for the implementation into plan.md. ultrathink
'''
    agent.run_convo(prompt2, stream=True)

    # Step 2: Execute the plan continuing the same conversation
    print("\nExecuting plan from plan.md...")
    prompt3 = '''
Given the plan in plan.md, execute the plan step by step by exploring the codebase
and following your todo list of tasks until the plan is complete.
'''
    agent.run_convo(prompt3, stream=True)

if __name__ == "__main__":
    print(f"Working directory: {WORKING_DIR}")
    print(f"Task: {USER_MESSAGE}")
    generate_plan_and_execute()
