# Model Service

`Model_service` is a FastAPI service responsible for model registry management, provider registry management, model selection policies, context building, inference execution, feedback storage, and metrics aggregation for the AI Business Assistant system.

Swagger UI:

```txt
http://localhost:8888/docs
```

## What Model Service Does

Model Service acts as the middle layer between the business application and LLM endpoints that are already served elsewhere.

Its current responsibilities include:

- Managing `providers`: create, update, delete, and search providers.
- Managing `models`: register new models, update them, delete them, and run upstream health checks.
- Managing `policies`: define default model, fallback model, `temperature`, `max_tokens`, and `system_prompt` by `use_case` and `organization_id`.
- Building context for a query before inference.
- Executing inference and storing request/response metadata.
- Storing assembled context and context snapshots for traceability.
- Storing user feedback per request, model, and conversation.
- Aggregating usage, latency, token, and estimated-cost metrics.

## Model Service Architecture

### Overview

Model Service is separated into its own microservice:

- API layer: FastAPI routes.
- Service layer: business logic.
- DB layer: SQLAlchemy models and session management.
- Infrastructure layer: adapters for upstream LLM providers.
- Dedicated MariaDB database for model metadata and runtime records.

### Directory Structure

```txt
Model_service/
  app/
    api/routes/              # FastAPI routes
    core/                    # config, security, serialization helpers
    db/                      # SQLAlchemy models and DB session
    infrastructure/llm/      # adapters for openai_compatible and ollama
    schemas/                 # request/response schemas
    services/                # business logic
    main.py                  # FastAPI app
  Dockerfile
  requirements.txt
  README.md
```

### Main Processing Flow

1. `Server_service` or a client calls `Model_service`.
2. A route receives the request and forwards it to the service layer.
3. The service layer:
   - resolves a model by `model_id` or `policy`
   - builds context
   - calls the `openai_compatible` or `ollama` adapter
   - stores request, response, context snapshot, metrics, and feedback in the database
4. The API returns the result to the caller.

### Core Components

- `Provider`
  Represents a provider endpoint type such as `openai_compatible` or `ollama`.
- `RegisteredModel`
  Represents an actual model registered in the system.
- `ModelPolicy`
  Controls model selection by `use_case` and `organization_id`.
- `InferenceRequest` and `InferenceResponse`
  Store data for each model invocation.
- `ContextSnapshot`
  Stores the context used during an inference run.
- `FeedbackEvent`
  Stores like/dislike feedback.
- `MetricRollup`
  Stores aggregated metrics in time buckets.

### Supported Provider Adapters

- `openai_compatible`
- `ollama`

## Database Model

Main tables currently used by Model Service:

- `model_providers`
- `registered_models`
- `model_policies`
- `inference_requests`
- `inference_responses`
- `context_snapshots`
- `feedback_events`
- `metric_rollups`

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build model_service model_mariadb
```

Or run the entire stack:

```bash
docker compose up --build
```

## API Overview

### System

- `GET /`
- `GET /health`

### Providers

- `GET /api/v1/providers`
- `POST /api/v1/providers`
- `GET /api/v1/providers/{provider_id}`
- `PATCH /api/v1/providers/{provider_id}`
- `DELETE /api/v1/providers/{provider_id}`

### Models

- `GET /api/v1/models`
- `POST /api/v1/models`
- `GET /api/v1/models/{model_id}`
- `PATCH /api/v1/models/{model_id}`
- `DELETE /api/v1/models/{model_id}`
- `POST /api/v1/models/{model_id}/health`

### Policies

- `GET /api/v1/policies`
- `POST /api/v1/policies`
- `GET /api/v1/policies/{policy_id}`
- `PATCH /api/v1/policies/{policy_id}`
- `DELETE /api/v1/policies/{policy_id}`

### Contexts

- `POST /api/v1/contexts/build`
- `GET /api/v1/contexts`
- `GET /api/v1/contexts/{request_id}`

### Inferences

- `POST /api/v1/inferences`
- `GET /api/v1/inferences`
- `GET /api/v1/inferences/{request_id}`

### Feedback

- `POST /api/v1/feedback`
- `GET /api/v1/feedback`

### Metrics

- `GET /api/v1/metrics/summary`

## Recommended End-to-End Test Flow

To test the APIs quickly with linked examples, use this order:

1. Create a `provider`
2. Create a `model`
3. Run a health check on the `model`
4. Create a `policy`
5. Build a `context`
6. Run an `inference`
7. Retrieve the stored `context` by `request_id`
8. Submit `feedback`
9. View `metrics`

In the examples below, values copied from a previous response are represented as:

- `PROVIDER_ID`
- `MODEL_ID`
- `POLICY_ID`
- `REQUEST_ID`

## Detailed API Documentation

### 1. System APIs

#### `GET /`

Purpose:
- Returns general information about the service.

Input:
- None.

Output:
- Service name, version, docs URL, health URL, and capabilities.

Example response:

```json
{
  "name": "AI Business Assistant Model Service",
  "version": "0.1.0",
  "docs_url": "/docs",
  "health_url": "/health",
  "capabilities": [
    "provider-registry",
    "model-registry",
    "policy-management",
    "context-builder",
    "inference-orchestration",
    "feedback-tracking",
    "metrics-rollup"
  ]
}
```

#### `GET /health`

Purpose:
- Checks whether the service is alive.

Input:
- None.

Output:
- `status`, `timestamp`.

Example response:

```json
{
  "status": "ok",
  "timestamp": "2026-04-21T04:30:00.000000Z"
}
```

### 2. Provider APIs

#### `POST /api/v1/providers`

Purpose:
- Creates a new provider.

Input:

```json
{
  "name": "OpenAI Demo",
  "provider_type": "openai_compatible",
  "description": "OpenAI-compatible provider for testing",
  "metadata": {
    "owner": "local-dev"
  },
  "is_active": true
}
```

Output:
- Returns the created provider.

Example response:

```json
{
  "id": "PROVIDER_ID",
  "name": "OpenAI Demo",
  "provider_type": "openai_compatible",
  "description": "OpenAI-compatible provider for testing",
  "metadata": {
    "owner": "local-dev"
  },
  "is_active": true,
  "created_at": "2026-04-21T04:31:00",
  "updated_at": "2026-04-21T04:31:00"
}
```

#### `GET /api/v1/providers`

Purpose:
- Returns the provider list.
- Supports search by `name`.

Query params:
- `name`: search by provider name.

Example:

```bash
curl "http://localhost:8888/api/v1/providers?name=OpenAI"
```

Example response:

```json
[
  {
    "id": "PROVIDER_ID",
    "name": "OpenAI Demo",
    "provider_type": "openai_compatible",
    "description": "OpenAI-compatible provider for testing",
    "metadata": {
      "owner": "local-dev"
    },
    "is_active": true,
    "created_at": "2026-04-21T04:31:00",
    "updated_at": "2026-04-21T04:31:00"
  }
]
```

#### `GET /api/v1/providers/{provider_id}`

Purpose:
- Returns a provider by ID.

Input:
- `provider_id` in the path.

Output:
- Provider details.

#### `PATCH /api/v1/providers/{provider_id}`

Purpose:
- Updates a provider.

Example input:

```json
{
  "description": "Updated provider description"
}
```

Output:
- Updated provider object.

#### `DELETE /api/v1/providers/{provider_id}`

Purpose:
- Deletes a provider.

Output:
- `204 No Content`.

### 3. Model APIs

#### `POST /api/v1/models`

Purpose:
- Registers a new model under a provider.

Input:

```json
{
  "provider_id": "PROVIDER_ID",
  "display_name": "GPT OSS 20B",
  "model_name": "openai/gpt-oss-20b",
  "base_url": "http://77.48.24.239:43517/v1",
  "api_key": "demo-key",
  "capabilities": ["chat", "summarization", "translation"],
  "parameters": {
    "temperature": 0.2,
    "max_tokens": 2048,
    "pricing": {
      "prompt_per_1k": 0.001,
      "completion_per_1k": 0.002
    }
  },
  "priority": 100,
  "is_default": true,
  "is_active": true
}
```

Output:
- Returns the created model.

Example response:

```json
{
  "id": "MODEL_ID",
  "provider_id": "PROVIDER_ID",
  "display_name": "GPT OSS 20B",
  "model_name": "openai/gpt-oss-20b",
  "base_url": "http://77.48.24.239:43517/v1",
  "api_key_masked": "de***ey",
  "capabilities": ["chat", "summarization", "translation"],
  "parameters": {
    "temperature": 0.2,
    "max_tokens": 2048,
    "pricing": {
      "prompt_per_1k": 0.001,
      "completion_per_1k": 0.002
    }
  },
  "priority": 100,
  "is_default": true,
  "is_active": true,
  "health_status": "unknown",
  "last_checked_at": null,
  "created_at": "2026-04-21T04:32:00",
  "updated_at": "2026-04-21T04:32:00"
}
```

#### `GET /api/v1/models`

Purpose:
- Returns registered models.
- Supports filtering and search.

Query params:
- `provider_id`
- `provider_name`
- `model_name`
- `is_active`

Example:

```bash
curl "http://localhost:8888/api/v1/models?provider_name=OpenAI&model_name=gpt"
```

Example response:

```json
[
  {
    "id": "MODEL_ID",
    "provider_id": "PROVIDER_ID",
    "display_name": "GPT OSS 20B",
    "model_name": "openai/gpt-oss-20b",
    "base_url": "http://77.48.24.239:43517/v1",
    "api_key_masked": "de***ey",
    "capabilities": ["chat", "summarization", "translation"],
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 2048
    },
    "priority": 100,
    "is_default": true,
    "is_active": true,
    "health_status": "unknown",
    "last_checked_at": null,
    "created_at": "2026-04-21T04:32:00",
    "updated_at": "2026-04-21T04:32:00"
  }
]
```

#### `GET /api/v1/models/{model_id}`

Purpose:
- Returns a model by ID.

#### `PATCH /api/v1/models/{model_id}`

Purpose:
- Updates a model.

Example input:

```json
{
  "priority": 50,
  "is_default": true
}
```

#### `DELETE /api/v1/models/{model_id}`

Purpose:
- Deletes a model.

Output:
- `204 No Content`.

#### `POST /api/v1/models/{model_id}/health`

Purpose:
- Tests connectivity to the upstream model endpoint.

Input:
- `model_id` in the path.

Example response:

```json
{
  "model_id": "MODEL_ID",
  "status": "healthy",
  "detail": "Connected to upstream OpenAI-compatible endpoint.",
  "checked_at": "2026-04-21T04:33:00.000000Z"
}
```

### 4. Policy APIs

#### `POST /api/v1/policies`

Purpose:
- Creates a policy that selects a model by `use_case` and `organization_id`.

Input:

```json
{
  "organization_id": "org-002",
  "use_case": "chat_advisory",
  "default_model_id": "MODEL_ID",
  "fallback_model_id": null,
  "temperature": 0.2,
  "max_tokens": 512,
  "system_prompt": "You are a business analysis assistant.",
  "metadata": {
    "channel": "demo"
  },
  "is_active": true
}
```

Example response:

```json
{
  "id": "POLICY_ID",
  "organization_id": "org-002",
  "use_case": "chat_advisory",
  "default_model_id": "MODEL_ID",
  "fallback_model_id": null,
  "temperature": 0.2,
  "max_tokens": 512,
  "system_prompt": "You are a business analysis assistant.",
  "metadata": {
    "channel": "demo"
  },
  "is_active": true,
  "created_at": "2026-04-21T04:34:00",
  "updated_at": "2026-04-21T04:34:00"
}
```

#### `GET /api/v1/policies`

Purpose:
- Returns policies.

Query params:
- `organization_id`
- `use_case`

Example:

```bash
curl "http://localhost:8888/api/v1/policies?organization_id=org-002&use_case=chat_advisory"
```

#### `GET /api/v1/policies/{policy_id}`

Purpose:
- Returns a policy by ID.

#### `PATCH /api/v1/policies/{policy_id}`

Purpose:
- Updates a policy.

#### `DELETE /api/v1/policies/{policy_id}`

Purpose:
- Deletes a policy.

### 5. Context APIs

#### `POST /api/v1/contexts/build`

Purpose:
- Builds context from `query`, `history`, `external_contexts`, and `system_prompt`.
- This endpoint does not call a model. It only assembles context for preview.

Input:

```json
{
  "conversation_id": "test-conv-002",
  "organization_id": "org-002",
  "user_id": "user-002",
  "query": "Summarize the Q1 revenue situation.",
  "history": [
    {
      "role": "user",
      "content": "How did revenue perform last month?"
    },
    {
      "role": "assistant",
      "content": "Revenue increased by 5% last month."
    }
  ],
  "external_contexts": [
    {
      "title": "Q1 Report",
      "content": "Q1 revenue reached 12 billion VND, up 8% year over year.",
      "source": "report-q1.pdf",
      "metadata": {
        "file_type": "pdf"
      }
    }
  ],
  "system_prompt": "You are a corporate finance assistant.",
  "max_history_messages": 12
}
```

Example response:

```json
{
  "system_prompt": "You are a corporate finance assistant.\n\nOrganization context: org-002.\n\nTrusted context:\n[1] Q1 Report (report-q1.pdf)\nQ1 revenue reached 12 billion VND, up 8% year over year.",
  "messages": [
    {
      "role": "system",
      "content": "You are a corporate finance assistant.\n\nOrganization context: org-002.\n\nTrusted context:\n[1] Q1 Report (report-q1.pdf)\nQ1 revenue reached 12 billion VND, up 8% year over year."
    },
    {
      "role": "user",
      "content": "How did revenue perform last month?"
    },
    {
      "role": "assistant",
      "content": "Revenue increased by 5% last month."
    },
    {
      "role": "user",
      "content": "Summarize the Q1 revenue situation."
    }
  ],
  "context_items": [
    {
      "title": "Q1 Report",
      "content": "Q1 revenue reached 12 billion VND, up 8% year over year.",
      "source": "report-q1.pdf",
      "metadata": {
        "file_type": "pdf"
      }
    }
  ],
  "token_estimate": 86
}
```

#### `GET /api/v1/contexts`

Purpose:
- Returns stored contexts saved after inference.

Query params:
- `conversation_id`
- `organization_id`
- `user_id`
- `limit`

Example:

```bash
curl "http://localhost:8888/api/v1/contexts?conversation_id=test-conv-002&organization_id=org-002&user_id=user-002"
```

Output:
- A list of stored contexts, where `context.conversation_messages` may include the assistant response.

#### `GET /api/v1/contexts/{request_id}`

Purpose:
- Returns the full stored context for a given request.

Input:
- `request_id` from the inference response.

Output:
- `stored_context`
- `snapshots`

### 6. Inference APIs

#### `POST /api/v1/inferences`

Purpose:
- Builds context, resolves a model, calls the upstream model, and stores request/response/context/metrics.

Notes:
- If `model_id` is provided, the service uses that model directly.
- If `model_id` is omitted, the service may resolve the model through a `policy`.

Input linked to the policy created above:

```json
{
  "conversation_id": "test-conv-002",
  "organization_id": "org-002",
  "user_id": "user-002",
  "use_case": "chat_advisory",
  "question": "Summarize the Q1 revenue situation and provide 2 short observations.",
  "history": [
    {
      "role": "user",
      "content": "How did revenue perform last month?"
    },
    {
      "role": "assistant",
      "content": "Revenue increased by 5% last month."
    }
  ],
  "external_contexts": [
    {
      "title": "Q1 Report",
      "content": "Q1 revenue reached 12 billion VND, up 8% year over year.",
      "source": "report-q1.pdf",
      "metadata": {
        "file_type": "pdf"
      }
    }
  ],
  "metadata": {
    "trace_id": "demo-trace-001"
  }
}
```

Example response:

```json
{
  "request": {
    "id": "REQUEST_ID",
    "conversation_id": "test-conv-002",
    "organization_id": "org-002",
    "user_id": "user-002",
    "model_id": "MODEL_ID",
    "policy_id": "POLICY_ID",
    "question": "Summarize the Q1 revenue situation and provide 2 short observations.",
    "status": "completed",
    "latency_ms": 842,
    "error_message": null,
    "started_at": "2026-04-21T04:35:00.000000Z",
    "finished_at": "2026-04-21T04:35:01.000000Z"
  },
  "response": {
    "id": "RESPONSE_ID",
    "request_id": "REQUEST_ID",
    "response_text": "Q1 revenue reached 12 billion VND, up 8% year over year. Observation 1: growth is positive. Observation 2: margin performance should continue to be monitored.",
    "finish_reason": "stop",
    "prompt_tokens": 120,
    "completion_tokens": 45,
    "total_tokens": 165,
    "estimated_cost": 0.00021,
    "created_at": "2026-04-21T04:35:01.000000Z"
  },
  "context": {
    "system_prompt": "You are a business analysis assistant.",
    "messages": [
      {
        "role": "system",
        "content": "You are a business analysis assistant."
      },
      {
        "role": "user",
        "content": "How did revenue perform last month?"
      },
      {
        "role": "assistant",
        "content": "Revenue increased by 5% last month."
      },
      {
        "role": "user",
        "content": "Summarize the Q1 revenue situation and provide 2 short observations."
      }
    ],
    "context_items": [
      {
        "title": "Q1 Report",
        "content": "Q1 revenue reached 12 billion VND, up 8% year over year.",
        "source": "report-q1.pdf",
        "metadata": {
          "file_type": "pdf"
        }
      }
    ],
    "token_estimate": 100
  }
}
```

#### `GET /api/v1/inferences`

Purpose:
- Returns inference records.

Query params:
- `conversation_id`
- `organization_id`
- `user_id`
- `limit`

Example:

```bash
curl "http://localhost:8888/api/v1/inferences?conversation_id=test-conv-002&limit=10"
```

#### `GET /api/v1/inferences/{request_id}`

Purpose:
- Returns a single inference record by request ID.

Input:
- `request_id`.

### 7. Feedback APIs

#### `POST /api/v1/feedback`

Purpose:
- Stores feedback for an inference.

Input:

```json
{
  "request_id": "REQUEST_ID",
  "conversation_id": "test-conv-002",
  "organization_id": "org-002",
  "user_id": "user-002",
  "rating": "positive",
  "comment": "The answer was concise and relevant.",
  "metadata": {
    "source": "swagger"
  }
}
```

Example response:

```json
{
  "id": "FEEDBACK_ID",
  "request_id": "REQUEST_ID",
  "conversation_id": "test-conv-002",
  "organization_id": "org-002",
  "user_id": "user-002",
  "model_id": "MODEL_ID",
  "rating": "positive",
  "comment": "The answer was concise and relevant.",
  "metadata": {
    "source": "swagger"
  },
  "created_at": "2026-04-21T04:36:00"
}
```

#### `GET /api/v1/feedback`

Purpose:
- Returns feedback records.

Query params:
- `organization_id`
- `conversation_id`
- `model_id`
- `limit`

Example:

```bash
curl "http://localhost:8888/api/v1/feedback?conversation_id=test-conv-002&limit=20"
```

### 8. Metrics API

#### `GET /api/v1/metrics/summary`

Purpose:
- Returns aggregated metrics by model over a given `hours` window.

Query params:
- `hours`: default `24`
- `model_id`: filter by a specific model

Example:

```bash
curl "http://localhost:8888/api/v1/metrics/summary?hours=24&model_id=MODEL_ID"
```

Example response:

```json
{
  "generated_at": "2026-04-21T04:37:00.000000Z",
  "bucket_granularity": "hour",
  "items": [
    {
      "model_id": "MODEL_ID",
      "model_display_name": "GPT OSS 20B",
      "request_count": 1,
      "success_count": 1,
      "error_count": 0,
      "avg_latency_ms": 842.0,
      "prompt_tokens": 120,
      "completion_tokens": 45,
      "total_tokens": 165,
      "estimated_cost": 0.00021
    }
  ]
}
```

## Important Notes for Testing

- `provider_id` must be the actual provider ID from the database, not the provider name.
- `model_id` is optional in the inference API. If omitted, the service tries to resolve a model from `policy`.
- `conversation_id`, `organization_id`, and `user_id` are currently used for metadata, filtering, and stored context traceability.
- `POST /api/v1/contexts/build` only assembles context. It does not call a model.
- `GET /api/v1/contexts` only reads context that was stored after inference.
- `external_contexts` can represent uploaded file content, retrieved chunks, or business data prepared by `Server_service`.

## Quick cURL Flow

### Create provider

```bash
curl -X POST "http://localhost:8888/api/v1/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI Demo",
    "provider_type": "openai_compatible",
    "description": "OpenAI-compatible provider for testing",
    "metadata": {"owner": "local-dev"},
    "is_active": true
  }'
```

### Search provider by name

```bash
curl "http://localhost:8888/api/v1/providers?name=OpenAI"
```

### Create model

```bash
curl -X POST "http://localhost:8888/api/v1/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "PROVIDER_ID",
    "display_name": "GPT OSS 20B",
    "model_name": "openai/gpt-oss-20b",
    "base_url": "http://77.48.24.239:43517/v1",
    "api_key": "demo-key",
    "capabilities": ["chat", "summarization", "translation"],
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 2048
    },
    "priority": 100,
    "is_default": true,
    "is_active": true
  }'
```

### Search model by provider name and model name

```bash
curl "http://localhost:8888/api/v1/models?provider_name=OpenAI&model_name=gpt"
```

### Create policy

```bash
curl -X POST "http://localhost:8888/api/v1/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org-002",
    "use_case": "chat_advisory",
    "default_model_id": "MODEL_ID",
    "fallback_model_id": null,
    "temperature": 0.2,
    "max_tokens": 512,
    "system_prompt": "You are a business analysis assistant.",
    "metadata": {"channel": "demo"},
    "is_active": true
  }'
```

### Run inference

```bash
curl -X POST "http://localhost:8888/api/v1/inferences" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-conv-002",
    "organization_id": "org-002",
    "user_id": "user-002",
    "use_case": "chat_advisory",
    "question": "Summarize the Q1 revenue situation and provide 2 short observations.",
    "history": [
      {"role": "user", "content": "How did revenue perform last month?"},
      {"role": "assistant", "content": "Revenue increased by 5% last month."}
    ],
    "external_contexts": [
      {
        "title": "Q1 Report",
        "content": "Q1 revenue reached 12 billion VND, up 8% year over year.",
        "source": "report-q1.pdf",
        "metadata": {"file_type": "pdf"}
      }
    ],
    "metadata": {"trace_id": "demo-trace-001"}
  }'
```

### Get stored contexts

```bash
curl "http://localhost:8888/api/v1/contexts?conversation_id=test-conv-002&organization_id=org-002&user_id=user-002"
```

### Get full context by request ID

```bash
curl "http://localhost:8888/api/v1/contexts/REQUEST_ID"
```

### Submit feedback

```bash
curl -X POST "http://localhost:8888/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQUEST_ID",
    "conversation_id": "test-conv-002",
    "organization_id": "org-002",
    "user_id": "user-002",
    "rating": "positive",
    "comment": "The answer was concise and relevant.",
    "metadata": {"source": "curl"}
  }'
```

### View metrics

```bash
curl "http://localhost:8888/api/v1/metrics/summary?hours=24&model_id=MODEL_ID"
```

## Suggested Next Steps

- Connect `Server_service` chat flow to `Model_service`.
- Add a real retrieval layer so `external_contexts` can be populated from a document store or vector store.
- Add a migration tool such as `Alembic`.
- Add auth and RBAC between services.
- Add automated tests for the route and service layers.
