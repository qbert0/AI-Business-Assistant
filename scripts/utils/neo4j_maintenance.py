from __future__ import annotations


def purge_graph_namespace(
    *,
    uri: str,
    username: str,
    password: str,
    document_namespace: str,
) -> int:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing neo4j. Install with: pip install -r scripts/requirements.txt") from exc

    group_prefix = f"document-{document_namespace}-"
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n.group_id STARTS WITH $group_prefix
                WITH n
                DETACH DELETE n
                RETURN count(*) AS deleted_nodes
                """,
                group_prefix=group_prefix,
            )
            record = result.single()
            deleted = int(record["deleted_nodes"]) if record else 0
            print(f"neo4j purge complete: group_prefix={group_prefix} deleted_nodes={deleted}")
            return deleted
    finally:
        driver.close()
