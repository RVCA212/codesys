#!/usr/bin/env python3
"""
Enhanced CODESYS Agent - A comprehensive Python SDK for Claude CLI tool.
This is the full enhanced version with MCP support, tool management, structured responses, and professional features.
"""

import os
import json
import subprocess
import asyncio
import getpass
import re
import time
import tempfile
from typing import Optional, Dict, List, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# Custom Exceptions
# ============================================================================

class ClaudeSDKError(Exception):
    """Base exception for Claude SDK errors."""
    pass


class ClaudeAuthenticationError(ClaudeSDKError):
    """Raised when API key is invalid or missing."""
    pass


class ClaudeToolError(ClaudeSDKError):
    """Raised when there are issues with tool usage."""
    pass


class ClaudeSessionError(ClaudeSDKError):
    """Raised when there are session management issues."""
    pass


class ClaudeTimeoutError(ClaudeSDKError):
    """Raised when Claude operations timeout."""
    pass


class ClaudeMCPError(ClaudeSDKError):
    """Raised when there are MCP-related issues."""
    pass


# ============================================================================
# Data Classes for Structured Responses
# ============================================================================

@dataclass
class ClaudeMessage:
    """Represents a single message in a Claude conversation."""
    role: str
    content: List[Dict[str, Any]]
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ClaudeResponse:
    """Structured response from Claude with parsed message data."""
    messages: List[ClaudeMessage]
    final_text: Optional[str] = None
    session_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: Optional[str] = None


class StreamMessageType(Enum):
    """Types of streaming messages from Claude."""
    INIT = "init"
    MESSAGE = "message"
    RESULT = "result"
    ERROR = "error"


# ============================================================================
# Tool Management
# ============================================================================

class ToolManager:
    """Advanced tool management with policies and filtering."""

    def __init__(self):
        self.tool_policies = {}
        self.tool_groups = {
            'file_ops': ['Edit', 'View', 'Write'],
            'system': ['Bash', 'LSTool'],
            'search': ['GrepTool', 'GlobTool'],
            'batch': ['BatchTool', 'MultiEdit'],
            'notebook': ['NotebookEdit', 'NotebookRead'],
            'web': ['WebFetchTool'],
            'agent': ['AgentTool']
        }

    def add_tool_policy(self, tool_name: str, policy: str, conditions: Dict = None):
        """Add a policy for tool usage (allow, deny, prompt)."""
        self.tool_policies[tool_name] = {
            'policy': policy,
            'conditions': conditions or {}
        }

    def should_allow_tool(self, tool_name: str, context: Dict = None) -> bool:
        """Check if a tool should be allowed based on policies."""
        policy = self.tool_policies.get(tool_name, {})
        return policy.get('policy', 'allow') == 'allow'

    def get_tools_by_group(self, group_name: str) -> List[str]:
        """Get tools by predefined group name."""
        return self.tool_groups.get(group_name, [])

    def filter_tools(self, tools: List[str], allowed_groups: List[str] = None) -> List[str]:
        """Filter tools based on allowed groups."""
        if not allowed_groups:
            return tools

        allowed_tools = []
        for group in allowed_groups:
            allowed_tools.extend(self.get_tools_by_group(group))

        return [tool for tool in tools if tool in allowed_tools]


# ============================================================================
# MCP Management
# ============================================================================

class MCPManager:
    """Manages Model Context Protocol server configurations."""

    def __init__(self):
        self.servers = {}
        self.temp_config_files = []

    def add_server(self, server_name: str, server_config: Dict[str, Any]):
        """Add an MCP server configuration."""
        self.servers[server_name] = server_config

    def add_local_server(self, server_name: str, command: List[str],
                        args: List[str] = None, env: Dict[str, str] = None):
        """Add a local MCP server configuration."""
        config = {
            "command": command,
            "args": args or [],
        }
        if env:
            config["env"] = env
        self.add_server(server_name, config)

    def add_remote_server(self, server_name: str, url: str,
                         auth: Dict[str, str] = None):
        """Add a remote MCP server configuration."""
        config = {
            "url": url,
        }
        if auth:
            config["auth"] = auth
        self.add_server(server_name, config)

    def create_config_file(self, filepath: str = None) -> str:
        """Create an MCP configuration file from added servers."""
        if not self.servers:
            return None

        if filepath is None:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            filepath = temp_file.name
            temp_file.close()
            self.temp_config_files.append(filepath)

        config = {"mcpServers": self.servers}
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        return filepath

    def format_mcp_tool_names(self, tools: List[str]) -> List[str]:
        """Format tool names for MCP usage."""
        formatted_tools = []
        for tool in tools:
            if not tool.startswith("mcp__"):
                # Assume format: server_name__tool_name
                if "__" in tool:
                    formatted_tools.append(f"mcp__{tool}")
                else:
                    # Single name - assume it's a tool name for the first server
                    if self.servers:
                        first_server = list(self.servers.keys())[0]
                        formatted_tools.append(f"mcp__{first_server}__{tool}")
                    else:
                        formatted_tools.append(tool)
            else:
                formatted_tools.append(tool)
        return formatted_tools

    def cleanup_temp_files(self):
        """Clean up temporary MCP configuration files."""
        for filepath in self.temp_config_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
        self.temp_config_files.clear()

    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_temp_files()


# ============================================================================
# Utility Functions
# ============================================================================

def _filter_api_keys(text: str) -> str:
    """
    Filter API keys from text for security purposes.

    Replaces any API keys (starting with 'sk-ant-api') with redacted versions.

    Args:
        text: The text to filter

    Returns:
        The text with API keys redacted
    """
    if not text:
        return text

    # Pattern to match Claude API keys (sk-ant-api followed by any characters)
    pattern = r'sk-ant-api[a-zA-Z0-9\-_]+'

    def redact_key(match):
        key = match.group(0)
        return f"sk-ant-api***REDACTED***"

    return re.sub(pattern, redact_key, text)


# ============================================================================
# Enhanced Agent Class
# ============================================================================

class Agent:
    """
    Enhanced Claude CLI agent with MCP support, advanced tool management,
    structured responses, and professional-grade features.
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
                 tool_manager: Optional[ToolManager] = None):
        """
        Initialize an enhanced Claude Agent.

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

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _build_command(self, prompt: str, **kwargs) -> List[str]:
        """Build the Claude CLI command with all options."""
        cmd = ["claude"]

        # Session management (must appear before prompt for correct parsing)
        session_id = kwargs.get('session_id')
        continue_session = kwargs.get('continue_session', False)

        if session_id:
            cmd.extend(["--resume", session_id])
        elif continue_session:
            cmd.append("--continue")

        # Print (non-interactive) mode flag and prompt LAST, as recommended by
        # the Claude Code CLI.  The prompt should come after session flags so
        # that the CLI doesn't interpret them as part of the prompt string.
        cmd.extend(["-p", prompt])

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

    def _handle_subprocess_error(self, e: subprocess.CalledProcessError):
        """Convert subprocess errors to appropriate Claude exceptions."""
        stderr_lower = e.stderr.lower() if e.stderr else ""

        if "authentication" in stderr_lower or "api key" in stderr_lower:
            raise ClaudeAuthenticationError("Invalid API key or authentication failed")
        elif "tool" in stderr_lower:
            raise ClaudeToolError(f"Tool error: {e.stderr}")
        elif "session" in stderr_lower:
            raise ClaudeSessionError(f"Session error: {e.stderr}")
        elif "mcp" in stderr_lower:
            raise ClaudeMCPError(f"MCP error: {e.stderr}")
        else:
            raise ClaudeSDKError(f"Claude execution failed (code {e.returncode}): {e.stderr}")

    def parse_json_response(self, json_output: str) -> ClaudeResponse:
        """Parse Claude's JSON output into structured objects."""
        try:
            data = json.loads(json_output)

            # Handle single 'result' object from non-interactive agentic runs
            if isinstance(data, dict) and data.get("type") == "result":
                return ClaudeResponse(
                    messages=[],  # Intermediate messages are not in the final result object
                    final_text=data.get("result"),
                    session_id=data.get("session_id"),
                    tool_calls=[], # Tool calls are also not in the final result object
                    raw_output=json_output
                )

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

    def run(self, prompt: str,
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
            permission_prompt_tool: Optional[str] = None) -> Union[str, subprocess.Popen, List[str]]:
        """
        Run Claude with the specified prompt and enhanced options.

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
            If stream=True and auto_print=False: subprocess.Popen object
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
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=self.working_dir,
                env=child_env,
            )

            if not auto_print:
                return process

            # Auto-print streaming output
            lines = []
            try:
                for line in process.stdout:
                    filtered_line = _filter_api_keys(line)
                    print(filtered_line, end="")
                    lines.append(filtered_line.rstrip())

                return_code = process.wait()
                if return_code != 0:
                    stderr = process.stderr.read()
                    filtered_stderr = _filter_api_keys(stderr)
                    print(f"Error (code {return_code}): {filtered_stderr}", file=os.sys.stderr)

                return lines
            except KeyboardInterrupt:
                process.terminate()
                print("\nStreaming interrupted by user")
                return lines

        # Handle non-streaming execution
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.working_dir,
                env=child_env,
                timeout=timeout
            )

            # Extract session ID if JSON output
            if output_format == "json" or (not output_format and not stream):
                try:
                    output_json = json.loads(result.stdout)
                    if isinstance(output_json, list) and len(output_json) > 0 and 'session_id' in output_json[-1]:
                        self.last_session_id = output_json[-1]['session_id']
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

            return _filter_api_keys(result.stdout)

        except subprocess.TimeoutExpired:
            raise ClaudeTimeoutError(f"Claude operation timed out after {timeout} seconds")
        except subprocess.CalledProcessError as e:
            filtered_stderr = _filter_api_keys(e.stderr)
            self._handle_subprocess_error(subprocess.CalledProcessError(e.returncode, e.cmd, e.stdout, filtered_stderr))

    def run_with_retry(self, prompt: str, **kwargs):
        """Run Claude with automatic retry on certain failures."""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return self.run(prompt, **kwargs)
            except (ClaudeSDKError, ClaudeTimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff

    def run_with_structured_response(self, prompt: str, **kwargs) -> ClaudeResponse:
        """Run Claude and return a structured response object."""
        kwargs['output_format'] = 'json'
        result = self.run(prompt, **kwargs)
        return self.parse_json_response(result)

    def run_streaming_with_handlers(self, prompt: str,
                                   text_handler: Optional[Callable[[str], None]] = None,
                                   tool_handler: Optional[Callable[[Dict], None]] = None,
                                   error_handler: Optional[Callable[[str], None]] = None,
                                   **kwargs):
        """
        Run Claude with streaming and custom handlers for different message types.
        This version correctly handles streaming of a JSON array by parsing objects.
        """
        kwargs.update({
            'stream': True,
            'output_format': 'stream-json',
            'verbose': True,
            'auto_print': False
        })

        process = self.run(prompt, **kwargs)
        collected_text = []

        object_buffer = ""
        brace_level = 0
        in_string = False

        try:
            for char in iter(lambda: process.stdout.read(1), ''):
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

        except KeyboardInterrupt:
            process.terminate()
            if error_handler:
                error_handler("Streaming interrupted by user.")

        process.wait()
        return ''.join(collected_text)

    # ========================================================================
    # MCP Support Methods
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

    def run_with_mcp(self, prompt: str, mcp_tools: List[str], **kwargs):
        """Run Claude with specific MCP tools enabled."""
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

            return self.run(prompt, **kwargs)

        finally:
            # Always cleanup, but don't fail if cleanup fails
            try:
                if mcp_config_file and os.path.exists(mcp_config_file):
                    os.remove(mcp_config_file)
            except Exception:
                pass

    # ========================================================================
    # Convenience Methods (maintain backward compatibility)
    # ========================================================================

    def run_with_tools(self, prompt: str, tools: List[str], **kwargs):
        """Run Claude with specific allowed tools (backward compatibility)."""
        kwargs['allowed_tools_override'] = tools
        return self.run(prompt, **kwargs)

    def run_convo(self, prompt: str, **kwargs):
        """Continue the most recent Claude conversation (backward compatibility)."""
        return self.run(prompt, continue_session=True, **kwargs)

    def resume_convo(self, session_id: str, prompt: str, **kwargs):
        """Resume a specific Claude session (backward compatibility)."""
        return self.run(prompt, session_id=session_id, **kwargs)

    def get_last_session_id(self) -> Optional[str]:
        """Get the session ID from the last Claude run."""
        return self.last_session_id

    # ========================================================================
    # Tool Management Methods
    # ========================================================================

    def run_with_tool_groups(self, prompt: str, tool_groups: List[str], **kwargs):
        """Run Claude with tools from specific groups."""
        allowed_tools = []
        for group in tool_groups:
            allowed_tools.extend(self.tool_manager.get_tools_by_group(group))

        kwargs['allowed_tools_override'] = allowed_tools
        return self.run(prompt, **kwargs)

    def run_with_tool_policies(self, prompt: str, **kwargs):
        """Run with advanced tool policy checking."""
        if self.allowed_tools:
            filtered_tools = [
                tool for tool in self.allowed_tools
                if self.tool_manager.should_allow_tool(tool)
            ]
            kwargs['allowed_tools_override'] = filtered_tools

        return self.run(prompt, **kwargs)



if __name__ == "__main__":
    # Demo usage
    print("Enhanced Claude Code SDK")
    print("This is the complete enhanced version with:")
    print("✓ MCP server support (local and remote)")
    print("✓ Advanced tool management")
    print("✓ Structured response parsing")
    print("✓ Enhanced error handling")
    print("✓ Rate limiting and retry logic")
    print("✓ System prompt support")
    print("✓ Timeout handling")
    print("✓ Tool groups and policies")
    print("✓ Backward compatibility with existing code")