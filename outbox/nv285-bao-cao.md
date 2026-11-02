# NV285 — Báo cáo: API chi tiết một tài khoản (limit, đã dùng, phiên)

Nhánh cục bộ: `nv283-nv285` (từ main web2api `66d0a9b`), KHÔNG push.
Commit: `305dc29` (NV285), trên commit NV283 `9b6c6ff`. Brief gốc:
`giao/inbox/NV285.md` (đã đọc kỹ; brief là nguồn thắng — các điểm diễn
giải ghi ở mục «Diễn giải»). Dùng lại đúng hàm bọc NV283, không tạo sổ
thứ hai.

## Thay đổi

### 1. Helper lõi mới (`app/chi_tiet_tai_khoan.py`)

- `LAM_MOI_GIAN_CACH_GIAY = 60` (hằng số có tên), mốc làm mới theo id
  trong bộ nhớ tiến trình (`con_lai_lam_moi_giay` / `danh_dau_lam_moi`).
- `chuan_hoa_han_muc` / `chuan_hoa_muc`: chỉ giữ trường đã biết trong
  khuôn chuẩn; trường lạ (token, cookie, email…) trong dữ liệu module bị
  LOẠI, không ra phản hồi. Module trả `None`/không có mục có số liệu →
  `{"nguon": "khong_biet", "cap_nhat_luc": 0, "muc": []}`.
- `lay_han_muc_tu_module(so, ban_ghi)`: gọi khả năng tuỳ chọn
  `chi_tiet_tai_khoan(email)` của module sở hữu (đồng bộ hoặc coroutine),
  CHỈ ĐỌC bộ đệm — không gọi mạng. Module không chạy/không khai/không có
  số → thử hạn mức thụ động từ tiêu đề (`nguon: "tieu_de"`, `muc: []` —
  tiêu đề chung không có mục từng tính năng nên không bịa mục «chung»
  thành tính năng); không có gì → `khong_biet`. Lỗi module → log.warning
  có kiểu lỗi, trả `khong_biet` (không hỏng route).
- `dung_thong_ke(id)`: cửa sổ 14 ngày từ `luong_dung_tai_khoan` —
  `hom_nay`, `7_ngay`, `thanh_cong` (tổng `luot` — chỉ đếm lượt thành công),
  `that_bai` (tổng `loi_han_muc + loi_het_phien + loi_khac`), `theo_ngay`
  tối đa 14 mục `{ngay, so_luot}`, `lan_dung_cuoi` (thêm
  `luong_dung_tai_khoan.lan_dung_cuoi` đọc `thay_lan_cuoi`). Bộ đếm tách
  được nên không bao giờ phải trả null với lược đồ hiện tại (null giữ
  trong hợp đồng cho lược đồ tương lai).
- `duong_cong_khai`: trạng thái từng đường từ `lay_trang_thai_duong`,
  xếp theo thứ tự ưu tiên đường của `duong_dung` (codex trước, rồi web).
- Hạng (`lap_bang_hang`, `thu_tu_xoay_cua_nhom`, `tinh_tong_quan`,
  `dem_tong_quan`): xem §3.

### 2. Routes mới (`app/tuyen.py`, router `/api/tai-khoan`, đã có QT)

- `GET /api/tai-khoan/da-luu/{id}/chi-tiet` → 200 khuôn §3b: bản công khai
  (`id`, `email_che`, `nhan`, `module_id`, `nhom`, `bac_goi`,
  `loai_hien_thi`, `trang_thai`) + `dang_nhap` + `loai_hien_thi` (NV283) +
  `goi` + `dung` + `duong` + `han_muc` (mỗi mục thêm `hang` và
  `giu_hang_1_cua_nhom`). Id lạ HOẶC bản ghi nhập → 404 chung chung
  (`khong_tim_thay`, không phân biệt «không có» với «của module khác»).
  Email đầy đủ chỉ khi `?hien_email=true` (cùng quy tắc `da-luu`).
- `POST /api/tai-khoan/da-luu/{id}/chi-tiet/lam-moi` (cần step-up): MỘT
  tài khoản, gọi `lam_moi_han_muc(email)` của module đó MỘT lần; quá sớm
  → 429 kèm `cho_lai_sau_giay` (trần 60); module không chạy/không khai →
  502 `chua_ho_tro`; module ném/không trả dữ liệu → 502 `loi_module`
  (không tiêu giãn cách khi module ném, cho phép thử lại ngay); tạm dừng
  → 403 `tam_dung`; thành công → `{"ok": true, "chi_tiet": …}` (khuôn
  mới). Không bao giờ lặp qua nhiều tài khoản.
- `GET /api/tai-khoan/tong-quan?nha=&duong=` (chỉ đọc, quản trị): xem §3.
- Hỗ trợ trong kho: `tat_ca_ban_ghi()` (bản ghi nội bộ, CHỈ dùng trong
  lõi — route API vẫn dùng `ban_cong_khai`).

### 3. Tổng quan + hạng xoay vòng

- Lọc theo `nha` (nhóm hiệu lực) và `duong` (đích dùng chính, không có
  thì `dung_cho` đầu); không truyền tham số → đếm toàn kho, hạng tính
  riêng theo từng (nhà, đường).
- Đếm: `tong`, `binh_thuong` (= đăng nhập ok VÀ không mục nào cạn),
  `can_xu_ly`, `loi`, `tam_dung`, `chua_biet` (= chưa có kết quả đăng
  nhập). Tài khoản ok nhưng CẠN hạn mức không rơi vào ô trạng thái nào
  — chỉ đếm ở `het_limit_theo_muc` (dải tổng hợp vẽ riêng hàng «Hết
  limit theo mục», đúng demo NV282 v9).
- `het_limit_theo_muc`: CHỈ mục mà nhóm có số liệu (mục có số liệu =
  có `con_lai`/`tong`/`da_dung_pct`); cạn = `con_lai <= 0` hoặc
  `da_dung_pct >= 100`. Nhóm không có mục nào → mảng rỗng +
  `co_so_lieu_han_muc: false`.
- Hạng #n: thứ tự xoay vòng THẬT — thứ tự tài khoản trong
  `liet_ke_tai_khoan` của chính module sở hữu (thứ tự module thử các tài
  khoản khi phục vụ); tài khoản không có trong danh sách module xếp sau
  theo thứ tự liệt kê của kho (`cap_nhat` giảm dần). `duong_dung.chon_duong`
  chỉ là thứ tự ĐƯỜNG trong một tài khoản (codex trước web), đã dùng cho
  `duong` trong chi-tiet — không dùng làm thứ tự tài khoản (ghi rõ để
  tránh hiểu lầm: brief nhắc `dd_mod.chon_duong` nhưng đó là chọn đường,
  không phải chọn tài khoản).
- Ứng viên xếp hạng: không tạm dừng, `dang_nhap` = ok, còn lượt ở mục đó
  (không cạn mục, không hết hạn mức cấp tài khoản qua
  `luong_dung.con_het_han_muc`). `giu_hang_1`: một phần tử cho mỗi (nhóm,
  mục) có người giữ: `{nhom: "chatgpt/web", muc, tai_khoan_id, email}` —
  email theo quy tắc công khai (`email_che` mặc định, đầy đủ khi
  `?hien_email=true`).

### 4. Bảng module nào trả hạn mức gì

| Module | `chi_tiet_tai_khoan` | `lam_moi_han_muc` | Hạn mức trả |
|---|---|---|---|
| chatgpt-web | Có | Có (1 lần `init` `/backend-api/me`) | `limits_progress` từ bước init, giữ vào đối tượng tài khoản trong bộ nhớ + `han_muc_luc` (cả ở `_init_tai_khoan` và `_kiem_token`); gói từ `tk.goi`. Parser chấp nhận danh sách mục hoặc bản đồ tên→mục, đọc các khoá số đã biết (remaining/limit/used_percent/reset_at/reset_after_seconds + biến thể). **Hình dạng thật từ nhà cung cấp CHƯA được kiểm** (xem hỏi). |
| openaicodex | Có | Có (1 lần `han_muc.lam_moi` — chỉ ra mạng khi bản quá TTL 120 s, còn không trả bộ đệm) | Cửa sổ chính/phụ từ `han_muc.kho_han_muc` (chỉ % đã dùng + mốc hồi; `con_lai`/`tong` = null — không bịa số lượt từ %); gói từ `tk.plan`. |
| Mọi module khác (gemini-web, claude-web, grok-web, muse2api, gemini-api, grok-api, …) | Không khai | Không khai | Lõi trả `khong_biet` (hoặc `tieu_de` nếu có hạn mức thụ động từ tiêu đề). Không bịa số. |

### 5. Tài liệu

- `docs/THAM-CHIEU.md`: 3 route + khuôn trả + định nghĩa đếm/hạng.
- `docs/CHUAN-MODULE.md`: hai khả năng tuỳ chọn mới + bảng module đã khai.

## Diễn giải (không mâu thuẫn brief, ghi để điều phối duyệt)

1. `goi` theo hợp đồng đóng chỉ `plus|free|khong_biet`: bậc `pro`/team
   (chatgpt-web có `pro`, openaicodex `plan` có thể là pro/team) hiện gộp
   vào `khong_biet` — xem câu hỏi có mở rộng hợp đồng không.
2. `tieu_de`: chỉ dùng khi module không có khả năng/số liệu nhưng sổ
   lượng dùng có hạn mức thụ động từ tiêu đề; `muc` luôn rỗng (tiêu đề
   chung không phân tách theo tính năng).
3. `duong` trong chi-tiet trả đích dùng thật của tài khoản (web/codex/
   api/gemini/antigravity…) chứ không chỉ web|codex như ví dụ §3b (ví dụ
   đó minh hoạ cho nhóm chatgpt).
4. `lam-moi` khi module trả `None` (không có dữ liệu sau khi đã gọi) →
   502 `loi_module` nhưng VẪN tiêu giãn cách (đã gọi nhà cung cấp một
   lần); chỉ khi module NÉM mới không tiêu giãn cách.
5. NV285 phụ thuộc NV283: cùng nhánh, dùng lại sổ phụ NV283, không sổ
   thứ hai.

## Kết quả test (thật, module giả, conftest chặn Internet)

`test/test_nv285_chi_tiet_tai_khoan.py`: **9/9 xanh**, gồm:

- Khuôn trả đủ trường với module có/không có `chi_tiet_tai_khoan`
  (module có → `nguon: module`, `goi: plus`, mục đúng số, `hang: 1`,
  `giu_hang_1_cua_nhom` đúng id; module không có → `khong_biet` + `goi:
  khong_biet`).
- Hạn mức đã biết hiển thị đúng (con_lai 5/tong 20, reset_sau_giay 3600).
- Hạn mức thụ động từ tiêu đề → `nguon: tieu_de`, `muc: []`.
- `lam-moi` giãn cách: lần 1 → 200 + module được gọi đúng 1 lần; lần 2
  trong hạn → 429 kèm `cho_lai_sau_giay` trong (0, 60], module không bị
  gọi lại; module không hỗ trợ → 502; tạm dừng → 403.
- IDOR/404: id lạ → 404; chi-tiet của A không chứa email tài khoản
  khác; quét toàn bộ phản hồi mẫu: chuỗi token/cookie giả cấy trong
  trường lạ của module và mật khẩu tài khoản đều KHÔNG xuất hiện.
- Xác thực: không khoá → 401; khoá lạ → 401; khoá khách đúng nhưng sai
  phạm vi (chỉ chat) → 403.
- Thống kê dùng: 3 lượt 200 + 2 lượt 500 → `hom_nay`/`7_ngay` = 3,
  `thanh_cong` = 3, `that_bai` = 2, `theo_ngay` 1 dòng `so_luot` 3,
  `lan_dung_cuoi` > 0.
- Tổng quan nhóm chatgpt/web (4 tài khoản, thứ tự module d,a,b,c):
  `tong` 4, `binh_thuong` 2, `chua_biet` 1, `het_limit` image_gen
  (can 1 / co_so_lieu 4), `giu_hang_1` = d; hạng chi-tiet: d=1, a=2,
  b (cạn)=None, c (chưa đăng nhập)=None; nhóm google/web rỗng →
  `het_limit` [], `co_so_lieu_han_muc` false, `giu_hang_1` [].

## Kiểm chứng tổng hợp (NV283 + NV285)

- Test mới + liên quan: NV283 17/17 + NV285 9/9 = **26/26 xanh**.
- Toàn bộ suite (chạy với `--ignore=test/test_web2api_dang_nhap_tu_dong.py`
  vì file này lỗi collection có sẵn cả trên main: thiếu `pydantic_settings`
  rồi `test.gia` không import được khi thiếu `test/__init__.py`):
  nhánh **64 failed, 6186 passed, 239 skipped, 31 xfailed, 18 errors**;
  main sạch **60 failed, 6164 passed, 239 skipped, 31 xfailed, 18 errors**.
  So sánh diff danh sách đỏ: ban đầu có 5 đỏ mới do NV283/NV285
  (README thiếu đường lam-moi, NV45 nuốt lỗi, pin phien_ban gemini-api,
  doc_lap nhắc tên nhà cung cấp, phân loại trường loai_tai_khoan_ten)
  — cả 5 đã sửa ở commit `1d7cb84` và `7c54a56`, kiểm lại bằng test
  đích danh: 37 passed, chỉ còn README đỏ duy nhất do đường
  `trinh-duyet/{module}/man-hinh` có sẵn (chạy trên main sạch cũng đỏ
  đúng đường đó). NV85 chatgpt-web cũng đỏ sẵn trên main
  (`api.openai.com` trong `lam_moi_jwt.py`), không phải do nhánh này.
  **Kết luận: sau 2 commit sửa, nhánh không còn đỏ mới so với main.**
  Lưu ý: suite nhánh chạy trước 2 commit sửa; 2 commit chỉ đổi tài liệu,
  dòng log và phân loại trường, đã kiểm bằng test đích danh thay vì
  chạy lại toàn bộ 17 phút.
- Bandit: `bandit -r app modules -lll` thoát 0, 0 issue ở ngưỡng,
  High = 0, cả nhánh và main sạch (diff đầu ra rỗng).
- Quét bí mật/IP trên diff `main...HEAD`: sạch (chỉ chuỗi giả rõ ràng
  `TOKEN-GIA-NV285-…`, `MatKhauGia123!`, email `example.com`).
- Patch: `~/workspace/nv283-nv285/nv283-nv285.patch` (21 file,
  2084 insertions, 14 deletions) — `git apply --check` trong clone tạm
  từ main: **OK**.

## Chỗ chưa kiểm — nói thật

- Chưa gọi nhà cung cấp thật (không tài khoản thật): hình dạng
  `limits_progress` của chatgpt-web, cửa sổ wham của openaicodex trên
  tài khoản thật, và gói `pro`/team đều chưa được xác nhận bằng dữ liệu
  thật.
- Module chưa có số liệu hạn mức: gemini-web, claude-web, grok-web,
  muse2api, gemini-api, grok-api và mọi module khác — giao diện sẽ thấy
  `khong_biet` cho các tài khoản đó cho tới khi module khai khả năng.
- Hạng xoay vòng dùng thứ tự `liet_ke_tai_khoan` của module: module
  không chạy hoặc không khai liệt kê thì rơi về thứ tự kho (không phải
  thứ tự xoay nội bộ thật của module đó nếu nó xoay khác).
- Chưa kiểm trên container thật / giao diện NV282.
