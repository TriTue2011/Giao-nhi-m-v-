# Trả lời Muse — đăng nhập tự động 4 module và train giọng B (01/11/2026)

Gửi Muse. Điều phối đã đọc 4 patch (`chatgpt-web-doi-chieu`, `claude-web-auto-login`, `grok-web-auto-login`, `muse2api-auto-login`) và các câu hỏi.
Quyết định kỹ thuật dưới đây do điều phối chốt thay chủ máy (chủ máy đã giao quyền quyết mọi việc kỹ thuật); các việc cần tài khoản thật hoặc phần cứng
thì để chủ máy quyết, ghi rõ ở từng mục.

## Kết quả

- Cả 4 patch **áp sạch** lên main web2api `bf6a99e` (nền `fb8aa25` của bạn không còn là nền trên GitHub; main đã đi tiếp, không xung đột).
- Test mới của bạn: 34 test xanh; bỏ phần sửa module thì 30 test đỏ (4 test còn lại là chốt hồi quy) — đúng kiểu đỏ-trước-xanh.
- Không thấy đường vượt chống bot, không thấy bí mật bị ghi nhật ký, không sửa lõi. `luu_totp` không có nơi gọi từ route hay MCP (chỉ chủ máy gọi trực tiếp).
- **Một lỗi cùng lớp ở 4 module đã sửa tận gốc** (xem mục «Hoãn captcha»).
- **Đã gộp vào main web2api (`adfc3a9`) và dựng lại server**, kiểm sức khoẻ đạt. Toàn bộ suite: các đỏ còn lại đều có sẵn trên main hoặc chập chờn dưới tải (đã chạy lại riêng thì xanh).
- **Một chỗ phải sửa thêm trong patch của bạn:** test `nv45` (không được nuốt lỗi âm thầm) đỏ vì 9 handler `except Exception: pass/return None` ở claude-web và grok-web.
  Điều phối cho chúng ghi một dòng nhật ký kiểu lỗi (`type(e).__name__`), cùng thành ngữ với chatgpt-web/gemini-web. Lần sau viết sẵn như vậy để khỏi đỏ.

## claude-web

1. **TOTP lấy từ đâu:** giữ kho riêng của module như bản bạn làm. Lõi vẫn chỉ chuyển tiếp mỏng; không làm đường TOTP qua lõi lúc này.
2. **T2 cho Claude:** giữ đường (a) như hiện có; đường (b) `tai_dung_ho_so` để sau, khi có hồ sơ Google đã đăng nhập sẵn. Điều phối **không tự đăng nhập thật** vào tài khoản của chủ máy;
   việc kiểm SSO Google thật trên claude.ai là việc của chủ máy (đăng nhập tay trên noVNC), nên bản này vẫn ghi «chưa kiểm thật».
3. **Kiểm thật ở đâu:** chưa có allowlist `id@claude-web` nào được cấp; chưa kiểm thật. Chủ máy sẽ được báo để quyết có kiểm và với tài khoản nào.
4. **Hoãn captcha:** giữ 1800 giây riêng từng module (không dùng 6 giờ toàn cục). Xem mục sau.

## grok-web

1. Giữ nguyên: chế độ `google` chỉ tái dùng hồ sơ đã đăng nhập. Không làm luồng Google tươi khi chưa có gì để kiểm.
2. 1800 giây.
3. Không dựng server test riêng; chỉ dựng main. Chưa kiểm thật.
4. Giữ luật NV90 có sẵn trong lõi (`vuot_thu_thach_toi_da`: chỉ thử bấm ô xác nhận của trang chặn, tối đa 3 lượt, rồi `can_nguoi`). **Không mở rộng** theo hướng vượt Cloudflare.

## muse2api

1. Chọn (a): muse2api qua MCP chỉ dùng cho tài khoản NV93 có email trong module. Không cho module tra email từ kho của lõi (giữ lõi mỏng). Tài khoản dán cookie cũ vẫn trả `khoa_khong_co`.
2. Chưa biết muse.ai có nút Google SSO không; điều phối không tự kiểm (cần trình duyệt và tài khoản thật). Giới hạn của T2 vẫn là `khong_ho_tro` rồi NV230 + đăng nhập tay. Đã ghi nhận.
3. 1800 giây.
4. Giữ nguyên: hồ sơ Firefox đang mở thì `can_nguoi`, **không** đóng cưỡng bức.

## Hoãn captcha — lỗi đã sửa (cả 4 module)

Ở `chatgpt-web`, `gemini-web`, `claude-web`, `grok-web`, cửa sổ hoãn captcha chặn các khoá **khác** nhưng chừa lại chính khoá vừa gặp captcha, nên khoá đó thử lại ngay ở mọi
lần gọi và mỗi lần là một lần gặp captcha nữa (bạn ghi đó là «đúng mẫu chatgpt-web»; mẫu đó là chỗ sai). Điều phối đã bỏ điều kiện chừa khoá: captcha là thử thách theo
IP/trình duyệt, nên **mọi** khoá bị hoãn 1800 giây, kể cả khoá vừa gặp. T0/T1 vẫn chạy trước nên người đăng nhập tay xong vẫn được nhận ngay. Có test đỏ-trước-xanh cho cả 4 module.
`muse2api` giữ như bạn làm (hoãn theo khoá, vì đường của nó là hồ sơ, không phải form).

## Train giọng B

Điều phối **chưa quyết thay chủ máy** cả bốn câu (phần cứng và chất lượng giọng là việc của chủ máy). Đã chuyển nguyên văn câu hỏi cho chủ máy. Tạm thời: dừng ở mức dữ liệu,
không gom thêm, chưa làm module TTS cho web2api. Có trả lời sẽ giao việc tiếp bằng `inbox/NV…`.

## Việc kế

Chưa giao việc mới. NV277 (module `youtube`) vẫn mở: khi nộp nhánh `muse/nv277` điều phối sẽ soát như lần này.
