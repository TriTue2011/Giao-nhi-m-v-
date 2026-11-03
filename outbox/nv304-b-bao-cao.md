# NV304 — mảnh (b): trình phát đúng demo (tìm lên trên cùng, 2 cột, nút tròn SVG)

## KẾT QUẢ

- Mảnh (b) đã xong và nộp lên nhánh Giao `muse/nv304-b`, patch
  `outbox/nv304-b.patch` (338 dòng, 3 tệp). Đây là DELTA trên mảnh (a):
  thứ tự gộp (a) → (b) → (c) → (d); patch (b) KHÔNG chứa lại thay đổi
  của (a), đã kiểm áp nối tiếp (a) rồi (b) lên nền web2api main
  `5f4df48` bằng `git apply` trên worktree nền sạch.
- Trình phát giờ đúng demo ở 3 điểm điều phối chụp lệch: ô tìm lên
  TRÊN CÙNG; màn hình rộng thì 2 cột (thẻ đang phát bên trái, kết quả
  bên phải); ba nút kết quả là nút TRÒN có biểu tượng SVG (Phát /
  Queue / Playlist) thay vì nút viên thuốc. Dùng skill Impeccable
  (đọc `craft-floor.md` trước khi sửa) + Taste v2 (chạy lint tĩnh
  `--app`).
- **Chưa kiểm Chrome thật / chưa thử trên HA thật** (máy này không có
  Chrome; Taste `inspect.mjs` cần trình duyệt thật nên chưa chạy được
  — cần chủ máy mở trang tab và Đời sống trên Chrome thật sau khi
  điều phối dựng lại, ở 375 px và 1280 px).

## ĐÃ LÀM

### 1. Thứ tự mục + lưới 2 cột (`modules/youtube/web/index.html`)

- Mục «Tìm kiếm» (chip nguồn YouTube · Zing MP3 · Facebook + ô tìm +
  ghi chú nguồn) dời lên ĐẦU TIÊN, trước «Đang phát».
- Thêm mục «Kết quả» riêng chứa ô chọn «Playlist nhận bài» + danh sách
  kết quả (trước đây danh sách nằm trong mục Tìm kiếm).
- «Đang phát» + «Nhóm đang phát» vào cột trái, «Kết quả» vào cột phải,
  trong khung `.luoi-2-cot`: từ 1024 px trở lên là lưới 2 cột
  (5fr / 7fr, căn đầu cột), dưới đó một cột. Các mục còn lại
  (Playlist, Hàng đợi, Loa & tivi, Cài đặt) vẫn toàn chiều rộng bên
  dưới. Mọi id cũ giữ nguyên nên `trang.js` và test NV301 cũ không
  phải sửa (chỉ dời khối DOM, không đổi id hay hành động).

### 2. Nút tròn SVG (`modules/youtube/web/trang.js` + CSS)

- Ba nút ở mỗi kết quả tìm kiếm giờ là nút tròn 40 px (chạm được bằng
  ngón tay, viền nhạt, nền trắng / tối theo giao diện, viền focus rõ
  khi đi bằng bàn phím): Phát (tam giác đặc), Thêm vào Queue (danh
  sách + dấu cộng), Thêm vào Playlist (nốt nhạc). Nút Phát giữ dạng
  chính (nền đậm).
- SVG dựng bằng `createElementNS` — KHÔNG `innerHTML`, giữ quy ước
  NV301 (dữ liệu ngoài chỉ qua `textContent`); ba biểu tượng là hằng
  trong mã, không chứa dữ liệu ngoài. Nhãn đầy đủ nằm ở `aria-label` +
  `title` với đúng chữ cũ («Phát», «Thêm vào Queue», «Thêm vào
  Playlist») nên test NV301 cũ vẫn tìm thấy chuỗi và trình đọc màn
  hình vẫn đọc được.
- Phạm vi cố tình hẹp: chỉ ba nút kết quả theo đúng tên file NV304
  nêu. Nút quản lý ở Playlist/Hàng đợi («Phát từ đây», «Xoá»,
  «Xem bài») giữ dạng chữ nhỏ — các động từ này mà chỉ vẽ biểu tượng
  thì khó hiểu, không đổi để khỏi đoán nghĩa.

### 3. Dọn theo lint Taste + Impeccable

- Taste lint tĩnh `--app` trên hai tệp trình phát: trước sửa có 1 FAIL
  (emoji 🌙 làm biểu tượng ở nút «Nghe khi tắt màn hình», có sẵn từ
  NV301) → đã thay bằng SVG trăng khuyết vẽ bằng đường nét, giữ nguyên
  chữ nút. Sau sửa: 0 FAIL, 3 WARN — đã xem và GIỮ NGUYÊN có lý do:
  zero-padding `padStart` là định dạng đồng hồ (phút:giây, lint cho
  phép); dấu gạch ngang «—» là dấu câu trong câu tiếng Việt, không
  phải đánh số mục.
- Impeccable `craft-floor`: không gradient, không bóng cứng, không
  kicker/eyebrow, không thẻ lồng thẻ; màu chỉ ở dữ liệu (nút Phát
  chính), còn lại viền nhạt 1 px; nút 40 px, focus thấy rõ; chữ tiếng
  Việt thường, nút đặt tên theo hành động.

## KIỂM CHỨNG

- Test mới `test/test_module_youtube_nv304_b.py`: 4/4 xanh (đỏ trước:
  3 đỏ — thứ tự mục, lưới 2 cột, nút tròn; 1 test `node --check` vốn
  đã xanh). Test NV301 cũ về trang tab (đủ id/chữ, không innerHTML,
  chỉ gọi hành động đã khai) vẫn xanh nguyên.
- Taste lint `--app`: 0 FAIL (3 WARN đã xem, giữ nguyên có lý do ở
  trên). `node --check` cả `trang.js` và `khung.js` sạch.
- Patch (b) áp nối tiếp sau patch (a) lên nền `5f4df48` (kiểm bằng
  `git apply` thật trên worktree nền sạch, không chỉ `--check` rời).
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật.

## CHƯA LÀM / CẦN CHỦ MÁY

- Chưa mở Chrome thật: cần kiểm 375 px + 1280 px sau khi dựng lại
  (thứ tự mục, lưới 2 cột có đúng không, nút tròn có dễ bấm không,
  iframe trong Đời sống có cuộn ổn không).
- Mảnh (c) tiếp theo: giải luồng Zing/Facebook + nhập playlist Zing +
  `seek_url`; mảnh (d): port test cũ + bảng endpoint.
