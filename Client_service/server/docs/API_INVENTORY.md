# API Inventory

Tài liệu này thống kê các API mà `Client_service` đang gọi qua lớp `server/api`.

## Auth

Composable: `app/composables/api/auth/useApiAuth.ts`

| Method | Client route | Server handler |
|---|---|---|
| `POST` | `/api/auth/login` | `server/api/auth/login.post.ts` |
| `POST` | `/api/auth/register` | `server/api/auth/register.post.ts` |
| `GET` | `/api/auth/me` | `server/api/auth/me.get.ts` |
| `POST` | `/api/auth/logout` | `server/api/auth/logout.post.ts` |

## Chat

Composable: `app/composables/api/chat/useApiChat.ts`

| Method | Client route | Purpose | Server handler |
|---|---|---|---|
| `GET` | `/api/chat/:slug/sessions` | Lấy lịch sử cuộc chat theo workspace | `server/api/chat/[slug]/sessions.get.ts` |
| `GET` | `/api/chat/:slug/messages` | Lấy message của một session | `server/api/chat/[slug]/messages.get.ts` |
| `POST` | `/api/chat/:slug/ask` | Gửi câu hỏi không stream | `server/api/chat/[slug]/ask.post.ts` |
| `GET` | `/api/chat/:slug/suggestions` | Lấy câu hỏi gợi ý và câu hỏi phổ biến | `server/api/chat/[slug]/suggestions.get.ts` |
| `POST` | `/api/chat/:slug/feedback` | Gửi feedback cho câu trả lời | `server/api/chat/[slug]/feedback.post.ts` |

Ngoài các route nội bộ trên, `app/utils/chat/stream-chat.ts` còn gọi trực tiếp backend streaming:

- Personal: `/chat/personal/ask/stream`
- Organization: `/organizations/:slug/chat/ask/stream`

## Documents

Composable: `app/composables/api/documents/useApiDocuments.ts`

| Method | Client route | Purpose | Server handler |
|---|---|---|---|
| `GET` | `/api/documents/:slug` | Danh sách tài liệu tổ chức | `server/api/documents/[slug]/index.get.ts` |
| `POST` | `/api/documents/:slug` | Upload/tạo tài liệu | `server/api/documents/[slug]/index.post.ts` |
| `GET` | `/api/documents/:slug/pipeline` | Lấy pipeline xử lý tài liệu | `server/api/documents/[slug]/pipeline.get.ts` |
| `GET` | `/api/documents/:slug/:documentId/preview` | Lấy preview text của file đang mở | `server/api/documents/[slug]/[documentId]/preview.get.ts` |

Các URL được dùng trực tiếp bởi UI viewer:

| Method | Client route | Purpose | Server handler |
|---|---|---|---|
| `GET` | `/api/documents/:slug/:documentId/content` | Render PDF/image/file content | `server/api/documents/[slug]/[documentId]/content.get.ts` |

## Organizations

Composable: `app/composables/api/organizations/useApiOrganizations.ts`

| Method | Client route | Purpose | Server handler |
|---|---|---|---|
| `GET` | `/api/organizations` | Danh sách tổ chức và yêu cầu tham gia | `server/api/organizations/index.get.ts` |
| `POST` | `/api/organizations` | Tạo tổ chức | `server/api/organizations/index.post.ts` |
| `GET` | `/api/organizations/:slug` | Lấy chi tiết tổ chức | `server/api/organizations/[slug]/index.get.ts` |
| `GET` | `/api/organizations/:slug/members` | Danh sách nhân viên | `server/api/organizations/[slug]/members.get.ts` |
| `POST` | `/api/organizations/:slug/members` | Thêm nhân viên | `server/api/organizations/[slug]/members.post.ts` |
| `PATCH` | `/api/organizations/:slug/members/:memberId` | Cập nhật vai trò/quyền/thông tin nhân viên | `server/api/organizations/[slug]/members/[memberId].patch.ts` |
| `DELETE` | `/api/organizations/:slug/members/:memberId` | Xóa nhân viên | `server/api/organizations/[slug]/members/[memberId].delete.ts` |

## Public organization

| Method | Client route | Purpose | Server handler |
|---|---|---|---|
| `GET` | `/api/public/organizations/:slug` | Trang public của tổ chức | `server/api/public/organizations/[slug].get.ts` |

## Ghi chú

- Quy ước hiện tại là page/component không gọi trực tiếp backend, mà gọi composable `useApi*`.
- Nếu thêm API mới, cập nhật cả composable tương ứng và tài liệu này.
