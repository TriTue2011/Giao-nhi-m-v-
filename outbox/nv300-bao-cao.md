# NV300 — Cách đăng nhập theo từng tài khoản — Báo cáo nộp

- Base: web2api main `8ef3ca9` («NV277+NV289», đã chứa NV289 nên không làm lại phần đó).
- Brief: `inbox/NV300.md` trên Giao main (blob `680ad714fe92dd08a1c1353dfbf3b3f6967eda6a`, không đổi
  trong lúc làm). Bổ sung 03/11: Claude tạm thời chỉ Google.
- Patch: `outbox/nv300.patch` (áp lên base `8ef3ca9`, 17 file, 1557 dòng). Nhánh Giao: `muse/nv300`.
- «Chưa thử với loa/HA thật» — NV300 không chạm đường loa, nhưng ghi rõ theo quy ước chung.

## Làm gì

### Kho tài khoản (`app/kho_tai_khoan.py`)
- Giá trị cách đăng nhập sống trong bảng dữ liệu `du_lieu/phan_loai_ai.json` (mục mới
  `cach_dang_nhap`: `ho_so`/`email`/`truong_ho_so`) — lõi chỉ đọc qua hằng `CACH_HO_SO`/
  `CACH_EMAIL`/`CACH_DANG_NHAP_CHO_PHEP`/`TRUONG_HO_SO`, KHÔNG gõ cứng tên phương thức hay tên
  trường vào mã lõi (đúng quy tắc ghi trong `_ghi_chu` của bảng và cổng
  `test_loi_khong_mang_dac_thu_nha_cung_cap`, cùng mẫu NV223).
  `kiem_cach_dang_nhap`, `kiem_ho_so` (tên hàm/trường trong mã lõi dùng `ho_so`, khóa
  bản ghi/API chuẩn vẫn là `ho_so_google` qua hằng).
- `luu_tai_khoan(..., cach_dang_nhap, ho_so_google)`: google bắt buộc có `ho_so_google` khác rỗng
  (thiếu → `invalid_value`, không lưu dở); google mới được phép không có mật khẩu (bí mật rỗng).
- `cach_dang_nhap_cua` (hiệu lực): giá trị đã ghi thắng; chưa ghi thì có mật khẩu → `email`,
  không có gì → rỗng (module giữ hành vi cũ).
- **Không suy từ NV223 (quyết định sửa sau khi test NV271 đỏ):** `dang_nhap_bang` qua tài khoản lưu là
  «đăng nhập HỘ bằng bí mật của tài khoản Google» (vẫn đi đường mật khẩu — NV271 A2/C3), KHÁC với
  cach `google` là «tái dùng hồ sơ đã đăng nhập, không cần mật khẩu». Trộn hai thứ phá đường đăng nhập hộ
  (đã chứng minh bằng test: A2/C3 đỏ khi suy, xanh khi bỏ suy).
- Bản công khai hiện `cach_dang_nhap` hiệu lực + `ho_so_google` đã lưu; bí mật không bao giờ trả ra.

### Module web (mỗi module hai đường, chọn theo tài khoản)
- `grok-web`: `CACH_DANG_NHAP_HO_TRO = ("google", "email")`; ghi nhớ theo tài khoản
  (`_doc_cach`/`_luu_cach`/`dat_cach_dang_nhap`/`cach_dang_nhap_cua`/`ho_so_google_cua`);
  `_dang_nhap_bang_trinh_duyet(..., cach_dang_nhap)` rẽ theo cách; `dang_nhap()` thêm nhánh
  `loai == "google"` (qua `tai_dung_ho_so`, không điền gì) và hai nhánh `mat_khau`/`dang_nhap_lai`
  truyền cách đã phân giải (google ở `dang_nhap_lai` đi đường hồ sơ, không đòi mật khẩu đã lưu);
  `dang_nhap_tu_dong` (tầng b) rẽ google/email; `khoi_phuc_tu_dong(..., cach_dang_nhap, ho_so_google)`
  phân giải ở T2, google bỏ kiểm `thieu_mat_khau`, ghi nhớ lựa chọn tường minh; bỏ
  `che_do_dang_nhap` khỏi `modules/grok-web/manifest.json` (đọc ngược giá trị cũ làm mặc định).
- `chatgpt-web`, `gemini-web`: `("google", "email")`; `khoi_phuc_tu_dong` google → `tai_dung_ho_so`
  (không đòi mật khẩu), email/không truyền → đường mật khẩu cũ; `dang_nhap()` thêm nhánh `google`
  và đổi đường khi lần gọi mang `cach_dang_nhap == "google"`.
- `claude-web`: `("google",)` (tạm thời, bổ sung 03/11); `khoi_phuc_tu_dong` ÉP google khi lần
  gọi mang cách tường minh (khác rỗng, bất kể giá trị — kể cả `email`); không mang cách
  (tài khoản cũ, gọi trực tiếp) thì giữ đường mật khẩu cũ — tinh chỉnh sau khi 7 test
  `test_web2api_nv_module_claude_tu_dong.py` đỏ vì ép tuyệt đối. `dang_nhap()` cùng quy tắc
  (đường route mang `cach_dang_nhap` khác rỗng → google, trực tiếp không kèm cách → cũ).
- `muse2api`: `("google",)`; `khoi_phuc_tu_dong` nhận thêm tham số nhưng bỏ qua (luôn đường hồ sơ,
  không có form mật khẩu); `dang_nhap()` loại `google` → `can_nguoi` như đường mật khẩu
  (đăng nhập qua hồ sơ chỉ diễn ra ở `khoi_phuc_tu_dong`).

### Lõi
- `app/tuyen.py`: đường lưu đơn + lưu hàng loạt truyền `cach_dang_nhap`/`ho_so` vào kho;
  lưu đơn chế độ hồ sơ lấy email từ bản ghi hồ sơ khi thiếu email, không bắt mật khẩu, và kiểm
  hồ sơ phải là bản ghi đã lưu (`invalid_value` nếu không); `dang_nhap_tai_khoan_da_luu_noi_bo`:
  chế độ hồ sơ dựng `dong` loại hồ sơ (gắn `dong.cach_dang_nhap`, thuộc tính hồ sơ qua hằng),
  không bắt buộc bí mật. Mọi so sánh cách trong lõi dùng hằng bảng dữ liệu, không literal.
  Route chấp nhận cả khóa chuẩn `ho_so_google` lẫn bí danh `ho_so` (khung gửi bí danh để
  không gõ tên trường chuẩn trong `web/*` — xem mục giao diện).
- `app/tai_khoan_hang_loat.py`: `DongDaTach.loai` thêm `"google"` (route tự tạo trực tiếp;
  bộ tách dán vẫn chỉ tạo 3 loại cũ).
- `app/cong_mcp_cong_cu.py` (`_thu_khoi_phuc_module`): đọc cách hiệu lực từ bản ghi, truyền
  `cach_dang_nhap` (+ `ho_so_google`) chỉ khi chữ ký module nhận (kiểm `inspect`, tương thích module khác).
  Giãn cách đăng nhập hàng loạt 3600 giây đã có sẵn, chỉ kiểm chứng, không làm lại.
- `app/so_module.py` (`tinh_nang`): thêm `cach_dang_nhap_ho_tro` cho mỗi module — từ thuộc tính lớp
  nếu có, không thì suy từ cấu trúc (`dang_nhap` → email, `tai_dung_ho_so` → hồ sơ), giá trị suy
  cũng lấy từ hằng bảng dữ liệu.

### Giao diện (`web/He-thong-AI.dc.html`, khu vực `laDn`)
- Chip «Đăng nhập bằng» trong form thêm tài khoản, nhãn lấy từ giá trị API (viết hoa chữ đầu);
  chọn hồ sơ → chip chọn tài khoản hồ sơ đã lưu (lọc theo khả năng `dang_nhap_danh_tinh` của
  module từ dữ liệu API, không gõ tên module ở khung); chọn Email → email + mật khẩu (+ OTP)
  như cũ; module chỉ hỗ trợ hồ sơ (claude-web) thì chip Email vô hiệu kèm chú thích «chưa hỗ trợ».
- `themDangNhap` gửi `cach_dang_nhap` + bí danh `ho_so` trong payload tới `POST api/tai-khoan/da-luu`
  (lõi chấp nhận cả bí danh lẫn khóa chuẩn); chế độ hồ sơ không cần mật khẩu, thiếu hồ sơ đã
  chọn thì báo lỗi tại chỗ; hướng dẫn OTP và «Dán nhiều dòng» chỉ hiện ở chế độ Email.
  State `tkCachDn`/`tkHoSo` reset cùng mọi điểm reset `tkCachThem`/`tkThem`; lựa chọn cũ mà
  module hiện tại không hỗ trợ thì rơi về mặc định.
- Tuân thủ TRAN=0 của `test_web2api_doc_lap.py`: sau refactor, `web/*` không còn dòng nào chứa
  tên hãng (trừ dòng phông fonts.googleapis được matcher bỏ qua) — KHÔNG cần miễn trừ test nào.

### NV101 — phát hiện từ toàn suite và cách sửa (quan trọng)
Toàn suite lần đầu lộ đỏ mới do quy tắc «lõi/giao diện không mang tên hãng» (trần doc_lap = 0):
1. `test_web2api_tinh_nang.py` (3 test): dict chính xác thiếu trường mới → thêm
   `'cach_dang_nhap_ho_tro': []` vào kỳ vọng (có chủ đích); quét literal lõi + quét khung →
   sửa bằng dữ liệu (mục 2–3 dưới), KHÔNG miễn trừ.
2. Lõi (`app/*.py`): CHUYỂN GIÁ TRỊ + TÊN TRƯỜNG VÀO BẢNG DỮ LIỆU — thêm mục `cach_dang_nhap`
   (`ho_so`/`email`/`truong_ho_so`) vào `du_lieu/phan_loai_ai.json`, lõi chỉ đọc hằng
   (`CACH_HO_SO`/`CACH_EMAIL`/`TRUONG_HO_SO`); định danh mã lõi dùng `ho_so` (khóa bản ghi/API
   chuẩn vẫn là `ho_so_google` qua hằng). Đúng quy tắc ghi trong `_ghi_chu` của bảng («mọi tên
   cụ thể sống ở ĐÂY (dữ liệu)») và mẫu NV223. Test lõi xanh mà không cần miễn trừ.
3. Khung (`web/*`): nhãn chip lấy từ giá trị API (viết hoa chữ đầu); lọc hồ sơ theo khả năng
   module từ API; payload gửi bí danh `ho_so` (route chấp nhận cả hai khóa). Sau refactor,
   `web/*` không còn dòng nào chứa tên hãng (trừ dòng phông được matcher bỏ qua).
   Các miễn trừ đã thêm giữa chừng (NV225, tinh_nang UI) đều đã GỠ — test giữ nguyên độ chặt.
4. Claude: ép google tuyệt đối phá 7 test đường mật khẩu cũ → tinh chỉnh: chỉ ép khi lần gọi
   mang cách tường minh (khác rỗng); không mang cách thì giữ đường cũ.
Sau sửa: `test_web2api_tinh_nang.py`, `test_web2api_doc_lap.py`, `test_web2api_nv101_giao_dien.py`,
`test_web2api_nv225_giao_dien_tai_khoan.py`, `test_web2api_nv_module_claude_tu_dong.py` đều xanh;
NV300 10 test (thêm 1 test bí danh `ho_so`); các suite liên quan 558 xanh.

### Tài liệu
- `docs/CHUAN-MODULE.md` thêm mục 16 (cách theo từng tài khoản, khai báo lớp, không trộn NV223, T0–T3).

## Test
- Mới: `test/test_nv300_cach_dang_nhap.py` — 10 test, đỏ-trước-xanh (lần chạy đầu trên mã cũ:
  8 đỏ đúng lý do, 1 xanh là test giữ hành vi cũ đọc ngược; test bí danh thêm sau), sau khi làm
  xong: 10/10 xanh.
  Hai tài khoản grok-web (một hồ sơ, một Email) cùng chạy đúng đường của mình; route lưu hồ sơ
  không cần mật khẩu; Claude truyền `email` vẫn đi đường hồ sơ; kiểm chéo NV223 không suy thành hồ sơ;
  bí danh `ho_so` được chấp nhận như khóa chuẩn.
- Cập nhật có chủ đích: `test/test_web2api_grok-web.py` (manifest không còn `che_do_dang_nhap`),
  `test/test_web2api_nv225_giao_dien_tai_khoan.py` (miễn trừ NV300). Các test cũ sau giữ nguyên vì
  `_nap_tu` vẫn kiểm giá trị cũ: `test_web2api_nv90_grok_cloudflare.py`, `test_web2api_nv94_phan2.py:318`,
  `test_web2api_nv_module_grok_tu_dong.py:161`, `test_nv271_dnt_chuoi_dang_nhap_http.py:288`.
- Sửa fixture test NV300 (claude): module kiểm phiên qua client nhẹ `ClaudeWebClient` (nhận transport),
  không qua `MayKhachClaudeWeb` — fixture cũ chích nhầm lớp nên đi mạng thật và lỗi `loi_may_chu`.
- Liên quan: grok/claude/chatgpt/gemini + NV88/NV89 + MCP delegate + route/kho + NV271 A2/C3 — xanh
  (xem số liệu cuối báo cáo).
- Toàn suite (venv NV289, trừ 8 file chạy bù ở dưới): patch cuối 180 failed / 5896 passed /
  285 skipped / 31 xfailed / 20 errors; base `8ef3ca9` cùng lệnh: 180 failed / 5887 passed /
  285 skipped / 31 xfailed / 20 errors. Lệch duy nhất 2 test, cả hai đều xanh khi chạy lẻ
  (flake do tải máy, không liên quan patch): patch-lệch
  `test_web2api_gemini.py::test_models_bo_tien_to_dem_va_dung_ban_cu_khi_loi`,
  base-lệch `test_web2api_nv159_sua.py::test_c5_tran_tong_moc_mot_lan_goi`.
  → KHÔNG có đỏ mới do patch (180 đỏ còn lại có sẵn trên base: phần lớn do môi trường máy này
  — thiếu Chrome thật, thiếu dịch vụ ngoài, timeout mạng).
- Patch đã kiểm: áp sạch lên cây base `8ef3ca9` (`git apply --check` OK), NV300 + tinh_nang +
  doc_lap 56 xanh trên cây đã áp patch.
- Bandit trên các file sửa: 5 Low, giống hệt base, không phát hiện mới.
- Chưa chạy được ở máy này (lệch môi trường, không liên quan patch):
  `test_web2api_dang_nhap_tu_dong.py` (thiếu `pydantic_settings` ở cả hai venv);
  7 file muse2api ở venv NV289 (thiếu `curl_cffi`) — đã chạy bù bằng venv NV277, chỉ còn 1 lỗi
  có sẵn do thiếu `paho` ở venv đó (`test_moi_manifest_goi_thieu_rong`, modules/mqtt), đã kiểm
  trên base cũng đỏ y hệt; các test NV268 dùng Chrome thật error ở setup (không có Chrome thật).

## Lưu ý cho chủ máy / điều phối
- Tài khoản cũ chưa có `cach_dang_nhap` giữ hành vi cũ (grok đọc ngược cài đặt chung cũ;
  các module khác giữ đường mật khẩu). Tài khoản NV223 đăng nhập hộ KHÔNG bị đổi đường.
- Giao diện chưa kiểm bằng Chrome thật (máy này không có Chrome thật cho test NV268);
  nhờ chủ máy kiểm form chip Google/Email trên trình duyệt thật sau khi gộp.
- Không có bí mật, token, cookie, email thật, IP thật trong patch hay báo cáo này.
