# Hỏi NV276 — những điểm chưa chốt (không chặn chạy thử, cần host quyết trước khi gộp)

1. **Id nút và số phận nút ảnh chụp.** Brief yêu cầu nút «Theo dõi» id `k268-theo-doi`, nhưng id
   này trên main đã là nút bật/tắt khung xem ảnh chụp (hướng NV276 trước đó, commit `a958550` /
   `8e389e7`) và có test assert nó. Bản này giữ nút ảnh chụp và thêm nút xem trực tiếp riêng
   `k268-theo-doi-truc-tiep` (tên tránh chuỗi `novnc` theo luật C6). Hỏi: giữ cả hai như vậy,
   hay host muốn nút cũ đổi thành xem trực tiếp (và bỏ/tách hướng ảnh chụp)?
2. **Mật khẩu VNC hiển thị hay nhập tay?** Bản này: mật khẩu không đi qua API nào, người xem nhập
   một lần ở hộp nhập của noVNC (chủ máy đọc từ container dịch vụ). Nếu host muốn giao diện hiển
   thị mật khẩu (có step-up, một lần, tự che) thì cần thêm endpoint ở dịch vụ — ngoài phạm vi brief
   và mở rộng bề mặt lộ bí mật; tác giả khuyến nghị **không** làm theo hướng đó trừ khi host
   quyết rõ.
3. **Mạng Docker trên máy thật.** Compose trong repo không khai network cho container web2api;
   module mặc định trỏ tới tên container `web2api-may-dang-nhap` nên suy ra hai container đã chung
   mạng trên máy thật, nhưng chưa được xác nhận. Hỏi điều phối xác nhận trước khi đo đầu cuối.
4. **Step-up cho đường xin vé lại?** Đường `/xem` đã có step-up; đường `/ve` cũ (xin vé mới cho hồ
   sơ đã mở) vẫn không có step-up như trước. Vé xem đã là một lần 60 giây nên rủi ro thấp — hỏi
   host có muốn siết thêm step-up cho `/ve` của hồ sơ xem hay giữ nguyên.
5. **Nút «Dừng theo dõi»?** Đóng tab trình duyệt không báo về server; phiên xem tự hết hạn sau
   8 giờ hoặc thu hồi qua `DELETE /api/trinh-duyet/phien`. Hỏi host có cần thêm nút dừng xem
   trong giao diện không (lưu ý: dừng xem chỉ thu hồi phiên xem, không đóng trình duyệt dịch vụ).
