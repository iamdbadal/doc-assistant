import re
from typing import Any, Dict, List

import pymupdf
import pytesseract
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langdetect import LangDetectException, detect
from PIL import Image

# Set the path to the Tesseract executable (adjust this path based on your OS and installation)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def clean_text(raw_text: str) -> str:
    """Normalizes whitespace and cleans up PDF extraction artifacts."""
    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def extract_pages_from_pdf(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Extracts raw text from a PDF, falling back to OCR for scanned pages."""
    pages = []

    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page_num, page in enumerate(doc):
            # 1. Try standard text layer extraction first (Blazing fast)
            text = page.get_text()

            # 2. If empty, this is likely a scanned image. Fallback to OCR!
            if not text.strip():
                try:
                    # Render the page to a high-res image (150 DPI is good for OCR)
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Run Tesseract OCR on the image
                    text = pytesseract.image_to_string(img)
                except pytesseract.TesseractNotFoundError:
                    print(
                        f"⚠️ Tesseract binary not found. Skipping OCR for page {page_num + 1}."
                    )
                    text = ""
                except Exception as e:
                    print(f"⚠️ OCR failed on page {page_num + 1}: {e}")
                    text = ""

            # Only append if we actually found text via either method
            if text.strip():
                pages.append({"page_number": page_num + 1, "text": text})

    return pages


def chunk_document(
    pages: List[Dict[str, Any]], chunk_size: int = 600, chunk_overlap: int = 100
) -> List[Document]:
    """Splits the text into token-based chunks optimized for RAG."""
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    lc_documents = []
    for page in pages:
        cleaned_text = clean_text(page["text"])
        if not cleaned_text:
            continue

        try:
            lang = detect(cleaned_text)
        except LangDetectException:
            lang = "unknown"

        lc_documents.append(
            Document(
                page_content=cleaned_text,
                metadata={"page_number": page["page_number"], "language": lang},
            )
        )

    return text_splitter.split_documents(lc_documents)
