# NV300 BỔ SUNG — Báo cáo

## KẾT QUẢ

**Đã xong và đã đẩy.** Nhánh Giao mới **`muse/nv300-bo-sung`** (không đẩy vào nhánh `muse/nv300` đã có):
`outbox/nv300-bo-sung.patch` (14 file, 920 dòng thêm, 79 dòng bớt, 1442 dòng patch) +
`outbox/nv300-bo-sung-bao-cao.md` (file này).

**Thứ tự gộp bắt buộc: NV300 gốc trước, rồi bổ sung này.** Patch bổ sung KHÔNG chứa lại thay đổi NV300 gốc:
nó là delta từ lớp NV300 gốc (`8d9ba45`) lên cây cuối. Lý do: web2api main `8ef3ca9` chưa chứa NV300 gốc
(đã kiểm bằng grep `cach_dang_nhap` trong `app/kho_tai_khoan.py` — không có).

**Nền đọc:** Giao main `8b00fce`, `inbox/NV300.md` blob `cd2fa2d5` — file KHÔNG đổi trong lúc làm
(đã kiểm lại lúc nộp). 1 tài khoản được loại trừ khỏi di trú theo dặn (không nhắc lại địa chỉ ở đây).

## Làm gì (theo đúng 4 mục bổ sung)

### 1. Kho tài khoản phân vùng theo provider — `app/kho_tai_khoan.py`
- `ma_tai_khoan(email, module_id="")`: không module → id cũ (băm riêng email, đọc ngược kho cũ);
  có module → băm `module_id + NUL + email`. Cùng Gmail ở Gemini, Grok, Claude, ChatGPT thành các bản
  ghi độc lập, mỗi bản có phiên/token/trạng thái/lịch lấy lại phiên riêng.
- `_doc()` chấp nhận cả id cũ và id phân vùng cho bản ghi kiểu `mat_khau` (bản ghi kiểu khác giữ nguyên).
- `luu_tai_khoan` (đường không truyền id, kiểu `mat_khau`): thứ tự tìm — (1) id phân vùng (email, module);
  (2) bản ghi cũ id-theo-email mà chưa mang module hoặc mang đúng module → cập nhật tại chỗ, giữ id cũ;
  (3) không có thì tạo mới với id phân vùng. Không nhân đôi, không mất bản ghi.
- Mới: `tim_theo_email_va_module(email, module_id)`; `xoa_tai_khoan` đã theo id nên xoá một provider
  không chạm provider khác (có test chứng minh).
- Mới: `di_tru_khoa_theo_provider(du_lieu, loai_tru=())` — hàm thuần, KHÔNG tự chạy khi đọc kho, chỉ để
  chủ máy/điều phối gọi lúc di trú: đổi khoá các bản ghi có module_id sang id phân vùng (sửa cả trường
  `id` trong bản ghi), bỏ qua email trong `loai_tru` và bản ghi không module, đụng khoá đích thì giữ bản
  ghi đích. Không nhúng địa chỉ email thật nào vào code.
- `thu_dang_nhap_lai` chọn bản ghi đúng provider trước (bản ghi cũ chưa mang module vẫn dùng được qua
  đường rút về). Vòng nền đã độc lập theo module từ trước (`QuanLyTuLamMoi` một `VongTuLamMoi` cho mỗi
  module_id, sổ lần kiểm key theo `(module_id, khoa)`); bổ sung test chứng minh lỗi/dừng một vòng không
  ảnh hưởng vòng khác và `dong_hoa` chỉ gỡ vòng của module đã đi.
- **Sửa thêm sau khi đối chiếu test cũ (quan trọng):** `ghi_ket_qua_theo_email(email, kq, module_id=None)`
  — ba điểm gọi ở `app/tuyen.py` (đăng nhập hàng loạt, đăng nhập theo module với `module_so_huu` là chủ
  sở hữu bản ghi, đăng nhập tự động) đều truyền module của lượt chạy, nên kết quả hàng loạt ghi đúng bản
  ghi provider, không ghi chéo. Không truyền module thì đường cũ theo email.

### 2. Quy tắc nghiệm thu lỗi «thêm bằng email nhưng lại đăng nhập qua Google» — `modules/grok-web/module.py`
- Nguyên nhân: `cach_dang_nhap_cua` rớt về cài đặt chung cũ (`google`) khi tài khoản không ghi cách riêng,
  dù tài khoản thêm bằng email (kho riêng của module không có bản ghi đó) — đúng lỗi đã báo.
- Sửa: `cach_dang_nhap_cua(..., co_mat_khau=...)` ưu tiên: gợi ý tường minh → đã ghi theo tài khoản →
  «email» nếu lần gọi mang mật khẩu → cài đặt chung cũ. Áp cho `dang_nhap` (nhánh `mat_khau` với
  `co_mat_khau=True`, nhánh `dang_nhap_lai` đọc mật khẩu đã lưu trước rồi truyền theo đó), `dang_nhap_tu_dong`
  (tầng b), `khoi_phuc_tu_dong` (T2: đọc mật khẩu đã lưu TRƯỚC rồi mới giải cách) và fallback trong
  `_dang_nhap_bang_trinh_duyet` (mật khẩu hiện diện ⇒ email). Đường lõi đã đúng, không sửa.
- Ranh giới giữ nguyên, có test chốt: không mật khẩu + không cách riêng + cài đặt chung google → vẫn đi
  đường hồ sơ như cũ (đọc ngược). Các module khác đã đúng, chỉ thêm test hồi quy: chatgpt-web, gemini-web
  (email ⇒ form trực tiếp, google ⇒ hồ sơ, không điền mật khẩu), claude-web (kể cả `cach=email` tường
  minh vẫn đi đường google), muse2api (`mat_khau` ⇒ `can_nguoi`, không có form).

### 3. Đường «trực tiếp» của Grok — `modules/grok-web/module.py`
- `_URL_DANG_NHAP`: `https://x.com/login` → **`https://grok.com/sign-in`** (form email+mật khẩu của chính
  grok.com, theo mẫu chatgpt-web). Lý do: x.com/login sai với tài khoản email vì hotmail/outlook không
  phải tài khoản X.
- Bước điền mới: điền `email` → bấm `tiep_tuc` (nút «Tiếp tục») → điền `mat_khau` → bấm `dang_nhap`.
  **Lưu ý cho dịch vụ máy đăng nhập:** khoá logic mới `tiep_tuc` — bộ điều khiển trình duyệt thật phải map
  khoá này sang nút Tiếp tục ở bước email của grok.com/sign-in (phần map nằm ngoài repo web2api).
  Chọn phần tử theo vai trò/cấu trúc, không dựa duy nhất vào chữ tiếng Việt.
- Đường google không đổi (mở `grok.com/` rồi bấm nút «Tiếp tục với Google»).
- **Chưa kiểm trên trình duyệt thật — NV293 sẽ thử thật** đường grok.com/sign-in mới này.

### 4. Claude tạm thời chỉ Google
- Không đổi code (đã chỉ google từ NV300 gốc); bổ sung test hồi quy ở cả `dang_nhap` và `khoi_phuc`.
  Grok cả hai cách; ChatGPT/Gemini giữ như hiện có, sửa theo nguyên tắc «theo từng tài khoản».

### Docs — `docs/CHUAN-MODULE.md`
- Thêm mục 17 nối tiếp mục 16 của NV300 gốc: khoá phân vùng, helper di trú, quy tắc email/Google,
  đường Grok mới + ghi chú map `tiep_tuc`, ghi kết quả hàng loạt theo (email, module).

## Quyết cần chủ máy biết (đã áp, ghi rõ để khỏi hiểu nhầm)

1. **NV300 bổ sung THẮNG NV224 ở đúng chỗ phân vùng.** NV224 từng chốt «một bản ghi/email, `dung_cho`
   tích lũy»; NV300 bổ sung (mới hơn) chốt khoá = `(module_id, email)`. Theo bài học NV98 (cập nhật test cũ
   theo hành vi mới), đã cập nhật 2 test cũ: NV217e (gemini-web + antigravity → 2 bản ghi độc lập, mỗi bản
   `dung_cho` chỉ có đích của chính nó) và NV224 `dung_cho_tich_luy_qua_route` (tương tự). Tích lũy
   `dung_cho` vẫn giữ nguyên TRONG một bản ghi provider. Nếu chủ máy muốn giữ NV224 cho các module cùng
   nhóm Google thì cần chốt lại — patch hiện tại theo đúng chữ của file NV300 bổ sung (`module_id`).
2. **Bản ghi cũ chưa mang module được «nhận» về provider đầu tiên lưu nó** (giữ id, không nhân đôi);
   provider thứ hai lưu cùng email sẽ tạo bản ghi mới. Đây là ngữ nghĩa di trú dần, không làm mất dữ liệu.
3. **`module_id` trong `thu_dang_nhap_lai` là provider SỞ HỮU bản ghi, không phải executor.** Test NV217d
   đã sửa theo đó (gọi bằng module sở hữu; đối tượng thực hiện vẫn là executor). Caller sản xuất
   (`app/tu_lam_moi.py`) đã truyền đúng module sở hữu nên không đổi code đó.

## Test

- **Đỏ-trước-xanh:** file mới `test/test_nv300_bo_sung.py` (24 test) — 9 test phần mới đỏ trước khi sửa
  (6 kho + 3 Grok), xanh sau khi sửa; 2 test `ghi_ket_qua_theo_email` thêm sau khi phát hiện luồng hàng
  loạt ghi chéo. Cuối cùng: venv NV289 **23 passed, 1 skipped** (muse2api thiếu dep `google` ở venv đó);
  venv NV277 **24 passed**.
- **Tập liên quan cuối (12 file, đúng cây nộp): 196 passed, 1 skipped.**
- **Test cũ sửa có lý do (không nới kiểm):** các test key trang giả bằng `x.com/login` đổi sang
  `grok.com/sign-in` + thêm bước `tiep_tuc` (nv89, nv90, nv90-cloudflare, nv-module-grok-tu-dong, nv271,
  nv300); 3 test google cũ của nv90-cloudflare chuyển sang cách google tường minh theo tài khoản (mật khẩu
  hiện diện không còn rớt về cài đặt chung); test nv94 grok-google truyền `cach_dang_nhap="google"` tường
  minh; test NV217d/NV217e/NV224 theo quyết mới (mục trên).
- **Toàn suite đối chiếu (cùng danh sách bỏ qua 8 file muse2api thiếu dep ở venv NV289):**
  base NV300-gốc `8d9ba45`: 161 failed / 17 errors; cây patch (trước khi sửa 6 test): 187 failed /
  20 errors. Diff theo tên test: **base-only = rỗng** (không test nào base đỏ mà patch xanh); patched-only
  = đúng 6 test đã sửa (nay xanh) + cụm nv192 (ảnh AI) và 1 test hiệu năng — cụm này chạy riêng đều xanh
  60/60 trên CẢ hai cây nên là flake do tải, không phải do patch. 7 file muse2api (venv NV277): 247 passed
  + 1 lỗi giống hệt trên base (thiếu gói `paho` ở venv). File `test_web2api_dang_nhap_tu_dong.py` lỗi
  collect giống hệt trên base (repo không có `test/__init__.py` nên `test.gia` bị stdlib `test` chiếm).
- **Bandit** trên `app/kho_tai_khoan.py`, `app/tuyen.py`, `modules/grok-web/module.py`: High 0, Medium 0
  (2 Low là code có sẵn từ trước, không phải diff mới). **Quét bí mật** trên patch: sạch (chỉ có địa chỉ
  `@example.com` giả trong test, không khoá/mật khẩu/token/email thật/IP thật).

## Chưa kiểm

- Giao diện chưa kiểm trên Chrome thật (patch không đổi giao diện, chỉ lõi + module + test).
- Đường grok.com/sign-in mới chưa kiểm trên trình duyệt thật — NV293 sẽ thử thật (cả hai kiểu đăng nhập).
- Không thử trên loa/HA thật (không liên quan — đây là việc web2api).

## File đổi trong patch (delta từ `8d9ba45`)

- `app/kho_tai_khoan.py` — khoá phân vùng, `tim_theo_email_va_module`, `di_tru_khoa_theo_provider`,
  `thu_dang_nhap_lai` theo provider, `ghi_ket_qua_theo_email` theo (email, module).
- `app/tuyen.py` — ba điểm ghi kết quả hàng loạt truyền module.
- `modules/grok-web/module.py` — `cach_dang_nhap_cua` + `co_mat_khau`, URL grok.com/sign-in, bước `tiep_tuc`.
- `docs/CHUAN-MODULE.md` — mục 17.
- `test/test_nv300_bo_sung.py` (mới, 24 test).
- Test cũ cập nhật: `test_nv300_cach_dang_nhap.py`, `test_web2api_nv89_grok_web.py`,
  `test_web2api_nv90_bo_sung.py`, `test_web2api_nv90_grok_cloudflare.py`,
  `test_web2api_nv_module_grok_tu_dong.py`, `test_nv271_dnt_chuoi_dang_nhap_http.py`,
  `test_nv217_do_vong_doi_tai_khoan.py`, `test_web2api_nv224_codex_loai_dung_cho.py`,
  `test_web2api_nv94_phan2.py`.
