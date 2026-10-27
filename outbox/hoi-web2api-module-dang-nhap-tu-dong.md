# Hỏi thêm — bản module đăng nhập tự động (2026-10-27)

Bản này chưa push, chưa tạo PR. Nhánh cũ `muse/web2api-dang-nhap-tu-dong`
(commit `86a32e6`) vẫn còn trên GitHub; bản này không xoá hay force-push
nhánh cũ. Trả lời 4 câu dưới để quyết bước tiếp theo.

1. **Gỡ hẳn thang khôi phục cũ ở lõi hay giữ làm legacy?**
   `app/khoi_phuc_phien.py` đã về nền `ffb7f3e`, nhưng thang nội bộ có sẵn
   trong file đó (cho các caller nội bộ khác) vẫn còn. Luồng MCP từ bản
   này trở đi không đi qua nó nữa. Có muốn gỡ hẳn thang đó khỏi mọi luồng
   nội bộ còn lại không, hay giữ nguyên làm legacy cho các caller hiện có?

2. **Nạp secret TOTP cho từng tài khoản bằng cách nào trên máy chủ?**
   Module đã có `luu_totp(khoa, email, secret)` và `totp_da_luu(khoa)`.
   Ai nạp secret, nạp khi nào, và secret lấy từ đâu (kho tài khoản đã lưu
   có trường `totp_secret` thì có được phép chuyển vào kho riêng của
   module không)? Chưa nạp thì 2FA vẫn dừng ở cần người.

3. **Controller thật đăng ký cho từng module như thế nào trên máy chủ?**
   Mỗi module nay có `dang_ky_trinh_duyet(factory)` riêng. Factory nào sẽ
   được đăng ký cho chatgpt-web và cho gemini-web, gắn hồ sơ trình duyệt
   nào, và ai là người gọi đăng ký khi máy chủ khởi động?

4. **Allowlist `id@module` đã đúng chưa?**
   Tài khoản ChatGPT `tk-21045e6bd2684c5f` chạy qua module nào, tài khoản
   Google `tk-b7b85b75867aac4c` chạy qua module nào, và allowlist trên máy
   chủ có ghi đúng hai cặp `id@module` đó không? Nếu sai, MCP vẫn trả
   `khong_cho_phep`/`chua_ho_tro` trước khi delegate tới module, dù module
   đã có đủ luồng tự động.
