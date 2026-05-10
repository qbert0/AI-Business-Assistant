from __future__ import annotations

from io import BytesIO

from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter

from deepdoc.parsers.base import BaseParser, ParsedDocument


class DoclingParser(BaseParser):
    input_format: InputFormat

    def __init__(self) -> None:
        self.converter = DocumentConverter(allowed_formats=[self.input_format])

    def parse_bytes(self, file_bytes: bytes, source_name: str) -> ParsedDocument:
        source = DocumentStream(name=source_name, stream=BytesIO(file_bytes))
        result = self.converter.convert(source)
        document = result.document

        markdown = document.export_to_markdown()
        text = document.export_to_markdown(strict_text=True)

        return ParsedDocument(
            text=text,
            markdown=markdown,
            source_name=source_name,
            parser_name=self.name,
            metadata={
                "input_format": self.input_format.value,
            },
        )
