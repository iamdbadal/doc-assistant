import json

import httpx

BASE_URL = "http://localhost:8000"
FILE_CONTENT = b"Hello, this is a test document for MinIO!"
FILE_NAME = "test_document.txt"
CONTENT_TYPE = "text/plain"


def run_test():
    print("🚀 Starting End-to-End Upload Test...")

    # 1. Signup / Login to get JWT Token
    print("\n1️⃣ Authenticating...")
    auth_data = {
        "email": "test_uploader@acme.com",
        "password": "SecurePassword123!",
        "tenant_name": "Acme Upload Testers",
    }

    # Try to signup first
    httpx.post(f"{BASE_URL}/auth/signup", json=auth_data)

    # Login to get the access token
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": auth_data["email"], "password": auth_data["password"]},
    )

    if login_resp.status_code != 200:
        print("❌ Login failed:", login_resp.text)
        return

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated successfully!")

    # 2. Initialize the Upload via your API
    print("\n2️⃣ Requesting Presigned URL from API...")
    init_payload = {
        "filename": FILE_NAME,
        "content_type": CONTENT_TYPE,
        "file_size": len(FILE_CONTENT),
    }

    init_resp = httpx.post(
        f"{BASE_URL}/v1/documents/upload", json=init_payload, headers=headers
    )

    if init_resp.status_code != 201:
        print("❌ Upload init failed:", init_resp.text)
        return

    doc_data = init_resp.json()
    doc_id = doc_data["doc_id"]
    upload_url = doc_data["upload_url"]
    print(f"✅ Got Presigned URL for Document ID: {doc_id}")

    # 3. Upload the file DIRECTLY to MinIO (Bypassing your FastAPI server)
    print("\n3️⃣ Uploading file directly to MinIO...")
    # Note: httpx uses 'content' for raw bytes instead of 'data'
    upload_resp = httpx.put(
        upload_url, content=FILE_CONTENT, headers={"Content-Type": CONTENT_TYPE}
    )

    if upload_resp.status_code != 200:
        print("❌ MinIO upload failed:", upload_resp.text)
        return

    print("✅ File uploaded successfully to MinIO!")

    # 4. Confirm the upload status back to your API
    print("\n4️⃣ Updating document status to UPLOADED...")
    status_resp = httpx.patch(
        f"{BASE_URL}/v1/documents/{doc_id}/status",
        json={"status": "UPLOADED"},
        headers=headers,
    )

    if status_resp.status_code != 200:
        print("❌ Status update failed:", status_resp.text)
        return

    print("✅ Status updated successfully!")
    print("\n🎉 End-to-End Test Completed Successfully!")
    print(json.dumps(status_resp.json(), indent=2))


if __name__ == "__main__":
    run_test()
