from __future__ import annotations

import glob
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_start: int
    page_end: int
    content: str
    metadata: dict[str, Any]


def slugify(value: str, max_length: int = 72) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return (slug or "document")[:max_length].strip("-")


def stable_document_id(path: Path, namespace: str = "benchmark") -> str:
    digest = hashlib.sha1(path.name.encode("utf-8")).hexdigest()[:12]
    return f"{slugify(namespace, 32)}-{slugify(path.stem, 56)}-{digest}"


def discover_reports(pattern: str, limit: int | None = None) -> list[Path]:
    paths = [Path(item) for item in glob.glob(pattern)]
    reports = sorted(path for path in paths if path.is_file() and path.suffix.lower() == ".pdf")
    return reports[:limit] if limit is not None else reports


def extract_pdf_pages(pdf_path: Path) -> list[PageText]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing PyMuPDF. Install with: pip install -r scripts/requirements.txt") from exc

    pages: list[PageText] = []
    with fitz.open(str(pdf_path)) as document:
        for index, page in enumerate(document, start=1):
            text = repair_mojibake(page.get_text("text")).strip()
            if text:
                pages.append(PageText(page_number=index, text=text))
    if not pages:
        raise RuntimeError(f"No extractable text found in PDF: {pdf_path}")
    return pages


def repair_mojibake(text: str) -> str:
    """Repair common UTF-8 text that was decoded as latin-1/cp1252.

    Some Windows Python/PDF extraction paths can produce strings like
    "Má»¥c lá»¥c" instead of "Mục lục". If the text is already valid, this is a no-op.
    """
    if not text or not _looks_like_mojibake(text):
        return text
    candidates = [text]
    for source_encoding in ("latin1", "cp1252"):
        try:
            candidates.append(text.encode(source_encoding).decode("utf-8"))
        except UnicodeError:
            continue
    return min(candidates, key=_mojibake_score)


def _looks_like_mojibake(text: str) -> bool:
    sample = text[:4000]
    markers = ("Ã", "Â", "Ä", "áº", "á»", "Æ", "Ð", "ð")
    return sum(sample.count(marker) for marker in markers) >= 2


def _mojibake_score(text: str) -> int:
    sample = text[:4000]
    markers = ("Ã", "Â", "Ä", "áº", "á»", "Æ", "Ð", "ð", "�")
    return sum(sample.count(marker) for marker in markers)


def split_paragraphs(text: str) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [part.strip() for part in re.split(r"(?<=[.!?。])\s+", normalized) if part.strip()]
    return paragraphs


def split_long_text(text: str, max_chars: int) -> Iterable[str]:
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            yield piece
        start = max(end, start + 1)


def chunk_pages(
    pages: list[PageText],
    *,
    document_id: str,
    document_name: str,
    source_path: Path,
    chunk_chars: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    paragraph_items: list[tuple[int, str]] = []
    for page in pages:
        for paragraph in split_paragraphs(page.text):
            if len(paragraph) > chunk_chars:
                paragraph_items.extend((page.page_number, piece) for piece in split_long_text(paragraph, chunk_chars))
            else:
                paragraph_items.append((page.page_number, paragraph))

    chunks: list[TextChunk] = []
    current: list[tuple[int, str]] = []
    current_chars = 0

    def emit() -> None:
        if not current:
            return
        content = "\n\n".join(item[1] for item in current).strip()
        if not content:
            return
        chunk_index = len(chunks)
        page_start = min(item[0] for item in current)
        page_end = max(item[0] for item in current)
        chunk_id = f"{document_id}-chunk-{chunk_index:04d}"
        metadata = {
            "benchmark": True,
            "document_id": document_id,
            "document_name": document_name,
            "source_path": source_path.as_posix(),
            "chunk_index": chunk_index,
            "page_start": page_start,
            "page_end": page_end,
        }
        chunks.append(
            TextChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                document_name=document_name,
                chunk_index=chunk_index,
                page_start=page_start,
                page_end=page_end,
                content=content,
                metadata=metadata,
            )
        )

    for page_number, paragraph in paragraph_items:
        next_len = len(paragraph) + 2
        if current and current_chars + next_len > chunk_chars:
            emit()
            overlap: list[tuple[int, str]] = []
            overlap_chars = 0
            for item in reversed(current):
                overlap.insert(0, item)
                overlap_chars += len(item[1]) + 2
                if overlap_chars >= chunk_overlap:
                    break
            current = overlap
            current_chars = overlap_chars
        current.append((page_number, paragraph))
        current_chars += next_len
    emit()
    return chunks


def build_chunks_for_report(
    path: Path,
    *,
    chunk_chars: int,
    chunk_overlap: int,
    document_namespace: str = "benchmark",
) -> tuple[list[PageText], list[TextChunk]]:
    document_id = stable_document_id(path, namespace=document_namespace)
    pages = extract_pdf_pages(path)
    chunks = chunk_pages(
        pages,
        document_id=document_id,
        document_name=path.name,
        source_path=path,
        chunk_chars=chunk_chars,
        chunk_overlap=chunk_overlap,
    )
    return pages, chunks
