from __future__ import annotations


def delete_stream(
    *,
    host: str,
    port: int,
    db: int,
    password: str | None,
    queue_name: str,
) -> int:
    try:
        import redis  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing redis. Install with: pip install -r scripts/requirements.txt") from exc

    client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
    deleted = int(client.delete(queue_name))
    print(f"redis stream delete complete: stream={queue_name} deleted={deleted}")
    return deleted
