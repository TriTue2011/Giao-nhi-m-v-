# Giao việc qua GitHub

Repo riêng `TriTue2011/Giao-nhi-m-v-`: kênh giao việc giữa chủ máy/điều phối và Muse (Muse không còn vào máy chủ).
Thư mục `/opt/claude-c2a/giao-viec-github` trên máy chủ tự đồng bộ với nhánh `main` của repo này (cron mỗi 5 phút, script `dong_bo.sh`).
Repo này **không chứa mã sản phẩm**; mã làm việc nằm ở các nhánh `muse/*` của từng kho (ví dụ `TriTue2011/calendar`).

**Kho này CÔNG KHAI: không được đặt khoá, mật khẩu, token hay dữ liệu riêng vào đây.** Script tự quét bằng gitleaks và chỉ đẩy các đuôi
tệp an toàn (văn bản, ảnh, patch, mã tham chiếu), mỗi tệp ≤ 20 MB; vẫn phải tự giữ.

- `inbox/` — việc giao cho Muse (`NV270.md`, kèm ảnh và mã tham chiếu).
- `outbox/` — kết quả Muse trả về: `nvNNN.patch`, `nvNNN-bao-cao.md`, ảnh chụp, `hoi-*.md` (câu hỏi). Muse nộp bằng Pull Request vào `main`
  của repo này; điều phối kéo về (pull) rồi xem.
- Mã làm việc của NV270: nhánh `muse/nv270` của `TriTue2011/calendar`.

Nhật ký đồng bộ: `dong_bo.log`.
