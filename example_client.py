"""
Example client script demonstrating how to use the Agentic AI System.
Run the FastAPI server first: python main.py
Then run this script: python example_client.py
"""

import asyncio
import aiohttp
import json
from typing import AsyncGenerator


async def create_task(session: aiohttp.ClientSession, task_description: str) -> str:
    """Create a new task and return its ID."""
    async with session.post(
        "http://localhost:8000/tasks",
        json={"task_description": task_description},
    ) as response:
        data = await response.json()
        return data["task_id"]


async def stream_task_execution(
    session: aiohttp.ClientSession, task_id: str
) -> AsyncGenerator[dict, None]:
    """Stream task execution events."""
    async with session.post(
        f"http://localhost:8000/tasks/{task_id}/execute"
    ) as response:
        async for line in response.content:
            if line:
                event = json.loads(line.decode())
                yield event


async def get_task_status(session: aiohttp.ClientSession, task_id: str) -> dict:
    """Get the current status of a task."""
    async with session.get(
        f"http://localhost:8000/tasks/{task_id}/status"
    ) as response:
        return await response.json()


async def main():
    """Main example demonstrating the full workflow."""
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a task
        print("=" * 60)
        print("STEP 1: Creating task...")
        print("=" * 60)
        
        task_description = (
            "Analyze the impact of asynchronous programming on system performance "
            "and scalability in modern distributed systems"
        )
        
        task_id = await create_task(session, task_description)
        print(f"✓ Task created with ID: {task_id}\n")
        
        # Step 2: Execute task and stream events
        print("=" * 60)
        print("STEP 2: Executing task and streaming events...")
        print("=" * 60)
        
        event_count = 0
        async for event in stream_task_execution(session, task_id):
            event_count += 1
            event_type = event["event_type"]
            
            if event_type == "step_started":
                data = event["data"]
                print(f"\n📍 Step {data['step_number']}/{data['total_steps']}: {data['description']}")
                print(f"   Agent: {data['agent_type']}")
                
            elif event_type == "partial_output":
                data = event["data"]
                output_preview = data["output"][:100] + "..." if len(data["output"]) > 100 else data["output"]
                print(f"   Output: {output_preview}")
                
            elif event_type == "step_completed":
                print(f"   ✓ Step completed")
                
            elif event_type == "task_completed":
                data = event["data"]
                print(f"\n✓ Task completed successfully!")
                print(f"   Total steps: {data['total_steps']}")
                final_output_preview = data["final_output"][:200] + "..." if len(data["final_output"]) > 200 else data["final_output"]
                print(f"   Final output preview: {final_output_preview}")
                
            elif event_type == "error":
                data = event["data"]
                print(f"\n✗ Error: {data.get('error', 'Unknown error')}")
        
        print(f"\nTotal events received: {event_count}\n")
        
        # Step 3: Get final task status
        print("=" * 60)
        print("STEP 3: Checking final task status...")
        print("=" * 60)
        
        status = await get_task_status(session, task_id)
        print(f"Task ID: {status['task_id']}")
        print(f"Status: {status['status']}")
        print(f"User Input: {status['user_input'][:80]}...")
        if status["final_output"]:
            print(f"Final Output: {status['final_output'][:200]}...")
        if status["error_message"]:
            print(f"Error: {status['error_message']}")
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Agentic AI System - Example Client\n")
    print("Make sure the FastAPI server is running:")
    print("  python main.py\n")
    
    try:
        asyncio.run(main())
    except ConnectionRefusedError:
        print("❌ Error: Could not connect to the server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
