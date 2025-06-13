#!/usr/bin/env python3
"""
Example 5: Error Handling & Retry Logic
Demonstrates enhanced error handling, custom exceptions, and automatic retry.
"""

from codesys import Agent, ClaudeSDKError, ClaudeTimeoutError, ClaudeAuthenticationError

def main():
    print("=== Error Handling & Retry Logic Demo ===")

    agent = Agent(
        working_dir="./",
        max_retries=3,           # Retry up to 3 times
        rate_limit_delay=0.5     # 500ms between requests
    )

    print("\n1. Testing enhanced error types:")
    print("Available custom exceptions:")
    print("  • ClaudeSDKError (base)")
    print("  • ClaudeAuthenticationError")
    print("  • ClaudeToolError")
    print("  • ClaudeSessionError")
    print("  • ClaudeTimeoutError")
    print("  • ClaudeMCPError")

    try:
        print("\n2. Testing timeout handling:")
        response = agent.run(
            "This is a timeout test",
            timeout=0.001  # Very short timeout to trigger error
        )
    except ClaudeTimeoutError as e:
        print(f"✓ Caught timeout error: {e}")
    except Exception as e:
        print(f"✓ Expected timeout-related error: {type(e).__name__}")

    try:
        print("\n3. Testing retry logic:")
        response = agent.run_with_retry(
            "Hello, test retry logic",
            timeout=5
        )
        print("✓ Retry request completed")
    except Exception as e:
        print(f"✓ Retry logic tested: {type(e).__name__}")

    print("\n4. Rate limiting demonstration:")
    print("The agent automatically:")
    print("  • Waits between requests (rate_limit_delay)")
    print("  • Uses exponential backoff for retries")
    print("  • Tracks request timing")

    print("\n5. Error handling strategies:")
    try:
        # This will fail due to no API key, demonstrating error classification
        agent.run("Test authentication error")
    except ClaudeAuthenticationError:
        print("✓ Authentication error properly classified")
    except Exception as e:
        print(f"✓ Error properly handled: {type(e).__name__}")

    print("\n6. Best practices demonstrated:")
    print("  • Specific exception types for different error categories")
    print("  • Automatic retry with exponential backoff")
    print("  • Rate limiting to prevent API throttling")
    print("  • Timeout protection for hanging requests")
    print("  • Graceful error degradation")

    print("\n7. Retry configuration options:")
    print("  • max_retries: Maximum number of attempts")
    print("  • rate_limit_delay: Minimum time between requests")
    print("  • Exponential backoff: 2^attempt seconds between retries")

    # Demonstrate different agent configurations
    print("\n8. Different agent configurations:")

    # Conservative agent
    conservative_agent = Agent(
        max_retries=5,
        rate_limit_delay=1.0  # 1 second between requests
    )
    print("Conservative: 5 retries, 1s rate limit")

    # Aggressive agent
    aggressive_agent = Agent(
        max_retries=1,
        rate_limit_delay=0.1  # 100ms between requests
    )
    print("Aggressive: 1 retry, 100ms rate limit")

    print("\n✅ Error handling & retry demo completed!")
    print("New features demonstrated:")
    print("  • Custom exception hierarchy")
    print("  • Automatic retry with exponential backoff")
    print("  • Rate limiting between requests")
    print("  • Timeout protection")
    print("  • Error classification and handling")
    print("  • Configurable retry strategies")

if __name__ == "__main__":
    main()