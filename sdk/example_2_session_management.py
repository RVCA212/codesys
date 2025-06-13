import os
import subprocess
import getpass
import json

# This example demonstrates how to manage multi-turn conversations with the Claude Code CLI.
# It corresponds to the "Multi-turn conversations" section of the documentation and the
# "Resume previous conversations" tutorial. This is similar to your `plan_and_execute.py`
# and `examples/example8_share_state.py` examples.

def run_claude_convo():
    """
    Demonstrates a multi-turn conversation with Claude, using session management.
    """
    # Use a shared environment for all calls to handle the API key
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    session_id = None

    try:
        # --- Step 1: Start a conversation and get a session ID ---
        print("--- Step 1: Starting conversation ---")
        prompt1 = "My name is Alex. I am writing a python script."
        # We use `--output-format json` to get structured output, which includes the session_id.
        cmd1 = ["claude", "-p", prompt1, "--output-format", "json"]

        result1 = subprocess.run(
            cmd1, capture_output=True, text=True, check=True, env=env
        )

        # The output is a JSON string representing a list of messages.
        # We parse it to extract the session_id from the last message.
        response1 = json.loads(result1.stdout)
        last_message = response1[-1]
        session_id = last_message.get("session_id")

        print("Claude's Response:")
        # The actual content is in the 'text' field of the 'content' block.
        print(last_message['content'][-1]['text'])
        print(f"\nSuccessfully started session: {session_id}")


        # --- Step 2: Continue the conversation using the session ID ---
        if session_id:
            print("\n--- Step 2: Resuming conversation with session ID ---")
            prompt2 = "What is my name?"
            # Use `--resume` to continue a specific session.
            cmd2 = ["claude", "-p", prompt2, "--resume", session_id]
            result2 = subprocess.run(
                cmd2, capture_output=True, text=True, check=True, env=env
            )
            print("Claude's Response:")
            print(result2.stdout)

        # --- Step 3: Continue the most recent conversation automatically ---
        print("\n--- Step 3: Continuing the most recent session with --continue ---")
        prompt3 = "What was the topic of our conversation?"
        # Use `--continue` to resume the last session without needing the ID.
        cmd3 = ["claude", "-p", prompt3, "--continue"]
        result3 = subprocess.run(
            cmd3, capture_output=True, text=True, check=True, env=env
        )
        print("Claude's Response:")
        print(result3.stdout)

    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Claude (return code {e.returncode}):")
        print(e.stderr)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing Claude's JSON output: {e}")
        print("This can happen if the response format changes or an error occurred.")

if __name__ == "__main__":
    run_claude_convo()