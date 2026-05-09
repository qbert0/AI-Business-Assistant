# BUSINESS.md

## 1. Vai trò tài liệu

`BUSINESS.md` là tài liệu đặc tả cho AI Business Assistant theo hai trục:

- Đặc tả nghiệp vụ: hệ thống phải phục vụ ai, giải quyết bài toán gì, các use case nào phải chạy đúng, quyền nào chi phối hành vi nào.
- Kiến trúc thiết kế giao diện: người dùng nhìn thấy bố cục nào, đi theo route nào, component nào phối hợp với nhau để hoàn thành nghiệp vụ.

Tài liệu này không đi vào màu sắc, font, token thiết kế, class CSS hay cấu trúc source code kỹ thuật.

---

## 2. Mục tiêu hệ thống

AI Business Assistant là hệ thống trợ lý AI theo ngữ cảnh cá nhân và tổ chức.

Hệ thống phải đáp ứng các mục tiêu sau:

- Cho phép người dùng đăng nhập và làm việc bằng tài khoản cá nhân.
- Cho phép người dùng tạo tổ chức, tham gia tổ chức và chuyển đổi giữa các workspace.
- Cho phép người dùng chat với AI trong hai ngữ cảnh tách biệt: cá nhân và tổ chức.
- Cho phép tổ chức quản lý tài liệu nội bộ để AI có thể trả lời dựa trên tri thức của tổ chức.
- Cho phép tổ chức quản lý nhân viên, vai trò và quyền truy cập theo RBAC.
- Cho phép admin theo dõi thông báo, thanh toán, phân tích sử dụng và các cài đặt vận hành.

Một nguyên tắc cốt lõi của hệ thống là mọi dữ liệu và hành động phải luôn gắn với đúng ngữ cảnh:

- Ngữ cảnh công khai.
- Ngữ cảnh cá nhân.
- Ngữ cảnh tổ chức.

Không được trộn dữ liệu giữa các ngữ cảnh này.

---

## 3. Phạm vi route chính

### 3.1 Route cá nhân

- `/dashboard`
- `/setting/profile`
- `/setting/payment`
- `/setting/organize`
- `/setting/authen`
- `/notifications`
- `/profile`

### 3.2 Route tổ chức tổng quát

- `/org/search/[id]`: `id` là tên công ty mà người dùng tìm kiếm.
- `/org/create`
- `/org`

### 3.3 Route workspace tổ chức

Toàn bộ route của workspace tổ chức phải bắt đầu bằng `/org/[id]`, trong đó `id` là mã định danh của tổ chức.

- `/org/[id]`
- `/org/[id]/dashboard`
- `/org/[id]/employees`
- `/org/[id]/documents`
- `/org/[id]/analytics`
- `/org/[id]/settings`
- `/org/[id]/chat`

Quy ước:

- `/org/[id]` là route gốc của một tổ chức, có thể điều hướng mặc định sang `/org/[id]/dashboard`.
- Chat tổ chức chỉ được vận hành trong `/org/[id]/chat`.
- Mọi dữ liệu thuộc tổ chức phải truy xuất theo `orgId`, không theo trạng thái chọn tạm thời ở frontend.

---

## 4. Xác thực và ngữ cảnh truy cập

Sau khi người dùng đăng nhập thành công, server phát hành token cho client. Token này do server tự sinh, dùng JWT để xác thực các request tiếp theo.

Các nguyên tắc nghiệp vụ liên quan:

- Guest không có token thì không được vào route riêng tư.
- Personal User có token thì được vào khu vực cá nhân.
- Khi truy cập workspace tổ chức, backend phải xác minh người dùng có thuộc tổ chức đó hay không.
- Quyền hiển thị ở frontend chỉ là lớp hướng dẫn giao diện; backend vẫn phải là nơi chặn truy cập thật.

Frontend phải luôn xác định rõ:

- Người dùng đã đăng nhập hay chưa.
- Workspace hiện tại là cá nhân hay tổ chức.
- Nếu là tổ chức thì đang là tổ chức nào.
- Người dùng có những quyền nào trong workspace hiện tại.

---

## 5. Actor hệ thống

### 5.1 Guest

Guest là người chưa đăng nhập.

Guest có thể:

- Xem trang giới thiệu.
- Đăng nhập hoặc đăng ký.
- Xem hồ sơ public nếu hồ sơ được công khai.

Guest không thể:

- Vào dashboard.
- Vào route setting.
- Vào thông báo.
- Vào bất kỳ workspace tổ chức nào.

### 5.2 Personal User

Personal User là người đã đăng nhập và đang thao tác bằng không gian cá nhân.

Personal User có thể:

- Dùng chat cá nhân.
- Xem hồ sơ cá nhân và chỉnh setting.
- Nhận thông báo.
- Tạo tổ chức.
- Xem danh sách tổ chức đã tham gia.
- Tìm tổ chức để gửi yêu cầu tham gia.
- Chuyển sang workspace của tổ chức mà mình thuộc về.

### 5.3 Org User

Org User là thành viên của một tổ chức, nhưng không mặc định có quyền quản trị.

Org User mặc định có thể:

- Vào tổng quan tổ chức nếu thuộc tổ chức.
- Chat tổ chức nếu có `chat_advisory`.
- Đọc tài liệu nếu có `read_documents`.

Org User có thể được cấp thêm quyền:

- Upload tài liệu.
- Xem danh sách nhân viên.
- Xem analytics.
- Truy cập setting tổ chức.

### 5.4 Org Admin

Org Admin là quản trị viên của tổ chức.

Org Admin có thể:

- Quản lý toàn bộ workspace tổ chức.
- Quản lý nhân viên.
- Quản lý vai trò và quyền.
- Quản lý tài liệu.
- Xem analytics.
- Quản lý thanh toán và cấu hình tổ chức.
- Nhận thông báo quản trị như thành viên mới hoặc hạn gói sắp hết.

---

## 6. Mô hình quyền và RBAC

Hệ thống phải hỗ trợ RBAC theo tổ chức, không dùng chung role giữa mọi tổ chức.

### 6.1 Vai trò mặc định

Khi chưa có cấu hình tùy chỉnh, hệ thống có tối thiểu 3 vai trò:

- `guest`
- `employee`
- `admin`

`guest` trong ngữ cảnh tổ chức là vai trò cực thấp hoặc tạm thời nếu hệ thống dùng cho lời mời/chờ cấp quyền.

### 6.2 Vai trò tùy chỉnh

Admin có thể tạo vai trò mới trong `permission-assign` bằng cách chọn một tổ hợp quyền từ permission matrix rồi đặt tên cho tổ hợp đó.

Mỗi vai trò tùy chỉnh gồm:

- Tên vai trò.
- Mô tả ngắn nếu có.
- Tập quyền đi kèm.

### 6.3 Permission matrix

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

### 6.4 Tập quyền nghiệp vụ đề xuất

- `chat_advisory`
- `read_documents`
- `upload_documents`
- `view_employees`
- `manage_employees`
- `view_analytics`
- `access_org_settings`
- `manage_roles_permissions`
- `manage_billing`

Nguyên tắc:

- `employee` mặc định không có toàn quyền.
- `admin` có toàn bộ quyền.
- Quyền phải được kiểm tra theo từng tổ chức.

---

## 7. Đặc tả nghiệp vụ

### 7.1 Nghiệp vụ đăng nhập và khởi tạo phiên làm việc

Mục tiêu:

- Xác thực người dùng.
- Nhận JWT từ server.
- Mở phiên làm việc cá nhân mặc định.

Luồng chính:

1. Người dùng đăng nhập.
2. Server xác thực và sinh JWT.
3. Client lưu trạng thái phiên làm việc.
4. Hệ thống chuyển người dùng tới `/dashboard`.

Kết quả mong đợi:

- Người dùng vào được khu vực riêng tư.
- Workspace mặc định là tài khoản cá nhân nếu chưa chọn tổ chức.

### 7.2 Nghiệp vụ chat cá nhân

Route: `/dashboard`

Mục tiêu:

- Cho phép người dùng trao đổi với AI trong phạm vi tài khoản cá nhân.

Luồng chính:

1. Người dùng vào dashboard.
2. Hệ thống hiển thị lịch sử chat cá nhân.
3. Người dùng chọn cuộc chat cũ hoặc bắt đầu chat mới.
4. Người dùng gửi tin nhắn, hình ảnh hoặc file PDF.
5. Hệ thống trả lời trong cùng cuộc hội thoại.

Quy tắc:

- Chat history cá nhân không được trộn với chat tổ chức.
- Một phiên chat chỉ nên được tạo khi có tin nhắn đầu tiên.
- Người dùng có thể xem lại các cuộc chat cũ.

### 7.3 Nghiệp vụ chuyển workspace

Mục tiêu:

- Cho phép người dùng chuyển nhanh giữa tài khoản cá nhân và các tổ chức đã tham gia.

Luồng chính:

1. Người dùng mở bộ chọn workspace.
2. Hệ thống hiển thị tài khoản cá nhân, danh sách tổ chức, nút tạo tổ chức và nút quản lý tổ chức.
3. Người dùng chọn một tổ chức.
4. Hệ thống chuyển sang workspace tương ứng.
5. Route chat của tổ chức được mở tại `/org/[id]/chat`.

Kết quả mong đợi:

- Toàn bộ sidebar, lịch sử chat và quyền hiển thị phải đổi theo workspace mới.

### 7.4 Nghiệp vụ tìm kiếm và tham gia tổ chức

Route:

- `/org`
- `/org/search/[id]`

Mục tiêu:

- Cho phép người dùng tìm công ty theo tên và gửi yêu cầu tham gia.

Luồng chính:

1. Người dùng vào `/org` hoặc search từ giao diện.
2. Hệ thống điều hướng tới `/org/search/[id]`.
3. Hệ thống hiển thị kết quả theo tên công ty.
4. Người dùng xem thông tin và gửi yêu cầu tham gia nếu phù hợp.

### 7.5 Nghiệp vụ tạo tổ chức

Route: `/org/create`

Mục tiêu:

- Tạo một tổ chức mới và khởi tạo workspace ban đầu.

Luồng chính:

1. Người dùng nhập thông tin cơ bản của tổ chức.
2. Người dùng chọn dùng mặc định hoặc cấu hình ban đầu.
3. Hệ thống tạo tổ chức.
4. Người dùng trở thành `admin` mặc định của tổ chức đó.
5. Hệ thống điều hướng sang workspace tổ chức.

### 7.6 Nghiệp vụ xem danh sách tổ chức

Route: `/org`

Mục tiêu:

- Hiển thị danh sách tổ chức người dùng đang tham gia hoặc quản trị.

Nội dung phải có:

- Các tổ chức đang tham gia.
- Các tổ chức đang quản lý nếu có phân biệt.
- Trạng thái lời mời hoặc yêu cầu tham gia.
- Hành động tạo tổ chức mới.
- Hành động đi tới trang tổ chức.

### 7.7 Nghiệp vụ tổng quan tổ chức

Route: `/org/[id]/dashboard`

Mục tiêu:

- Cho người dùng thấy nhanh trạng thái vận hành của một tổ chức.

Nội dung nghiệp vụ có thể gồm:

- Thông tin cơ bản của tổ chức.
- Số lượng nhân viên.
- Số lượng tài liệu.
- Tình trạng hoạt động gần đây.
- Các chỉ số hoặc liên kết nhanh sang chat, documents, employees, analytics.

### 7.8 Nghiệp vụ chat tổ chức

Route: `/org/[id]/chat`

Mục tiêu:

- Cho phép thành viên hỏi AI trong phạm vi tri thức của tổ chức.

Luồng chính:

1. Người dùng mở workspace tổ chức.
2. Hệ thống hiển thị lịch sử chat của đúng tổ chức đó.
3. Người dùng gửi câu hỏi.
4. Hệ thống dùng tri thức và tài liệu của tổ chức để trả lời.

Quy tắc:

- Không được trộn chat giữa các tổ chức.
- Chỉ người có `chat_advisory` mới được dùng.
- Lịch sử chat phải được cô lập theo `orgId`.

### 7.9 Nghiệp vụ quản lý tài liệu

Route: `/org/[id]/documents`

Mục tiêu:

- Quản lý cây tài liệu và mở tài liệu để xem nội dung.

Luồng chính:

1. Người dùng mở cây tài liệu.
2. Người dùng duyệt folder hoặc file.
3. Người dùng chọn một file.
4. Hệ thống mở file ở vùng xem tài liệu mà không đổi route.

Quy tắc:

- Folder có thể chứa folder và file.
- File hỗ trợ: `pdf`, `png`, `excel`, `word`, `doc`, `txt`, `md`, `jpg`.
- Với folder: được thêm folder con, thêm file, đổi tên, xóa.
- Với file: được đổi tên, xóa, tải xuống.
- Hệ thống phải giữ được nhiều tài liệu đang mở đồng thời theo dạng tab điều hướng.

### 7.10 Nghiệp vụ quản lý nhân viên

Route: `/org/[id]/employees`

Mục tiêu:

- Quản lý danh sách thành viên và vai trò trong tổ chức.

Luồng chính:

1. Người dùng có quyền mở danh sách nhân viên.
2. Hệ thống hiển thị 4 cột: tên, email, vai trò, nút chức năng.
3. Người dùng mở menu chức năng trên từng dòng.
4. Người dùng có thể xóa nhân viên hoặc đổi vai trò.
5. Khi đổi vai trò, hệ thống hiển thị danh sách vai trò hiện có để chọn.

Quy tắc:

- Admin luôn có thể quản lý.
- Người không có quyền thì không thấy hoặc không thao tác được.
- Xóa nhân viên cần xác nhận.

### 7.11 Nghiệp vụ phân quyền

Thành phần chính: `permission-assign`

Mục tiêu:

- Cho phép admin định nghĩa vai trò theo permission matrix.

Luồng chính:

1. Admin mở khu vực phân quyền.
2. Admin chọn các quyền trong ma trận.
3. Admin đặt tên vai trò.
4. Hệ thống lưu vai trò.
5. Vai trò mới xuất hiện trong danh sách để gán cho nhân viên.

Kết quả mong đợi:

- Tổ chức có thể vận hành RBAC linh hoạt thay vì chỉ dùng vai trò cứng.

### 7.12 Nghiệp vụ analytics

Route: `/org/[id]/analytics`

Mục tiêu:

- Cho phép tổ chức theo dõi hành vi sử dụng và dữ liệu hoạt động.

Ví dụ nội dung:

- Lượt sử dụng.
- Số tài liệu.
- Câu hỏi phổ biến.
- Tăng trưởng sử dụng theo thời gian.

### 7.13 Nghiệp vụ setting cá nhân

Route:

- `/setting/profile`
- `/setting/payment`
- `/setting/organize`
- `/setting/authen`

Mục tiêu:

- Cho phép người dùng quản lý thông tin tài khoản cá nhân.

Phân tách:

- `profile`: chỉnh hồ sơ cá nhân.
- `payment`: thông tin thanh toán cá nhân.
- `organize`: các cấu hình liên quan đến tổ chức từ góc nhìn cá nhân.
- `authen`: bảo mật, mật khẩu, xác thực.

### 7.14 Nghiệp vụ setting tổ chức

Route: `/org/[id]/settings`

Mục tiêu:

- Cho phép admin hoặc người có quyền cấu hình các thiết lập của tổ chức.

Nội dung có thể bao gồm:

- Hồ sơ tổ chức.
- Thanh toán tổ chức.
- Vai trò và quyền.
- Khu vực thao tác nguy hiểm.

### 7.15 Nghiệp vụ hồ sơ public

Route: `/profile`

Mục tiêu:

- Hiển thị thông tin công khai của người dùng.

Quy tắc:

- Đây là trang xem hồ sơ.
- Không đồng nhất với `/setting/profile`, là trang chỉnh sửa riêng tư.

### 7.16 Nghiệp vụ thông báo

Route: `/notifications`

Mục tiêu:

- Hiển thị các thông báo có thể dẫn người dùng tới hành động tiếp theo.

Thông báo bao gồm:

- Thanh toán thành công.
- Hạn sử dụng còn dưới 5 ngày.
- Thành viên mới được thêm vào tổ chức, dành cho admin.

Nguyên tắc:

- Thông báo không chỉ để đọc mà còn phải có điểm đến hoặc hành động phù hợp.

---

## 8. Kiến trúc thiết kế giao diện

Phần này mô tả cách tổ chức màn hình để người dùng thực hiện nghiệp vụ, không phải mô tả logic backend.

### 8.1 Nguyên tắc bố cục chung

Mọi màn hình phải giúp người dùng nhận biết ngay:

- Mình đang ở tài khoản cá nhân hay tổ chức.
- Nếu là tổ chức thì là tổ chức nào.
- Khu vực này dùng để làm gì.
- Hành động chính tiếp theo là gì.

Giao diện nên tổ chức theo 3 lớp nhận thức:

1. Lớp ngữ cảnh: workspace hiện tại, avatar, notification, tên tổ chức.
2. Lớp điều hướng: sidebar hoặc navigation-horizon.
3. Lớp nội dung thao tác: chat, form, danh sách, tài liệu, cài đặt.

### 8.2 Cụm component `sidebar - form-chat - checkout-org`

#### `sidebar`

`sidebar` là khung điều hướng chính của khu vực chat.

Chứa:

- `checkout-org`
- Danh sách `sidebaritem`
- Nút tạo chat mới nếu có

`sidebaritem` đại diện cho một cuộc chat thuộc workspace đang chọn.

Mỗi `sidebaritem` có:

- Tên cuộc chat
- Trạng thái đang chọn
- Nút ba chấm để mở popup chức năng

Popup chức năng gồm:

- Xóa
- Đổi tên

Quy tắc giao diện:

- Danh sách phải lọc theo workspace hiện tại.
- Khi đổi workspace thì danh sách phải thay đổi tương ứng.
- Nếu chưa có cuộc chat nào thì sidebar vẫn phải giải thích được người dùng cần làm gì tiếp theo.

#### `checkout-org`

`checkout-org` là bộ chọn workspace.

Trạng thái mặc định:

- Người dùng ở tài khoản cá nhân khi vừa vào hệ thống.

Khi người dùng bấm vào:

- Mở popup chứa danh sách tổ chức đã tham gia.
- Hiển thị 2 nút:
  - Tạo tổ chức mới.
  - Quản lý tổ chức.

Điều hướng:

- Tạo tổ chức mới sang `/org/create`
- Quản lý tổ chức sang `/org`
- Chọn một tổ chức thì chuyển sang workspace tổ chức tương ứng, thường vào `/org/[id]/chat`

#### `form-chat`

`form-chat` là vùng trò chuyện với AI.

Bao gồm:

- Khu vực hiển thị lịch sử tin nhắn của cuộc chat đang mở
- Vùng xem lại nội dung cũ trong cùng cuộc chat
- Nút gửi hình ảnh
- Nút gửi file PDF
- Ô nhập tin nhắn
- Nút gửi tin nhắn

Quy tắc giao diện:

- Ô nhập luôn nằm ở phần dưới cùng của khung chat.
- Khi chưa có cuộc trò chuyện, hiển thị empty state.
- Phải hỗ trợ xem lại lịch sử tin nhắn của cuộc chat cũ tương tự trải nghiệm message.

### 8.3 Cụm component `tree-document - content-document`

#### `tree-document`

`tree-document` là vùng duyệt thư mục và file theo cấu trúc cây.

Mỗi item có thể là:

- Folder
- File

Folder có thể chứa:

- Folder con
- File

Các định dạng file:

- PDF
- PNG
- Excel
- Word
- DOC
- TXT
- MD
- JPG

Menu chức năng theo item:

- Xóa
- Đổi tên
- Thêm file
- Thêm folder, chỉ với folder
- Tải xuống, chỉ với file

#### `content-document`

`content-document` là vùng hiển thị nội dung tài liệu đang mở.

Khi người dùng bấm vào file trong `tree-document`:

- Tài liệu tương ứng mở trong `content-document`.
- Route hiện tại giữ nguyên.

Khi có nhiều tài liệu mở:

- Hiển thị dạng navigation/tab để chuyển nhanh giữa các tài liệu.

Mục tiêu bố cục:

- Bên trái là cây tài liệu.
- Bên phải là vùng nội dung và tab tài liệu đang mở.

### 8.4 Cụm component `list-employee - permission-assign`

#### `list-employee`

`list-employee` hiển thị danh sách nhân viên trong tổ chức.

4 cột chính:

- Tên
- Email
- Vai trò
- Nút chức năng

Popup chức năng theo dòng:

- Xóa nhân viên
- Đổi vai trò

Khi bấm đổi vai trò:

- Hiện danh sách vai trò hiện hữu để chọn.

#### `permission-assign`

`permission-assign` là khu vực tạo và quản lý vai trò.

Chức năng:

- Tạo vai trò mới từ tổ hợp quyền trong permission matrix
- Đặt tên vai trò
- Dùng vai trò đó để gán cho nhân viên

Khi chưa có cấu hình tùy chỉnh:

- Hệ thống dùng 3 vai trò mặc định: `guest`, `employee`, `admin`

### 8.5 Cụm component `navigation-horizon - content-horizon`

Đây là cặp component dùng cho các màn hình cài đặt cá nhân hoặc tổ chức.

#### `navigation-horizon`

Vai trò:

- Chuyển tab theo chiều dọc giữa các phần cài đặt.

Ví dụ:

- Profile
- Payment
- Organize
- Authen

hoặc trong tổ chức:

- General
- Billing
- Roles
- Danger zone

#### `content-horizon`

Vai trò:

- Hiển thị nội dung tương ứng với mục đang chọn ở `navigation-horizon`.

Mục tiêu bố cục:

- Bên trái là điều hướng.
- Bên phải là form hoặc nội dung cài đặt.

### 8.6 `create-org-form`

`create-org-form` là component tạo tổ chức.

Nhiệm vụ:

- Nhập thông tin ban đầu của tổ chức.
- Cho phép người dùng dùng cấu hình mặc định hoặc tùy chỉnh thuộc tính ban đầu.

Vị trí sử dụng:

- `/org/create`

### 8.7 `avatar`

`avatar` là khung hình tròn hiển thị tên hoặc đại diện của người dùng.

Khi bấm vào:

- Mở popup điều hướng tới trang cá nhân.
- Mở các trang setting.

`avatar` là điểm vào nhanh cho:

- `/profile`
- Các route `/setting/*`

### 8.8 `notification`

`notification` là khu vực hiển thị các cảnh báo và cập nhật.

Thông báo ưu tiên:

- Thanh toán thành công
- Gói còn dưới 5 ngày
- Thành viên mới được thêm vào, dành cho admin

Nguyên tắc giao diện:

- Mỗi thông báo nên có tiêu đề, mô tả ngắn, thời gian và liên kết điều hướng nếu có.

---

## 9. Bản đồ route và bố cục đề xuất

### 9.1 Khu vực cá nhân

- `/dashboard`
  - Bố cục: `sidebar` + `form-chat`
- `/setting/profile`
  - Bố cục: `navigation-horizon` + `content-horizon`
- `/setting/payment`
  - Bố cục: `navigation-horizon` + `content-horizon`
- `/setting/organize`
  - Bố cục: `navigation-horizon` + `content-horizon`
- `/setting/authen`
  - Bố cục: `navigation-horizon` + `content-horizon`
- `/notifications`
  - Bố cục: danh sách `notification`
- `/profile`
  - Bố cục: trang hồ sơ public

### 9.2 Khu vực tổ chức tổng quát

- `/org`
  - Bố cục: danh sách tổ chức + hành động tạo mới/quản lý/tham gia
- `/org/search/[id]`
  - Bố cục: danh sách kết quả tìm kiếm tổ chức
- `/org/create`
  - Bố cục: `create-org-form`

### 9.3 Khu vực workspace tổ chức

- `/org/[id]/dashboard`
  - Bố cục: dashboard tổng quan tổ chức
- `/org/[id]/employees`
  - Bố cục: `list-employee` + `permission-assign` nếu người dùng có quyền quản trị vai trò
- `/org/[id]/documents`
  - Bố cục: `tree-document` + `content-document`
- `/org/[id]/analytics`
  - Bố cục: khối biểu đồ/chỉ số phân tích
- `/org/[id]/settings`
  - Bố cục: `navigation-horizon` + `content-horizon`
- `/org/[id]/chat`
  - Bố cục: `sidebar` + `form-chat`, nhưng ở ngữ cảnh tổ chức

---

## 10. Trạng thái giao diện bắt buộc

Mỗi màn hình và component chính phải thiết kế đủ các trạng thái:

- `initial`
- `loading`
- `empty`
- `ready`
- `success`
- `error`
- `permission-denied`

Các câu hỏi mà empty state cần trả lời:

- Đây là khu vực gì?
- Vì sao hiện chưa có dữ liệu?
- Người dùng nên làm gì tiếp theo?

Ví dụ:

- Chat rỗng: mời người dùng bắt đầu câu hỏi đầu tiên.
- Tài liệu rỗng: mời upload file hoặc tạo folder đầu tiên.
- Nhân viên rỗng: mời thêm thành viên đầu tiên.

---

## 11. Quy tắc tránh lỗi nghiệp vụ và lỗi giao diện

Không được:

- Trộn lịch sử chat cá nhân với lịch sử chat tổ chức.
- Trộn chat của hai tổ chức khác nhau.
- Dùng role toàn cục để thay cho role theo từng tổ chức.
- Gộp `/profile` với `/setting/profile`.
- Dùng `/setting/organize` thay thế cho `/org`.
- Cho người dùng mặc định quyền upload tài liệu, analytics hoặc RBAC khi chưa được cấp.
- Cho route tổ chức hiển thị được dù người dùng không thuộc tổ chức đó.
- Để component hiển thị sai workspace hiện tại.
- Đổi route tổ chức mà không đổi dữ liệu tương ứng theo `orgId`.

---

## 12. Tiêu chí hoàn thành

Tài liệu, thiết kế và triển khai chỉ được xem là đạt khi các câu hỏi sau luôn có câu trả lời rõ ràng trên giao diện:

- Tôi đang ở workspace cá nhân hay tổ chức?
- Nếu là tổ chức thì đây là tổ chức nào?
- Ở màn hình này tôi có thể làm gì?
- Tôi không làm được gì nếu thiếu quyền?
- Hành động tiếp theo hợp lý nhất là gì?

Nếu người dùng không tự trả lời được các câu hỏi này, thì kiến trúc giao diện chưa phục vụ tốt nghiệp vụ.
