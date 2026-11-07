import re
import shutil
import zipfile
from pathlib import Path


def list_pdfs(folder) -> list[Path]:
    """All PDFs in the folder. Raises OSError if the folder or share is unavailable."""
    items = (f for f in Path(folder).iterdir() if f.is_file() and f.suffix.lower() == ".pdf")
    return sorted(items, key=lambda f: f.name.lower())


def match_pdf(student_id: str, pdfs):
    """Find the PDF whose file name contains the student ID as a separate token."""
    pattern = re.compile(rf"(?<![0-9A-Za-z]){re.escape(student_id)}(?![0-9A-Za-z])", re.IGNORECASE)
    for pdf in pdfs:
        if pattern.search(pdf.stem):
            return pdf
    return None


def copy_files(paths, dest_dir) -> int:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for p in paths:
        shutil.copy2(p, dest / Path(p).name)
    return len(paths)


def make_zip(paths, zip_path) -> int:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=Path(p).name)
    return len(paths)
