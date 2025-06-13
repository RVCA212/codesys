import os
import subprocess
import getpass

# This example demonstrates basic, non-interactive use of the Claude Code CLI.
# It corresponds to the "Basic SDK usage" section of the documentation.
# We use Python's subprocess module to call the `claude` command.

def run_claude_simple(prompt: str, api_key: str = None):
    """
    Runs a simple, non-interactive prompt with the Claude Code CLI.

    Args:
        prompt: The prompt to send to Claude.
        api_key: The Anthropic API key. If not provided, it will be
                 read from the ANTHROPIC_API_KEY environment variable.
    """
    print(f"Running prompt: '{prompt}'")

    # Prepare the command-line arguments for the claude tool.
    # The `-p` or `--print` flag is used for non-interactive mode.
    cmd = ["claude", "-p", prompt]

    # It's a security best practice to pass the API key via an environment
    # variable rather than a command-line argument.
    env = os.environ.copy()
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key

    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    try:
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,  # This will raise CalledProcessError on non-zero exit codes
            env=env,
        )

        print("\n--- Claude's Response ---")
        print(result.stdout)
        print("-------------------------\n")

    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Claude (return code {e.returncode}):")
        print(e.stderr)

if __name__ == "__main__":
    # Example taken from your `example.py`
    run_claude_simple("hello")

    # Example from the "Use Claude as a unix-style utility" tutorial
    run_claude_simple("translate this to french: 'good morning'")