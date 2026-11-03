# NV301 — mảnh tab: tab riêng YouTube + thực thể đọc trạng thái phát

- Nền: web2api main `8ef3ca9` (đã có NV277+NV289). Brief: `inbox/NV301.md`
  blob `7632f000` (kiểm lại lúc nộp: vẫn đúng blob này trên Giao main mới nhất).
- Patch: `outbox/nv301-tab.patch` (áp lên `8ef3ca9`, 5 tệp, +309/−1).
- Nhánh làm việc (web2api): `muse/nv301`, commit `4582666`.

## Làm gì

1. `modules/youtube/manifest.json`: thêm `tab_web: {"nhan": "YouTube",
   "trang": "web/index.html"}`. Khung đã hỗ trợ sẵn `tab_web` (hiện tab khi
   module đang chạy, phục vụ tệp tĩnh ở `/m/youtube/`): không sửa `app/`,
   không sửa `web/` — test độc lập vẫn xanh.
2. `modules/youtube/web/index.html` + `web/trang.js` (mới): trang tab chỉ
   ĐỌC trạng thái. Trang gọi lõi qua `POST /api/thiet-bi/<thực thể>/hanh-dong`
   (phiên quản trị, kèm CSRF như trang youtube-phat), KHÔNG gọi thẳng đường
   riêng của module (đường đó cần khoá khách `tich_hop@youtube`, trình duyệt
   không có), không chứa bí mật nào. Tự làm mới mỗi 20 giây như trang khu.
3. `modules/youtube/module.py`: thêm `thuc_the` / `trang_thai` / `thuc_hien`
   — một thực thể chỉ-đọc `youtube.xem` (rủi ro `doc`), trạng thái
   `chua_phat` / `dang_phat` / `dung` suy từ phiên trong RAM; hành động duy
   nhất hiện tại là `trang_thai` (đọc). Thực thể này cũng là ô trạng thái
   cho mục Đời sống (khung vẽ ô từ `GET /api/thiet-bi`).

## Cố tình CHƯA làm trong mảnh này (đi theo mảnh sau)

- Nút điều khiển (phát/dừng/bài kế/bài trước/tua/tìm/playlist) trên tab:
  đi theo mảnh lõi (hành vi ngang dịch vụ cũ) và mảnh giao diện.
- Không đổi `giao_dien` (chip/khu/mục) và không sửa README (README đang
  414 dòng, trần test 415 dòng).

## Kiểm thử (đỏ-trước-xanh)

- Mới: `test/test_module_youtube_tab.py` 5/5 (lúc đầu đỏ 5/5 vì chưa có
  `tab_web`, chưa có trang, chưa có `thuc_the`/`trang_thai`/`thuc_hien`).
- Liên quan xanh cùng lúc: `test_module_youtube_nv277.py`,
  `test_web2api_kham_pha.py`, `test_web2api_hang_manifest.py`,
  `test_web2api_doc_lap.py` — tổng 37 passed.
- Không có khoá/mật khẩu/token/cookie/email thật/IP thật trong patch,
  báo cáo hay log (từ “Bearer” chỉ xuất hiện trong mô tả manifest có sẵn
  từ main và trong assert kiểm tra sự vắng mặt).

## Lưu ý cho chủ máy khi gộp

- `tab_web` là một quyền thêm (module được chạy JS ở origin lõi): khi cài/
  cập nhật, luồng xác nhận quyền của lõi sẽ hỏi một lần như mọi module có
  tab riêng khác.
- Chưa kiểm tab trên Chrome thật (máy làm việc không có Chrome thật) và
  chưa thử với loa/HA thật: sau khi gộp, cần mở tab YouTube trên trình
  duyệt thật để đối chiếu hiển thị, và kiểm tra ô Đời sống không còn vẽ
  thẻ thực thể thô.
- Mảnh tiếp theo: lõi ngang dịch vụ cũ (siêu dữ liệu khi mở phiên, status
  đủ trường, next/prev + hàng đợi thật).
