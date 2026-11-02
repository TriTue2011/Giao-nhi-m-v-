# NV283 — Báo cáo: trạng thái đăng nhập thật + loại suy từ module (backend)

Nhánh cục bộ: `nv283-nv285` (từ main web2api `66d0a9b`), KHÔNG push.
Commit: `9b6c6ff` (NV283). Brief gốc: `giao/inbox/NV283.md` (đã đọc kỹ;
brief là nguồn thắng — không phát hiện điểm nào brief mâu thuẫn với
hướng dẫn triển khai; các điểm diễn giải ghi ở mục «Diễn giải»).

## Thay đổi

### 1. Sổ kết quả đăng nhập — một chỗ ghi duy nhất (`app/kho_tai_khoan.py`)

- Sổ phụ mới `bi_mat/_tai_khoan_da_luu_ket_qua_dang_nhap.json` (cùng cơ chế
  sổ phụ như `TEN_TRANG_THAI`: kho bí mật, quyền 0600), chỉ chứa dữ liệu
  không bí mật `{ket_qua, ma_loi, luc, co_phien, phien_het_han}` — không
  email ngoài id, không cookie/token/lý do tự do.
- `ghi_ket_qua_dang_nhap(id, ket_qua, ma_loi="", co_phien=None)`:
  `ket_qua` danh sách đóng `{thanh_cong, can_nguoi, that_bai}`; `ma_loi`
  chỉ lưu khi đúng hình `[A-Za-z0-9_-]{1,64}`, không thì suy từ mã HTTP
  (như `_ma_loi_an_toan` của hợp đồng đăng nhập); id lạ → `None` (không
  tạo bản ghi mới); ghi thành công xoá cờ `phien_het_han` cũ.
- `ghi_ket_qua_dang_nhap_tu_ket_qua(id, kq)` — HÀM BỌC CHUNG: phân loại kết
  quả (object hợp đồng hoặc dict) rồi ghi; lỗi ghi sổ chỉ `log.warning`
  có KIỂU lỗi, không làm hỏng kết quả đăng nhập (test nv45).
  Phân loại: `thanh_cong` → thanh_cong/co_phien True; cờ `can_nguoi`/
  `cho_2fa` hoặc mã trong `MA_LOI_CAN_NGUOI` (`can_nguoi`, `cho_2fa`,
  `can_ma_email`, `thu_thach_truoc_khi_dien`) → can_nguoi/co_phien None;
  còn lại → that_bai/co_phien False.
- `danh_dau_phien_het_han(id)`: đánh dấu phiên hết hạn THẬT; chỉ gọi khi
  lượt dùng/kiểm CÓ SẴN thấy 401 (xem §3), không gọi mạng thêm, không
  kiểm hàng loạt. Tài khoản chưa từng ghi kết quả vẫn đánh dấu được
  (phiên hết hạn là dữ liệu thật, không phải đoán «ok»).
- `xoa_tai_khoan` dọn luôn mục kết quả (vòng đời như trạng thái thử lại).
- `ban_cong_khai` thêm hai trường hợp đồng cứng cho MỌI bản ghi (kể cả
  bản ghi nhập): `dang_nhap` + `loai_hien_thi`. `liet_ke` đọc sổ phụ MỘT
  lần cho cả danh sách (không N+1 lần đọc tệp).

### 2. Mọi đường đăng nhập tìm được bằng grep + cách gom

Grep `\.dang_nhap\(` + `getattr(..., "dang_nhap")` + các hàm bọc
(`ham(dong)`, `ham_chay`, `QuanLyLuotChay`) trong `app/`. Kết quả: **6
điểm gọi hàm đăng nhập của module**, gom hết về hàm bọc chung:

| # | Đường | Vị trí | Ghi qua |
|---|-------|--------|---------|
| 1 | Một tài khoản `POST /da-luu/{id}/dang-nhap` | `tuyen.dang_nhap_tai_khoan_da_luu_noi_bo` | trực tiếp sau `await ham(dong)` |
| 2 | Theo module `POST /da-luu/dang-nhap-theo-module` | `tuyen.ham_chay` (trong route) | `ghi_ket_qua_theo_email` mỗi dòng (cả dòng ném lỗi → `loi_module`) |
| 3 | Hàng loạt dán văn bản `POST /dang-nhap-hang-loat/bat-dau` | `tuyen` bọc `_ham_dang_nhap_cua_module` | wrapper `ham_dang_nhap_ghi` |
| 4 | Tự động `POST /dang-nhap-tu-dong/bat-dau` (cả `truc_tiep` và `danh_tinh`) | `tuyen` bọc `ham_chay` sau khi chọn kiểu | wrapper `ham_chay_ghi` |
| 5 | Tự đăng nhập lại | `kho_tai_khoan.thu_dang_nhap_lai` (gọi từ `tu_lam_moi`) | trực tiếp sau `await dang_nhap(dong)`; ngoại lệ → `loi_module` |
| 6 | MCP `dang_nhap_bat_dau` | `cong_mcp_cong_cu._chay_dang_nhap` | qua đường 1 khi fallback `noi_bo`; RIÊNG đường `khoi_phuc_tu_dong` ghi tại `_chay_dang_nhap` (tránh ghi đúp) |

Không ghi (có lý do, đã cân nhắc): module chưa triển khai `dang_nhap`
(502 `chua_ho_tro`) và tài khoản tạm dừng (403 `tam_dung`) — đăng nhập
chưa từng chạy nên không thể ghi «thất bại»; trạng thái giữ «chua».
Đường `…/ma-2fa` (tiếp nối lượt đăng nhập, không gọi `dang_nhap`) và
luồng liên kết Codex OAuth (không phải `dang_nhap` của module) không
thuộc phạm vi grep của brief §2a — xem câu hỏi trong `hoi-nv283.md`.

### 3. Hết hạn phiên thật

- `luong_dung_tai_khoan.ghi_luot`: lượt dùng CÓ SẴN thấy HTTP 401 →
  `danh_dau_phien_het_han` (bảo vệ: id không phải tài khoản đã lưu thì
  không ghi; lỗi đánh dấu chỉ log, không hỏng ghi lượt). Giãn cách tự
  đăng nhập mỗi giờ giữ nguyên (không đổi `gian_cach_giay`, không thêm
  lượt kiểm nào).
- Route `suc-khoe` của module vẫn passthrough nguyên trạng (mỗi module
  một hình sức khoẻ khác nhau, lõi không dò hình theo tên để đánh dấu —
  xem câu hỏi trong `hoi-nv283.md`).

### 4. Hợp đồng công khai (`GET /api/tai-khoan/da-luu`)

- Mỗi bản ghi thêm:
  `"dang_nhap": {"trang_thai": "ok"|"can_xu_ly"|"loi"|"chua",
  "luc": epoch|0, "ma_loi": ""|mã, "co_phien": true|false|null}` —
  ok = lần gần nhất thành công VÀ chưa thấy phiên hết hạn; can_xu_ly =
  cần người HOẶC phiên hết hạn thật; loi = thất bại gần nhất; chua = chưa
  có số liệu (KHÔNG đoán ok).
- `"loai_hien_thi"` KHÔNG BAO GIỜ rỗng, suy theo nguyên tắc (không bảng
  từ khoá tên module trong lõi):
  1. `loai_tai_khoan` người dùng đặt → tên hiển thị trong bảng phân loại;
  2. nhãn `loai_tai_khoan_ten` trong manifest của module sở hữu (đọc lúc
     import, như cơ chế hợp nhất manifest của bảng phân loại);
  3. không module → `kieu_bi_mat` (mat_khau → «Mật khẩu»,
     khoa_api/token/cookie → «API»); bản ghi nhập → tên nhóm theo nguồn.
- Phản hồi `da-luu` thêm tổng `"can_xu_ly"` = số tài khoản ở trạng thái
  công khai `can_xu_ly` + `loi` (trừ tạm dừng; đếm trên danh sách đã lọc
  `?nhom` nếu có). Tài khoản tạm dừng vẫn `trang_thai` = `"tam_dung"`.

### 5. Manifest (`loai_tai_khoan_ten` + nâng `phien_ban`)

| Module | `loai_tai_khoan_ten` | `phien_ban` |
|---|---|---|
| chatgpt-web | Web | 0.1.1 → 0.1.2 |
| gemini-web | Web | 0.1.1 → 0.1.2 |
| claude-web | Web | 0.1.1 → 0.1.2 |
| grok-web | Web | 0.1.1 → 0.1.2 |
| openaicodex | Codex | 0.1.1 → 0.1.2 |
| muse2api | Web (giao thức web muse.ai, không phải khoá API) | 0.2.2 → 0.2.3 |
| gemini-api | API | 0.2.0 → 0.2.1 |
| grok-api | API | 0.1.0 → 0.1.1 |

Mỗi module đúng một dòng thêm + một dòng phiên bản (không viết lại tệp).
Module khác chưa khai trường này thì lõi rơi về `kieu_bi_mat` (đúng thiết
kế fallback, không phải lỗi).

### 6. Tài liệu

- `docs/THAM-CHIEU.md`: mục tài khoản đã lưu (sổ phụ, hợp đồng
  `dang_nhap`/`loai_hien_thi`, tổng `can_xu_ly`) + mục NV285.
- `docs/CHUAN-MODULE.md`: trường tuỳ chọn `loai_tai_khoan_ten` + hai khả
  năng tuỳ chọn NV285.

## Diễn giải (không mâu thuẫn brief, ghi để điều phối duyệt)

1. Brief §2e ghi tổng «can_xu_ly» là «số tài khoản can_nguoi/that_bai/
   phien_het_han»; hợp đồng §3 gộp chúng thành hai trạng thái công khai
   `can_xu_ly` + `loi` — tổng đếm cả hai (trừ tạm dừng).
2. Brief §2c nhắc «kiểm sức khoẻ (suc-khoe) mà một phiên 401 thì đánh
   dấu»: đã làm ở lượt DÙNG thấy 401 (điểm chung duy nhất có id tài
   khoản đã lưu + mã HTTP, không dò hình module); route suc-khoe
   passthrough chưa nối đánh dấu — xem câu hỏi.
3. Giãn cách: brief ghi «mặc định 3600 s» cho tự đăng nhập nhưng mã hiện
   tại `kho_tai_khoan.gian_cach_giay` mặc định 300 s (env
   `WEB2API_DANG_NHAP_GIAN_CACH_GIAY`); không đổi giá trị này (ngoài
   phạm vi), chỉ giữ nguyên cơ chế.

## Kết quả test (thật, module giả, conftest chặn Internet)

`test/test_nv283_trang_thai_dang_nhap.py`: **17/17 xanh**, gồm:

- 1 tài khoản: thành công → ok/co_phien True/loai Web; cần người
  (CAPTCHA `thu_thach_truoc_khi_dien`, 2FA `cho_2fa`) → can_xu_ly; sai
  mật khẩu → loi + đúng ma_loi; module không hỗ trợ → 502 và vẫn chua;
  tạm dừng → 403, vẫn tam_dung + chua; lỗi ghi sổ (patch `_ghi_ket_qua`
  ném) → đăng nhập vẫn thành công + log warning (nv45).
- Hàng loạt theo module 5 tài khoản (3 ok, 1 cần người, 1 lỗi, thứ tự
  xen kẽ để không chạm luật dừng sau 2 hỏng liên tiếp của `LuotChay`) →
  sổ ghi đúng 5 kết quả, không ghi chéo, `can_xu_ly` = 2; chạy lại lần 2
  → kết quả không đổi (không ghi trùng sai).
- Hàng loạt dán văn bản qua `QuanLyLuotChay` → đúng 5 kết quả.
- Đăng nhập tự động (`truc_tiep`) qua `QuanLyLuotChay` → ok + loi đúng.
- Giãn cách: `LuotChay` với đồng hồ/ngủ giả, giãn cách 5 s → ngủ đúng
  [5.0, 5.0] giữa 3 dòng (không chờ thật).
- Tự đăng nhập lại (`thu_dang_nhap_lai`) → ok.
- Lượt dùng thấy 401 → ok thành can_xu_ly; ghi thành công lại → hết cờ.
- MCP `_chay_dang_nhap` qua `khoi_phuc_tu_dong` → phiên thanh_cong và
  sổ ghi ok (đường fallback qua `noi_bo` đã có test ở đường 1).
- Đo 30 tài khoản module chatgpt-web → `loai_hien_thi` = «Web» cho cả 30,
  không còn «Chưa phân loại»; `can_xu_ly` có trong phản hồi.
- Loại theo `kieu_bi_mat` khi không module: khoa_api → «API».
- Kiểm hình: ket_qua sai → `LoiKhoTaiKhoan`; id lạ → `None`.

Toàn bộ suite + bandit: xem báo cáo tổng hợp ở cuối báo cáo NV285
(chạy chung sau NV285); riêng file NV283 + NV285: 26/26 xanh.

## Chỗ chưa kiểm — nói thật

- Chưa thử với ChatGPT/Google thật (không tài khoản thật, không đăng nhập
  thật trong test, đúng ranh giới). Đặc biệt: 27 token 401 trong brief
  (module giữ, lõi chưa từng đăng nhập qua core) sẽ chỉ chuyển sang
  can_xu_ly khi có lượt dùng/kiểm 401 MỚI đi qua `ghi_luot`, hoặc sau lần
  đăng nhập tiếp theo qua core — sổ phụ không tự quét ngược lịch sử
  module (không có dữ liệu lịch sử đó trong lõi).
- Chưa kiểm trên container thật / giao diện NV282 (agy làm phần giao diện;
  hợp đồng trường giữ nguyên tên theo brief §3).
- `loai_tai_khoan_ten` đọc lúc import: module cài thêm sau khi lõi chạy
  cần khởi động lại mới nhận nhãn (cùng giới hạn như bảng phân loại hiện
  tại).
