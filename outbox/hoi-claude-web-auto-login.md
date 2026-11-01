# Câu hỏi cần chủ máy quyết — claude-web đăng nhập tự động

Bản này đã xong ở mức mock, chưa đẩy, chưa kiểm thật. 4 chỗ dưới đây cần
quyết trước khi kiểm thật hoặc gộp, để không làm sai hướng.

1. **TOTP lấy từ đâu khi chạy qua MCP?**
   Hiện tại `khoi_phuc_tu_dong` lấy TOTP từ **kho riêng của module**
   (`luu_totp`/`totp_da_luu`), vì delegate MCP chỉ gọi
   `khoi_phuc_tu_dong(tk_id, email)` mà không truyền TOTP. Đáp án trước đây
   cho chatgpt-web/gemini-web là TOTP từ kho tài khoản qua lõi đưa vào
   module lúc gọi — việc đó chưa làm. Hỏi: giữ kho riêng của module như bản
   này, hay chờ làm TOTP qua lõi rồi mới kiểm thật qua MCP?

2. **T2 cho Claude nên là đường nào trên trình duyệt thật?**
   - (a) Giữ khuôn điền email + mật khẩu hiện tại (cho tài khoản Google đã
     liên kết đi qua SSO) — nhưng chi tiết popup OAuth/chọn tài khoản của
     chatgpt2api không có trong giao diện trình duyệt trừu tượng của web2api,
     nên chưa chắc chạy được trên claude.ai thật.
   - (b) Khi có hồ sơ Google đã đăng nhập sẵn thì T2 dùng `tai_dung_ho_so`
     (NV93: bấm «Continue with Google», không nhập lại mật khẩu/2FA).
   - (c) Cả hai, theo thứ tự nào?
   Cần chủ máy chọn và cho kiểm thật trên trình duyệt thật mới xác nhận được.

3. **Kiểm thật ở đâu, với tài khoản nào?**
   `claude-web` đang `dang_chay=false` trên cổng MCP test (server
   `0.1.0-khung`), trong khi bản đã gộp là main `4a213a4`. Hỏi: kiểm thật
   trên server nào, và có cho phép tài khoản `id@claude-web` nào không?
   Không có allowlist thì đường MCP vẫn không chạy được dù mã đã có.

4. **Hoãn captcha và khóa serial giữ ở mức nào?**
   Bản này theo mẫu module cũ: khóa serial **riêng claude-web**, hoãn
   captcha **1800s**, và cửa sổ hoãn chặn các khoá khác (không chặn chính
   khoá đã gặp captcha — đúng mẫu chatgpt-web). chatgpt2api thì khóa serial
   **toàn cục** và giữ captcha **6 giờ**. Hỏi: giữ 1800s riêng module như
   bản này, hay đổi sang mức toàn cục/6 giờ cho khớp chatgpt2api?
