#!/usr/bin/env python3
"""
Production Parallel Streaming with Git Worktrees

Bare-metal parallel streaming implementation where each Claude request runs
in its own isolated Git worktree with raw JSON streaming output.

Usage: python parallel_development_worktree.py
"""

import asyncio
import sys
import os

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


async def stream_worktree_task(agent, task_config, stream_id):
    """Stream a single task in its own Git worktree with stream ID prefix."""
    task_name = task_config["task_name"]
    prompt = task_config["prompt"]
    branch = task_config.get("branch")

    try:
        # Get raw streaming process in dedicated worktree
        process = await agent.run_in_worktree(
            prompt=prompt,
            task_name=task_name,
            branch=branch,
            stream=True,
            auto_print=False,
            output_format="stream-json",
            cleanup_after=True  # Auto-cleanup when done
        )

        # Stream raw output with worktree stream ID
        async for line in process.stdout:
            line_str = line.decode('utf-8').strip()
            if line_str:
                print(f"[WORKTREE-{stream_id}:{task_name}] {line_str}")

        await process.wait()

    except Exception as e:
        # Output error in JSON format for consistency
        print(f"[WORKTREE-{stream_id}:{task_name}] {{\"type\":\"error\",\"message\":\"{str(e)}\"}}")


async def parallel_worktree_streaming():
    """Production-ready parallel streaming with Git worktrees."""
    agent = AsyncAgent(enable_worktrees=True)

    # Fail silently if not in Git repo
    if not agent.worktree_manager.is_git_repo():
        return

    # Set worktree directory for organization
    worktree_base_dir = os.path.join(os.getcwd(), "worktrees")
    os.makedirs(worktree_base_dir, exist_ok=True)
    agent.set_worktree_directory(worktree_base_dir)

    # Define parallel tasks for documentation generation
    tasks_config = [
        {
            "prompt": "Create comprehensive API reference documentation for AsyncAgent. "
                     "Document all classes, methods, parameters, return types, and exceptions. "
                     "Include the WorktreeManager and all worktree-related functionality. "
                     "Format as a detailed API reference with examples for each method.",
            "task_name": "api-reference",
            "branch": "docs/api-reference"
        },
        {
            "prompt": "Write a comprehensive user guide and tutorial for AsyncAgent. "
                     "Cover installation, basic usage, advanced features, MCP integration, "
                     "parallel execution, and Git worktree functionality. "
                     "Include step-by-step examples and common use cases.",
            "task_name": "user-guide",
            "branch": "docs/user-guide"
        }
    ]

    # Run all streams in parallel with worktree isolation
    tasks = [
        stream_worktree_task(agent, config, i+1)
        for i, config in enumerate(tasks_config)
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(parallel_worktree_streaming())