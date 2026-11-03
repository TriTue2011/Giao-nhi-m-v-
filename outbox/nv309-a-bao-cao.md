# KẾT QUẢ — NV309-a: nối cầu nối trình duyệt thật vào MCP + đường module.dang_nhap (SAI S1)

> Base: web2api main 8ed35ab (đã chứa sửa của điều phối: Grok email mặc định
> đường thẳng, sổ lỗi theo khóa, vòng đời dịch vụ, trần RAM lõi).
> Nhánh nộp: muse/nv309-a — CHỈ nhánh muse/*, không đẩy main, không force-push.
> Bảng đối chiếu: outbox/nv309-doi-chieu.md trên nhánh muse/nv309-doi-chieu
> (134ae25f). Nhiệm vụ gốc: inbox/NV309.md trên Giao main.
> Trạng thái kiểm thật: CHƯA THỬ TRÊN TRÌNH DUYỆT THẬT (xem «Kế hoạch kiểm thật»).

## 1. Vấn đề — hỏng nội tại, không phải «khác c2a nên sai»

Theo đính chính 16:58 ngày 03/11: khác c2a không tự động là sai; mỗi điểm phải
được test chứng minh. S1 qua được tiêu chuẩn đó — nó hỏng nội tại, chứng minh
bằng code + test đỏ, không phải bằng so sánh với c2a:

- `modules/grok-web/module.py::dang_nhap` đọc controller từ hook test
  `_tao_trinh_duyet` (mặc định None); production không có lời gọi
  `dang_ky_trinh_duyet` nào → `_dang_nhap_bang_trinh_duyet` trả `can_nguoi`
  (hoặc `trinh_duyet_none` ở tầng T2) mà chưa từng mở trình duyệt.
- `claude-web` cùng lỗi; `chatgpt-web`/`gemini-web` đã hỏi factory qua
  `_lay_trinh_duyet_module()` nhưng vẫn không nhận controller từ lõi.
- Các đường production bị ảnh hưởng: batch `kieu="truc_tiep"` (app/tuyen.py),
  tài khoản đã lưu, tự đăng nhập lại NV144, MCP `_thu_khoi_phuc_module`
  (chỉ T0/T1 chạy được — hai lần thành công NV275 đều khớp dạng T0).
- UI tài khoản AI KHÔNG ĐỔI (đang đúng, giữ nguyên theo đính chính).

## 2. Cách chọn — lõi cấp controller trước khi gọi (một cách duy nhất)

- Không chọn đăng ký factory ở lifespan: factory không có ngữ cảnh tài khoản
  (không chọn được workspace theo từng tài khoản), và gán factory theo từng
  lượt gọi sẽ đua giữa các lời gọi đồng thời dùng chung một thể hiện module.
- Truyền tham số `trinh_duyet` theo từng lượt gọi — đúng mẫu tầng (b) sẵn có
  (`dang_nhap_tu_dong(..., trinh_duyet=...)`), an toàn đồng thời vì batch chạy
  tuần tự theo tài khoản và mỗi lượt mang controller của riêng nó.
- Module giữ nguyên tiers/quyết định; chỉ nhận controller từ lõi. Không đổi
  ngữ nghĩa challenge → can_nguoi (Q4, chờ chủ máy). Không port solver captcha.
  Các điểm w2a hơn c2a (NV209, NV231, NV271, proxy mọi nhánh, /v1/man-hinh,
  bảo mật dịch vụ) không bị sửa lùi.

## 3. Thay đổi (file đầy đủ — xem patch kèm theo)

- `app/khoi_phuc_phien.py`: `tim_module_trinh_duyet(dang_chay)`,
  `lay_trinh_duyet_cho_tai_khoan(dang_chay, *, ho_so, email)` → (controller,
  ho_so, da_tao_moi), `dong_workspace_moi(dang_chay, ho_so)`.
  Thứ tự: ho_so hợp lệ → tái dùng workspace sẵn (KHÔNG tạo mới, KHÔNG đóng
  sau lượt); không có ho_so mà có email → tạo workspace mới rồi lấy controller.
- 4 module `*-web`: `dang_nhap(..., trinh_duyet=None)`; tham số tường minh
  thắng factory/hook; None → hỏi `_lay_trinh_duyet_module()` như cũ (grok-web
  và claude-web bỏ đọc hook trực tiếp — chính chỗ S1).
- `app/tuyen.py` (batch truc_tiep + tài khoản đã lưu), `app/cong_mcp_cong_cu.py`
  (MCP), `app/kho_tai_khoan.py::thu_dang_nhap_lai` + `app/tu_lam_moi.py`
  (NV144, thêm tham số `dang_chay=None`): cấp controller, bọc
  `phien_dieu_khien_that`, `dong()` cuối lượt, đóng workspace MỚI tạo khi lượt
  kết thúc ở trạng thái cuối (KHÔNG đóng khi can_nguoi — người vẫn hoàn tất
  qua noVNC; KHÔNG BAO GIỜ đóng workspace sẵn có, ví dụ hồ sơ Google thật).
  Truyền `trinh_duyet` chỉ khi module nhận tham số (kiểm signature, mẫu cũ ở MCP).
- Quy tắc riêng từng đường (đã ghi trong code):
  - Batch: đường cookie không cần trình duyệt; đường google chỉ tái dùng hồ sơ
    sẵn có (hồ sơ mới không có phiên Google nên không thể tái dùng); không lấy
    được controller: lõi CHỈ CẤP khi có, KHÔNG BAO GIỜ chặn lời gọi khi
    không có (xem «Hồi quy đã sửa» ở §4c — bản đầu chặn sớm bằng
    `loi_module` đã phá hợp đồng module-tự-quyết và đã bị gỡ).
  - Google-cach qua kho module (module tự quyết cach từ kho riêng) vẫn là giới
    hạn đã biết: workspace mới không có phiên Google nên lượt đó vẫn hỏng như
    cũ, không sửa lùi; đường đúng cho tài khoản Google là đường đã lưu (đọc
    ho_so từ bản ghi).
- `app/tai_khoan_hang_loat.py`: ghi chú hợp đồng `KetQuaDangNhap` về tham số
  `trinh_duyet` tuỳ chọn.

## 4. Test — đỏ-trước-xanh, khẳng định hành vi đúng (không chỉ «giống c2a»)

- Mới: `test/test_nv309_a.py` — 11 test, xanh 11/11 (cả trong suite đầy đủ).
  - Module grok-web: mật khẩu + controller truyền vào → thành công và
    `mo_trang` gọi đúng URL đăng nhập (đỏ trước: TypeError);
    factory đã đăng ký → được hỏi (đỏ trước: can_nguoi);
    tham số tường minh thắng factory; không controller nào → can_nguoi (giữ
    fail-closed, xanh trước và sau).
  - Grok đường Google: tái dùng hồ sơ → trả cookie phiên chứa `sso` (chứng
    minh session ở mức test; probe thử thách HTTP được stub — không phải phần
    chứng minh của test này).
  - Lõi: helper — ho_so sẵn có → tái dùng (không tạo mới); email → tạo
    workspace mới (created=True); không có đường nào → (None, "", False).
  - MCP: `_thu_khoi_phuc_module` truyền controller thật vào `khoi_phuc_tu_dong`.
  - NV144: có dang_chay → truyền controller; không có dang_chay → lời gọi cũ,
    module kiểu cũ vẫn chạy (tương thích ngược).

## 4b. Chứng minh theo từng loại — luật thứ tự 17:52 ngày 03/11

Luật: làm phần đăng nhập trước, xong mỗi loại = lấy được cookie/session;
tuần tự từng loại một, Grok trước (ca lỗi nêu đầu trong NV309 + NV293 thử
Grok trước rồi mới Claude); trong mỗi loại, xong hẳn 1 cách mới sang cách tiếp
theo. Áp vào mảnh này:

- **Grok — XONG Ở MỨC TEST, cả 2 cách**: email-direct (mật khẩu → thành công
  + cookie) và Google (tái dùng hồ sơ → cookie phiên) đều đã chứng minh bằng
  test tự động ở đây. Kiểm thật MCP → noVNC thao tác tay (§5) chờ vòng sau gộp
  (cần tài khoản cho phép + bản dựng mới).
- **Claude — CHƯA TỚI LƯỢT**: chỉ mới nối tham số `trinh_duyet` (cùng mẫu
  1 dòng như Grok, không sửa logic); chưa có test chứng minh session riêng
  cho Claude — tới lượt sau Grok, theo thứ tự NV293.
- **ChatGPT, Gemini — CHƯA TỚI LƯỢT**: như Claude (đã nối tham số, chưa chứng
  minh session riêng từng loại).
- Hạ tầng lõi (helper + 4 đường lõi) là đường ống chung, không phải «loại» —
  chứng minh của nó là test helper/MCP/NV144 ở §4, không nhận là đã chứng minh
  session từng loại.
- Liên quan hiện có: 279 test xanh (grok/chatgpt/gemini/claude-web, NV92 P3,
  NV88 chatgpt, NV300 cach, MCP, NV91 tu_lam_moi).
- Toàn suite lần 3 (trước các sửa §4c): 6419 test, 192 hỏng — NHƯNG toàn bộ
  192 đều ở file không liên quan (a) (lớn nhất: mqtt 59, sao_luu 40+10,
  da_phuong_thuc 17…); 11 test nv309_a đều xanh trong suite đầy đủ.
  Trừ 8 file muse2api lỗi thu thập SẴN CÓ trên base sạch do thiếu module
  `google` trong venv (đã kiểm bằng worktree ở 8ed35ab, không phải do patch).
- Đối chiếu sau sửa §4c (mẫu NV306 — so theo tên, không so tổng thô):
  chạy 28 file từng hỏng + 10 file liên quan trên cây (a) sau sửa và trên
  base sạch: cây (a) 175 hỏng, base 175 hỏng, TRÙNG TÊN 100% (chỉ-(a): 0,
  chỉ-base: 0); 10 file liên quan 0 hỏng. Kết luận: (a) sau sửa KHÔNG gây
  hồi quy nào so với base; 175 hỏng còn lại là hỏng sẵn có trên base.

## 4c. Hồi quy đã sửa trong quá trình kiểm chứng (ghi rõ, không giấu)

So sánh lần 3 với base phát hiện 17 test chỉ hỏng trên cây (a) — điều tra
chứng minh là hồi quy thật của (a), không phải flake (base chạy riêng 10
file đó: 237 xanh; cây (a) chạy riêng: 15 hỏng, 2 flake):

1. CHẶN SỚM SAI Ở BATCH (chức năng): bản đầu của (a) trả `loi_module` ngay
   khi lõi không lấy được controller cho đường mật khẩu — phá hợp đồng cũ
   (module tự quyết có cần trình duyệt không; module giả/không cần trình
   duyệt vẫn phải chạy). Hỏng: NV88 (batch xong 1 thay vì 2), NV119, NV283,
   toàn bộ NV122 (luồng mã email không bao giờ tới module). SỬA: gỡ chặn
   sớm — lõi chỉ cấp khi có, module quyết; kiểm lại 22 xanh (NV88 + NV119
   + NV283 + NV122).
2. LUẬT TĨNH CỦA LÕI (không phải nới test): (a) thêm literal `google` vào
   app/ (nhánh `dong.loai == "google"`, `ho_so_google`, comment) → vi phạm
   doc_lap (trần 0) + tinh_nang (lõi không mang đặc thù nhà cung cấp); thêm
   `noVNC` vào comment ngoài file cho phép → vi phạm C6. SỬA: batch viết
   lại theo nghĩa chung (cookie → không cấp; mật khẩu/đăng nhập lại → tạo
   mới theo email; bản ghi CÓ hồ sơ đã lưu → tái dùng; không nêu tên nhà
   cung cấp nào — dùng hằng `kho_tai_khoan.TRUONG_HO_SO` thay cho literal
   trường, giá trị hằng đọc từ JSON nên không thêm literal mới); comment
   `Google` → `SSO`, `noVNC` → `bằng tay`. Ngữ nghĩa với mọi loại đã biết
   không đổi (loại lạ có hồ sơ → tái dùng, module vẫn tự quyết).
3. NV45 (nuốt lỗi): 4 điểm `td.dong()` best-effort mới ở finally (MCP,
   NV144, đã lưu, batch) được thêm vào danh sách đã kiểm toán kèm lý do
   (lỗi đóng không được làm hỏng kết quả đăng nhập đã có) — đúng cơ chế
   của test, không phải nới luật.
- Sau cả 3 sửa: 248 xanh (10 file từng hỏng + test mới) trong 52.61 giây;
  đối chiếu 38 file như trên: trùng base 100%.

## 5. Kế hoạch kiểm thật — theo thứ tự MCP trước, noVNC THAO TÁC TAY sau

Chưa kiểm thật ở đây (không có tài khoản cho phép + bản dựng mới trên máy này;
không nhận đã kiểm thật khi chưa kiểm). Theo phương pháp 17:38 ngày 03/11,
noVNC KHÔNG chỉ để xem thụ động — chủ máy tự bấm/gõ bằng tay để CHỌN ĐÚNG Ô
đăng nhập, rồi từ đó mới xác định automation phải bấm ô nào. Sau khi điều phối
gộp + dựng lại, vòng lặp với điều phối/chủ máy kiểm theo thứ tự:

1. **MCP trước**: chạy lượt đăng nhập thật qua MCP cho một tài khoản đã cho
   phép (mật khẩu + Google tái dùng hồ sơ), xác nhận tầng T2 chạy được qua MCP
   (trước đây chỉ T0/T1 chạy được) và kết quả trả về đúng.
2. **noVNC thao tác tay sau**: chủ máy mở noVNC, tự bấm/gõ bằng tay để chọn
   đúng ô đăng nhập và xác nhận từng ô dưới đây (không chỉ theo dõi). Đồng
   thời kiểm: cửa sổ trình duyệt có mở đúng workspace không, và khi lượt báo
   can_nguoi thì cửa sổ có còn mở cho người hoàn tất không (workspace mới tạo
   chỉ đóng ở trạng thái cuối, không đóng khi can_nguoi).
3. Kiểm thêm: batch truc_tiep mật khẩu, tài khoản đã lưu, NV144 tự đăng nhập
   lại — mỗi đường một lượt thật, đối chiếu mã lỗi (khi không có dịch vụ
   trình duyệt, module tự quyết như cũ — lõi không chặn sớm).

### 5.1. Các ô đăng nhập CHƯA được xác nhận bằng tay qua noVNC

Mảnh này KHÔNG thêm/sửa selector nào — nó chỉ nối controller để các đường vốn
đã có code mới chạy được. Vì vậy mọi selector dưới đây là code sẵn có, và test
controller giả ở đây CHỈ chứng minh đường ống (plumbing), KHÔNG chứng minh
selector thật đúng. Từng ô cần chủ máy xác nhận bằng tay qua noVNC ở vòng kiểm
thật (sau gộp + dựng lại; cơ chế xem noVNC dùng mật khẩu NV305 sau khi triển
khai — agent không dùng, không sao chép bất kỳ mã nào người dùng đã gửi):

- Grok đường trực tiếp, bước email: nút **Tiếp tục** — NV300 bổ sung đã ghi
  «bộ điều khiển trình duyệt thật phải map khóa logic `tiep_tuc` sang nút Tiếp
  tục»; mapping này CHƯA được xác nhận bằng tay, phải chọn đúng nút bằng tay
  qua noVNC trước khi coi là xong.
- Grok đường trực tiếp: ô email, ô mật khẩu, nút gửi form đăng nhập.
- Grok đường Google: nút **«Sign in with Google»** (`_BO_CHON_GOOGLE` trong
  module) — cần chọn đúng nút bằng tay qua noVNC.
- Tương tự ở chatgpt-web, gemini-web, claude-web: ô email/mật khẩu và nút
  Google của từng module (selector sẵn có của module, chưa xác nhận bằng tay).
- Không ô nào trong danh sách trên được coi là «đã xác nhận» cho tới khi chủ
  máy thao tác tay qua noVNC ở vòng kiểm thật.

## 6. Câu hỏi chủ máy trong bảng (ghi lại, KHÔNG đoán đáp án)

- Q1: lịch nền giữ BẬT mặc định 1800 giây hay học c2a TẮT mặc định + 3 giờ?
- Q2: thứ tự ưu tiên tài khoản có cấu hình được không? (mảnh (d) đang chờ Q2.)
- Q3: sau lượt MCP thành công có đóng thật workspace không (hiện chỉ đóng
  controller, giữ workspace để tái dùng)?
- Q4: gặp challenge thì giữ «challenge → can_nguoi» hay học c2a «cf_chan ≠ het,
  vẫn dùng cookie cũ»? (Mảnh này KHÔNG đổi ngữ nghĩa đó.)
- Mảnh (d) (xoay vòng theo thứ tự ưu tiên + thử lại 1 lần qua làm mới, SAI S4)
  vẫn đang chờ Q2 — không làm trong lượt này, không tự đoán thiết kế.

## 7. Thứ tự gộp

(a) → (b) → (c). Mỗi mảnh một nhánh riêng trên cùng base 8ed35ab (không xếp
chồng); (c) có thể chạm cùng file module ở hàm khác nên gộp sau (a).
