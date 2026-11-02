# NV278 — Báo cáo: Module AdGuard Home mới trên web2api

## Tóm tắt

Module mới `adguard` (0.1.0) cho web2api: đọc thống kê DNS chặn quảng cáo
của cả nhà từ AdGuard Home trong LAN và một hành động duy nhất `bao_ve`
bật/tắt bảo vệ (tắt kèm thời gian tự bật lại, mặc định 5 phút). Không sửa
lõi (`app/`), không Dockerfile/docker-compose/.github/.gitleaks.toml.
Chưa kiểm với AdGuard thật — chỉ kiểm với máy chủ AdGuard giả (xem «Kiểm
thử»); chủ kho cần dựng thật và đo lại (câu hỏi ở `hoi-nv278.md`).

## File trong patch (nền web2api main 66d0a9b)

| File | Nội dung |
|---|---|
| `modules/adguard/manifest.json` | id `adguard`, tiền tố `adguard`, `cung_cap: ["thiet_bi"]`, hạng `A`, 6 trường cấu hình |
| `modules/adguard/module.py` | Vòng đời module + kiểm địa chỉ LAN + thực thể + hành động `bao_ve` |
| `modules/adguard/adguard.py` | Client HTTP AdGuard (chỉ thư viện chuẩn `urllib`, Basic auth, proxy tắt) |
| `modules/adguard/README.md` | Tài liệu module |
| `test/test_nv278_adguard.py` | 6 test (máy chủ AdGuard giả + test leo thang quyền ở tầng lõi) |
| `docs/THAM-CHIEU.md` | Tiểu mục module adguard + dòng bảng trạng thái |
| `README.md` | Dòng bảng «Module có sẵn» |

## Thực thể và hành động (chuẩn `thiet_bi`, không route riêng)

- `adguard.tong_truy_van`, `adguard.so_bi_chan`, `adguard.ti_le_chan` (%),
  `adguard.thoi_gian_xu_ly_trung_binh` (giây),
  `adguard.so_bo_loc_dang_bat` — cảm biến chỉ đọc, `rui_ro_mac_dinh: "doc"`.
- `adguard.bao_ve` — công tắc, `rui_ro_mac_dinh: "nguy_hiem"`. Top miền bị
  chặn và top máy khách nằm trong `thuoc_tinh` của thực thể này (giới hạn
  theo `gioi_han_top`, mặc định 10, kẹp 1–50; chuỗi cắt 64 ký tự).
- Hành động `bao_ve`: tham số `bat` (bool, bắt buộc) + `thoi_gian_giay`
  (int 0–86400, chỉ dùng khi `bat=false`; bỏ trống = thời gian tắt mặc
  định đã cấu hình, mặc định 300 giây = 5 phút; `0` = vô thời hạn;
  trần 86400 giây). Khi `bat=true` không gửi `duration`.
- Vì `bao_ve` là `nguy_hiem` theo cấu trúc, nó đi đúng cơ chế quyền/duyệt
  sẵn có của lõi: khách thiếu quyền `thiet_bi:ghi` → 403
  `insufficient_scope`; khách gọi nguy hiểm → 202 vào hàng chờ phê duyệt
  của quản trị; quản trị thiếu `xac_nhan: true` → 409 `can_xac_nhan`;
  nhật ký kiểm toán của lõi ghi ai làm, lúc nào. Module chỉ ghi thêm một
  dòng log trạng thái + thời hạn (không mật khẩu, không header, không địa
  chỉ). Không có hành động ghi nào khác: không sửa bộ lọc, không xoá
  nhật ký.

## API AdGuard Home dùng (đối chiếu tài liệu chính thức v0.107.x)

- `GET /control/status` → `protection_enabled`.
- `GET /control/stats` → `num_dns_queries`, `num_blocked_filtering`,
  `avg_processing_time` (giây), `top_blocked_domains`, `top_clients`
  (dạng mảng object một khoá).
- `GET /control/filtering/status` → đếm `filters[].enabled`.
- `GET /control/clients` → tên máy khách (`auto` + `persistent`); hỏng thì
  giữ IP, không hỏng thống kê.
- `POST /control/protection` → `{"enabled": bool, "duration": ms}`;
  `duration` tính bằng mili-giây; tắt kèm `duration = 0` là vô thời hạn.
- Cố tình KHÔNG dùng `GET /control/querylog`: top list đã có dạng tổng hợp
  trong `/control/stats`; đọc nhật ký thô là không cần thiết và trái yêu
  cầu «không trả nguyên nhật ký truy vấn» của brief.

## An toàn

- **Chỉ LAN, chặt hơn helper của mikrotik-routeros:** `kiem_dia_chi` phân
  giải tên máy và ghim IP đã kiểm (chống DNS rebinding) như mikrotik, rồi
  siết thêm — IP công cộng bị từ chối (chỉ chấp nhận IP riêng RFC1918/ULA);
  loopback chỉ cho phép khi test bật `WEB2API_TEST_CHO_PHEP_LOOPBACK=1`;
  link-local/metadata/không định tuyến bị từ chối qua `_dia_chi_bi_chan`.
  Client tắt proxy hoàn toàn.
- **Mật khẩu:** chỉ nằm trong cấu hình đã lưu của lõi (kho bí mật mã hoá);
  không vào manifest, log, ngoại lệ hay phản hồi. Test kiểm chứng log
  không chứa mật khẩu giả và không chứa header `Authorization`.
- **Lỗi không nuốt (tinh thần test nv45):** mã rõ `sai_dang_nhap` (401/403),
  `mang_loi`, `het_gio` (timeout 10 giây), `loi_may_chu`, `du_lieu_sai`
  (JSON/hình dạng sai), `tham_so_sai`; `cai()` trả thông báo rõ,
  `thuc_the`/`trang_thai` giữ số cũ và gắn mã lỗi khi chưa có số nào.
- **Dữ liệu từ máy chủ là không tin:** bỏ ký tự điều khiển, cắt chuỗi 64
  ký tự, kiểm kiểu từng trường số/bool trước khi dùng, bỏ mục top sai hình.

## Cấu hình

| Trường | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|
| `dia_chi` | Có | — | `host[:cổng]`, cổng mặc định 3000, chỉ LAN |
| `tai_khoan` | Có | — | Tài khoản AdGuard Home |
| `mat_khau` | Có | — | Kiểu `bi_mat`, kho riêng mã hoá của lõi |
| `gioi_han_top` | Không | 10 | Kẹp 1–50 |
| `thoi_gian_tat_mac_dinh_giay` | Không | 300 | Kẹp 30–86400 |
| `chu_ky_giay` | Không | 30 | Chu kỳ làm mới thống kê, kẹp 10–3600 |

Cài: `POST /api/modules/adguard/cai` với `{"cau_hinh": {"dia_chi":
"192.168.1.2:3000", "tai_khoan": "admin", "mat_khau": "<mat-khau>"}}` —
lúc cài module nối + đăng nhập thật để kiểm.

## Kiểm thử

- Mới NV278: **6/6 passed** (`test/test_nv278_adguard.py`): đọc thống kê
  đầy đủ (số, tỉ lệ 51,0%, top list giới hạn/cắt chuỗi, tên máy khách),
  bật/tắt có thời hạn (mặc định 300000 ms, 60000 ms, vô thời hạn 0, bật
  không gửi duration), tham số sai/hành động lạ bị từ chối, mật khẩu sai
  → `sai_dang_nhap` + trạng thái không hợp lệ, mất kết nối → `mang_loi`,
  địa chỉ ngoài LAN bị từ chối (IP công cộng, metadata 169.254.x, loopback
  khi tắt cờ test), và test leo thang quyền ở tầng lõi với module thật nạp
  nóng: không khoá → 401, khoá chỉ `thiet_bi:doc` → 403
  `insufficient_scope`, khoá `thiet_bi:ghi` gọi `bao_ve` → 202 hàng chờ
  (chưa thực thi), quản trị duyệt → thực thi đúng thân POST, quản trị
  thiếu xác nhận → 409 `can_xac_nhan`, quản trị kèm `xac_nhan: true` →
  200 thực thi ngay.
- Liên quan: **67/67 passed** (NV278 + `test_web2api_thiet_bi.py` +
  `test_mikrotik_routeros.py` + `test_web2api_nv279_mikrotik_thuc_the.py`).
- Bandit trên `modules/adguard`: exit 0, không vấn đề.
- Toàn bộ suite: xem mục dưới (chạy sau khi viết báo cáo; cập nhật trước
  khi đẩy nếu số đổi).

## Toàn bộ suite — đọc kèm cảnh báo môi trường

- Nhánh NV278 (chạy đủ, trừ file `test_web2api_dang_nhap_tu_dong.py`
  lỗi thu thập có sẵn — xem dưới): **697 failed / 4568 passed /
  223 skipped / 31 xfailed / 1004 errors, 56 phút**. Con số này KHÔNG
  dùng được làm «patch làm hỏng X test»: cùng đợt chạy, các file không
  liên quan gì tới adguard đỏ hàng loạt ở khâu setup fixture `tmp_path`
  (nguoi_dung 91, mqtt 59, nguon_git 40…) — đúng dấu hiệu khối ghi file
  của Python trên máy này mà agent NV276 cũng gặp cùng ngày (225 errors
  setup `tmp_path`, không phải assertion) trong lúc nhiều agent chạy song
  song. So sánh sạch với main trong cùng điều kiện đã không chạy lại
  được (mỗi lượt ~56 phút, máy đang tranh chấp).
- Bằng chứng có trọng số thay cho so sánh đó:
  - NV278 mới: **6/6**, nhóm liên quan (thiet_bi + mikrotik + nv279 +
    quyen truong hien thi): **70/70** sau mọi lần sửa.
  - Smoke NV184 cho adguard: **skipped** (cần AdGuard thật) — cùng trạng
    thái với mikrotik-routeros và home-assistant khi chạy lẻ; trước khi
    sửa thông báo lỗi, smoke này FAIL vì cụm «Không nối được» không nằm
    trong từ khoá «cần dịch vụ ngoài» của test — đã sửa thành «Không kết
    nối được tới AdGuard» (đúng nghĩa, đúng quy ước của kho).
  - Audit NV187 (khoá không tái nhập): sau sửa, danh sách vi phạm KHÔNG
    còn mục nào của adguard; các mục còn lại (do_tai_nguyen, chatgpt-web,
    mikrotik-routeros, muse2api, antigravity) là có sẵn trên main, không
    do patch này.
  - Test phân loại trường manifest (quyen truong hien thi): **3/3** sau
    khi bỏ `loai_tai_khoan_ten` khỏi manifest adguard (xem dưới).
- Lỗi thu thập có sẵn (không do patch): `test_web2api_dang_nhap_tu_dong.py`
  import `test.gia` thất bại khi chạy từ thư mục repo (agent NV276 cũng
  ghi nhận file này lỗi thu thập vì thiếu gói trong venv) — nên mọi lượt
  suite đều `--ignore` file này, giống cách agent NV283 đã loại test
  auto-login khỏi suite đầy đủ.

## Ba lỗi do chính patch này gây ra, đã sửa trước khi đẩy

1. Manifest adguard khai `loai_tai_khoan_ten` (NV283 nói «thêm vào
   manifest nếu chưa có») nhưng trường này chưa nằm trong
   `app/quyen_module._TRUONG_KHONG_QUYEN` và chưa manifest nào trong kho
   dùng — test phân loại trường đỏ. **Đã bỏ trường khỏi manifest**
   (module thiết bị không cần tên loại tài khoản; `loai_hien_thi` vẫn
   suy từ `kieu_bi_mat` theo hợp đồng NV283). Không sửa lõi để qua test
   — nếu chủ máy muốn trường này trên adguard thì cần thêm vào allowlist
   của lõi (xem `hoi-nv278.md` câu 6).
2. `log.warning` nằm trong `async with self._khoa_lam_moi` — audit NV187
   gắn cờ (lớp tự khoá chết NV185). **Đã chuyển log ra sau khi thả
   khoá** (lưu mã lỗi vào biến cục bộ trước).
3. Thông báo lỗi mạng «Không nối được» không khớp từ khoá skip của smoke
   NV184. **Đã đổi thành «Không kết nối được tới AdGuard»** (xem trên).

## Việc chủ kho phải duyệt / làm khi dựng thật

1. Kiểm module xuất hiện trong `GET /api/modules/thong-bao` và cài được
   qua `POST /api/modules/adguard/cai` với địa chỉ LAN của AdGuard thật.
2. Xác nhận hình dạng JSON thật của `/control/stats` và `/control/status`
   (mẫu đã che) khớp parser — xem `hoi-nv278.md` câu 1.
3. Xác nhận thời gian tắt mặc định 300 giây và trần 86400 giây đúng ý
   (câu 2), và nguồn tên máy khách (câu 3), và cách đặt top list (câu 4).
4. Chưa kiểm với AdGuard thật, chưa kiểm trên container thật / giao diện
   (giao diện không nằm trong brief NV278).
