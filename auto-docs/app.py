#!/usr/bin/env python3

import argparse
import os
from codesys import Agent



# Hardcoded defaults - modify these values directly in the code if desired
DEFAULT_WORKING_DIR = os.getcwd()  # Use the current working directory by default


DEFAULT_USER_MESSAGE = "gener"  # Replace with your default message




def generate_plan(working_dir, user_message):
    """Generate a plan in plan.md based on the user message."""
    prompt = f'''
generate a plan into plan.md file given the following task:
<task>
{user_message}
</task>
Given this task, explore the codebase and create a plan for the implementation into plan.md. ultrathink
'''
    Agent(working_dir=working_dir).run(prompt, stream=True)





def execute_plan(working_dir):
    """Execute the plan laid out in plan.md."""
    prompt = '''
Implement the task laid out in plan.md: ultrathink
'''
    Agent(working_dir=working_dir).run(prompt, stream=True)




def main():
    parser = argparse.ArgumentParser(description='Generate and execute a plan based on a task.')
    parser.add_argument('--working-dir', '-w', help='Working directory for the agent')
    parser.add_argument('--message', '-m', help='Task message to generate plan for')

    args = parser.parse_args()

    # Use command-line args if provided, otherwise use hardcoded defaults
    working_dir = args.working_dir if args.working_dir else DEFAULT_WORKING_DIR
    user_message = args.message if args.message else DEFAULT_USER_MESSAGE

    print(f"Working directory: {working_dir}")
    print(f"Generating plan for task: {user_message}")
    generate_plan(working_dir, user_message)

    print("Executing plan from plan.md")
    execute_plan(working_dir)

if __name__ == "__main__":
    main()
