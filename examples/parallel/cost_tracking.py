#!/usr/bin/env python3
"""
Parallel execution with cost tracking.
Shows how to run multiple Claude requests in parallel and capture cost information.
"""

import asyncio
import json
from codesys import AsyncAgent


async def parallel_with_cost():
    """Run multiple requests in parallel and capture cost information."""
    agent = AsyncAgent()

    async def run_with_cost(prompt, label):
        """Run a single prompt and return result with cost info."""
        try:
            # Use structured response to get cost information
            response = await agent.run_with_structured_response(prompt)

            # Extract cost from raw output
            cost = 0.0
            usage = {}
            if response.raw_output:
                try:
                    raw_data = json.loads(response.raw_output)
                    if isinstance(raw_data, list):
                        last_message = raw_data[-1] if raw_data else {}
                    else:
                        last_message = raw_data
                    cost = last_message.get('cost_usd', 0.0)
                    usage = last_message.get('usage', {})
                except Exception as parse_error:
                    print(f"Debug - Failed to parse cost for {label}: {parse_error}")

            # Debug info
            print(f"Debug - {label}: final_text={'<None>' if response.final_text is None else f'{len(response.final_text)} chars'}")

            return {
                'label': label,
                'response': response.final_text,
                'cost': cost,
                'usage': usage,
                'session_id': response.session_id
            }
        except Exception as e:
            print(f"Debug - Error in {label}: {e}")
            return {'label': label, 'error': str(e), 'cost': 0.0}

    # Run multiple requests in parallel with cost tracking
    tasks = [
        run_with_cost("What's this repo about?", "Repo Info"),
        run_with_cost("What is the capital of France?", "Geography"),
        run_with_cost("Explain photosynthesis briefly", "Science")
    ]

    results = await asyncio.gather(*tasks)

    total_cost = 0.0
    for result in results:
        if 'error' in result:
            print(f"❌ {result['label']}: {result['error']}")
        else:
            print(f"✅ {result['label']}: ${result['cost']:.6f}")
            # Handle case where response might be None
            response_text = result['response'] or "No response text"
            print(f"   {response_text[:100]}...")
            # Show usage if available
            if result.get('usage'):
                print(f"   Usage: {result['usage']}")
            print()
            total_cost += result['cost']

    print(f"💰 Total cost: ${total_cost:.6f}")


async def main():
    print("=== Parallel Execution with Cost Tracking ===")
    print("Running 3 Claude requests in parallel")
    print("Capturing cost and usage information for each request")
    print("=" * 60)

    await parallel_with_cost()


if __name__ == "__main__":
    asyncio.run(main())