import os
import subprocess
import getpass
import json

# This example demonstrates how to use custom system prompts to guide
# Claude's behavior, corresponding to the "Custom system prompts"
# section of the documentation. This allows for significant customization
# of Claude's persona, response style, and task focus.

def run_claude_with_system_prompts():
    """
    Demonstrates using --system-prompt and --append-system-prompt.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    try:
        # --- Example 1: Overriding the system prompt ---
        # We can make Claude adopt a specific persona. Here, a pirate.
        print("--- Example 1: Overriding system prompt with a persona ---")
        pirate_prompt = "You are a friendly pirate. All your responses must be in pirate dialect."
        user_prompt_1 = "What are the benefits of using a version control system like git?"

        cmd1 = ["claude", "-p", user_prompt_1, "--system-prompt", pirate_prompt]

        print(f"Command: {' '.join(cmd1)}")
        result1 = subprocess.run(
            cmd1, capture_output=True, text=True, check=True, env=env
        )
        print("Claude's Pirate Response:")
        print(result1.stdout)

        # --- Example 2: Appending to the system prompt for format control ---
        # Here, we append an instruction to get a structured JSON response.
        print("\n--- Example 2: Appending to system prompt for JSON output ---")
        append_prompt = "Please provide your response as a single JSON object with two keys: 'summary' and 'language'."
        user_prompt_2 = "Analyze the following code snippet and identify the programming language: `def hello(): print('world')`"

        # We don't need the claude CLI's --output-format json, as we are asking the model itself
        # to generate a JSON string in its response content.
        cmd2 = ["claude", "-p", user_prompt_2, "--append-system-prompt", append_prompt]

        print(f"Command: {' '.join(cmd2)}")
        result2 = subprocess.run(
            cmd2, capture_output=True, text=True, check=True, env=env
        )
        print("Claude's JSON-formatted Response:")
        print(result2.stdout)

        # We can try to parse the JSON to verify it's correct
        try:
            parsed_json = json.loads(result2.stdout)
            print("\nSuccessfully parsed response as JSON:")
            print(parsed_json)
        except json.JSONDecodeError:
            print("\nCould not parse the response as JSON. The model may not have perfectly followed instructions.")


    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Claude (return code {e.returncode}):")
        print(e.stderr)

if __name__ == "__main__":
    run_claude_with_system_prompts()