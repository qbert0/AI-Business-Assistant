# BUSINESS.md

## 1. Vai trò tài liệu

`BUSINESS.md` mô tả logic nghiệp vụ, vai trò người dùng và các kịch bản sử dụng của sản phẩm AI Business Assistant. Tài liệu này không quy định token màu, font, Tailwind class, folder code hay dependency kỹ thuật. Những phần đó nằm trong `DESIGN.md` và `PROJECT.md`.

Tài liệu này trả lời:

- Người dùng là ai?
- Họ dùng sản phẩm trong bối cảnh nào?
- Các use case chính là gì?
- Role và permission ảnh hưởng thế nào đến giao diện?
- Trang nào phục vụ nghiệp vụ nào?
- Luồng chat, tài liệu, nhân viên, tổ chức, phân tích và setting phải vận hành ra sao?

---

## 2. Mô tả sản phẩm

AI Business Assistant là hệ thống trợ lý tri thức cho doanh nghiệp. Người dùng có thể hỏi đáp với AI dựa trên tài liệu nội bộ của từng tổ chức. Tổ chức có thể quản lý nhân viên, tài liệu, pipeline xử lý tài liệu, phân quyền, dashboard phân tích và các cấu hình liên quan đến chatbot tư vấn.

Sản phẩm có hai không gian chính:

- Không gian cá nhân: người dùng đăng nhập, dùng chat chính, quản lý hồ sơ/cài đặt cá nhân, tạo hoặc tham gia tổ chức.
- Không gian tổ chức: người dùng làm việc trong một công ty cụ thể với quyền admin hoặc user/employee.

---

## 3. Actor chính

### 3.1 Guest

Guest là người chưa đăng nhập.

Guest có thể:

- Xem trang giới thiệu sản phẩm.
- Đi tới đăng nhập.
- Đi tới đăng ký.

Guest không được truy cập dashboard cá nhân, tổ chức, setting, notification hoặc chat nội bộ.

### 3.2 Personal User

Personal User là người đã đăng nhập nhưng chưa nhất thiết đang thao tác trong một tổ chức cụ thể.

Personal User có thể:

- Dùng dashboard chính.
- Chọn context chat cá nhân hoặc context tổ chức.
- Xem và sửa setting cá nhân.
- Xem hồ sơ public.
- Tạo công ty mới.
- Xem danh sách công ty đang tham gia hoặc quản trị.
- Gửi yêu cầu tham gia công ty.
- Xem thông báo.

### 3.3 Organization User / Employee

Organization User là người thuộc một tổ chức với quyền giới hạn.

Mặc định user có quyền:

- Chat tư vấn.
- Đọc tài liệu.

User có thể được cấp thêm quyền:

- Xem nhân viên.
- Upload tài liệu.
- Xem phân tích.
- Sửa hạn chế nội dung.
- Xóa đoạn chat.
- Truy cập cài đặt tổ chức.

### 3.4 Organization Admin

Organization Admin là người quản trị một tổ chức.

Admin có thể:

- Quản lý nhân viên.
- Thêm nhân viên theo email đã đăng ký.
- Xóa nhân viên.
- Đổi role nhân viên.
- Cấp hoặc thu hồi permission.
- Upload tài liệu.
- Theo dõi pipeline tài liệu.
- Xem analytics.
- Quản lý setting tổ chức.
- Quản lý RBAC.
- Dùng chat tổ chức.

---

## 4. Role và permission

Hệ thống hỗ trợ tối thiểu hai role:

- `admin`
- `user`

Permission nghiệp vụ hiện tại:

| Permission | Ý nghĩa |
|---|---|
| `access_org_settings` | Truy cập cài đặt tổ chức |
| `chat_advisory` | Dùng chat tư vấn |
| `read_documents` | Đọc tài liệu |
| `view_employees` | Xem danh sách nhân viên |
| `upload_documents` | Upload tài liệu |
| `view_analytics` | Xem phân tích |
| `edit_sensitive_restrictions` | Sửa hạn chế nội dung nhạy cảm |
| `delete_chat_sessions` | Xóa đoạn chat |

Default:

- `user`: `chat_advisory`, `read_documents`.
- `admin`: toàn bộ permission.

RBAC ở frontend chỉ dùng để điều hướng và hiển thị UI phù hợp. Backend vẫn phải là nơi bảo vệ dữ liệu thật.

---

## 5. Ngữ cảnh sử dụng

Người dùng luôn phải hiểu mình đang ở context nào:

- Public context.
- Personal context.
- Organization context.

Nếu đang ở organization context, UI phải hiển thị tên tổ chức hiện tại. Tên này là nhãn context, không phải nút điều hướng.

Chat history luôn phải lọc theo context:

- Personal context chỉ hiển thị chat cá nhân.
- Organization A chỉ hiển thị chat của Organization A.
- Organization B chỉ hiển thị chat của Organization B.

---

## 6. Use case: Xem trang giới thiệu sản phẩm

Actor: Guest.

Mục tiêu: hiểu sản phẩm và đi tới đăng nhập/đăng ký.

Luồng chính:

1. Guest mở `/`.
2. Hệ thống hiển thị hero giới thiệu AI Business Assistant.
3. Hệ thống mô tả giá trị: hỏi đáp dựa trên tài liệu, quản lý tri thức, hỗ trợ tổ chức.
4. Guest chọn đăng nhập hoặc đăng ký.

Kết quả:

- Guest chuyển sang auth flow.

---

## 7. Use case: Đăng nhập

Actor: Guest.

Mục tiêu: vào hệ thống với tài khoản đã có.

Luồng chính:

1. Guest mở `/auth/login`.
2. Guest nhập email và mật khẩu hoặc chọn provider xã hội nếu được hỗ trợ.
3. Hệ thống xác thực.
4. Nếu thành công, chuyển tới `/dashboard`.
5. Nếu thất bại, hiển thị lỗi gần form.

Quy tắc:

- User đã đăng nhập không nên ở lại login/register.
- Guest chưa đăng nhập không được vào route private.

---

## 8. Use case: Dùng dashboard chính

Actor: Personal User.

Mục tiêu: dùng khung chat chính sau khi đăng nhập.

Luồng chính:

1. User mở `/dashboard`.
2. Sidebar hiển thị context switcher.
3. User chọn personal hoặc một tổ chức.
4. Sidebar chat chỉ hiển thị đoạn chat của context đã chọn.
5. User chọn một đoạn chat hoặc bắt đầu chat mới.
6. Nội dung chat hiển thị ở vùng content.
7. Input chat luôn nằm dưới cùng khung chat.

Quy tắc:

- Nếu chưa chọn chat, hiển thị empty state để bắt đầu.
- Chat history item chỉ nên được tạo sau khi user gửi message đầu tiên.
- Chat row menu gồm ghim, đổi tên, xóa.
- Nếu không có quyền xóa, hành động xóa phải bị chặn rõ.

---

## 9. Use case: Quản lý danh sách tổ chức

Actor: Personal User.

Mục tiêu: xem công ty đang quản trị, công ty đang tham gia và yêu cầu tham gia.

Route: `/org`.

Luồng chính:

1. User mở `/org`.
2. Hệ thống hiển thị nhóm công ty user đang quản trị.
3. Hệ thống hiển thị nhóm công ty user đang tham gia.
4. Hệ thống hiển thị danh sách yêu cầu tham gia công ty.
5. User có thể tạo công ty mới.
6. User có thể gửi yêu cầu tham gia công ty.

Quy tắc:

- `/org` là trang nghiệp vụ quản lý tổ chức và yêu cầu tham gia.
- `/setting/organize` chỉ là setting cá nhân liên quan đến tổ chức mặc định/cách truy cập, không thay thế `/org`.

---

## 10. Use case: Tạo công ty mới

Actor: Personal User.

Mục tiêu: tạo tổ chức mới và trở thành admin của tổ chức đó.

Route: `/org/create`.

Luồng chính:

1. User nhập tên công ty.
2. User nhập ngành nghề.
3. User nhập mô tả ngắn.
4. Hệ thống tạo tổ chức.
5. User trở thành admin mặc định.
6. Hệ thống chuyển user vào trang tổ chức hoặc danh sách tổ chức.

Kết quả:

- Công ty mới có workspace riêng.
- Admin có quyền quản lý nhân viên, tài liệu, analytics, chat và setting.

---

## 11. Use case: Vào workspace tổ chức

Actor: Organization User hoặc Organization Admin.

Mục tiêu: thao tác trong một tổ chức cụ thể.

Route family:

- `/org/[id]/dashboard`
- `/org/[id]/employees`
- `/org/[id]/documents`
- `/org/[id]/analytics`
- `/org/[id]/chat`
- `/org/[id]/settings`

Luồng chính:

1. User chọn một tổ chức.
2. Hệ thống mở trang tổng quan tổ chức.
3. Organization navigation hiển thị tên tổ chức và các tab chức năng.
4. User chuyển tab theo quyền được cấp.
5. Nếu thiếu quyền, hệ thống đưa tới trang permission-denied hoặc ẩn/disable hành động phù hợp.

---

## 12. Use case: Xem tổng quan tổ chức

Actor: Organization User hoặc Admin.

Mục tiêu: hiểu nhanh tình trạng tổ chức.

Route: `/org/[id]/dashboard`.

Nội dung:

- Tên tổ chức.
- Ngành nghề.
- Mô tả.
- Số nhân viên.
- Số tài liệu.
- Lượt truy cập.
- Câu hỏi phổ biến.
- Câu hỏi gợi ý.

Quy tắc:

- Đây là overview, không phải analytics chuyên sâu.
- Các action chính dẫn tới nhân viên, tài liệu và chat.

---

## 13. Use case: Quản lý nhân viên

Actor: Organization Admin hoặc user có quyền `view_employees`.

Mục tiêu: xem và quản lý nhân viên trong công ty.

Route: `/org/[id]/employees`.

Luồng chính:

1. Admin mở trang nhân viên.
2. Hệ thống hiển thị danh sách nhân viên.
3. Admin tìm nhân viên theo tên hoặc email.
4. Admin mở popup thêm nhân viên.
5. Admin tìm email đã đăng ký.
6. Admin chọn role và permission.
7. Hệ thống thêm nhân viên ở trạng thái invited hoặc active theo backend.

Row actions:

- Xóa nhân viên.
- Đổi role.
- Chỉnh permission.

Quy tắc:

- Danh sách phải có phân trang hoặc cơ chế giới hạn khi dữ liệu lớn.
- Hành động theo dòng phải nằm gần dòng.
- Xóa nhân viên cần xác nhận.
- Permission mặc định của user chỉ gồm chat tư vấn và đọc tài liệu.

---

## 14. Use case: Upload và xử lý tài liệu

Actor: Organization Admin hoặc user có quyền `upload_documents`.

Mục tiêu: đưa tài liệu vào hệ tri thức của tổ chức.

Route: `/org/[id]/documents`.

Luồng nghiệp vụ:

1. User upload tài liệu.
2. Hệ thống lưu tài liệu gốc.
3. Hệ thống lưu source link và metadata.
4. Hệ thống chunking tài liệu thành các phần nhỏ hơn.
5. Hệ thống embedding các chunk.
6. Hệ thống ghi vector vào Vector DB/Elasticsearch.
7. Hệ thống liên kết tài liệu gốc với record đã xử lý trong DB.
8. Chatbot có thể retrieval tới Elasticsearch để lấy tài liệu liên quan.

UI cần hiển thị:

- Form upload.
- Danh sách tài liệu.
- Trạng thái pipeline.
- Số chunk.
- Embedding model.
- Vector index.
- Link tài liệu gốc.
- Cây tài liệu hoặc vùng tổ chức tài liệu.

---

## 15. Use case: Thiết kế pipeline Multi-Agent

Actor: Organization Admin.

Mục tiêu: mô tả và vận hành pipeline AI từ tài liệu tới câu trả lời.

Pipeline logic:

1. Agent ingest nhận tài liệu và metadata.
2. Agent chunking chia tài liệu theo block phù hợp.
3. Agent embedding tạo vector.
4. Agent indexing ghi dữ liệu vào Elasticsearch.
5. Agent retrieval lấy top-k tài liệu liên quan.
6. Agent rerank sắp xếp lại tài liệu.
7. Agent answer generation tạo câu trả lời.
8. Agent citation gắn nguồn để user kiểm chứng.

UI hiện tại thể hiện pipeline trong trang tài liệu và route legacy pipeline. Về nghiệp vụ, pipeline là phần thuộc tổ chức và liên quan trực tiếp tới tài liệu/chat.

---

## 16. Use case: Chat tư vấn tổ chức

Actor: Organization User hoặc Admin có quyền `chat_advisory`.

Mục tiêu: hỏi đáp dựa trên tài liệu nội bộ của tổ chức.

Route: `/org/[id]/chat`.

Luồng chính:

1. User mở chat tổ chức.
2. Hệ thống chỉ hiển thị lịch sử chat của tổ chức đó.
3. User chọn chat cũ hoặc nhập câu hỏi mới.
4. Backend retrieval tài liệu liên quan từ Elasticsearch.
5. Backend rerank tài liệu.
6. Backend tạo câu trả lời có thể kèm citation.
7. User gửi feedback tốt hoặc cần cải thiện.

Quy tắc:

- Chat không được trộn giữa các tổ chức.
- Input phải luôn ở đáy khung chat.
- Suggested questions hỗ trợ user bắt đầu nhanh.
- Nếu câu trả lời thiếu nguồn hoặc thiếu độ tin cậy, UI nên thể hiện thận trọng.

---

## 17. Use case: Gợi ý câu hỏi cho employee

Actor: Organization User.

Mục tiêu: giúp employee bắt đầu hỏi đúng phạm vi.

Nội dung gợi ý có thể bao gồm:

- Thu nhập.
- Phúc lợi.
- Quy trình nội bộ.
- Chính sách nghỉ phép.
- Hướng dẫn sử dụng tài liệu.

Quy tắc:

- Gợi ý phải theo context tổ chức.
- Click gợi ý sẽ đưa câu hỏi vào chat hoặc gửi câu hỏi theo thiết kế UI hiện tại.

---

## 18. Use case: Feedback câu trả lời

Actor: Organization User hoặc Personal User.

Mục tiêu: phản hồi chất lượng câu trả lời để cải thiện hệ thống.

Luồng chính:

1. User nhận câu trả lời.
2. User chọn phản hồi tích cực hoặc tiêu cực.
3. User có thể nhập nhận xét ngắn.
4. Hệ thống lưu feedback theo context chat và tổ chức.

Quy tắc:

- Feedback phải nằm gần câu trả lời hoặc vùng chat.
- Không bắt user rời khỏi chat để phản hồi.

---

## 19. Use case: Dashboard phân tích công ty

Actor: Organization Admin hoặc user có quyền `view_analytics`.

Mục tiêu: xem tình hình sử dụng và câu hỏi phổ biến.

Route: `/org/[id]/analytics`.

Nội dung:

- Số lượt truy cập.
- Số nhân viên.
- Số tài liệu đã index.
- Câu hỏi phổ biến.
- Vùng nhập mô tả nội dung nhạy cảm nhân viên không nên hỏi.

Quy tắc:

- Analytics và policy restriction phải tách block rõ.
- Restriction text là cấu hình nghiệp vụ, không chỉ là ghi chú.
- Nếu user thiếu quyền chỉnh restriction, UI phải disable hoặc ẩn action chỉnh.

---

## 20. Use case: Cài đặt tổ chức

Actor: Organization Admin hoặc user có quyền `access_org_settings`.

Mục tiêu: quản lý định danh, thanh toán, RBAC và vùng nguy hiểm của tổ chức.

Route: `/org/[id]/settings`.

Nội dung:

- Đổi tên tổ chức.
- Thanh toán tổ chức.
- Vai trò và quyền.
- Tạo role mới.
- Cấu hình permission theo role.
- Xóa tổ chức.

Quy tắc:

- Vùng nguy hiểm phải tách riêng.
- Xóa tổ chức cần confirm.
- Role là bundle permission, không chỉ là label.

---

## 21. Use case: Cài đặt cá nhân

Actor: Personal User.

Mục tiêu: quản lý tài khoản cá nhân.

Route family:

- `/setting/profile`
- `/setting/payment`
- `/setting/organize`
- `/setting/authen`

Nội dung:

- Hồ sơ công khai.
- Thanh toán cá nhân.
- Tổ chức mặc định và quyền truy cập cá nhân.
- Đăng nhập và bảo mật.

Quy tắc:

- `/profile` là trang public cho người khác xem.
- `/setting/profile` là trang private để chỉnh hồ sơ public.
- Setting dùng layout riêng có sidebar và padding.

---

## 22. Use case: Thông báo

Actor: Personal User.

Mục tiêu: xem các sự kiện cần chú ý và đi tới đúng khu vực xử lý.

Route: `/notifications`.

Ví dụ thông báo:

- Tài liệu đã index xong.
- Yêu cầu tham gia đã được duyệt.
- Có sự kiện liên quan tới tổ chức.

Quy tắc:

- Notification phải có link tới vùng liên quan nếu có.
- Notification không chỉ để đọc, mà phải hỗ trợ hành động tiếp theo.

---

## 23. Search nghiệp vụ

Search hiện tại có hai nhóm chính:

### 23.1 Search tổ chức

Vị trí: header.

Tìm theo:

- Mã tổ chức.
- Tên tổ chức.
- Ngành nghề hoặc mô tả nếu cần.

Search phải gợi ý khi user nhập từng ký tự.

### 23.2 Search nhân viên

Vị trí: trang nhân viên hoặc popup thêm nhân viên.

Tìm theo:

- Email đã đăng ký.
- Tên nhân viên nếu danh sách đã có.

Mục tiêu nghiệp vụ là tránh thêm nhân viên không tồn tại trong hệ thống tài khoản.

---

## 24. Permission matrix UI

| Chức năng | Guest | Personal User | Org User mặc định | Org Admin |
|---|---|---|---|---|
| Trang giới thiệu | Có | Có thể bỏ qua | Có thể bỏ qua | Có thể bỏ qua |
| Login/Register | Có | Không cần | Không cần | Không cần |
| Dashboard chat | Không | Có | Có | Có |
| Hồ sơ public | Có thể xem nếu public | Có | Có | Có |
| Setting cá nhân | Không | Có | Có | Có |
| Danh sách tổ chức `/org` | Không | Có | Có | Có |
| Tạo tổ chức | Không | Có | Có | Có |
| Gửi yêu cầu tham gia | Không | Có | Có | Có |
| Tổng quan tổ chức | Không | Không | Có nếu thuộc tổ chức | Có |
| Chat tổ chức | Không | Không | Có nếu có `chat_advisory` | Có |
| Đọc tài liệu | Không | Không | Có nếu có `read_documents` | Có |
| Upload tài liệu | Không | Không | Nếu được cấp | Có |
| Nhân viên | Không | Không | Nếu được cấp | Có |
| Analytics | Không | Không | Nếu được cấp | Có |
| Cài đặt tổ chức | Không | Không | Nếu được cấp | Có |
| RBAC | Không | Không | Không mặc định | Có |

---

## 25. Trạng thái giao diện bắt buộc

Mỗi use case nên có trạng thái phù hợp:

- `initial`: trước khi user nhập hoặc chọn.
- `loading`: đang gọi API.
- `empty`: không có dữ liệu.
- `ready`: có dữ liệu và có thể thao tác.
- `success`: thao tác hoàn tất.
- `error`: thao tác lỗi.
- `permission-denied`: user không có quyền.

Empty state cần trả lời:

- Đây là khu vực gì?
- Vì sao đang trống?
- User có thể làm gì tiếp?

---

## 26. Quy tắc tránh lỗi nghiệp vụ

Không được:

- Trộn chat của nhiều tổ chức.
- Tạo chat history khi user chưa gửi message.
- Coi role global là role của mọi tổ chức.
- Gộp `/profile` và `/setting/profile`.
- Dùng `/setting/organize` thay cho `/org`.
- Cho employee mặc định quyền upload hoặc analytics nếu chưa được cấp.
- Để action xóa chat hoạt động khi chat bị hạn chế xóa.
- Để user thiếu quyền vào trang tổ chức mà không có phản hồi rõ.

---

## 27. Nguyên tắc cuối

Mỗi màn hình nghiệp vụ phải giúp user trả lời nhanh:

- Tôi đang ở cá nhân hay tổ chức?
- Nếu là tổ chức, đó là tổ chức nào?
- Tôi có quyền gì ở đây?
- Dữ liệu tôi đang xem thuộc context nào?
- Hành động chính tiếp theo là gì?

Nếu user không trả lời được các câu hỏi này, luồng nghiệp vụ chưa đạt yêu cầu dù giao diện có đẹp.
