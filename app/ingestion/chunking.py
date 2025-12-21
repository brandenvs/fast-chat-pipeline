from typing import List

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = max(0, end - overlap)
    return chunks
