#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


ENV = load_env_file(ENV_PATH)


def default_server_url() -> str:
    return f"http://127.0.0.1:{ENV.get('SERVER_SERVICE_PORT', '8000')}"


def default_model_url() -> str:
    return f"http://127.0.0.1:{ENV.get('MODEL_SERVICE_PORT', '8888')}"


def http_json(method: str, url: str, payload: dict | None = None) -> dict | list:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            content = response.read().decode("utf-8")
            return json.loads(content)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def build_chat_url(server_url: str, personal: bool, organization_id: str | None) -> str:
    if personal:
        return f"{server_url}/chat/personal/ask"
    if not organization_id:
        raise ValueError("--organization-id is required unless --personal is used.")
    return f"{server_url}/organizations/{organization_id}/chat/ask"


def call_chat_api(
    *,
    server_url: str,
    personal: bool,
    organization_id: str | None,
    user_id: str,
    question: str,
) -> dict:
    url = build_chat_url(server_url, personal, organization_id)
    payload = {
        "user_id": user_id,
        "question": question,
    }
    return http_json("POST", url, payload)


def fetch_model_inferences(model_url: str, conversation_id: str) -> list[dict]:
    query = urllib.parse.urlencode({"conversation_id": conversation_id, "limit": 20})
    url = f"{model_url}/api/v1/inferences?{query}"
    data = http_json("GET", url)
    if not isinstance(data, list):
        return []
    return data


def sql_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")


def query_agent_rows_from_model_db(
    *,
    container_name: str,
    database_name: str,
    database_user: str,
    database_password: str,
    conversation_id: str,
) -> list[dict]:
    escaped_conversation_id = sql_escape(conversation_id)
    sql = f"""
SELECT JSON_OBJECT(
  'request_id', r.id,
  'agent', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(r.request_payload_json, '$.metadata.agent')), ''),
  'phase', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(r.request_payload_json, '$.metadata.phase')), ''),
  'status', r.status,
  'context_count', COALESCE(JSON_LENGTH(JSON_EXTRACT(r.request_payload_json, '$.external_contexts')), 0),
  'finish_reason', COALESCE(resp.finish_reason, ''),
  'prompt_tokens', COALESCE(resp.prompt_tokens, 0),
  'completion_tokens', COALESCE(resp.completion_tokens, 0),
  'total_tokens', COALESCE(resp.total_tokens, 0),
  'response_text', COALESCE(resp.response_text, ''),
  'reasoning', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(resp.raw_response_json, '$.choices[0].message.reasoning')), '')
)
FROM inference_requests r
LEFT JOIN inference_responses resp ON resp.request_id = r.id
WHERE r.conversation_id = '{escaped_conversation_id}'
ORDER BY r.started_at ASC;
""".strip()

    command = [
        "docker",
        "exec",
        container_name,
        "mariadb",
        f"-u{database_user}",
        f"-p{database_password}",
        database_name,
        "--batch",
        "--raw",
        "--skip-column-names",
        "-e",
        sql,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Could not query model DB from container {container_name}: {stderr}")

    rows: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def preview(text: str, limit: int = 280) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def print_chat_summary(response: dict) -> None:
    session = response.get("session") or {}
    print("=== Chat Response ===")
    print(f"session_id : {session.get('id', '')}")
    print(f"answer     : {response.get('answer', '')}")
    citations = response.get("citations") or []
    print(f"citations  : {len(citations)}")
    for citation in citations:
        print(f"  - {citation.get('file_name', '')} | {citation.get('source_url', '')}")
    print()


def print_agent_trace(rows: list[dict]) -> None:
    print("=== Agent Trace ===")
    if not rows:
        print("No agent rows found.")
        return

    for index, row in enumerate(rows, start=1):
        agent = row.get("agent") or f"step-{index}"
        phase = row.get("phase") or "-"
        finish_reason = row.get("finish_reason") or "-"
        print(f"[{index}] agent={agent} phase={phase} status={row.get('status', '')}")
        print(
            f"    tokens: prompt={row.get('prompt_tokens', 0)} "
            f"completion={row.get('completion_tokens', 0)} total={row.get('total_tokens', 0)} "
            f"finish={finish_reason} contexts={row.get('context_count', 0)}"
        )

        response_text = row.get("response_text") or ""
        if response_text.strip():
            print(f"    response : {preview(response_text)}")
        else:
            print("    response : <empty>")

        reasoning = row.get("reasoning") or ""
        if reasoning.strip():
            print(f"    reasoning: {preview(reasoning)}")
        print()


def print_http_fallback_trace(items: list[dict]) -> None:
    print("=== Agent Trace (HTTP Fallback) ===")
    if not items:
        print("No inference records found.")
        return

    guessed_agents = ["planner", "answerer", "verifier"]
    for index, item in enumerate(items, start=1):
        request = item.get("request") or {}
        response = item.get("response") or {}
        guessed_agent = guessed_agents[index - 1] if index <= len(guessed_agents) else f"step-{index}"
        print(f"[{index}] agent={guessed_agent} request_id={request.get('id', '')} status={request.get('status', '')}")
        print(
            f"    tokens: prompt={response.get('prompt_tokens', 0)} "
            f"completion={response.get('completion_tokens', 0)} total={response.get('total_tokens', 0)} "
            f"finish={response.get('finish_reason', '-')}"
        )
        print(f"    response : {preview(response.get('response_text', ''))}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call chat API and print per-agent responses for debugging the multi-agent flow.",
    )
    parser.add_argument("--question", required=True, help="The user question to send to chat.")
    parser.add_argument("--user-id", required=True, help="User ID for the chat request.")
    parser.add_argument("--organization-id", help="Organization ID for organization chat.")
    parser.add_argument("--personal", action="store_true", help="Use personal chat endpoint instead of organization chat.")
    parser.add_argument("--server-url", default=default_server_url(), help="Server_service base URL.")
    parser.add_argument("--model-url", default=default_model_url(), help="Model_service base URL.")
    parser.add_argument(
        "--model-db-container",
        default=ENV.get("MODEL_MARIADB_CONTAINER_NAME", "model_mariadb_app"),
        help="Docker container name for the model MariaDB instance.",
    )
    parser.add_argument(
        "--model-db-name",
        default=ENV.get("MODEL_MARIADB_DATABASE", "model_service"),
        help="Database name inside the model MariaDB instance.",
    )
    parser.add_argument(
        "--model-db-user",
        default=ENV.get("MODEL_MARIADB_USER", "model_service"),
        help="Database user for the model MariaDB instance.",
    )
    parser.add_argument(
        "--model-db-password",
        default=ENV.get("MODEL_MARIADB_PASSWORD", "model_service123"),
        help="Database password for the model MariaDB instance.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.personal and not args.organization_id:
        print("error: --organization-id is required unless --personal is set", file=sys.stderr)
        return 2

    response = call_chat_api(
        server_url=args.server_url.rstrip("/"),
        personal=args.personal,
        organization_id=args.organization_id,
        user_id=args.user_id,
        question=args.question,
    )
    if not isinstance(response, dict):
        raise RuntimeError("Unexpected chat response shape.")

    print_chat_summary(response)
    session = response.get("session") or {}
    conversation_id = session.get("id")
    if not conversation_id:
        raise RuntimeError("Chat response did not include session.id")

    try:
        rows = query_agent_rows_from_model_db(
            container_name=args.model_db_container,
            database_name=args.model_db_name,
            database_user=args.model_db_user,
            database_password=args.model_db_password,
            conversation_id=conversation_id,
        )
        print_agent_trace(rows)
        return 0
    except Exception as exc:
        print(f"warning: DB trace lookup failed: {exc}", file=sys.stderr)

    fallback_items = fetch_model_inferences(args.model_url.rstrip("/"), conversation_id)
    print_http_fallback_trace(fallback_items)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
