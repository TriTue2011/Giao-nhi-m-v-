# NV304 — mảnh (a): trình phát YouTube trong tab Đời sống + ẩn tab_web

## KẾT QUẢ

- Mảnh (a) đã xong và nộp lên nhánh Giao `muse/nv304-a`, patch
  `outbox/nv304-a.patch` (334 dòng, 8 tệp), nền web2api main `5f4df48`
  (đúng nền file NV304 dặn). Đây là mảnh ĐẦU TIÊN của NV304 — các mảnh
  (b), (c), (d) nộp sau sẽ là delta trên mảnh này, thứ tự gộp
  (a) → (b) → (c) → (d).
- Trình phát YouTube giờ nằm TRONG tab Đời sống: chip «YouTube» của khu
  Đời sống nhúng trang tab của module thay vì vẽ ô thực thể thô
  («unknown» như điều phối chụp). Tab «YouTube» KHÔNG còn trên thanh Hệ
  thống — ẩn SAU KHI trình phát đã vào Đời sống, đúng thứ tự file dặn
  (không gỡ trước kẻo mất trình phát). Trang tab vẫn mở được bằng đường
  dẫn trực tiếp (`/m/youtube/index.html`) và qua trang Module.
- **Chưa thử trên HA thật / chưa kiểm Chrome thật.** Phần này cần điều
  phối dựng lại rồi chủ máy thử trên HA thật: mở Đời sống → chip YouTube
  thấy trình phát đầy đủ; thanh Hệ thống không còn tab YouTube.

## ĐÃ LÀM

### 1. Cơ chế nhúng tab chung (không viết cứng tên module)

- `app/kham_pha.py` `_chuan_hoa_giao_dien`: chấp nhận thêm trường tuỳ
  chọn `nhung_tab` (phải là bool; sai kiểu thì bỏ cả `giao_dien` như
  mọi trường sai định dạng khác). Trường này đi theo `giao_dien` qua
  `giao_dien_cua` ra `/api/tinh-nang` mà không cần sửa gì thêm.
- `web/khung.js`: hàm thuần mới `tabNhungCua(mods, tab)` (đã export qua
  `window.Khung` để test bằng node) — chỉ chọn tab khi module ĐÃ LIÊN
  KẾT, khai `nhung_tab: true` và có mục tab trong `/api/tinh-nang`.
  `khu.vm` dùng nó: có tab nhúng thì tính `nhungDuong` (đường tuyệt đối
  suy từ đường tương đối của lõi + `?nhung=1`) và KHÔNG vẽ lưới ô thực
  thể, không hiện «Chưa có dữ liệu» hay «Đang đọc số liệu…» cho chip
  đó. Chưa nối thì vẫn đường «Chưa nối → Cài đặt» như cũ; chip «Cài
  đặt» không bị ảnh hưởng.
- Ba trang khu (`web/Doi-song.dc.html`, `web/Nha.dc.html`,
  `web/Tac-pham.dc.html` — cùng một mẫu) thêm section khung nhúng
  `<iframe class="khung-module" src="{{nhungDuong}}">` với đúng sandbox
  của trang Module (`allow-scripts allow-same-origin allow-forms
  allow-popups allow-popups-to-escape-sandbox allow-downloads`,
  `referrerpolicy="no-referrer"`) và CSS `.khung-module` như trang
  Module (cao `calc(100vh - 220px)`, tối thiểu 640 px).

### 2. Module youtube khai nhúng + ẩn tab

- `modules/youtube/manifest.json`: `giao_dien` thêm `"nhung_tab": true`;
  `tab_web` thêm `"an_khoi_thanh": true` — dùng đúng cơ chế NV263 sẵn có
  (`app/so_module.py` đã đưa cờ này vào mục tab của `/api/tinh-nang`,
  `khung.js` `navHeThong` đã bỏ qua mục tab có cờ). Không sửa logic
  ẩn tab — chỉ khai cờ.
- `modules/youtube/web/index.html`: khi URL có `?nhung=1` thì thêm lớp
  `nhung` vào `<html>`, CSS ẩn nút «← Hệ thống» và tiêu đề «YouTube»
  (Đời sống đã có tiêu đề và hàng chip của nó). Nội dung trình phát
  giữ nguyên — mảnh này chưa đổi bố cục (đó là mảnh (b)).

### 3. Quyết định trung thực: nhúng bằng iframe thay vì chép lại trình phát

Trình phát NV301 (`trang.js` 689 dòng + `index.html`) chỉ có MỘT bản:
Đời sống nhúng đúng trang đó qua iframe. Chép lại trình phát vào trang
khu sẽ thành hai bản lệch nhau sau mỗi lần sửa. Đánh đổi: trong iframe,
trình phát cuộn trong khung riêng (như trang Module đã làm) thay vì
cuộn cùng trang Đời sống — chấp nhận được vì đây đúng là mẫu trang
Module sẵn có, và mảnh (b) sửa bố cục bên trong trang tab thì cả hai
nơi cùng hưởng.

## KIỂM CHỨNG

- Test mới `test/test_module_youtube_nv304_a.py`: 5/5 xanh (đỏ trước:
  cả 5 đỏ khi chưa có code — manifest thiếu cờ, chuẩn hoá bỏ
  `nhung_tab`, template chưa có khung, trang tab chưa xử lý `?nhung`,
  `Khung.tabNhungCua` chưa tồn tại).
- Bộ liên quan: test youtube NV277 + NV301 (tab, lõi, playlist, giao
  diện, kiểm HA) + markdown khung + NV263 ẩn tab: 60 passed; test lõi
  `test_web2api_doc_lap` 6 passed; test khu NV297: 4 passed, 8 skipped
  (lý do skip sẵn có, không đổi). `node --check web/khung.js` sạch.
- Patch áp sạch lên nền `5f4df48` (kiểm bằng `git apply --check` trên
  worktree nền sạch).
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật.

## CHƯA LÀM / CẦN CHỦ MÁY (ghi rõ, không nhận vơ)

- Chưa thử trên HA thật, chưa mở Chrome thật (máy này không có
  Chrome): sau khi điều phối dựng lại, cần kiểm trên HA thật rằng chip
  YouTube ở Đời sống hiện trình phát đầy đủ và thanh Hệ thống không
  còn tab YouTube.
- Người dùng không phải quản trị: danh sách tab của `/api/tinh-nang`
  có thể không gồm youtube → khi đó chip rơi về đường ô thực thể cũ
  (không vỡ, chỉ chưa được nhúng). Nếu chủ máy muốn người dùng thường
  cũng thấy trình phát nhúng thì cần quyết riêng ở mảnh sau.
- Mảnh (b) sẽ sửa bố cục trình phát đúng demo (tìm lên trên cùng,
  2 cột, nút tròn SVG); mảnh (c) Zing/Facebook + seek_url; mảnh (d)
  port test cũ + bảng endpoint.
