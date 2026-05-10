from __future__ import annotations

import time
from typing import Any


def get_redis_ingest_status(
    *,
    host: str,
    port: int,
    db: int,
    password: str | None,
    queue_name: str,
    group_name: str,
) -> dict[str, Any]:
    try:
        import redis  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing redis. Install with: pip install -r scripts/requirements.txt") from exc

    client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
    status: dict[str, Any] = {
        "queue_name": queue_name,
        "group_name": group_name,
        "stream_exists": False,
        "stream_length": 0,
        "groups": [],
        "pending": None,
    }
    if not client.exists(queue_name):
        return status

    status["stream_exists"] = True
    status["stream_length"] = int(client.xlen(queue_name))
    try:
        groups = client.xinfo_groups(queue_name)
        status["groups"] = groups
        for group in groups:
            if group.get("name") == group_name:
                status["pending"] = int(group.get("pending") or 0)
                status["lag"] = group.get("lag")
                status["last_delivered_id"] = group.get("last-delivered-id")
                break
    except Exception as exc:  # noqa: BLE001
        status["error"] = str(exc)
    return status


def get_neo4j_namespace_status(
    *,
    uri: str,
    username: str,
    password: str,
    document_namespace: str,
) -> dict[str, Any]:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing neo4j. Install with: pip install -r scripts/requirements.txt") from exc

    group_prefix = f"document-{document_namespace}-"
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        with driver.session() as session:
            node_record = session.run(
                """
                MATCH (n)
                WHERE n.group_id STARTS WITH $group_prefix
                RETURN count(n) AS node_count,
                       count(DISTINCT n.group_id) AS group_count
                """,
                group_prefix=group_prefix,
            ).single()
            edge_record = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.group_id STARTS WITH $group_prefix
                   OR b.group_id STARTS WITH $group_prefix
                RETURN count(r) AS direct_edge_count
                """,
                group_prefix=group_prefix,
            ).single()
            group_edge_record = session.run(
                """
                MATCH ()-[r]->()
                WHERE r.group_id STARTS WITH $group_prefix
                RETURN count(r) AS group_edge_count
                """,
                group_prefix=group_prefix,
            ).single()
            edge_type_records = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.group_id STARTS WITH $group_prefix
                   OR b.group_id STARTS WITH $group_prefix
                   OR r.group_id STARTS WITH $group_prefix
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
                LIMIT 20
                """,
                group_prefix=group_prefix,
            )
            sample_records = session.run(
                """
                MATCH (n)
                WHERE n.group_id STARTS WITH $group_prefix
                RETURN n.group_id AS group_id, count(n) AS node_count
                ORDER BY group_id
                LIMIT 20
                """,
                group_prefix=group_prefix,
            )
            label_records = session.run(
                """
                MATCH (n)
                WHERE n.group_id STARTS WITH $group_prefix
                UNWIND labels(n) AS label
                RETURN label, count(*) AS count
                ORDER BY count DESC
                """,
                group_prefix=group_prefix,
            )
            direct_edge_count = int(edge_record["direct_edge_count"]) if edge_record else 0
            group_edge_count = int(group_edge_record["group_edge_count"]) if group_edge_record else 0
            return {
                "group_prefix": group_prefix,
                "node_count": int(node_record["node_count"]) if node_record else 0,
                "group_count": int(node_record["group_count"]) if node_record else 0,
                "edge_count": max(direct_edge_count, group_edge_count),
                "direct_edge_count": direct_edge_count,
                "group_edge_count": group_edge_count,
                "label_counts": [dict(record) for record in label_records],
                "edge_types": [dict(record) for record in edge_type_records],
                "groups": [dict(record) for record in sample_records],
            }
    finally:
        driver.close()


def wait_for_graph_idle(
    *,
    redis_options: dict[str, Any],
    neo4j_options: dict[str, Any],
    interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    started = time.monotonic()
    last_status: dict[str, Any] = {}
    while True:
        redis_status = get_redis_ingest_status(**redis_options)
        neo4j_status = get_neo4j_namespace_status(**neo4j_options)
        last_status = {"redis": redis_status, "neo4j": neo4j_status}
        pending = redis_status.get("pending")
        lag = redis_status.get("lag")
        print(
            "graph-status "
            f"stream_length={redis_status.get('stream_length')} "
            f"pending={pending} lag={lag} "
            f"group_prefix={neo4j_status.get('group_prefix')} "
            f"neo4j_groups={neo4j_status.get('group_count')} "
            f"neo4j_nodes={neo4j_status.get('node_count')} "
            f"neo4j_edges={neo4j_status.get('edge_count')} "
            f"direct_edges={neo4j_status.get('direct_edge_count')} "
            f"group_edges={neo4j_status.get('group_edge_count')} "
            f"labels={_format_counts(neo4j_status.get('label_counts'), 'label')} "
            f"edge_types={_format_counts(neo4j_status.get('edge_types'), 'type')}"
        )
        if pending == 0 and (lag in (0, None)):
            return last_status
        if time.monotonic() - started >= timeout_seconds:
            return last_status
        time.sleep(interval_seconds)


def _format_counts(rows: Any, key: str) -> str:
    if not rows:
        return "none"
    parts = []
    for row in rows[:6]:
        name = row.get(key) if isinstance(row, dict) else None
        count = row.get("count") if isinstance(row, dict) else None
        parts.append(f"{name}:{count}")
    return ",".join(parts)
