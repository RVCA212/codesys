#!/usr/bin/env python3
"""
Bare-bone parallel streaming with stream IDs.
Shows how to run multiple Claude requests in parallel with raw JSON streaming.
"""

import asyncio
from codesys import AsyncAgent


async def bare_bone_parallel_streaming():
    """Bare-bone parallel streaming with stream IDs."""
    agent = AsyncAgent()

    prompts = [
        "What's this repo about?",
        "What is the capital of France?",
        "Explain photosynthesis briefly"
    ]

    async def stream_with_id(prompt, stream_id):
        """Stream a single prompt with stream ID prefix."""
        print(f"\n🚀 [STREAM-{stream_id}] Starting...")

        try:
            # Get raw streaming process
            process = await agent.run(
                prompt,
                stream=True,
                auto_print=False,
                output_format="stream-json"
            )

            # Stream raw output with stream ID
            async for line in process.stdout:
                line_str = line.decode('utf-8').strip()
                if line_str:
                    print(f"[STREAM-{stream_id}] {line_str}")

            await process.wait()
            print(f"✅ [STREAM-{stream_id}] Completed")

        except Exception as e:
            print(f"❌ [STREAM-{stream_id}] Error: {e}")

    # Run all 3 streams in parallel
    tasks = [stream_with_id(prompt, i+1) for i, prompt in enumerate(prompts)]
    await asyncio.gather(*tasks)


async def main():
    print("=== Bare-bone Parallel Streaming ===")
    print("Running 3 Claude requests in parallel with stream IDs")
    print("Each stream outputs raw JSON with [STREAM-X] prefix")
    print("=" * 60)

    await bare_bone_parallel_streaming()


if __name__ == "__main__":
    asyncio.run(main())