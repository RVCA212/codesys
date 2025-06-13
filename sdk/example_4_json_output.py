import os
import subprocess
import getpass
import json

# This example focuses on using the `--output-format json` flag to get
# structured, machine-readable output from the Claude Code CLI.
# This is crucial for programmatically integrating Claude into applications.
# It expands on the JSON parsing we did in the session management example.

def run_claude_with_json_output():
    """
    Runs Claude and processes the structured JSON output.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    try:
        # We'll ask Claude to perform a task that involves a tool call
        # to see how that is represented in the JSON output.
        prompt = "Read the first 2 lines of `sdk/example_1_basic_usage.py`"
        cmd = ["claude", "-p", prompt, "--output-format", "json"]

        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )

        print("\n--- Raw JSON Output ---")
        print(result.stdout)
        print("-----------------------\n")

        # --- Processing the JSON Output ---
        print("--- Parsed Conversation ---")
        try:
            # The output is a JSON string representing a list of messages
            messages = json.loads(result.stdout)

            for i, message in enumerate(messages):
                role = message.get("role", "N/A")
                print(f"Message {i+1}: Role = {role}")

                # Content is a list of blocks (e.g., text, tool_use)
                for content_block in message.get("content", []):
                    content_type = content_block.get("type", "N/A")

                    if content_type == "text":
                        print(f"  - Content (text): {content_block.get('text', '').strip()}")
                    elif content_type == "tool_use":
                        tool_name = content_block.get('name')
                        tool_input = content_block.get('input')
                        print(f"  - Tool Call: {tool_name}")
                        print(f"    - Input: {tool_input}")

                # The final message from the assistant will have the session_id
                if "session_id" in message:
                    print(f"Session ID from this message: {message['session_id']}")

            # The final human-readable response is typically the text content
            # of the last message from the "assistant".
            final_response = "Not found"
            if messages and messages[-1]["role"] == "assistant":
                 for block in messages[-1]['content']:
                     if block['type'] == 'text':
                         final_response = block['text']
                         break

            print("\n--- Extracted Final Response ---")
            print(final_response)
            print("--------------------------------\n")


        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing JSON: {e}")

    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Claude (return code {e.returncode}):")
        print(e.stderr)

if __name__ == "__main__":
    run_claude_with_json_output()