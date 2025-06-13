#!/usr/bin/env python3
"""
Async Enhanced CODESYS Agent - An async version of the comprehensive Python SDK for Claude CLI tool.
This provides the same functionality as Agent but with async/await support.
"""

import os
import json
import asyncio
import getpass
import re
import time
import tempfile
import subprocess
import shutil
from typing import Optional, Dict, List, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import all the existing classes and exceptions from the original module
from .agent import (
    ClaudeSDKError, ClaudeAuthenticationError, ClaudeToolError,
    ClaudeSessionError, ClaudeTimeoutError, ClaudeMCPError,
    ClaudeMessage, ClaudeResponse, StreamMessageType,
    ToolManager, MCPManager, _filter_api_keys
)


# ============================================================================
# Git Worktree Management
# ============================================================================

@dataclass
class WorktreeInfo:
    """Information about a Git worktree."""
    path: str
    branch: str
    is_bare: bool = False
    is_detached: bool = False
    locked: bool = False


class WorktreeManager:
    """Manages Git worktrees for parallel Claude sessions."""

    def __init__(self, base_repo_path: Optional[str] = None, worktree_dir: Optional[str] = None):
        """
        Initialize the worktree manager.

        Args:
            base_repo_path: Path to the base Git repository. If None, uses current directory.
            worktree_dir: Directory where worktrees should be created. If None, uses current directory.
        """
        self.base_repo_path = base_repo_path or os.getcwd()
        self.worktree_dir = worktree_dir or os.getcwd()
        self.created_worktrees: List[str] = []  # Track worktrees we created for cleanup

    def _run_git_command(self, cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        full_cmd = ["git"] + cmd
        result = subprocess.run(
            full_cmd,
            cwd=cwd or self.base_repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise ClaudeSDKError(f"Git command failed: {' '.join(full_cmd)}\nError: {result.stderr}")
        return result

    def is_git_repo(self, path: Optional[str] = None) -> bool:
        """Check if the given path (or base path) is a Git repository."""
        check_path = path or self.base_repo_path
        try:
            self._run_git_command(["rev-parse", "--git-dir"], cwd=check_path)
            return True
        except ClaudeSDKError:
            return False

    def list_worktrees(self) -> List[WorktreeInfo]:
        """List all existing worktrees."""
        if not self.is_git_repo():
            raise ClaudeSDKError(f"Not a Git repository: {self.base_repo_path}")

        result = self._run_git_command(["worktree", "list", "--porcelain"])
        worktrees = []
        current_worktree = {}

        for line in result.stdout.strip().split('\n'):
            if not line:
                if current_worktree:
                    worktrees.append(WorktreeInfo(
                        path=current_worktree.get('worktree', ''),
                        branch=current_worktree.get('branch', ''),
                        is_bare=current_worktree.get('bare', False),
                        is_detached=current_worktree.get('detached', False),
                        locked=current_worktree.get('locked', False)
                    ))
                    current_worktree = {}
                continue

            if line.startswith('worktree '):
                current_worktree['worktree'] = line[9:]
            elif line.startswith('branch '):
                current_worktree['branch'] = line[7:]
            elif line == 'bare':
                current_worktree['bare'] = True
            elif line == 'detached':
                current_worktree['detached'] = True
            elif line.startswith('locked'):
                current_worktree['locked'] = True

        # Handle last worktree if file doesn't end with empty line
        if current_worktree:
            worktrees.append(WorktreeInfo(
                path=current_worktree.get('worktree', ''),
                branch=current_worktree.get('branch', ''),
                is_bare=current_worktree.get('bare', False),
                is_detached=current_worktree.get('detached', False),
                locked=current_worktree.get('locked', False)
            ))

        return worktrees

    def create_worktree(self, path: str, branch: Optional[str] = None,
                       new_branch: bool = False, force: bool = False) -> str:
        """
        Create a new Git worktree.

        Args:
            path: Path where the worktree should be created
            branch: Branch name to checkout (optional)
            new_branch: Whether to create a new branch
            force: Force creation even if path exists

        Returns:
            Absolute path to the created worktree
        """
        if not self.is_git_repo():
            raise ClaudeSDKError(f"Not a Git repository: {self.base_repo_path}")

        cmd = ["worktree", "add"]

        if force:
            cmd.append("--force")

        if new_branch and branch:
            cmd.extend(["-b", branch])

        cmd.append(path)

        if branch and not new_branch:
            cmd.append(branch)

        self._run_git_command(cmd)

        # Convert to absolute path and track it
        abs_path = os.path.abspath(path)
        self.created_worktrees.append(abs_path)

        return abs_path

    def remove_worktree(self, path: str, force: bool = False) -> bool:
        """
        Remove a Git worktree.

        Args:
            path: Path to the worktree to remove
            force: Force removal even if worktree is dirty

        Returns:
            True if removal was successful
        """
        if not self.is_git_repo():
            raise ClaudeSDKError(f"Not a Git repository: {self.base_repo_path}")

        cmd = ["worktree", "remove"]

        if force:
            cmd.append("--force")

        cmd.append(path)

        try:
            self._run_git_command(cmd)
            # Remove from our tracking list
            abs_path = os.path.abspath(path)
            if abs_path in self.created_worktrees:
                self.created_worktrees.remove(abs_path)
            return True
        except ClaudeSDKError:
            return False

    def cleanup_created_worktrees(self, force: bool = False) -> List[str]:
        """
        Clean up all worktrees that were created by this manager.

        Args:
            force: Force cleanup even if worktrees are dirty

        Returns:
            List of paths that were successfully cleaned up
        """
        cleaned_up = []
        for worktree_path in self.created_worktrees.copy():  # Copy to avoid modification during iteration
            try:
                if self.remove_worktree(worktree_path, force=force):
                    cleaned_up.append(worktree_path)
            except Exception:
                # Continue cleanup even if one fails
                pass
        return cleaned_up

    def generate_worktree_path(self, base_name: str, parent_dir: Optional[str] = None) -> str:
        """
        Generate a unique worktree path based on a base name.

        Args:
            base_name: Base name for the worktree directory
            parent_dir: Parent directory (defaults to configured worktree_dir)

        Returns:
            Unique path for the worktree
        """
        if parent_dir is None:
            parent_dir = self.worktree_dir

        base_path = os.path.join(parent_dir, base_name)
        counter = 1

        while os.path.exists(base_path):
            base_path = os.path.join(parent_dir, f"{base_name}-{counter}")
            counter += 1

        return base_path


# ============================================================================
# Async Enhanced Agent Class
# ============================================================================

class AsyncAgent:
    """
    Async Enhanced Claude CLI agent with MCP support, advanced tool management,
    structured responses, and Git worktree support for parallel runs.
    """

    def __init__(self,
                 working_dir: Optional[str] = None,
                 allowed_tools: Optional[List[str]] = None,
                 disallowed_tools: Optional[List[str]] = None,
                 max_turns: Optional[int] = None,
                 mcp_config_path: Optional[str] = None,
                 permission_prompt_tool: Optional[str] = None,
                 prompt_for_key: bool = False,
                 default_api_key: Optional[str] = None,
                 rate_limit_delay: float = 0.1,
                 max_retries: int = 3,
                 tool_manager: Optional[ToolManager] = None,
                 enable_worktrees: bool = False,
                 worktree_manager: Optional[WorktreeManager] = None,
                 worktree_dir: Optional[str] = None):
        """
        Initialize an async enhanced Claude Agent.

        Args:
            working_dir: The working directory for Claude to use
            allowed_tools: List of tools to allow Claude to use
            disallowed_tools: List of tools to explicitly disallow
            max_turns: Maximum number of agentic turns per conversation
            mcp_config_path: Path to MCP configuration file
            permission_prompt_tool: MCP tool for permission prompting
            prompt_for_key: If True, will prompt for API key interactively
            default_api_key: Default API key for all requests
            rate_limit_delay: Minimum delay between requests (seconds)
            max_retries: Maximum number of retry attempts
            tool_manager: Custom tool manager instance
            enable_worktrees: Enable Git worktree support for parallel runs
            worktree_manager: Custom worktree manager instance
            worktree_dir: Directory where worktrees should be created (defaults to working_dir)
        """
        self.working_dir = working_dir or os.getcwd()
        self.allowed_tools = allowed_tools or [
            "Bash", "Edit", "View", "GlobTool", "GrepTool", "LSTool",
            "BatchTool", "AgentTool", "WebFetchTool", "Write",
            "NotebookEdit", "NotebookRead", "MultiEdit"
        ]
        self.disallowed_tools = disallowed_tools or []
        self.max_turns = max_turns
        self.mcp_config_path = mcp_config_path
        self.permission_prompt_tool = permission_prompt_tool
        self.prompt_for_key = prompt_for_key
        self.default_api_key = default_api_key
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.last_request_time = 0
        self.last_session_id = None

        # Enhanced components
        self.tool_manager = tool_manager or ToolManager()
        self.mcp_manager = MCPManager()

        # Git worktree support
        self.enable_worktrees = enable_worktrees
        self.worktree_dir = worktree_dir or self.working_dir
        self.worktree_manager = worktree_manager or WorktreeManager(
            base_repo_path=self.working_dir,
            worktree_dir=self.worktree_dir
        )

        # Load MCP config if provided
        if self.mcp_config_path and os.path.exists(self.mcp_config_path):
            self._load_mcp_config(self.mcp_config_path)

    def _load_mcp_config(self, config_path: str):
        """Load MCP configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Support both 'mcpServers' (correct format) and 'servers' (legacy)
                servers_key = 'mcpServers' if 'mcpServers' in config else 'servers'
                if servers_key in config:
                    for server_name, server_config in config[servers_key].items():
                        self.mcp_manager.add_server(server_name, server_config)
        except Exception as e:
            raise ClaudeMCPError(f"Failed to load MCP config from {config_path}: {e}")

    def _get_api_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """Get the API key to use, with fallback logic."""
        if api_key:
            return api_key
        if self.default_api_key:
            return self.default_api_key
        if self.prompt_for_key:
            return getpass.getpass("Enter Claude API key: ")
        return None

    async def _async_rate_limit(self):
        """Enforce rate limiting between requests using async sleep."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _build_command(self, prompt: str, **kwargs) -> List[str]:
        """Build the Claude CLI command with all options."""
        cmd = ["claude", "-p", prompt]

        # Session management
        session_id = kwargs.get('session_id')
        continue_session = kwargs.get('continue_session', False)

        if session_id:
            cmd.extend(["--resume", session_id])
        elif continue_session:
            cmd.append("--continue")

        # System prompts
        system_prompt = kwargs.get('system_prompt')
        append_system_prompt = kwargs.get('append_system_prompt')

        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        if append_system_prompt:
            cmd.extend(["--append-system-prompt", append_system_prompt])

        # Output format and streaming
        output_format = kwargs.get('output_format')
        stream = kwargs.get('stream', False)
        verbose = kwargs.get('verbose', False)

        if output_format:
            cmd.extend(["--output-format", output_format])
        elif stream:
            cmd.extend(["--output-format", "stream-json"])

        # Verbose flag (automatically added for stream-json or when explicitly requested)
        effective_output_format = output_format or ("stream-json" if stream else None)
        if verbose or effective_output_format == "stream-json":
            cmd.append("--verbose")

        # Turn limits
        max_turns_override = kwargs.get('max_turns_override')
        max_turns = max_turns_override or self.max_turns
        if max_turns:
            cmd.extend(["--max-turns", str(max_turns)])

        # Tool management
        allowed_tools_override = kwargs.get('allowed_tools_override')
        allowed_tools = allowed_tools_override or self.allowed_tools

        if allowed_tools:
            cmd.append("--allowedTools")
            cmd.extend(allowed_tools)

        if self.disallowed_tools:
            cmd.append("--disallowedTools")
            cmd.extend(self.disallowed_tools)

        # MCP configuration
        mcp_config = kwargs.get('mcp_config_path') or self.mcp_config_path
        if mcp_config:
            cmd.extend(["--mcp-config", mcp_config])

        permission_tool = kwargs.get('permission_prompt_tool') or self.permission_prompt_tool
        if permission_tool:
            cmd.extend(["--permission-prompt-tool", permission_tool])

        # Additional arguments
        additional_args = kwargs.get('additional_args', {})
        for key, value in additional_args.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not False and value is not None:
                cmd.extend([f"--{key}", str(value)])

        return cmd

    def _handle_subprocess_error(self, returncode: int, stderr: str):
        """Convert subprocess errors to appropriate Claude exceptions."""
        stderr_lower = stderr.lower() if stderr else ""

        if "authentication" in stderr_lower or "api key" in stderr_lower:
            raise ClaudeAuthenticationError("Invalid API key or authentication failed")
        elif "tool" in stderr_lower:
            raise ClaudeToolError(f"Tool error: {stderr}")
        elif "session" in stderr_lower:
            raise ClaudeSessionError(f"Session error: {stderr}")
        elif "mcp" in stderr_lower:
            raise ClaudeMCPError(f"MCP error: {stderr}")
        else:
            raise ClaudeSDKError(f"Claude execution failed (code {returncode}): {stderr}")

    def parse_json_response(self, json_output: str) -> ClaudeResponse:
        """Parse Claude's JSON output into structured objects."""
        try:
            data = json.loads(json_output)
            messages = []
            final_text = None
            session_id = None
            tool_calls = []

            # Handle both list of messages and single message formats
            if isinstance(data, list):
                message_list = data
            else:
                message_list = [data]

            for msg_data in message_list:
                message = ClaudeMessage(
                    role=msg_data.get("role", ""),
                    content=msg_data.get("content", []),
                    session_id=msg_data.get("session_id"),
                    timestamp=msg_data.get("timestamp")
                )
                messages.append(message)

                # Extract final text from last assistant message
                if message.role == "assistant":
                    for content_block in message.content:
                        if content_block.get("type") == "text":
                            final_text = content_block.get("text")
                        elif content_block.get("type") == "tool_use":
                            tool_calls.append(content_block)

                # Get session ID from any message that has it
                if message.session_id:
                    session_id = message.session_id

            return ClaudeResponse(
                messages=messages,
                final_text=final_text,
                session_id=session_id,
                tool_calls=tool_calls,
                raw_output=json_output
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse Claude response: {e}")

    async def run(self, prompt: str,
                  stream: bool = False,
                  output_format: Optional[str] = None,
                  additional_args: Optional[Dict[str, Any]] = None,
                  auto_print: bool = True,
                  continue_session: bool = False,
                  session_id: Optional[str] = None,
                  api_key: Optional[str] = None,
                  timeout: Optional[int] = None,
                  system_prompt: Optional[str] = None,
                  append_system_prompt: Optional[str] = None,
                  verbose: bool = False,
                  max_turns_override: Optional[int] = None,
                  allowed_tools_override: Optional[List[str]] = None,
                  mcp_config_path: Optional[str] = None,
                  permission_prompt_tool: Optional[str] = None) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Async version of run Claude with the specified prompt and enhanced options.

        Args:
            prompt: The prompt to send to Claude
            stream: If True, handles streaming output
            output_format: Output format ('text', 'json', 'stream-json')
            additional_args: Additional CLI arguments
            auto_print: If True and stream=True, automatically prints output
            continue_session: If True, continues the most recent session
            session_id: If provided, resumes the specific session
            api_key: API key to use for this request
            timeout: Request timeout in seconds
            system_prompt: Override system prompt
            append_system_prompt: Append to system prompt
            verbose: Enable verbose logging
            max_turns_override: Override max turns for this request
            allowed_tools_override: Override allowed tools for this request
            mcp_config_path: Override MCP config path for this request
            permission_prompt_tool: Override permission prompt tool

        Returns:
            If stream=False: Complete output as string
            If stream=True and auto_print=False: asyncio.subprocess.Process object
            If stream=True and auto_print=True: List of output lines
        """
        # Build command with all options
        cmd = self._build_command(
            prompt,
            stream=stream,
            output_format=output_format,
            additional_args=additional_args or {},
            continue_session=continue_session,
            session_id=session_id,
            system_prompt=system_prompt,
            append_system_prompt=append_system_prompt,
            verbose=verbose,
            max_turns_override=max_turns_override,
            allowed_tools_override=allowed_tools_override,
            mcp_config_path=mcp_config_path,
            permission_prompt_tool=permission_prompt_tool
        )

        # Prepare environment with API key
        effective_api_key = self._get_api_key(api_key)
        child_env = os.environ.copy()
        if effective_api_key:
            child_env["ANTHROPIC_API_KEY"] = effective_api_key

        # Handle streaming
        if stream:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=child_env,
            )

            if not auto_print:
                return process

            # Auto-print streaming output
            lines = []
            try:
                async for line in process.stdout:
                    line_str = line.decode('utf-8')
                    filtered_line = _filter_api_keys(line_str)
                    print(filtered_line, end="")
                    lines.append(filtered_line.rstrip())

                await process.wait()
                if process.returncode != 0:
                    stderr = await process.stderr.read()
                    filtered_stderr = _filter_api_keys(stderr.decode('utf-8'))
                    print(f"Error (code {process.returncode}): {filtered_stderr}", file=os.sys.stderr)

                return lines
            except asyncio.CancelledError:
                process.terminate()
                await process.wait()
                print("\nStreaming interrupted")
                return lines

        # Handle non-streaming execution
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=child_env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            if process.returncode != 0:
                filtered_stderr = _filter_api_keys(stderr.decode('utf-8'))
                self._handle_subprocess_error(process.returncode, filtered_stderr)

            stdout_str = stdout.decode('utf-8')

            # Extract session ID if JSON output
            if output_format == "json" or (not output_format and not stream):
                try:
                    output_json = json.loads(stdout_str)
                    if isinstance(output_json, list) and len(output_json) > 0 and 'session_id' in output_json[-1]:
                        self.last_session_id = output_json[-1]['session_id']
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

            return _filter_api_keys(stdout_str)

        except asyncio.TimeoutError:
            raise ClaudeTimeoutError(f"Claude operation timed out after {timeout} seconds")
        except Exception as e:
            if hasattr(e, 'returncode') and hasattr(e, 'stderr'):
                filtered_stderr = _filter_api_keys(e.stderr)
                self._handle_subprocess_error(e.returncode, filtered_stderr)
            raise ClaudeSDKError(f"Claude execution failed: {e}")

    async def run_with_retry(self, prompt: str, **kwargs):
        """Async version of run Claude with automatic retry on certain failures."""
        for attempt in range(self.max_retries):
            try:
                await self._async_rate_limit()
                return await self.run(prompt, **kwargs)
            except (ClaudeSDKError, ClaudeTimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def run_with_structured_response(self, prompt: str, **kwargs) -> ClaudeResponse:
        """Async version of run Claude and return a structured response object."""
        kwargs['output_format'] = 'json'
        result = await self.run(prompt, **kwargs)
        return self.parse_json_response(result)

    async def run_streaming_with_handlers(self, prompt: str,
                                         text_handler: Optional[Callable[[str], None]] = None,
                                         tool_handler: Optional[Callable[[Dict], None]] = None,
                                         error_handler: Optional[Callable[[str], None]] = None,
                                         **kwargs):
        """
        Async version of run Claude with streaming and custom handlers for different message types.
        This version correctly handles streaming of a JSON array by parsing objects.
        """
        kwargs.update({
            'stream': True,
            'output_format': 'stream-json',
            'verbose': True,
            'auto_print': False
        })

        process = await self.run(prompt, **kwargs)
        collected_text = []

        object_buffer = ""
        brace_level = 0
        in_string = False

        try:
            async for line in process.stdout:
                for char in line.decode('utf-8'):
                    if not in_string:
                        if char == '{':
                            if brace_level == 0:
                                object_buffer = ""  # Start of a new object
                            brace_level += 1

                        if brace_level > 0:
                            object_buffer += char

                        if char == '}':
                            brace_level -= 1
                            if brace_level == 0 and object_buffer:
                                # We have a complete JSON object string
                                try:
                                    message = json.loads(object_buffer)
                                    msg_type = message.get("type")

                                    if msg_type == "assistant":  # Handle assistant messages
                                        for content_block in message.get("message", {}).get("content", []):
                                            content_type = content_block.get("type")
                                            if content_type == "text" and text_handler:
                                                text = content_block.get("text", "")
                                                text_handler(text)
                                                collected_text.append(text)
                                            elif content_type == "tool_use" and tool_handler:
                                                tool_handler(content_block)
                                    elif msg_type == "error" and error_handler:
                                        error_handler(message.get("message", "Unknown error"))

                                except json.JSONDecodeError:
                                    if error_handler:
                                        error_handler(f"JSON parse error on object: {object_buffer}")
                                finally:
                                    object_buffer = ""  # Reset for next object
                    elif brace_level > 0:
                        object_buffer += char

                    # Simple string tracking
                    if char == '"':
                        # This is a simplification and doesn't handle escaped quotes perfectly
                        # but is good enough for finding object boundaries.
                        if len(object_buffer) > 1 and object_buffer[-2] != '\\':
                            in_string = not in_string

        except asyncio.CancelledError:
            process.terminate()
            await process.wait()
            if error_handler:
                error_handler("Streaming interrupted.")

        await process.wait()
        return ''.join(collected_text)

    # ========================================================================
    # MCP Support Methods (Async versions)
    # ========================================================================

    def add_mcp_server(self, server_name: str, server_config: Dict[str, Any]):
        """Add an MCP server configuration."""
        self.mcp_manager.add_server(server_name, server_config)

    def add_local_mcp_server(self, server_name: str, command: List[str],
                            args: List[str] = None, env: Dict[str, str] = None):
        """Add a local MCP server configuration."""
        self.mcp_manager.add_local_server(server_name, command, args, env)

    def add_remote_mcp_server(self, server_name: str, url: str,
                             auth: Dict[str, str] = None):
        """Add a remote MCP server configuration."""
        self.mcp_manager.add_remote_server(server_name, url, auth)

    async def run_with_mcp(self, prompt: str, mcp_tools: List[str], **kwargs):
        """Async version of run Claude with specific MCP tools enabled."""
        if not self.mcp_manager.servers:
            raise ClaudeMCPError("No MCP servers configured. Add servers first with add_mcp_server()")

        # Create temporary MCP config file
        mcp_config_file = self.mcp_manager.create_config_file()

        try:
            # Format MCP tool names correctly
            formatted_tools = self.mcp_manager.format_mcp_tool_names(mcp_tools)

            # Combine with existing allowed tools
            combined_tools = (self.allowed_tools or []) + formatted_tools

            # Run with MCP configuration
            kwargs['mcp_config_path'] = mcp_config_file
            kwargs['allowed_tools_override'] = combined_tools

            return await self.run(prompt, **kwargs)

        finally:
            # Always cleanup, but don't fail if cleanup fails
            try:
                if mcp_config_file and os.path.exists(mcp_config_file):
                    os.remove(mcp_config_file)
            except Exception:
                pass

    # ========================================================================
    # Convenience Methods (maintain backward compatibility, async versions)
    # ========================================================================

    async def run_with_tools(self, prompt: str, tools: List[str], **kwargs):
        """Async version of run Claude with specific allowed tools."""
        kwargs['allowed_tools_override'] = tools
        return await self.run(prompt, **kwargs)

    async def run_convo(self, prompt: str, **kwargs):
        """Async version of continue the most recent Claude conversation."""
        return await self.run(prompt, continue_session=True, **kwargs)

    async def resume_convo(self, session_id: str, prompt: str, **kwargs):
        """Async version of resume a specific Claude session."""
        return await self.run(prompt, session_id=session_id, **kwargs)

    def get_last_session_id(self) -> Optional[str]:
        """Get the session ID from the last Claude run."""
        return self.last_session_id

    # ========================================================================
    # Tool Management Methods (Async versions)
    # ========================================================================

    async def run_with_tool_groups(self, prompt: str, tool_groups: List[str], **kwargs):
        """Async version of run Claude with tools from specific groups."""
        allowed_tools = []
        for group in tool_groups:
            allowed_tools.extend(self.tool_manager.get_tools_by_group(group))

        kwargs['allowed_tools_override'] = allowed_tools
        return await self.run(prompt, **kwargs)

    async def run_with_tool_policies(self, prompt: str, **kwargs):
        """Async version of run with advanced tool policy checking."""
        if self.allowed_tools:
            filtered_tools = [
                tool for tool in self.allowed_tools
                if self.tool_manager.should_allow_tool(tool)
            ]
            kwargs['allowed_tools_override'] = filtered_tools

        return await self.run(prompt, **kwargs)

    # ========================================================================
    # Git Worktree Support Methods
    # ========================================================================

    def setup_worktree_for_parallel_run(self, task_name: str, branch: Optional[str] = None,
                                       create_new_branch: bool = True) -> str:
        """
        Set up a Git worktree for a parallel Claude run.

        Args:
            task_name: Name for the task/worktree
            branch: Branch name (if None, uses task_name)
            create_new_branch: Whether to create a new branch

        Returns:
            Path to the created worktree
        """
        if not self.enable_worktrees:
            raise ClaudeSDKError("Worktree support is not enabled. Set enable_worktrees=True")

        if not self.worktree_manager.is_git_repo():
            raise ClaudeSDKError(f"Working directory is not a Git repository: {self.working_dir}")

        # Generate unique branch and path names
        branch_name = branch or f"claude-task-{task_name}"
        worktree_path = self.worktree_manager.generate_worktree_path(f"claude-{task_name}")

        # Create the worktree
        return self.worktree_manager.create_worktree(
            worktree_path,
            branch_name,
            new_branch=create_new_branch
        )

    async def run_in_worktree(self, prompt: str, task_name: str,
                             branch: Optional[str] = None,
                             create_new_branch: bool = True,
                             cleanup_after: bool = True,
                             **kwargs) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Run Claude in a dedicated Git worktree for isolation.

        Args:
            prompt: The prompt to send to Claude
            task_name: Name for the task/worktree
            branch: Branch name (if None, uses task_name)
            create_new_branch: Whether to create a new branch
            cleanup_after: Whether to remove the worktree after completion
            **kwargs: Additional arguments passed to run()

        Returns:
            Same as run() method
        """
        if not self.enable_worktrees:
            return await self.run(prompt, **kwargs)

        worktree_path = None
        original_working_dir = None

        try:
            # Set up worktree
            worktree_path = self.setup_worktree_for_parallel_run(
                task_name, branch, create_new_branch
            )

            # Store original working directory
            original_working_dir = self.working_dir

            # Update working directory to worktree
            self.working_dir = worktree_path

            # Check if this is a streaming call with auto_print=False
            is_streaming = kwargs.get('stream', False) and not kwargs.get('auto_print', True)

            # Run Claude in the worktree
            result = await self.run(prompt, **kwargs)

            # If streaming with auto_print=False, return a wrapped process that handles cleanup
            if is_streaming and cleanup_after:
                # Create a wrapper that handles cleanup after process completion
                original_process = result

                class WorktreeProcess:
                    def __init__(self, process, worktree_path, worktree_manager, original_working_dir, agent):
                        self.process = process
                        self.worktree_path = worktree_path
                        self.worktree_manager = worktree_manager
                        self.original_working_dir = original_working_dir
                        self.agent = agent
                        self._cleaned_up = False

                    def __getattr__(self, name):
                        return getattr(self.process, name)

                    async def wait(self):
                        try:
                            result = await self.process.wait()
                            return result
                        finally:
                            await self._cleanup()

                    async def _cleanup(self):
                        if not self._cleaned_up:
                            self._cleaned_up = True
                            # Restore working directory
                            if self.original_working_dir:
                                self.agent.working_dir = self.original_working_dir
                            # Remove worktree
                            try:
                                self.worktree_manager.remove_worktree(self.worktree_path, force=True)
                            except Exception:
                                pass

                # Don't cleanup in finally block for streaming
                cleanup_after = False
                return WorktreeProcess(result, worktree_path, self.worktree_manager, original_working_dir, self)

            return result

        finally:
            # Restore original working directory
            if original_working_dir:
                self.working_dir = original_working_dir

            # Cleanup worktree if requested (only for non-streaming or auto_print=True)
            if cleanup_after and worktree_path:
                try:
                    self.worktree_manager.remove_worktree(worktree_path, force=True)
                except Exception:
                    # Don't fail the main operation if cleanup fails
                    pass

    async def run_parallel_in_worktrees(self, prompts_and_tasks: List[Dict[str, Any]],
                                       cleanup_after: bool = True,
                                       **common_kwargs) -> List[Any]:
        """
        Run multiple Claude sessions in parallel, each in its own Git worktree.

        Args:
            prompts_and_tasks: List of dicts with 'prompt', 'task_name', and optional 'kwargs'
            cleanup_after: Whether to cleanup worktrees after completion
            **common_kwargs: Common kwargs applied to all runs

        Returns:
            List of results from each parallel run
        """
        if not self.enable_worktrees:
            # Fall back to regular parallel runs without worktrees
            tasks = []
            for item in prompts_and_tasks:
                prompt = item['prompt']
                task_kwargs = {**common_kwargs, **item.get('kwargs', {})}
                tasks.append(self.run(prompt, **task_kwargs))
            return await asyncio.gather(*tasks)

        # Create tasks for parallel execution in worktrees
        async def run_single_task(item):
            prompt = item['prompt']
            task_name = item['task_name']
            task_kwargs = {**common_kwargs, **item.get('kwargs', {})}

            return await self.run_in_worktree(
                prompt=prompt,
                task_name=task_name,
                branch=item.get('branch'),
                create_new_branch=item.get('create_new_branch', True),
                cleanup_after=cleanup_after,
                **task_kwargs
            )

        # Execute all tasks in parallel
        tasks = [run_single_task(item) for item in prompts_and_tasks]
        return await asyncio.gather(*tasks)

    def list_active_worktrees(self) -> List[WorktreeInfo]:
        """List all active Git worktrees."""
        if not self.enable_worktrees:
            raise ClaudeSDKError("Worktree support is not enabled")
        return self.worktree_manager.list_worktrees()

    def cleanup_all_worktrees(self, force: bool = False) -> List[str]:
        """
        Clean up all worktrees created by this agent.

        Args:
            force: Force cleanup even if worktrees are dirty

        Returns:
            List of cleaned up worktree paths
        """
        if not self.enable_worktrees:
            return []
        return self.worktree_manager.cleanup_created_worktrees(force=force)

    def set_worktree_directory(self, worktree_dir: str):
        """
        Set the directory where worktrees should be created.

        Args:
            worktree_dir: Directory path where worktrees should be created
        """
        self.worktree_dir = worktree_dir
        self.worktree_manager.worktree_dir = worktree_dir



if __name__ == "__main__":
    # Demo usage
    async def demo():
        print("Async Enhanced Claude Code SDK")
        print("This is the async version with:")
        print("✓ Async/await support")
        print("✓ MCP server support (local and remote)")
        print("✓ Advanced tool management")
        print("✓ Structured response parsing")
        print("✓ Enhanced error handling")
        print("✓ Rate limiting and retry logic")
        print("✓ System prompt support")
        print("✓ Timeout handling")
        print("✓ Tool groups and policies")
        print("✓ Git worktree support")
        print("✓ Backward compatibility with existing code")

        # Example usage
        agent = AsyncAgent()
        try:
            result = await agent.run("Hello, Claude!")
            print(f"Claude says: {result}")
        except Exception as e:
            print(f"Error: {e}")

    # Run demo if executed directly
    asyncio.run(demo())