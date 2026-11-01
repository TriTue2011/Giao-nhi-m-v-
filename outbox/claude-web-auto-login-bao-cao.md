# claude-web: đăng nhập tự động độc lập trong module

- Nền: web2api nhánh `web2api-module-dang-nhap-tu-dong`, commit `fb8aa25`
  (repo làm việc: `~/workspace/auto-login-claude/repo`).
- Phạm vi: **chỉ `modules/claude-web/module.py`** (mã chạy) và **1 file test mới**
  `test/test_web2api_nv_module_claude_tu_dong.py`. Không sửa core, không sửa
  module khác, không push, không PR, không đăng nhập thật, không dùng key MCP,
  không dùng token GitHub, không bí mật/IP/email thật trong patch/báo cáo.
- Patch: `claude-web-auto-login.patch` (560 dòng), áp sạch từ `fb8aa25`
  (đã kiểm bằng `git apply --check` trên clone sạch + chạy lại test mới).

## 1. chatgpt2api làm gì cho Claude/Google (đọc trực tiếp, không copy solver)

Nguồn đọc: `TriTue2011/chatgpt2api` HEAD `d879b03`,
`services/account_recovery.py` và `captcha-solver/src/claude_web_login.py`,
`captcha-solver/src/auto_login.py`.

- Thang dùng chung `_dang_nhap_lai_theo_thang`, áp cho Claude qua
  `claude_recover_and_notify`: **T0** kiểm phiên → **T1** nghỉ rồi kiểm lại
  (45s, tối đa 2 lượt, chưa đụng mật khẩu) → **T2** đăng nhập lại tài khoản
  Google bằng mật khẩu + TOTP đã lưu trong solver (`_freshen_google`,
  `auto-login-saved`) → **T3** kiểm lại phiên, chỉ `ok` mới tính thành công.
- Kiểm phiên Claude **không cần trình duyệt**: `_claude_verify` gọi thẳng
  `GET https://claude.ai/api/organizations` bằng cookie `sessionKey`;
  200 có org → `ok`, 401/403 → `mat`, 409/429 → `ban`, còn lại → `chua_ro`.
- Đăng nhập lại Claude: mở `claude.ai` → nếu đã có `sessionKey` thì xong;
  nếu không thì `/login` → bấm «Continue with Google» → **popup OAuth**,
  chọn tài khoản Google, đồng ý → **scrape cookie `sessionKey`** → kiểm
  bằng `/api/organizations`. Vậy “token/cookie” ở đây là **cookie
  `sessionKey`**, không phải access token OAuth.
- Khóa và hoãn: **khóa serial toàn cục** `_glogin_serial` (một phiên
  đăng nhập Google trên toàn hệ thống tại một thời điểm, giãn cách tối thiểu
  25s, cooldown đăng nhập lại 1800s/tài khoản); gặp CAPTCHA thì giữ
  **6 giờ** (`blocked_captcha_window`); trạng thái `need_captcha` /
  `need_code` / `need_tap` → **cần người** trên noVNC, solver chỉ gắn cờ
  rồi đợi người gõ, không tự vượt.
- Điểm **KHÔNG áp sang web2api** (nói rõ, không bịa):
  1. Solver Turnstile/Cloudflare của chatgpt2api (`pass_challenge`) — web2api
     gặp Cloudflare/CAPTCHA thì dừng ở `can_nguoi` /
     `thu_thach_truoc_khi_dien`, không vượt, không giải hộ, không OCR.
  2. Popup OAuth / chọn tài khoản Google / đồng ý của chatgpt2api — giao
     diện điều khiển trình duyệt trừu tượng của web2api
     (`mo_trang`/`tin_hieu`/`dien`/`bam`/`doc_cookie`) không có bước đó.
  3. Khóa serial toàn cục và giữ captcha 6 giờ — kiến trúc web2api yêu cầu
     mỗi module độc lập, nên bản này chỉ có khóa serial riêng của
     claude-web và hoãn captcha 1800s (theo đúng mẫu chatgpt-web/gemini-web
     đã làm ở `fb8aa25`).

## 2. Đã áp gì cho claude-web

Thêm `khoi_phuc_tu_dong(khoa, email, mat_khau, totp, trinh_duyet,
nghi_t1_giay)` **trong chính `modules/claude-web/module.py`**, cùng các hàm
riêng: `dang_ky_trinh_duyet`, `_lay_trinh_duyet_module`,
`luu_totp`/`totp_da_luu`, `_xu_ly_2fa`, `_lay_khoa_tu_dong`,
`dat_lai_trang_thai_tu_dong`. Core chỉ chuyển tiếp mỏng đã có
(`app/cong_mcp_cong_cu.py:_thu_khoi_phuc_module` gọi
`module.khoi_phuc_tu_dong(tk_id, email)` nếu module có) — **không sửa core**.

- **T0**: `lam_moi_phien(khoa)` — kiểm bằng `GET /api/organizations`
  (giống `_claude_verify`), không bịa endpoint làm mới (claude.ai không có
  endpoint làm mới session công khai).
- **T1**: nghỉ `nghi_t1_giay` rồi kiểm lại (mặc định 0 để test không chờ).
- **T2**: khóa serial riêng của module + hoãn captcha riêng 1800s +
  đăng nhập lại bằng mật khẩu và TOTP đã lưu qua trình duyệt.
  `_dang_nhap_bang_trinh_duyet` được mở rộng thêm tham số
  `totp`/`khoi_phuc=True`; đường cũ (`khoi_phuc=False`) giữ nguyên mã cũ
  để test NV89 không đổi. Sau mật khẩu, nếu hiện 2FA thì đi kênh TOTP của
  module: có TOTP thì điền mã, **dùng xong xóa mã và TOTP ngay**; không có
  TOTP thì dừng. Secret TOTP chỉ lưu khi chủ máy gọi tường minh `luu_totp`,
  phải đúng khuôn Base32 (16–128 ký tự), không bao giờ log secret, không
  trả secret thô (chỉ trả đối tượng `BiMatTotp` tính mã lúc gọi).
- **T3**: kiểm lại bằng `lam_moi_phien`; nếu khoa là id ngoài module
  (vd: id kho MCP, khoá NV93 `tk-…` mà `lam_moi_phien` không nhận) thì lấy
  luôn kết quả xác minh phiên của T2 (module đã kiểm `sessionKey` qua
  `/api/organizations` trong lúc đăng nhập), không báo hỏng giả.
- **Tầng (c)** vẫn là `tai_khoan_ke()` riêng; `khoi_phuc_tu_dong` không tự
  đổi tài khoản âm thầm.
- **Mã lỗi riêng**: `trinh_duyet_none` (chưa nối controller, khác
  `can_nguoi`), `thu_thach_truoc_khi_dien` (CAPTCHA/xác minh/Cloudflare
  trước khi điền), `het_gio` (hết thời gian mở trang), `captcha_hoan`
  (đang trong cửa sổ hoãn captcha), `thieu_mat_khau`, `can_nguoi`
  (CAPTCHA/selfie/điện thoại/khóa tài khoản/tap/code không có TOTP đã lưu).
  Mọi trường hợp đó đều **dừng, không vượt, không OCR/giải hộ**.
- **Cookie/token lấy được bằng cách nào trong mã**: sau đăng nhập, đọc
  cookie `sessionKey` từ trình duyệt (`doc_cookie("claude.ai")`), chuẩn hoá
  thành `sessionKey=…`, kiểm bằng `GET /api/organizations`, rồi mới thêm
  tài khoản và lưu mật khẩu cho lần sau. Đây là cùng một loại “phiên” mà
  chatgpt2api scrape, nhưng **chỉ là đường mã, chưa kiểm thật** (xem §3).

## 3. Chưa làm / chưa kiểm thật — nói thẳng

- **Chưa đăng nhập thật, chưa lấy được token/cookie thật.** Mọi kết quả
  dưới đây đều bằng **trình duyệt giả + máy chủ claude.ai giả (mock)**.
- **SSO Google thật là chỗ chưa khớp lớn nhất.** Đường T2 hiện tại vẫn là
  khuôn điền email + mật khẩu cũ của claude-web (dành cho tài khoản Google
  đã liên kết đi qua SSO), nhưng chi tiết SSO Google thật (popup OAuth,
  chọn tài khoản, đồng ý) **chưa kiểm** và không có trong giao diện trình
  duyệt trừu tượng của web2api. Nếu claude.ai thật hiện popup Google thay
  vì form mật khẩu thì T2 sẽ lỗi `loi_module`, không tự biến thành SSO được.
  Đường Google đã kiểm theo mock trong repo là `tai_dung_ho_so` (NV93:
  hồ sơ đã đăng nhập Google sẵn, bấm «Continue with Google», không nhập
  lại mật khẩu/2FA) — nhưng đó là tái dùng hồ sơ, không phải đăng nhập
  lại bằng mật khẩu + TOTP.
- **TOTP qua lõi chưa làm.** Delegate MCP hiện tại chỉ gọi
  `khoi_phuc_tu_dong(tk_id, email)` mà không truyền mật khẩu/TOTP, nên
  đường MCP chỉ dùng được TOTP khi nó đã được lưu trước vào **kho riêng
  của module** qua `luu_totp`. Đáp án chủ máy trước đây (cho chatgpt-web/
  gemini-web) là TOTP lấy từ kho tài khoản qua lõi đưa vào module lúc gọi —
  việc đó **chưa làm**, chờ quyết ở file câu hỏi.
- **claude-web đang `dang_chay=false` trên cổng MCP test** (kiểm 30/10):
  bản này không tự làm nó chạy lên được; cần chủ máy áp nhánh + cho phép
  tài khoản `id@claude-web` thì mới kiểm thật được.
- Hoãn captcha 1800s theo mẫu module cũ, **không phải 6 giờ toàn cục** như
  chatgpt2api; khóa serial chỉ trong module, không phải toàn hệ thống.

## 4. Test (mock, không Internet, không Chrome)

- Test mới: `test/test_web2api_nv_module_claude_tu_dong.py` — **12 passed**,
  gồm: độc lập không import module khác, T0 phiên còn sống, T1 nghỉ-kiểm
  lại lên, T2 bằng mật khẩu đã lưu, T2 qua factory riêng của module,
  `trinh_duyet_none` khác `can_nguoi`, `thieu_mat_khau`, 2FA có TOTP tự
  điền mã, 2FA không TOTP dừng ở thử thách, captcha hoãn + đặt lại,
  `luu_totp` sai khuôn bị từ chối, đường cũ vẫn trả `can_nguoi` khi
  không có trình duyệt.
- Nhóm liên quan (claude-web, NV89, NV93, chatgpt/gemini tự động, MCP
  delegate, NV102 grok/claude, NV80): **115 passed, 0 failed** với bản này.
- Nền sạch `fb8aa25` (không có bản này, cùng 8 file cũ): **103 passed**.
  Vậy **12 test mới đều xanh, không có đỏ mới** (115 = 103 + 12).
- Ngoại lệ tái hiện trên nền sạch, không liên quan bản này:
  `test/test_web2api_dang_nhap_tu_dong.py` lỗi collection
  `ModuleNotFoundError: No module named 'test.gia'` (đã biết từ NV272).
- Bandit trên `modules/claude-web`: severity Medium/High = **0**; 5 Low
  dạng B110 `try/except/pass` ở khối dọn bí mật (1 có sẵn ở `client.py`,
  4 mới ở khối `finally` xóa mật khẩu/TOTP — cùng pattern với module
  chatgpt-web), không phải lỗi bảo mật mới.
- Patch áp sạch từ `fb8aa25` trên clone sạch (`git apply --check` OK,
  chạy lại test mới 12 passed sau khi áp).
