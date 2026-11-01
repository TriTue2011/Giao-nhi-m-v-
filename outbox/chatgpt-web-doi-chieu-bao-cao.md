# Đối chiếu chatgpt-web với chatgpt2api — đăng nhập tự động

Ngắn gọn, chỉ module **chatgpt-web**, không làm lại từ đầu, không đụng module
khác, không sửa web2api core.

- Nền đối chiếu: web2api nhánh `web2api-module-dang-nhap-tu-dong`, commit
  **fb8aa25**, repo làm việc `~/workspace/auto-login-chatgpt/repo`
  (sao chép từ `~/workspace/web2api-fix/repo`; repo gốc kiểm lại sạch,
  `git status` trống).
- Mẫu đối chiếu: TriTue2011/chatgpt2api, main **d879b03**, chỉ clone đọc
  (không push, không sửa): `services/account_recovery.py` (thang T0–T3,
  khóa serial, hoãn captcha, ghi pool), `captcha-solver/src/auto_login.py`
  (solver đăng nhập Google, TOTP, need_captcha/need_code/need_tap),
  `captcha-solver/src/chatgpt_login.py` (đăng nhập ChatGPT, scrape JWT).
- Không đăng nhập thật, không dùng key MCP, không dùng token GitHub,
  không push, không PR, không ghi bí mật thật vào patch/báo cáo
  (chuỗi trong test mới đều là chuỗi GIẢ, ghi rõ trong file test).

## Kết luận

**chatgpt-web fb8aa25 đã khớp phần lớn khung của chatgpt2api** (thang T0–T3,
kênh TOTP trong module, controller riêng, khóa serial, dừng ở captcha).
**Còn 1 lệch rõ ràng đã sửa được trong module:** token lấy được sau đăng
nhập bằng trình duyệt trước đây chỉ nằm trong bộ nhớ, không ghi bền.
Các lệch còn lại đều cần đổi delegate lõi, thêm đường đăng nhập mới, hoặc
đổi chính sách đã duyệt — nên chỉ liệt kê, không tự sửa (xem bảng và câu hỏi).

## Bảng khớp / lệch

| Hạng mục | chatgpt2api | chatgpt-web fb8aa25 | Kết luận |
|---|---|---|---|
| Thang T0–T3 | T0 kiểm phiên, T1 kiểm lại 2 lượt cách 45 s, T2 đăng nhập lại, T3 kiểm lại; ngân sách 1200 s, poll đăng nhập Google tới 700 s | T0 `lam_moi_phien` qua `/backend-api/me`; T1 nghỉ `nghi_t1_giay` rồi kiểm lại; T2 trình duyệt + mật khẩu + TOTP; T3 kiểm lại, nếu khoa là id ngoài module thì lấy kết quả xác minh của T2 | **Khớp cấu trúc. Lệch:** T1 mặc định 0 s và delegate MCP truyền `nghi_t1_giay=0.0`, nên ở đường MCP T1 thực tế không chạy. Không sửa ở đây vì cần đổi delegate lõi. |
| Solver đăng nhập lại | ChatGPT: "Continue with Google" hoặc OpenAI native (`auth.openai.com`), scrape JWT + email sau redirect; mật khẩu + hạt giống TOTP nằm trong solver, không rời khỏi solver | Form trực tiếp `chatgpt.com/auth/login`: điền email/mật khẩu, sau 2FA thì kênh TOTP, đọc `access_token` từ cookie, kiểm qua `/backend-api/me` mới tính thành công | **Khớp khung, khác đường.** Tài khoản ChatGPT chỉ có Google, không có mật khẩu ChatGPT, sẽ không đi được đường form này. Thêm đường OAuth là việc mới, cần quyết (câu hỏi 3). |
| TOTP | TOTP trong `accounts_db` của solver; có TOTP thì tự sinh mã, không có thì `need_code`/`need_tap` và dừng | `luu_totp` chỉ nhận secret Base32 (16–128 ký tự), `totp_da_luu` trả đối tượng chứ không trả secret thô, không log secret; `_xu_ly_2fa` điền mã rồi xoá mã và totp ngay; không TOTP thì dừng ở `can_nguoi`/`thu_thach_truoc_khi_dien` | **Khớp.** **Lệch còn mở:** delegate MCP không truyền mật khẩu/TOTP, module tự lấy từ kho riêng của nó — đúng câu hỏi 2 của chủ máy (TOTP từ kho tài khoản qua lõi đưa vào lúc gọi). Chưa làm, chờ NV274/NV275, vì cần đổi delegate lõi. |
| Controller trình duyệt | Profile bền trong solver (`user-data-dir`); chỉ có cookie `__Secure-1PSID/SID` chưa đủ, vẫn phải đăng nhập lại khi máy chủ đã đăng xuất | Factory riêng `dang_ky_trinh_duyet`, `_tao_trinh_duyet` cho test; chưa đăng ký hoặc factory lỗi thì `None` -> mã riêng `trinh_duyet_none` (fail-closed); profile do dịch vụ may-dang-nhap/vnc-xa giữ, module chỉ dùng controller | **Khớp về mặt trừu tượng, đúng kiến trúc module** (profile không nằm trong module). |
| Khóa serial | `_glogin_serial` toàn cục, giữ suốt lượt poll, giãn cách tối thiểu 25 s giữa 2 phiên Google; MCP của web2api thì 1 phiên + nghỉ 3600 s | `asyncio.Lock` riêng của module, giữ trong T2; module có ghi mốc `_lan_t2` nhưng không dùng để giãn cách | **Khớp một phần.** Đường MCP đã được bù bằng nghỉ 3600 s; đường gọi trực tiếp module thì 2 lượt T2 có thể chạy sát nhau. Không tự thêm giãn cách (sẽ làm chậm test, cần quyết). |
| Hoãn captcha | Hoãn toàn cục 6 giờ (`_GLOGIN_CAPTCHA_HOLD_S`), mọi profile khác đều bị chặn, mở lại sớm khi hồ sơ đó đăng nhập xong | Hoãn riêng 1800 s (`_captcha_hoan_giay`), chỉ chặn khoá khác (`captcha_hoan`), cùng khoá được thử lại | **Khớp hướng (dừng, không vượt), khác số và phạm vi.** Không đổi sang chặn toàn cục, vì sẽ kẹt tài khoản đã giải tay xong trong cửa sổ hoãn. |
| Lấy cookie/token sau thành công | `_cgf_ghi_pool`: JWT nào lấy được cũng ghi vào pool; chỉ cập nhật dòng free đã có cùng email, **không tự thêm** tài khoản mới | Trước sửa: đọc `access_token` từ cookie, kiểm `/backend-api/me`, rồi chỉ `_them_token` vào bộ nhớ + `_luu_mat_khau`; `nap()` không dựng lại token từ bản ghi `phien` (hàm `ap_dung_ban_ghi` nói rõ không đụng token) | **Đã sửa (xem dưới).** Khác còn lại, giữ theo NV210 đã duyệt: `gan_jwt` thêm mới nếu chưa có khoá, nhưng từ chối khi nhiều khoá cùng email — ngược luật "không tự thêm" của chatgpt2api, nhưng đây là đường khôi phục tài khoản đã được phép, không phải thêm tài khoản lạ. |
| Không áp được, nói rõ | Solver tự thử qua recaptcha 1 lần (`tich_o_recaptcha` / `solve_recaptcha_v2`) rồi mới báo `need_captcha`; `_cgf_reuse` cưỡi session Google, onboard Codex; lượt `reuse_session=False` xoá profile | — | **Không mang sang.** Web2api cấm vượt/né/giải chống bot: gặp captcha/cloudflare/xác minh thì dừng ở `thu_thach_truoc_khi_dien`/`can_nguoi`, không tự giải. Codex onboard và xóa profile không thuộc chatgpt-web. |

## Sửa đã làm (duy nhất, trong `modules/chatgpt-web`)

Đường `_dang_nhap_bang_trinh_duyet` trong `modules/chatgpt-web/module.py`,
sau khi kiểm token thành công, thay vì chỉ `_them_token(token)`:

- Gọi `gan_jwt_tu_dang_nhap(email, token)` (đường NV210 đã có trong module:
  thay token cũ cùng email, hoặc thêm mới; nhiều khoá cùng email thì từ chối).
- Ghi bền hỏng hoặc hàm ném lỗi thì rơi về `_them_token(token)` — lần đăng
  nhập vừa thành công vẫn trả thành công, token vẫn dùng được trong phiên
  đang chạy. Không log token.
- Test mới `test/test_web2api_nv_module_chatgpt_doi_chieu.py` (2 test, mock
  trình duyệt và máy chủ giả, không mạng): (1) đường trình duyệt gọi
  `gan_jwt` đúng `(email, token)`; (2) `gan_jwt` hỏng hoặc ném lỗi thì đăng
  nhập vẫn thành công và token vẫn nằm trong bộ nhớ.

## Test

- Nhóm chính: `test_web2api_nv_module_chatgpt_doi_chieu.py` +
  `test_web2api_nv_module_chatgpt_tu_dong.py` +
  `test_web2api_mcp_module_delegate.py` = **13 passed, 0 failed**.
- Nhóm rộng chatgpt-web: `test_web2api_chatgpt-web.py`,
  `test_web2api_nv88_chatgpt_web.py`, `test_web2api_nv93_chatgpt_web.py`,
  `test_nv210_gan_jwt_chatgpt_web.py`, `test_nv210_chatgpt_dang_nhap.py` =
  **83 passed, 0 failed**.
- Ngoại lệ có sẵn, không do sửa này: `test_web2api_dang_nhap_tu_dong.py`
  lỗi collection `ModuleNotFoundError: test.gia` — đã kiểm trên repo gốc
  fb8aa25 cũng lỗi y hệt, nên loại khỏi 2 lượt chạy trên.

## File giao

- Báo cáo này: `~/workspace/auto-login-chatgpt/chatgpt-web-doi-chieu-bao-cao.md`
- Patch (1 file module + 1 file test mới, áp từ fb8aa25):
  `~/workspace/auto-login-chatgpt/chatgpt-web-doi-chieu.patch` (154 dòng)
- Không có nhánh push, không có PR (đúng phạm vi nhiệm vụ).

## Câu hỏi (chờ quyết, không tự làm)

1. **TOTP qua lõi lúc gọi (câu hỏi 2 của chủ máy):** có làm tiếp sau
   NV274/NV275 không? Việc này cần đổi delegate MCP để lõi đưa mật khẩu/
   TOTP từ kho tài khoản vào `khoi_phuc_tu_dong`, ngoài phạm vi module-only
   của nhiệm vụ này.
2. **T1 ở đường MCP:** delegate đang truyền `nghi_t1_giay=0.0` nên T1
   nghỉ-kiểm lại không chạy qua MCP — có muốn khôi phục T1 (ví dụ nghỉ
   rồi kiểm lại như chatgpt2api) không, chấp nhận phiên MCP kéo dài thêm?
3. **Đường OAuth cho ChatGPT:** tài khoản ChatGPT chỉ-Google (không mật
   khẩu ChatGPT) có cần thêm đường "Continue with Google" như chatgpt2api
   không, hay giữ nguyên chỉ form email/mật khẩu?
