from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Literal
from xml.etree import ElementTree

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


PreviewKind = Literal["text", "image", "pdf", "download"]


@dataclass(slots=True)
class DocumentPreviewPayload:
    kind: PreviewKind
    content: str | None = None
    message: str | None = None


TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".log", ".json"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


def _extension(file_name: str) -> str:
    if "." not in file_name:
        return ""
    return "." + file_name.rsplit(".", 1)[-1].lower()


def _normalize_text(content: str, *, limit: int = 50000) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"[ \t]{2,}", " ", content)
    return content.strip()[:limit]


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text(content: bytes) -> str | None:
    if PdfReader is None:
        return None
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)
    return _normalize_text("\n\n".join(parts)) if parts else None


def _extract_docx_text(content: bytes) -> str | None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile):
        return None

    root = ElementTree.fromstring(xml_bytes)
    texts = [node.text for node in root.iter() if node.tag.endswith("}t") and node.text]
    return _normalize_text("\n".join(texts)) if texts else None


def _extract_xlsx_text(content: bytes) -> str | None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        return None

    with archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.iter():
                if item.tag.endswith("}t") and item.text:
                    shared_strings.append(item.text)

        rows: list[str] = []
        worksheet_files = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet"))
        for worksheet_file in worksheet_files:
            root = ElementTree.fromstring(archive.read(worksheet_file))
            current_row: list[str] = []
            for cell in root.iter():
                if not cell.tag.endswith("}c"):
                    continue
                cell_type = cell.attrib.get("t")
                value_node = next((child for child in cell if child.tag.endswith("}v")), None)
                if value_node is None or value_node.text is None:
                    continue
                value = value_node.text
                if cell_type == "s":
                    try:
                        value = shared_strings[int(value)]
                    except (ValueError, IndexError):
                        pass
                current_row.append(str(value))
            if current_row:
                rows.append("\t".join(current_row))

        return _normalize_text("\n".join(rows)) if rows else None


def extract_document_text(file_name: str, content: bytes) -> str | None:
    ext = _extension(file_name)
    if ext in TEXT_EXTENSIONS:
        return _normalize_text(_decode_text(content))
    if ext == ".pdf":
        return _extract_pdf_text(content)
    if ext == ".docx":
        return _extract_docx_text(content)
    if ext == ".xlsx":
        return _extract_xlsx_text(content)
    return None


def build_preview_payload(file_name: str, content: bytes) -> DocumentPreviewPayload:
    ext = _extension(file_name)
    if ext == ".pdf":
        return DocumentPreviewPayload(kind="pdf")
    if ext in IMAGE_EXTENSIONS:
        return DocumentPreviewPayload(kind="image")

    extracted_text = extract_document_text(file_name, content)
    if extracted_text:
        return DocumentPreviewPayload(kind="text", content=extracted_text)

    return DocumentPreviewPayload(
        kind="download",
        message="Dinh dang nay chua co viewer trich noi dung truc tiep. Ban van co the mo file goc.",
    )
