# AI Business Assistant API Reference

Tài liệu này mô tả các API chính của `Server_service`, chức năng của chúng và mẫu phản hồi JSON.

## Tổng quan
- Server cung cấp API cho:
  - Xác thực và quản lý user
  - Quản lý tổ chức và RBAC
  - Quản lý tài liệu và pipeline
  - Chat theo tổ chức
  - Thống kê analytics
  - Cài đặt người dùng và tổ chức
  - Thanh toán và notification
- Hầu hết các endpoint trả về HTTP 200 cùng JSON chuẩn.
- Đối với các ứng dụng bên ngoài, có thể định nghĩa wrapper custom như:
  - `200`: kết quả tiêu chuẩn
  - `2001`: envelope kiểu `status`, `success`, `message`, `data`

## Response example: HTTP 200
```json
{
  "id": "uuid-1234",
  "name": "Acme Vietnam"
}
```

## Response example: HTTP 2001
```json
{
  "status": 2001,
  "success": true,
  "message": "Thao tac thanh cong",
  "data": {
    "id": "uuid-1234",
    "name": "Acme Vietnam"
  }
}
```

## System

### `GET /`
- Trả metadata API và link Swagger UI.
- Mô tả: `ApiInfo`

### `GET /health`
- Trả trạng thái server.
- Mô tả: `{"status":"ok"}`

### `GET /permissions`
- Trả danh mục Role và Permission.
- Sử dụng để hiển thị quyền trong UI RBAC.

## Auth

### `POST /auth/register`
- Đăng ký email/password và nhận JWT.
- Body: `AuthRegister`
- Response: `TokenResponse`

### `POST /auth/login`
- Đăng nhập bằng email/password.
- Body: `AuthLogin`
- Response: `TokenResponse`

### `GET /auth/me`
- Lấy user hiện tại từ Bearer JWT.
- Response: `UserRead`

## Users

### `POST /users`
- Tạo user mới.
- Body: `UserCreate`
- Response: `UserRead`

### `GET /users`
- Lấy danh sách user.
- Hỗ trợ tìm kiếm, phân trang.

### `GET /users/{user_id}`
- Lấy chi tiết user.

## Organizations

### `POST /organizations`
- Tạo tổ chức mới.
- Body: `OrganizationCreate`
- Tự động tạo member admin cho owner.

### `GET /organizations`
- Lấy danh sách tổ chức.
- Hỗ trợ lọc theo tên/ngành hoặc user tham gia.

### `GET /organizations/{org_id}`
- Lấy thông tin tổ chức.

### `PATCH /organizations/{org_id}`
- Cập nhật thông tin tổ chức.
- Yêu cầu `acting_user_id` có quyền `access_org_settings`.

### `GET /organizations/{org_id}/dashboard`
- Lấy overview tổ chức.
- Trả `employee_count`, `document_count`, `chat_session_count`, gợi ý câu hỏi.

## Members & RBAC

### `POST /organizations/{org_id}/members`
- Thêm thành viên vào tổ chức.
- Yêu cầu quyền `access_org_settings`.

### `GET /organizations/{org_id}/members`
- Lấy danh sách nhân viên.
- Yêu cầu quyền `view_employees`.

### `PATCH /organizations/{org_id}/members/{member_id}`
- Cập nhật role/permissions/status của thành viên.

### `DELETE /organizations/{org_id}/members/{member_id}`
- Xóa thành viên khỏi tổ chức.

### `DELETE /organizations/{org_id}/membership`
- Người dùng rời tổ chức.

## Documents

### `POST /organizations/{org_id}/documents`
- Đăng ký tài liệu và bắt đầu pipeline ingest.
- Body: `DocumentCreate`

### `POST /organizations/{org_id}/documents/upload`
- Upload file lên MinIO và tạo metadata tài liệu.
- Yêu cầu `acting_user_id` có quyền `upload_documents`.

### `GET /organizations/{org_id}/documents`
- Lấy danh sách tài liệu của tổ chức.
- Yêu cầu quyền `read_documents`.

### `GET /documents/{document_id}/pipeline`
- Xem trạng thái pipeline của tài liệu.

### `PATCH /documents/{document_id}/status`
- Cập nhật trạng thái pipeline/tài liệu.
- Yêu cầu quyền `upload_documents`.

## Chat

### `GET /organizations/{org_id}/chat/suggestions`
- Lấy gợi ý câu hỏi theo tổ chức.
- Yêu cầu `chat_advisory`.

### `GET /organizations/{org_id}/chat/sessions`
- Lấy lịch sử chat theo tổ chức.
- Yêu cầu `chat_advisory`.

### `POST /organizations/{org_id}/chat/sessions`
- Tạo chat session mới.

### `GET /chat/sessions/{session_id}/messages`
- Lấy thông tin message trong một session.

### `POST /organizations/{org_id}/chat/ask`
- Hỏi đáp theo tài liệu nội bộ tổ chức.
- Tạo session mới nếu không truyền `session_id`.
- Response: `ChatAnswer`

### `POST /chat/messages/{message_id}/feedback`
- Gửi feedback cho câu trả lời.

### `DELETE /chat/sessions/{session_id}`
- Xóa một đoạn chat.

## Analytics

### `GET /organizations/{org_id}/analytics`
- Lấy thống kê tổ chức.
- Yêu cầu quyền `view_analytics`.

### `PUT /organizations/{org_id}/analytics/restrictions`
- Cập nhật hạn chế nội dung nhạy cảm của tổ chức.

## Settings

### `GET /settings/profile`
- Lấy cài đặt người dùng hiện tại từ JWT.

### `PATCH /settings/profile`
- Cập nhật cài đặt cá nhân.

### `GET /users/{user_id}/settings`
- Lấy cài đặt người dùng theo `user_id`.

### `PATCH /users/{user_id}/settings`
- Cập nhật cài đặt người dùng theo `user_id`.

### `GET /organizations/{org_id}/settings`
- Lấy cài đặt tổ chức.

### `PATCH /organizations/{org_id}/settings`
- Cập nhật cài đặt tổ chức.

## Billing

### `GET /organizations/{org_id}/billing`
- Lấy thông tin thanh toán của tổ chức.

### `POST /organizations/{org_id}/billing/checkout`
- Tạo checkout/thanh toán cho gói dịch vụ.

### `PATCH /billing/records/{record_id}`
- Cập nhật trạng thái thanh toán.

## Notifications

### `POST /notifications`
- Tạo notification cho user.

### `GET /users/{user_id}/notifications`
- Lấy notification của user.

### `PATCH /notifications/{notification_id}/read`
- Đánh dấu notification đã đọc.

## Xác thực chủ yếu
- Nhiều endpoint yêu cầu `Bearer <token>` trong header.
- Một số endpoint dùng query param `acting_user_id` để kiểm tra quyền.

---

> Ghi chú: file này dựa trên routes hiện tại trong `Server_service/app/main.py` và các schema trong `Server_service/app/schemas.py`.
