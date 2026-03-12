# AG-UI Protocol Example

This example demonstrates how to use AgentScope Runtime to build a ReAct Agent service compatible with the AG-UI protocol. The service supports streaming responses, tool calls, conversation history management, and state persistence.

## Features

- **AG-UI Protocol Support**: Full AG-UI protocol compatibility
- **ReAct Agent**: Uses AgentScope's ReAct Agent for reasoning and action loops
- **Tool Calls**: Integrates `get_weather` and `execute_python_code` as example tools
- **Conversation Management**: Supports multi-session history management and persistence
- **State Management**: Agent state can be saved and restored across requests

## Prerequisites

### 1. Install Dependencies

Make sure agentscope-runtime and its dependencies are installed:

```bash
pip install --upgrade agentscope-runtime
```

### 2. Configure DashScope API Key

This example uses DashScope's qwen-max model. Configure your API key:

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

You can also modify the API key directly in `agent.py` or switch to another model.

## Running the Agent Service

Start the service using the `agentscope` CLI:

```bash
# Run from the current directory:
agentscope run .

# Or run from the project root:
agentscope run examples/ag-ui
```

The service will start at `http://localhost:8080`, with the AG-UI protocol endpoint at `/ag-ui`.

## Making Requests

Send a POST request using curl. The following request triggers a tool call:

```bash
uuid=$(python -c "import uuid; print(uuid.uuid4(), end='')")

curl -X POST http://localhost:8080/ag-ui \
  --header "Content-Type: application/json" \
  --data '{
    "context": [],
    "messages": [
      {
        "content": "What is the weather in Beijing today?",
        "id": "'$uuid'",
        "role": "user"
      }
    ],
    "runId": "run_456",
    "threadId": "thread_123",
    "context": [],
    "tools": [],
    "forwardedProps": {},
    "state": null
  }'
```

### Request Parameters

- **threadId**: Thread/session ID used to identify different conversation sessions
- **runId**: Run ID, a unique identifier for each request
- **messages**: Message list containing user input and conversation history
- **state**: (Optional) Agent state data for restoring the agent's state
- **context**: Context information
- **tools**: Tool list
- **forwardedProps**: Forwarded properties

### Response Format

The service returns streaming responses in Server-Sent Events (SSE) format:

```plain
data: {"type": "RUN_STARTED", "threadId": "thread_123", "runId": "run_456"}

data: {"type": "TOOL_CALL_START", "toolCallId": "call_51529f037f2641ddba53cd", "toolCallName": "get_weather", "message_id": "msg_7fb52b7b-4037-4868-907e-125d18828992_0"}

data: {"type": "TOOL_CALL_ARGS", "toolCallId": "call_51529f037f2641ddba53cd", "delta": "{\"location\": \"Beijing\"}"}

data: {"type": "TOOL_CALL_END", "toolCallId": "call_51529f037f2641ddba53cd"}

data: {"type": "TOOL_CALL_RESULT", "messageId": "msg_012a1e31-af54-4bb1-99db-4ebe2020c89e_0", "toolCallId": "call_51529f037f2641ddba53cd", "content": "[{\"type\": \"text\", \"text\": \"The weather in Beijing is sunny with a temperature of 25°C.\"}]", "role": "tool"}

data: {"type": "TEXT_MESSAGE_START", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0", "role": "assistant"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0", "delta": "The weather"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0", "delta": " in Beijing today is"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0", "delta": " sunny,"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0", "delta": " with a temperature of 25°C."}

data: {"type": "TEXT_MESSAGE_END", "messageId": "msg_a6dec420-0631-473f-854c-e4c42cf283f0_0"}

data: {"type": "RUN_FINISHED", "threadId": "thread_123", "runId": "run_456"}
```

### Event Types

| Event Type | Description |
|-----------|-------------|
| `RUN_STARTED` | Run started |
| `TOOL_CALL_START` | Tool call started |
| `TOOL_CALL_ARGS` | Tool call arguments (streaming) |
| `TOOL_CALL_END` | Tool call ended |
| `TOOL_CALL_RESULT` | Tool call result |
| `TEXT_MESSAGE_START` | Text message started |
| `TEXT_MESSAGE_CONTENT` | Text message content (streaming) |
| `TEXT_MESSAGE_END` | Text message ended |
| `RUN_FINISHED` | Run finished |

## Troubleshooting

### Cannot connect to the service

- Confirm the service is running: check terminal output
- Confirm the port is not in use: `lsof -i :8080`

### API Key error

- Check that the `DASHSCOPE_API_KEY` environment variable is set correctly
- Confirm the DashScope API key is valid and has sufficient quota

### Adding custom tools

Define and register new tool functions in `agent.py`:

```python
async def your_custom_tool(param: str) -> ToolResponse:
    """Your tool description."""
    # Implement tool logic
    return ToolResponse(content=[TextBlock(type="text", text="result")])

# Register in create_stateful_agent
toolkit.register_tool_function(your_custom_tool)
```
