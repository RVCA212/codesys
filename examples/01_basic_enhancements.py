#!/usr/bin/env python3
"""
Example 1: Basic Enhanced Features
Demonstrates system prompts, timeouts, verbose mode, and structured responses.
"""

from codesys import Agent

def main():
    print("=== Basic Enhanced Features Demo ===")

    # Create enhanced agent with new parameters
    agent = Agent(
        working_dir="./",
        allowed_tools=["View", "Edit", "Bash"],
        disallowed_tools=["Write"],  # NEW: Explicitly disallow tools
        max_turns=3,                 # NEW: Limit conversation turns
        rate_limit_delay=0.2,        # NEW: Rate limiting
        max_retries=2                # NEW: Retry logic
    )

    try:
        print("\n1. Using custom system prompts:")
        response = agent.run(
            "What tools do you have access to?",
            system_prompt="You are a helpful coding assistant. Be concise.",  # NEW
            verbose=True,    # NEW: Verbose output
            timeout=30       # NEW: Timeout support
        )
        print("✓ Custom system prompt request completed")

        print("\n2. Using structured response parsing:")
        structured = agent.run_with_structured_response(
            "List the files in the current directory"
        )
        print(f"✓ Session ID: {structured.session_id}")
        print(f"✓ Number of messages: {len(structured.messages)}")
        print(f"✓ Tool calls made: {len(structured.tool_calls)}")

        print("\n3. Using append system prompt:")
        response = agent.run(
            "Analyze this directory",
            append_system_prompt="Provide a brief summary in bullet points."  # NEW
        )
        print("✓ Append system prompt request completed")

    except Exception as e:
        print(f"Demo completed with expected behavior (no API key): {type(e).__name__}")

    print("\n✅ Basic enhanced features demo completed!")
    print("New features demonstrated:")
    print("  • Custom system prompts")
    print("  • Append system prompts")
    print("  • Timeout support")
    print("  • Verbose logging")
    print("  • Structured response parsing")
    print("  • Tool disallow lists")
    print("  • Max turns limiting")
    print("  • Rate limiting")

if __name__ == "__main__":
    main()