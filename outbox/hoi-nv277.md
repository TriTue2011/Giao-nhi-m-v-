# NV277 — CÂU HỎI CHO CHỦ KHO (không chặn triển khai thử nghiệm)

1. **Chặn đường `/m/*/api/*` qua hầm cloudflared bằng cách nào?**
   Cổng LAN trong `app/duong_module.py` không chặn được truy cập qua hầm
   vì peer qua hầm là IP gateway Docker (IP riêng). Hiện tại đường
   integration vẫn cần Bearer (an toàn), nhưng đường luồng mở chỉ dựa
   vào vé ký — nếu hầm công bố `/m/*/api/*` ra Internet thì ai có vé
   (vé chỉ nằm trong phản hồi integration đã xác thực) vẫn gọi được
   luồng từ Internet. Chủ kho chọn: (a) thêm luật ingress của hầm từ
   chối `/m/*/api/*`, hay (b) chấp nhận vé ký là đủ (vé hạn 3600 giây,
   không đoán được), hay (c) thêm biến tắt đường luồng khi qua hầm?
   Tạm thời: chưa chặn thêm gì, ghi rõ giới hạn trong báo cáo.

2. **Khả năng lõi mới có phải chuẩn chung không?**
   `app/duong_module.py` thiết kế mở: module nào khai `duong_module`
   trong manifest là dùng được, không cần sửa lõi thêm. Chủ kho có muốn
   giữ nó làm chuẩn cho module sau này, hay thu hẹp chỉ cho module
   youtube (ví dụ kiểm id module trong lõi)? Hiện tại là mở theo
   manifest (không nhắc tên module nào trong lõi).

3. **Tên hai phương thức module (`tich_hop`/`luong`) có cần khớp tên
   trong `docs/CHUAN-MODULE.md` không?**
   Hiện `CHUAN-MODULE.md` chưa có hai phương thức này (chỉ có trong
   docstring `app/kham_pha.py` và báo cáo NV277). Nếu chủ kho muốn đưa
   vào chuẩn module chính thức thì ghi thêm vào `CHUAN-MODULE.md` ở đợt
   sau; không đổi tên trong nhánh này nếu chưa có quyết định.

4. **Tăng `mem_limit`/`pids_limit` không, và đo ở đâu?**
   Môi trường làm việc không có docker nên chưa đo được RSS khi 2 trích
   xuất cùng lúc và kích thước ảnh tăng. Đề xuất tạm: giữ 1g/100, đo
   thật khi dựng ảnh rồi quyết. Nếu máy chủ đã có số đo từ dịch vụ cũ
   (cùng yt-dlp) thì dùng số đó làm căn cứ thay cho đo lại.

5. **Giải luồng Zing/Facebook có cần chuyển tiếp không, hay YouTube
   là đủ cho đợt đầu?**
   Hiện Zing chỉ có tìm kiếm (endpoint gợi ý công khai); giải luồng
   Zing/Facebook trả 502 rõ. Dịch vụ cũ có luồng lấy khoá web riêng
   từng nguồn — chuyển tiếp cần kiểm chứng lại với nguồn thật, không
   làm mò trong nhánh này.

6. **Khi nào chuyển HA từ c2a sang?**
   c2a vẫn phục vụ HA (cổng 3030) và không bị đụng trong nhánh này.
   Chủ kho chuyển URL gốc + khoá mới rồi kiểm với loa thật xong mới
   tính chuyện gỡ c2a / gỡ `youtube-phat`.
