from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import HTTPException, UploadFile, status

from app import messages
from app.config import MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY, MINIO_SECURE
from app.entities.storage import MinioObjectEntity

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None
    BotoCoreError = ClientError = Exception


def get_minio_client():
    if not MINIO_ENDPOINT:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=messages.MINIO_NOT_CONFIGURED)
    if boto3 is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=messages.MINIO_BOTO3_MISSING)
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        use_ssl=MINIO_SECURE,
    )


def ensure_minio_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=MINIO_BUCKET)


def upload_file_to_minio(org_id: str, file: UploadFile) -> MinioObjectEntity:
    client = get_minio_client()
    ensure_minio_bucket(client)
    safe_name = quote(file.filename or "document", safe="._-")
    object_key = f"organizations/{org_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{safe_name}"
    try:
        file.file.seek(0)
        client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            object_key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Khong upload duoc file len MinIO: {exc}")
    return MinioObjectEntity(
        bucket=MINIO_BUCKET,
        object_key=object_key,
        source_url=f"s3://{MINIO_BUCKET}/{object_key}",
        content_type=file.content_type,
    )


def get_file_from_minio(bucket: str, object_key: str):
    client = get_minio_client()
    try:
        return client.get_object(Bucket=bucket, Key=object_key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{messages.MINIO_DOWNLOAD_FAILED}: {exc}")
