# NV281 — KHOÁ TẠO Ở «BẢO MẬT & NGƯỜI DÙNG» (MỘT NƠI DUY NHẤT)

## Tóm tắt

Khoá của module nay CHỈ tạo/dán/xoá ở Hệ thống → Bảo mật & người dùng, mục mới
«Khoá của module». Nút «Thêm khoá» trong bảng chi tiết Module đã bỏ, thay bằng liên
kết tới neo `#khoa-module-<id>` ở trang Bảo mật. Sau khi lưu khoá, module tự chạy
không cần cài lại (tái dùng đúng đường `POST /api/modules/{id}/cai` hiện có). Xoá
khoá đưa module về «cần khoá» mà không gỡ mã.

Nền: web2api main `66d0a9b` (cùng nền với NV283/NV285). Không đẩy main, chỉ nộp
nhánh `muse/nv281` lên outbox Giao.

## Thiết kế ngắn (mục a của brief)

Ba thứ hay bị gọi chung là «khoá», phân loại rõ:

1. **Khoá khách gọi /v1** — đã có ở trang Bảo mật (tạo khoá khách, phạm vi theo
   tính năng, hiện đúng một lần khi tạo). Không đổi.
2. **Bí mật của MODULE** — khoá API/token nhà cung cấp, khoá Integration của dịch
   vụ nội bộ — đây là thứ module «chờ khoá» cần, và là đối tượng của NV281: nay
   chỉ tạo ở mục «Khoá của module» trong trang Bảo mật.
3. **Tài khoản đăng nhập AI** — giữ ở AI → Tài khoản, không đổi. Ngoại lệ duy
   nhất của `K.noiThemKhoa`: module thuộc AI → Tài khoản cần ĐĂNG NHẬP (không
   phải khoá) vẫn trỏ về `He-thong-AI.dc.html#tk-<id>`.

Quy tắc «hiện đúng một lần khi tạo» được hiểu theo đúng cơ chế hiện có: khoá
khách tạo mới vẫn hiện một lần như cũ; còn bí mật module do quản trị DÁN vào thì
không bao giờ được trả lại nguyên văn qua bất kỳ API đọc nào — chỉ hiện dạng che
(`che()` của kho) — chặt hơn «hiện một lần», và đúng câu thứ hai của brief
(«không bao giờ trả lại nguyên văn qua API đọc, không vào log/phản hồi lỗi»).
Giá trị vừa dán được xoá khỏi state trang ngay sau khi lưu (cơ chế `K.cauHinh`
hiện có: đổi `lan` để dựng ô mới rỗng).

## Thay đổi

### Backend — route mới duy nhất

- `DELETE /api/modules/{id}/khoa` (`app/tuyen.py`, dependencies QT = quản trị,
  CSRF như các đường ghi khác): dừng thể hiện đang chạy (nếu có) bằng
  `SoModule._dung_an_toan` rồi bỏ khỏi `dang_chay`, sau đó dùng đúng hàm kho hiện
  có `kho.xoa_cai_dat` (xoá mục `modules.json` + tệp bí mật). Module quay về
  «cần khoá»; mã vẫn nằm trên đĩa (catalog còn) nên dán khoá mới là chạy lại.
  Phản hồi chỉ `{ok, id, da_xoa}` — không bao giờ chứa bí mật. Ghi nhật ký kênh
  `quan_tri` (chỉ id, không giá trị). Module chưa cài → 404; module từ xa (khoá
  không nằm trong kho bí mật cục bộ) → 400 `module_tu_xa`.
- Không viết cơ chế lưu bí mật mới: đường lưu vẫn là `POST /api/modules/{id}/cai`
  hiện có (đọc-ghép-lưu trong khoá sổ, bí mật ghi trước vào `bi_mat/` rồi mới
  ghi `modules.json`, thể hiện phục vụ dựng lại và cho vào `dang_chay`).

### Giao diện

- `web/khung.js` — `K.noiThemKhoa`: module cần khoá (không thuộc AI → Tài
  khoản) nay trả `{tab: 'bao_mat', href: 'He-thong-Bao-mat.dc.html#khoa-module-<id>'}`.
  Thanh trạng thái «Chờ khoá» (khung nav), bảng chi tiết và Studio đều dùng
  chung hàm này nên tự đổi theo, không sửa riêng từng chỗ gọi.
- `web/He-thong.dc.html` — bỏ nút `#nut-them-khoa` và trường `themKhoa`/
  `coNutThemKhoa`; module chờ khoá luôn hiện liên kết `#lk-them-khoa` tới neo
  Bảo mật (hoặc tới trang Tài khoản nếu thuộc AI → Tài khoản). Ngoài nút/liên
  kết này, bảng chi tiết Module không sửa gì (phần NV280 của agy).
- `web/He-thong-Bao-mat.dc.html` — mục mới «Khoá của module» (chỉ quản trị, luôn
  mở để neo tới đúng khối; trang tải bất đồng bộ nên có `cuộnTớiNeoKhoaModule()`
  nhảy lại tới neo sau khi tải xong):
  - Nguồn dữ liệu: `K.taiTinhNang()` + `GET /api/modules/{id}/cau-hinh` cho từng
    ứng viên; tiêu chí liệt kê = module đã cài, không phải từ xa, `noiThemKhoa`
    trỏ sang Bảo mật, và có ít nhất một trường `bi_mat`/`danh_sach_bi_mat`.
  - Hai nhóm: «Cần khoá» (chưa liên kết, kèm huy hiệu «Đã có khoá lưu · chưa
    liên kết» nếu đã có bí mật lưu mà chưa liên kết) và «Đã liên kết» (đang
    chạy, xoá khoá sẽ dừng module và đưa về «Cần khoá»).
  - Mỗi khối tái dùng nguyên form `K.cauHinh.vm` (ô dán theo trường đã khai,
    trạng thái «đã có / chưa có» từ giá trị che, nút «Kiểm tra và lưu» qua
    `/cai` hiện có). Lưu xong form tự tải lại và danh sách tự làm mới → module
    đổi nhóm ngay, không cần cài lại.
  - Xoá khoá: nút «Xoá khoá» xác nhận hai lần (theo mẫu thu hồi khoá khách),
    gọi `DELETE /api/modules/{id}/khoa`, rồi tải lại danh sách.
- `docs/THAM-CHIEU.md` — mục giao diện + mục bảo mật (dòng «Khoá của module»
  và hàng bảng trang Bảo mật).

### Test viết lại (theo file điều phối: «viết lại các test NV280 buộc phải bỏ»)

- `test/test_web2api_giao_dien.py::test_them_khoa_tren_o_module_khong_co_tab_tai_khoan_mo_bang_chi_tiet`
  — đây là test duy nhất khẳng định hành vi cũ (nút «Thêm khoá» mở form ngay
  trong bảng chi tiết). Viết lại theo NV281: bảng chi tiết không còn nút, chỉ
  còn liên kết `#lk-them-khoa` tới `He-thong-Bao-mat.dc.html#khoa-module-app-khoa`;
  bấm liên kết phải mở được khối khoá của đúng module ở trang Bảo mật.
- Lưu ý: nhánh `agy/nv280-module-gon` không tồn tại trên remote tại thời điểm
  làm (đã kiểm `git ls-remote` cả web2api lẫn Giao — đều trống), nên không đối
  chiếu được diff NV280 thật và không xác định được test NV280 gốc nào khác đã
  bị bỏ; test viết lại ở trên là test bị ảnh hưởng trực tiếp bởi thay đổi
  `noiThemKhoa` trong NV281. Xem `hoi-nv281.md` câu 1.

## Kết quả kiểm (đo thật, không ước)

- Test mới `test/test_nv281_khoa_module.py`: **6/6 xanh** (lõi thật, module giả,
  không Internet): không khoá quản trị → 401/403 (không khoá → 401; khoá sai →
  401; khoá khách hợp lệ không phải quản trị → 403 cho cả đọc cấu hình và xoá);
  dán khoá → module vào `dang_chay` (tự chạy, không cài lại); khoá không lộ qua
  `/cau-hinh`, `/api/modules`, `/api/tinh-nang`; xoá khoá → rời `dang_chay`,
  tệp bí mật + mục `modules.json` bị xoá, catalog còn (không bị gỡ mã); xoá
  module lạ → 404; xoá khi chưa có khoá lưu → 200 `da_xoa: false`, không hỏng.
- Test liên quan: `test_web2api_dc_lite.py`, `test_web2api_dc_cau_truc.py`,
  `test_web2api_bao_mat_hai_tab.py`, `test_web2api_bao_mat_thu_gon.py` +
  test mới: **18 passed, 23 skipped** (skipped là các ca trình duyệt, xem dưới).
- `bandit -r app modules -lll`: thoát 0 (High: 0).
- Quét diff: không có token/mật khẩu/cookie/email thật (khoá trong test mới là
  giá trị giả theo mẫu các test khác, ví dụ `khoa-qt-nv281-…`).
- Toàn bộ suite: KHÔNG có số liệu cuối đáng tin — xem phần «Chưa kiểm» (lý do
  môi trường, không phải code). KHÔNG được suy ra «toàn suite xanh» từ báo cáo
  này.

## Thời gian chuyển (đo bằng test)

Dán khoá qua `/cai` → module vào `dang_chay` ngay trong cùng một lời gọi (không
có độ trễ nền nào thêm); giao diện tải lại danh sách sau khi lưu xong nên nhóm
«Cần khoá» → «Đã liên kết» đổi trong cùng một lần tải lại trang mục. Xoá khoá →
`dang_chay` bỏ ngay trong cùng lời gọi DELETE.

## Bảo mật

- Mọi đường mới/cũ liên quan đều qua dependencies QT (chỉ quản trị); khoá khách
  → 403, không khoá/khoá sai → 401 (đo thực tế; brief nghiệm thu ghi «không
  khoá → 401, quyền sai → 403» — với khoá sai hoàn toàn, lõi trả 401
  `invalid_api_key`, còn 403 là cho khoá hợp lệ nhưng không phải quản trị).
- Không đường nào trả bí mật nguyên văn; phản hồi DELETE chỉ có id + cờ; nhật
  ký chỉ ghi id module, không giá trị. CSRF: route DELETE dùng cùng cơ chế với
  các đường ghi khác (cookie phiên cần `X-CSRF-Token` qua `K.goi`).
- Handler mới không nuốt lỗi âm thầm: lỗi dừng thể hiện được `_dung_an_toan`
  ghi log (theo kiểm nv45); lỗi xoá ở giao diện hiện thành thông báo, không im.
- IDOR: khoá khách (không phải quản trị) bị 403 trước khi tới handler, nên
  không đọc/xoá được khoá của bất kỳ module nào; id module lạ → 404.

## Chưa kiểm (nói thật)

- Test trình duyệt viết lại CHƯA chạy được ở đây: máy này không có Chrome thật
  (`/usr/bin/google-chrome` không tồn tại; `/opt/meta-chromium/chrome` từ chối
  mở cổng DevTools — báo lỗi «Hatch WebGL domain policy is required»). Các test
  trình duyệt vì vậy skip/fail ở fixture, không phải do code. Cần chạy lại trên
  máy có Chrome thật (đặc biệt test viết lại + test form Bảo mật 390 px).
- Ảnh chụp trang Bảo mật điện thoại 390 px và máy tính theo brief CHƯA chụp
  được vì cùng lý do trên (không có trình duyệt thật). Không bịa ảnh.
- Chưa kiểm với module thật / trên container thật; chưa kiểm giao diện NV282
  (Claude làm) đọc neo này.
- Toàn bộ suite so với main sạch: KHÔNG đối chiếu được trong lượt này, vì hai
  lý do môi trường dồn lại: (1) `/tmp` (tmpfs 512 MB) đầy 99% do các agent song
  song — các test cần thư mục tạm chết hàng loạt (35 failed + 100 errors ở
  subset đầu, 1 F trong 6% đầu của full suite, đều là lỗi tạo thư mục tạm,
  không liên quan code NV281); (2) từ ~11:45 UTC, mọi process con qua exec đều
  bị chặn ghi file (write → EPERM; chỉ bash builtin và tool ghi file trực
  tiếp còn ghi được) nên không chạy lại test và không git commit/push được
  nữa. Vì vậy: **outbox đã chuẩn bị xong nhưng CHƯA commit, CHƯA push** — xem
  mục «Việc còn lại cho parent agent» ở cuối.
- Patch đã kiểm áp sạch lên main 66d0a9b và test mới 6/6 xanh từ chính patch
  đó (kiểm trước khi chặn ghi xảy ra).

## Việc còn lại cho parent agent (làm ở phiên khác, nơi exec/git còn ghi được)

1. Kiểm lại 3 file đã stage trong `~/workspace/nv281/giao` (nhánh `muse/nv281`,
   nền `addba159`): `outbox/nv281-bao-cao.md`, `outbox/hoi-nv281.md`,
   `outbox/nv281.patch` (769 dòng thêm, đã kiểm bằng `git diff --cached --stat`).
2. Commit với đúng message 3 câu + đoạn «Bảo mật» đã dùng cho các commit web2api
   (xem commit trong `~/workspace/nv281/repo`, nhánh `nv281-lam-viec`).
3. Chỉ push nhánh `muse/nv281`, không bao giờ push main; kiểm bằng
   `git ls-remote` như các lần trước.
4. Trước hoặc sau khi push, chạy lại trên máy sạch: test trình duyệt viết lại
   (cần Chrome thật), ảnh 390 px, và đối chiếu toàn suite nhánh vs main sạch
   (lưu ý đặt TMPDIR sang workspace vì `/tmp` tmpfs 512 MB dễ đầy).

## Việc chủ kho phải duyệt

1. Nhánh NV280 không có trên remote — khớp neo `#khoa-module-<id>` đã theo đúng
   spec trong file điều phối; nếu agy dùng neo khác, cần đối chiếu (xem hoi).
2. Form cấu hình trong bảng chi tiết Module vẫn còn (để sửa cấu hình thường và
   khoá của module ĐÃ liên kết) — nếu chủ kho muốn «một nơi duy nhất» tuyệt đối
   (kể cả sửa khoá của module đã liên kết cũng chỉ ở Bảo mật), cần quyết riêng:
   form đó là form chung `K.cauHinh` dùng cả ở trang AI, nên việc tách nó khỏi
   bảng chi tiết là một bước riêng, không làm trong NV281 để khỏi chạm phần
   NV280 (xem hoi câu 2).
3. Module từ xa (`tu_xa`) không vào danh sách «Khoá của module» và DELETE trả
   400 `module_tu_xa` — khoá của chúng không nằm trong kho bí mật cục bộ.
