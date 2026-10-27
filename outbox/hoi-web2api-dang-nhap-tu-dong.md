# Câu hỏi thêm cho lần sửa đăng nhập tự động web2api

Các câu hỏi này không chặn việc nộp patch hiện tại, nhưng cần chủ máy trả
lời trước khi thử lại đăng nhập thật hoặc làm tiếp P4.

## 1. Có bổ sung kênh TOTP cho thang c2a không?

Hiện tại `TaiKhoanCanKhoiPhuc` không có trường TOTP, nên đường MCP mới
không đưa TOTP đã lưu vào thang khôi phục (TOTP bị xoá ngay sau khi đọc).
Tài khoản nào gặp 2FA qua đường này vẫn dừng ở `can_nguoi`.

Hỏi: chủ máy có muốn bổ sung kênh TOTP cho c2a trong một lần sửa riêng
(không bỏ qua 2FA, chỉ dùng TOTP đã lưu để sinh mã), hay giữ nguyên
2FA là cổng cần người?

## 2. Tài khoản Google `tk-b7b85b75867aac4c` chạy qua module nào, và module đó có đang chạy không?

Phiên Google `420ad58837d765c6` trả `chua_ho_tro`. Trước đó danh sách
tài khoản đã che ghi id này có nhóm và module để trống, và `tong_quan`
ghi `gemini-web` không chạy (chỉ `gemini-api` chạy).

Hỏi: chủ máy xác nhận giúp module thực thi đúng cho tài khoản này là gì
(vd: `gemini-web`), module đó có đang chạy trên máy chủ không, và allowlist
`WEB2API_MCP_DANG_NHAP_CHO_PHEP` có ghi đúng dạng `id@module` cho nó không?
Nếu allowlist hoặc module chạy chưa khớp, patch này cũng không làm phiên
Google qua được `chua_ho_tro`.

## 3. Log máy chủ cho phiên ChatGPT `can_nguoi` nói gì?

Phiên ChatGPT `c232ead015502c50` trả `can_nguoi` ngay trong cùng một giây.
Từ code, giả thuyết mạnh nhất là thiếu controller trình duyệt
(`trinh_duyet_none` trước đây chìm thành `can_nguoi`), nhưng chưa loại
trừ được trường hợp trang đích đã có sẵn tín hiệu thử thách trước khi điền.

Hỏi: chủ máy kiểm tra giúp log máy chủ tại thời điểm phiên đó xem có phải
«controller None» hay «tín hiệu thử thách trước khi điền» không, để lần
sửa tiếp theo nhắm đúng chỗ thay vì chỉ dựa vào giả thuyết từ code.

## 4. Chủ máy đã đăng ký controller thật chưa?

Patch này thêm điểm nối `dang_ky_trinh_duyet` /
`dang_ky_trinh_duyet_that`, nhưng bản thân việc đăng ký vẫn do chủ máy
thực hiện trên máy chủ (qua cầu nối danh tính → hồ sơ trình duyệt hoặc
đăng ký factory trực tiếp).

Hỏi: trên máy chủ, controller thật đã được đăng ký cho `chatgpt-web` và
`gemini-web` chưa, hay vẫn chưa đăng ký gì (khi đó module sẽ trả đúng mã
`trinh_duyet_none` mới, thay vì `can_nguoi` như trước)?
