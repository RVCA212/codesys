#!/usr/bin/env python3
"""
Worktree Directory Configuration Demo

This example demonstrates different ways to configure where Git worktrees
are created when using AsyncAgent.

Usage: python worktree_directory_demo.py [--demo default|custom|temp]
"""

import asyncio
import sys
import os
import argparse
import tempfile

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


async def demo_default_location():
    """Demo using default worktree location (current working directory)."""
    print("📁 Demo 1: Default Worktree Location")
    print("=" * 50)

    # Default behavior - worktrees created in current directory
    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    print(f"🏠 Current working directory: {os.getcwd()}")
    print(f"📁 Default worktree directory: {agent.worktree_dir}")

    try:
        result = await agent.run_in_worktree(
            prompt="List the current directory contents",
            task_name="default-location-test",
            cleanup_after=False
        )

        # Show created worktrees
        worktrees = agent.list_active_worktrees()
        claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

        if claude_worktrees:
            print(f"\n📋 Created worktree:")
            for wt in claude_worktrees:
                print(f"   📁 {wt.path}")
                print(f"   💡 Located in: {os.path.dirname(wt.path)}")

        # Cleanup
        cleaned = agent.cleanup_all_worktrees(force=True)
        if cleaned:
            print(f"\n🧹 Cleaned up: {len(cleaned)} worktrees")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_custom_location():
    """Demo using custom worktree location."""
    print("\n📁 Demo 2: Custom Worktree Location")
    print("=" * 50)

    # Create agent with custom worktree directory
    custom_dir = os.path.join(os.getcwd(), "my-custom-worktrees")
    agent = AsyncAgent(
        enable_worktrees=True,
        worktree_dir=custom_dir
    )

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    print(f"🏠 Current working directory: {os.getcwd()}")
    print(f"📁 Custom worktree directory: {agent.worktree_dir}")

    # Create the directory if it doesn't exist
    os.makedirs(custom_dir, exist_ok=True)
    print(f"✅ Created directory: {custom_dir}")

    try:
        result = await agent.run_in_worktree(
            prompt="List the current directory contents and show the path",
            task_name="custom-location-test",
            cleanup_after=False
        )

        # Show created worktrees
        worktrees = agent.list_active_worktrees()
        claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

        if claude_worktrees:
            print(f"\n📋 Created worktree:")
            for wt in claude_worktrees:
                print(f"   📁 {wt.path}")
                print(f"   💡 Located in: {os.path.dirname(wt.path)}")
                print(f"   ✅ Custom directory used: {custom_dir in wt.path}")

        # Cleanup
        cleaned = agent.cleanup_all_worktrees(force=True)
        if cleaned:
            print(f"\n🧹 Cleaned up: {len(cleaned)} worktrees")

        # Remove the custom directory if empty
        try:
            os.rmdir(custom_dir)
            print(f"🗑️  Removed empty directory: {custom_dir}")
        except OSError:
            print(f"📁 Directory not empty, keeping: {custom_dir}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_temp_location():
    """Demo using temporary directory for worktrees."""
    print("\n📁 Demo 3: Temporary Directory Location")
    print("=" * 50)

    # Use a temporary directory for worktrees
    with tempfile.TemporaryDirectory(prefix="claude-worktrees-") as temp_dir:
        agent = AsyncAgent(enable_worktrees=True)

        if not agent.worktree_manager.is_git_repo():
            print("❌ This demo requires a Git repository.")
            return

        # Set worktree directory to temp directory
        agent.set_worktree_directory(temp_dir)

        print(f"🏠 Current working directory: {os.getcwd()}")
        print(f"📁 Temporary worktree directory: {agent.worktree_dir}")

        try:
            result = await agent.run_in_worktree(
                prompt="Show current directory and create a small test file",
                task_name="temp-location-test",
                cleanup_after=False
            )

            # Show created worktrees
            worktrees = agent.list_active_worktrees()
            claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

            if claude_worktrees:
                print(f"\n📋 Created worktree:")
                for wt in claude_worktrees:
                    print(f"   📁 {wt.path}")
                    print(f"   💡 Located in: {os.path.dirname(wt.path)}")
                    print(f"   🔄 Temporary directory: {temp_dir in wt.path}")

            # Cleanup
            cleaned = agent.cleanup_all_worktrees(force=True)
            if cleaned:
                print(f"\n🧹 Cleaned up: {len(cleaned)} worktrees")

            print(f"📝 Temporary directory will be automatically deleted on exit")

        except Exception as e:
            print(f"❌ Error: {e}")


async def demo_dynamic_location():
    """Demo changing worktree directory dynamically."""
    print("\n📁 Demo 4: Dynamic Directory Changes")
    print("=" * 50)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        return

    print(f"🏠 Current working directory: {os.getcwd()}")

    # Test different locations
    locations = [
        ("default", None),
        ("subfolder", os.path.join(os.getcwd(), "test-worktrees")),
        ("sibling", os.path.join(os.path.dirname(os.getcwd()), "claude-test-worktrees"))
    ]

    for name, location in locations:
        print(f"\n🔄 Testing {name} location...")

        if location:
            os.makedirs(location, exist_ok=True)
            agent.set_worktree_directory(location)
            print(f"   📁 Set worktree directory to: {location}")
        else:
            print(f"   📁 Using default worktree directory: {agent.worktree_dir}")

        try:
            result = await agent.run_in_worktree(
                prompt=f"Echo 'Working in {name} location'",
                task_name=f"{name}-test",
                cleanup_after=True  # Auto-cleanup for this demo
            )
            print(f"   ✅ {name.capitalize()} location test completed")

        except Exception as e:
            print(f"   ❌ Error in {name} location: {e}")

    # Cleanup any remaining directories
    for name, location in locations[1:]:  # Skip default
        if location and os.path.exists(location):
            try:
                os.rmdir(location)
                print(f"🗑️  Removed test directory: {location}")
            except OSError:
                print(f"📁 Directory not empty, keeping: {location}")


async def main():
    parser = argparse.ArgumentParser(description="Worktree Directory Configuration Demo")
    parser.add_argument(
        "--demo",
        choices=["default", "custom", "temp", "dynamic", "all"],
        default="all",
        help="Which demo to run"
    )

    args = parser.parse_args()

    print("📁 Worktree Directory Configuration Demo")
    print("=" * 60)
    print("This demo shows different ways to control where Git worktrees are created")

    if args.demo == "all":
        await demo_default_location()
        await demo_custom_location()
        await demo_temp_location()
        await demo_dynamic_location()
    elif args.demo == "default":
        await demo_default_location()
    elif args.demo == "custom":
        await demo_custom_location()
    elif args.demo == "temp":
        await demo_temp_location()
    elif args.demo == "dynamic":
        await demo_dynamic_location()

    print(f"\n💡 Worktree Directory Configuration Options:")
    print("   • Default: Worktrees created in current working directory")
    print("   • Constructor: AsyncAgent(worktree_dir='/path/to/dir')")
    print("   • Method: agent.set_worktree_directory('/path/to/dir')")
    print("   • Temporary: Use tempfile.TemporaryDirectory()")
    print("   • Custom: Create organized subdirectories for different projects")


if __name__ == "__main__":
    asyncio.run(main())