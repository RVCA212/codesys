#!/usr/bin/env python3
"""
Individual streaming with custom handlers.
Shows how to stream multiple Claude requests individually in parallel with custom text handlers.
"""

import asyncio
from codesys import AsyncAgent


async def parallel_streaming():
    """Stream multiple requests individually in parallel."""
    agent = AsyncAgent()

    prompts = [
        ("Stream 1", "Write a haiku about coding"),
        ("Stream 2", "What is AI?"),
        ("Stream 3", "Explain gravity")
    ]

    async def handle_stream(stream_id, prompt):
        """Handle streaming for a single prompt."""
        print(f"\n🚀 {stream_id} starting...")

        def text_handler(text):
            # Prefix each chunk with the stream ID
            print(f"[{stream_id}] {text}", end="", flush=True)

        def error_handler(error):
            print(f"[{stream_id}] ERROR: {error}")

        try:
            await agent.run_streaming_with_handlers(
                prompt,
                text_handler=text_handler,
                error_handler=error_handler
            )
            print(f"\n✅ {stream_id} completed!")
        except Exception as e:
            print(f"\n❌ {stream_id} failed: {e}")

    # Start all streams in parallel
    tasks = [handle_stream(sid, prompt) for sid, prompt in prompts]
    await asyncio.gather(*tasks)


async def advanced_handler_streaming():
    """More advanced streaming with progress tracking."""
    agent = AsyncAgent()

    prompts = [
        ("Poetry", "Write a poem about the ocean"),
        ("Science", "Explain quantum mechanics simply"),
        ("Story", "Write a short story about a cat")
    ]

    # Track progress for each stream
    progress = {stream_id: {"chars": 0, "words": 0} for stream_id, _ in prompts}

    async def advanced_stream_handler(stream_id, prompt):
        """Advanced streaming with real-time progress tracking."""
        print(f"\n🚀 [{stream_id}] Starting...")

        def text_handler(text):
            # Update progress
            progress[stream_id]["chars"] += len(text)
            progress[stream_id]["words"] += len(text.split())

            # Stream with progress info
            chars = progress[stream_id]["chars"]
            words = progress[stream_id]["words"]
            print(f"[{stream_id}|{chars}c|{words}w] {text}", end="", flush=True)

        def tool_handler(tool_call):
            print(f"\n[{stream_id}] 🔧 Tool: {tool_call.get('name', 'Unknown')}")

        def error_handler(error):
            print(f"\n[{stream_id}] ❌ Error: {error}")

        try:
            await agent.run_streaming_with_handlers(
                prompt,
                text_handler=text_handler,
                tool_handler=tool_handler,
                error_handler=error_handler
            )

            final_stats = progress[stream_id]
            print(f"\n✅ [{stream_id}] Complete! {final_stats['chars']} chars, {final_stats['words']} words")

        except Exception as e:
            print(f"\n❌ [{stream_id}] Failed: {e}")

    # Run all streams with advanced handlers
    tasks = [advanced_stream_handler(sid, prompt) for sid, prompt in prompts]
    await asyncio.gather(*tasks)

    # Show final summary
    print("\n" + "="*60)
    print("📊 Final Statistics:")
    for stream_id, stats in progress.items():
        print(f"  {stream_id}: {stats['chars']} characters, {stats['words']} words")


async def main():
    print("=== Individual Streaming with Custom Handlers ===")
    print("Running multiple Claude requests with custom text handlers")
    print("Each stream processes text individually in parallel")
    print("=" * 60)

    await parallel_streaming()

    print("\n" + "="*60)
    print("=== Advanced Handler Streaming ===")
    print("Same concept but with progress tracking and statistics")
    print("=" * 60)

    await advanced_handler_streaming()


if __name__ == "__main__":
    asyncio.run(main())