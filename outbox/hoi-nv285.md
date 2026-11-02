# Hỏi NV285 (chưa có câu nào chặn triển khai — làm xong rồi mới hỏi)

1. **Hình dạng thật của `limits_progress` trong `/backend-api/me` của
   ChatGPT là gì?** Parser của chatgpt-web hiện chấp nhận danh sách mục
   hoặc bản đồ tên→mục với các khoá số đã biết (remaining/limit/
   used_percent/reset_at/reset_after_seconds + biến thể) — nhưng chưa
   được kiểm bằng tài khoản thật hay bằng mẫu phản hồi thật từ nhà cung
   cấp. Cần chủ kho (hoặc NV282) cung cấp một mẫu `limits_progress`
   thật (đã che) để khóa parser; nếu hình thật khác, parser sẽ trả
   `khong_biet` chứ không bịa — giao diện sẽ thấy trống thay vì sai số.
2. **Hợp đồng `goi` có mở rộng thêm `pro`/team không?** Hợp đồng §3b
   đóng ở `plus|free|khong_biet`; chatgpt-web có bậc `pro`,
   openaicodex `plan` có thể là pro/team — hiện tất cả gộp vào
   `khong_biet`. Nếu giao diện cần phân biệt `pro`, cần duyệt mở rộng
   hợp đồng (thêm giá trị) trước khi đổi mã.
3. **Route suc-khoe có nên cấp số liệu cho chi-tiet không?**
   `chi_tiet_tai_khoan` hiện chỉ đọc bộ đệm init/dùng gần nhất; tài
   khoản chỉ từng kiểm qua suc-khoe (chưa init qua core) sẽ thấy
   `khong_biet` cho tới lần init/làm mới kế. Đây là thiết kế theo spec
   («không gọi mạng thêm khi chỉ đọc») — ghi để xác nhận, không phải
   lỗi.
4. **Nhóm không có `duong` thì hạng tính thế nào?** Tài khoản chưa đặt
   `dich_dung`/`dung_cho` rơi vào nhóm `(nhà, "")`, tách khỏi nhóm
   `(nhà, "web")` dù cùng module — hạng #1 của hai nhóm tính riêng.
   Nếu chủ kho muốn gộp (đường suy từ module khi tài khoản chưa đặt
   đích), cần duyệt vì đó là suy luận thêm ngoài dữ liệu tài khoản.
