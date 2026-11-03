# KẾT QUẢ — NV309-c: khóa serial toàn cục cho đường Google + giữ captcha toàn cục (SAI S3)

> Base: web2api main 8ed35ab (đã chứa sửa của điều phối: Grok email mặc định
> đường thẳng, sổ lỗi theo khóa, vòng đời dịch vụ, trần RAM lõi).
> Nhánh nộp: muse/nv309-c — CHỈ nhánh muse/*, không đẩy main, không force-push.
> Bảng đối chiếu: outbox/nv309-doi-chieu.md trên nhánh muse/nv309-doi-chieu
> (134ae25f). Nhiệm vụ gốc: inbox/NV309.md trên Giao main.
> Thứ tự gộp: (a) → (b) → (c). Patch (c) dựa trên cùng base 8ed35ab, KHÔNG
> xếp chồng lên (a); khi gộp theo thứ tự này vẫn cần điều phối kiểm tra áp
> patch, vì (c) chạm cùng 4 module nhưng KHÔNG chạm dòng nào của (a) (xem §3).
> Trạng thái kiểm thật: CHƯA THỬ TRÊN TRÌNH DUYỆT THẬT (xem «Kế hoạch kiểm thật»).

## 1. Vấn đề — hỏng nội tại, không phải «khác c2a nên sai»

Theo đính chính 16:58 ngày 03/11: khác c2a không tự động là sai; mỗi điểm phải
được test chứng minh. S3 qua được tiêu chuẩn đó — nó hỏng ở mức hệ thống,
chứng minh bằng cấu trúc code + test đỏ, không phải bằng so sánh với c2a:

- Đường Google của w2a hiện chỉ có khóa riêng từng module + hoãn captcha
  riêng từng module 1800 giây → hai module có thể đăng nhập Google song song
  (ví dụ Grok + ChatGPT cùng lúc), dồn RAM và mời Google bung captcha chùm
  cho cả IP — đúng điều c2a tránh bằng `_glogin_serial` + giữ captcha toàn cục.
- Đã phân tích kỹ code c2a trước khi làm (luật 16:11): nguồn là
  `inbox/tai-lieu/c2a-dang-nhap/services/account_recovery.py` (bản copy trong
  Giao, đối chiếu với commit c2a `d879b03`):
  - `_glogin_serial` (threading.Lock) giữ SUỐT lượt kể cả poll (~700 giây);
    `_GLOGIN_GAP_S = 25.0` giãn cách từ mốc kết thúc lượt trước;
    `_GLOGIN_CAPTCHA_HOLD_S = 6 * 3600.0`.
  - `_freshen_google(profile)`: dưới lock, đọc lại trạng thái của CHỦ hold
    (không mở Chrome); chủ đã đăng nhập xong → gỡ hold, coi như xong; còn
    hold → trả `blocked_captcha_window`, không chạy; gặp `need_captcha`
    (lúc gọi hoặc lúc poll) → đặt hold 6 giờ + chủ; thành công → gỡ hold.
  - Lý do ghi trong code c2a: nhiều recover song song từ một IP → Google
    bung captcha chùm; bấm tay từng-lần-một thì không.
- UI tài khoản AI KHÔNG ĐỔI (đang đúng, giữ nguyên theo đính chính).
- Không đổi ngữ nghĩa challenge → `can_nguoi` (Q4, chờ chủ máy). Không port
  solver captcha (2captcha, Turnstile, reCAPTCHA âm thanh); gate `giai_captcha`
  mặc định tắt. Các điểm w2a hơn c2a (NV209, NV231, NV271, proxy mọi nhánh,
  /v1/man-hinh, bảo mật dịch vụ) không bị sửa lùi.

## 2. Thiết kế — MỘT chỗ ở lõi, không phải khóa riêng từng module

- Module lõi mới `app/khoa_dang_nhap_google.py`: singleton asyncio trong
  tiến trình lõi (không threading, vì module chạy asyncio):
  - `GIAN_CACH_GIAY = 25.0`, `GIU_CAPTCHA_GIAY = 6 * 3600.0`,
    `MA_LOI_GIU = "cho_captcha_toan_cuc"` (khớp khuôn `[a-z0-9_]{1,64}`; khác
    `can_nguoi` — người đã xử lý captcha đầu rồi, các lượt khác chỉ chờ).
  - `TIN_HIEU_CAPTCHA = {"captcha", "cloudflare", "thu_thach_truy_cap"}`.
  - `phien_dang_nhap_google(chu)` (async context manager): giữ serial suốt
    lượt; trong lock, nếu đang giữ và `chu` không phải chủ → raise
    `BiGiuCaptchaToanCuc` (module dịch thành `MA_LOI_GIU`, không lái trình
    duyệt); chủ hold được chạy lại (đường hồi phục: người đã tích tay xong →
    lượt này thấy `da_dang_nhap` → thành công → gỡ hold); nếu được chạy →
    ngủ nốt gap từ mốc kết thúc lượt trước rồi yield; `finally` chỉ đóng mốc
    khi lượt thực sự chạy (lượt bị chặn không đẩy mốc), luôn nhả lock.
  - `dat_giu_captcha(chu)`: chỉ khi `chu` khác rỗng; lượt không danh tính gặp
    captcha vẫn trả `can_nguoi` như cũ nhưng không đặt hold toàn cục (không có
    chủ để gỡ).
  - `bo_giu_neu_chu(chu)`: thành công của đúng chủ → gỡ hold.
    `dang_giu()`, `thong_tin_giu()` chỉ dùng nội bộ/log kỹ thuật — KHÔNG đưa
    email chủ hold vào thông điệp người dùng. `dat_lai()` reset singleton
    cho test.
  - Gap đọc từ env `WEB2API_GOOGLE_GIAN_CACH_GIAY` lúc gọi (mặc định 25 giây;
    env sai → mặc định). Conftest đặt gap = 0 trong test (xem §4).
- Điểm chặn: `tai_dung_ho_so` của cả 4 module (đường Google SSO duy nhất:
  nhánh google của `dang_nhap`, `dang_nhap_lai` google, T2 google). Đổi thành
  wrapper `tai_dung_ho_so(ho_so, trinh_duyet, chu_giu="")` → CM + gọi
  `_tai_dung_ho_so_chay` (thân cũ). Chủ hold: `chu_giu` (email, nếu điểm gọi
  truyền) nếu không thì id hồ sơ đã chuẩn hóa; cả hai rỗng → chỉ serial,
  không đặt hold.
- Đặt hold (KHÔNG đổi mã trả — Q4 giữ nguyên): trong `_tai_dung_ho_so_chay`,
  khi gặp tín hiệu captcha-subset hoặc `_co_thu_thach()` True (cả probe đầu,
  vòng bấm, và probe cuối với jar — grok-web có 4 điểm, các module khác 2–3
  điểm theo đúng hình dạng thân riêng của chúng) → `dat_giu_captcha(chu)`
  rồi trả `can_nguoi` như cũ. 2FA/xác minh thuần → KHÔNG đặt hold (theo tài
  khoản, không phải theo IP). Thành công → `bo_giu_neu_chu(chu)`.
- Giữ nguyên: hoãn captcha riêng từng module 1800 giây (ví dụ grok-web
  `_captcha_hoan_giay = 1800.0`, T2 đặt `_captcha_den_het` khi mã thuộc
  `("captcha", "thu_thach_truoc_khi_dien")`); tiers module không đổi.

## 3. Thay đổi (file đầy đủ — xem patch kèm theo)

- `app/khoa_dang_nhap_google.py` (mới, 144 dòng).
- `modules/{grok,chatgpt,gemini,claude}-web/module.py`: import
  `khoa_dang_nhap_google`; wrapper + `_tai_dung_ho_so_chay`; hook
  captcha/thành công theo đúng thân riêng của từng module; nối
  `chu_giu=email` tại T2 (`dang_nhap_tu_dong`) của cả 4 module.
- `test/conftest.py`: `WEB2API_GOOGLE_GIAN_CACH_GIAY = 0` trong test.
- `test/test_nv309_c.py` (mới, 6 test).
- TRÁNH XUNG ĐỘT VỚI (a) — đã kiểm bằng diff: (c) KHÔNG sửa các dòng
  `dang_nhap` mà (a) đã sửa (các nhánh google của `dang_nhap` ở chatgpt-web
  1039, gemini-web 646, claude-web 431 giữ nguyên — wrapper tự dùng id hồ sơ
  làm chủ hold khi điểm gọi không truyền email). Chỉ T2 và thân
  `tai_dung_ho_so` được chạm. Khi gộp (a) → (c), nếu xung đột ngữ cảnh thì
  điều phối báo, không tự ý sửa patch của mảnh khác.

## 4. Test — đỏ-trước-xanh, khẳng định hành vi đúng (không chỉ «giống c2a»)

- Mới `test/test_nv309_c.py`, 6 test, đỏ-trước-xanh (đỏ trước: lỗi thu thập
  do module lõi chưa tồn tại), xanh 6/6:
  1. Hai lượt Google song song không chạy chồng (thứ tự vào–ra–vào–ra).
  2. Gap giữa hai lượt (monkeypatch env 0.2 giây, ngưỡng 0.19 chống flake).
  3. Captcha ở module A chặn module B bằng `cho_captcha_toan_cuc` mà KHÔNG
     gọi `mo_trang` (không lái trình duyệt khi bị giữ).
  4. Chủ hold chạy lại thành công → gỡ hold → lượt khác chạy được.
  5. 2FA thuần không đặt hold (lượt khác vẫn chạy).
  6. Lượt không danh tính (không `chu_giu`, không id hồ sơ) gặp captcha →
     `can_nguoi` nhưng không đặt hold.
- Liên quan hiện có: 95 test xanh — `test_web2api_nv93_chatgpt_web.py`,
  `test_web2api_nv89_{grok,gemini,claude}_web.py`,
  `test_web2api_nv88_chatgpt_web.py` — trong 6.36 giây.
- BÀI HỌC GAP ĐÃ ĐO THẬT (ghi rõ để điều phối biết): lần chạy liên quan đầu
  tiên chưa có env override: 95 xanh nhưng mất 409.71 giây — vì mỗi lượt
  `tai_dung_ho_so` trong cùng tiến trình test phải ngủ gần đủ 25 giây.
  Đối chứng: file NV93 chatgpt trên base sạch 8ed35ab chạy 2.18 giây, trên
  cây (c) chưa fix chạy >2 phút. Vì vậy gap đọc từ env lúc gọi + conftest
  đặt 0 trong test; production mặc định vẫn 25 giây. Đây là thay đổi theo
  bằng chứng đo, không phải đoán.
- Patch đã kiểm áp sạch trên cây mới ở 8ed35ab (`git apply --check` đạt, áp
  xong chạy lại `test_nv309_c.py` 6 xanh).
- Toàn suite lõi không chạy lại cho (c) (vùng đổi: lõi khóa mới + 4 module
  `tai_dung_ho_so` + conftest gap=0; các file liên quan trực tiếp đã chạy ở
  trên). Điều phối chạy toàn suite ở vòng soát/gộp nếu cần.

## 5. Chứng minh theo từng loại (luật 17:52 — tuần tự, Grok trước)

- **Grok — xong ở mức test, đường Google đầu tiên:** wrapper + 4 điểm hook
  (kiểm đầu, probe đầu, vòng bấm, probe cuối với jar) + T2 nối email; test
  (c) dùng chính grok-web (fake trang + stub `_co_thu_thach`) để chứng minh
  serial/gap/hold. Kiểm thật MCP → noVNC thao tác tay chờ vòng sau gộp.
- **ChatGPT, Gemini, Claude — chưa tới lượt:** chỉ mới nối cùng mẫu wrapper +
  hook theo thân riêng của từng module (2 điểm chatgpt/gemini, 3 điểm claude)
  + T2 nối email; chưa có test chứng minh session riêng cho từng module
  (test (c) chứng minh khóa/hold qua grok-web; khóa lõi là đường ống chung).
- **Đường email trực tiếp không thuộc (c):** (c) chỉ chặn đường Google SSO
  (`tai_dung_ho_so`); đường mật khẩu/email-direct không qua khóa này.
- Thứ tự trong mỗi loại: xong hẳn đường Google (khóa + hold) mới sang cách
  tiếp theo; (d) vẫn chờ Q2, không làm ở đây.

## 6. Ranh giới tiến trình — phải đọc trước khi gộp

- Khóa + hold sống trong TIẾN TRÌNH LÕI → serialize các lượt Google của
  module (đúng S3: «hai module song song»).
- Tiến trình DỊCH VỤ (`do_google_login_steps` trong `auto_login.py`, gọi từ
  `chatgpt_login.py`, `claude_web_login.py`, `gemini_web_login.py`) là tiến
  trình khác, KHÔNG bị khóa này serialize (vẫn bị trần 2 ngữ cảnh của pool).
  Serialize xuyên tiến trình cần cơ chế khóa chia sẻ — là follow-up, KHÔNG
  tự đoán thiết kế ở đây.

## 7. Khác c2a có chủ đích (ghi rõ, không giấu)

1. Owner = email (không phải profile) để khớp đường đã lưu ↔ T2.
2. Lượt không danh tính chỉ serial, không đặt hold.
3. Gap chỉ tính khi lượt thực sự chạy (lượt bị chặn không đẩy mốc).
4. Gap đọc từ env lúc gọi (c2a gõ cứng 25 giây) — để test không ngủ 25 giây
   mỗi lượt; production mặc định không đổi.

## 8. Kế hoạch kiểm thật — ĐẦU TIÊN qua MCP, rồi noVNC THAO TÁC TAY

(Chưa kiểm thật — máy này không tự chạy lượt đăng nhập thật qua MCP nếu chưa
có tài khoản cho phép + bản dựng mới. Các bước dưới thuộc vòng lặp với điều
phối/chủ máy sau khi gộp + dựng lại.)

1. MCP: gọi khôi phục Google cho tài khoản Grok đã lưu (đường đã lưu, hồ sơ
   Google thật) → kỳ vọng thành công, cookie/session thu được.
2. MCP song song: gọi khôi phục Google cho 2 module cùng lúc (Grok + ChatGPT)
   → kỳ vọng lượt thứ hai chờ serial (không chạy chồng, không captcha chùm);
   đo thời gian chờ ≈ gap 25 giây.
3. noVNC thao tác tay: chủ máy tự bấm ô đăng nhập Google (ô email, nút Tiếp
   tục, ô mật khẩu, nút «Sign in with Google») để xác nhận selector thật;
   nếu Google bung captcha ở lượt đầu, tích tay xong → lượt khôi phục tiếp
   theo của cùng chủ phải thành công và gỡ hold (các lượt khác không còn bị
   `cho_captcha_toan_cuc`).
4. Kiểm hold: sau khi 1 tài khoản gặp captcha, tài khoản Google khác gọi ngay
   → kỳ vọng `cho_captcha_toan_cuc` (không mở trình duyệt); sau 6 giờ hoặc
   sau khi chủ hold thành công → chạy lại bình thường.

## 9. Ô đăng nhập CHƯA được xác nhận bằng thao tác tay qua noVNC

(Phương pháp 17:38 — test controller giả chỉ chứng minh đường ống, không
chứng minh selector thật đúng. Tất cả các ô dưới đây đều CHƯA xác nhận bằng
tay, thuộc vòng kiểm thật sau gộp.)

- Grok đường Google: nút «Sign in with Google» trên trang đăng nhập Grok;
  ô chọn tài khoản Google trong hồ sơ.
- Grok đường trực tiếp: ô email + nút Tiếp tục ở bước email (NV300 ghi «bộ
  điều khiển trình duyệt thật phải map khóa logic `tiep_tuc` sang nút Tiếp
  tục» — chưa xác nhận bằng tay); ô mật khẩu; ô mã xác minh (nếu có).
- ChatGPT đường Google: nút «Log in» + «Continue with Google».
- Gemini đường Google: nút Đăng nhập + chọn tài khoản Google (SSO).
- Claude đường Google: nút «Continue with Google» (popup) + chọn tài khoản.
- Ô «Xác minh bạn là con người» (Cloudflare) trên grok.com — liên quan mảnh (b):
  cửa sổ `need_manual` phải còn mở khi chủ máy vào noVNC (nhờ (b) giữ 10 phút).

## 10. Câu hỏi của chủ máy (ghi lại, KHÔNG đoán đáp án)

- Q1: lịch nền giữ BẬT mặc định 1800 giây hay học c2a TẮT mặc định + 3 giờ?
- Q2: thứ tự ưu tiên tài khoản có cấu hình được không? → mảnh (d) ĐANG CHỜ
  Q2, không tự đoán thiết kế, không làm trong lượt này.
- Q3: sau lượt MCP thành công có đóng thật workspace không (hiện chỉ đóng
  controller, giữ workspace để tái dùng)?
- Q4: gặp challenge thì giữ «challenge → can_nguoi» hay học c2a «cf_chan ≠
  het, vẫn dùng cookie cũ»? Mảnh (c) giữ nguyên ngữ nghĩa hiện tại.
