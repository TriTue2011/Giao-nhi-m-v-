# Hỏi NV283 (chưa có câu nào chặn triển khai — làm xong rồi mới hỏi)

1. **Route suc-khoe có nên nối đánh dấu hết hạn không?** Brief §2c nói
   «lần kiểm sức khoẻ (suc-khoe) mà một phiên 401 thì đánh dấu». Hiện tại
   chỉ lượt DÙNG qua `luong_dung.ghi_luot` thấy 401 mới đánh dấu; route
   `GET /api/modules/{id}/suc-khoe` vẫn passthrough nguyên trạng vì mỗi
   module trả một hình sức khoẻ khác nhau (chatgpt-web: `loai_loi` từng
   khoá; openaicodex: `trang_thai` từng tài khoản…) — lõi dò hình theo
   module sẽ vi phạm nguyên tắc «suy từ cấu trúc, không từ tên». Chủ kho
   duyệt một trong hai: (a) giữ như hiện tại (đánh dấu ở lượt dùng +
   lần đăng nhập kế — đủ cho chấm màu sau khi tài khoản được dùng lại);
   (b) thêm khả năng tuỳ chọn của module (vd `phien_het_han(email)`)
   để route suc-khoe gọi một cách có cấu trúc.
2. **Đường `…/ma-2fa` và luồng liên kết Codex OAuth có nên ghi kết quả
   không?** Cả hai không gọi hàm `dang_nhap` của module nên nằm ngoài
   phạm vi grep của brief §2a và hiện chưa ghi. Nếu chủ kho muốn: `ma-2fa`
   thành công có thể ghi đè `can_xu_ly` thành `thanh_cong` (đăng nhập hoàn
   tất sau 2FA); liên kết Codex hoàn tất có thể ghi `thanh_cong` cho
   đường codex. Cần duyệt trước khi thêm (tránh ghi đè sai ngữ nghĩa:
   2FA là tiếp nối lượt đã ghi, không phải lượt mới).
3. **Giãn cách mặc định?** Brief §1 ghi tự đăng nhập «mặc định 3600 s»
   nhưng mã `gian_cach_giay` mặc định 300 s (env
   `WEB2API_DANG_NHAP_GIAN_CACH_GIAY`). Không đổi (ngoài phạm vi) — chủ
   kho xác nhận giá trị nào là đúng trên server thật (env server có thể
   đã đặt 3600).
