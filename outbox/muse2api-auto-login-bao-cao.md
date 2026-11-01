# muse2api — khôi phục tự động trong module (không đăng nhập tươi)

Ngày: 2026-10-30. Nền: web2api nhánh `web2api-module-dang-nhap-tu-dong`
commit fb8aa25. Chỉ sửa `modules/muse2api/`, không sửa lõi, không sửa
module khác. Không đăng nhập thật, không dùng key MCP, không dùng token
GitHub, không push, không PR. Patch áp sạch từ fb8aa25 (đã kiểm bằng
`git apply --check` trên bản sao nền sạch, test mới trên bản áp patch:
9 passed).

## Kết luận trước hết: đăng nhập tự động TƯƠI cho muse.ai KHÔNG làm được

- muse.ai đăng nhập qua SSO của Meta, **không có form email/mật khẩu để
  tự điền**. `dang_nhap_tu_dong` cũ đã trả `can_nguoi` vì lý do này và
  được giữ nguyên, không bịa luồng điền mật khẩu cho Meta SSO.
- Protocol của muse2api (`modules/muse2api/protocol.py`) **không có
  refresh_token** (grep toàn module: 0 lần). `fetch_access_token` chỉ là
  `POST /api/auth/check` với cookie còn sống → access_token mới;
  `fetch_session_info` là `GET /api/session` → vm_id. Cookie chết thì
  không có đường nào suy ra token mới, và không được đổi trạng thái tài
  khoản trái phép để giả vờ làm mới.
- chatgpt2api (HEAD d879b03, đọc chỉ, không lấy mã) cũng **không có cơ
  chế nào cho Muse/Meta SSO**: không nhắc tới muse.ai, metaaivm hay Meta
  SSO trong `services/`. Những gì nó có đều gắn với nhà cung cấp khác:
  đổi refresh_token OAuth lấy access_token mới (Antigravity, Codex),
  đăng nhập lại bằng mật khẩu+TOTP qua captcha-solver, tái dùng hồ sơ
  trình duyệt, kiểm phiên Claude bằng sessionKey HTTP. Không áp được
  nguyên xi cho muse.ai, và không được bịa một luồng tương đương.

## Những gì chatgpt2api cho áp được, và đã áp theo cách của muse.ai

| chatgpt2api | Áp cho muse2api như thế nào |
|---|---|
| Khung T0 kiểm phiên → T1 nghỉ-kiểm lại → T2 cứu → T3 kiểm lại | Giữ nguyên khung, nhưng T2 không phải mật khẩu (xem dưới) |
| Tái dùng hồ sơ trình duyệt đã đăng nhập | NV230 (workspace Firefox đã gắn) + NV93 `tai_dung_ho_so` |
| Gặp need_captcha / need_code / need_tap thì dừng, hoãn lượt sau | T2 gặp thử thách → `can_nguoi`, hoãn T2 1800 giây cho khoá đó; T0/T1 vẫn chạy trước ở lần sau nên người đăng nhập tay xong vẫn được nhận ngay |
| Khóa serial, không đăng nhập dồn | Khóa serial riêng của module (`_khoa_tu_dong`, tạo lười) |
| Không có refresh_token thì báo cần người, không tự vượt | Cookie chết + không có hồ sơ/controller → `can_nguoi` kèm hướng dẫn noVNC Meta SSO |

Lưu ý thời gian hoãn: chatgpt2api giữ CAPTCHA Google tới 6 giờ; bản này
giữ 1800 giây như bản sửa module chatgpt-web/gemini-web đã có, vì
muse2api không phải luồng Google — nếu chủ máy muốn 6 giờ thì đổi một
hằng `_captcha_hoan_giay`, xem câu hỏi 3.

## Patch làm gì (chỉ 2 file)

`modules/muse2api/module.py` (+~230 dòng, không sửa lõi, không sửa
module khác):

1. **Hoàn thiện NV230 — kiểm phiên SAU KHI THAY cookie.**
   Trước đây `lam_moi_phien` chỉ kiểm cookie mới TRƯỚC khi thay rồi báo
   thành công. Nay sau khi `_thay_cookie` cập nhật bộ nhớ, nó kiểm lại
   bằng bootstrap trên cookie mới: qua mới tính thành công (kèm
   `khoa_moi`), hỏng thì trả `het_han`/`loi_may_chu` và đánh dấu tài
   khoản không khoẻ — không báo thành công giả khi cookie xoay giữa
   chừng.
2. **`_lam_moi_token_tu_cookie(cookies)`** — làm mới token từ cookie
   còn sống: gọi bootstrap của module qua `_kiem_cookie`, trả ok/het_han.
   Không lưu token, không đổi cookie, không đổi trạng thái tài khoản.
   Đây là giới hạn thật của protocol, không phải refresh_token.
3. **`khoi_phuc_tu_dong(khoa, email, mat_khau, totp, trinh_duyet,
   nghi_t1_giay)`** — thang T0-T3 riêng của module, lõi chỉ chuyển tiếp
   mỏng sẵn có (`app/cong_mcp_cong_cu.py` đã gọi đúng chữ ký này, không
   cần sửa lõi):
   - T0: `lam_moi_phien` (trong đó NV230 đã thử lấy cookie mới từ
     workspace Firefox đã gắn).
   - T1: nghỉ `nghi_t1_giay` rồi kiểm lại (mặc định 0 để test không chờ).
   - T2: trong khóa serial riêng. Khoá không có → `khoa_khong_co`.
     Đang trong cửa sổ hoãn captcha của chính khoá → `captcha_hoan`,
     không gọi trình duyệt lại. Có controller + hồ sơ đã gắn → thử
     `tai_dung_ho_so` (đọc hatch_sess từ hồ sơ đã đăng nhập, KHÔNG
     bao giờ `dien()` mật khẩu/2FA); gặp thử thách → `can_nguoi` +
     đặt hoãn 1800 giây. Không có controller/hồ sơ → `can_nguoi` kèm
     hướng dẫn noVNC Meta SSO (giống tầng b cũ).
   - T3: kiểm lại bằng `lam_moi_phien` trên khoá mới; qua mới tính
     thành công, không qua → `het_han`/`loi_may_chu`.
   - Mật khẩu/TOTP nếu lõi đưa vào: **nhận nhưng không điền, xoá ngay**
     sau khi dùng, không log — điền chúng vào đâu cũng là bịa luồng
     Meta SSO.
   - Tầng (c) vẫn là `tai_khoan_ke()` riêng; hàm này **không tự đổi
     tài khoản âm thầm**, người gọi tự chọn khoá kế.
4. **Ánh xạ email → khoá NV93** (`_tim_khoa_tu_email`): delegate MCP đưa
   tk_id ngoài module, không phải khoá ms- nội bộ. Với tài khoản NV93,
   bản ghi kho riêng đã có email + hatch_sess nên tìm được khoá ms-
   thật qua cookie chứa chính hatch_sess đó. Tài khoản dán cookie cũ
   không lưu email trong module nên không ánh xạ được → vẫn
   `khoa_khong_co`, không đoán tài khoản.

`test/test_web2api_muse2api_khoi_phuc_tu_dong.py` (mới, 9 test, mock
riêng, không Internet, không trình duyệt thật, chuỗi đều giả rõ ràng):
T0 sống; T1 nghỉ rồi sống; T2 không controller → can_nguoi + xoá mật
khẩu/TOTP; T2 tái dùng hồ sơ → T3 thành công, không `dien()`; T2
can_nguoi → hoãn captcha, gọi lại không chạm trình duyệt, xoá trạng
thái thì chạy lại; khoá không có; ánh xạ email NV93 cho tk_id ngoài
module; làm mới token không đổi trạng thái; kiểm lại sau khi thay
cookie hỏng → không báo thành công.

## Test

- Mới: **9 passed**.
- Nhóm liên quan (muse2api + NV90 + NV230 + NV93 + NV103 + test muse2api
  chung): **103 passed, 1 failed**. Failed duy nhất là
  `test_moi_manifest_goi_thieu_rong` (thiếu gói `paho` của module mqtt
  trong venv) — đã kiểm trên nền fb8aa25 chưa sửa cũng failed y hệt,
  **không phải đỏ mới**, không liên quan muse2api.
- Bandit `modules/muse2api`: 2 LOW (B110, có sẵn trên nền, chỉ lệch số
  dòng do thêm docstring) — không thêm lỗi mới.
- Patch: 536 dòng, chỉ 2 file trên, áp sạch từ fb8aa25.

## Token/cookie lấy bằng cách nào — nói thẳng

- **Cookie sống:** kiểm bằng bootstrap, access_token suy ra lại từ
  cookie mỗi lần (không lưu token riêng).
- **Cookie chết, workspace Firefox đã gắn còn đăng nhập:** NV230 đọc
  cookie muse.ai từ hồ sơ đã đóng, kiểm bằng bootstrap, thay qua đường
  cai {giu, them}, rồi kiểm lại sau khi thay (mới thêm).
- **Cookie chết, có controller + hồ sơ đã gắn:** `tai_dung_ho_so` đọc
  hatch_sess từ hồ sơ, thêm tài khoản, rồi T3 kiểm lại bằng bootstrap.
- **Còn lại:** không có đường nào tự lấy được — trả `can_nguoi`, người
  đăng nhập tay qua noVNC rồi bấm «Đã xử lý xong». Đây không phải
  đăng nhập tự động tươi, và báo cáo này không gọi nó như vậy.

## Chưa kiểm thật — phải nói rõ

- Chưa đăng nhập muse.ai thật, chưa gọi muse.ai thật, chưa chạy qua
  MCP thật, chưa thử với workspace Firefox thật hay loa/HA nào.
- Chưa kiểm delegate MCP với tk_id thật của muse2api: ánh xạ email chỉ
  phủ tài khoản NV93; tài khoản dán cookie cũ qua MCP vẫn có thể trả
  `khoa_khong_co` (xem câu hỏi 1).
- Chưa kiểm `tai_dung_ho_so` trên muse.ai thật: nút Google SSO có tồn
  tại hay không vẫn chưa rõ (docstring NV90-C đã ghi), và T2 trong bản
  này dùng đúng hàm đó nên cũng mang giới hạn đó.
- Không kiểm claude-web, grok-web, chatgpt-web trong patch này — đó là
  việc riêng của các subagent song song, theo đúng phạm vi chỉ-muse2api.
