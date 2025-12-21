from pathlib import Path
from typing import List
from pypdf import PdfReader

from ingestion.ocr_helper import infer_ocr

def needs_ocr(text: str) -> bool:
    return len(text.strip()) < 50

def normalize_text(text: str) -> str:
    return (
        text
        .replace("\x00", "")
        .replace("\u200b", "")
        .strip()
    )

def parse_pdf(file_path: Path) -> List[dict]:
    reader = PdfReader(str(file_path))
    pages = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text(extraction_mode="layout") or ""

        if not text.strip():
            print(f"[INFO] PAGE {idx + 1} IS BLANK - IGNORING ...")
            continue

        if not text.strip():
            text = page.extract_text() or ""

        if needs_ocr(text):
            print('[INFO] PAGE REQUIRES OCR ...')
            text = infer_ocr(file_path, page_num=idx)

        text = normalize_text(text)        
        if text:
            pages.append({
                "page": idx + 1,
                "text": text
            })

    return pages

