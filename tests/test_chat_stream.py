import asyncio
import json

import httpx


async def test_stream():
    url = "http://localhost:8000/v1/chat/stream"
    payload = {
        "query": "Why are they highly confidential?",  # Follow-up question!
        "tenant_id": "d8e68631-71e1-4381-bdbd-5191314dd149",
        "session_id": "6e83f5c3-5d0f-44c7-8574-9b75c84bbeb8",  # Pass your DB session ID here
        "top_k": 3,
    }

    print("🚀 Starting Streaming Request...")
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload, timeout=30.0) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    # Parse the SSE JSON payload
                    data = json.loads(line[6:])

                    if data["type"] == "meta":
                        print(f"\n[💾 Session Created in DB] ID: {data['session_id']}")
                        print(f"[🔍 Sources Retrieved]: {len(data['sources'])}")
                        print("\n=== 🤖 ASSISTANT STREAM ===")
                    elif data["type"] == "token":
                        # Print tokens to console exactly as they stream in
                        print(data["content"], end="", flush=True)

            print("\n\n=== STREAM COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(test_stream())
