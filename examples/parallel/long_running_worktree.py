#!/usr/bin/env python3
"""
Long-Running Tasks with Git Worktrees

This example demonstrates how to manage long-running Claude tasks using Git worktrees.
Each task runs independently in its own isolated environment.

Usage: python long_running_worktree.py
"""

import asyncio
import sys
import os
import time

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


async def monitor_task_progress(task_name: str, task_future: asyncio.Task, check_interval: int = 5):
    """Monitor a long-running task and print progress updates."""
    start_time = time.time()

    while not task_future.done():
        elapsed = time.time() - start_time
        print(f"   ⏰ {task_name}: Running for {elapsed:.1f}s...")
        await asyncio.sleep(check_interval)

    # Task completed
    elapsed = time.time() - start_time
    if task_future.exception():
        print(f"   ❌ {task_name}: Failed after {elapsed:.1f}s - {task_future.exception()}")
    else:
        print(f"   ✅ {task_name}: Completed after {elapsed:.1f}s")


async def main():
    """Demonstrate managing long-running tasks with worktrees."""
    print("⏰ Long-Running Tasks with Git Worktrees")
    print("=" * 60)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        print("   Run 'git init' to initialize a repository if needed.")
        return

    print("✅ Git repository detected")

    # Define long-running tasks that might take significant time
    long_tasks = [
        {
            "prompt": "Analyze this entire codebase thoroughly and write comprehensive documentation. "
                     "Include architecture overview, API documentation, and usage examples.",
            "task_name": "documentation",
            "kwargs": {"max_turns_override": 10}  # Allow multiple turns for thorough work
        },
        {
            "prompt": "Perform a comprehensive code review and refactoring. "
                     "Look for performance improvements, code quality issues, and suggest optimizations.",
            "task_name": "refactoring",
            "kwargs": {"max_turns_override": 8}
        },
        {
            "prompt": "Create a complete test suite for this codebase. "
                     "Include unit tests, integration tests, and performance benchmarks.",
            "task_name": "testing",
            "kwargs": {"max_turns_override": 6}
        }
    ]

    print("🚀 Starting long-running tasks in isolated worktrees...")
    print("These tasks will run independently without interfering with each other")
    print("\nTasks to start:")
    for i, task in enumerate(long_tasks, 1):
        max_turns = task["kwargs"].get("max_turns_override", 1)
        print(f"   {i}. {task['task_name']} (max {max_turns} turns)")

    try:
        # Start all tasks as background asyncio tasks
        task_futures = []
        monitor_futures = []

        print(f"\n🔄 Launching tasks...")
        for task_config in long_tasks:
            # Create the actual Claude task
            claude_task = asyncio.create_task(
                agent.run_in_worktree(
                    prompt=task_config["prompt"],
                    task_name=task_config["task_name"],
                    cleanup_after=False,  # Keep for monitoring and inspection
                    **task_config.get("kwargs", {})
                )
            )
            task_futures.append(claude_task)

            # Create a monitoring task for this Claude task
            monitor_task = asyncio.create_task(
                monitor_task_progress(task_config["task_name"], claude_task)
            )
            monitor_futures.append(monitor_task)

            print(f"   🚀 Started: {task_config['task_name']}")

        print(f"\n⏳ All tasks started! Monitoring progress...")
        print("   (This is where you could do other work while tasks run in background)")

        # Simulate doing other work while tasks run
        print("\n💼 Simulating other work while tasks run in background...")
        for i in range(3):
            await asyncio.sleep(2)
            completed_count = sum(1 for task in task_futures if task.done())
            print(f"   📊 Status check {i+1}: {completed_count}/{len(task_futures)} tasks completed")

        # Wait for all tasks to complete
        print(f"\n⌛ Waiting for all tasks to complete...")
        results = await asyncio.gather(*task_futures, return_exceptions=True)

        # Stop monitoring tasks
        for monitor_task in monitor_futures:
            if not monitor_task.done():
                monitor_task.cancel()

        # Report final results
        print(f"\n📊 Final Results:")
        successful_tasks = []
        failed_tasks = []

        for i, result in enumerate(results):
            task_name = long_tasks[i]["task_name"]
            if isinstance(result, Exception):
                failed_tasks.append((task_name, result))
                print(f"   ❌ {task_name}: {result}")
            else:
                successful_tasks.append(task_name)
                print(f"   ✅ {task_name}: Completed successfully")

        # Show created worktrees
        worktrees = agent.list_active_worktrees()
        claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

        if claude_worktrees:
            print(f"\n📁 Created worktrees for inspection:")
            for wt in claude_worktrees:
                status = "✅" if any(task_name in wt.path for task_name in successful_tasks) else "❌"
                print(f"   {status} {wt.path} (branch: {wt.branch})")

            print(f"\n💡 Next steps:")
            if successful_tasks:
                print(f"   • Review completed work in worktrees")
                print(f"   • Commit and merge successful changes")
            if failed_tasks:
                print(f"   • Debug failed tasks in their worktrees")
                print(f"   • Fix issues and re-run if needed")
            print(f"   • Clean up worktrees when done")

    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted! Canceling running tasks...")
        for task in task_futures:
            if not task.done():
                task.cancel()
        for monitor_task in monitor_futures:
            if not monitor_task.done():
                monitor_task.cancel()

        # Give tasks a moment to clean up
        await asyncio.sleep(1)
        print("   Tasks canceled")

    except Exception as e:
        print(f"❌ Error managing long-running tasks: {e}")

    print(f"\n💡 Benefits of worktree-based long-running tasks:")
    print("   • Tasks run in complete isolation")
    print("   • No conflicts between parallel long-running processes")
    print("   • Easy to monitor and debug individual tasks")
    print("   • Can cancel or restart individual tasks without affecting others")
    print("   • Results are preserved in separate worktrees for review")


if __name__ == "__main__":
    asyncio.run(main())