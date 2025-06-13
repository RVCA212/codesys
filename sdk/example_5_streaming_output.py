import os
import subprocess
import getpass
import json

# This example demonstrates how to handle streaming output from the Claude Code CLI.
# This is useful for applications that want to show Claude's response in real-time,
# similar to the `stream=True` functionality in your `agent.py`.
# It uses the `--output-format stream-json` flag.

def run_claude_with_streaming():
    """
    Runs Claude and processes the streaming JSON output in real-time.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    try:
        prompt = "Tell me a short story about a robot who discovers music."
        # The `--verbose` flag is recommended with `stream-json` to get all message types.
        cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]

        print(f"Command: {' '.join(cmd)}\n")
        print("--- Streaming Claude's Response ---")

        # We use Popen for streaming, which allows us to read the output line-by-line.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered
            env=env,
        )

        # Read and process the output stream line by line
        for line in process.stdout:
            try:
                # Each line is a self-contained JSON object
                message = json.loads(line)

                # We can inspect the message type to decide how to process it.
                msg_type = message.get("type")

                if msg_type == "message":
                    content_type = message.get("content", {}).get("type")
                    if content_type == "text_delta":
                        # For text responses, we get a stream of 'text_delta' chunks.
                        # We can print them as they arrive to show the response building up.
                        print(message["content"]["text"], end="", flush=True)

                # You could add more logic here to handle other message types,
                # like 'tool_use_start', 'tool_use_delta', 'tool_use_result', etc.

            except json.JSONDecodeError:
                # Ignore lines that are not valid JSON
                pass

        print("\n-----------------------------------\n")

        # Wait for the process to finish and check for errors
        return_code = process.wait()
        if return_code != 0:
            print(f"Error executing Claude (return code {return_code}):")
            stderr = process.stderr.read()
            print(stderr)

    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_claude_with_streaming()