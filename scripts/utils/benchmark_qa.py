from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.utils.http_client import post_json


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    page_start: int | None = None
    page_end: int | None = None


@dataclass
class RasRound:
    index: int
    queries: list[str]
    hits: list[SearchHit]
    sufficient: bool = False
    missing_knowledge: list[str] = field(default_factory=list)
    follow_up_queries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BenchmarkQuestion:
    index: int
    question: str
    ground_truth: str


def create_query_embedding(
    text: str,
    *,
    model_service_url: str,
    organization_id: str,
    model_id: str | None,
    use_case: str,
    dimensions: int | None,
    timeout: float,
    retries: int,
) -> list[float]:
    result = post_json(
        model_service_url,
        "/api/v1/embeddings",
        {
            "organization_id": organization_id,
            "model_id": model_id,
            "use_case": use_case,
            "input": [text],
            "dimensions": dimensions,
            "metadata": {"source": "benchmark-qa", "kind": "query"},
        },
        timeout=timeout,
        retries=retries,
    )
    data = result.get("data", [])
    if not data:
        raise RuntimeError("Model service did not return query embedding.")
    return data[0]["embedding"]


def search_elasticsearch(
    query_vector: list[float],
    *,
    url: str,
    username: str | None,
    password: str | None,
    verify_certs: bool,
    index_name: str,
    top_k: int,
    num_candidates: int,
) -> list[SearchHit]:
    try:
        from elasticsearch import Elasticsearch  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing elasticsearch. Install with: pip install -r scripts/requirements.txt") from exc

    client_kwargs: dict[str, Any] = {
        "hosts": [url],
        "verify_certs": verify_certs,
        "request_timeout": 120,
    }
    if username and password:
        client_kwargs["basic_auth"] = (username, password)
    client = Elasticsearch(**client_kwargs)
    response = client.search(
        index=index_name,
        size=top_k,
        knn={
            "field": "embedding",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": max(num_candidates, top_k),
        },
        _source=[
            "chunk_id",
            "document_id",
            "document_name",
            "content",
            "page_start",
            "page_end",
        ],
    )
    hits: list[SearchHit] = []
    for item in response.get("hits", {}).get("hits", []):
        source = item.get("_source", {})
        hits.append(
            SearchHit(
                chunk_id=str(source.get("chunk_id") or item.get("_id")),
                document_id=str(source.get("document_id") or ""),
                document_name=str(source.get("document_name") or ""),
                content=str(source.get("content") or ""),
                score=float(item.get("_score") or 0.0),
                page_start=_optional_int(source.get("page_start")),
                page_end=_optional_int(source.get("page_end")),
            )
        )
    return hits


def call_llm(
    prompt: str,
    *,
    model_service_url: str,
    organization_id: str,
    model_id: str | None,
    use_case: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
    metadata: dict[str, Any] | None = None,
) -> str:
    result = post_json(
        model_service_url,
        "/api/v1/inferences",
        {
            "organization_id": organization_id,
            "model_id": model_id,
            "use_case": use_case,
            "question": prompt,
            "history": [],
            "external_contexts": [],
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "metadata": metadata or {},
        },
        timeout=timeout,
        retries=retries,
    )
    response = result.get("response") or {}
    text = response.get("response_text") or result.get("response_text") or result.get("text")
    if not text:
        raise RuntimeError("Model service inference did not return response text.")
    return str(text)


def answer_with_rag(
    question: str,
    *,
    model_service_url: str,
    organization_id: str,
    embedding_model_id: str | None,
    embedding_use_case: str,
    embedding_dimensions: int | None,
    llm_model_id: str | None,
    llm_use_case: str,
    elasticsearch_url: str,
    elasticsearch_username: str | None,
    elasticsearch_password: str | None,
    elasticsearch_verify_certs: bool,
    index_name: str,
    top_k: int,
    num_candidates: int,
    answer_max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    vector = create_query_embedding(
        question,
        model_service_url=model_service_url,
        organization_id=organization_id,
        model_id=embedding_model_id,
        use_case=embedding_use_case,
        dimensions=embedding_dimensions,
        timeout=timeout,
        retries=retries,
    )
    hits = search_elasticsearch(
        vector,
        url=elasticsearch_url,
        username=elasticsearch_username,
        password=elasticsearch_password,
        verify_certs=elasticsearch_verify_certs,
        index_name=index_name,
        top_k=top_k,
        num_candidates=num_candidates,
    )
    answer = call_llm(
        _build_answer_prompt(question, hits),
        model_service_url=model_service_url,
        organization_id=organization_id,
        model_id=llm_model_id,
        use_case=llm_use_case,
        system_prompt=ANSWER_SYSTEM_PROMPT,
        max_tokens=answer_max_tokens,
        temperature=temperature,
        timeout=timeout,
        retries=retries,
        metadata={"source": "benchmark-qa", "strategy": "rag"},
    )
    return {
        "strategy": "rag",
        "question": question,
        "answer": answer,
        "evidence": [_hit_to_dict(hit) for hit in hits],
        "rounds": [],
    }


def run_rag_benchmark(
    questions: list[BenchmarkQuestion],
    *,
    model_service_url: str,
    organization_id: str,
    embedding_model_id: str | None,
    embedding_use_case: str,
    embedding_dimensions: int | None,
    llm_model_id: str | None,
    llm_use_case: str,
    elasticsearch_url: str,
    elasticsearch_username: str | None,
    elasticsearch_password: str | None,
    elasticsearch_verify_certs: bool,
    index_name: str,
    top_k: int,
    num_candidates: int,
    answer_max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in questions:
        print(f"benchmark rag question {item.index}/{len(questions)}")
        try:
            result = answer_with_rag(
                item.question,
                model_service_url=model_service_url,
                organization_id=organization_id,
                embedding_model_id=embedding_model_id,
                embedding_use_case=embedding_use_case,
                embedding_dimensions=embedding_dimensions,
                llm_model_id=llm_model_id,
                llm_use_case=llm_use_case,
                elasticsearch_url=elasticsearch_url,
                elasticsearch_username=elasticsearch_username,
                elasticsearch_password=elasticsearch_password,
                elasticsearch_verify_certs=elasticsearch_verify_certs,
                index_name=index_name,
                top_k=top_k,
                num_candidates=num_candidates,
                answer_max_tokens=answer_max_tokens,
                temperature=temperature,
                timeout=timeout,
                retries=retries,
            )
            context = _serialize_context(result.get("evidence", []))
            answer = str(result.get("answer") or "")
        except Exception as exc:  # noqa: BLE001
            context = ""
            answer = f"ERROR: {exc}"
        rows.append(
            {
                "question": item.question,
                "ground_truth": item.ground_truth,
                "context": context,
                "answer": answer,
            }
        )
    return rows


def run_ras_benchmark(
    questions: list[BenchmarkQuestion],
    *,
    model_service_url: str,
    organization_id: str,
    embedding_model_id: str | None,
    embedding_use_case: str,
    embedding_dimensions: int | None,
    llm_model_id: str | None,
    llm_use_case: str,
    elasticsearch_url: str,
    elasticsearch_username: str | None,
    elasticsearch_password: str | None,
    elasticsearch_verify_certs: bool,
    index_name: str,
    top_k: int,
    num_candidates: int,
    max_rounds: int,
    max_follow_up_queries: int,
    analysis_max_tokens: int,
    answer_max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    query_graph_namespace: str,
    cleanup_query_graph: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in questions:
        print(f"benchmark ras question {item.index}/{len(questions)}")
        try:
            result = answer_with_ras(
                item.question,
                model_service_url=model_service_url,
                organization_id=organization_id,
                embedding_model_id=embedding_model_id,
                embedding_use_case=embedding_use_case,
                embedding_dimensions=embedding_dimensions,
                llm_model_id=llm_model_id,
                llm_use_case=llm_use_case,
                elasticsearch_url=elasticsearch_url,
                elasticsearch_username=elasticsearch_username,
                elasticsearch_password=elasticsearch_password,
                elasticsearch_verify_certs=elasticsearch_verify_certs,
                index_name=index_name,
                top_k=top_k,
                num_candidates=num_candidates,
                max_rounds=max_rounds,
                max_follow_up_queries=max_follow_up_queries,
                analysis_max_tokens=analysis_max_tokens,
                answer_max_tokens=answer_max_tokens,
                temperature=temperature,
                timeout=timeout,
                retries=retries,
                neo4j_uri=neo4j_uri,
                neo4j_username=neo4j_username,
                neo4j_password=neo4j_password,
                query_graph_namespace=query_graph_namespace,
                cleanup_query_graph=cleanup_query_graph,
            )
            context = _serialize_context(result.get("evidence", []))
            answer = str(result.get("answer") or "")
            rounds = json.dumps(result.get("rounds", []), ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            context = ""
            answer = f"ERROR: {exc}"
            rounds = "[]"
        rows.append(
            {
                "question": item.question,
                "ground_truth": item.ground_truth,
                "context": context,
                "answer": answer,
                "rounds": rounds,
            }
        )
    return rows


def load_benchmark_questions(path: str | Path, limit: int | None = None) -> list[BenchmarkQuestion]:
    try:
        from openpyxl import load_workbook  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing openpyxl. Install with: pip install -r scripts/requirements.txt") from exc

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [_normalize_header(value) for value in rows[0]]
    question_index = _find_column(headers, {"question", "questions", "cau hoi", "cau_hoi", "câu hỏi"})
    ground_truth_index = _find_column(
        headers,
        {"ground_truth", "ground truth", "groundtruth", "answer", "expected_answer", "dap an", "dap_an", "đáp án"},
    )
    data_rows = rows[1:]

    if question_index is None:
        question_index = 0
    if ground_truth_index is None:
        ground_truth_index = 1 if len(rows[0]) > 1 else 0

    questions: list[BenchmarkQuestion] = []
    for index, row in enumerate(data_rows, start=1):
        question = _cell_to_text(row[question_index] if question_index < len(row) else "")
        if not question:
            continue
        ground_truth = _cell_to_text(row[ground_truth_index] if ground_truth_index < len(row) else "")
        questions.append(BenchmarkQuestion(index=len(questions) + 1, question=question, ground_truth=ground_truth))
        if limit is not None and len(questions) >= limit:
            break
    workbook.close()
    return questions


def write_benchmark_results(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".jsonl":
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"benchmark results written: {path}")
        return
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"benchmark results written: {path}")
        return

    try:
        from openpyxl import Workbook  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing openpyxl. Install with: pip install -r scripts/requirements.txt") from exc

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "rag_results"
    columns = ["question", "ground_truth", "context", "answer"]
    if any("rounds" in row for row in rows):
        columns.append("rounds")
    sheet.append(columns)
    for row in rows:
        sheet.append([row.get(column, "") for column in columns])
    workbook.save(path)
    print(f"benchmark results written: {path}")


def answer_with_ras(
    question: str,
    *,
    model_service_url: str,
    organization_id: str,
    embedding_model_id: str | None,
    embedding_use_case: str,
    embedding_dimensions: int | None,
    llm_model_id: str | None,
    llm_use_case: str,
    elasticsearch_url: str,
    elasticsearch_username: str | None,
    elasticsearch_password: str | None,
    elasticsearch_verify_certs: bool,
    index_name: str,
    top_k: int,
    num_candidates: int,
    max_rounds: int,
    max_follow_up_queries: int,
    analysis_max_tokens: int,
    answer_max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    query_graph_namespace: str,
    cleanup_query_graph: bool,
) -> dict[str, Any]:
    query_id = f"{query_graph_namespace}-{uuid.uuid4().hex[:12]}"
    all_hits: dict[str, SearchHit] = {}
    rounds: list[RasRound] = []
    queries = [question]

    create_query_graph(
        uri=neo4j_uri,
        username=neo4j_username,
        password=neo4j_password,
        group_id=query_id,
        question=question,
    )

    try:
        for round_index in range(1, max_rounds + 1):
            round_hits: dict[str, SearchHit] = {}
            for query in queries:
                vector = create_query_embedding(
                    query,
                    model_service_url=model_service_url,
                    organization_id=organization_id,
                    model_id=embedding_model_id,
                    use_case=embedding_use_case,
                    dimensions=embedding_dimensions,
                    timeout=timeout,
                    retries=retries,
                )
                for hit in search_elasticsearch(
                    vector,
                    url=elasticsearch_url,
                    username=elasticsearch_username,
                    password=elasticsearch_password,
                    verify_certs=elasticsearch_verify_certs,
                    index_name=index_name,
                    top_k=top_k,
                    num_candidates=num_candidates,
                ):
                    round_hits.setdefault(hit.chunk_id, hit)
                    all_hits.setdefault(hit.chunk_id, hit)

            analysis = analyze_knowledge_gap(
                question,
                list(all_hits.values()),
                model_service_url=model_service_url,
                organization_id=organization_id,
                model_id=llm_model_id,
                use_case=llm_use_case,
                max_tokens=analysis_max_tokens,
                temperature=temperature,
                timeout=timeout,
                retries=retries,
            )
            follow_up_queries = [
                query.strip()
                for query in analysis.get("follow_up_queries", [])
                if isinstance(query, str) and query.strip()
            ][:max_follow_up_queries]
            missing_knowledge = [
                item.strip()
                for item in analysis.get("missing_knowledge", [])
                if isinstance(item, str) and item.strip()
            ]
            current_round = RasRound(
                index=round_index,
                queries=queries,
                hits=list(round_hits.values()),
                sufficient=bool(analysis.get("sufficient")),
                missing_knowledge=missing_knowledge,
                follow_up_queries=follow_up_queries,
            )
            rounds.append(current_round)
            upsert_query_round(
                uri=neo4j_uri,
                username=neo4j_username,
                password=neo4j_password,
                group_id=query_id,
                round_data=current_round,
            )
            print(
                f"ras round {round_index}: queries={len(queries)} "
                f"new_hits={len(round_hits)} total_hits={len(all_hits)} "
                f"sufficient={current_round.sufficient} followups={len(follow_up_queries)}"
            )
            if current_round.sufficient or not follow_up_queries:
                break
            queries = follow_up_queries

        answer = call_llm(
            _build_answer_prompt(question, list(all_hits.values())),
            model_service_url=model_service_url,
            organization_id=organization_id,
            model_id=llm_model_id,
            use_case=llm_use_case,
            system_prompt=ANSWER_SYSTEM_PROMPT,
            max_tokens=answer_max_tokens,
            temperature=temperature,
            timeout=timeout,
            retries=retries,
            metadata={"source": "benchmark-qa", "strategy": "ras", "query_graph_id": query_id},
        )
        return {
            "strategy": "ras",
            "question": question,
            "answer": answer,
            "query_graph_id": query_id,
            "evidence": [_hit_to_dict(hit) for hit in all_hits.values()],
            "rounds": [_round_to_dict(item) for item in rounds],
        }
    finally:
        if cleanup_query_graph:
            purge_query_graph(
                uri=neo4j_uri,
                username=neo4j_username,
                password=neo4j_password,
                group_id=query_id,
            )


def analyze_knowledge_gap(
    question: str,
    hits: list[SearchHit],
    *,
    model_service_url: str,
    organization_id: str,
    model_id: str | None,
    use_case: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    text = call_llm(
        _build_gap_prompt(question, hits),
        model_service_url=model_service_url,
        organization_id=organization_id,
        model_id=model_id,
        use_case=use_case,
        system_prompt=GAP_SYSTEM_PROMPT,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        retries=retries,
        metadata={"source": "benchmark-qa", "task": "knowledge-gap-analysis"},
    )
    parsed = _parse_json_object(text)
    if not isinstance(parsed, dict):
        return {"sufficient": False, "missing_knowledge": [], "follow_up_queries": []}
    return parsed


def create_query_graph(
    *,
    uri: str,
    username: str,
    password: str,
    group_id: str,
    question: str,
) -> None:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing neo4j. Install with: pip install -r scripts/requirements.txt") from exc

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        session.run(
            """
            MERGE (q:BenchmarkQuery {id: $group_id})
            SET q.group_id = $group_id,
                q.question = $question,
                q.created_at = datetime()
            """,
            group_id=group_id,
            question=question,
        )
    driver.close()


def upsert_query_round(
    *,
    uri: str,
    username: str,
    password: str,
    group_id: str,
    round_data: RasRound,
) -> None:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing neo4j. Install with: pip install -r scripts/requirements.txt") from exc

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        session.run(
            """
            MATCH (q:BenchmarkQuery {id: $group_id})
            MERGE (r:BenchmarkQueryRound {id: $round_id})
            SET r.group_id = $group_id,
                r.index = $index,
                r.queries = $queries,
                r.sufficient = $sufficient,
                r.created_at = datetime()
            MERGE (q)-[:HAS_ROUND]->(r)
            """,
            group_id=group_id,
            round_id=f"{group_id}-round-{round_data.index}",
            index=round_data.index,
            queries=round_data.queries,
            sufficient=round_data.sufficient,
        )
        for need_index, need in enumerate(round_data.missing_knowledge):
            session.run(
                """
                MATCH (r:BenchmarkQueryRound {id: $round_id})
                MERGE (n:BenchmarkQueryNeed {id: $need_id})
                SET n.group_id = $group_id,
                    n.text = $text,
                    n.status = 'missing'
                MERGE (r)-[:NEEDS]->(n)
                """,
                group_id=group_id,
                round_id=f"{group_id}-round-{round_data.index}",
                need_id=f"{group_id}-round-{round_data.index}-need-{need_index}",
                text=need,
            )
        for hit in round_data.hits:
            session.run(
                """
                MATCH (r:BenchmarkQueryRound {id: $round_id})
                MERGE (e:BenchmarkQueryEvidence {id: $chunk_id})
                SET e.group_id = $group_id,
                    e.chunk_id = $chunk_id,
                    e.document_id = $document_id,
                    e.document_name = $document_name,
                    e.score = $score,
                    e.content = $content
                MERGE (r)-[:FOUND]->(e)
                """,
                group_id=group_id,
                round_id=f"{group_id}-round-{round_data.index}",
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                document_name=hit.document_name,
                score=hit.score,
                content=hit.content[:1200],
            )
    driver.close()


def purge_query_graph(*, uri: str, username: str, password: str, group_id: str) -> int:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing neo4j. Install with: pip install -r scripts/requirements.txt") from exc

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n)
            WHERE n.group_id = $group_id
            WITH collect(n) AS nodes
            FOREACH (n IN nodes | DETACH DELETE n)
            RETURN size(nodes) AS deleted_nodes
            """,
            group_id=group_id,
        )
        record = result.single()
        deleted = int(record["deleted_nodes"] or 0) if record else 0
    driver.close()
    print(f"query graph cleaned: group_id={group_id} deleted_nodes={deleted}")
    return deleted


def _build_answer_prompt(question: str, hits: list[SearchHit]) -> str:
    evidence = "\n\n".join(_format_hit(index, hit) for index, hit in enumerate(hits, start=1))
    return (
        f"Câu hỏi:\n{question}\n\n"
        f"Bằng chứng đã truy xuất từ Elasticsearch:\n{evidence or 'Không có bằng chứng.'}\n\n"
        "Hãy trả lời bằng tiếng Việt. Nếu bằng chứng không đủ, nói rõ phần còn thiếu. "
        "Khi có thể, nhắc tên tài liệu/trang nguồn liên quan."
    )


def _build_gap_prompt(question: str, hits: list[SearchHit]) -> str:
    evidence = "\n\n".join(_format_hit(index, hit, max_chars=900) for index, hit in enumerate(hits[:20], start=1))
    return (
        f"Câu hỏi gốc:\n{question}\n\n"
        f"Bằng chứng hiện có:\n{evidence or 'Không có bằng chứng.'}\n\n"
        "Hãy đánh giá bằng chứng đã đủ để trả lời chưa. "
        "Nếu thiếu, chỉ ra knowledge còn thiếu và sinh truy vấn tìm kiếm tiếp theo trên Elasticsearch."
    )


def _format_hit(index: int, hit: SearchHit, max_chars: int = 1600) -> str:
    page = ""
    if hit.page_start is not None:
        page = f", pages={hit.page_start}-{hit.page_end or hit.page_start}"
    return (
        f"[{index}] chunk_id={hit.chunk_id}, document={hit.document_name}{page}, score={hit.score:.4f}\n"
        f"{hit.content[:max_chars]}"
    )


def _parse_json_object(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    candidates.append(text)
    for candidate in candidates:
        try:
            value = json.loads(candidate)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def _hit_to_dict(hit: SearchHit) -> dict[str, Any]:
    return {
        "chunk_id": hit.chunk_id,
        "document_id": hit.document_id,
        "document_name": hit.document_name,
        "score": hit.score,
        "page_start": hit.page_start,
        "page_end": hit.page_end,
        "content": hit.content,
    }


def _round_to_dict(round_data: RasRound) -> dict[str, Any]:
    return {
        "index": round_data.index,
        "queries": round_data.queries,
        "hit_count": len(round_data.hits),
        "sufficient": round_data.sufficient,
        "missing_knowledge": round_data.missing_knowledge,
        "follow_up_queries": round_data.follow_up_queries,
    }


def _serialize_context(evidence: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        (
            f"[{index}] document={item.get('document_name', '')} "
            f"chunk_id={item.get('chunk_id', '')} "
            f"pages={item.get('page_start', '')}-{item.get('page_end', '')} "
            f"score={item.get('score', '')}\n"
            f"{item.get('content', '')}"
        )
        for index, item in enumerate(evidence, start=1)
    )


def _normalize_header(value: Any) -> str:
    text = _cell_to_text(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _find_column(headers: list[str], candidates: set[str]) -> int | None:
    normalized_candidates = {_normalize_header(candidate) for candidate in candidates}
    for index, header in enumerate(headers):
        if header in normalized_candidates:
            return index
    for index, header in enumerate(headers):
        if any(candidate in header for candidate in normalized_candidates):
            return index
    return None


def _cell_to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


ANSWER_SYSTEM_PROMPT = (
    "Bạn là hệ thống trả lời benchmark RAG. Chỉ sử dụng bằng chứng được cung cấp. "
    "Không bịa thông tin ngoài evidence. Trả lời ngắn gọn, có căn cứ."
)

GAP_SYSTEM_PROMPT = (
    "Bạn là bộ điều phối retrieval cho RAS (Restructured Augmented Search). "
    "Trả về DUY NHẤT JSON hợp lệ theo schema: "
    '{"sufficient": boolean, "missing_knowledge": string[], "follow_up_queries": string[]}. '
    "follow_up_queries phải là truy vấn ngắn, trực tiếp, dùng được cho vector search. "
    "Nếu bằng chứng đủ, sufficient=true và follow_up_queries=[]."
)
