# Getting Started Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Navigate to project directory
cd agentic-ai-systems

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3. Test the API

Open a new terminal and run:

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Analyze the benefits of async programming"}'
```

You'll get a response like:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### 4. Execute the Task

```bash
curl -X POST http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000/execute
```

You'll see streaming events:
```json
{"event_type": "step_started", "task_id": "...", "data": {...}}
{"event_type": "partial_output", "task_id": "...", "data": {...}}
{"event_type": "step_completed", "task_id": "...", "data": {...}}
...
{"event_type": "task_completed", "task_id": "...", "data": {...}}
```

### 5. Check Task Status

```bash
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000/status
```

---

## Using the Example Client

The project includes a Python client example that demonstrates the full workflow:

```bash
# In a new terminal (with venv activated)
python example_client.py
```

This will:
1. Create a task
2. Stream execution events
3. Display progress in real-time
4. Show final results

---

## API Documentation

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### 1. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "agentic-ai-system"
}
```

#### 2. Create Task
```bash
POST /tasks
Content-Type: application/json

{
  "task_description": "Your task here"
}
```

Response:
```json
{
  "task_id": "uuid",
  "status": "pending"
}
```

#### 3. Execute Task (Streaming)
```bash
POST /tasks/{task_id}/execute
```

Streams newline-delimited JSON events:
```
{"event_type": "step_started", ...}
{"event_type": "partial_output", ...}
{"event_type": "step_completed", ...}
{"event_type": "task_completed", ...}
```

#### 4. Get Task Status
```bash
GET /tasks/{task_id}/status
```

Response:
```json
{
  "task_id": "uuid",
  "status": "completed",
  "user_input": "Your task",
  "final_output": "Result here",
  "error_message": null
}
```

#### 5. List All Tasks
```bash
GET /tasks
```

Response:
```json
{
  "tasks": [
    {
      "task_id": "uuid",
      "status": "completed",
      "user_input": "Task description",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

---

## Project Structure

```
agentic-ai-systems/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py              # Agent factory
│   │   ├── retriever.py             # RetrieverAgent
│   │   ├── analyzer.py              # AnalyzerAgent
│   │   └── writer.py                # WriterAgent
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # FastAPI endpoints
│   ├── core/
│   │   ├── __init__.py              # Orchestrator factory
���   │   └── orchestrator.py          # TaskOrchestrator
│   └── models/
│       └── __init__.py              # Data models
├── main.py                          # Entry point
├── example_client.py                # Example usage
├── requirements.txt                 # Dependencies
├── README.md                        # Full documentation
├── SYSTEM_DESIGN.md                 # Architecture details
├── POST_MORTEM.md                   # Design decisions
├── VIDEO_SCRIPT.md                  # Video explanation
└── GETTING_STARTED.md               # This file
```

---

## Understanding the Code

### 1. Models (app/models/__init__.py)

Defines data structures:
- `TaskState`: Tracks task execution state
- `ExecutionPlan`: Contains steps to execute
- `ExecutionStep`: Individual step in the plan
- `StreamEvent`: Events sent to clients

### 2. Agents (app/agents/)

Three specialized agents:

**RetrieverAgent** (`retriever.py`):
- Fetches context from knowledge base
- Simple keyword matching
- Returns relevant documents

**AnalyzerAgent** (`analyzer.py`):
- Breaks tasks into steps
- Creates execution plan
- Deterministic output

**WriterAgent** (`writer.py`):
- Generates final output
- Combines all context
- Produces comprehensive report

### 3. Orchestrator (app/core/orchestrator.py)

Main coordination logic:
- Task state management
- Execution planning
- Agent coordination
- Retry logic with exponential backoff
- Event streaming

### 4. API Routes (app/api/routes.py)

FastAPI endpoints:
- Task creation
- Task execution with streaming
- Status queries
- Task listing

### 5. Main Application (main.py)

Entry point:
- Initializes FastAPI app
- Adds middleware
- Starts uvicorn server

---

## Common Tasks

### Run with Different Configuration

```python
# In main.py, modify:
orchestrator = TaskOrchestrator(
    max_queue_size=200,  # Increase queue size
    max_retries=5        # Increase retry attempts
)
```

### Add Custom Knowledge Base

```python
# In app/agents/retriever.py, modify knowledge_base:
self.knowledge_base = {
    "your_category": [
        "Your document 1",
        "Your document 2",
    ],
}
```

### Modify Retry Strategy

```python
# In app/core/orchestrator.py, modify _execute_step_with_retry:
backoff_delay = 0.5 * (2 ** (step.retry_count - 1))  # Longer delays
```

### Add New Agent

```python
# Create app/agents/custom.py
class CustomAgent:
    async def execute(self, step: ExecutionStep, context: Dict) -> str:
        # Your implementation
        return result

# Register in app/agents/__init__.py
@classmethod
def get_custom(cls):
    if cls._custom is None:
        cls._custom = CustomAgent()
    return cls._custom
```

---

## Debugging

### Enable Debug Logging

```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Task State

```python
from app.core import get_orchestrator

orchestrator = get_orchestrator()
task_state = orchestrator.get_task_state(task_id)
print(task_state.to_dict())
```

### Monitor Events

```python
# In example_client.py, add:
print(f"Full event: {json.dumps(event, indent=2)}")
```

---

## Performance Tips

1. **Increase workers**: `uvicorn main:app --workers 4`
2. **Increase queue size**: `TaskOrchestrator(max_queue_size=500)`
3. **Reduce retry delays**: Modify backoff calculation
4. **Cache context**: Add caching to RetrieverAgent
5. **Parallel execution**: Modify orchestrator for parallel steps

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Import Errors

```bash
# Ensure you're in the project directory
cd agentic-ai-systems

# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Connection Refused

```bash
# Make sure server is running
python main.py

# Check if it's listening
curl http://localhost:8000/health
```

### Streaming Not Working

```bash
# Ensure you're using the correct endpoint
POST /tasks/{task_id}/execute

# Check response headers
curl -v -X POST http://localhost:8000/tasks/{task_id}/execute
```

---

## Next Steps

1. **Read the documentation**:
   - `README.md`: Full system overview
   - `SYSTEM_DESIGN.md`: Architecture details
   - `POST_MORTEM.md`: Design decisions

2. **Explore the code**:
   - Start with `main.py`
   - Then `app/api/routes.py`
   - Then `app/core/orchestrator.py`
   - Finally, individual agents

3. **Extend the system**:
   - Add new agents
   - Implement persistent storage
   - Add authentication
   - Add monitoring

4. **Deploy to production**:
   - Use Docker
   - Deploy to Kubernetes
   - Add load balancing
   - Set up monitoring

---

## Support

For issues or questions:
1. Check the documentation files
2. Review the example client
3. Check the code comments
4. Inspect the logs

---

## License

MIT License - See LICENSE file for details
