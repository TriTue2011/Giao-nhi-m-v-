# NV276 — THEO DÕI TRÌNH DUYỆT KHI ĐĂNG NHẬP TỰ ĐỘNG BẰNG noVNC (02/11/2026)

## Vấn đề gốc

Ngày 28/10/2026 người dùng bấm «Đăng nhập tự động» rồi «Mở Trình duyệt» thì Workspace báo
«Module lỗi khi liệt kê hồ sơ (ConnectError)»: web2api không với tới noVNC của container
`web2api-may-dang-nhap` (websockify chỉ nghe loopback trong container đó). Bản này sửa đúng chỗ đó.

## Thiết kế đã chọn (mục 2a của brief)

**Chọn phương án (1): module `may-dang-nhap` khai thêm khả năng `trinh_duyet_xem`, tái dùng proxy
`/novnc` hiện có — với một đường lấy vé riêng có step-up.** Lý do:

- Proxy `/novnc` đã có đủ thứ khó: vé một lần 60 giây, phiên 256 bit trong đường dẫn, CSP sandbox,
  ghim đích + kiểm SSRF, thu hồi trước khi đóng. Viết lại (phương án 2) chỉ nhân đôi logic vé.
- Không tái dùng nguyên đường `/mo`: `/mo` tạo/khôi phục một hồ sơ trình duyệt riêng và không có
  step-up; còn noVNC của may-dang-nhap là **một màn hình dùng chung (:99)**, không phải hồ sơ riêng
  theo tài khoản. Vì vậy đường mới `POST /api/trinh-duyet/{module}/xem` chỉ xin đích xem + cấp vé,
  không tạo hồ sơ, không mở trình duyệt mới.
- Mật khẩu VNC: **không đi qua bất kỳ API nào**. x11vnc vẫn bắt mật khẩu; người xem nhập một lần ở
  hộp nhập của noVNC. Mật khẩu chỉ chủ máy biết (đọc trong container dịch vụ, xem README dịch vụ).
  Không làm endpoint hiển thị mật khẩu — đó là bề mặt lộ bí mật mới và cần sửa `src/` ngoài phạm vi
  brief (xem `hoi-nv276.md` câu 2).

## Thay đổi (nền web2api main 66d0a9b, nhánh làm việc `nv276`)

| File | Thay đổi |
|---|---|
| `app/novnc.py` | Đường mới `POST /api/trinh-duyet/{module}/xem`: quản trị + **step-up** (phiên web phải xác nhận lại; Bearer quản trị được miễn như mọi đường chạm bí mật), gọi `module.trinh_duyet_xem_mo()`, ghim đích qua kiểm SSRF, cấp vé một lần như vé `/novnc` cũ, trả `{ho_so, ve, url}`. Hồ sơ ghim chỉ là khoá phiên xem (ID ngẫu nhiên); thu hồi/đóng nó **không** đóng trình duyệt đang đăng nhập của dịch vụ. Mọi `except` đều ghi log kiểu lỗi. |
| `app/kham_pha.py` | Hợp đồng khả năng mới `trinh_duyet_xem: (trinh_duyet_xem_mo,)`, xếp vào nhóm khả năng nguy hiểm (khoá khách `*` không tự có). |
| `modules/may-dang-nhap/module.py` | `trinh_duyet_xem_mo()`: suy host từ `dich_vu_url` đã cấu hình, trả `http://<host>:6080`; không gọi mạng, không dùng khoá dịch vụ, không biết mật khẩu VNC. |
| `modules/may-dang-nhap/manifest.json` | `phien_ban` 0.1.3 → **0.1.4**, `cung_cap` thêm `trinh_duyet_xem`. |
| `dich-vu/may-dang-nhap/supervisord-novnc.conf` | websockify `127.0.0.1:6080` → **`0.0.0.0:6080`** (chỉ trên mạng Docker nội bộ; compose không publish cổng này nên ngoài mạng nội bộ không với tới). x11vnc giữ nguyên `127.0.0.1:5900` + bắt mật khẩu. |
| `dich-vu/may-dang-nhap/README.md` | Cập nhật 3 chỗ: cổng 6080 dùng được từ web2api qua proxy `/novnc`, không publish, mật khẩu đọc bằng `docker exec`. |
| `web/He-thong-AI.dc.html` | Nút **«Theo dõi trực tiếp»** mới (id `k268-theo-doi-truc-tiep`) ở chi tiết tài khoản + dòng chữ đúng brief («Xem trình duyệt đang đăng nhập; gặp CAPTCHA/xác minh thì tự xử lý rồi bấm Đăng nhập tự động lần nữa»). Bấm mở cửa sổ **ngay** trong cú bấm rồi mới xin vé (không bị chặn popup). Tên nút/hàm cố tình tránh chuỗi `novnc` để qua luật C6 (xem dưới). |
| `test/test_nv276_xem_novnc.py` | 13 test mới (viết đỏ trước, xem commit `bc9952a`). |

**Không đụng:** `Dockerfile`, `docker-compose.yml`, `.github/`, `.gitleaks.toml`, `src/solvers/`.
Lõi (`app/`, `web/`) không nhắc tên nhà cung cấp cụ thể; giao diện tìm module theo khả năng
`trinh_duyet_xem`, không theo tên module. Giao diện cũng không chứa chuỗi `novnc` (luật C6:
`test_grep_tu_khoa_trong_app_va_web` chỉ cho phép chuỗi đó trong vài file `app/`) — lần đầu đặt
tên nút `k268-theo-doi-novnc` đã làm test này đỏ, đã đổi sang `k268-theo-doi-truc-tiep` và test
lại xanh (commit `4ae4aa5`).

## Xung đột id đã gặp và cách xử lý

Brief yêu cầu nút «Theo dõi» id `k268-theo-doi`, nhưng id này **đã bị chiếm** trên main 66d0a9b bởi
nút bật/tắt khung xem **ảnh chụp** (commit `a958550` «NV276: bấm Đăng nhập tự động mở trình duyệt
theo dõi…», đổi hướng ở `8e389e7` sang ảnh chụp qua API có khoá, không mở noVNC) và test
`test_nv274_dang_nhap_tay.py` đang assert id đó. Vì vậy bản này **giữ nguyên nút ảnh chụp** và thêm
nút noVNC riêng id **`k268-theo-doi-novnc`** — hai cách xem sống chung, không phá test cũ, không
tạo hai nút cùng id. Host quyết đổi tên/đổi hành vi nút cũ hay không thì xem `hoi-nv276.md` câu 1.

## Vận hành trên máy chủ thật (ngoài repo, điều phối làm)

1. Đặt `CAPTCHA_SOLVER_BAT_NOVNC=1` ở tệp ghi đè cục bộ ngoài repo (không sửa trong repo).
2. Container web2api phải chung mạng Docker nội bộ với container may-dang-nhap (mặc định
   `dich_vu_url` của module đã là tên container trong mạng đó; compose trong repo không khai
   network cho web2api nên cần xác nhận trên máy thật — xem `hoi-nv276.md` câu 3).
3. Người xem nhập mật khẩu VNC một lần ở hộp nhập của noVNC (chủ máy đọc bằng
   `docker exec web2api-may-dang-nhap cat /khoa/mat-khau-vnc`).

## Kiểm thử (đã chạy, số thật)

- Test mới `test/test_nv276_xem_novnc.py`: **13/13 xanh** — cấp vé + URL không lộ mật khẩu VNC,
  vé đổi thành phiên một lần (dùng lại → 401), vé hết hạn → 401, thu hồi hồ sơ → vé mất hiệu lực,
  IDOR (thu hồi hồ sơ module khác không ảnh hưởng vé này), không khoá → 401, khoá khách → 403,
  module không hỗ trợ → 501 / không có → 404, module lỗi → 502 không lộ chi tiết, đích SSRF
  (metadata) → 502 không lộ địa chỉ đích, module thật suy đích từ `dich_vu_url`, giao diện có nút
  riêng + mở cửa sổ ngay trong cú bấm + hàng nút `flex-wrap:wrap`.
- Test liên quan (chạy trước khi máy gặp chặn tạo file, xem dưới): novnc (NV25/NV54) + xem ảnh
  NV276 + đăng nhập tay NV274 + kham_pha: **35 passed, 3 skipped**; may-dang-nhap (NV145b/NV209)
  + NV56: **51 passed**.
- Tập hồi quy nhắm đúng diff (22 file: novnc, kham_pha, may-dang-nhap, trinh-duyet, C6, vnc-xa,
  tab trình duyệt, cookie-sang-module, tinh-nang…): **153 passed, 8 skipped, 1 failed, 225 errors**.
  1 failed duy nhất là luật C6 (nút chứa chuỗi `novnc`) — **đã sửa và chạy lại xanh** (cùng 4 test
  giao diện mới). 225 errors đều là lỗi setup fixture `tmp_path` do máy chặn tạo file (xem dưới),
  không phải assertion của test.
- `bandit -r app modules -lll`: **thoát 0, No issues identified**.
- Quét diff: không token/khoá/mật khẩu/cookie/email thật; IP duy nhất trong test là loopback
  (dịch vụ giả) và dải tài liệu 192.0.2.x. Patch áp sạch lên main 66d0a9b (`git apply --check`).
- Toàn bộ suite `test/` trên nhánh: **đã bắt đầu chạy nhưng dừng ở 37%** vì quá chậm (6000+ test,
  ~1,3%/phút) và máy bắt đầu chặn tạo file; **chưa có số đối chiếu main sạch đầy đủ** — đây là
  điểm còn thiếu duy nhất về kiểm thử, host nên chạy full suite trước khi gộp. File lỗi
  collection có sẵn trên cả main sạch: `test_web2api_dang_nhap_tu_dong.py` (thiếu gói
  `pydantic_settings` trong venv test, không liên quan patch).

## Chưa kiểm được (nói thật)

- **Chưa chạy container thật + trình duyệt thật**: supervisord đổi cổng nghe và luồng noVNC đầu cuối
  (bấm nút → nhập mã truy cập → thấy màn hình :99 đang đăng nhập) chưa được đo trên máy chủ thật.
  Subagent không có trình duyệt trực tiếp nên kiểm 390 px / 1280 px chỉ là kiểm tĩnh
  (`flex-wrap:wrap` của hàng nút + class nút sẵn có), chưa đo bằng Chrome thật.
- Full suite đối chiếu main sạch chưa xong (dừng ở 37%, xem trên).
- **Máy test chặn tạo file chập chờn** trong lúc làm: Python và git thỉnh thoảng báo
  `Operation not permitted` khi tạo file mới (shell vẫn ghi được), cùng dấu hiệu agent giọng gặp
  tối 01–02/11; chặn tự hết sau vài phút rồi lại tái phát. Nó làm chậm việc chạy test/commit cuối
  nhưng không làm sai kết quả test nào (các lỗi setup `tmp_path` đều mang đúng dấu hiệu này).

## Nộp

- Patch: `nv276.patch` (8 file, +308/−8 so với web2api main 66d0a9b), nhánh làm việc local `nv276`
  (6 commit: test đỏ `bc9952a`, đường `/xem` + module `969b63e`, dịch vụ + giao diện `7f936cc`,
  test flex-wrap `4eb50bd`, test IP tài liệu `1ade2ba`, đổi tên qua C6 `4ae4aa5`).
- Outbox: nhánh `muse/nv276-nop` trên TriTue2011/Giao-nhi-m-v- với 3 file
  (`outbox/nv276-bao-cao.md`, `outbox/hoi-nv276.md`, `outbox/nv276.patch`), đã kiểm bằng `ls-remote`
  sau khi đẩy (xem commit ở cuối báo cáo này sau khi đẩy xong).
