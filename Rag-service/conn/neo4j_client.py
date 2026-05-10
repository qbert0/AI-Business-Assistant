from __future__ import annotations

from typing import Any, Optional

from neo4j import Driver, GraphDatabase

from utils.constants import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME
from utils.logs import logger


class Neo4jClient:
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.uri = uri or NEO4J_URI
        self.username = username or NEO4J_USERNAME
        self.password = password or NEO4J_PASSWORD
        self.driver: Optional[Driver] = None

    def connect(self) -> None:
        if self.driver is not None:
            return

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as exc:
            logger.error(f"Failed to connect to Neo4j: {exc}")
            raise ValueError(f"Failed to connect to Neo4j: {exc}") from exc

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()
            self.driver = None

    def health(self) -> bool:
        try:
            self.connect()
            records = self.run_read_query(
                "CALL dbms.components() YIELD name, versions RETURN name, versions LIMIT 1"
            )
            return bool(records)
        except Exception as exc:
            logger.error(f"Neo4j health check failed: {exc}")
            return False

    def run_read_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        driver = self._require_driver()
        try:
            with driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as exc:
            logger.error(f"Neo4j read query failed: {exc}")
            raise ValueError(f"Neo4j read query failed: {exc}") from exc

    def run_write_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        driver = self._require_driver()
        try:
            with driver.session() as session:
                result = session.run(query, parameters or {})
                summary = result.consume()
                return [
                    {
                        "query_type": summary.query_type,
                        "counters": summary.counters,
                    }
                ]
        except Exception as exc:
            logger.error(f"Neo4j write query failed: {exc}")
            raise ValueError(f"Neo4j write query failed: {exc}") from exc

    def _require_driver(self) -> Driver:
        self.connect()
        if self.driver is None:
            raise ValueError("Neo4j driver is not initialized")
        return self.driver
