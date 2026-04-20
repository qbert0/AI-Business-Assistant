# Serving model service

## Objectives

Mục tiêu chính của hệ thống này là tư vấn về tài chính, do đó cần phải có một Model Service để thực hiện việc deploying, managing, monitoring và cải thiện model. 

Model được sử dụng sẽ là các LLM từ nhiều Provider khác nhau, ví dụ như OpenAI cho GPT-models, Ollama models, .... Các model đã được serving riêng trên một cơ sở hạ tầng khác, với các thông tin được cung cấp như BASE_URL, API_KEY và MODEL_NAME.

Khi đó, tuy nhiên, hạ tầng đó sẽ đóng vai trò serve model và inference thôi. Còn nhiệm vụ chính của Model Service sẽ thực hiện các công việc xung quanh Models đó. Model Service sẽ được triển khai dưới dạng một FastAPI server để cung cấp các api tương tác với models, đồng thời triển khai thêm cả các databases để quản lý các metadata và thông số cần thiết:
- Thêm / sửa / xóa thông tin các models, sau đó lưu các metadata vào database chung.
- Tùy chọn model trong quá trình chat / tư vấn
- Model Inference (Gọi tới model bên phía server đã serve để get response). Các metadata của một lần inference cũng được lưu vào db, bao gồm conversation gọi, query, response, lượng tokens, thời gian, .....
- Luồng quản lý context cho query (context của một lần query có thể đến từ các query + response từ các truy vấn của cùng conversation trước đó). Do đó, cần có một api để get các context cần thiết cho một query để kết hợp với việc inference.
- Cơ chế tiếp nhận feedback từ người dùng (với 1 query khi nhận được response, người dùng có thể response thông qua chức năng like / dislike). Vì vậy, có thể cần có một api để tiếp nhận các feedback đó để điều chỉnh context khi query.
- Các api để quản lý metrics của models, ví dụ như lưu lượng, tốc độ phản hồi, .... Các thông tin này cũng được lưu lại vào trong DB.
- Thêm các API để get các records từ DB.
- Còn các chức năng khác bạn có thể đề xuất thêm.

## Architecture

- Triển khai dưới dạng FastAPI, dùng MariaDB để quản lý dữ liệu.
- Triển khai từ Abstraction tới Concretization để có thể dễ dàng thay đổi các engine khi cần thiết (loại model, loại database, ....)
- Triển khai các API sao cho hiệu quả, tránh các bottleneck tiềm ẩn có thể xảy ra.
- Còn các kiến trúc khác bạn có thể đề xuất thêm.

## Current implementation

Model Service da duoc scaffold thanh mot FastAPI service rieng, co database MariaDB rieng va duoc docker hoa tach biet khoi `Server_service`.

### Service structure

```txt
Model_service/
  app/
    api/routes/
    core/
    db/
    infrastructure/llm/
    schemas/
    services/
    main.py
  Dockerfile
  requirements.txt
  .env.example
```

### Data isolation

- `Server_service` tiep tuc dung database `precisioncast`.
- `Model_service` dung database rieng `model_service`.
- Trong `docker-compose.yml`, Model Service co MariaDB rieng la `model_mariadb`.

### Main capabilities implemented

- CRUD cho `providers`.
- CRUD cho `registered models`.
- CRUD cho `model policies`.
- Health check upstream endpoint cho tung model.
- API build context cho query.
- API inference co luu `request`, `response`, `context snapshot`, `token usage`, `latency`, `estimated cost`.
- API feedback.
- API metric summary dua tren bang `metric_rollups`.

### Supported provider adapters

- `openai_compatible`
- `ollama`

## API overview

### System

- `GET /`
- `GET /health`

### Provider registry

- `GET /api/v1/providers`
- `POST /api/v1/providers`
- `GET /api/v1/providers/{provider_id}`
- `PATCH /api/v1/providers/{provider_id}`
- `DELETE /api/v1/providers/{provider_id}`

### Model registry

- `GET /api/v1/models`
- `POST /api/v1/models`
- `GET /api/v1/models/{model_id}`
- `PATCH /api/v1/models/{model_id}`
- `DELETE /api/v1/models/{model_id}`
- `POST /api/v1/models/{model_id}/health`

### Policy management

- `GET /api/v1/policies`
- `POST /api/v1/policies`
- `GET /api/v1/policies/{policy_id}`
- `PATCH /api/v1/policies/{policy_id}`
- `DELETE /api/v1/policies/{policy_id}`

### Runtime APIs

- `POST /api/v1/contexts/build`
- `POST /api/v1/inferences`
- `GET /api/v1/inferences`
- `GET /api/v1/inferences/{request_id}`
- `POST /api/v1/feedback`
- `GET /api/v1/feedback`
- `GET /api/v1/metrics/summary`

## Database model

Nhung bang chinh da duoc tao trong Model Service:

- `model_providers`
- `registered_models`
- `model_policies`
- `inference_requests`
- `inference_responses`
- `context_snapshots`
- `feedback_events`
- `metric_rollups`

## Run with Docker Compose

Tu root repo:

```bash
docker compose up --build model_service model_mariadb
```

Hoac chay ca stack:

```bash
docker compose up --build
```

Swagger UI cua Model Service se nam tai:

```txt
http://localhost:8100/docs
```

## Suggested next steps

- Noi `Server_service` chat flow sang `Model_service` thay cho placeholder response.
- Bo sung migration tool nhu `Alembic` thay vi phu thuoc vao `create_all`.
- Them retrieval layer thuc su de `external_contexts` chua noi dung chunk/document thay vi metadata.
- Them RBAC va auth giua `Server_service` va `Model_service`.
