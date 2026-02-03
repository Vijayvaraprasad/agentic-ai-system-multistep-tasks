# Agentic AI System for Multi-Step Task Execution

A production-grade, fully asynchronous multi-agent system built with FastAPI that orchestrates complex task execution through specialized agents with streaming responses.

## System Overview

This system implements a custom-built agent orchestration framework (no LangChain, AutoGPT, or similar frameworks) that:

- **Accepts complex user tasks** via REST API
- **Analyzes tasks** into structured execution plans
- **Distributes work** to specialized agents (Retriever, Analyzer, Writer)
- **Streams real-time events** to clients as execution progresses
- **Handles failures gracefully** with exponential backoff retry logic
- **Manages backpressure** through queue size limits
- **Tracks task state** throughout the entire lifecycle

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  ┌──────────────────────────────────────────��───────────┐   │
│  │              REST API Endpoints                      │   │
│  │  POST /tasks              - Create task              │   │
│  │  POST /tasks/{id}/execute - Execute & stream events  │   │
│  │  GET /tasks/{id}/status   - Get task status          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Task Orchestrator                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Task State Management                            │   │
│  │  - Execution Queue (asyncio.Queue)                  │   │
│  │  - Retry Logic (Exponential Backoff)                ��   │
│  │  - Event Streaming                                  │   │
│  │  - Backpressure Handling                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Retriever   │  │   Analyzer   │  │    Writer    │      │
│  │   Agent      │  │    Agent     │  │    Agent     │      │
│  │              │  │              │  │              │      │
│  │ - Fetches    │  │ - Breaks     │  │ - Generates  │      │
│  │   context    │  │   down tasks │  │   output     │      │
│  │ - Queries    │  │ - Creates    │  │ - Formats    │      │
│  │   knowledge  │  │   plans      │  │   results    │      │
│  │   base       │  │ - Determines │  │              │      │
│  │              │  │   strategy   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

### 1. RetrieverAgent
- **Purpose**: Fetches relevant context from knowledge sources
- **Input**: Query string from task
- **Output**: Retrieved context/documents
- **Latency**: ~100ms (simulated I/O)
- **Failure Mode**: Returns empty context on error

### 2. AnalyzerAgent
- **Purpose**: Breaks complex tasks into structured execution steps
- **Input**: User task description
- **Output**: ExecutionPlan with 3 deterministic steps
- **Latency**: ~200ms (analysis work)
- **Failure Mode**: Retries with exponential backoff

### 3. WriterAgent
- **Purpose**: Generates final output incrementally
- **Input**: Task, analysis, and context from previous steps
- **Output**: Comprehensive report
- **Latency**: ~100ms (generation work)
- **Failure Mode**: Graceful degradation with partial output

## Orchestration Flow

### Step 1: Task Creation
```
POST /tasks
{
  "task_description": "Analyze the impact of async programming on system performance"
}
↓
Returns: { "task_id": "uuid", "status": "pending" }
```

### Step 2: Task Analysis
- Orchestrator calls AnalyzerAgent
- Creates ExecutionPlan with 3 steps:
  1. Retrieve context (RetrieverAgent)
  2. Analyze task (AnalyzerAgent)
  3. Generate output (WriterAgent)

### Step 3: Execution with Streaming
```
POST /tasks/{task_id}/execute
↓
Streams JSON events (newline-delimited):
{
  "event_type": "step_started",
  "task_id": "uuid",
  "data": { "step_id": "step_001", "description": "..." }
}
{
  "event_type": "partial_output",
  "task_id": "uuid",
  "data": { "step_id": "step_001", "output": "..." }
}
{
  "event_type": "step_completed",
  "task_id": "uuid",
  "data": { "step_id": "step_001", "status": "completed" }
}
...
{
  "event_type": "task_completed",
  "task_id": "uuid",
  "data": { "status": "completed", "final_output": "..." }
}
```

## Async & Streaming Design

### Async-First Architecture
- **All endpoints are async**: Uses `async def` for all route handlers
- **Non-blocking I/O**: All agent operations use `await asyncio.sleep()` to simulate I/O
- **Concurrent execution**: Multiple tasks can execute simultaneously
- **Event loop integration**: Leverages Python's asyncio event loop

### Streaming Implementation
- **Media Type**: `application/x-ndjson` (newline-delimited JSON)
- **Event Format**: Each event is a complete JSON object followed by newline
- **Real-time feedback**: Clients receive events as they occur
- **Backpressure**: Queue size limits prevent memory exhaustion

### Queue Management
```python
# Execution queue with backpressure
execution_queue = asyncio.Queue(maxsize=100)

# Manual batching: Process steps sequentially
for step in execution_plan.steps:
    await execute_step_with_retry(step)
    yield StreamEvent(...)
```

## Failure Handling Strategy

### Retry Logic with Exponential Backoff
```
Attempt 1: Immediate
Attempt 2: Wait 0.1s (2^0 * 0.1)
Attempt 3: Wait 0.2s (2^1 * 0.1)
Attempt 4: Wait 0.4s (2^2 * 0.1)
Max Retries: 3 (configurable)
```

### Graceful Degradation
- **Step Failure**: Task fails, error event streamed to client
- **Partial Output**: Previous step outputs preserved
- **Error Context**: Full error message and retry count included
- **Task State**: Marked as FAILED with error_message

### Error Recovery
```python
async def _execute_step_with_retry(step, context):
    while step.retry_count < step.max_retries:
        try:
            result = await agent.execute(step)
            step.status = StepStatus.COMPLETED
            return True
        except Exception as e:
            step.retry_count += 1
            if step.retry_count < step.max_retries:
                backoff = 0.1 * (2 ** (step.retry_count - 1))
                await asyncio.sleep(backoff)
            else:
                step.status = StepStatus.FAILED
                return False
```

## Scaling Considerations

### Horizontal Scaling
1. **Stateless Design**: Each orchestrator instance is independent
2. **Distributed Task Store**: Replace in-memory dict with Redis/PostgreSQL
3. **Message Queue**: Replace asyncio.Queue with RabbitMQ/Kafka
4. **Load Balancing**: Deploy multiple FastAPI instances behind nginx

### Vertical Scaling
1. **Async Concurrency**: Increase worker count in uvicorn
2. **Connection Pooling**: Implement for external services
3. **Memory Management**: Monitor task_states dict size
4. **CPU Optimization**: Profile agent execution times

### Performance Optimization
1. **Caching**: Cache frequently retrieved context
2. **Parallel Steps**: Modify orchestrator to execute independent steps in parallel
3. **Agent Pooling**: Reuse agent instances (already implemented)
4. **Batch Processing**: Group similar tasks for efficiency

## Project Structure

```
agentic-ai-systems/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py              # Agent factory
│   │   ├── retriever.py             # RetrieverAgent class
│   │   ├── analyzer.py              # AnalyzerAgent class
│   │   └── writer.py                # WriterAgent class
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # FastAPI endpoints
│   ├── core/
│   │   ├── __init__.py              # Orchestrator factory
│   │   └── orchestrator.py          # TaskOrchestrator class
│   └── models/
│       └── __init__.py              # Data models & enums
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── SYSTEM_DESIGN.md                 # Detailed architecture
└── POST_MORTEM.md                   # Design decisions & trade-offs
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- pip or conda

### Installation
```bash
# Clone or navigate to project directory
cd agentic-ai-systems

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### Example 1: Create and Execute a Task
```bash
# Create task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Analyze the benefits of async programming"}'

# Response:
# {"task_id": "550e8400-e29b-41d4-a716-446655440000", "status": "pending"}

# Execute task with streaming
curl -X POST http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000/execute

# Streams events as they occur...
```

### Example 2: Check Task Status
```bash
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000/status

# Response:
# {
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "completed",
#   "user_input": "Analyze the benefits of async programming",
#   "final_output": "...",
#   "error_message": null
# }
```

### Example 3: List All Tasks
```bash
curl http://localhost:8000/tasks

# Response:
# {
#   "tasks": [
#     {
#       "task_id": "550e8400-e29b-41d4-a716-446655440000",
#       "status": "completed",
#       "user_input": "Analyze the benefits...",
#       "created_at": "2024-01-15T10:30:00"
#     }
#   ],
#   "total": 1
# }
```

## Testing

### Manual Testing with curl
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test task creation
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Test task"}'

# Test streaming execution
curl -X POST http://localhost:8000/tasks/{task_id}/execute
```

### Python Client Example
```python
import requests
import json

# Create task
response = requests.post(
    "http://localhost:8000/tasks",
    json={"task_description": "Analyze system performance"}
)
task_id = response.json()["task_id"]

# Execute with streaming
response = requests.post(
    f"http://localhost:8000/tasks/{task_id}/execute",
    stream=True
)

for line in response.iter_lines():
    if line:
        event = json.loads(line)
        print(f"Event: {event['event_type']}")
        print(f"Data: {event['data']}")
```

## Key Design Decisions

1. **No External Agent Frameworks**: Custom implementation provides full control and transparency
2. **Async-First**: All operations are non-blocking for maximum concurrency
3. **Streaming Events**: Real-time feedback without polling
4. **Exponential Backoff**: Prevents cascading failures
5. **In-Memory State**: Fast access; can be replaced with persistent store
6. **Sequential Step Execution**: Ensures deterministic output; can be parallelized

## Monitoring & Debugging

### Logging
- All operations logged to console with timestamps
- Log levels: INFO (default), DEBUG (detailed), ERROR (failures)

### Task State Inspection
```python
from app.core import get_orchestrator

orchestrator = get_orchestrator()
task_state = orchestrator.get_task_state(task_id)
print(task_state.to_dict())
```

### Event Inspection
Each streaming event includes:
- `event_type`: Type of event (step_started, partial_output, etc.)
- `task_id`: Associated task ID
- `timestamp`: When event occurred
- `data`: Event-specific data

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Task Creation | <1ms | In-memory operation |
| Task Analysis | ~200ms | Analyzer agent work |
| Retrieval Step | ~100ms | Simulated I/O |
| Analysis Step | ~150ms | Processing |
| Writing Step | ~100ms | Generation |
| **Total Task** | **~550ms** | Sequential execution |

## Limitations & Future Improvements

1. **In-Memory Storage**: Replace with persistent database for production
2. **Sequential Execution**: Implement parallel step execution for independent steps
3. **Agent Specialization**: Add more specialized agents (Validator, Optimizer, etc.)
4. **Caching**: Implement context caching for repeated queries
5. **Monitoring**: Add Prometheus metrics and distributed tracing
6. **Authentication**: Add API key or OAuth2 authentication
7. **Rate Limiting**: Implement per-user rate limits

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.
