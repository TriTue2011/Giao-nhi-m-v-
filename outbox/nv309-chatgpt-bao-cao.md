# KẾT QUẢ — NV309-chatgpt: chứng minh session chatgpt-web ở mức test

- **Đã đẩy nhánh `muse/nv309-chatgpt`** (chỉ nhánh `muse/*`, không main, không
  force-push; kiểm `ls-remote` ở cuối báo cáo). Patch:
  `outbox/nv309-chatgpt.patch` (2 file, +539/−3, 566 dòng) + báo cáo này.
- **Phạm vi đúng luật tuần tự:** chỉ CHATGPT trong lượt này — không Gemini,
  không NV309-d (vẫn chờ Q2), không chạm module khác, không chạm `web/`
  (giao diện trang tài khoản AI giữ nguyên), không tài khoản thật, không đăng
  nhập thật (toàn bộ controller GIẢ + máy chủ HTTP GIẢ + tài khoản GIẢ).
- **Nền và thứ tự gộp bắt buộc: (a) → (c) → chatgpt.** Nền web2api main
  `8ed35ab`; patch NV309-a (`muse/nv309-a` = `7b0399e5`) rồi NV309-c
  (`muse/nv309-c` = `8b020ce`) áp sạch theo thứ tự lên cây mới
  (`git apply --check` cả hai OK, không xung đột, không ép, không tự sửa
  patch của người khác). Delta chatgpt kiểm lại trên cây (a)+(c) mới:
  patch áp sạch, 25 test mới xanh.
- **Test: mới `test/test_nv309_chatgpt.py` 25/25 xanh** (venv NV289, pytest
  9.1.1). Tập liên quan có delta: **187 passed, 0 failed** (gồm mới,
  (a), (c), chatgpt-web NV88/NV93/NV-module-tu-dong/NV-module-doi-chieu,
  NV102, NV210 dang-nhap + gan-jwt, NV271-dnt can_nguoi + chuoi dang-nhap).
  Đối chiếu nền (a)+(c) không delta: **162 passed** — chênh đúng +25 test
  mới, **0 hồi quy**. Toàn suite lõi chưa chạy lại riêng cho delta này
  (thay đổi chỉ là mở rộng điều kiện dừng trong 1 module + 1 file test mới)
  — điều phối chạy toàn suite ở vòng soát/gộp nếu cần. Gap Google trong
  test = 0 nhờ `test/conftest.py` đặt `WEB2API_GOOGLE_GIAN_CACH_GIAY=0`;
  **production mặc định 25 giây không đổi** (hằng `GIAN_CACH_GIAY = 25.0`,
  test khóa).
- **Quét:** không bí mật/khóa/cookie/mật khẩu/email thật/IP thật trong
  patch/báo cáo/log (tài khoản test dùng miền `example.com` + chuỗi giả rõ
  ràng; TOTP test là mã giả cố định do stub trả, không phải secret thật).

## Bằng chứng theo từng trường hợp

### 1. Email-direct → session

Đường code: `dang_nhap(loai="mat_khau", trinh_duyet)` →
`_dang_nhap_bang_trinh_duyet(email, mat_khau, td)`: mở
`https://chatgpt.com/auth/login` → kiểm tín hiệu → điền khóa logic
`"email"` → điền khóa logic `"mat_khau"` → bấm khóa logic `"dang_nhap"` →
kiểm tín hiệu sau-điền (2FA đi kênh TOTP riêng, xem dưới) → đọc cookie
`access_token` của `chatgpt.com` → kiểm phiên qua `/backend-api/me` → ghi
bền token theo đường NV210 (`gan_jwt_tu_dang_nhap`, hỏng thì rơi về bộ nhớ,
không làm hỏng lần đăng nhập vừa thành công) + lưu mật khẩu vào kho riêng
của module → trả session.

Test khóa: thứ tự bước `mo_trang` → `dien email` → `dien mat_khau` →
`bam dang_nhap`; cookie trả về đúng token giả; tài khoản đã thêm với đúng
email; module không tự đóng controller; không gọi solver.

**Chưa xác nhận bằng tay:** ô email, ô mật khẩu, nút đăng nhập ở đường
email là **khóa logic** (`"email"`, `"mat_khau"`, `"dang_nhap"`) — controller
thật (dịch vụ may-dang-nhap) mới map các khóa này sang ô thật, nên selector
ô thật **không nằm trong module và chưa được xác nhận bằng tay**. Tương tự
ô mã 2FA (`"ma_xac_minh"`) và nút xác nhận 2FA (`"xac_nhan_2fa"`).

### 2. Email-direct không controller → fail-closed

Không truyền controller, không đăng ký factory → `_lay_trinh_duyet_module()`
trả None → `_dang_nhap_bang_trinh_duyet` trả `trinh_duyet_none` mà chưa từng
mở trình duyệt. T2 đường Google không controller → `T2 trinh_duyet_none`.
(Lưu ý mã lỗi riêng của module: đường email dùng `trinh_duyet_none`, đường
Google tái dùng hồ sơ dùng `can_nguoi` khi không có controller — cả hai đều
fail-closed, lõi xử lý như nhau.)

### 3. Challenge/CAPTCHA/Cloudflare → dừng, không solver

- Challenge đã có trước khi điền (`captcha`, `xac_minh`, `cloudflare`) →
  `thu_thach_truoc_khi_dien`, **không điền gì**, không gọi solver.
- 2FA hiện từ đầu mà không có TOTP (cũng không có TOTP đã lưu) →
  `thu_thach_truoc_khi_dien`, không điền email/mật khẩu.
- 2FA có TOTP → kênh TOTP riêng của module (`_xu_ly_2fa`): điền
  `"ma_xac_minh"` + bấm `"xac_nhan_2fa"` → đọc session → thành công.
- Không solver: kiểm tĩnh — module không gọi `.vuot_thu_thach(`, không chuỗi
  `2captcha`, không có gate `giai_captcha` nào để bật; mọi test challenge
  đều khẳng định không có hành động `vuot_thu_thach` trong nhật ký.

**Một sửa ngoài test (duy nhất) — bài học từ Claude, đỏ-trước-xanh:**
`modules/chatgpt-web/module.py`, `_dang_nhap_bang_trinh_duyet`, cả hai điểm
kiểm trước-điền và sau-điền: tập tín hiệu dừng mở rộng từ 3
(`captcha`, `xac_minh`, `cloudflare`) thành 5 (thêm `xac_minh_thiet_bi`,
`thu_thach_truy_cap`). Lý do: cả hai tín hiệu mới đều nằm trong
`_TIN_HIEU_CAN_NGUOI` của chính module (đường Google) nhưng đường email
không kiểm, nên chúng lọt qua bước điền rồi mới hỏng ở
`khong_lay_duoc_phien` — tệ hơn, qua controller giả thì **thành công giả**
(điền cả email + mật khẩu vào trang đang có thử thách rồi vẫn đọc được
cookie). Sau sửa, tập dừng đường email bằng `_TIN_HIEU_CAN_NGUOI` trừ
`"2fa"` — **2fa cố tình KHÔNG đưa vào tập dừng blanket** vì 2FA có kênh
TOTP riêng: có TOTP thì điền mã tiếp (test 2FA+TOTP khóa hành vi này), chỉ
dừng khi không có TOTP. Đưa 2fa vào tập dừng sẽ phá luồng TOTP.
Đỏ-trước-xanh: đúng 4 test mới (2 tín hiệu × trước-điền/sau-điền) FAIL
trên cây chỉ-(a)+(c) (21 test còn lại xanh), 25/25 PASS sau sửa.
Hệ quả phụ tốt: `khoi_phuc_tu_dong` đã map `thu_thach_truoc_khi_dien`
thành hoãn captcha riêng 1800 giây của module + `can_nguoi=True`, nên hai
tín hiệu mới nay cũng nuôi đúng cơ chế hoãn đó.

### 4. Google tái dùng hồ sơ đi tắt → session

`tai_dung_ho_so(ho_so, trinh_duyet, chu_giu)`: mở
`https://chatgpt.com/auth/login` → thấy `da_dang_nhap` → đọc cookie
`access_token` → kiểm qua `/backend-api/me` + làm giàu gói qua
`/backend-api/accounts/check` → thêm tài khoản của chính module → trả
session. Test khóa: không `bam`, không `dien` (không bao giờ điền mật khẩu
trên đường này); tài khoản thêm đúng `ho_so` + email + gói `plus`.
NV300: `dang_nhap` loại `mat_khau` nhưng `cach_dang_nhap="google"` thì đổi
đường sang tái dùng hồ sơ, không đòi mật khẩu, không điền.

### 5. Google SSO bấm lại khi hồ sơ chưa có phiên → session

Hồ sơ chưa có phiên → bấm nút «Log in» (`_BO_CHON_DANG_NHAP` =
`button[data-testid="login-button"], a[href*="auth/login"]`) rồi nút
«Continue with Google» (`_BO_CHON_GOOGLE` =
`button[data-provider="google"], button[aria-label*="Google" i],
[data-testid="login-form"] form > div > button:first-of-type`) → chờ phiên
hình thành (vòng chờ tối đa 20 lần, thấy `da_dang_nhap` thì dừng) → đọc
cookie → kiểm phiên → trả session. Test khóa đúng hai selector trên xuất
hiện trong nhật ký bấm, và không có `dien` nào.

**Chưa xác nhận bằng tay:** selector nút «Continue with Google» — code ghi
đã đo trên trang thật 18/10/2026 nhưng nhánh dự phòng là vị trí cấu trúc
(nút đầu tiên trong form login), chưa có chủ máy chọn bằng tay qua noVNC ở
vòng này. Nút «Log in» cũng chưa chọn bằng tay. **Các bước popup OAuth /
chọn tài khoản Google / đồng ý trong SSO thật KHÔNG có trong bộ điều khiển
trừu tượng** — luồng thật có thể cần thêm bước chỉ kiểm thật mới thấy
(cùng giới hạn đã ghi ở Claude và Grok).

### 6. Khóa serial/gap/hold Google của (c) trên đường chatgpt-web

- Đang giữ captcha cho chủ khác → lượt này bị chặn bằng mã
  `cho_captcha_toan_cuc`, **nhật ký trình duyệt rỗng** (không chạm trình
  duyệt).
- Chủ hold chạy lại (đi tắt thành công) → gỡ hold toàn cục (`dang_giu()`
  False sau lượt).
- Đường Google gặp `captcha` hoặc `cloudflare` → `can_nguoi` + đặt hold
  toàn cục cho đúng chủ (email của lượt này); `cloudflare` đặt hold vì nó
  nằm trong `TIN_HIEU_CAPTCHA` của (c) — 2FA không đặt hold (theo đúng
  thiết kế (c): hold chỉ cho thử thách theo IP).
- Gap: lượt Google thứ hai chờ nốt giãn cách (đo bằng env 0.5 giây thay cho
  25 giây production); production mặc định 25 giây không đổi.
- T2 đường Google qua `khoi_phuc_tu_dong` (`cach_dang_nhap="google"` +
  controller lõi cấp + `chu_giu=email`) → thành công ở T2, hold đã gỡ.

### 7. Vòng đời controller theo (a)

- Module không bao giờ tự đóng controller: khẳng định nhật ký không có
  `dong` sau cả ba đường (email thành công, email `can_nguoi`, Google
  thành công). Đóng là việc của người gọi (lõi).
- Cầu nối lõi (mẫu NV309-a, module trình duyệt giả): hồ sơ sẵn có → tái
  dùng (`da_tao=False`, không tạo mới); không hồ sơ → tạo workspace mới
  (`da_tao=True`); `dong_workspace_moi` chỉ đóng workspace mới tạo với
  `(ho_so_moi, False)`; hồ sơ sẵn có không bao giờ bị đóng. (Người gọi tự
  quyết khi nào gọi `dong_workspace_moi` — không gọi khi `can_nguoi`.)

### 8. Không phá đường chatgpt-web đã có

- T2 email qua `khoi_phuc_tu_dong` (mật khẩu đã lưu qua controller lõi cấp)
  → thành công ở T2; T2 email + TOTP (sau mật khẩu hiện 2FA) → thành công.
- Tập liên quan 187 passed, 0 failed — nền (a)+(c) 162 passed, chênh đúng
  +25 test mới, 0 hồi quy.

## Vẫn cần kiểm thật sau gộp (MCP trước → noVNC thao tác tay)

Controller giả chỉ chứng minh đường ống + quyết định của module, KHÔNG
chứng minh selector thật đúng. Các ô **chưa xác nhận bằng tay**: ô email,
ô mật khẩu, nút đăng nhập đường email (khóa logic, map ở controller thật);
nút «Log in» và nút «Continue with Google» (selector đo 18/10/2026, chưa
chọn bằng tay ở vòng này); ô mã 2FA; các bước popup OAuth / chọn tài khoản
Google / đồng ý trong SSO thật (bộ điều khiển trừu tượng không có bước
popup/chọn tài khoản); ô «Xác minh bạn là con người» (Cloudflare).

Kế hoạch kiểm thật: đường Google tái dùng hồ sơ bằng tài khoản Google đã
cho phép — theo kế hoạch trio Claude → Grok → Gemini, cần tài khoản
ChatGPT trong kho ở chế độ «dùng hồ sơ Google đã đăng nhập» + id vào danh
sách cho phép MCP + dựng lại trước (tài khoản ChatGPT đã cho phép hiện có
đã thành công ở NV275, nhưng đó là trên code trước NV309; kiểm lại sau
gộp mới chứng minh được đường mới). Sau đó chủ máy thao tác tay qua noVNC
chọn đúng từng ô.
