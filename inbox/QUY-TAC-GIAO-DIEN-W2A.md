QUY TẮC GIAO DIỆN W2A — CHỦ MÁY CHỐT 03/11/2026 (Muse đọc TRƯỚC khi làm bất kỳ việc giao diện nào)
=============================================================================================
1. KẾT NỐI RA NGOÀI (w2a nối tới dịch vụ khác: AdGuard, MikroTik, nhà cung cấp AI…): nằm TRONG module đó, ở chip/tab «Cài đặt» của chính module (và Khu Tài khoản cho tài khoản AI). Luôn ẨN sau khi cài; bấm mới mở sửa; bí mật chỉ ghi đè («••••• đã lưu»), không bao giờ trả lại qua API. KHÔNG nhét vào Bảo mật & người dùng. (NV296 đã làm.)
2. KHOÁ DO W2A CẤP cho thứ bên ngoài gọi VÀO w2a (khoá khách, khoá MCP, khoá cho Home Assistant gọi module…): tạo ở «Bảo mật & người dùng», w2a TỰ sinh, hiện một lần, chọn module được phép (giống MCP). Chỉ những thứ này ở Bảo mật. (NV289.)
3. THANH CHÍNH theo demo: Studio · Tác phẩm ▾ · Nhà ▾ · Đời sống ▾ … Hệ thống. Cài module xong thì tab đúng loại hiện, trong có chip quản lý/đọc/kiểm soát + chip «Cài đặt» (ẩn). Gỡ module thì biến mất. (NV297.) Tab «Module» (= «Tiện ích» của demo) chủ máy nói đã ổn: KHÔNG đổi.
4. BỎ rườm rà: không trang «Thiết bị» chung, không «Đặt rủi ro Đọc/Ghi/Nguy hiểm», không id kỹ thuật hiện cho người dùng, không bước thừa. Module cài từ nguồn của chủ máy/fork là module đã tin; hành động GHI nguy hiểm vẫn xác nhận MỘT lần lúc gọi. (NV298.)
5. Người dùng không rành kỹ thuật: mọi ô có mô tả «điền gì, lấy ở đâu» bằng tiếng thường; giá trị đo được tự động (vân tay TLS…) thì hiện nút «Tin chứng chỉ này», không bắt dán. (NV295.)
6. Demo: /opt/claude-c2a/web2api-thiet-ke/project/*.dc.html — phải có `support.js` (chép từ web/support.js) cạnh các tệp rồi mở bằng http.server + Chrome mới thấy đúng (không có thì hiện chữ {{…}}). Bám demo: bố cục, chữ, chip, ô.

VÒNG LẶP LÀM CHO ĐẾN KHI ĐÚNG (chủ máy: «giao Muse cho đến khi đúng như yêu cầu»):
  Muse làm → nộp patch → điều phối soát + chạy test + đẩy main + dựng lại → Muse kiểm lại bằng chính bộ test Chrome và đối chiếu từng điều 1–6 với bản đang chạy (đọc mã + test; nếu có thể chụp ảnh) → Muse ghi LỖI/LỆCH tìm được vào outbox/kiem-giao-dien-<lần>.md rồi TỰ sửa trong lần nộp kế → lặp. Dừng khi một lượt kiểm không còn lệch nào so với 6 điều trên và demo.
Thứ tự: NV289 → NV297+NV298 (một patch) → NV295 → NV288 → NV291 → NV292 → NV294 → NV290.
