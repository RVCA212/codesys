#!/usr/bin/env python3
"""
Custom Workflow with Git Worktrees

This example demonstrates a custom code review and fix workflow using Git worktrees.
It shows how to chain related tasks across multiple isolated environments.

Usage: python custom_workflow_worktree.py
"""

import asyncio
import sys
import os
import json

# Add the parent directory to Python path to import codesys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from codesys import AsyncAgent


async def main():
    """Demonstrate a custom code review and fix workflow using worktrees."""
    print("🛠️ Custom Code Review Workflow with Git Worktrees")
    print("=" * 70)

    agent = AsyncAgent(enable_worktrees=True)

    if not agent.worktree_manager.is_git_repo():
        print("❌ This demo requires a Git repository.")
        print("   Run 'git init' to initialize a repository if needed.")
        return

    print("✅ Git repository detected")
    print("\n📋 Workflow Overview:")
    print("   1. 🔍 Code Review - Analyze code quality and identify issues")
    print("   2. 🔧 Apply Fixes - Implement suggested improvements")
    print("   3. ✅ Quality Check - Verify fixes and final review")
    print("   4. 📚 Documentation - Update docs based on changes")

    try:
        # Step 1: Code Review in dedicated worktree
        print(f"\n🔍 Step 1: Performing Code Review...")
        review_path = agent.setup_worktree_for_parallel_run(
            "code-review",
            branch="review/analysis",
            create_new_branch=True
        )
        print(f"📁 Review worktree created: {review_path}")

        # Switch to review worktree for analysis
        original_dir = agent.working_dir
        agent.working_dir = review_path

        print("   🔍 Analyzing codebase...")
        review_result = await agent.run(
            "Perform a comprehensive code review of this repository. "
            "Identify code quality issues, potential bugs, performance problems, "
            "and suggest specific improvements. Format your response as a detailed report.",
            output_format="json"
        )

        agent.working_dir = original_dir

        # Parse review results
        review_issues = []
        try:
            review_data = json.loads(review_result)
            print("✅ Code review completed and parsed")
            # In a real workflow, you'd extract specific issues from the review
            review_issues = ["Extracted issues would go here"]
        except json.JSONDecodeError:
            print("✅ Code review completed (text format)")
            review_issues = ["Review completed in text format"]

        # Step 2: Apply Fixes in parallel worktree
        print(f"\n🔧 Step 2: Applying Fixes...")
        fix_path = agent.setup_worktree_for_parallel_run(
            "apply-fixes",
            branch="feature/code-improvements",
            create_new_branch=True
        )
        print(f"📁 Fix worktree created: {fix_path}")

        agent.working_dir = fix_path

        print("   🔧 Implementing improvements...")
        fix_result = await agent.run(
            "Based on a previous code review, implement code improvements and fixes. "
            "Focus on code quality, performance, and maintainability. "
            "Make specific, targeted improvements to the codebase.",
            continue_session=True,  # Continue from review context
            output_format="json"
        )

        agent.working_dir = original_dir

        # Step 3: Quality Check in another worktree
        print(f"\n✅ Step 3: Quality Check...")
        qa_path = agent.setup_worktree_for_parallel_run(
            "quality-check",
            branch="qa/verification",
            create_new_branch=True
        )
        print(f"📁 QA worktree created: {qa_path}")

        agent.working_dir = qa_path

        print("   ✅ Verifying improvements...")
        qa_result = await agent.run(
            "Verify the code improvements made in the previous steps. "
            "Check if the fixes are appropriate and don't introduce new issues. "
            "Provide a final quality assessment.",
            continue_session=True,
            output_format="json"
        )

        agent.working_dir = original_dir

        # Step 4: Documentation update
        print(f"\n📚 Step 4: Updating Documentation...")
        docs_path = agent.setup_worktree_for_parallel_run(
            "update-docs",
            branch="docs/improvements",
            create_new_branch=True
        )
        print(f"📁 Documentation worktree created: {docs_path}")

        agent.working_dir = docs_path

        print("   📚 Updating documentation...")
        docs_result = await agent.run(
            "Update the repository documentation to reflect the code improvements made. "
            "Update README, add comments, and create any necessary documentation files.",
            continue_session=True,
            output_format="json"
        )

        agent.working_dir = original_dir

        # Summary of workflow
        print(f"\n🎉 Workflow Complete!")
        print("=" * 50)

        # Show all created worktrees
        worktrees = agent.list_active_worktrees()
        workflow_worktrees = [wt for wt in worktrees if "claude-" in wt.path]

        if workflow_worktrees:
            print(f"\n📁 Created Worktrees:")
            workflow_steps = {
                "code-review": "🔍 Code Review",
                "apply-fixes": "🔧 Apply Fixes",
                "quality-check": "✅ Quality Check",
                "update-docs": "📚 Documentation"
            }

            for wt in workflow_worktrees:
                step_name = None
                for key, description in workflow_steps.items():
                    if key in wt.path:
                        step_name = description
                        break
                step_name = step_name or "❓ Unknown Step"

                print(f"   {step_name}")
                print(f"      📁 Path: {wt.path}")
                print(f"      🌿 Branch: {wt.branch}")
                print(f"      💡 Inspect: cd {wt.path}")

            print(f"\n💡 Workflow Integration Steps:")
            print("   1. Review each worktree's changes:")
            for wt in workflow_worktrees:
                print(f"      cd {wt.path} && git status")

            print("   2. Test changes in each environment")
            print("   3. Commit changes in each worktree:")
            print("      git add . && git commit -m 'Descriptive commit message'")

            print("   4. Integrate changes to main branch:")
            print("      git checkout main")
            for wt in workflow_worktrees:
                if wt.branch != "main":
                    print(f"      git merge {wt.branch}")

            print("   5. Clean up worktrees when satisfied:")
            print("      python examples/parallel/cleanup_worktree.py")

            # Option to clean up immediately
            print(f"\n🧹 Clean up all workflow worktrees now? (y/N): ", end='')
            try:
                if sys.stdin.isatty():
                    response = input().lower().strip()
                    if response in ['y', 'yes']:
                        cleaned = agent.cleanup_all_worktrees(force=True)
                        if cleaned:
                            print("✅ Cleaned up workflow worktrees:")
                            for path in cleaned:
                                print(f"   🗑️  {path}")
                        else:
                            print("📭 No worktrees to clean up")
                    else:
                        print("📝 Worktrees preserved for inspection")
                else:
                    print("📝 Non-interactive mode - worktrees preserved")
            except (EOFError, KeyboardInterrupt):
                print("📝 Worktrees preserved for inspection")

    except Exception as e:
        print(f"❌ Error in custom workflow: {e}")
        # Restore original working directory
        agent.working_dir = original_dir
        # Try to clean up any created worktrees
        try:
            cleaned = agent.cleanup_all_worktrees(force=True)
            if cleaned:
                print(f"🧹 Cleaned up after error: {cleaned}")
        except:
            pass

    print(f"\n💡 Benefits of worktree-based workflows:")
    print("   • Each workflow step runs in complete isolation")
    print("   • No interference between parallel workflow steps")
    print("   • Easy to review and test each step independently")
    print("   • Can rollback or retry individual steps")
    print("   • Perfect for complex, multi-step development workflows")
    print("   • Maintains clean Git history with dedicated branches")


if __name__ == "__main__":
    asyncio.run(main())