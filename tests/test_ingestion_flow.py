import json
import time

import httpx

BASE_URL = "http://localhost:8000"

# A mathematically minimal, perfectly valid PDF file in raw bytes
# containing the text: "Hello, this is a test PDF document!"
MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
    b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n"
    b"/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/Contents 5 0 R\n>>\nendobj\n"
    b"4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n"
    b"5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n"
    b"(Hello, this is a test PDF document!) Tj\nET\nendstream\nendobj\n"
    b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
    b"0000000115 00000 n\n0000000229 00000 n\n0000000318 00000 n\n"
    b"trailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n413\n%%EOF\n"
)
FILE_NAME = "sample_test.pdf"
CONTENT_TYPE = "application/pdf"


def run_test():
    print("🚀 Starting End-to-End PDF Ingestion Test...")

    # 1. Authenticate
    auth_data = {
        "email": "test_uploader@acme.com",
        "password": "SecurePassword123!",
        "tenant_name": "Acme Upload Testers",
    }
    httpx.post(f"{BASE_URL}/auth/signup", json=auth_data)

    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": auth_data["email"], "password": auth_data["password"]},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Initialize Upload
    print("\n1️⃣ Requesting Presigned URL for PDF...")
    init_resp = httpx.post(
        f"{BASE_URL}/v1/documents/upload",
        json={
            "filename": FILE_NAME,
            "content_type": CONTENT_TYPE,
            "file_size": len(MINIMAL_PDF),
        },
        headers=headers,
    )
    doc_id = init_resp.json()["doc_id"]
    upload_url = init_resp.json()["upload_url"]

    # 3. Upload PDF directly to MinIO
    print("2️⃣ Uploading PDF directly to MinIO...")
    httpx.put(upload_url, content=MINIMAL_PDF, headers={"Content-Type": CONTENT_TYPE})

    # 4. Confirm Upload (This triggers the background processing)
    print("3️⃣ Updating status to UPLOADED (Triggering Background Task)...")
    httpx.patch(
        f"{BASE_URL}/v1/documents/{doc_id}/status",
        json={"status": "UPLOADED"},
        headers=headers,
    )

    # 5. Wait for background task to complete
    print("\n⏳ Waiting 3 seconds for backend to extract and chunk the PDF...")
    time.sleep(3)

    # 6. Verify Final Status
    print("4️⃣ Checking final document status...")
    check_resp = httpx.get(f"{BASE_URL}/v1/documents/{doc_id}", headers=headers)
    final_doc = check_resp.json()

    print("\n🎉 Final Document State:")
    print(json.dumps(final_doc, indent=2))

    if final_doc["status"] == "COMPLETED":
        print(
            "\n✅ SUCCESS: PDF was successfully extracted, chunked, and saved to the database!"
        )
    elif final_doc["status"] == "FAILED":
        print(
            "\n❌ FAILED: Something broke in the processing pipeline. Check Uvicorn logs!"
        )
    else:
        print(
            f"\n⚠️ UNKNOWN STATE: Document is still '{final_doc['status']}'. Processing might be slow."
        )


if __name__ == "__main__":
    run_test()
