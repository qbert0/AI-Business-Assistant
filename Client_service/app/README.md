# App Structure

`app` được tổ chức theo trách nhiệm, không để page ôm toàn bộ logic giao diện và dữ liệu.

## Thư mục chính

- `assets/`: logo, hình ảnh, CSS dùng chung.
- `components/`: UI component, chia theo 3 nhóm.
- `composables/`: composable theo domain nghiệp vụ và nhóm API.
- `constants/`: route, message, RBAC, dữ liệu bất biến.
- `layouts/`: bố cục trang.
- `locales/`: ngôn ngữ.
- `middleware/`: bảo vệ route bằng auth và RBAC.
- `pages/`: định nghĩa route và ghép shared component theo layout.
- `schemas/`: schema validate form với `zod`.
- `stores/`: state phục vụ render và vòng đời dữ liệu.
- `types/`: type dùng chung.
- `utils/`: hàm hỗ trợ frontend.

## Components

- `components/shared/`: component lớn theo bố cục hoặc ngữ cảnh trang.
  - Ví dụ: `AppHeader`, `AppSidebar`, `ChatSessionSidebar`.
- `components/form/`: form hoặc modal nhập liệu có validate.
  - Ví dụ: `EmployeeModal`.
- `components/card/`: component con tái sử dụng nhiều lần.
  - Ví dụ: `ActionCard`, `StatsCard`, `AppPanel`, `AppPopup`.

## Composables

- `composables/api/`: chỉ phụ trách gọi API nội bộ qua `server/api`.
- `composables/auth|chat|documents|organizations|settings|security|system/`: composable nghiệp vụ theo nhóm chức năng.

## Stores

- `stores/auth/`: phiên đăng nhập và người dùng hiện tại.
- `stores/chat/`: tách riêng lịch sử chat và nội dung chat.
  - `useChatSessionStore`: quản lý danh sách cuộc trò chuyện, gợi ý, phân trang lịch sử.
  - `useChatMessageStore`: quản lý message, stream, feedback, load thêm tin cũ.
  - `useChatStore`: facade gom 2 store trên để giảm thay đổi call site.
- `stores/documents/`: tách thư viện tài liệu và tài liệu đang mở.
  - `useDocumentLibraryStore`: danh sách tài liệu, pipeline, upload.
  - `useDocumentViewerStore`: tài liệu đang mở, tab hiện tại, preview cache theo vòng đời mở tab.
  - `useDocumentStore`: facade cho page/composable.
- `stores/organizations/`: tổ chức, nhân viên, lời mời/yêu cầu.

## Quy ước triển khai

- `pages/` chỉ ghép layout, gọi shared component và composable cần thiết.
- Không để page tự giữ state dài hạn nếu state đó cần tái sử dụng hoặc có vòng đời rõ ràng.
- API client luôn đi qua `composables/api/*`, không gọi trực tiếp backend từ page/component.
- Mọi route thuộc tổ chức phải gắn với `orgId` hoặc `slug` rõ ràng trong store.
