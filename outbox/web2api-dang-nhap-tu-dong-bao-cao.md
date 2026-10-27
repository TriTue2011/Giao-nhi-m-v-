# Báo cáo sửa lỗi đăng nhập tự động web2api

## Cơ sở và phạm vi

- Repo nguồn: TriTue2011/web2api, nhánh làm việc `web2api-dang-nhap-tu-dong`,
  nền `ffb7f3e` (main, commit `7457fbd` trong kho làm việc).
- Không làm trên nhánh `muse/nv271-nen` vì nhánh đó cũ hơn và chưa có cổng MCP.
- Không chạy đăng nhập thật với bất kỳ nhà cung cấp nào, không gọi
  `dang_nhap_bat_dau`, không dùng key MCP, không chạm phiên đang chạy.
- Chỉ test bằng module giả và bộ điều khiển giả.
- Chưa push, chưa tạo Pull Request. Việc đẩy đi vẫn cần người dùng xác nhận
  cách đẩy an toàn, như trường hợp NV270 (không dùng lại token đã gửi trong chat
  cho repo công khai).

## Lỗi đã quan sát trước khi sửa (để đối chiếu, không phải kết quả test mới)

- Phiên ChatGPT, tài khoản `tk-21045e6bd2684c5f`, phiên `c232ead015502c50`,
  bắt đầu và kết thúc cùng lúc 19:29:42 ngày 27/10/2026, trạng thái cuối
  `that_bai`, mã lỗi `can_nguoi`, thử lại sau 3594 giây.
- Phiên Google, tài khoản `tk-b7b85b75867aac4c`, phiên `420ad58837d765c6`,
  bắt đầu và kết thúc cùng lúc 20:31:08 ngày 27/10/2026, trạng thái cuối
  `that_bai`, mã lỗi `chua_ho_tro`, thử lại sau 3594 giây.
- Hai mã này khác nhau và không được gộp chung thành một lỗi đăng nhập.
  `chua_ho_tro` của phiên Google phù hợp với việc module thực thi không có
  trong danh sách đang chạy (trước đó `tong_quan` ghi `gemini-web` không chạy,
  chỉ `gemini-api` chạy), hoặc allowlist `id@module` chưa khớp — xem file hỏi thêm.

## Đã sửa

### P0 — Nối bộ điều khiển trình duyệt thật (NV92) và tách mã lỗi riêng

- `app/tu_lam_moi.py`: thêm `lay_trinh_duyet_da_dang_ky(module_id)` và
  `dang_ky_trinh_duyet_that(module_id, ham_lay_dang_chay, ham_lay_ho_so)`.
  Factory tìm module có khả năng `trinh_duyet` và gọi `trinh_duyet_that(ho_so)`
  của nó; không tìm được, hồ sơ sai khuôn hoặc dịch vụ chưa cấu hình thì
  trả `None` (fail-closed).
- `modules/chatgpt-web/module.py` và `modules/gemini-web/module.py`:
  khi `_tao_trinh_duyet` chưa gán thì lấy controller đã đăng ký qua
  `tu_lam_moi.lay_trinh_duyet_da_dang_ky`, thay vì để `None` rồi trả
  `can_nguoi` ngay chưa điền gì.
- Mã lỗi riêng, không chìm chung vào `can_nguoi`:
  - `trinh_duyet_none`: chưa có bộ điều khiển trình duyệt — lỗi nối dây /
    cấu hình, không phải thử thách.
  - `thu_thach_truoc_khi_dien`: trang đích đã có tín hiệu CAPTCHA / 2FA /
    xác minh trước khi điền gì — dừng, không cố vượt.
  - `het_gio`: hết thời gian khi mở trang / đọc tín hiệu (cả ở
    `app/khoi_phuc_phien.py:_goi_an_toan`, trước đây chìm thành `loi_module`).
- `app/khoi_phuc_phien.py`: thêm `lay_trinh_duyet_that_theo_email(email, dang_chay)`
  (email → danh tính → hồ sơ trình duyệt hex → cầu nối `lay_trinh_duyet_that`).

### P1 — Cổng MCP đi qua thang khôi phục T0–T3

- `app/cong_mcp_cong_cu.py`: thêm `_thu_khoi_phuc_tang(phien, so, tk_id, module_id)`,
  được `_chay_dang_nhap` gọi trước đường cũ.
- Đường mới: đọc bản ghi kho tài khoản, kiểm tra tạm dừng, lấy mật khẩu đã
  lưu dưới dạng `BiMatTam` (xoá sau khi dùng, kể cả khi lỗi), rồi gọi
  `app/khoi_phuc_phien.py:khoi_phuc_theo_tang_c2a()` với
  `dang_chay=so.dang_chay`, `xac_nhan_lai_sau_dang_nhap=False`,
  `nghi_t1_giay=0.0`. Kết quả được ánh xạ qua `_ap_ket_qua` như cũ
  (thanh_cong / can_nguoi / cho_2fa / that_bai kèm mã).
- Giữ nguyên mọi cổng MCP: allowlist `id@module` mặc định rỗng, một phiên
  một lúc, nghỉ 3600 giây, tối đa 3 thành công mỗi ngày, khóa sau 2 hỏng
  liên tiếp, timeout 300 giây.
- Giữ đường cũ (`tuyen.dang_nhap_tai_khoan_da_luu_noi_bo`) làm fallback
  trong đúng hai trường hợp: module không có tầng khôi phục nào
  (`lam_moi_phien` / `dang_nhap_tu_dong`), và tài khoản ở chế độ
  «đăng nhập qua tài khoản lưu khác» (đường cũ mới giữ đúng bí mật của
  tài khoản hộ). Nhờ đó các test MCP cũ dùng module giả chỉ có `dang_nhap`
  không bị vỡ.
- Để gọi được c2a từ MCP, `khoi_phuc_theo_tang_c2a` có thêm hai tham số
  tùy chọn, mặc định giữ hành vi cũ cho mọi người gọi khác:
  - `xac_nhan_lai_sau_dang_nhap=True`: sau T2 thành công thì làm T3.
    MCP đặt `False` vì lý do có ghi rõ trong mã: khoa MCP truyền vào là
    id tài khoản `tk-…`, không phải khoa nội bộ suy từ token / cookie của
    module, nên `lam_moi_phien` không thể xác nhận đúng tài khoản đó;
    thành công của T2 đã do chính module xác minh khi đăng nhập trình duyệt.
  - `nghi_t1_giay=None` (mặc định `T1_NGHI_GIAY`): MCP đặt `0.0` vì nó đã
    có nghỉ 3600 giây riêng và T1 không có ý nghĩa khi khoa không phải
    khoa nội bộ.

### P2 — Khóa serial và cửa sổ hoãn captcha cho T2

- `app/khoi_phuc_phien.py`: khóa serial `_khoa_t2()` quanh lượt đăng nhập
  lại (một lượt T2 tại một thời điểm), giãn cách `T2_GIAN_CACH_GIAY`
  (mặc định 0.0, MCP đã có nghỉ riêng), cửa sổ hoãn captcha
  `CAPTCHA_HOAN_GIAY` (mặc định 1800 giây) cho các tài khoản khác cùng
  module khi một tài khoản gặp captcha (`captcha`,
  `thu_thach_truoc_khi_dien`, `need_captcha`). Hàm `dat_lai_trang_thai_t2()`
  dùng cho test.

### P3 / P4 — Chưa làm, và lý do

- P3 (làm mới chủ động): không thêm endpoint làm mới nào. Tầng (a) của
  `chatgpt-web` (gọi `/backend-api/me`) và `gemini-web` (kiểm cookie PSID)
  chỉ KIỂM, không phải làm mới thật; hai nhà cung cấp này không có endpoint
  làm mới token / cookie công khai, nên không được bịa endpoint.
- P4 (TOTP): chưa có kênh TOTP trong thang c2a (`TaiKhoanCanKhoiPhuc`
  không có trường TOTP), nên trong đường MCP mới, TOTP đã lưu (nếu có) bị
  xoá ngay mà không đưa vào c2a. Hệ quả: tài khoản nào gặp 2FA qua đường
  này vẫn dừng ở `can_nguoi`. Cách sửa đúng cho P4 là bổ sung kênh TOTP
  cho c2a trong một lần sửa riêng, không phải bỏ qua 2FA — xem file hỏi thêm.

## File thay đổi (6 file, 530 thêm, 22 bớt)

- `app/cong_mcp_cong_cu.py` (+82): `_thu_khoi_phuc_tang`, nối P1 vào `_chay_dang_nhap`.
- `app/khoi_phuc_phien.py` (+183, gồm cả phần P0/P2 của lần sửa trước):
  `het_gio` riêng, `lay_trinh_duyet_that_theo_email`, khóa serial T2,
  cửa sổ hoãn captcha, tham số `xac_nhan_lai_sau_dang_nhap` /
  `nghi_t1_giay` cho c2a.
- `app/tu_lam_moi.py` (+54): `lay_trinh_duyet_da_dang_ky`,
  `dang_ky_trinh_duyet_that`.
- `modules/chatgpt-web/module.py` (+35): mã lỗi riêng, lấy controller
  đã đăng ký khi `_tao_trinh_duyet` chưa gán.
- `modules/gemini-web/module.py` (+27): tương tự chatgpt-web.
- `test/test_web2api_mcp_khoi_phuc_tang.py` (+171, file mới): 7 test
  (xem dưới).

## Kết quả test (chỉ module giả, không đăng nhập thật)

Môi trường test: venv riêng tại `/tmp/venv-web2api-fix` (pytest, fastapi,
cryptography, python-multipart, websockets, pillow, uvicorn); không đưa
venv vào patch.

- Test mới `test/test_web2api_mcp_khoi_phuc_tang.py`: **7 passed**.
  Chứng minh: MCP qua c2a, T2 thành công → `thanh_cong`;
  `trinh_duyet_none` → `that_bai` với đúng mã đó, không thành `can_nguoi`;
  `thu_thach_truoc_khi_dien` → `can_nguoi`; module không có tầng khôi phục
  → giữ đường cũ, không gọi module; tài khoản tạm dừng → `tam_dung`;
  tài khoản không có → `khong_tim_thay`; tài khoản đăng nhập qua tài khoản
  lưu khác → giữ đường cũ; c2a mặc định (có T3) và MCP (bỏ T3) khác nhau
  đúng như thiết kế ở trên.
- Test cũ liên quan: `test/test_mcp_cong.py`,
  `test/test_web2api_nv235_t0_t3.py`, `test/test_web2api_nv88_khoi_phuc.py`,
  `test/test_web2api_nv92_p3.py`: **125 passed**.
- Test cũ module web: `test/test_web2api_chatgpt-web.py`,
  `test/test_web2api_gemini-web.py`, `test/test_nv210_chatgpt_dang_nhap.py`,
  `test/test_nv209_may_dang_nhap_can_nguoi.py`: **94 passed**.
- Tổng các test liên quan đã chạy: **226 passed, 0 failed**.
- Kiểm tra khác: `git diff --check` đạt, `python -m py_compile` đạt cho
  6 file thay đổi, patch áp sạch bằng `git am --3way` trên clone sạch từ
  `ffb7f3e` (xem dưới).

## Mã lỗi riêng sau sửa (để người sửa phân biệt)

- `trinh_duyet_none`: thiếu controller — nối dây, không phải thử thách.
- `thu_thach_truoc_khi_dien`: trang đã có thử thách trước khi điền — dừng.
- `het_gio`: hết thời gian.
- `hoan_captcha`: tài khoản khác cùng module vừa gặp captcha, hoãn T2.
- `hoan_phien_ban`, `dang_trong_debounce`: hoãn theo thang c2a, không phải lỗi.
- `can_nguoi`: vẫn là mã cuối cho thử thách cần người, nhưng nay chỉ dùng
  khi thật sự có thử thách, không dùng cho lỗi nối dây nữa.
- `chua_ho_tro`: giữ nguyên cho trường hợp module không có trong danh sách
  đang chạy hoặc không triển khai đường đăng nhập — không tự biến thành
  thành công.

## Vẫn giữ cổng cần người (không được tự động vượt)

CAPTCHA và mọi bot-check mà bước bấm ô / đường âm thanh có sẵn không qua
được; xác minh selfie; xác minh qua điện thoại gọi / SMS; tài khoản bị
khóa hoặc đăng nhập bị từ chối; `need_tap` và `need_code` khi không có
TOTP đã lưu; mọi xác minh danh tính khác. Khi gặp các tín hiệu này: dừng
ngay tại `can_nguoi`, đóng trình duyệt, không lặp tới hết trần, không thử
lại dồn dập, không dùng dịch vụ giải hộ hay OCR ngoài, và không biến
chúng thành «thành công» chỉ vì cookie cũ còn sót. Allowlist MCP giữ dạng
`id@module` do chủ máy đặt, mặc định rỗng.

## Giới hạn còn lại (đọc trước khi thử lại đăng nhập thật)

1. Chưa có kênh TOTP trong c2a (xem P4 ở trên và file hỏi thêm).
2. Chủ máy vẫn phải đăng ký controller thật qua `dang_ky_trinh_duyet` /
   `dang_ky_trinh_duyet_that` (hoặc cầu nối danh tính → hồ sơ trình duyệt);
   nếu chưa đăng ký gì, module vẫn trả `trinh_duyet_none` — nay ít nhất
   báo đúng mã đó thay vì `can_nguoi`.
3. Chủ máy vẫn phải đặt allowlist đúng `id@module` và module thực thi phải
   đang chạy; nếu không, MCP vẫn trả `khong_cho_phep` / `chua_ho_tro`
   trước cả khi chạy thang khôi phục.
4. Chưa đối chiếu log máy chủ để phân biệt «controller None» với
   «tín hiệu thử thách có sẵn trên trang» cho phiên ChatGPT `can_nguoi`
   ban đầu — giả thuyết controller None là mạnh nhất từ code, chưa phải
   kết luận tuyệt đối.

## Kiểm chứng patch

- Patch được tạo bằng `git format-patch ffb7f3e..HEAD --stdout`.
- Đã áp thử bằng `git am --3way` trên clone sạch từ `ffb7f3e`: áp được,
  cùng diffstat 6 file, 530 thêm, 22 bớt.
- Đã quét các file outbox: không có token / key / mật khẩu thật / cookie /
  TOTP thật. Chỗ duy nhất trông giống mật khẩu là chuỗi giả trong test
  mới (`mat-khau-gia`, giá trị placeholder trong code test, không phải
  bí mật thật). Các file chỉ chứa id tài khoản dạng `tk-…` và id phiên
  đã báo trước đó, không chứa bí mật thật.
