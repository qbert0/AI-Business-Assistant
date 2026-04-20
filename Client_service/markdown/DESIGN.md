# DESIGN.md

## 1. Vai trò tài liệu

`DESIGN.md` quy định ngôn ngữ giao diện dùng chung cho sản phẩm. Tài liệu này không phụ thuộc vào Nuxt, Vue, API, database hay logic nghiệp vụ cụ thể. Nếu một dự án khác dùng công nghệ khác nhưng muốn giữ cùng trải nghiệm người dùng, tài liệu này vẫn áp dụng được.

Tài liệu này trả lời các câu hỏi:

- Giao diện nên trông như thế nào?
- Bố cục các nhóm trang nên được tổ chức ra sao?
- Typography, màu sắc, khoảng cách, popup, sidebar, form, table, chat nên theo nguyên tắc nào?
- Các trạng thái loading, empty, error, permission-denied phải hiển thị thế nào?
- Text giao diện phải được quản lý ra sao để hỗ trợ đa ngôn ngữ?

Logic nghiệp vụ nằm trong `BUSINESS.md`. Cách triển khai bằng Nuxt, Tailwind, Pinia và server routes nằm trong `PROJECT.md`.

---

## 2. Hướng thị giác

Giao diện lấy cảm hứng từ Apple web: tối giản, nhiều khoảng thở, header mỏng, nền trung tính, CTA rõ, ít màu nhấn và ít hiệu ứng trang trí. Sản phẩm không dùng phong cách dashboard nặng, nhiều border, nhiều màu trạng thái hoặc các khối thông tin dày đặc.

Nguyên tắc chính:

- Ưu tiên nền trắng, đen và xám rất nhạt.
- Chỉ dùng một màu nhấn chính cho tương tác.
- Giữ chữ và khoảng cách gọn, dễ đọc trên màn hình laptop.
- Header và navigation phải chuyên nghiệp, nhỏ gọn, không chiếm nhiều chiều cao.
- Các khối lớn chỉ nên có một mục đích rõ ràng.
- Không dùng text mô tả thừa nếu tiêu đề đã đủ rõ.

---

## 3. Bảng màu

### Màu nền

| Vai trò | Màu | Ghi chú |
|---|---:|---|
| Nền sáng chính | `#ffffff` | Trang làm việc, form, bảng |
| Nền xám Apple | `#f5f5f7` | Card, panel, vùng phụ |
| Nền tối | `#000000` | Header, hero public, CTA tối |
| Text chính | `#1d1d1f` | Gần đen, dễ đọc hơn đen thuần |
| Text phụ | `rgba(0,0,0,0.8)` | Mô tả ngắn |
| Text mờ | `rgba(0,0,0,0.48)` | Caption, metadata |

### Màu tương tác

| Vai trò | Màu | Ghi chú |
|---|---:|---|
| Primary / focus | `#0071e3` | CTA chính, focus ring, link quan trọng |
| Hover primary | `#0066cc` | Trạng thái hover hoặc active |
| Badge nhẹ | `#fafafc` | Pill, chip, control phụ |

### Màu trạng thái

Màu trạng thái chỉ dùng khi cần phản hồi nghiệp vụ:

- Thành công: xanh lá.
- Cảnh báo: cam.
- Thông tin: xanh nhấn hoặc nền badge.
- Nguy hiểm: cam hoặc đỏ trầm, không dùng quá nhiều.

---

## 4. Typography

Giao diện phải hỗ trợ tiếng Việt tốt. Font cần có đủ glyph tiếng Việt và dấu không bị cắt.

Font đề xuất:

- Primary: `Inter`.
- Fallback tiếng Việt: `Noto Sans`.
- Fallback hệ thống: `-apple-system`, `system-ui`, `Segoe UI`, `Helvetica`, `Arial`, `sans-serif`.

### Thang chữ

| Vai trò | Kích thước | Line height | Cách dùng |
|---|---:|---:|---|
| Hero public | `clamp(2.75rem, 7vw, 4.5rem)` | 1.07 | Trang giới thiệu sản phẩm |
| Page title | `clamp(1.625rem, 2.5vw, 3rem)` | 1.12 | Tiêu đề trang |
| Panel title | `1.375rem` | 1.27 | Tiêu đề card/panel |
| Body | `1rem` | 1.5 | Nội dung chính |
| Caption | `0.875rem` | 1.43 | Bảng, metadata, menu |
| Micro | `0.75rem` | 1.33 | Kicker, badge, footnote |

Nguyên tắc:

- Không dùng chữ quá lớn trong trang làm việc.
- Chỉ dùng hero typography ở trang public hoặc các section giới thiệu.
- Không dùng nhiều cấp heading trong cùng một card.
- Không để text bị hardcode trong file giao diện nếu sản phẩm cần đa ngôn ngữ.

---

## 5. Spacing và Shell

Spacing nên gọn hơn dashboard truyền thống. Base unit là 4px và 8px.

Các shell chuẩn:

- Landing shell: full width, không padding mặc định, dùng cho trang giới thiệu.
- Dashboard shell: full width, không padding ngoài, ưu tiên chat workspace.
- Settings shell: có padding và max width để form dễ đọc.
- Organization shell: có padding vừa phải, max width rộng hơn settings.
- Content shell: fallback cho các trang nội dung thường.

Nguyên tắc:

- Trang chat không nên bị padding ngoài quá lớn.
- Trang setting cần padding để form không dính mép.
- Trang tổ chức cần đủ rộng cho bảng, card và navigation cấp hai.
- Khoảng cách giữa các section nên vừa phải, không tạo cảm giác hai trang bị tách quá xa.

---

## 6. Header toàn cục

Header là thanh định hướng chính của ứng dụng.

Yêu cầu:

- Cao khoảng 48px.
- Sticky ở trên cùng.
- Nền đen/translucent với blur nhẹ.
- Bên trái có nút mở navigation drawer.
- Có logo sản phẩm.
- Có tiêu đề trang hiện tại.
- Có search thu gọn, chỉ mở rộng khi người dùng focus hoặc nhập.
- Có notification icon.
- Có avatar người dùng mở popup tài khoản.

Search trong header:

- Mặc định nhỏ gọn.
- Khi focus thì mở rộng.
- Tìm theo từng ký tự nhập.
- Có gợi ý phổ biến khi chưa nhập.
- Có empty state khi không có kết quả.

Avatar menu:

- Avatar tạo màu theo tên người dùng.
- Menu chứa hồ sơ, cài đặt, tổ chức, đăng xuất và các hành động tài khoản.
- Không hiển thị role toàn cục cạnh avatar, vì role phụ thuộc vào từng tổ chức.

---

## 7. Navigation Drawer

Navigation drawer mở từ icon ở header.

Yêu cầu:

- Dính lề trái, cao full viewport.
- Không cần mô tả dài cho từng item.
- Nhóm đầu là điều hướng chính: trang chủ/dashboard và tổ chức.
- Có đường kẻ phân tách.
- Bên dưới là lịch sử chat.
- Tên chat dài phải dùng ellipsis.
- Có search chat.
- Có show more để mở rộng danh sách chat.

Drawer này là điều hướng toàn cục nhanh, không thay thế sidebar chat chuyên dụng trong trang chat.

---

## 8. Sidebar chat

Sidebar chat dùng cho dashboard cá nhân và trang chat tổ chức.

Yêu cầu:

- Hiển thị danh sách đoạn chat theo context hiện tại.
- Không hiển thị mô tả dài cho từng chat, chỉ hiện tên.
- Tên dài phải ellipsis.
- Có search chat.
- Có show more nếu danh sách dài.
- Có menu một nút cho mỗi chat.
- Menu chat gồm ghim, đổi tên, xóa.
- Nếu chat bị hạn chế quyền xóa, nút xóa phải disabled hoặc phản hồi rõ.

Trong dashboard cá nhân, phía trên sidebar có switcher đổi context:

- Personal.
- Tổ chức A.
- Tổ chức B.

Khi đổi context, lịch sử chat và nội dung chat phải đổi theo context đó.

---

## 9. Popup, modal và menu nổi

Tất cả popup/menu/modal dùng chung một hành vi:

- Mở từ trigger cụ thể.
- Đóng khi click ra ngoài.
- Đóng khi route hoặc context liên quan thay đổi nếu cần.
- Không để popup bị kẹt trên màn hình.
- Nội dung popup nhận qua slot hoặc children để tái sử dụng.

Các loại popup:

- Avatar menu.
- Search suggestions.
- Chat row actions.
- Employee row actions.
- Organization context switcher.
- Add employee modal.

---

## 10. Card, panel và block thông tin

Card nên dùng nền `#f5f5f7`, ít border, ít shadow.

Nguyên tắc:

- Nếu block có tên block và mô tả dài, chỉ giữ một trong hai khi nội dung bị trùng.
- Card chỉ nên chứa một nhóm thông tin.
- Action của card đặt gần thông tin mà action tác động.
- Không nhồi dashboard metrics, form và setting nguy hiểm vào cùng một card.

---

## 11. Form và input

Form phải rõ mục đích và gọn.

Yêu cầu:

- Label hoặc placeholder phải đến từ message catalog.
- Save và Cancel đặt cùng vùng.
- Lỗi hiển thị gần field gây lỗi.
- Destructive action tách khỏi action bình thường.
- Modal thêm nhân viên dùng form ngắn, không chuyển trang nếu tác vụ nhẹ.

---

## 12. Table và list

Bảng dùng cho dữ liệu có nhiều dòng như nhân viên, tài liệu, yêu cầu.

Yêu cầu:

- Có search/filter gần bảng.
- Có phân trang hoặc show more khi dữ liệu có thể lớn.
- Row action đặt ngay trên dòng.
- Các quyền hoặc trạng thái nên dùng chip/badge.
- Empty state phải nói rõ danh sách đang rỗng và hành động tiếp theo là gì.

---

## 13. Chat workspace

Chat workspace là vùng làm việc chính của sản phẩm.

Yêu cầu:

- Main chat area có thread scroll riêng.
- Composer/input phải sticky ở đáy khung chat.
- Khi người dùng scroll lên đọc lịch sử, input vẫn nằm dưới.
- Nếu chưa chọn chat, hiển thị empty state có gợi ý bắt đầu.
- Chỉ tạo chat history sau khi user gửi message đầu tiên.
- Câu trả lời nên hiển thị citations/source khi có.
- Có feedback cho câu trả lời.

---

## 14. Settings layout

Settings dùng bố cục riêng, không dùng layout chat/dashboard.

Yêu cầu:

- Có padding ngoài.
- Có sidebar nhóm cài đặt.
- Đầu sidebar có avatar, tên và email.
- Các nhóm setting gồm hồ sơ công khai, thanh toán, tổ chức, bảo mật.
- `/profile` là hồ sơ public.
- `/setting/profile` là màn hình private để chỉnh hồ sơ public.

---

## 15. Organization navigation

Trang tổ chức phải có navigation cấp hai.

Yêu cầu:

- Hiển thị tên tổ chức hiện tại như nhãn context.
- Nhãn tên tổ chức không phải link và không bấm được.
- Các tab chức năng gồm tổng quan, nhân viên, tài liệu, phân tích, chat, cài đặt.
- Navigation này nằm trong vùng content của tổ chức, không đặt trong header global.

---

## 16. Đa ngôn ngữ và message catalog

Không hardcode text giao diện trong file UI nếu text đó hiển thị cho người dùng.

Quy tắc:

- Text hiển thị nằm trong message catalog.
- Route path nằm trong route constants.
- Label navigation sinh từ message catalog.
- Placeholder, empty state, confirm message, menu label đều là message.
- Cho phép locale mặc định là tiếng Việt.
- Khi có backend i18n sau này, message catalog frontend có thể được thay bằng payload từ server.

Ngoại lệ hợp lý:

- Dữ liệu mock mô phỏng nội dung nghiệp vụ.
- ID kỹ thuật, route segment, permission key.
- Text chỉ dùng cho developer log hoặc type name.

---

## 17. Accessibility

Yêu cầu tối thiểu:

- Button thật dùng `<button>`.
- Link điều hướng dùng link thật.
- Focus visible rõ bằng màu nhấn.
- Menu/popup có thể đóng khi click ngoài.
- Hit target tối thiểu khoảng 32-44px tùy ngữ cảnh.
- Text tiếng Việt không bị cắt dấu.
- Không dùng màu làm tín hiệu duy nhất cho trạng thái.

---

## 18. Do và Don't

Do:

- Dùng nền trung tính, CTA rõ, ít màu.
- Tách dashboard, settings và organization shell theo mục đích.
- Giữ chat input sticky ở đáy.
- Dùng ellipsis cho tên chat dài.
- Đưa text UI vào message catalog.
- Đưa route path vào constants.

Don't:

- Không hardcode text UI trong nhiều file Vue.
- Không dùng một shell cho mọi trang.
- Không hiển thị role global cạnh avatar.
- Không trộn profile public với setting private.
- Không để sidebar chat chứa mô tả dài.
- Không để popup không thể đóng khi click ra ngoài.
