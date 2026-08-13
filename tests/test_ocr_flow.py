import io
import time

import httpx
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:8000"
FILE_NAME = "scanned_receipt.pdf"
CONTENT_TYPE = "application/pdf"


def generate_image_pdf() -> bytes:
    """Creates a PDF that is purely an image (no text layer)."""
    # Create a white image
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw literal pixels onto the image
    draw.text((20, 50), "CONFIDENTIAL INVOICE: $4,500", fill=(0, 0, 0))
    draw.text((20, 80), "This text was extracted using OCR!", fill=(0, 0, 0))

    # Save as PDF bytes
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format="PDF")
    return pdf_bytes.getvalue()


def run_test():
    print("🚀 Starting OCR PDF Ingestion Test...")

    scanned_pdf_bytes = generate_image_pdf()

    # 1. Authenticate
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": "test_uploader@acme.com", "password": "SecurePassword123!"},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Upload Flow
    print("1️⃣ Generating image-based PDF & Uploading...")
    init_resp = httpx.post(
        f"{BASE_URL}/v1/documents/upload",
        json={
            "filename": FILE_NAME,
            "content_type": CONTENT_TYPE,
            "file_size": len(scanned_pdf_bytes),
        },
        headers=headers,
    )
    doc_id = init_resp.json()["doc_id"]

    httpx.put(
        init_resp.json()["upload_url"],
        content=scanned_pdf_bytes,
        headers={"Content-Type": CONTENT_TYPE},
    )
    httpx.patch(
        f"{BASE_URL}/v1/documents/{doc_id}/status",
        json={"status": "UPLOADED"},
        headers=headers,
    )

    print("⏳ Waiting 4 seconds for OCR to process...")
    time.sleep(4)

    # 3. Verify
    doc_resp = httpx.get(f"{BASE_URL}/v1/documents/{doc_id}", headers=headers)
    print(f"\n🎉 Document Status: {doc_resp.json()['status']}")


if __name__ == "__main__":
    run_test()
