import os
import asyncio
import getpass

# This example demonstrates how to run the Claude Code CLI asynchronously
# using Python's `asyncio` library. This is useful for applications that
# need to perform other tasks while waiting for Claude's response, or
# for running multiple Claude instances concurrently. This mirrors the
# `AsyncAgent` class in your `agent.py`.

async def run_claude_async(prompt: str, env: dict):
    """
    Runs a single Claude command asynchronously.

    Args:
        prompt: The prompt to send to Claude.
        env: The environment variables, including the API key.

    Returns:
        The standard output from the Claude command.
    """
    cmd = ["claude", "-p", prompt]
    print(f"Starting async run for prompt: '{prompt}'")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"Error in async run for prompt '{prompt}':")
        print(stderr.decode())
        return None

    print(f"Finished async run for prompt: '{prompt}'")
    return stdout.decode()

async def main():
    """
    Main asynchronous function to set up the environment and run examples.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    # --- Example 1: Run a single async command ---
    print("--- Running a single async command ---")
    response = await run_claude_async("What is the capital of France?", env)
    if response:
        print("Response:\n", response)

    # --- Example 2: Run multiple commands concurrently ---
    print("\n--- Running two commands concurrently ---")
    prompts = [
        "Write a haiku about Python.",
        "Write a haiku about asynchronous code."
    ]

    # Create a list of tasks to run
    tasks = [run_claude_async(p, env) for p in prompts]

    # asyncio.gather runs the tasks concurrently and waits for them all to complete
    responses = await asyncio.gather(*tasks)

    for i, resp in enumerate(responses):
        if resp:
            print(f"--- Response for prompt {i+1} ---")
            print(resp)
            print("---------------------------------")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")