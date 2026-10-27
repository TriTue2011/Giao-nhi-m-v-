# NV272 — Báo cáo: gemini-web và grok-web khởi động được khi chưa có cookie

- Nhánh: `muse/nv272` trên repo `TriTue2011/web2api`, nền `ffb7f3e`,
  commit `64e741c` (1 commit duy nhất, 6 file, 94 thêm / 7 bớt).
- Patch: `nv272.patch` (`git format-patch ffb7f3e..HEAD`, 193 dòng),
  đã kiểm `git am --3way` áp sạch trên clone sạch từ `ffb7f3e`.
- **Chưa push** (theo lệnh giao việc: chat chính xử lý push/outbox sau).
- Không chạm NV273: không sửa file/nhánh của NV273; không sửa
  claude-web, openaicodex, muse2api theo hướng NV273.

## 1. Lớp lỗi (ba câu cho commit)

- **Lớp lỗi:** module có khả năng tự đăng nhập (manifest khai
  `dang_nhap_bang`) bị lõi chặn ở `app/so_module.py::_tao_tu_kho`
  vì thiếu trường bí mật bắt buộc, nên không vào `dang_chay`, không có
  chỗ chạy để đăng nhập tự động tự lấy cookie về. Đây là lý do Google
  trả `chua_ho_tro`: `/api/modules` báo `gemini-web` có
  `da_cau_hinh: False` vì nó không nằm trong `dang_chay`.
- **Đã grep chỗ cùng lớp (lệnh + số):** duyệt mọi
  `modules/*/manifest.json`, lọc trường `bat_buoc` có kiểu chứa
  `bi_mat` → **25 module**. Trong đó **5 module khai `dang_nhap_bang`**
  (cùng lớp lỗi, diện tự đăng nhập): antigravity (`khoa_cau_noi`),
  chatgpt-web (`tai_khoan`), claude-web (`cookies`), gemini-web
  (`cookies`), grok-web (`tai_khoan`). **20 module không khai**
  `dang_nhap_bang` thì giữ bắt buộc như cũ: cameronha, doc-ma-hop-thu,
  email, facebook, gemini-api, grok-api, home-assistant, khoa-cua,
  lich-ics, may-dang-nhap, mikrotik-routeros, muse, muse2api, rclone,
  telegram-bot, van-phong, vnc-xa, youtube-phat, zalo-bot, zte-e2633.
- **Theo nguyên tắc, không theo danh sách:** lõi chỉ kiểm tra cấu trúc
  manifest có `dang_nhap_bang` hay không; lõi không nhắc tên module hay
  nhà cung cấp nào. Mỗi module tự trả mã rõ, không phụ thuộc chéo,
  không dùng chung logic qua lõi.

## 2. Thay đổi theo từng module

### Lõi chung (app/so_module.py, +12/-1) — theo nguyên tắc

Trong `_tao_tu_kho`: nếu manifest có `dang_nhap_bang` thì trường bí mật
bị thiếu (kiểu chứa `bi_mat`) không còn chặn khởi động; trường bắt
buộc không phải bí mật vẫn chặn như cũ; module chưa có mục trong
`modules.json` vẫn chưa chạy. Module được `nap()` với cấu hình rỗng
(gemini-web: 0 tài khoản; grok-web: 0 tài khoản) và vào `dang_chay`,
nên `/api/modules` báo `da_cau_hinh: True`.

Hệ quả cần biết (đã báo rõ, không giấu): quy tắc này áp chung cho cả
5 module có `dang_nhap_bang`, không chỉ gemini-web/grok-web. Vì vậy
antigravity, chatgpt-web và claude-web khi thiếu bí mật cũng sẽ khởi
động ở trạng thái chưa có phiên từ nay. ChatGPT được file NV272 nói là
không bị lỗi này (đã có tài khoản lưu nên `da_cau_hinh: True` sẵn);
với tài khoản đã lưu thì hành vi không đổi. Test nhóm của các module
này đã chạy (xem mục 3).

### gemini-web (modules/gemini-web/module.py, +8/-2) — độc lập

- Khởi động: `nap({})` vốn đã chỉ tách cookie, không gọi mạng; danh
  sách rỗng → 0 tài khoản, không lỗi. Nay lõi cho thể hiện này vào
  `dang_chay`.
- Chat chưa có phiên: trước đây trả 401 với thông điệp “chưa có tài
  khoản nào: thêm cookie…”; nay trả **401, mã rõ `can_dang_nhap`**
  (qua tham số `code` của `than_loi`), thông điệp “chưa có phiên:
  đăng nhập tự động để lấy cookie Google về rồi gọi lại”.
  Mã HTTP giữ nguyên 401.
- `cai()` không đổi: 0 cookie vẫn trả `ok: False` (“Chưa nhập cookie
  nào”) — đường lấy cookie là đăng nhập tự động, không phải `cai()`
  với 0 cookie.
- `models()` vốn đã liệt kê model khi 0 tài khoản, nên `/v1/models`
  vẫn thấy model sau khi module chạy.

### grok-web (modules/grok-web/module.py, +8/-2) — độc lập

- Khởi động: `_nap_tu({})` với danh sách rỗng → 0 tài khoản, không lỗi
  (chỉ lỗi khi một chuỗi cookie có mà thiếu `sso`). Nay lõi cho thể
  hiện này vào `dang_chay`.
- Chat chưa có phiên: trước đây trả 404, mã `missing_credentials`;
  nay trả **404, mã rõ `can_dang_nhap`**, thông điệp “chưa có phiên:
  đăng nhập tự động để lấy cookie Grok về rồi gọi lại”. Mã HTTP giữ
  nguyên 404 để ít vỡ test cũ nhất; mã rõ nằm ở `error.code`.
- `cai()` không đổi: 0 tài khoản vẫn trả `ok: False`.
- Không phụ thuộc chatgpt-web/gemini-web: không import chéo, không
  dùng chung helper/khóa/hoãn; hai bản sửa nằm trong chính file của
  từng module.

## 3. Test — số thật

Test đỏ trước (chứng minh): trên nền `ffb7f3e`, test mới
`test/test_web2api_nv272_khoi_dong_khong_cookie.py` đỏ đúng chỗ chặn
(`so_module.py:683`, “cấu hình đã lưu thiếu trường bắt buộc
['cookies'] — coi như chưa liên kết”), sau sửa thì xanh.

Test mới (HTTP qua TestClient, theo mẫu test_antigravity_module, chỉ
máy chủ giả, không mạng thật):
- Khởi động với module đã cài nhưng không có cookie → `/api/modules`
  báo `gemini-web` và `grok-web` có `da_cau_hinh: True`.
- Gọi `/v1/chat/completions` chưa có phiên → cả hai đều trả
  `error.code == "can_dang_nhap"`.
- Đối chứng: `gemini-api` (không tự đăng nhập, trống `api_keys`) vẫn
  `da_cau_hinh: False`.

Nhóm test của module + liên quan (chạy bằng venv
`~/workspace/nv272/.venv`, `pytest -p no:randomly -p no:cacheprovider`):
**220 passed** — gồm test NV272 mới, gemini-web, grok-web, nv102
(gemini/grok/claude), nv134, nv80, nv89, nv93, api, antigravity,
cai_khong_khoa. Hai test cũ được cập nhật theo đúng hành vi mới bắt
buộc của NV272 (không xóa test, không nới kiểm):
- `test_web2api_gemini-web.py::TestKhongCoTaiKhoan::test_chat_khong_tai_khoan_401_chu_khong_vo`:
  vẫn 401, nay kiểm `code == "can_dang_nhap"` và “chưa có phiên”.
- `test_web2api_grok-web.py::test_khong_co_tai_khoan_nao`: vẫn 404, nay
  kiểm `code == "can_dang_nhap"` (thay `missing_credentials` cũ).

Toàn bộ `test/` (trừ file lỗi import sẵn có dưới đây):
- Lần chạy đầu bị ngắt ở khâu thu thập do lỗi import sẵn có trên nền
  sạch (không phải do NV272): `test/test_web2api_dang_nhap_tu_dong.py`
  import `test.gia` — đã kiểm chứng lỗi này cũng xảy ra trên clone
  sạch `ffb7f3e` trong cùng môi trường. Vì vậy toàn bộ được chạy trừ
  file đó, lệnh: `pytest test/ -q -p no:randomly -p no:cacheprovider
  --ignore=test/test_web2api_dang_nhap_tu_dong.py`.
- Kết quả cuối (log: `full-suite.log`, 17 phút 27 giây):
  **61 failed, 5980 passed, 237 skipped, 31 xfailed, 18 errors**
  trên tổng 6327 test thu thập được.
- **Không có đỏ mới do NV272.** Đối chiếu từng nhóm failed/error với
  nền sạch `ffb7f3e` trong cùng môi trường:
  - `test_nv151_mqtt.py` 51 failed + 8 errors: giống hệt trên nền sạch
    khi chạy riêng (51 failed, 36 passed, 6 skipped, 8 errors) — lỗi
    `app.kham_pha…` sẵn có, không liên quan tới gemini/grok.
  - `test_web2api_nv268_giao_dien_khu_tai_khoan.py` 8 errors,
    `test_web2api_nv259_trang_module.py` 2 errors,
    `test_web2api_muse2api.py` 1 failed, `test_module_youtube_phat.py`
    1 failed, `test_web2api_nv85_kiem_module.py` 2 failed,
    `test_web2api_nv187_khoa_khong_tai_nhap.py` 1 failed,
    `test_web2api_nv159_sua.py` 1 failed (c5),
    `test_web2api_bien_env_tai_lieu.py` 1 failed: tất cả đều tái hiện
    y hệt trên nền sạch (lượt chạy riêng nền sạch: 7 failed, 10 errors
    cho đúng các file này) — trùng với danh sách 9 đỏ có sẵn/chập
    chờn mà file NV272 đã nêu.
  - `test_web2api_nv266_do_tai_nguyen.py`,
    `test_web2api_nv261_do_tai_nguyen.py`, `test_nv154_email.py` (mỗi
    file 1 failed trong lượt toàn bộ): chạy riêng trên nhánh NV272 đều
    xanh (**60 passed, 8 skipped, 0 failed**) — chập chờn theo tải máy
    khi chạy toàn bộ (nv261 đã được ghi chú là chỉ đỏ khi máy bận),
    không phải do sửa này.
  - Không có failed/error nào ở các file gemini-web, grok-web,
    chatgpt-web, claude-web, antigravity, cai_khong_khoa, nv102, nv89,
    nv93 trong lượt toàn bộ.

Bandit: `bandit -r app modules -lll` **thoát 0**, không có finding ở
các file đã sửa. `git diff --check` sạch. Quét bí mật/IP trên patch:
sạch (không token/key/mật khẩu/cookie/IP thật; test chỉ dùng khóa giả
`khoa-qt-nv272` và khóa quản trị giả trong test cũ).

## 4. Chỗ chưa kiểm — nói thật

- **Không đăng nhập thật vào nhà cung cấp ngoài**, không gọi
  `dang_nhap_bat_dau`, không dùng key MCP, không dùng bí mật nào.
  Việc đăng nhập tự động thật (qua MCP hoặc nút Đăng nhập) và việc
  cookie thật được lấy về sau khi module chạy vẫn cần người dùng
  áp patch, test và dựng lại server rồi chạy trên máy chủ thật.
- Chat thành công với cookie giả không được khẳng định bằng HTTP:
  `cai()` của hai module kiểm cookie bằng cách gọi nhà cung cấp thật
  nên không thể “thêm cookie giả → chạy bình thường” qua HTTP offline;
  đường chat bình thường khi có cookie đã được các test mock-transport
  sẵn có của từng module bao phủ (nằm trong 220 passed trên).
- `suc_khoe()` không đổi: khi 0 tài khoản vẫn báo “chưa cấu hình”
  (grok-web) / `ok: False` (gemini-web); chỉ đường chat đổi sang
  `can_dang_nhap` theo đúng yêu cầu của file NV272.

## 5. Còn lại cho người dùng áp/test/dựng lại

1. Đẩy nhánh `muse/nv272` lên `TriTue2011/web2api` (hoặc nộp patch
   ở outbox nếu push bị 403) — agent này không push theo lệnh giao việc.
2. Gộp với nhánh module đăng nhập `muse/web2api-module-dang-nhap-tu-dong`
   (đã có trên Giao-nhi-m-v-): NV272 chỉ cho module chỗ chạy khi chưa
   có cookie; việc đăng nhập tự động lấy cookie vẫn nằm ở bản module đó.
3. Trên máy chủ: sau khi dựng lại, kiểm tra `/api/modules` thấy
   `gemini-web`/`grok-web` có `da_cau_hinh: True` khi chưa có cookie,
   gọi chat thấy `can_dang_nhap`, rồi chạy đăng nhập tự động và kiểm
   tra cookie được lấy về.
4. Trả lời giúp câu hỏi mở: có chấp nhận antigravity/chatgpt-web/
   claude-web cũng khởi động ở trạng thái chưa có phiên khi thiếu bí
   mật (hệ quả của quy tắc chung) hay muốn thu hẹp quy tắc chỉ cho
   gemini-web/grok-web — nếu thu hẹp thì đó sẽ là danh sách tên trong
   lõi, trái nguyên tắc file NV272 đã đặt.
