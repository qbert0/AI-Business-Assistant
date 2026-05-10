import json
import re
from typing import Any

from app.entities.chat import ReportArtifactEntity


REPORT_ARTIFACT_FENCE = "report_file"
REPORT_ARTIFACT_PATTERN = re.compile(
    r"\n*```report_file\s*\n(.*?)\n```\s*",
    flags=re.DOTALL,
)


def _artifact_to_payload(artifact: ReportArtifactEntity) -> dict[str, Any]:
    return {
        "kind": artifact.kind,
        "label": artifact.label,
        "file_name": artifact.file_name,
        "bucket": artifact.bucket,
        "object_key": artifact.object_key,
        "source_url": artifact.source_url,
        "content_type": artifact.content_type,
    }


def serialize_report_artifacts(content: str, artifacts: list[ReportArtifactEntity]) -> str:
    if not artifacts:
        return (content or "").strip()

    blocks = [
        f"```{REPORT_ARTIFACT_FENCE}\n{json.dumps(_artifact_to_payload(artifact), ensure_ascii=False)}\n```"
        for artifact in artifacts
    ]
    base_content = (content or "").strip()
    if not base_content:
        return "\n\n".join(blocks)
    return base_content + "\n\n" + "\n\n".join(blocks)


def extract_report_artifacts(content: str) -> tuple[str, list[dict[str, Any]]]:
    raw_content = content or ""
    artifacts: list[dict[str, Any]] = []

    def _collect(match: re.Match[str]) -> str:
        raw_payload = (match.group(1) or "").strip()
        if raw_payload:
            try:
                payload = json.loads(raw_payload)
                if isinstance(payload, dict):
                    artifacts.append(payload)
            except json.JSONDecodeError:
                pass
        return "\n"

    cleaned = REPORT_ARTIFACT_PATTERN.sub(_collect, raw_content)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, artifacts
