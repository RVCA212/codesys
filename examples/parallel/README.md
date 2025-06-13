# Parallel Async Examples

This folder contains multiple approaches to running Claude requests in parallel using the `AsyncAgent`, including basic parallel execution and advanced Git worktree isolation.

## 📁 Files

### 1. `bare_bone_streaming.py`
**Raw parallel streaming with stream IDs**

- **Purpose**: Shows the simplest way to run multiple Claude requests in parallel with raw JSON streaming
- **Features**:
  - Stream IDs (`[STREAM-1]`, `[STREAM-2]`, `[STREAM-3]`)
  - Raw JSON output from Claude
  - Minimal code, maximum clarity
  - True parallel execution

**Usage:**
```bash
cd examples/parallel
python bare_bone_streaming.py
```

**Output Example:**
```
🚀 [STREAM-1] Starting...
🚀 [STREAM-2] Starting...
🚀 [STREAM-3] Starting...
[STREAM-1] {"type":"message_start","message":{"id":"msg_123"...}}
[STREAM-2] {"type":"content_block_delta","delta":{"text":"Paris"}}
[STREAM-1] {"type":"content_block_delta","delta":{"text":"This repo..."}}
✅ [STREAM-1] Completed
✅ [STREAM-2] Completed
✅ [STREAM-3] Completed
```

### 2. `cost_tracking.py`
**Parallel execution with cost tracking**

- **Purpose**: Run multiple requests in parallel while capturing cost and usage information
- **Features**:
  - Cost tracking (`$0.012894` per request)
  - Usage statistics (input/output tokens)
  - Structured response parsing
  - Error handling and debugging

**Usage:**
```bash
cd examples/parallel
python cost_tracking.py
```

**Output Example:**
```
✅ Repo Info: $0.012894
   This is a Python SDK for interacting with the Claude CLI tool...
   Usage: {'input_tokens': 45, 'output_tokens': 123}

✅ Geography: $0.008456
   Paris is the capital and largest city of France...
   Usage: {'input_tokens': 28, 'output_tokens': 67}

💰 Total cost: $0.021350
```

### 3. `handler_streaming.py`
**Individual streaming with custom handlers**

- **Purpose**: Stream multiple requests with custom text processing and progress tracking
- **Features**:
  - Custom text handlers for each stream
  - Real-time progress tracking (character/word count)
  - Tool usage detection
  - Advanced statistics

**Usage:**
```bash
cd examples/parallel
python handler_streaming.py
```

**Output Example:**
```
🚀 Stream 1 starting...
🚀 Stream 2 starting...
[Stream 1] Code flows like
[Stream 2] AI stands for Artificial Intelligence...
[Stream 1|15c|3w] water through pipes,
[Stream 2|45c|8w] It refers to...
✅ Stream 1 completed!
✅ Stream 2 completed!

📊 Final Statistics:
  Poetry: 245 characters, 52 words
  Science: 892 characters, 156 words
```

## 🚀 Key Concepts

### Parallel Execution
All examples use `asyncio.gather()` to run multiple Claude requests simultaneously:

```python
tasks = [handle_stream(prompt, i) for i, prompt in enumerate(prompts)]
await asyncio.gather(*tasks)
```

### Stream Identification
Each approach uses different methods to identify which output comes from which stream:
- **Bare-bone**: `[STREAM-1]` prefixes
- **Cost tracking**: Label-based identification
- **Handler streaming**: Custom handler prefixes

### Error Handling
All examples include proper error handling for individual stream failures without affecting other streams.

## 📋 When to Use Each

| Example | Use Case |
|---------|----------|
| `bare_bone_streaming.py` | Raw JSON debugging, simple parallel execution |
| `cost_tracking.py` | Budget tracking, usage monitoring, production apps |
| `handler_streaming.py` | Custom text processing, real-time apps, progress tracking |

## 🔧 Requirements

- Python 3.7+
- `codesys` package with `AsyncAgent`
- Claude CLI tool installed
- Valid Anthropic API key

## 💡 Tips

1. **Performance**: All examples run requests truly in parallel, not sequentially
2. **Cost**: Use `cost_tracking.py` to monitor API usage costs
3. **Debugging**: Use `bare_bone_streaming.py` to see raw Claude responses
4. **Production**: Use `handler_streaming.py` for real applications with custom processing

## 🎯 Next Steps

Try combining approaches:
- Use cost tracking with custom handlers
- Add progress monitoring to bare-bone streaming
- Implement custom error recovery strategies