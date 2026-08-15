import asyncio
import json

import httpx

# Adjust this to match your local FastAPI port
API_URL = "http://localhost:8000/v1/query"


async def test_rag_query():
    # Use a specific tenant_id that you know has documents ingested in Pinecone
    test_payload = {
        "query": "What are the main points covered in the document?",
        "tenant_id": "d8e68631-71e1-4381-bdbd-5191314dd149",
        "top_k": 3,
    }

    print(f"Testing RAG Query Endpoint: {API_URL}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}\n")

    # Using the resilient httpx client pattern you established earlier
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(API_URL, json=test_payload)
            response.raise_for_status()

            data = response.json()

            print("=== LLM ANSWER ===")
            print(data.get("answer", "No answer returned."))
            print("\n=== MODEL USED ===")
            print(data.get("model", "Unknown"))

            print("\n=== RETRIEVED SOURCES ===")
            sources = data.get("sources", [])
            if not sources:
                print(
                    "No sources retrieved. (Check if tenant_id has vectors in Pinecone)"
                )

            for idx, source in enumerate(sources, start=1):
                print(f"\n[Source {idx}]")
                print(f"Doc ID:   {source.get('doc_id')}")
                print(f"Chunk ID: {source.get('chunk_id')}")
                print(f"Score:    {source.get('score')}")
                print(f"Text snippet: {source.get('text')[:150]}...")

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(e.response.text)
        except Exception as e:
            print(f"Connection Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_rag_query())
