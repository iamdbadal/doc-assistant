import os
import time
from pathlib import Path

import httpx
import pymupdf  # type: ignore
from dotenv import load_dotenv
from pinecone import Pinecone  # type: ignore

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = "http://localhost:8000"
FILE_NAME = "vector_test_doc.pdf"
CONTENT_TYPE = "application/pdf"


def generate_text_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "This is a highly confidential document used to test the integration "
        "between Cohere embeddings and the Pinecone vector database! "
        "If you can retrieve this, the RAG pipeline is working.",
    )
    return doc.write()


def run_test():
    print("🚀 Starting End-to-End RAG Pipeline Test...")

    pdf_bytes = generate_text_pdf()

    # Use a client with an explicit 30s timeout for all network calls
    with httpx.Client(timeout=30.0) as client:
        # 1. Authenticate
        print("\n🔐 Logging in...")
        login_resp = client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "test_uploader@acme.com",
                "password": "SecurePassword123!",
            },
        )
        if login_resp.status_code != 200:
            print("❌ Login failed! Did you run the seed script?")
            return

        access_token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Upload Flow
        print("📤 Initializing upload...")
        init_resp = client.post(
            f"{BASE_URL}/v1/documents/upload",
            json={
                "filename": FILE_NAME,
                "content_type": CONTENT_TYPE,
                "file_size": len(pdf_bytes),
            },
            headers=headers,
        )

        doc_id = init_resp.json()["doc_id"]
        upload_url = init_resp.json()["upload_url"]

        print("💾 Uploading file bytes to MinIO...")
        client.put(
            upload_url, content=pdf_bytes, headers={"Content-Type": CONTENT_TYPE}
        )

        print("✅ Triggering background processing...")
        client.patch(
            f"{BASE_URL}/v1/documents/{doc_id}/status",
            json={"status": "UPLOADED"},
            headers=headers,
        )

        print(
            "⏳ Waiting 8 seconds for extraction, Cohere embeddings, and Pinecone upsert..."
        )
        time.sleep(8)

        # 3. Verify PostgreSQL Status
        doc_resp = client.get(f"{BASE_URL}/v1/documents/{doc_id}", headers=headers)
        status = doc_resp.json()["status"]
        print(f"\n📊 PostgreSQL Document Status: {status}")

        if status != "COMPLETED":
            print(
                "❌ Document did not complete processing. Check FastAPI logs for errors."
            )
            return

    # 4. Verify Pinecone
    print("\n🌲 Connecting directly to Pinecone to verify vectors...")
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX")

        if not index_name:
            print("⚠️ PINECONE_INDEX not found in .env. Skipping Pinecone check.")
            return

        index = pc.Index(index_name)
        stats = index.describe_index_stats()

        print("\n🎉 PINECONE STATS:")
        print(f"Total Vectors: {stats.total_vector_count}")
        print(f"Namespaces: {stats.namespaces}")

        print(
            "\n✨ SUCCESS! Your full ingestion and vectorization pipeline is operational!"
        )

    except Exception as e:
        print(f"❌ Failed to verify Pinecone: {e}")


if __name__ == "__main__":
    run_test()
