# Câu hỏi cho chủ máy — muse2api khôi phục tự động

1. **tk_id MCP → khoá muse2api cho tài khoản dán cookie cũ:** delegate MCP
   đưa tk_id ngoài module, bản này chỉ ánh xạ được qua email cho tài
   khoản NV93 (bản ghi có email + hatch_sess). Tài khoản dán cookie cũ
   không lưu email trong module nên qua MCP vẫn trả `khoa_khong_co`.
   Chủ máy muốn (a) giữ vậy — muse2api qua MCP chỉ dùng cho NV93, hay
   (b) cho phép module tra email từ kho tài khoản của lõi lúc gọi (cần
   quyết kiến trúc, vì hiện tại lõi chỉ chuyển tiếp mỏng), hay (c) dùng
   khoá ms- nội bộ làm tk_id cho muse2api?
2. **Nút Google SSO trên muse.ai có tồn tại không?** T2 của bản này dùng
   `tai_dung_ho_so` (NV93), mà docstring NV90-C đã ghi là chưa kiểm thật:
   muse.ai dùng SSO Meta nên có thể không có Google SSO. Nếu không có,
   T2 qua controller sẽ trả `khong_ho_tro` và đường cứu duy nhất còn lại
   là NV230 + đăng nhập tay — có chấp nhận giới hạn đó không, hay cần
   kiểm thật nút này trước khi gộp?
3. **Hoãn captcha 1800 giây hay 6 giờ?** Bản này giữ 1800 giây như bản
   sửa module chatgpt-web/gemini-web; chatgpt2api giữ CAPTCHA Google tới
   6 giờ. Muốn đổi `_captcha_hoan_giay` của muse2api lên 6 giờ không?
4. **Có muốn NV230 tự mở hồ sơ đang mở không?** Hiện tại hồ sơ Firefox
   đang mở → 409 → `can_nguoi`, không đóng cưỡng bức. Giữ nguyên (an
   toàn, cần người đóng hồ sơ giữ phiên) hay cho phép một đường đóng
   hồ sơ có xác nhận?
