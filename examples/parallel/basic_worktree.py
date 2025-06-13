#!/usr/bin/env python3
"""
Basic Git Worktree Example

This example demonstrates the fundamental concepts of running Claude in Git worktrees.
Git worktrees provide complete code isolation for parallel Claude sessions.

Usage: python basic_worktree.py
"""

import asyncio
import sys
import os

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


async def main():
    """Basic demonstration of running Claude in a Git worktree."""
    print("🌿 Basic Git Worktree Demo")
    print("=" * 50)

    # Create agent with worktree support enabled
    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository. Please run in a Git repo directory.")
        print("   Run 'git init' to initialize a repository if needed.")
        return

    print("✅ Git repository detected")

    # Example 1: Simple task in worktree with auto-cleanup
    print("\n1️⃣ Running simple task in dedicated worktree...")
    try:
        result = await agent.run_in_worktree(
            prompt="List all Python files in this directory and count them",
            task_name="count-python-files",
            cleanup_after=True  # Automatically clean up when done
        )
        print(f"📄 Result: {result[:200]}..." if len(result) > 200 else f"📄 Result: {result}")
        print("✅ Task completed and worktree cleaned up automatically")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: Keep worktree for inspection
    print("\n2️⃣ Creating persistent worktree for inspection...")
    try:
        # Create a worktree manually for more control
        worktree_path = agent.setup_worktree_for_parallel_run("inspection-task")
        print(f"📁 Worktree created at: {worktree_path}")
        print(f"💡 You can inspect this worktree manually:")
        print(f"   cd {worktree_path}")
        print(f"   ls -la")

        # Run task without cleanup to inspect results
        result = await agent.run_in_worktree(
            prompt="Create a simple README.md file explaining this repository",
            task_name="create-readme",
            cleanup_after=False  # Keep the worktree for inspection
        )
        print("📝 README.md creation completed")

        # Show what worktrees are currently active
        worktrees = agent.list_active_worktrees()
        print(f"\n📋 Active worktrees: {len(worktrees)}")
        for wt in worktrees:
            if "claude-" in wt.path:  # Only show our created worktrees
                print(f"   📁 {wt.path} (branch: {wt.branch})")

        # Optional: Clean up the worktree we created
        print(f"\n🧹 Cleaning up the inspection worktree...")
        cleaned = agent.cleanup_all_worktrees(force=True)
        if cleaned:
            print(f"✅ Cleaned up: {cleaned}")
        else:
            print("📭 No worktrees to clean up")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n💡 Key takeaways:")
    print("   • Each worktree provides complete file isolation")
    print("   • Use cleanup_after=True for temporary tasks")
    print("   • Use cleanup_after=False to inspect results")
    print("   • Always clean up worktrees when you're done")


if __name__ == "__main__":
    asyncio.run(main())