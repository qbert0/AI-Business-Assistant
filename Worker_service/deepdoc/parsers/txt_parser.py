from __future__ import annotations

from deepdoc.parsers.base import BaseParser, ParsedDocument


class TxtParser(BaseParser):
    name = "txt"

    def parse_bytes(self, file_bytes: bytes, source_name: str) -> ParsedDocument:
        text = file_bytes.decode("utf-8")
        return ParsedDocument(
            text=text,
            markdown=text,
            source_name=source_name,
            parser_name=self.name,
            metadata={"encoding": "utf-8"},
        )
