# grok-web — đăng nhập tự động độc lập trong module (theo mẫu chatgpt2api)

Ngắn gọn, tiếng Việt. Chỉ sửa `modules/grok-web/` — không đụng module khác,
không sửa web2api core ngoài delegate mỏng đã có từ fb8aa25 (không cần sửa
thêm). Không đăng nhập thật, không dùng key MCP, không dùng token GitHub,
không push, không PR, không ghi bí mật/IP/email thật vào patch/báo cáo.
Nền: web2api nhánh `web2api-module-dang-nhap-tu-dong`, commit fb8aa25
(đã có khoi_phuc_tu_dong cho chatgpt-web và gemini-web).

## 1. chatgpt2api làm gì — và chỗ nào áp / không áp cho grok-web

Nguồn đọc (chỉ đọc, không push): TriTue2011/chatgpt2api, main d879b03
(cùng commit đã điều tra ngày 27/10).

- Thang T0–T3 trong `services/account_recovery.py`:
  - T0 kiểm phiên còn sống không (provider tự định nghĩa `trang_thai_fn`).
  - T1 nghỉ rồi kiểm lại, chưa đụng mật khẩu — phiên có lúc chập chờn rồi
    lên lại, không cần đăng nhập.
  - T2 đăng nhập lại tài khoản Google (`_freshen_google`, qua
    `captcha-solver/src/auto_login.py`): điền email/mật khẩu kiểu người,
    gặp 2FA thì chọn đường Authenticator/TOTP (pyotp) hoặc báo need_code /
    need_tap cho người xử lý.
  - T3 đăng nhập xong kiểm lại vài lượt; chỉ «ok» mới xác nhận khôi phục.
  - Khóa serial toàn cục cho lượt đăng nhập Google (đăng nhập đồng thời
    là thứ làm Google bung captcha); captcha là thử thách theo IP/trình
    duyệt, không phải theo từng tài khoản, nên sau một hồ sơ gặp captcha
    thì hoãn toàn cục 6 giờ (`_GLOGIN_CAPTCHA_HOLD_S`), đợi người gõ tay
    trên noVNC rồi mới mở lại.
  - need_captcha / need_code / need_tap → dừng cho người, không giải hộ.
  - Cookie/token sau thành công: Google login xong, cookie chứng minh là
    `__Secure-1PSID`, `__Secure-3PSID`, `SID` (đọc từ hồ sơ trình duyệt);
    các provider khác tái dùng session Google đó thay vì đăng nhập lại.
- Riêng cho Grok — CHỖ KHÔNG ÁP ĐƯỢC, phải nói rõ:
  - `captcha-solver/src/grok_web_login.py` tự ghi là «bản PHỤ THUỘC MỘT
    CÚ TÍCH TAY»: đo 20/09/2026, Cloudflare của grok.com KHÔNG tự qua
    được sau 60s, kể cả khi hồ sơ đã có sẵn. Luồng đó là: mở grok.com →
    bấm «Sign in with Google» → SSO trong hồ sơ → đợi người tích tay →
    rồi mới đọc cookie từ hồ sơ (trừ nhóm `cf_*`), và «KHÔNG ĐOÁN TÊN
    COOKIE» vì chưa từng đăng nhập được vào grok.com lần nào.
  - Vì vậy bản grok-web này KHÔNG hứa tự qua được Cloudflare grok.com,
    và KHÔNG bịa tên cookie phiên Grok mới. Nó giữ nguyên luật cũ của
    grok-web: «đã đăng nhập» = phiên dùng được (kiểm qua
    `/api/auth/session` / `lay_uid_tu_phien`), cookie `sso` là điều kiện
    module đã khai ở `_nap_tu`, thử thách truy cập cố vượt tối đa 3 lượt
    theo NV90 có sẵn rồi dừng ở can_nguoi.

## 2. Đã áp gì cho grok-web (chỉ files modules/grok-web/)

File sửa: `modules/grok-web/module.py` (+363/−14 dòng).
File test mới: `test/test_web2api_nv_module_grok_tu_dong.py` (11 test).

- `khoi_phuc_tu_dong(khoa, email, mat_khau, totp, trinh_duyet,
  nghi_t1_giay)` đầy đủ trong chính module:
  - T0: `lam_moi_phien(khoa)` — chỉ kiểm qua `/api/auth/session`
    (hoặc cookie `x-userid` có sẵn), không bịa endpoint làm mới.
  - T1: nghỉ `nghi_t1_giay` rồi kiểm lại (mặc định 0 để test không chờ).
  - T2: khóa serial RIÊNG của module, hoãn captcha RIÊNG 1800s
    (theo mẫu fb8aa25, không lấy 6 giờ của chatgpt2api), rồi đăng nhập
    lại qua `_dang_nhap_bang_trinh_duyet(..., ma_loi_rieng=True)`.
  - T3: kiểm lại bằng `lam_moi_phien`; nếu khoa ngoài module mà lam_moi
    không nhận thì lấy luôn kết quả xác minh phiên của T2, không báo
    hỏng giả. Tầng (c) vẫn là `tai_khoan_ke()` riêng, không tự đổi
    tài khoản âm thầm.
- Kênh TOTP trong module (chỉ chế độ `truc_tiep`, form x.com/login):
  `luu_totp()` kiểm khuôn Base32 (16–128 ký tự, sai khuôn → False),
  `totp_da_luu()` trả đối tượng BiMatTotp chứ không trả secret thô,
  không log secret; `_xu_ly_2fa()` điền `ma_xac_minh` rồi bấm
  `xac_nhan_2fa`, tính mã đúng lúc gọi rồi ghi đè và xoá totp ngay sau
  khi dùng. Không có TOTP → 2FA dừng ở can_nguoi.
- Controller trình duyệt thật: `dang_ky_trinh_duyet()` + 
  `_lay_trinh_duyet_module()` — ưu tiên `_tao_trinh_duyet` (test), rồi
  factory đã đăng ký; factory lỗi → None (fail-closed) → mã riêng
  `trinh_duyet_none`, không chìm thành can_nguoi.
- Mã lỗi riêng: `trinh_duyet_none`, `thu_thach_truoc_khi_dien` (thử thách
  trước khi điền, ở khoi_phuc), `het_gio` (hết thời gian mở trang),
  `captcha_hoan` (đang trong cửa sổ hoãn 1800s), `thieu_mat_khau`,
  `can_nguoi`. Đường `dang_nhap()` cũ giữ nguyên mã can_nguoi/loi_module
  (không có trình duyệt vẫn can_nguoi, captcha vẫn can_nguoi như test
  NV89 cũ) — mã riêng chỉ khi khoi_phuc gọi với `ma_loi_rieng=True`;
  ngoại lệ duy nhất có chủ ý: nếu đã có TOTP lưu thì đường cũ cũng điền
  mã 2fa thay vì dừng ở can_nguoi, vì đó chính là kênh TOTP.
- Dừng ở can_nguoi, không vượt, không OCR/giải hộ: CAPTCHA chữ, selfie,
  điện thoại, khóa tài khoản, tap, code không có TOTP → can_nguoi.
  Tín hiệu selfie/điện thoại/khóa/tap được thêm vào tập chặn
  fail-closed (`_TIN_HIEU_CAN_NGUOI_BO_SUNG`), dù bộ tín hiệu khai báo
  của grok-web chưa phân biệt riêng các tín hiệu đó.
- Token/cookie sau đăng nhập thành công: chế độ truc_tiep đọc cookie
  grok.com từ trình duyệt qua `_doc_va_kiem_phien()` có sẵn (yêu cầu
  cookie `sso`, kiểm phiên bằng `lay_uid_tu_phien`, rồi thêm jar và lưu
  mật khẩu theo khoá jar). Không bịa thêm tên cookie/token nào.

## 3. Chưa làm gì — và chưa kiểm thật cái gì

- Chế độ `google` của grok-web KHÔNG được điền mật khẩu/TOTP mới:
  nó chỉ tái dùng hồ sơ Google đã đăng nhập (`tai_dung_ho_so`, không bao
  giờ `dien()`). Hồ sơ chưa đăng nhập → can_nguoi /
  khong_lay_duoc_phien. Muốn đăng nhập Google tươi cho Grok thì cần
  một luồng riêng (điền form Google + TOTP Google, như auto_login.py
  của chatgpt2api), không nằm trong bản này — xem file câu hỏi.
- Cloudflare grok.com tự qua được hay không: CHƯA KIỂM thật. Bản này
  giữ luật NV90 cũ (cố vượt tối đa 3 lượt rồi can_nguoi) và ghi rõ
  chatgpt2api đo được là không tự qua được.
- Token/cookie lấy được: CHỈ BẰNG MOCK. Test giả lập trình duyệt
  TrinhDuyetGia + cookie `sso`/`x-userid` giả; không gọi grok.com thật,
  không gọi Google thật, không lấy được token/cookie thật nào.
- grok-web trên MCP test vẫn `dang_chay=false` (kiểm 30/10): bản này
  chưa được chủ máy áp/dựng lên server, nên chưa thể nói nó chạy thật
  trên server. NV272 (module chạy khi chưa có cookie) là điều kiện cần
  để nó có chỗ chạy, không phải bằng chứng nó đã chạy.

## 4. Test

- Test mới riêng cho grok-web:
  `test/test_web2api_nv_module_grok_tu_dong.py` — **11 passed**.
  Bao gồm: T0 phiên còn sống; T2 đăng nhập lại bằng mật khẩu đã lưu;
  T2 qua factory đăng ký riêng; trinh_duyet_none là mã riêng, không phải
  can_nguoi; thieu_mat_khau chế độ truc_tiep; 2fa có TOTP thì tự điền
  `ma_xac_minh`; 2fa không TOTP dừng ở can_nguoi, không điền mã;
  captcha trước khi điền → thu_thach_truoc_khi_dien, khoá khác bị
  captcha_hoan, dat_lai xong thì chạy lại được; luu_totp sai khuôn bị
  từ chối; chế độ google không điền ma_xac_minh khi hồ sơ chưa đăng nhập.
- Nhóm module liên quan (grok NV89/NV93/Cloudflare + chatgpt/gemini
  module + MCP delegate): **98 passed**; nhóm khôi phục/grok khác
  (NV88/NV79/NV80/NV102/NV90-api/NV94-phần2): **80 passed**. Tổng
  riêng lẻ (không tính trùng): **189 passed** (11 mới + 98 + 80).
- Patch áp sạch từ fb8aa25 trên bản copy sạch, test trên bản đó:
  **37 passed** (11 mới + 26 NV89).
- Bandit `modules/grok-web` (`-lll`): 0 medium/high, 6 low — 2 low có sẵn
  ở client.py, 4 low mới theo đúng mẫu fb8aa25 (try/except pass khi xoá
  bí mật tạm, để không ném lỗi khi dọn bí mật).
- Gitleaks/quét bí mật: patch chỉ chứa chuỗi GIẢ rõ ràng trong test
  (sso-gia-*, mat-khau-gia-*, ban-gia-*-@example.com, secret TOTP mẫu
  JBSWY3DPEHPK3PXP — đây là secret mẫu công khai trong test của
  chatgpt-web, không phải secret thật); không có IP/email/token thật.

## 5. Toàn suite — số liệu và lý do không dùng làm kết luận đỏ mới

Log: `full-suite-nv272venv.log` (venv của NV272, có pydantic_settings;
venv-test của web2api-fix thiếu gói này nên lần chạy đầu bị lỗi
collection ở `test_web2api_dang_nhap_tu_dong.py` — lỗi này tái hiện
y hệt trên nền sạch fb8aa25, không liên quan grok).

- Toàn suite (bỏ qua file collection-lỗi trên): **5363 passed,
  271 failed, 455 errors, 237 skipped, 31 xfailed**, 25 phút 58 giây.
- Con số này KHÔNG dùng để kết luận «đỏ mới», vì trong lúc chạy /tmp
  (tmpfs 512M, dùng chung với các subagent song song) đầy 100%, và
  lỗi chiếm đa số là OSError khi ghi kho/tmp. Bằng chứng:
  - Các test module chatgpt-web và gemini-web ở fb8aa25 (không hề
    đụng trong bản này) cũng đỏ đúng 6 test mỗi module trong full
    suite, với cùng lỗi «không lưu được mật khẩu: OSError».
  - Các test grok đỏ trong full suite (6 test mới + 2 NV89 + 2
    Cloudflare) có cùng nguyên nhân OSError.
  - Sau khi dọn `/tmp/pytest-of-root` (135M, của các lần chạy pytest
    đã xong), chạy lại đúng các file grok/chatgpt/gemini liên quan:
    **70 passed, 0 failed**.
  - Phân bố đỏ trong full suite cũng lệch về file không liên quan
    grok: mqtt 51, sao_luu_an_toan 45, tinh_nang 26, novnc 19, v.v.
- Kết luận đúng mức: không có đỏ mới nào được chứng minh là do bản
  grok này trong các nhóm liên quan chạy riêng lẻ (189 passed);
  toàn suite trong môi trường /tmp dùng chung này không đủ sạch để
  đối chiếu đỏ mới, cần chạy lại toàn suite khi /tmp còn trống và
  không có subagent song song khác dùng /tmp.
