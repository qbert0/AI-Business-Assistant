from pathlib import Path
from typing import Any

from conn.rag_service_client import RagServiceClient
from deepdoc.chunkers import chunk_text
from deepdoc.parsers import create_parser
from conn.redis_client import Message
from utils.constants import ROOT_PATH
from utils.logs import logger


class PayloadParserWorker:
    def __init__(
        self,
        name: str = "payload-parser",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.name = name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.rag_service_client = RagServiceClient()

    async def handle(self, message: Message) -> dict[str, Any]:
        payload = message.payload

        if not isinstance(payload, dict):
            raise ValueError("Message payload must be a dictionary")

        source_path = self._resolve_source_path(payload)
        parser = create_parser(source_path.name)
        parsed_document = parser.parse_file(source_path)
        chunks = chunk_text(
            parsed_document.text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )

        logger.info(
            f"[{self.name}] processed message_id={message.id} parser={parsed_document.parser_name} "
            f"source={source_path.name} chunk_count={len(chunks)}"
        )
        self._log_chunks(chunks)
        ingest_result = await self.rag_service_client.ingest_chunks(
            document_id=self._resolve_document_id(payload, source_path),
            document_name=source_path.name,
            source="worker-service",
            source_description=f"Parsed by {parsed_document.parser_name} from {source_path.name}",
            metadata={
                "message_id": message.id,
                "parser_name": parsed_document.parser_name,
                "source_path": str(source_path),
                "file_type": source_path.suffix.lstrip(".").lower(),
            },
            chunks=[
                {
                    "chunk_id": f"{message.id or source_path.stem}-chunk-{index}",
                    "content": chunk,
                    "metadata": {
                        "chunk_index": index,
                    },
                }
                for index, chunk in enumerate(chunks, start=1)
            ],
        )
        logger.info(
            f"[{self.name}] ingested document_id={self._resolve_document_id(payload, source_path)} "
            f"into rag-service chunk_count={len(chunks)}"
        )
        return {
            "message_id": message.id,
            "source_path": str(source_path),
            "parser_name": parsed_document.parser_name,
            "chunk_count": len(chunks),
            "chunks": chunks,
            "ingest_result": ingest_result,
        }

    def _resolve_source_path(self, payload: dict[str, Any]) -> Path:
        raw_path = payload.get("local_path") or payload.get("location") or payload.get("filename")
        if not raw_path or not isinstance(raw_path, str):
            raise ValueError("Payload must include one of: local_path, location, filename")

        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = ROOT_PATH / candidate

        if not candidate.exists():
            raise FileNotFoundError(f"Local file not found: {candidate}")

        return candidate

    def _log_chunks(self, chunks: list[str]) -> None:
        if not chunks:
            logger.warning(f"[{self.name}] no chunks produced")
            return

        for index, chunk in enumerate(chunks, start=1):
            logger.info(f"[{self.name}] chunk {index}/{len(chunks)}:\n{chunk}")

    @staticmethod
    def _resolve_document_id(payload: dict[str, Any], source_path: Path) -> str:
        candidate = payload.get("document_id") or payload.get("file_id") or source_path.stem
        return str(candidate)
