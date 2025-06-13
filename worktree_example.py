#!/usr/bin/env python3
"""
Comprehensive Git Worktree Example for AsyncAgent

This example demonstrates how to use Git worktrees for isolated parallel Claude sessions.
Git worktrees provide complete code isolation between parallel runs, preventing conflicts.

Usage Examples:
1. Basic worktree usage: python worktree_example.py --demo basic
2. Parallel development: python worktree_example.py --demo parallel
3. Long-running tasks: python worktree_example.py --demo longrunning
4. Custom workflows: python worktree_example.py --demo custom
"""

import asyncio
import argparse
import os
import json
from pathlib import Path
from codesys import AsyncAgent


async def basic_worktree_demo():
    """Basic demonstration of running Claude in a Git worktree."""
    print("🌿 Basic Git Worktree Demo")
    print("=" * 50)

    # Create agent with worktree support enabled
    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository. Please run in a Git repo directory.")
        return

    print("✅ Git repository detected")

    # Example 1: Simple task in worktree
    print("\n1️⃣ Running simple task in dedicated worktree...")
    try:
        result = await agent.run_in_worktree(
            prompt="List all Python files in this directory and count them",
            task_name="count-python-files",
            cleanup_after=True
        )
        print(f"📄 Result: {result[:200]}..." if len(result) > 200 else f"📄 Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: Keep worktree for inspection
    print("\n2️⃣ Creating persistent worktree for inspection...")
    try:
        worktree_path = agent.setup_worktree_for_parallel_run("inspection-task")
        print(f"📁 Worktree created at: {worktree_path}")
        print(f"💡 You can now inspect this worktree manually:")
        print(f"   cd {worktree_path}")
        print(f"   ls -la")

        # Run task without cleanup
        result = await agent.run_in_worktree(
            prompt="Create a simple README.md file explaining this repository",
            task_name="create-readme",
            cleanup_after=False  # Keep the worktree
        )
        print("📝 README.md creation completed")

        # List worktrees
        worktrees = agent.list_active_worktrees()
        print(f"\n📋 Active worktrees: {len(worktrees)}")
        for wt in worktrees:
            print(f"   📁 {wt.path} (branch: {wt.branch})")

    except Exception as e:
        print(f"❌ Error: {e}")


async def parallel_development_demo():
    """Demonstrate parallel development tasks using worktrees."""
    print("🚀 Parallel Development Demo")
    print("=" * 50)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    # Define multiple development tasks
    development_tasks = [
        {
            "prompt": "Create a Python utility module for file operations (read, write, copy, move)",
            "task_name": "file-utils",
            "branch": "feature/file-utils"
        },
        {
            "prompt": "Write unit tests for a hypothetical string processing module",
            "task_name": "string-tests",
            "branch": "feature/string-tests"
        },
        {
            "prompt": "Create a configuration parser that handles JSON, YAML, and INI files",
            "task_name": "config-parser",
            "branch": "feature/config-parser"
        }
    ]

    print(f"🔄 Running {len(development_tasks)} parallel development tasks...")
    print("Each task runs in its own isolated Git worktree with a dedicated branch")

    try:
        # Run all tasks in parallel
        results = await agent.run_parallel_in_worktrees(
            development_tasks,
            cleanup_after=False,  # Keep worktrees for inspection
            output_format="json"
        )

        print(f"\n✅ All {len(results)} tasks completed!")

        # Show what was created
        worktrees = agent.list_active_worktrees()
        print(f"\n📋 Created worktrees:")
        for wt in worktrees:
            if "claude-" in wt.path:  # Our created worktrees
                print(f"   📁 {wt.path}")
                print(f"      🌿 Branch: {wt.branch}")
                print(f"      💡 Inspect with: cd {wt.path}")

        print(f"\n💡 To merge changes back:")
        print("   1. Review each worktree's changes")
        print("   2. Commit changes in each worktree")
        print("   3. Switch to main branch: git checkout main")
        print("   4. Merge branches: git merge feature/branch-name")
        print("   5. Clean up: git worktree remove path/to/worktree")

    except Exception as e:
        print(f"❌ Error in parallel development: {e}")


async def long_running_tasks_demo():
    """Demonstrate managing long-running tasks with worktrees."""
    print("⏰ Long-Running Tasks Demo")
    print("=" * 50)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    # Simulate starting long-running tasks
    long_tasks = [
        {
            "prompt": "Analyze this codebase and write comprehensive documentation",
            "task_name": "documentation",
            "kwargs": {"max_turns_override": 5}  # Allow multiple turns
        },
        {
            "prompt": "Refactor any existing code to improve performance and readability",
            "task_name": "refactoring",
            "kwargs": {"max_turns_override": 5}
        }
    ]

    print("🚀 Starting long-running tasks in background worktrees...")
    print("These tasks will run independently without interfering with each other")

    try:
        # Start tasks without waiting (in practice you might want to monitor them)
        task_futures = []
        for task_config in long_tasks:
            future = asyncio.create_task(
                agent.run_in_worktree(
                    prompt=task_config["prompt"],
                    task_name=task_config["task_name"],
                    cleanup_after=False,  # Keep for monitoring
                    **task_config.get("kwargs", {})
                )
            )
            task_futures.append(future)
            print(f"   🔄 Started: {task_config['task_name']}")

        # In a real scenario, you might not wait for all tasks
        # Here we'll wait just for demonstration
        print("\n⏳ Waiting for tasks to complete...")
        results = await asyncio.gather(*task_futures, return_exceptions=True)

        print("\n📊 Task Results:")
        for i, result in enumerate(results):
            task_name = long_tasks[i]["task_name"]
            if isinstance(result, Exception):
                print(f"   ❌ {task_name}: {result}")
            else:
                print(f"   ✅ {task_name}: Completed successfully")

    except Exception as e:
        print(f"❌ Error managing long-running tasks: {e}")


async def custom_workflow_demo():
    """Demonstrate custom worktree workflows."""
    print("🛠️ Custom Worktree Workflow Demo")
    print("=" * 50)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    # Custom workflow: Code review simulation
    print("📋 Simulating code review workflow...")

    try:
        # Step 1: Create review worktree
        review_path = agent.setup_worktree_for_parallel_run(
            "code-review",
            branch="review/main",
            create_new_branch=True
        )
        print(f"📁 Review worktree created: {review_path}")

        # Step 2: Run review in worktree
        original_dir = agent.working_dir
        agent.working_dir = review_path

        review_result = await agent.run(
            "Perform a code review of this repository. "
            "Check for code quality, potential bugs, and improvement suggestions.",
            output_format="json"
        )

        agent.working_dir = original_dir

        # Step 3: Process review results
        try:
            review_data = json.loads(review_result)
            print("✅ Code review completed")
            # In practice, you might save this to a file or send to a review system
        except json.JSONDecodeError:
            print("✅ Code review completed (non-JSON output)")

        # Step 4: Create fix worktree based on review
        fix_path = agent.setup_worktree_for_parallel_run(
            "apply-fixes",
            branch="fixes/review-suggestions",
            create_new_branch=True
        )
        print(f"🔧 Fix worktree created: {fix_path}")

        # Step 5: Apply fixes in parallel
        agent.working_dir = fix_path

        fix_result = await agent.run(
            "Based on the previous code review, implement the suggested improvements and fixes.",
            continue_session=True,  # Continue from review context
            output_format="json"
        )

        agent.working_dir = original_dir

        print("🔧 Fixes applied in separate worktree")
        print("\n💡 Workflow complete! You now have:")
        print(f"   📋 Review branch: review/main at {review_path}")
        print(f"   🔧 Fixes branch: fixes/review-suggestions at {fix_path}")
        print("   💡 You can compare, test, and merge as needed")

    except Exception as e:
        print(f"❌ Error in custom workflow: {e}")


async def cleanup_demo():
    """Demonstrate worktree cleanup operations."""
    print("🧹 Worktree Cleanup Demo")
    print("=" * 50)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    # Show current worktrees
    print("📋 Current worktrees:")
    worktrees = agent.list_active_worktrees()
    for wt in worktrees:
        print(f"   📁 {wt.path} (branch: {wt.branch})")

    if len([wt for wt in worktrees if "claude-" in wt.path]) == 0:
        print("📭 No Claude-created worktrees to clean up")
        return

    print(f"\n🧹 Cleaning up Claude-created worktrees...")
    cleaned = agent.cleanup_all_worktrees(force=True)

    if cleaned:
        print("✅ Cleaned up worktrees:")
        for path in cleaned:
            print(f"   🗑️  {path}")
    else:
        print("📭 No worktrees were cleaned up")

    # Show worktrees after cleanup
    print("\n📋 Worktrees after cleanup:")
    worktrees = agent.list_active_worktrees()
    for wt in worktrees:
        print(f"   📁 {wt.path} (branch: {wt.branch})")


async def main():
    parser = argparse.ArgumentParser(description="Git Worktree Examples for AsyncAgent")
    parser.add_argument(
        "--demo",
        choices=["basic", "parallel", "longrunning", "custom", "cleanup", "all"],
        default="basic",
        help="Which demo to run"
    )

    args = parser.parse_args()

    print("🌿 Git Worktree Examples for AsyncAgent")
    print("=" * 60)
    print()

    if args.demo == "all":
        demos = [
            ("Basic Usage", basic_worktree_demo),
            ("Parallel Development", parallel_development_demo),
            ("Long-Running Tasks", long_running_tasks_demo),
            ("Custom Workflow", custom_workflow_demo),
            ("Cleanup", cleanup_demo)
        ]

        for name, demo_func in demos:
            print(f"\n{'='*20} {name} {'='*20}")
            await demo_func()
            print("\n" + "="*60)

    elif args.demo == "basic":
        await basic_worktree_demo()
    elif args.demo == "parallel":
        await parallel_development_demo()
    elif args.demo == "longrunning":
        await long_running_tasks_demo()
    elif args.demo == "custom":
        await custom_workflow_demo()
    elif args.demo == "cleanup":
        await cleanup_demo()

    print("\n💡 Tips for using Git worktrees with Claude:")
    print("   • Each worktree provides complete file isolation")
    print("   • Changes in one worktree don't affect others")
    print("   • Perfect for parallel development tasks")
    print("   • Use cleanup_after=False to inspect results")
    print("   • Always clean up worktrees when done")
    print("   • Consider using descriptive branch names")


if __name__ == "__main__":
    asyncio.run(main())