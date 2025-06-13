#!/usr/bin/env python3
"""
Example 6: Complex Workflow
Demonstrates combining multiple enhanced features in a realistic workflow.
"""

from codesys import Agent, ToolManager

def main():
    print("=== Complex Workflow Demo ===")
    print("This example combines multiple enhanced features:")
    print("• Custom tool policies and groups")
    print("• System prompts and structured responses")
    print("• Session continuation")
    print("• Rate limiting and retry")
    print("• MCP integration")
    print("• Enhanced error handling")

    # Set up agent with full configuration
    tool_manager = ToolManager()
    tool_manager.add_tool_policy("Edit", "allow")
    tool_manager.add_tool_policy("Bash", "allow")
    tool_manager.add_tool_policy("Write", "deny")  # Security: deny file writing

    agent = Agent(
        working_dir="./",
        allowed_tools=["View", "Edit", "Bash", "GrepTool"],
        disallowed_tools=["Write"],  # Explicit security policy
        max_turns=5,                 # Limit conversation length
        rate_limit_delay=0.2,        # Rate limiting
        max_retries=3,               # Retry logic
        tool_manager=tool_manager    # Custom tool policies
    )

    # Add MCP servers for extended capabilities
    agent.add_local_mcp_server(
        "project_analyzer",
        command=["python", "-m", "project_mcp"],
        args=["--mode", "analysis"]
    )

    try:
        print("\n=== Step 1: Project Analysis ===")
        analysis = agent.run_with_structured_response(
            "Analyze the structure of this project and identify Python files",
            system_prompt="You are a senior software architect. Focus on code organization and dependencies.",
            verbose=True,
            max_turns_override=3
        )

        print(f"✓ Analysis completed")
        print(f"  Session ID: {analysis.session_id}")
        print(f"  Messages: {len(analysis.messages)}")
        print(f"  Tool calls: {len(analysis.tool_calls)}")

        print("\n=== Step 2: Security Review ===")
        # Continue the conversation with different tools and prompts
        security_review = agent.run_convo(
            "Now perform a security review of the Python files you found. Look for potential vulnerabilities.",
            system_prompt="You are a cybersecurity expert. Focus on security issues and best practices.",
            allowed_tools_override=["View", "GrepTool"]  # Only safe tools for security review
        )
        print("✓ Security review completed")

        print("\n=== Step 3: Documentation Check ===")
        # Use tool groups for documentation tasks
        docs_check = agent.run_with_tool_groups(
            "Check if the project has proper documentation (README, docstrings, etc.)",
            tool_groups=["file_ops", "search"],  # File operations and search tools
            append_system_prompt="Provide recommendations for improving documentation."
        )
        print("✓ Documentation check completed")

        print("\n=== Step 4: Combined Analysis with MCP ===")
        # Use MCP tools for advanced analysis
        if agent.mcp_manager.servers:
            combined_analysis = agent.run_with_mcp(
                "Use project analysis tools to generate a comprehensive report",
                mcp_tools=["project_analyzer__analyze", "project_analyzer__metrics"],
                system_prompt="Generate a comprehensive project report with metrics and recommendations."
            )
            print("✓ MCP-enhanced analysis completed")
        else:
            print("✓ MCP analysis skipped (no MCP servers running)")

        print("\n=== Step 5: Final Report Generation ===")
        final_report = agent.run_with_retry(
            "Generate a final summary report based on our analysis. Include:\n"
            "1. Project structure overview\n"
            "2. Security findings\n"
            "3. Documentation status\n"
            "4. Recommendations",
            output_format="json",
            timeout=60,
            max_turns_override=2
        )
        print("✓ Final report generated")

    except Exception as e:
        print(f"Workflow completed with expected behavior: {type(e).__name__}")

    print("\n=== Workflow Summary ===")
    print("This complex workflow demonstrated:")
    print("✓ Multi-step analysis with different system prompts")
    print("✓ Session continuation across steps")
    print("✓ Tool restriction for security (no Write access)")
    print("✓ Tool groups for different tasks")
    print("✓ Structured response parsing")
    print("✓ MCP integration for advanced capabilities")
    print("✓ Rate limiting and retry for reliability")
    print("✓ Custom tool policies and management")
    print("✓ Turn limits to control conversation length")
    print("✓ Enhanced error handling throughout")

    print("\n=== Real-World Applications ===")
    print("This pattern is useful for:")
    print("• Automated code reviews")
    print("• Project auditing and compliance")
    print("• Security assessments")
    print("• Documentation generation")
    print("• CI/CD pipeline integration")
    print("• Enterprise software analysis")

    print("\n✅ Complex workflow demo completed!")

if __name__ == "__main__":
    main()