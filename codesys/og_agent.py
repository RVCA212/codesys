"""
CODESYS Agent - A Python SDK for interacting with the Claude CLI tool.
"""

import os
import json
import subprocess
import asyncio
import getpass
import re
from typing import Optional, Dict, List, Union, Any


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


class Agent:
    """
    A class to interact with the Claude CLI tool.

    This class provides a simple interface to run Claude with various
    prompts and configuration options.
    """

    def __init__(self, working_dir: Optional[str] = None, allowed_tools: Optional[List[str]] = None,
                 prompt_for_key: bool = False, default_api_key: Optional[str] = None):
        """
        Initialize a Claude Agent.

        Args:
            working_dir: The working directory for Claude to use. Defaults to current directory.
            allowed_tools: List of tools to allow Claude to use. Defaults to ["Edit", "Bash", "Write"].
            prompt_for_key: If True, will prompt for API key interactively when needed.
            default_api_key: Default API key to use for all requests.
        """
        self.working_dir = working_dir or os.getcwd()
        self.allowed_tools = allowed_tools or [
            "Bash",
            "Edit",
            "View",
            "GlobTool",
            "GrepTool",
            "LSTool",
            "BatchTool",
            "AgentTool",
            "WebFetchTool",
            "Write",
            "NotebookEdit",
            "NotebookRead",
            "MultiEdit",
        ]
        self.last_session_id = None
        self.prompt_for_key = prompt_for_key
        self.default_api_key = default_api_key

    def _get_api_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Get the API key to use, with fallback logic.

        Args:
            api_key: API key passed directly to method

        Returns:
            The API key to use, or None if none available
        """
        # Priority: method parameter > default_api_key > prompt if enabled
        if api_key:
            return api_key

        if self.default_api_key:
            return self.default_api_key

        if self.prompt_for_key:
            return getpass.getpass("Enter Claude API key: ")

        return None

    def run(self, prompt: str, stream: bool = False, output_format: Optional[str] = None,
            additional_args: Optional[Dict[str, Any]] = None, auto_print: bool = True,
            continue_session: bool = False, session_id: Optional[str] = None,
            api_key: Optional[str] = None) -> Union[str, subprocess.Popen, List[str]]:
        """
        Run Claude with the specified prompt.

        Args:
            prompt: The prompt to send to Claude.
            stream: If True, handles streaming output either automatically or by returning a process.
            output_format: Optional output format (e.g., "stream-json").
            additional_args: Additional arguments to pass to the Claude CLI.
            auto_print: If True and stream=True, automatically prints output and returns collected lines.
                       If False and stream=True, returns the subprocess.Popen object for manual streaming.
            continue_session: If True, continues the most recent Claude session.
            session_id: If provided, resumes the specific Claude session with this ID.
            api_key: API key to use for this request.

        Returns:
            If stream=False: Returns the complete output as a string.
            If stream=True and auto_print=False: Returns a subprocess.Popen object for manual streaming.
            If stream=True and auto_print=True: Automatically prints output and returns collected lines as a list.
        """
        # Prepare the command
        cmd = ["claude", "-p", prompt]

        # ---------------- Secure auth ----------------
        effective_api_key = self._get_api_key(api_key)

        # Construct child env so secret never reaches argv or parent shell
        child_env = os.environ.copy()
        if effective_api_key:
            child_env["ANTHROPIC_API_KEY"] = effective_api_key

        # Add session continuation flags if specified
        if session_id:
            cmd.extend(["--resume", session_id])
        elif continue_session:
            cmd.append("--continue")

        # Add allowed tools
        if self.allowed_tools:
            cmd.append("--allowedTools")
            cmd.extend(self.allowed_tools)

        # Add output format if specified
        if output_format:
            cmd.extend(["--output-format", output_format])
        elif stream:
            # Default to stream-json if streaming and no format specified
            cmd.extend(["--output-format", "stream-json"])

        # Always add --verbose flag when using stream-json output format
        effective_output_format = output_format or ("stream-json" if stream else None)
        if effective_output_format == "stream-json":
            cmd.append("--verbose")

        # Add any additional arguments
        if additional_args:
            for key, value in additional_args.items():
                if value is True:
                    cmd.append(f"--{key}")
                elif value is not False and value is not None:
                    cmd.extend([f"--{key}", str(value)])

        # If streaming is requested
        if stream:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=self.working_dir,
                env=child_env,      # <<<<<< key lives only here
            )

            # If auto_print is False, return the process for manual streaming
            if not auto_print:
                return process

            # If auto_print is True, handle streaming automatically
            lines = []
            try:
                for line in process.stdout:
                    filtered_line = _filter_api_keys(line)
                    print(filtered_line, end="")
                    lines.append(filtered_line.rstrip())

                # Wait for process to complete
                return_code = process.wait()
                if return_code != 0:
                    stderr = process.stderr.read()
                    filtered_stderr = _filter_api_keys(stderr)
                    print(f"Error (code {return_code}): {filtered_stderr}", file=os.sys.stderr)

                return lines
            except KeyboardInterrupt:
                # Handle user interruption gracefully
                process.terminate()
                print("\nStreaming interrupted by user")
                return lines

        # For non-streaming, run the command and return the output
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.working_dir,
                env=child_env,
            )

            # If output is JSON and we're using a format that contains session_id, extract it
            if output_format == "json" or (not output_format and not stream):
                try:
                    # Try to parse the output as JSON
                    output_json = json.loads(result.stdout)
                    # If it's a list of messages, get the session_id from the last one
                    if isinstance(output_json, list) and len(output_json) > 0 and 'session_id' in output_json[-1]:
                        self.last_session_id = output_json[-1]['session_id']
                except (json.JSONDecodeError, KeyError, IndexError):
                    # If parsing fails, just continue without setting session_id
                    pass

            return _filter_api_keys(result.stdout)
        except subprocess.CalledProcessError as e:
            filtered_stderr = _filter_api_keys(e.stderr)
            error_msg = f"Error executing Claude (code {e.returncode}): {filtered_stderr}"
            raise RuntimeError(error_msg)

    def run_with_tools(self, prompt: str, tools: List[str], stream: bool = False,
                      auto_print: bool = True, continue_session: bool = False,
                      session_id: Optional[str] = None, api_key: Optional[str] = None) -> Union[str, subprocess.Popen, List[str]]:
        """
        Run Claude with specific allowed tools.

        Args:
            prompt: The prompt to send to Claude.
            tools: List of tools to allow Claude to use.
            stream: If True, handles streaming output.
            auto_print: If True and stream=True, automatically prints output.
            continue_session: If True, continues the most recent Claude session.
            session_id: If provided, resumes the specific Claude session with this ID.
            api_key: API key to use for this request.

        Returns:
            If stream=False: Returns the complete output as a string.
            If stream=True and auto_print=False: Returns a subprocess.Popen object.
            If stream=True and auto_print=True: Automatically prints output and returns collected lines.
        """
        # Save original tools, set the new ones, run, then restore
        original_tools = self.allowed_tools
        self.allowed_tools = tools

        try:
            return self.run(prompt, stream=stream, auto_print=auto_print,
                           continue_session=continue_session, session_id=session_id,
                           api_key=api_key)
        finally:
            self.allowed_tools = original_tools

    def run_convo(self, prompt: str, **kwargs) -> Union[str, subprocess.Popen, List[str]]:
        """
        Continue the most recent Claude conversation.

        This is a convenience method that sets continue_session=True.

        Args:
            prompt: The prompt to send to Claude.
            **kwargs: Additional arguments to pass to the run method.

        Returns:
            The result from the run method.
        """
        return self.run(prompt, continue_session=True, **kwargs)

    def resume_convo(self, session_id: str, prompt: str, **kwargs) -> Union[str, subprocess.Popen, List[str]]:
        """
        Resume a specific Claude session.

        Args:
            session_id: The session ID to resume.
            prompt: The prompt to send to Claude.
            **kwargs: Additional arguments to pass to the run method.

        Returns:
            The result from the run method.
        """
        return self.run(prompt, session_id=session_id, **kwargs)

    def get_last_session_id(self) -> Optional[str]:
        """
        Get the session ID from the last Claude run.

        Returns:
            The session ID if available, otherwise None.
        """
        return self.last_session_id

class AsyncAgent:
    """
    An asynchronous class to interact with the Claude CLI tool.

    This class provides a simple interface to run Claude with various
    prompts and configuration options using async/await.
    """

    def __init__(self, working_dir: Optional[str] = None, allowed_tools: Optional[List[str]] = None,
                 prompt_for_key: bool = False, default_api_key: Optional[str] = None):
        """
        Initialize a Claude AsyncAgent.

        Args:
            working_dir: The working directory for Claude to use. Defaults to current directory.
            allowed_tools: List of tools to allow Claude to use. Defaults to ["Edit", "Bash", "Write"].
            prompt_for_key: If True, will prompt for API key interactively when needed.
            default_api_key: Default API key to use for all requests.
        """
        self.working_dir = working_dir or os.getcwd()
        self.allowed_tools = allowed_tools or [
            "Bash",
            "Edit",
            "View",
            "GlobTool",
            "GrepTool",
            "LSTool",
            "BatchTool",
            "AgentTool",
            "WebFetchTool",
            "Write",
        ]
        self.last_session_id = None
        self.prompt_for_key = prompt_for_key
        self.default_api_key = default_api_key

    def _get_api_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Get the API key to use, with fallback logic.

        Args:
            api_key: API key passed directly to method

        Returns:
            The API key to use, or None if none available
        """
        # Priority: method parameter > default_api_key > prompt if enabled
        if api_key:
            return api_key

        if self.default_api_key:
            return self.default_api_key

        if self.prompt_for_key:
            return getpass.getpass("Enter Claude API key: ")

        return None

    async def run(self, prompt: str, stream: bool = False, output_format: Optional[str] = None,
            additional_args: Optional[Dict[str, Any]] = None, auto_print: bool = True,
            continue_session: bool = False, session_id: Optional[str] = None,
            api_key: Optional[str] = None) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Run Claude with the specified prompt.

        Args:
            prompt: The prompt to send to Claude.
            stream: If True, handles streaming output either automatically or by returning a process.
            output_format: Optional output format (e.g., "stream-json").
            additional_args: Additional arguments to pass to the Claude CLI.
            auto_print: If True and stream=True, automatically prints output and returns collected lines.
                       If False and stream=True, returns the asyncio.subprocess.Process object for manual streaming.
            continue_session: If True, continues the most recent Claude session.
            session_id: If provided, resumes the specific Claude session with this ID.
            api_key: API key to use for this request.

        Returns:
            If stream=False: Returns the complete output as a string.
            If stream=True and auto_print=False: Returns an asyncio.subprocess.Process object for manual streaming.
            If stream=True and auto_print=True: Automatically prints output and returns collected lines as a list.
        """
        # Prepare the command
        cmd = ["claude", "-p", prompt]

        # ---------------- Secure auth ----------------
        effective_api_key = self._get_api_key(api_key)

        # Construct child env so secret never reaches argv or parent shell
        child_env = os.environ.copy()
        if effective_api_key:
            child_env["ANTHROPIC_API_KEY"] = effective_api_key

        # Add session continuation flags if specified
        if session_id:
            cmd.extend(["--resume", session_id])
        elif continue_session:
            cmd.append("--continue")

        # Add allowed tools
        if self.allowed_tools:
            cmd.append("--allowedTools")
            cmd.extend(self.allowed_tools)

        # Add output format if specified
        if output_format:
            cmd.extend(["--output-format", output_format])
        elif stream:
            # Default to stream-json if streaming and no format specified
            cmd.extend(["--output-format", "stream-json"])

        # Always add --verbose flag when using stream-json output format
        effective_output_format = output_format or ("stream-json" if stream else None)
        if effective_output_format == "stream-json":
            cmd.append("--verbose")

        # Add any additional arguments
        if additional_args:
            for key, value in additional_args.items():
                if value is True:
                    cmd.append(f"--{key}")
                elif value is not False and value is not None:
                    cmd.extend([f"--{key}", str(value)])

        # If streaming is requested
        if stream:
            # Start the process - Note: no text=True parameter since asyncio doesn't support it
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=child_env,      # <<<<<< key lives only here
            )

            # If auto_print is False, return the process for manual streaming
            if not auto_print:
                return process

            # If auto_print is True, handle streaming automatically
            lines = []
            try:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode('utf-8')
                    filtered_line = _filter_api_keys(line_str)
                    print(filtered_line, end="")
                    lines.append(filtered_line.rstrip())

                # Wait for process to complete
                return_code = await process.wait()
                if return_code != 0:
                    stderr = await process.stderr.read()
                    stderr_str = stderr.decode('utf-8')
                    filtered_stderr = _filter_api_keys(stderr_str)
                    print(f"Error (code {return_code}): {filtered_stderr}", file=os.sys.stderr)

                return lines
            except KeyboardInterrupt:
                # Handle user interruption gracefully
                process.terminate()
                print("\nStreaming interrupted by user")
                return lines

        # For non-streaming, run the command and return the output
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=child_env,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                filtered_stderr = _filter_api_keys(stderr.decode('utf-8'))
                error_msg = f"Error executing Claude (code {process.returncode}): {filtered_stderr}"
                raise RuntimeError(error_msg)

            result_stdout = stdout.decode('utf-8')

            # If output is JSON and we're using a format that contains session_id, extract it
            if output_format == "json" or (not output_format and not stream):
                try:
                    # Try to parse the output as JSON
                    output_json = json.loads(result_stdout)
                    # If it's a list of messages, get the session_id from the last one
                    if isinstance(output_json, list) and len(output_json) > 0 and 'session_id' in output_json[-1]:
                        self.last_session_id = output_json[-1]['session_id']
                except (json.JSONDecodeError, KeyError, IndexError):
                    # If parsing fails, just continue without setting session_id
                    pass

            return _filter_api_keys(result_stdout)
        except Exception as e:
            filtered_error = _filter_api_keys(str(e))
            error_msg = f"Error executing Claude: {filtered_error}"
            raise RuntimeError(error_msg)

    async def run_with_tools(self, prompt: str, tools: List[str], stream: bool = False,
                      auto_print: bool = True, continue_session: bool = False,
                      session_id: Optional[str] = None, api_key: Optional[str] = None) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Run Claude with specific allowed tools.

        Args:
            prompt: The prompt to send to Claude.
            tools: List of tools to allow Claude to use.
            stream: If True, handles streaming output.
            auto_print: If True and stream=True, automatically prints output.
            continue_session: If True, continues the most recent Claude session.
            session_id: If provided, resumes the specific Claude session with this ID.
            api_key: API key to use for this request.

        Returns:
            If stream=False: Returns the complete output as a string.
            If stream=True and auto_print=False: Returns an asyncio.subprocess.Process object.
            If stream=True and auto_print=True: Automatically prints output and returns collected lines.
        """
        # Save original tools, set the new ones, run, then restore
        original_tools = self.allowed_tools
        self.allowed_tools = tools

        try:
            return await self.run(prompt, stream=stream, auto_print=auto_print,
                           continue_session=continue_session, session_id=session_id,
                           api_key=api_key)
        finally:
            self.allowed_tools = original_tools

    async def run_convo(self, prompt: str, **kwargs) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Continue the most recent Claude conversation.

        This is a convenience method that sets continue_session=True.

        Args:
            prompt: The prompt to send to Claude.
            **kwargs: Additional arguments to pass to the run method.

        Returns:
            The result from the run method.
        """
        return await self.run(prompt, continue_session=True, **kwargs)

    async def resume_convo(self, session_id: str, prompt: str, **kwargs) -> Union[str, asyncio.subprocess.Process, List[str]]:
        """
        Resume a specific Claude session.

        Args:
            session_id: The session ID to resume.
            prompt: The prompt to send to Claude.
            **kwargs: Additional arguments to pass to the run method.

        Returns:
            The result from the run method.
        """
        return await self.run(prompt, session_id=session_id, **kwargs)

    def get_last_session_id(self) -> Optional[str]:
        """
        Get the session ID from the last Claude run.

        Returns:
            The session ID if available, otherwise None.
        """
        return self.last_session_id