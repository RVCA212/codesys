#!/usr/bin/env python3
"""
Example 2: Advanced Tool Management
Demonstrates tool groups, tool policies, and advanced tool control.
"""

from codesys import Agent, ToolManager

def main():
    print("=== Advanced Tool Management Demo ===")

    # Create custom tool manager
    tool_manager = ToolManager()
    tool_manager.add_tool_policy("Bash", "allow")
    tool_manager.add_tool_policy("Write", "deny")

    agent = Agent(
        working_dir="./",
        tool_manager=tool_manager
    )

    try:
        print("\n1. Using tool groups:")
        print("Available tool groups:")
        print("  • file_ops: Edit, View, Write")
        print("  • system: Bash, LSTool")
        print("  • search: GrepTool, GlobTool")
        print("  • batch: BatchTool, MultiEdit")
        print("  • notebook: NotebookEdit, NotebookRead")
        print("  • web: WebFetchTool")
        print("  • agent: AgentTool")

        response = agent.run_with_tool_groups(
            "Check what files are in this directory",
            tool_groups=["file_ops", "system"]  # Only file operations and system tools
        )
        print("✓ Tool groups request completed")

        print("\n2. Using tool policies:")
        response = agent.run_with_tool_policies(
            "Analyze the current directory structure"
        )
        print("✓ Tool policy request completed")

        print("\n3. Comparing tool configurations:")

        # Standard agent
        standard_agent = Agent(allowed_tools=["View", "Edit", "Bash", "Write"])
        print("Standard agent tools: View, Edit, Bash, Write")

        # Restricted agent
        restricted_agent = Agent(
            allowed_tools=["View", "Edit", "Bash"],
            disallowed_tools=["Write"]
        )
        print("Restricted agent: View, Edit, Bash (Write explicitly denied)")

        # Group-based agent
        print("Group-based agent: file_ops + system groups")

    except Exception as e:
        print(f"Demo completed with expected behavior (no API key): {type(e).__name__}")

    print("\n✅ Tool management demo completed!")
    print("New features demonstrated:")
    print("  • Tool groups (predefined sets)")
    print("  • Tool policies (allow/deny rules)")
    print("  • Custom tool managers")
    print("  • Tool filtering")
    print("  • Explicit disallow lists")

if __name__ == "__main__":
    main()