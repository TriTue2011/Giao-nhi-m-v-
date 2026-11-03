KẾT QUẢ — NV294 BƯỚC 1: docs/DESIGN.md + docs/PRODUCT.md MỚI, KHÔNG ĐỔI GIAO DIỆN

- Đã đẩy: nhánh `muse/nv294-buoc-1` (Giao main không đổi `82d9ff46`).
- Nền: web2api main `8ed35ab` (kiểm bằng ls-remote trước khi làm).
- Patch: `outbox/nv294-buoc-1.patch` (465 dòng, 2 file mới, +453/−0,
  áp sạch lên cây mới clone từ main, đã kiểm).
- File nộp kèm: `outbox/nv294-buoc-1-bao-cao.md` (báo cáo này).

## Làm gì

Đọc trước mọi việc: `inbox/NV294.md` và `inbox/QUY-TAC-GIAO-DIEN-W2A.md`
(lấy mới từ Giao main), `SKILL.md` của Taste v2 và Impeccable v4.8.0
(đã cài sẵn trên máy), `references/app-screens.md` của Taste (màn hình
quản trị là app screen, không phải landing page) và
`references/document.md` + `references/init.md` của Impeccable.

Rồi đo hệ thống hiện có từ mã nguồn (không đoán, không chụp màn hình):
`web/khung.css` (đọc toàn bộ 208 dòng), toàn bộ `web/*.dc.html`,
`web/khung.js`, `web/support.js`, `README.md` (chỉ đọc, không sửa —
README đang 413/415 dòng, còn 2 dòng trần), CSP trong
`app/tieu_de_bao_mat.py`.

## docs/DESIGN.md — hệ thống thiết kế hiện có (296 dòng)

Frontmatter YAML theo đúng spec của Impeccable `document` (đã kiểm
`yaml.safe_load`: 22 màu, 4 vai trò chữ, 7 bo, 6 khoảng cách, 6 thành
phần; giá trị trong frontmatter khớp đúng phần văn xuôi), rồi 8 mục
chuẩn theo thứ tự: Overview, Colors, Typography, Layout,
Elevation & Depth, Shapes, Components, Do's and Don'ts.

Tóm tắt hệ đã mô tả:

- **Mặt**: nền giấy ấm `#F6F5F2`, thẻ trắng viền `#E4E2DC`, mực
  `#181816`, một điểm teal `#0F766E`. Nút chính tô màu mực, teal chỉ ở
  viền focus, liên kết, nhãn nhỏ, mục đang chọn ở thanh dưới.
- **Chữ**: Be Vietnam Pro cho nội dung (14px/1.5), Newsreader chỉ cho
  tên web, tiêu đề lớn và con số ô khu; mono cho mã. Phông nạp từ
  Google Fonts, CSP cho phép `font-src https:` nên nạp được.
- **Tương phản đã đo**: mực trên nền 16,31:1; chữ phụ 5,42:1 (nền) /
  5,91:1 (thẻ); teal 5,02:1 / 5,47:1; các cặp huy hiệu/báo 6,89–8,14:1
  — tất cả đạt AA cho chữ thường.
- **Hình dạng**: họ mềm — thẻ 18px, thẻ con 14px, nút/chip viên thuốc
  22px/20px, ô nhập 10px; bóng chỉ ở menu nổi, không bóng thẻ, không
  gradient (grep toàn `web/` = 0), không emoji chào mừng.
- **Hai token chết ghi rõ trong tài liệu**: `.tieu-de` (38px) và
  `.nhan-tren` không trang nào dùng — chờ giai đoạn 3 quyết dùng lại
  hay dọn, không tự xoá ở bước này.
- **Bắc cực sáng tạo**: chỉ mô tả từ hệ hiện có («giấy ấm, mực đen,
  một điểm teal»), ghi rõ là chưa chốt với chủ máy — không bịa thành
  quyết định thương hiệu.

## docs/PRODUCT.md — người dùng và mục tiêu (157 dòng)

Theo mẫu `init` của Impeccable (kèm chú thích `impeccable:product-schema
1`): Platform web; người dùng chính là một chủ máy (tiếng Việt, không
nhất thiết rành kỹ thuật, dùng cả máy tính và điện thoại), phụ là thành
viên gia đình (vai trò `user`); mục đích là cổng AI chuẩn OpenAI với lõi
trung lập + module nạp nóng; 5 nguyên tắc sản phẩm; các ràng buộc cứng
(không đổi hành vi/id/văn bản test khẳng định, không phụ thuộc mới,
không thư viện ngoài, bí mật không bao giờ quay lại, hành động nguy hiểm
xác nhận một lần lúc gọi). Ba điểm **(chưa chốt)** ghi rõ, không coi là
quyết định: phạm vi chế độ tối, thang tiêu đề thống nhất, mốc điện thoại
(1023px của demo so với lưới nghiệm thu 375/1280px).

## Ranh giới đã giữ

- Không đổi một dòng giao diện nào: patch chỉ có 2 file mới trong
  `docs/`; không sửa `web/`, không sửa `README.md`, không thêm phụ thuộc.
- Không ghi bí mật/khoá/IP thật/email thật/vân tay thật vào patch, báo
  cáo hay log (đã quét nhanh 2 file mới: sạch).
- Không đụng `web/He-thong-AI.dc.html` (NV282) và bảng chi tiết Module
  (NV280) — bước 1 chỉ đọc mã chung, không kiểm hay sửa hai màn hình đó.
- Launcher `impeccable context`: binary không có sẵn cạnh script trên
  máy này (thư mục `scripts/bin/` trống) nên theo đúng đường dự phòng
  của skill: không tải thêm gì, đọc trực tiếp bối cảnh dự án từ mã nguồn
  và tài liệu. Việc này không chặn công việc lập tài liệu.

## Chưa làm (thuộc bước 2)

Bảng kiểm theo từng trang (mẫu AI slop + tương phản/khoảng cách/chữ +
trạng thái trống/lỗi/đang tải + sáng-tối + điện thoại 375px), xếp theo
mức ảnh hưởng — nộp ở nhánh `muse/nv294-buoc-2`. Bước 3 (sửa giao diện)
không làm trong lượt này vì máy này không có Chrome thật để chụp ảnh
trước/sau (sáng/tối, 375px + 1280px) mà NV294 nghiệm thu yêu cầu.
