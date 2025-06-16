# codesys SDK

A Python SDK for interacting with the Claude CLI tool.

---
Codesys ships with sync and async classes:

1. `Agent` – **enhanced synchronous** SDK with professional-grade features (MCP support, advanced tool management, retries, time-outs, structured responses, etc.). (`codesys/agent.py`)
2. `AsyncAgent` – the **fully asynchronous** counterpart offering identical functionality via `async/await` for non-blocking workflows. (`codesys/async_agent.py`)

This README unifies the documentation for **both** variants. If you just want to see them in action head straight to the [Quick Start](#quick-start) section.

---

## Table of Contents
- [Installation](#installation)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
  - [Synchronous](#synchronous-quick-start)
  - [Asynchronous](#asynchronous-quick-start)
- [Features](#features)
- [Advanced Features](#enhanced-claude-code-sdk)
- [AsyncAgent](#asyncagent---async-claude-cli-sdk)
- [API Reference](#api-reference)
- [Examples](#examples)
- [License](#license)

## Installation

```bash
pip install codesys
```

model names:
claude-opus-4-20250514
claude-sonnnet-4-20250514
claude-3-5-haiku-20241022

set by running `export ANTHROPIC_MODEL=claude-3-5-haiku-20241022`

## Requirements

- Claude CLI tool must be installed, available in your PATH, and set up with your api key.

## Quick Start

### Synchronous Quick Start

```python
from codesys import Agent
import os

# Initialize with a working directory set to the current working directory
agent = Agent(working_dir=os.getcwd())

# This can be a prompt string or claude code command (treat it as your claude code input)
lines = agent.run("""/init""", stream=True)
```

### Asynchronous Quick Start
```python
import asyncio
from codesys import AsyncAgent

async def main():
    agent = AsyncAgent()
    result = await agent.run("Hello, Claude!")
    print(result)

asyncio.run(main())
```

### Practical Use:

the most effective way I've found of using this sdk is by mimicing my actual workflow with claude code which I've found extremely effective.

the workflow is simple: plan the task by exploring the codebase, then implement the plan
```python
#!/usr/bin/env python3

import os
from codesys import Agent


# Configuration - modify these values as needed
WORKING_DIR = os.getcwd()  # Use the current working directory



USER_MESSAGE = """Your super long, complex task here."""



def generate_plan_and_execute():
    """Generate a plan and then execute it using the same conversation session."""
    agent = Agent(working_dir=WORKING_DIR)



    # Step 1: Generate the plan
    print("Generating plan...")
    prompt = f'''
generate a plan into plan.md file given the following task:
<task>
{USER_MESSAGE}
</task>
Given this task, explore the codebase and create a plan for the implementation into plan.md for our developer to accomplish this task step by step. ultrathink
'''
    agent.run(prompt, stream=True)



    # Step 2: Execute the plan continuing the same conversation
    print("\nExecuting plan from plan.md...")
    prompt = '''
Implement the task laid out in plan.md: ultrathink
'''
    agent.run_convo(prompt, stream=True)



if __name__ == "__main__":
    print(f"Working directory: {WORKING_DIR}")
    print(f"Task: {USER_MESSAGE}")
    generate_plan_and_execute()

```


## Features

- Simple interface to the Claude CLI tool
- Support for all Claude CLI options
- Automatic or manual streaming output
- Customizable tool access
- Conversation management with session continuity
- Support for resuming specific conversations by ID

## API Reference

### Agent Class

```python
Agent(working_dir=None, allowed_tools=None)
```

**Parameters:**
- `working_dir` (str, optional): The working directory for Claude to use. Defaults to current directory.
- `allowed_tools` (list, optional): List of tools to allow Claude to use. Defaults to ["Edit", "Bash", "Write"].

### Methods

#### run

```python
run(prompt, stream=False, output_format=None, additional_args=None, auto_print=True, continue_session=False, session_id=None)
```

Run Claude with the specified prompt.

**Parameters:**
- `prompt` (str): The prompt to send to Claude.
- `stream` (bool): If True, handles streaming output. If False, returns the complete output.
- `output_format` (str, optional): Optional output format (e.g., "stream-json").
- `additional_args` (dict, optional): Additional arguments to pass to the Claude CLI.
- `auto_print` (bool): If True and stream=True, automatically prints output. If False, you need to handle streaming manually.
- `continue_session` (bool): If True, continues the most recent Claude session.
- `session_id` (str, optional): If provided, resumes the specific Claude session with this ID.

**Returns:**
- If `stream=False`: Returns the complete output as a string.
- If `stream=True` and `auto_print=False`: Returns a subprocess.Popen object for manual streaming.
- If `stream=True` and `auto_print=True`: Automatically prints output and returns collected lines as a list.

#### run_with_tools

```python
run_with_tools(prompt, tools, stream=False, auto_print=True, continue_session=False, session_id=None)
```

Run Claude with specific allowed tools.

**Parameters:**
- `prompt` (str): The prompt to send to Claude.
- `tools` (list): List of tools to allow Claude to use.
- `stream` (bool): If True, handles streaming output.
- `auto_print` (bool): If True and stream=True, automatically prints output.
- `continue_session` (bool): If True, continues the most recent Claude session.
- `session_id` (str, optional): If provided, resumes the specific Claude session with this ID.

**Returns:**
- If `stream=False`: Returns the complete output as a string.
- If `stream=True` and `auto_print=False`: Returns a subprocess.Popen object.
- If `stream=True` and `auto_print=True`: Automatically prints output and returns collected lines.

#### run_convo

```python
run_convo(prompt, **kwargs)
```

Continue the most recent Claude conversation. This method maintains the same session state as the previous interaction, allowing for context-aware follow-up prompts.

**Parameters:**
- `prompt` (str): The prompt to send to Claude.
- `**kwargs`: Additional arguments to pass to the run method (stream, output_format, etc.)

**Returns:**
- Same return types as the `run` method, depending on parameters used.

#### resume_convo

```python
resume_convo(session_id, prompt, **kwargs)
```

Resume a specific Claude conversation by ID. This allows you to return to a previous conversation even after starting other sessions.

**Parameters:**
- `session_id` (str): The session ID to resume.
- `prompt` (str): The prompt to send to Claude.
- `**kwargs`: Additional arguments to pass to the run method (stream, output_format, etc.)

**Returns:**
- Same return types as the `run` method, depending on parameters used.

#### get_last_session_id

```python
get_last_session_id()
```

Get the session ID from the last Claude run. Useful for saving session IDs to resume conversations later.

**Returns:**
- The session ID if available, otherwise None.

## Example: Automatic Streaming

```python
from codesys import Agent

agent = Agent()
# This will automatically print the output line by line
lines = agent.run("Generate a short story", stream=True)
```

## Example: Manual Streaming with JSON parsing

```python
from codesys import Agent
import json

agent = Agent()
process = agent.run("Generate a short story", stream=True, output_format="stream-json", auto_print=False)

for line in process.stdout:
    if line.strip():
        try:
            data = json.loads(line)
            print(data.get("content", ""))
        except json.JSONDecodeError:
            print(f"Error parsing JSON: {line}")
```

# Examples

```python
from codesys import Agent

# Initialize with a working directory
agent = Agent(working_dir="/Users/seansullivan/codesys/")

# Run Claude with a prompt and automatically print streaming output
lines = agent.run("create another example of example1_custom_tools.py which shows how to use read only tools. note the source code of the sdk in codesys/agent.py", stream=True)

```

```python
"""
Example 1: Customizing tools during initialization

This example demonstrates how to initialize an Agent with only specific tools.
"""

from codesys import Agent

# Initialize with only specific tools
restricted_agent = Agent(
    working_dir="./",
    allowed_tools=["Edit", "Write", "View"]  # Only allow editing, writing files and viewing
)  # Implementation in agent.py lines 19-39

print(f"Agent initialized with tools: {restricted_agent.allowed_tools}")
```

```python

from codesys import Agent

# Initialize with default tools
agent = Agent(working_dir="./")  # Implementation in agent.py lines 19-39
print(f"Default tools: {agent.allowed_tools}")

# Run with only specific tools for one operation
bash_only_response = agent.run_with_tools(
    prompt="List files in the current directory",
    tools=["Bash"],  # Only allow Bash for this specific run
    stream=False
)  # Implementation in agent.py lines 132-155

print(f"Tools after run_with_tools: {agent.allowed_tools}  # Original tools are restored")
```

```python
"""
Example 3: Manual handling of streaming output

This example demonstrates how to manually handle streaming output from the agent.
"""

from codesys import Agent
import json
import time

# Initialize an agent
agent = Agent(working_dir="./")

# Get a process for streaming manually
process = agent.run(
    prompt="Explain what an LLM Agent is in 3 sentences",
    stream=True,
    auto_print=False  # Don't auto-print, we'll handle the output manually
)  # Implementation in agent.py lines 41-96 (stream=True, auto_print=False path)

print("Streaming output manually, processing each line:")
for i, line in enumerate(process.stdout):
    # Parse the JSON line
    try:
        data = json.loads(line)
        # Do something with each piece of output
        print(f"Line {i+1}: {data.get('content', '')}")
    except json.JSONDecodeError:
        print(f"Raw line: {line}")

    # Simulate processing time
    time.sleep(0.1)
    # Compare with agent.py lines 98-116 (auto-handling of streaming)
```

```python
"""
Example 4: Using output formats and additional arguments

This example demonstrates how to use different output formats and pass additional arguments.
"""

from codesys import Agent

# Initialize an agent
agent = Agent(working_dir="./")

# Run with custom output format and additional arguments
response = agent.run(
    prompt="What can you tell me about this codebase?",
    output_format="json",  # Request JSON output
    additional_args={
        "temperature": 0.7,     # Set temperature
        "max-tokens": 500,      # Limit output tokens
        "silent": True          # Suppress progress output
    }
)  # Implementation in agent.py lines 41-70 (output_format handling), 74-80 (additional_args)

print(f"Response type: {type(response)}")
print("First 100 characters of response:", response[:100] if isinstance(response, str) else "Not a string")
```

```python
"""
Example 5: Using run_convo and resume_convo for multi-turn conversations

This example demonstrates how to continue conversations with Claude and maintain context.
"""

from codesys import Agent
import time

# Initialize an agent
agent = Agent(working_dir="./")

# Start a new conversation
print("Starting a new conversation...")
response1 = agent.run(
    prompt="Analyze the structure of this project. What are the main components?",
    stream=True
)

# Continue the same conversation with follow-up
print("\nContinuing the conversation with a follow-up question...")
response2 = agent.run_convo(
    prompt="What improvements would you suggest for this codebase?",
    stream=True
)  # Implementation in agent.py lines 184-197

# Get the session ID for later use
session_id = agent.get_last_session_id()
print(f"\nSession ID: {session_id}")

# Start a different conversation
print("\nStarting a new, unrelated conversation...")
agent.run(
    prompt="Tell me about Python's type hinting system.",
    stream=True
)

# Later, resume the original conversation by ID
print("\nResuming our original conversation about codebase improvements...")
agent.resume_convo(
    session_id=session_id,
    prompt="Could you elaborate on the first improvement you suggested?",
    stream=True
)  # Implementation in agent.py lines 199-211
```



## License

MIT
#### CodeSYS



# Enhanced Claude Code SDK

This enhanced version of your Claude Code SDK implements all the improvements from the analysis guide while maintaining **full backward compatibility** with your existing code.

## 🚀 Key Enhancements

### ✅ **What's New**
- **MCP Server Support**: Local and remote Model Context Protocol servers
- **Advanced Tool Management**: Tool groups, policies, and fine-grained control
- **Structured Response Parsing**: Rich data classes for JSON responses
- **Enhanced Error Handling**: Specific exception types with better debugging
- **Professional Features**: Rate limiting, retry logic, timeouts
- **System Prompt Support**: Custom and appended system prompts
- **Streaming Enhancements**: Custom handlers for different message types

### ✅ **Backward Compatibility**
All your existing examples work unchanged:
- `example.py` ✓
- `example2.py` ✓
- `plan_and_execute.py` ✓
- `example8_share_state.py` ✓

## 📦 Installation & Usage

### Using Your Current SDK (Recommended)
Your current `agent.py` works perfectly for most use cases:

```python
from codesys import Agent

# This still works exactly as before
agent = Agent(working_dir="./")
response = agent.run("hello", stream=True)
```

### Using the Enhanced Version
For advanced features, use the enhanced agent:

```python
from enhanced_agent import Agent

# Enhanced initialization with new features
agent = Agent(
    working_dir="./",
    allowed_tools=["View", "Edit", "Bash"],
    disallowed_tools=["Write"],  # NEW: Explicit deny list
    max_turns=5,                 # NEW: Conversation limits
    rate_limit_delay=0.2,        # NEW: Rate limiting
    max_retries=3,               # NEW: Retry logic
    timeout=30                   # NEW: Default timeout
)
```

## 🔧 Enhanced Features Guide

### 1. **MCP Server Support**

Add Model Context Protocol servers for extended capabilities:

```python
# Local MCP server
agent.add_local_mcp_server(
    "filesystem",
    command=["python", "-m", "mcp_filesystem"],
    args=["--root", "./"],
    env={"MCP_LOG_LEVEL": "INFO"}
)

# Remote MCP server
agent.add_remote_mcp_server(
    "database",
    url="http://localhost:8080/mcp",
    auth={"token": "your-token"}
)

# Use MCP tools
response = agent.run_with_mcp(
    "List files using MCP filesystem tools",
    mcp_tools=["filesystem__list_files", "filesystem__read_file"]
)
```

### 2. **System Prompt Control**

Override or append to the default system prompt:

```python
# Override system prompt
response = agent.run(
    "Review this code for security issues",
    system_prompt="You are a security expert. Focus on vulnerabilities.",
    verbose=True,
    timeout=60
)

# Append to system prompt
response = agent.run(
    "Analyze this function",
    append_system_prompt="Provide metrics in JSON format.",
    output_format="json"
)
```

### 3. **Structured Response Parsing**

Get rich, parsed response objects instead of raw strings:

```python
# Get structured response
structured = agent.run_with_structured_response(
    "Analyze this codebase and return metrics"
)

print(f"Session ID: {structured.session_id}")
print(f"Number of messages: {len(structured.messages)}")
print(f"Tool calls made: {len(structured.tool_calls)}")
print(f"Final text: {structured.final_text}")

# Access individual messages
for message in structured.messages:
    print(f"Role: {message.role}")
    print(f"Content: {message.content}")
```

### 4. **Advanced Tool Management**

Use tool groups and policies for better control:

```python
# Tool groups (predefined sets)
response = agent.run_with_tool_groups(
    "Check the project structure",
    tool_groups=["file_ops", "system"]  # Edit, View, Write, Bash, LSTool
)

# Available tool groups:
# - file_ops: Edit, View, Write
# - system: Bash, LSTool
# - search: GrepTool, GlobTool
# - batch: BatchTool, MultiEdit
# - notebook: NotebookEdit, NotebookRead
# - web: WebFetchTool
# - agent: AgentTool

# Custom tool policies
tool_manager = ToolManager()
tool_manager.add_tool_policy("Bash", "allow")
tool_manager.add_tool_policy("Write", "deny")

agent = Agent(tool_manager=tool_manager)
response = agent.run_with_tool_policies("Analyze files safely")
```

### 5. **Enhanced Error Handling**

Specific exception types for better error management:

```python
try:
    response = agent.run_with_retry(
        "Complex analysis task",
        timeout=30,
        max_turns_override=10
    )
except ClaudeTimeoutError as e:
    print(f"Request timed out: {e}")
except ClaudeAuthenticationError as e:
    print(f"Authentication failed: {e}")
except ClaudeToolError as e:
    print(f"Tool usage error: {e}")
except ClaudeMCPError as e:
    print(f"MCP server error: {e}")
except ClaudeSDKError as e:
    print(f"General SDK error: {e}")
```

### 6. **Streaming with Custom Handlers**

Handle different types of streaming messages:

```python
def text_handler(text):
    print(f"[TEXT] {text}", end="")

def tool_handler(tool_call):
    print(f"\n[TOOL] {tool_call.get('name', 'unknown')} called")

def error_handler(error):
    print(f"\n[ERROR] {error}")

# Stream with custom handlers
result = agent.run_streaming_with_handlers(
    "Write a Python script with explanations",
    text_handler=text_handler,
    tool_handler=tool_handler,
    error_handler=error_handler
)
```

### 7. **Rate Limiting and Retry Logic**

Built-in resilience for production use:

```python
# Configure rate limiting and retries
agent = Agent(
    rate_limit_delay=0.5,  # Minimum 500ms between requests
    max_retries=5          # Retry up to 5 times on failure
)

# Automatic retry with exponential backoff
response = agent.run_with_retry(
    "Analyze this complex codebase",
    timeout=120  # 2 minute timeout
)
```

## 🔄 Migration Guide

### Phase 1: Keep Using Current SDK
Your existing code works perfectly. No changes needed:

```python
# This continues to work exactly as before
from codesys import Agent
agent = Agent(working_dir="./")
response = agent.run("hello", stream=True)
```

### Phase 2: Add Enhanced Features Gradually
Import the enhanced agent and start using new features:

```python
from enhanced_agent import Agent

# Start with basic enhanced features
agent = Agent(
    working_dir="./",
    max_turns=5,        # Add turn limits
    timeout=30          # Add default timeout
)

# All existing methods still work
response = agent.run_convo("continue our discussion")
```

### Phase 3: Use Advanced Features
Gradually adopt MCP, tool policies, and structured responses:

```python
# Add MCP servers
agent.add_local_mcp_server("db", ["python", "db_server.py"])

# Use structured responses
structured = agent.run_with_structured_response("analyze project")

# Use tool groups
response = agent.run_with_tool_groups("check files", ["file_ops"])
```

## 📊 Comparison: Current vs Enhanced

| Feature | Current SDK | Enhanced SDK |
|---------|-------------|--------------|
| Basic Usage | ✅ | ✅ (same API) |
| Streaming | ✅ | ✅ (enhanced) |
| Tool Control | ✅ Basic | ✅ Advanced |
| Session Management | ✅ | ✅ (same API) |
| Error Handling | ✅ Basic | ✅ Comprehensive |
| MCP Support | ❌ | ✅ Full |
| System Prompts | ❌ | ✅ |
| Timeouts | ❌ | ✅ |
| Rate Limiting | ❌ | ✅ |
| Retry Logic | ❌ | ✅ |
| Structured Responses | ❌ | ✅ |
| Tool Groups | ❌ | ✅ |

## 🎯 Use Cases

### **Current SDK is perfect for:**
- Quick prototyping and testing
- Simple automation scripts
- Basic Claude interactions
- Learning and experimentation

### **Enhanced SDK is ideal for:**
- Production applications
- Complex workflows with multiple tools
- Integration with external systems (MCP)
- Enterprise deployments
- Applications requiring reliability and monitoring

## 🧪 Examples

See the example files:

- **`simple_enhanced_demo.py`** - Shows concepts and backward compatibility
- **`enhanced_agent.py`** - Full enhanced implementation
- **Your existing examples** - Continue to work unchanged

## 🔧 Configuration Options

### Enhanced Agent Parameters

```python
Agent(
    working_dir="./",                    # Working directory
    allowed_tools=["View", "Edit"],      # Allowed tools list
    disallowed_tools=["Write"],          # Explicit deny list
    max_turns=5,                         # Max conversation turns
    mcp_config_path="mcp.json",          # MCP config file
    permission_prompt_tool="auth_tool",  # MCP permission tool
    prompt_for_key=False,                # Interactive API key prompt
    default_api_key=None,                # Default API key
    rate_limit_delay=0.1,                # Rate limiting (seconds)
    max_retries=3,                       # Retry attempts
    tool_manager=custom_manager          # Custom tool manager
)
```

### Enhanced Run Method

```python
agent.run(
    prompt="Your prompt",
    stream=False,                        # Enable streaming
    output_format="json",                # Output format
    system_prompt="Custom prompt",       # Override system prompt
    append_system_prompt="Addition",     # Append to system prompt
    timeout=30,                          # Request timeout
    verbose=True,                        # Verbose logging
    max_turns_override=10,               # Override max turns
    allowed_tools_override=["View"],     # Override allowed tools
    mcp_config_path="custom.json",       # Override MCP config
    permission_prompt_tool="tool"        # Override permission tool
)
```

## 📈 Performance & Reliability

The enhanced SDK includes:

- **Exponential backoff** for retries
- **Rate limiting** to prevent API throttling
- **Timeout protection** to prevent hanging requests
- **Memory-efficient streaming** with custom handlers
- **Automatic cleanup** of temporary MCP config files
- **Comprehensive logging** for debugging

## 🤝 Contributing

The enhanced agent maintains the same design principles as your original SDK:

- **Simple by default** - Basic usage remains simple
- **Powerful when needed** - Advanced features available
- **Backward compatible** - Existing code always works
- **Secure** - API keys filtered from all output
- **Well documented** - Clear examples and docstrings

## 📄 License

Same license as your original SDK.




# AsyncAgent - Async Claude CLI SDK

This is an async version of the Agent class that provides the same comprehensive functionality but with full async/await support for non-blocking operations.

## Key Features

✅ **Full Async/Await Support** - All methods are async and non-blocking
✅ **Parallel Execution** - Run multiple Claude requests concurrently
✅ **Async Streaming** - Stream responses with async iteration
✅ **Same API** - Identical interface to the sync version
✅ **Enhanced Error Handling** - Async-aware exception handling
✅ **Rate Limiting** - Async rate limiting with `asyncio.sleep`
✅ **MCP Support** - Full Model Context Protocol support
✅ **Tool Management** - Advanced tool filtering and policies

## Quick Start

```python
import asyncio
from codesys import AsyncAgent

async def main():
    agent = AsyncAgent()
    result = await agent.run("Hello, Claude!")
    print(result)

asyncio.run(main())
```

## Key Differences from Sync Version

| Feature | Sync Version | Async Version |
|---------|-------------|---------------|
| Method calls | `agent.run(prompt)` | `await agent.run(prompt)` |
| Subprocess | `subprocess.run()` | `asyncio.create_subprocess_exec()` |
| Sleep/delays | `time.sleep()` | `await asyncio.sleep()` |
| Streaming | Iterator | `async for` iteration |
| Parallel execution | Not supported | `asyncio.gather()` |

## Usage Examples

### Basic Async Usage
```python
async def basic_example():
    agent = AsyncAgent()
    result = await agent.run("What is the capital of France?")
    print(result)
```

### Parallel Requests
```python
async def parallel_example():
    agent = AsyncAgent()

    prompts = [
        "What is 2 + 2?",
        "What is the capital of Japan?",
        "Explain photosynthesis briefly"
    ]

    # Run all requests in parallel
    tasks = [agent.run(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(result[:50] + "...")
```

### Async Streaming
```python
async def streaming_example():
    agent = AsyncAgent()

    lines = await agent.run(
        "Write a poem about programming",
        stream=True,
        auto_print=True
    )
    print(f"Collected {len(lines)} lines")
```

### Custom Async Handlers
```python
async def handlers_example():
    agent = AsyncAgent()

    def text_handler(text):
        print(f"[TEXT]: {text}")

    def tool_handler(tool_call):
        print(f"[TOOL]: {tool_call['name']}")

    result = await agent.run_streaming_with_handlers(
        "Calculate 2 + 2",
        text_handler=text_handler,
        tool_handler=tool_handler
    )
```

### Conversation Continuity
```python
async def conversation_example():
    agent = AsyncAgent()

    # First message
    await agent.run("My name is Alice")

    # Continue conversation
    response = await agent.run_convo("What's my name?")
    print(response)
```

### Structured Responses
```python
async def structured_example():
    agent = AsyncAgent()

    response = await agent.run_with_structured_response(
        "Explain quantum computing"
    )

    print(f"Session: {response.session_id}")
    print(f"Messages: {len(response.messages)}")
    print(f"Text: {response.final_text}")
```

### Tool Management
```python
async def tools_example():
    agent = AsyncAgent()

    # Run with specific tools
    result = await agent.run_with_tools(
        "List files in current directory",
        tools=["Bash", "LSTool"]
    )

    # Run with tool groups
    result2 = await agent.run_with_tool_groups(
        "Search for Python files",
        tool_groups=["file_ops", "search"]
    )
```

### MCP (Model Context Protocol)
```python
async def mcp_example():
    agent = AsyncAgent()

    # Add MCP server
    agent.add_local_mcp_server(
        "my_server",
        command=["python", "-m", "my_mcp_server"]
    )

    # Use MCP tools
    result = await agent.run_with_mcp(
        "Use my_server to get data",
        mcp_tools=["my_server__get_data"]
    )
```

### Error Handling & Retries
```python
async def retry_example():
    agent = AsyncAgent(max_retries=3)

    try:
        result = await agent.run_with_retry("Hello Claude!")
        print(result)
    except ClaudeSDKError as e:
        print(f"Failed after retries: {e}")
```

## Available Async Methods

All methods from the sync version are available with async equivalents:

- `await agent.run()` - Main execution method
- `await agent.run_with_retry()` - With automatic retry
- `await agent.run_with_structured_response()` - Returns parsed response
- `await agent.run_streaming_with_handlers()` - Custom streaming handlers
- `await agent.run_with_mcp()` - Use MCP servers
- `await agent.run_with_tools()` - Specific tools
- `await agent.run_with_tool_groups()` - Tool groups
- `await agent.run_convo()` - Continue conversation
- `await agent.resume_convo()` - Resume specific session

## Performance Benefits

### Concurrent Execution
```python
# Process multiple prompts simultaneously
async def process_many():
    agent = AsyncAgent()

    tasks = []
    for i in range(10):
        task = agent.run(f"Question {i}")
        tasks.append(task)

    # All 10 requests run concurrently
    results = await asyncio.gather(*tasks)
    return results
```

### Non-blocking Operations
```python
# Don't block the event loop
async def non_blocking():
    agent = AsyncAgent()

    # This doesn't block other operations
    claude_task = agent.run("Long complex query...")

    # Can do other work while Claude processes
    await asyncio.sleep(1)
    print("Still responsive!")

    # Get result when ready
    result = await claude_task
    return result
```

## Integration with Async Frameworks

### FastAPI
```python
from fastapi import FastAPI
from codesys import AsyncAgent

app = FastAPI()
agent = AsyncAgent()

@app.post("/ask-claude")
async def ask_claude(prompt: str):
    result = await agent.run(prompt)
    return {"response": result}
```

### AsyncIO Applications
```python
async def main_app():
    agent = AsyncAgent()

    # Set up background tasks
    tasks = [
        process_user_queries(agent),
        monitor_system(agent),
        generate_reports(agent)
    ]

    await asyncio.gather(*tasks)

asyncio.run(main_app())
```

## Error Handling

All the same exception types are raised as the sync version:

- `ClaudeSDKError` - Base exception
- `ClaudeAuthenticationError` - API key issues
- `ClaudeToolError` - Tool-related errors
- `ClaudeSessionError` - Session management errors
- `ClaudeTimeoutError` - Operation timeouts
- `ClaudeMCPError` - MCP-related errors

## Installation & Dependencies

The async version requires the same dependencies as the sync version, plus:

```bash
# Already included in Python 3.7+
import asyncio
```

## Backward Compatibility

The async version maintains the same API structure as the sync version, just with `async`/`await` added. This makes it easy to migrate existing code:

```python
# Sync version
agent = Agent()
result = agent.run(prompt)

# Async version
agent = AsyncAgent()
result = await agent.run(prompt)
```

## When to Use Async vs Sync

**Use Async When:**
- Running multiple Claude requests concurrently
- Integrating with async web frameworks (FastAPI, aiohttp)
- Building reactive/real-time applications
- Need non-blocking I/O operations
- Working with other async libraries

**Use Sync When:**
- Simple single-request scripts
- Synchronous applications
- Learning/experimenting
- Legacy codebases

## Complete Example

```python
#!/usr/bin/env python3
"""
Example usage of the AsyncAgent class.
Demonstrates various async features and use cases.
"""

import asyncio
import json
from codesys.async_enhanced_agent import AsyncAgent


async def basic_usage_example():
    """Basic usage example with async/await."""
    print("=== Basic Async Usage ===")
    agent = AsyncAgent()

    try:
        result = await agent.run("What is the capital of France?")
        print(f"Claude says: {result}")
    except Exception as e:
        print(f"Error: {e}")


async def streaming_example():
    """Example using streaming with async."""
    print("\n=== Async Streaming Example ===")
    agent = AsyncAgent()

    try:
        # Stream with auto-print
        lines = await agent.run(
            "Write a short poem about programming",
            stream=True,
            auto_print=True
        )
        print(f"\nCollected {len(lines)} lines")
    except Exception as e:
        print(f"Error: {e}")


async def structured_response_example():
    """Example using structured response parsing."""
    print("\n=== Async Structured Response Example ===")
    agent = AsyncAgent()

    try:
        response = await agent.run_with_structured_response(
            "Explain quantum computing in simple terms"
        )

        print(f"Session ID: {response.session_id}")
        print(f"Number of messages: {len(response.messages)}")
        print(f"Final text length: {len(response.final_text) if response.final_text else 0}")
        print(f"Tool calls: {len(response.tool_calls)}")
    except Exception as e:
        print(f"Error: {e}")


async def conversation_example():
    """Example showing conversation continuity."""
    print("\n=== Async Conversation Example ===")
    agent = AsyncAgent()

    try:
        # First message
        result1 = await agent.run("My name is Alice. Remember this.")
        print(f"First response: {result1[:100]}...")

        # Continue conversation
        result2 = await agent.run_convo("What's my name?")
        print(f"Second response: {result2[:100]}...")

        print(f"Session ID: {agent.get_last_session_id()}")
    except Exception as e:
        print(f"Error: {e}")


async def retry_example():
    """Example using retry functionality."""
    print("\n=== Async Retry Example ===")
    agent = AsyncAgent(max_retries=2)

    try:
        result = await agent.run_with_retry("Hello Claude!")
        print(f"Retry result: {result[:100]}...")
    except Exception as e:
        print(f"Error after retries: {e}")


async def custom_handlers_example():
    """Example using custom streaming handlers."""
    print("\n=== Async Custom Handlers Example ===")
    agent = AsyncAgent()

    def text_handler(text):
        print(f"[TEXT]: {text[:50]}...")

    def tool_handler(tool_call):
        print(f"[TOOL]: {tool_call.get('name', 'Unknown')} called")

    def error_handler(error):
        print(f"[ERROR]: {error}")

    try:
        result = await agent.run_streaming_with_handlers(
            "Calculate 2 + 2 and explain the result",
            text_handler=text_handler,
            tool_handler=tool_handler,
            error_handler=error_handler
        )
        print(f"\nFinal collected text: {result[:100]}...")
    except Exception as e:
        print(f"Error: {e}")


async def parallel_requests_example():
    """Example showing parallel async requests."""
    print("\n=== Parallel Async Requests Example ===")
    agent = AsyncAgent()

    # Define multiple prompts
    prompts = [
        "What is 2 + 2?",
        "What is the capital of Japan?",
        "Explain photosynthesis briefly",
    ]

    try:
        # Run multiple requests in parallel
        tasks = [agent.run(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Prompt {i+1} failed: {result}")
            else:
                print(f"Prompt {i+1} result: {result[:50]}...")
    except Exception as e:
        print(f"Error: {e}")


async def tool_management_example():
    """Example using tool management features."""
    print("\n=== Async Tool Management Example ===")
    agent = AsyncAgent()

    try:
        # Run with specific tools
        result = await agent.run_with_tools(
            "List files in the current directory",
            tools=["Bash", "LSTool"]
        )
        print(f"Tool result: {result[:100]}...")

        # Run with tool groups
        result2 = await agent.run_with_tool_groups(
            "Search for Python files",
            tool_groups=["file_ops", "search"]
        )
        print(f"Tool group result: {result2[:100]}...")
    except Exception as e:
        print(f"Error: {e}")


async def mcp_example():
    """Example using MCP (Model Context Protocol) features."""
    print("\n=== Async MCP Example ===")
    agent = AsyncAgent()

    # Add a local MCP server (example)
    agent.add_local_mcp_server(
        "example_server",
        command=["python", "-m", "example_mcp_server"],
        args=["--port", "8000"]
    )

    try:
        # This would work if you have an actual MCP server configured
        result = await agent.run_with_mcp(
            "Use the example server to get data",
            mcp_tools=["example_server__get_data"]
        )
        print(f"MCP result: {result[:100]}...")
    except Exception as e:
        print(f"MCP Error (expected if no server): {e}")


async def main():
    """Run all examples."""
    print("AsyncAgent Examples")
    print("=" * 50)

    examples = [
        basic_usage_example,
        streaming_example,
        structured_response_example,
        conversation_example,
        retry_example,
        custom_handlers_example,
        parallel_requests_example,
        tool_management_example,
        mcp_example,
    ]

    for example in examples:
        try:
            await example()
            await asyncio.sleep(0.1)  # Small delay between examples
        except Exception as e:
            print(f"Example failed: {e}")
        print()


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
```
