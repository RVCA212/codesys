import os
import subprocess
import getpass

# This example demonstrates how to control which tools Claude can use.
# It corresponds to the `--allowedTools` and `--disallowedTools` flags in the documentation.
# This pattern is similar to your `examples/example7_read_only_tools.py` and
# `examples/example2_run_with_tools.py`.

def run_claude_with_tool_control():
    """
    Demonstrates running Claude with a restricted set of tools.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    try:
        # --- Step 1: Run with only read-only tools ---
        # This is useful for analysis tasks where you want to prevent modifications.
        print("--- Step 1: Running with read-only tools ---")
        read_only_tools = ["View", "GlobTool", "GrepTool", "LSTool"]
        prompt1 = "List the files in the current directory."

        # The `--allowedTools` flag takes a space- or comma-separated list of tool names.
        cmd1 = ["claude", "-p", prompt1, "--allowedTools"] + read_only_tools

        print(f"Command: {' '.join(cmd1)}")
        result1 = subprocess.run(
            cmd1, capture_output=True, text=True, check=True, env=env
        )
        print("Claude's Response:")
        print(result1.stdout)

        # --- Step 2: Attempt an action that requires a disallowed tool ---
        # Here, we ask Claude to create a file, but we don't allow the "Edit" or "Write" tool.
        # We expect Claude to state that it cannot perform the action.
        print("\n--- Step 2: Attempting to use a disallowed tool ---")
        prompt2 = 'Create a new file named "test_file.txt" with the content "hello".'

        # We use the same read-only toolset as before.
        cmd2 = ["claude", "-p", prompt2, "--allowedTools"] + read_only_tools

        print(f"Command: {' '.join(cmd2)}")
        result2 = subprocess.run(
            cmd2, capture_output=True, text=True, check=True, env=env
        )

        print("Claude's Response (should indicate inability to write file):")
        print(result2.stdout)

    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Claude (return code {e.returncode}):")
        print(e.stderr)

if __name__ == "__main__":
    run_claude_with_tool_control()