# Agentic AI System for Multi-Step Task Execution

A production-grade, fully asynchronous **agentic AI system** built with **FastAPI** that orchestrates complex, multi-step task execution using specialized agents and real-time streaming responses.

This project is implemented **from scratch** (no LangChain, AutoGPT, CrewAI, etc.) to demonstrate a clear understanding of agent orchestration, async systems, and backend architecture.

---

## 🚀 System Overview

The system:
- Accepts complex user tasks via REST APIs
- Breaks tasks into structured execution plans
- Delegates work to specialized agents
- Streams real-time execution events
- Handles failures using exponential backoff
- Applies backpressure with async queues
- Tracks task state across the entire lifecycle

---

## 🧠 Architecture

┌─────────────────────────────────────────────────────────────┐
│ FastAPI Application │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ REST API Layer │ │
│ │ POST /tasks - Create task │ │
│ │ POST /tasks/{id}/execute - Execute & stream events │ │
│ │ GET /tasks/{id}/status - Task status │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────┐
│ Task Orchestrator │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ - Task State Management │ │
│ │ - Async Execution Queue │ │
│ │ - Retry Logic (Exponential Backoff) │ │
│ │ - Event Streaming │ │
│ │ - Backpressure Handling │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────┐
│ Agent Layer │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Retriever │ │ Analyzer │ │ Writer │ │
│ │ Agent │ │ Agent │ │ Agent │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────┘


---

## 🤖 Agent Responsibilities

### RetrieverAgent
- Fetches relevant context or knowledge
- Simulates I/O-bound operations
- Returns empty context on failure

### AnalyzerAgent
- Converts user input into structured execution plans
- Produces deterministic multi-step workflows
- Retries on failure using exponential backoff

### WriterAgent
- Generates final output incrementally
- Streams partial responses
- Preserves partial output on failure

---

## 🔁 Orchestration Flow

### Task Creation
```http
POST /tasks
{
  "task_description": "Analyze async programming impact"
}


Response:

{
  "task_id": "uuid",
  "status": "pending"
}

Task Execution
POST /tasks/{task_id}/execute


Streams newline-delimited JSON (application/x-ndjson):

{ "event_type": "step_started", "data": { "step": "analysis" } }
{ "event_type": "partial_output", "data": { "content": "..." } }
{ "event_type": "task_completed", "data": { "final_output": "..." } }

⚙️ Async & Streaming Design

Fully async FastAPI endpoints

Non-blocking agent execution

NDJSON streaming for real-time updates

Backpressure via bounded asyncio queues

Supports concurrent task execution

🔄 Failure Handling
Retry Strategy
Retry 1 → immediate
Retry 2 → 0.1s
Retry 3 → 0.2s
Retry 4 → 0.4s