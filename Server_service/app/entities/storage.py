from dataclasses import dataclass


@dataclass(slots=True)
class MinioObjectEntity:
    bucket: str
    object_key: str
    source_url: str
    content_type: str | None = None
