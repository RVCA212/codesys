#!/usr/bin/env python3
"""
Git Worktree Cleanup Utility

This utility helps manage and clean up Git worktrees created by Claude sessions.
It provides both interactive and automated cleanup options.

Usage:
  python cleanup_worktree.py                    # Interactive cleanup
  python cleanup_worktree.py --auto             # Automatic cleanup
  python cleanup_worktree.py --list             # List worktrees only
  python cleanup_worktree.py --force            # Force cleanup all
"""

import asyncio
import sys
import os
import argparse

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


def print_worktree_info(worktrees, title="Active Git Worktrees"):
    """Print formatted information about worktrees."""
    print(f"\n📋 {title}")
    print("=" * (len(title) + 4))

    if not worktrees:
        print("📭 No worktrees found")
        return

    main_worktrees = []
    claude_worktrees = []

    for wt in worktrees:
        if "claude-" in wt.path:
            claude_worktrees.append(wt)
        else:
            main_worktrees.append(wt)

    if main_worktrees:
        print("\n🏠 Main/Manual Worktrees:")
        for wt in main_worktrees:
            status = "🔒" if wt.locked else "📁"
            print(f"   {status} {wt.path}")
            print(f"      🌿 Branch: {wt.branch}")
            if wt.locked:
                print(f"      🔒 Status: Locked")

    if claude_worktrees:
        print(f"\n🤖 Claude-Created Worktrees:")
        for wt in claude_worktrees:
            status = "🔒" if wt.locked else "📁"
            print(f"   {status} {wt.path}")
            print(f"      🌿 Branch: {wt.branch}")
            if wt.locked:
                print(f"      🔒 Status: Locked")

    print(f"\n📊 Summary: {len(main_worktrees)} main, {len(claude_worktrees)} Claude-created")


async def interactive_cleanup(agent):
    """Interactive cleanup with user confirmation."""
    print("🧹 Interactive Worktree Cleanup")
    print("=" * 40)

    worktrees = agent.list_active_worktrees()
    claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

    print_worktree_info(worktrees)

    if not claude_worktrees:
        print("\n📭 No Claude-created worktrees to clean up")
        return

    print(f"\n🎯 Found {len(claude_worktrees)} Claude-created worktrees to potentially clean up")

    # Ask for each worktree individually
    to_cleanup = []
    for wt in claude_worktrees:
        print(f"\n📁 {wt.path}")
        print(f"   🌿 Branch: {wt.branch}")
        if wt.locked:
            print(f"   🔒 Status: Locked")
            print(f"   ⚠️  This worktree is locked - force cleanup required")

        try:
            response = input(f"   🗑️  Remove this worktree? (y/N): ").lower().strip()
            if response in ['y', 'yes']:
                to_cleanup.append(wt.path)
                print(f"   ✅ Marked for cleanup")
            else:
                print(f"   📝 Keeping")
        except (EOFError, KeyboardInterrupt):
            print(f"\n⚠️  Cleanup interrupted")
            return

    if not to_cleanup:
        print(f"\n📝 No worktrees selected for cleanup")
        return

    # Confirm batch cleanup
    print(f"\n🧹 Ready to clean up {len(to_cleanup)} worktrees:")
    for path in to_cleanup:
        print(f"   🗑️  {path}")

    try:
        confirm = input(f"\n⚠️  Proceed with cleanup? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print(f"📝 Cleanup canceled")
            return
    except (EOFError, KeyboardInterrupt):
        print(f"\n📝 Cleanup canceled")
        return

    # Perform cleanup
    print(f"\n🧹 Cleaning up worktrees...")
    cleaned = []
    failed = []

    for path in to_cleanup:
        try:
            success = agent.worktree_manager.remove_worktree(path, force=True)
            if success:
                cleaned.append(path)
                print(f"   ✅ Removed: {path}")
            else:
                failed.append(path)
                print(f"   ❌ Failed to remove: {path}")
        except Exception as e:
            failed.append(path)
            print(f"   ❌ Error removing {path}: {e}")

    # Report results
    print(f"\n📊 Cleanup Results:")
    print(f"   ✅ Successfully removed: {len(cleaned)}")
    print(f"   ❌ Failed to remove: {len(failed)}")

    if failed:
        print(f"\n❌ Failed worktrees (may need manual cleanup):")
        for path in failed:
            print(f"   🗑️  {path}")
            print(f"      💡 Try: git worktree remove --force {path}")


async def auto_cleanup(agent, force=False):
    """Automatic cleanup of all Claude-created worktrees."""
    print("🤖 Automatic Worktree Cleanup")
    print("=" * 40)

    worktrees = agent.list_active_worktrees()
    claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

    print_worktree_info(worktrees)

    if not claude_worktrees:
        print("\n📭 No Claude-created worktrees to clean up")
        return

    print(f"\n🧹 Automatically cleaning up {len(claude_worktrees)} Claude worktrees...")

    if force:
        print("   ⚠️  Force mode enabled - will remove locked worktrees")

    cleaned = agent.cleanup_all_worktrees(force=force)

    if cleaned:
        print(f"\n✅ Successfully cleaned up {len(cleaned)} worktrees:")
        for path in cleaned:
            print(f"   🗑️  {path}")
    else:
        print(f"\n📭 No worktrees were cleaned up")
        if not force:
            print("   💡 Try with --force flag if worktrees are locked")


async def list_worktrees(agent):
    """List all worktrees without cleanup."""
    print("📋 Git Worktree Listing")
    print("=" * 30)

    worktrees = agent.list_active_worktrees()
    print_worktree_info(worktrees)

    # Additional analysis
    claude_worktrees = [wt for wt in worktrees if "claude-" in wt.path]
    if claude_worktrees:
        print(f"\n💡 Cleanup options:")
        print(f"   • Interactive: python cleanup_worktree.py")
        print(f"   • Automatic:  python cleanup_worktree.py --auto")
        print(f"   • Force all:  python cleanup_worktree.py --force")


async def main():
    parser = argparse.ArgumentParser(description="Git Worktree Cleanup Utility")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically clean up all Claude-created worktrees"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force cleanup of all Claude worktrees (including locked ones)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all worktrees without cleanup"
    )

    args = parser.parse_args()

    # Create agent with worktree support
    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This utility requires a Git repository.")
        print("   Please run from within a Git repository directory.")
        return

    print("✅ Git repository detected")

    try:
        if args.list:
            await list_worktrees(agent)
        elif args.force:
            await auto_cleanup(agent, force=True)
        elif args.auto:
            await auto_cleanup(agent, force=False)
        else:
            # Check if we're in an interactive terminal
            if sys.stdin.isatty():
                await interactive_cleanup(agent)
            else:
                print("📝 Non-interactive environment detected")
                print("   Use --auto or --force for non-interactive cleanup")
                await list_worktrees(agent)

    except KeyboardInterrupt:
        print(f"\n⚠️  Cleanup interrupted by user")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

    print(f"\n💡 Worktree Management Tips:")
    print("   • Regular cleanup prevents disk space issues")
    print("   • Review worktrees before cleanup to save important work")
    print("   • Use 'git worktree list' to see all worktrees")
    print("   • Lock important worktrees with 'git worktree lock <path>'")


if __name__ == "__main__":
    asyncio.run(main())