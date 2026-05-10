from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MinioObjectEntity:
    bucket: str
    object_key: str
    source_url: str
    content_type: str | None = None


@dataclass(slots=True)
class ObjectMetadata:
    size: int
    content_type: str | None = None
    last_modified: datetime | None = None
    etag: str | None = None
