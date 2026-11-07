from pathlib import Path

MAX_PAGES = 30          # scanned pages sent per document
MIN_TEXT_CHARS = 100    # below this a PDF is treated as a scan

IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def extract_content(path, dpi: int = 150) -> dict:
    """Return {"type": "text", "text": ...} or {"type": "images", "images": [(bytes, mime)]}."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        import pymupdf

        with pymupdf.open(str(p)) as doc:
            text = "".join(page.get_text() for page in doc).strip()
            if len(text) >= MIN_TEXT_CHARS:
                return {"type": "text", "text": text}
            images = []
            for index, page in enumerate(doc):
                if index >= MAX_PAGES:
                    break
                images.append((page.get_pixmap(dpi=dpi).tobytes("png"), "image/png"))
        return {"type": "images", "images": images}

    if ext == ".docx":
        from docx import Document

        document = Document(str(p))
        lines = [para.text for para in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        return {"type": "text", "text": "\n".join(lines)}

    if ext in IMAGE_MIME:
        return {"type": "images", "images": [(p.read_bytes(), IMAGE_MIME[ext])]}

    raise ValueError(f"Unsupported file type: {ext}")
