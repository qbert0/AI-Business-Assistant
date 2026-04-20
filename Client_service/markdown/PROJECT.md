# PROJECT.md

## 1. Vai trò tài liệu

`PROJECT.md` mô tả cách dự án hiện tại được tổ chức theo công nghệ đang sử dụng. Tài liệu này không mô tả quy chuẩn thị giác chung và không định nghĩa nghiệp vụ. Hai phần đó lần lượt nằm trong `DESIGN.md` và `BUSINESS.md`.

Tài liệu này trả lời:

- Dự án dùng stack gì?
- Folder nào chịu trách nhiệm gì?
- Route hiện tại được tổ chức như thế nào?
- State, API, RBAC, locale, schema và style được đặt ở đâu?
- Khi thêm tính năng mới thì nên đặt file ở đâu?

---

## 2. Stack hiện tại

Dự án là frontend Nuxt 4 dùng Vue 3 và TypeScript.

Các package chính:

- `nuxt`
- `vue`
- `vue-router`
- `@nuxtjs/tailwindcss`
- `@nuxt/icon`
- `@nuxt/image`
- `@nuxtjs/google-fonts`
- `@pinia/nuxt`
- `pinia`
- `zod`
- `shadcn-nuxt`

Ghi chú triển khai:

- Tailwind là lớp style chính.
- Pinia đang được dùng cho state bền vững.
- Zod đang được dùng cho schema validation.
- Nuxt server routes đang đóng vai trò API mock/proxy nội bộ.
- Dự án chưa dùng VeeValidate hoặc ECharts trong code hiện tại, nên không ghi chúng như dependency triển khai bắt buộc.

---

## 3. Cấu hình nền

Các file cấu hình chính:

- `nuxt.config.ts`: khai báo module Nuxt, Tailwind CSS path, Google Fonts và Vite optimize deps.
- `tailwind.config.ts`: khai báo token màu, font, font size, spacing, border radius và shadow.
- `app/assets/css/tailwind-core.css`: chứa Tailwind entry và component classes dùng chung.

Font hiện tại:

- `Inter`
- `Noto Sans`
- Subset `latin` và `vietnamese`

Điểm quan trọng: mọi class mẫu dùng nhiều lần phải được gom vào `tailwind-core.css`, không viết style rời rạc trong từng file Vue nếu có thể biểu diễn bằng Tailwind.

---

## 4. Folder structure

```txt
app/
  assets/css/
  components/
  composables/
  constants/
  layouts/
  locales/
  middleware/
  pages/
  schemas/
  stores/
  types/
  utils/

server/
  api/
  utils/

markdown/
  DESIGN.md
  PROJECT.md
  BUSINESS.md
```

---

## 5. `app/pages`

`app/pages` chứa route-level screens.

Route chính hiện tại:

| Route | Vai trò |
|---|---|
| `/` | Trang giới thiệu sản phẩm public |
| `/auth/login` | Đăng nhập |
| `/auth/register` | Đăng ký |
| `/dashboard` | Trang làm việc chính, mặc định là chat theo context |
| `/workspace` | Legacy route cho workspace |
| `/profile` | Hồ sơ public |
| `/setting` | Redirect về `/setting/profile` |
| `/setting/profile` | Chỉnh hồ sơ public ở khu vực private |
| `/setting/payment` | Cài đặt thanh toán cá nhân |
| `/setting/organize` | Cài đặt tổ chức mặc định/cách truy cập ở mức cá nhân |
| `/setting/authen` | Cài đặt đăng nhập và bảo mật |
| `/notifications` | Thông báo |
| `/org` | Danh sách tổ chức và yêu cầu tham gia công ty |
| `/org/create` | Tạo công ty mới |
| `/org/[id]/dashboard` | Tổng quan tổ chức |
| `/org/[id]/employees` | Nhân viên |
| `/org/[id]/documents` | Tài liệu |
| `/org/[id]/analytics` | Phân tích |
| `/org/[id]/chat` | Chat tổ chức |
| `/org/[id]/settings` | Cài đặt tổ chức |
| `/permission-denied` | Trang từ chối quyền |

Legacy route còn tồn tại:

- `/organizations`
- `/organizations/[slug]/*`

Các route này đang được giữ để tương thích trong quá trình chuyển sang route chuẩn `/org`.

Nguyên tắc:

- Page chỉ phối hợp layout, route params và component.
- Logic lặp lại đưa vào store/composable.
- Text hiển thị lấy từ locale.
- Route path lấy từ constants.

---

## 6. `app/layouts`

Layout hiện tại:

- `default.vue`: shell chính của app, gồm header, optional sidebar và main shell theo route.
- `auth.vue`: shell cho trang đăng nhập/đăng ký.

`default.vue` phân loại shell theo route:

- Landing shell cho `/`.
- Dashboard shell cho `/dashboard` và `/workspace`.
- Settings shell cho `/setting/*`.
- Organization shell cho `/org/*` và `/organizations/*`.
- Content shell cho route còn lại.

Không nên đưa logic nghiệp vụ nặng vào layout. Layout chỉ quyết định khung màn hình.

---

## 7. `app/components`

Các component dùng chung hiện tại:

- `AppHeader.vue`: header toàn cục, search tổ chức, notification, avatar menu.
- `AppNavigationDrawer.vue`: drawer mở từ header, chứa navigation chính và lịch sử chat.
- `AppSidebar.vue`: sidebar layout cũ/tuỳ trang.
- `AppPopup.vue`: popup dùng chung, đóng khi click ra ngoài.
- `ChatSessionSidebar.vue`: sidebar lịch sử chat theo context.
- `EmployeeModal.vue`: modal thêm nhân viên.
- `OrganizationContextNav.vue`: navigation cấp hai của tổ chức, có nhãn tên tổ chức không bấm được.
- `SettingsShell.vue`: layout nội bộ cho setting.
- `RbacProvider.vue`: wrapper hỗ trợ kiểm tra quyền ở UI.
- `StatsCard.vue`: card thống kê.
- `ActionCard.vue`: card hành động.

Nguyên tắc component:

- Component nên nhận dữ liệu qua props hoặc store/composable rõ ràng.
- Popup/menu nên dùng `AppPopup`.
- Component render text từ locale hoặc constants, không hardcode text UI.
- Component không nên tự định nghĩa route string trực tiếp.

---

## 8. `app/constants`

Các constant chính:

- `navigation.ts`: route constants, route builder và navigation item builders.
- `rbac.ts`: permission keys, permission labels, default permissions theo role.
- `messages.ts`: các message UI nhỏ còn dùng ngoài locale.
- `mock-data.ts`: dữ liệu directory user đăng ký để tìm email nhân viên.

Route path phải được lấy từ `APP_ROUTES` hoặc helper như `getOrganizationRoute`.

Permission keys hiện tại:

- `access_org_settings`
- `chat_advisory`
- `read_documents`
- `view_employees`
- `view_analytics`
- `edit_sensitive_restrictions`
- `delete_chat_sessions`
- `upload_documents`

---

## 9. `app/locales`

Locale module hiện tại:

- `vi.ts`
- `en.ts`
- `index.ts`

Locale mặc định là `vi`.

Quy tắc:

- Text UI trong Vue lấy từ `useAppLocale()`.
- Navigation label lấy từ locale thông qua function trong `navigation.ts`.
- Placeholder, button label, empty state, modal title, menu label đều nằm trong locale.
- Nếu sau này server trả message catalog theo ngôn ngữ user chọn, module này là điểm thay thế hoặc cache payload server.

---

## 10. `app/stores`

Pinia stores hiện tại:

- `auth.ts`: user hiện tại, hydrate, login, logout.
- `organizations.ts`: danh sách tổ chức, yêu cầu tham gia, member theo tổ chức, thêm/xóa/sửa nhân viên.
- `chat.ts`: chat sessions, messages, suggestions, popular questions theo context.
- `documents.ts`: tài liệu và pipeline xử lý theo tổ chức.

Nguyên tắc state:

- State dùng nhiều trang hoặc cần sống qua route nên nằm trong store.
- State chỉ phục vụ một component nhỏ nên giữ local.
- Server state có thể nằm trong store nếu nhiều nơi dùng chung hoặc cần cache theo context.

---

## 11. `app/composables`

Nhóm composable hiện tại:

- API composables: `useApiAuth`, `useApiOrganizations`, `useApiChat`, `useApiDocuments`.
- Compatibility/feature composables: `useAuth`, `useOrganization`, `useChatbot`, `useDocuments`, `useDashboard`.
- UI/system composables: `useAppLocale`, `useRbac`, `useSettingsForms`, `useUiState`.

Nguyên tắc:

- API composable chỉ bọc transport, không render UI.
- Feature composable có thể giữ adapter để code cũ không vỡ trong quá trình refactor.
- Reactive workflow dùng composable nếu chưa cần store.

---

## 12. `app/schemas`

Schema hiện tại dùng Zod:

- `auth.ts`: login schema.
- `organization.ts`: create organization và create employee schema.
- `settings.ts`: schema cho form setting.

Nguyên tắc:

- Form input có rule rõ nên có schema.
- Không copy validation giữa nhiều page.
- Schema không chứa text UI dài; error message có thể được chuẩn hoá về locale trong bước tiếp theo nếu cần i18n đầy đủ.

---

## 13. `app/types`

Types hiện tại:

- `auth.ts`
- `organization.ts`
- `dashboard.ts`

Các type quan trọng:

- `AuthUser`
- `OrganizationSummary`
- `OrganizationMember`
- `JoinRequest`
- `KnowledgeDocument`
- `PipelineStep`
- `ChatSession`
- `ChatMessage`
- `FeedbackEntry`

Nguyên tắc:

- Shared contract đặt ở `types`.
- Type local chỉ dùng một nơi có thể giữ trong file đó.

---

## 14. `app/utils`

Utils hiện tại:

- `avatar.ts`: tạo màu avatar theo tên.
- `search.ts`: helper search/normalize.
- `text.ts`: helper xử lý text như slug.

Utils phải là hàm nhỏ, ít side effect, không phụ thuộc Vue lifecycle.

---

## 15. `app/middleware`

Middleware hiện tại:

- `auth.global.ts`: hydrate auth, redirect guest vào login, redirect user khỏi login/register.
- `rbac.global.ts`: kiểm tra quyền route tổ chức và chuyển sang `/permission-denied` khi thiếu quyền.

RBAC route mapping đang nằm trong `useRbac`.

Middleware chỉ quyết định navigation, không render UI và không chứa workflow nghiệp vụ dài.

---

## 16. `server/api` và `server/utils`

Nuxt server routes hiện tại đóng vai trò API mock/proxy nội bộ.

Nhóm endpoint:

- Auth: login, logout, me, Google callback.
- Organizations: list, create, detail, members, add member, patch member, delete member.
- Chat: sessions, messages, suggestions, ask, feedback.
- Documents: list, upload/index, pipeline.

Server utils:

- `jwt.ts`
- `mockData.ts`

Nguyên tắc:

- Đây chưa phải backend nghiệp vụ đầy đủ.
- Có thể thay bằng backend thật mà vẫn giữ API composable ở client.
- Không đưa logic UI vào server routes.

---

## 17. Styling implementation

Tailwind core classes hiện tại nằm trong `app/assets/css/tailwind-core.css`.

Các class shell quan trọng:

- `.landing-page-shell`
- `.dashboard-page-shell`
- `.settings-page-shell`
- `.org-page-shell`
- `.content-page-shell`

Các class component quan trọng:

- `.header-shell`
- `.drawer-panel`
- `.chat-session-sidebar`
- `.workspace-chat-main`
- `.chat-composer`
- `.settings-shell`
- `.context-nav`
- `.context-organization-label`
- `.surface-card`
- `.btn-primary`
- `.btn-secondary`
- `.btn-dark`

Nguyên tắc:

- Style dùng lại nhiều lần thì đưa vào Tailwind core.
- Trang cụ thể có thể dùng utility class trực tiếp nếu không lặp lại.
- Không quay lại pattern `<style scoped>` cho UI phổ biến nếu Tailwind giải quyết được.

---

## 18. Current route constants

Route constants phải lấy từ `app/constants/navigation.ts`.

Các helper chính:

- `APP_ROUTES`
- `ORGANIZATION_ROUTE_SEGMENTS`
- `getOrganizationRoute(slug, segment)`
- `getContextChatRoute(slug)`
- `getAppNavigation(text)`
- `getSettingNavigation(text)`
- `getOrganizationNavigation(text)`

Không viết trực tiếp `/dashboard`, `/org`, `/setting/profile` trong file Vue nếu đó là điều hướng UI.

---

## 19. Quy tắc thêm file mới

Khi thêm tính năng:

- Route mới: thêm trong `app/pages`, cập nhật `APP_ROUTES` nếu route được điều hướng từ UI.
- UI dùng lại: thêm component trong `app/components`.
- Text UI: thêm vào `app/locales`.
- Permission mới: thêm vào `app/constants/rbac.ts`.
- Contract mới: thêm vào `app/types`.
- Form validation: thêm vào `app/schemas`.
- API call: thêm vào `app/composables/useApiX`.
- State dùng nhiều nơi: thêm hoặc mở rộng Pinia store.
- Pure helper: thêm vào `app/utils`.
- API mock/proxy: thêm vào `server/api`.

---

## 20. Kiểm tra build

Command chính:

```bash
npm run build
```

Lưu ý môi trường hiện tại:

- Build trong sandbox có thể lỗi `EPERM` khi Nuxt xoá cache trong `node_modules/.cache/nuxt/.nuxt`.
- Khi lỗi này xảy ra, chạy lại build ngoài sandbox để xác nhận source code.
- Các warning hiện tại thường là sourcemap warning của Nuxt module-preload và deprecation warning từ dependency.

---

## 21. Anti-patterns trong dự án này

Tránh:

- Hardcode route path trong Vue.
- Hardcode text UI trong Vue.
- Viết style scoped rời rạc cho pattern dùng chung.
- Dùng một layout shell cho mọi nhóm trang.
- Trộn public profile và private setting profile.
- Đưa nghiệp vụ RBAC trực tiếp vào từng page.
- Để popup riêng lẻ tự xử lý click-outside khác nhau.
- Gọi API thô trong component thay vì qua composable/store.

---

## 22. Nguyên tắc cuối

Dự án đang đi theo mô hình:

- `DESIGN.md` kiểm soát trải nghiệm giao diện.
- `PROJECT.md` kiểm soát tổ chức code theo stack hiện tại.
- `BUSINESS.md` kiểm soát nghiệp vụ và use case.

Khi code và tài liệu mâu thuẫn, cần xác định mâu thuẫn thuộc lớp nào trước khi sửa. Không dùng `PROJECT.md` để định nghĩa nghiệp vụ, và không dùng `BUSINESS.md` để ép cấu trúc folder.
