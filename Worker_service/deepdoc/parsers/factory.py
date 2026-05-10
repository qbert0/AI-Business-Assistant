from __future__ import annotations

from pathlib import Path

from deepdoc.parsers.base import BaseParser
from deepdoc.parsers.docx_parser import DocxParser
from deepdoc.parsers.excel_parser import ExcelParser
from deepdoc.parsers.pdf_parser import PdfParser
from deepdoc.parsers.txt_parser import TxtParser


def create_parser(source_name: str) -> BaseParser:
    suffix = Path(source_name).suffix.lower()
    if suffix == ".txt":
        return TxtParser()
    if suffix == ".pdf":
        return PdfParser()
    if suffix == ".docx":
        return DocxParser()
    if suffix in {".xlsx", ".xlsm"}:
        return ExcelParser()
    raise ValueError(f"Unsupported file type: {suffix or source_name}")
