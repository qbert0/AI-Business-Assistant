from pathlib import Path
from typing import Any

from conn.rag_service_client import RagServiceClient
from conn.server_service_client import ServerServiceClient
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
        self.server_service_client = ServerServiceClient()

    async def handle(self, message: Message) -> dict[str, Any]:
        payload = message.payload

        if not isinstance(payload, dict):
            raise ValueError("Message payload must be a dictionary")

        if payload.get("content_url"):
            return await self._handle_server_document(message, payload)

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

    async def _handle_server_document(self, message: Message, payload: dict[str, Any]) -> dict[str, Any]:
        document_id = str(payload["document_id"])
        acting_user_id = str(payload["acting_user_id"])
        file_name = str(payload.get("file_name") or document_id)
        content_url = str(payload["content_url"])
        run_id = str(payload.get("run_id") or message.id or document_id)

        try:
            await self._patch_analysis(
                document_id,
                acting_user_id,
                status="processing",
                stage="parsing",
                message="Worker dang tai va parse tai lieu.",
                analysis={
                    "state": "parsing",
                    "locked": True,
                    "stage": "parsing",
                    "message": "Worker dang tai va parse tai lieu.",
                    "run_id": run_id,
                },
                progress={"parse": 10, "graph": 0},
            )

            if await self.server_service_client.is_cancel_requested(document_id, acting_user_id):
                return await self._cancel_document(document_id, acting_user_id, message.id, "Da dung truoc khi parse.")

            file_bytes = await self.server_service_client.download_file(content_url)
            parser = create_parser(file_name)
            parsed_document = parser.parse_bytes(file_bytes, file_name)
            chunks = chunk_text(
                parsed_document.text,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )

            await self._patch_analysis(
                document_id,
                acting_user_id,
                status="processing",
                stage="chunking",
                message=f"Worker da chunk thanh {len(chunks)} doan.",
                chunk_count=len(chunks),
                analysis={
                    "state": "chunked",
                    "locked": True,
                    "stage": "chunking",
                    "message": f"Worker da chunk thanh {len(chunks)} doan.",
                },
                progress={"parse": 100, "graph": 0},
                metadata={
                    "parser_name": parsed_document.parser_name,
                    "worker_message_id": message.id,
                    "file_type": Path(file_name).suffix.lstrip(".").lower(),
                },
            )

            if await self.server_service_client.is_cancel_requested(document_id, acting_user_id):
                return await self._cancel_document(document_id, acting_user_id, message.id, "Da dung sau khi chunk.")

            await self._patch_analysis(
                document_id,
                acting_user_id,
                status="indexing",
                stage="indexing",
                message="Da gui chunks sang RAG service.",
                analysis={
                    "state": "graphing",
                    "locked": True,
                    "stage": "indexing",
                    "message": "Da gui chunks sang RAG service.",
                },
                progress={"parse": 100, "graph": 10},
            )

            ingest_result = await self.rag_service_client.ingest_chunks(
                document_id=document_id,
                document_name=file_name,
                source="worker-service",
                source_description=f"Parsed by {parsed_document.parser_name} from {file_name}",
                metadata={
                    "message_id": message.id,
                    "parser_name": parsed_document.parser_name,
                    "file_type": Path(file_name).suffix.lstrip(".").lower(),
                    "organization_id": payload.get("organization_id"),
                    "acting_user_id": acting_user_id,
                    "run_id": run_id,
                },
                chunks=[
                    {
                        "chunk_id": f"{document_id}-chunk-{index}",
                        "content": chunk,
                        "metadata": {
                            "chunk_index": index,
                        },
                    }
                    for index, chunk in enumerate(chunks, start=1)
                ],
            )
            logger.info(f"[{self.name}] queued rag ingest document_id={document_id} chunk_count={len(chunks)}")
            return {
                "message_id": message.id,
                "document_id": document_id,
                "parser_name": parsed_document.parser_name,
                "chunk_count": len(chunks),
                "ingest_result": ingest_result,
            }
        except Exception as exc:
            await self._patch_analysis(
                document_id,
                acting_user_id,
                status="failed",
                stage="parsing",
                message=f"Worker xu ly that bai: {exc}",
                analysis={
                    "state": "failed",
                    "locked": False,
                    "stage": "parsing",
                    "message": f"Worker xu ly that bai: {exc}",
                    "error": str(exc),
                },
            )
            raise

    async def _cancel_document(
        self,
        document_id: str,
        acting_user_id: str,
        message_id: str | None,
        message: str,
    ) -> dict[str, Any]:
        await self._patch_analysis(
            document_id,
            acting_user_id,
            status="cancelled",
            stage="cancelled",
            message=message,
            analysis={
                "state": "cancelled",
                "locked": False,
                "stage": "cancelled",
                "message": message,
                "cancel_requested": False,
            },
        )
        return {"message_id": message_id, "document_id": document_id, "cancelled": True}

    async def _patch_analysis(
        self,
        document_id: str,
        acting_user_id: str,
        *,
        status: str,
        stage: str,
        message: str,
        analysis: dict[str, Any],
        progress: dict[str, int] | None = None,
        chunk_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.server_service_client.update_document_status(
            document_id,
            acting_user_id,
            {
                "status": status,
                "stage": stage,
                "message": message,
                "chunk_count": chunk_count,
                "analysis": analysis,
                "progress": progress,
                "metadata": metadata,
            },
        )

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
