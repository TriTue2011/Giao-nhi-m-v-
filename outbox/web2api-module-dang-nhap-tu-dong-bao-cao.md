# Báo cáo: đăng nhập tự động gắn vào MODULE (thay thế bản lõi trước)

Ngày: 2026-10-27. Nền web2api: `ffb7f3e`. Nhánh làm việc web2api:
`web2api-module-dang-nhap-tu-dong`, commit `fb8aa25` (trên `7457fbd`).
Patch đính kèm: `web2api-module-dang-nhap-tu-dong.patch` — là
`git format-patch ffb7f3e..HEAD`, áp sạch bằng `git am --3way` trên clone
sạch từ `ffb7f3e` (đã kiểm chứng, xem mục Kiểm chứng patch).
**Chưa push, chưa tạo PR. Nhánh outbox mới cũng chỉ ở cục bộ.**

## 1. Bản này thay thế bản trước ở chỗ nào — đọc trước

- Bản trước đã push lên GitHub ở nhánh `muse/web2api-dang-nhap-tu-dong`,
  commit `86a32e6`: logic khôi phục nằm ở lõi web2api
  (`app/cong_mcp_cong_cu.py`, `app/khoi_phuc_phien.py`, `app/tu_lam_moi.py`).
  Theo đính chính của người dùng, chỗ đó là sai: web2api chỉ là phiên
  dịch viên (thin pass-through), logic phải gắn vào module.
- Bản này **gỡ logic lõi của bản trước ra và chuyển logic vào module**:
  - `app/cong_mcp_cong_cu.py`: phần nối MCP qua thang lõi của bản trước
    đã gỡ. Chỉ còn một hàm chuyển tiếp mỏng `_thu_khoi_phuc_module`
    (xem mục 4) — gọi `module.khoi_phuc_tu_dong()` rồi dịch kết quả.
  - `app/khoi_phuc_phien.py`: mọi phần thêm của bản trước đã gỡ, file về
    đúng nền `ffb7f3e`. Lưu ý thành thật: file này vốn đã có sẵn thang
    khôi phục nội bộ từ trước bản sửa (cho các caller nội bộ khác, không
    phải do bản này thêm). Luồng MCP từ bản này trở đi **không đi qua nó
    nữa** — MCP gọi thẳng module. Nếu người dùng muốn gỡ hẳn thang đó
    khỏi mọi luồng nội bộ còn lại thì đó là việc riêng, xem file hỏi thêm
    câu 1; bản này không tự gỡ vì sẽ vỡ các caller/test nội bộ hiện có.
  - `app/tu_lam_moi.py`: registry controller thật của bản trước đã gỡ,
    file về đúng nền `ffb7f3e`. Controller giờ đăng ký riêng từng module
    (xem mục 3).
  - `test/test_web2api_mcp_khoi_phuc_tang.py` (test lõi của bản trước):
    đã xoá, thay bằng test riêng từng module + test delegate mỏng.
- **Nhánh cũ trên GitHub vẫn còn nguyên** (`muse/web2api-dang-nhap-tu-dong`
  tại `86a32e6`). Bản này không xoá, không force-push, không sửa nhánh cũ.
  Người dùng quyết sau: cập nhật hay thay thế nhánh cũ bằng nhánh mới này.

## 2. Module nào được chọn và vì sao

Chọn **cả hai module provider, mỗi module độc lập**, không chọn một module
chung, không chọn lõi, không chọn dịch vụ máy đăng nhập làm chủ logic:

- `modules/chatgpt-web/module.py`: là module duy nhất biết kiểm phiên
  ChatGPT (`/backend-api/me`), biết kho mật khẩu/TOTP riêng của nó, biết
  form đăng nhập chatgpt.com và cách đọc `access_token` từ cookie.
- `modules/gemini-web/module.py`: là module duy nhất biết kiểm phiên Gemini
  (cookie `__Secure-1PSID` qua `init()`), biết kho riêng của nó, biết form
  Google và cách đọc `__Secure-1PSID/__Secure-1PSIDTS` từ cookie.
- `dich-vu/may-dang-nhap` (browser_pool, auto_login solver) **không** giữ
  thang T0–T3: nó chỉ cung cấp bộ điều khiển trình duyệt (qua factory đã
  đăng ký cho từng module). Nó không biết phiên của provider nào, không
  sở hữu kho mật khẩu/TOTP của provider nào.
- Tính độc lập, đã kiểm bằng test: mỗi module **không import module kia**
  (không có chuỗi `modules/gemini-web` trong chatgpt-web, không có
  `modules/chatgpt-web` trong gemini-web), không import logic khôi phục
  của lõi (`khoi_phuc_theo_tang` không có trong cả hai file), không dùng
  chung helper, không dùng chung khóa hay cửa sổ hoãn. Code hai module
  trông giống nhau vì cùng một thang, nhưng đó là **hai bản riêng** nằm
  trong chính file của từng module: hỏng module này không làm hỏng module
  kia, sửa module này không động module kia.

## 3. Đã thêm/chuyển gì vào trong từng module

Mỗi module (chatgpt-web và gemini-web, mỗi module một bản riêng) có:

- `khoi_phuc_tu_dong(khoa, email, mat_khau=None, totp=None,
  trinh_duyet=None, nghi_t1_giay=0.0)` — thang T0–T3 tự chứa, gọi trực
  tiếp module cũng chạy, không cần lõi làm thang:
  - **T0**: `lam_moi_phien(khoa)` — chỉ kiểm. chatgpt-web gọi
    `/backend-api/me`; gemini-web kiểm cookie PSID. **Không bịa endpoint
    làm mới** cho hai module này vì nhà cung cấp không có endpoint công
    khai; đường cứu chính vẫn là T2.
  - **T1**: nghỉ `nghi_t1_giay` rồi kiểm lại (mặc định 0 để test không chờ).
  - **T2**: trong khóa serial riêng của module, đăng nhập lại bằng mật
    khẩu đã lưu + TOTP đã lưu qua trình duyệt (xem dưới).
  - **T3**: kiểm lại bằng `lam_moi_phien`; nếu khoá là id ngoài module
    (ví dụ id kho MCP, không phải khoá nội bộ) mà `lam_moi` không nhận,
    thì lấy luôn kết quả xác minh phiên của T2 (module đã kiểm token/
    cookie trong lúc đăng nhập), không báo hỏng giả.
  - Tầng (c) vẫn là `tai_khoan_ke()` riêng; `khoi_phuc_tu_dong` không tự
    đổi tài khoản âm thầm.
- Kênh TOTP trong chính module:
  - `luu_totp(khoa, email, secret)` — lưu secret Base32 vào kho riêng
    mã hoá của module; sai khuôn (không phải Base32, độ dài ngoài
    16–128) thì trả `False`, không lưu. Secret chỉ lưu khi chủ máy gọi
    tường minh; module không tự trích secret từ đối tượng mã.
  - `totp_da_luu(khoa)` — trả `BiMatTotp` (mã được tính đúng lúc gọi),
    không trả secret thô, không log secret.
  - `_xu_ly_2fa(trinh_duyet, totp)` — gặp 2FA mà có TOTP thì tự điền mã
    (bộ chọn `ma_xac_minh`, nút `xac_nhan_2fa`), rồi ghi đè biến mã và
    xoá totp ngay sau khi dùng. Không có TOTP thì trả `can_nguoi`.
  - `_dang_nhap_bang_trinh_duyet` nay nhận `totp`: nếu trang đã có 2FA
    trước khi điền mà có TOTP thì vẫn điền mật khẩu rồi xử lý 2FA; không
    có TOTP thì dừng ở `thu_thach_truoc_khi_dien`. `dang_nhap` (hợp đồng
    NV67) truyền `tai_khoan.totp` qua; `dang_nhap_tu_dong` (tầng b) cũng
    nhận `totp` và dùng controller đã đăng ký riêng cho module nếu không
    được truyền vào.
- Controller thật, riêng từng module: `dang_ky_trinh_duyet(ham_tao)` và
  `_lay_trinh_duyet_module()` — thử `_tao_trinh_duyet` (đường test) trước,
  rồi factory đã đăng ký trên chính thể hiện module đó. Chưa đăng ký thì
  module trả `trinh_duyet_none`. Chủ máy phải đăng ký factory cho từng
  module riêng; không còn registry chung ở lõi.
- Khóa serial và hoãn captcha, riêng từng module: khóa `asyncio.Lock`
  tạo lười trên thể hiện module; cửa sổ hoãn captcha mặc định 1800 giây,
  chỉ hoãn các khoá khác trong cùng module đó, không hoãn module kia.
  `dat_lai_trang_thai_tu_dong()` dùng cho test để xoá trạng thái này.
- Mã lỗi riêng của module, tách khỏi `can_nguoi`:
  `trinh_duyet_none` (chưa nối controller), `thu_thach_truoc_khi_dien`
  (trang đã có thử thách trước khi điền), `het_gio` (hết thời gian),
  `captcha_hoan` (đang trong cửa sổ hoãn captcha của module),
  `thieu_mat_khau`. `can_nguoi` chỉ còn đúng nghĩa: cần người vì thử
  thách mà module không có cách tự xử lý (xem mục 5).

## 4. Lõi web2api còn làm gì (thin translator only)

- `app/cong_mcp_cong_cu.py` (+35 dòng, duy nhất một hàm mới):
  `_thu_khoi_phuc_module(so, tk_id, module_id)` — chuyển tiếp mỏng:
  lấy module đang chạy, nếu có `khoi_phuc_tu_dong` thì gọi nó với
  `(tk_id, email, nghi_t1_giay=0.0)` rồi dịch kết quả sang dict cho
  `_ap_ket_qua`. Nó không quyết tầng, không khóa, không hoãn captcha,
  không tạo TOTP, không chạm bí mật (mật khẩu/TOTP do module tự lấy từ
  kho riêng của nó). Module chưa có hàm này thì trả `None` và
  `_chay_dang_nhap` dùng đường cũ qua `tuyen` làm fallback.
- Mọi cổng MCP giữ nguyên: allowlist `id@module` mặc định rỗng, một phiên
  một lúc, nghỉ 3600 giây, tối đa 3 thành công/ngày, khóa sau 2 hỏng liên
  tiếp, timeout 300 giây. Cổng vẫn không có đường nhận mã 2FA hay giải
  thử thách từ phía MCP — TOTP chỉ đi qua kho riêng của module, không qua
  MCP, không qua log.

## 5. Không vượt thử thách — giữ nguyên

CAPTCHA, bot-check, selfie, xác minh điện thoại, tài khoản bị khóa, hoặc
tap/code khi không có TOTP đã lưu: vẫn dừng ở `can_nguoi` (hoặc mã riêng
`thu_thach_truoc_khi_dien` khi thử thách có trước khi điền), đóng trình
duyệt, không thử lại dồn dập, không dùng dịch vụ giải hộ, không OCR.
TOTP chỉ tự động khi secret đã được lưu trước trong kho riêng của module.

## 6. Kết quả test — báo theo từng module, không gộp chung

Tất cả test dùng trình duyệt giả (`TrinhDuyetGia`) và máy chủ giả
(`httpx.MockTransport`), không đăng nhập thật, không gọi
`dang_nhap_bat_dau`, không dùng key MCP, không chạm phiên đang chạy.
Chạy bằng venv riêng `~/workspace/web2api-fix/venv-test` (không nằm trong
patch) vì Python hệ thống không có pytest/httpx.

### chatgpt-web — riêng
- Test mới `test/test_web2api_nv_module_chatgpt_tu_dong.py`: **9 passed**.
  Gồm: độc lập không import module kia, T0 khi phiên còn sống, T2 bằng
  mật khẩu đã lưu, T2 qua factory đăng ký riêng, `trinh_duyet_none` là
  mã riêng, 2FA có TOTP tự điền mã, 2FA không TOTP dừng ở thử thách,
  captcha hoãn rồi đặt lại trạng thái thì chạy lại được, lưu TOTP sai
  khuôn bị từ chối.
- Test cũ của chatgpt-web (riêng, không gộp với gemini):
  `test_web2api_nv88_chatgpt_web.py`, `test_web2api_nv93_chatgpt_web.py`,
  `test_nv210_chatgpt_dang_nhap.py`, `test_web2api_chatgpt-web.py`,
  `test_web2api_nv102_web_chatgpt.py`: **81 passed, 0 failed**.

### gemini-web — riêng
- Test mới `test/test_web2api_nv_module_gemini_tu_dong.py`: **9 passed**.
  Cùng 9 nhóm kiểm như chatgpt-web nhưng chạy trong môi trường giả lập
  riêng của gemini-web (trang Google, cookie PSID).
- Test cũ của gemini-web (riêng, không gộp với chatgpt):
  `test_web2api_nv89_gemini_web.py`, `test_web2api_nv93_gemini_web.py`,
  `test_web2api_gemini-web.py`, `test_web2api_nv102_web_gemini.py`,
  `test_web2api_nv134_gemini_web_tools.py`: **95 passed, 0 failed**
  (sau khi cập nhật 2 test cũ, xem dưới).
- **2 test cũ đã cập nhật, không làm yếu**: trong
  `test_web2api_nv89_gemini_web.py`, `test_dang_nhap_gap_captcha_thi_can_nguoi`
  và `test_dang_nhap_khong_co_trinh_duyet_thi_can_nguoi` trước đây khẳng
  định mã `can_nguoi`. Theo yêu cầu mã riêng của bản này, chúng nay khẳng
  định `thu_thach_truoc_khi_dien` và `trinh_duyet_none`. Hành vi giữ
  nguyên: vẫn thất bại, vẫn không điền, vẫn xoá mật khẩu — chỉ mã rõ hơn.
  Trước khi cập nhật, 2 test này là 2 failed duy nhất của nhóm gemini;
  sau cập nhật, nhóm đạt 95/95.

### Lõi / MCP — riêng
- Test delegate mỏng `test/test_web2api_mcp_module_delegate.py`:
  **2 passed** (gọi đúng module và dịch kết quả; module không có hàm thì
  trả `None` để fallback).
- Nhóm lõi liên quan (MCP + khôi phục + NV92 + NV209):
  `test_mcp_cong.py`, `test_web2api_nv88_khoi_phuc.py`,
  `test_web2api_nv92_p2.py`, `test_web2api_nv92_p3.py`,
  `test_nv209_may_dang_nhap_can_nguoi.py`: **152 passed, 0 failed**.

## 7. Kiểm chứng patch

- Patch: `web2api-module-dang-nhap-tu-dong.patch`, 2729 dòng, 133878 byte,
  `git format-patch ffb7f3e..HEAD` (nền `ffb7f3e`, không phải patch tăng
  thêm từ `7457fbd`, vì so với `ffb7f3e` thì phần lõi của bản trước đã về
  0 — patch này tự nó đã là bản thay thế đầy đủ).
- Áp sạch bằng `git am --3way` trên clone sạch từ `ffb7f3e` (cùng diffstat
  7 file, 988 thêm / 32 bớt), và test mới + delegate trong clone đó đạt
  **20 passed** (9 chatgpt + 9 gemini + 2 delegate).
- Quét bí mật: không có token/key/mật khẩu thật/cookie/TOTP thật trong
  patch và báo cáo. Chuỗi duy nhất trông giống secret TOTP là secret test
  công khai trong tài liệu (chuỗi test giả, không gắn tài khoản thật) và
  các chuỗi giả `mat-khau-gia-…`, `token-gia-…` trong test.
- `git diff --check` đạt, `py_compile` đạt cho 3 file code đã sửa.

## 8. File outbox — tên chính xác

Nhánh Giao-nhi-m-v- cục bộ mới (chưa push, chưa PR):
`muse/web2api-module-dang-nhap-tu-dong`, nền `35ea07d`, chứa trong `outbox/`:

- `web2api-module-dang-nhap-tu-dong.patch`
- `web2api-module-dang-nhap-tu-dong-bao-cao.md` (file này)
- `hoi-web2api-module-dang-nhap-tu-dong.md` (4 câu hỏi)

Bản sao giống hệt ở `~/workspace/web2api-fix/outbox2/` (thư mục riêng,
không ghi đè `~/workspace/web2api-fix/outbox/` của bản trước).
Kho làm việc web2api: `~/workspace/web2api-fix/repo`, nhánh
`web2api-module-dang-nhap-tu-dong`, commit `fb8aa25`.

## 9. Giới hạn còn lại — chủ máy vẫn phải làm trên máy chủ

1. Đăng ký controller thật **cho từng module riêng** bằng
   `module.dang_ky_trinh_duyet(factory)`; chưa đăng ký thì module trả
   `trinh_duyet_none` (nay báo đúng mã, không còn chìm thành can_nguoi).
2. Nạp secret TOTP cho từng tài khoản vào kho riêng của module bằng
   `luu_totp(khoa, email, secret)`; chưa nạp thì 2FA vẫn dừng ở
   `thu_thach_truoc_khi_dien`/`can_nguoi`.
3. Đặt allowlist MCP đúng `id@module` cho từng tài khoản và module đang
   chạy, nếu không MCP vẫn trả `khong_cho_phep`/`chua_ho_tro` trước khi
   delegate tới module.
4. Tầng (a) của hai module web vẫn chỉ kiểm, không làm mới token/cookie
   thật; nhà cung cấp có đường refresh-token thật mới dùng đường đó.
5. Patch chưa merge, chưa chạy trên máy chủ web2api đang chạy, nên đăng
   nhập thật qua MCP ở đó vẫn như cũ cho tới khi merge + làm 1–3 ở trên.
