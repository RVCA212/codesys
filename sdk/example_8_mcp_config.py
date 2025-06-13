import os
import subprocess
import getpass
import json

# This example demonstrates the advanced feature of using the Model Context
# Protocol (MCP) to extend Claude's capabilities with external tools.
# It corresponds to the "MCP Configuration" section of the documentation.

def create_mcp_config_file():
    """Creates a dummy MCP server configuration file for the example."""
    mcp_config = {
        "servers": {
            "filesystem": {
                "command": ["node", "filesystem_server.js"],
                "working_directory": "/tmp/mcp_filesystem"
            }
        }
    }
    with open("mcp_servers.json", "w") as f:
        json.dump(mcp_config, f, indent=2)
    print("Created dummy MCP config file: mcp_servers.json")

def run_claude_with_mcp():
    """
    Demonstrates the syntax for running Claude with an MCP configuration.
    """
    env = os.environ.copy()
    if "ANTHROPIC_API_KEY" not in env:
        try:
            env["ANTHROPIC_API_KEY"] = getpass.getpass("Enter Anthropic API Key: ")
        except (IOError, EOFError):
            print("Could not read API key.", file=os.sys.stderr)
            return

    create_mcp_config_file()

    try:
        # This prompt is designed to invoke our hypothetical MCP tool.
        prompt = "Using the custom filesystem tool, list the contents of the root directory."

        # The tool name for --allowedTools follows the format: mcp__<serverName>__<toolName>
        # Since the MCP server defines the tools, we often just allow the server itself.
        # Let's assume the tool is named 'ls' by the server.
        allowed_tool_name = "mcp__filesystem__ls"

        # 1. --mcp-config points to our server definition file.
        # 2. --allowedTools must explicitly grant permission to use the MCP tool.
        cmd = [
            "claude",
            "-p", prompt,
            "--mcp-config", "mcp_servers.json",
            "--allowedTools", allowed_tool_name, "LSTool" # Allow regular ls too
        ]

        print(f"\nCommand: {' '.join(cmd)}")
        print("\nNOTE: This command is expected to fail because the MCP server defined")
        print("in mcp_servers.json (filesystem_server.js) does not actually exist.")
        print("The purpose of this example is to demonstrate the correct syntax.")

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, env=env # check=False because we expect an error
        )

        print("\n--- Claude CLI Output ---")
        if result.returncode == 0:
            print("Success! (This is unexpected, but here's the output):")
            print(result.stdout)
        else:
            print(f"As expected, the command failed (return code {result.returncode}).")
            print("This is because the MCP server could not be started.")
            print("\nStderr:")
            print(result.stderr)
        print("-------------------------\n")


    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Please ensure the Claude Code CLI is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Clean up the dummy config file
        if os.path.exists("mcp_servers.json"):
            os.remove("mcp_servers.json")
            print("Cleaned up dummy MCP config file.")

if __name__ == "__main__":
    run_claude_with_mcp()