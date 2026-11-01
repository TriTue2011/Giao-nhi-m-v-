# Câu hỏi cho chủ máy — grok-web đăng nhập tự động

Chỉ hỏi khi cần quyết, không hỏi lại những gì đã có đáp án.

1. Chế độ `google` của grok-web hiện chỉ tái dùng hồ sơ Google đã đăng
   nhập (không điền mật khẩu/TOTP). Có muốn làm thêm luồng đăng nhập
   Google tươi cho Grok (điền form Google + TOTP Google, theo mẫu
   `auto_login.py` của chatgpt2api), hay giữ nguyên chỉ tái dùng hồ sơ?
   Bản này chọn giữ nguyên, để tránh bịa một luồng Google chưa kiểm.

2. Hoãn captcha 1800s theo mẫu fb8aa25, hay lấy 6 giờ như chatgpt2api
   (`_GLOGIN_CAPTCHA_HOLD_S`)? Bản này giữ 1800s cho nhất quán với
   chatgpt-web/gemini-web trong web2api.

3. grok-web trên MCP test đang `dang_chay=false`. Khi áp bản này, chủ
   máy có dựng lại server test (0.1.0-khung) hay chỉ dựng main 4a213a4
   không? Bản này chưa kiểm thật trên server nào, cần chủ máy cho biết
   môi trường kiểm thật (và tài khoản Grok nào được phép thử, nếu có).

4. Thử thách truy cập grok.com (Cloudflare): chatgpt2api đo 20/09/2026
   là không tự qua được, cần một cú tích tay. Chủ máy có chấp nhận giữ
   luật NV90 cũ (cố vượt tối đa 3 lượt rồi can_nguoi, người tích tay qua
   noVNC) hay muốn đổi luật này cho grok-web?
