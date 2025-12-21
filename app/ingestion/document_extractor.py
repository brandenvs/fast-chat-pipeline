from pathlib import Path
from typing import Iterable
import pandas as pd
from docx import Document as DocxDocument

SUPPORTED_TEXT_EXTS = {".txt", ".csv"}
SUPPORTED_WORD_EXTS = {".docx"}
SUPPORTED_EXCEL_EXTS = {".xlsx", ".xls"} 
SUPPORTED_PDF_EXTS = {".pdf"}

def extract_text_data(file_path: Path) -> list[dict]:
    file_type = file_path.suffix.lower()
    if file_type in SUPPORTED_WORD_EXTS:
        return _extract_docx(file_path)

    if file_type == ".txt":
        return _extract_txt(file_path)

    if file_type == ".csv":
        return _extract_csv(file_path)

    if file_type in {".xlsx", ".xls"}:
        return _extract_excel(file_path)

    raise ValueError(f"Unsupported document type: {file_type}")

def _is_heading(paragraph) -> bool:
    style_name = (paragraph.style.name or "").lower()
    return style_name.startswith("heading")

def _heading_level(paragraph) -> int | None:
    name = (paragraph.style.name or "").lower().strip()
    if not name.startswith("heading"):
        return None
    parts = name.split()
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return None

def _extract_docx(file_path: Path) -> list[dict]:
    doc = DocxDocument(str(file_path))

    sections: list[dict] = []
    current_heading = "Untitled"
    current_level = None
    buffer: list[str] = []
    section_index = 0

    def flush():
        nonlocal section_index, buffer
        text = "\n".join([t for t in buffer if t.strip()]).strip()
        if text:
            sections.append({
                "page": None,
                "text": f"{current_heading}\n{text}" if current_heading else text,
                "meta": {
                    "entry": "section",
                    "heading": current_heading,
                    "headingLevel": current_level,
                    "sectionIndex": section_index,
                }
            })
            section_index += 1
        buffer = []

    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue

        if _is_heading(p):
            # new chunk begins
            flush()
            current_heading = text
            current_level = _heading_level(p)
            continue

        buffer.append(text)

    flush()
    return sections

def _extract_txt(file_path: Path) -> list[dict]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    text = text.strip()
    if not text:
        return []
    return [{"page": None, "text": text, "meta": {"entry": "file"}}]

def _extract_csv(file_path: Path) -> list[dict]:
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    return _tabular_to_data(df, meta_base={"entry": "csv"})

def _extract_excel(file_path: Path) -> list[dict]:
    xls = pd.ExcelFile(file_path)
    data: list[dict] = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, keep_default_na=False)
        data.extend(_tabular_to_data(df, meta_base={"entry": "excel", "sheet": sheet_name}))
    xls.close()
    return data

def _tabular_to_data(df: pd.DataFrame, meta_base: dict) -> list[dict]:
    """
    Turns a dataframe into text rows like:
      "colA: valA | colB: valB | ..." - ideal for RAG
    """
    cols = [str(c).strip() for c in df.columns.tolist()]
    data: list[dict] = []
    for idx, row in df.iterrows():
        parts = []
        for c in cols:
            v = str(row.get(c, "")).strip()
            if v:
                parts.append(f"{c}: {v}")
        line = " | ".join(parts).strip()
        if line:
            data.append({"page": None, "text": line, "meta": {**meta_base, "row": int(idx)}})

    return data
