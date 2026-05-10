import re
import unicodedata
from datetime import datetime, timezone

from app.agents.base import AgentWorkflowState
from app.entities.chat import CitationEntity, ReportArtifactEntity
from app.services.report_pdf import convert_markdown_to_pdf_bytes
from app.services.storage import upload_bytes_to_minio


class ReportExportService:
    REPORT_LABEL = "Xem báo cáo PDF"

    def _clean_title(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", (value or "").strip())
        return cleaned.strip(" -") or "Bao cao tong hop"

    def _build_report_title(self, state: AgentWorkflowState) -> str:
        return self._clean_title(state.report_title_hint or state.question)

    def _slugify_file_name(self, title: str) -> str:
        ascii_title = unicodedata.normalize(
            "NFKD",
            title.lower().replace("đ", "d"),
        )
        ascii_title = "".join(char for char in ascii_title if not unicodedata.combining(char))
        ascii_title = ascii_title.encode("ascii", "ignore").decode("ascii")
        ascii_title = re.sub(r"[^a-z0-9._-]+", "-", ascii_title)
        ascii_title = re.sub(r"-{2,}", "-", ascii_title).strip("-._")
        return ascii_title or "bao-cao"

    def _build_reference_lines(self, citations: list[CitationEntity]) -> list[str]:
        if not citations:
            return []

        seen: set[tuple[str, str]] = set()
        lines = ["## Tài liệu tham chiếu", ""]
        for citation in citations:
            key = (citation.file_name, citation.source_url)
            if key in seen:
                continue
            seen.add(key)
            source_url = (citation.source_url or "").strip()
            if source_url.startswith("http://") or source_url.startswith("https://"):
                lines.append(f"- [{citation.file_name}]({source_url})")
            else:
                lines.append(f"- {citation.file_name}")
        return lines

    def build_report_markdown(self, state: AgentWorkflowState) -> str:
        title = self._build_report_title(state)
        body = (state.answer or "").strip()
        if not body:
            return ""

        if re.match(r"^\s*#\s+", body):
            base_markdown = body
        else:
            base_markdown = f"# {title}\n\n{body}"

        reference_lines = self._build_reference_lines(state.citations)
        if reference_lines:
            base_markdown = base_markdown.rstrip() + "\n\n" + "\n".join(reference_lines)

        return base_markdown.strip()

    def export_pdf_report(self, state: AgentWorkflowState) -> ReportArtifactEntity | None:
        markdown_report = self.build_report_markdown(state)
        if not markdown_report:
            return None

        pdf_bytes = convert_markdown_to_pdf_bytes(markdown_report)
        report_title = self._build_report_title(state)
        file_stem = self._slugify_file_name(report_title)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        file_name = f"{file_stem or 'bao-cao'}-{timestamp}.pdf"

        if state.organization_id:
            object_key = (
                f"reports/organizations/{state.organization_id}/sessions/{state.session_id}/{file_name}"
            )
        else:
            object_key = f"reports/personal/{state.user_id}/sessions/{state.session_id}/{file_name}"

        stored_object = upload_bytes_to_minio(
            object_key=object_key,
            content=pdf_bytes,
            content_type="application/pdf",
        )
        return ReportArtifactEntity(
            kind="pdf",
            label=self.REPORT_LABEL,
            file_name=file_name,
            bucket=stored_object.bucket,
            object_key=stored_object.object_key,
            source_url=stored_object.source_url,
            content_type="application/pdf",
        )
