# Hỏi NV278 — Module AdGuard Home (không chặn triển khai)

Những câu này không chặn việc áp dụng patch; module đã chạy được với các
mặc định đã chọn, chủ kho chỉ cần xác nhận khi dựng thật.

1. **Xác nhận API trên AdGuard thật.** Patch đối chiếu tài liệu AdGuard Home
   v0.107.x (`/control/status`, `/control/stats`, `/control/filtering/status`,
   `/control/clients`, `POST /control/protection` với `duration` tính bằng
   mili-giây). Khi dựng thật, xin một mẫu JSON đã che của `/control/stats`
   và `/control/status` để khóa parser (nếu hình dạng khác, parser trả
   `du_lieu_sai` chứ không bịa số).
2. **Thời gian tắt mặc định 300 giây có đúng ý không?** Brief ghi «mặc định
   5 phút» — module dùng 300 giây làm mặc định cho cả `cau_hinh`
   (`thoi_gian_tat_mac_dinh_giay`) và cho lần tắt không kèm thời gian.
   Kẹp: tối thiểu 30 giây, tối đa 86400 giây (1 ngày, theo giới hạn pause
   của AdGuard v0.107.28). Nếu chủ máy muốn trần khác thì đổi một hằng số.
3. **Tên máy khách từ `/control/clients` có đủ không?** Top máy khách lấy
   từ `/control/stats` (IP + số lần); module tra tên qua `/control/clients`
   (nhóm `auto` + `persistent`), hỏng thì giữ IP. Nếu chủ máy muốn tên hiển
   thị theo nguồn khác (DHCP lease của mikrotik-routeros) thì nói rõ, hiện
   không gộp hai module.
4. **Có cần thực thể riêng cho top list không?** Hiện top miền bị chặn và
   top máy khách nằm trong `thuoc_tinh` của thực thể `adguard.bao_ve`
   (giới hạn theo `gioi_han_top`, chuỗi cắt 64 ký tự) thay vì thực thể
   riêng, vì chuẩn `thiet_bi` không có loại «bảng». Nếu giao diện cần
   thực thể riêng thì cần thêm quy ước ở lõi — không tự thêm route riêng.
6. **Có muốn `loai_tai_khoan_ten` trên manifest adguard không?** NV283
   nói «thêm `loai_tai_khoan_ten` vào manifest nếu chưa có», nhưng trường
   này chưa nằm trong `app/quyen_module._TRUONG_KHONG_QUYEN` và chưa
   manifest nào trong kho dùng, nên thêm vào là test phân loại trường
   đỏ. Patch này đã BỎ trường khỏi manifest adguard (không sửa lõi).
   Nếu chủ máy muốn giữ trường thì cần thêm nó vào allowlist của lõi
   trước khi gộp bản có trường.
5. **Cài đặt lên máy chủ: module mới có được tải từ nhánh này không?**
   Patch chỉ thêm `modules/adguard/` + test + tài liệu, không sửa lõi
   (`app/`), không Dockerfile/docker-compose/.github/.gitleaks.toml. Khi
   gộp, chủ kho cần kiểm module xuất hiện trong
   `GET /api/modules/thong-bao` và cài được qua
   `POST /api/modules/adguard/cai` với địa chỉ LAN của AdGuard thật.
