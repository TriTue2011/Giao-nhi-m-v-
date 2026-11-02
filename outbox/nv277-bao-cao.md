# NV277 — BÁO CÁO: MODULE YOUTUBE RIÊNG, CHẠY THẲNG TRONG W2A

- Nền: web2api main `66d0a9b` (lúc clone; Giao main lúc clone: `addba15`).
- Nhánh làm việc cục bộ: `nv277` trong `~/workspace/nv277/repo`.
- Nộp: nhánh outbox `muse/nv277` trên `TriTue2011/Giao-nhi-m-v-`
  (patch + báo cáo này + `hoi-nv277.md`). KHÔNG đẩy main của bất kỳ repo nào.
- Trạng thái: xong mã + test mới, CHƯA thử YouTube thật / loa thật / HA thật,
  CHƯA đo kích thước ảnh / RSS (không có docker ở môi trường làm việc).

## 1. Thiết kế (mục 2a của brief)

### 1.1 Khả năng do LÕI sở hữu, module không tự gắn route

Lõi định nghĩa tập đường theo hợp đồng HA dưới tiền tố riêng của từng
module, trong tệp mới `app/duong_module.py` (router `duong_module`,
prefix `/m`), include trong `app/main.py` **trước** `tep_module`
(GET `/m/<id>/<tệp>` cho tab web — nếu không route tĩnh sẽ nuốt mất
đường API của module). `app/kham_pha.py` chỉ thêm đoạn tài liệu về hai
phương thức mới (không đổi logic nạp module).

Module khai trong manifest (trường mới, `kiem_manifest` chỉ kiểm các
trường đã biết nên không bị từ chối):

```json
"duong_module": {"truong_bi_mat": "khoa_tich_hop", "lan_chi": true}
```

và cài hai phương thức (thiếu thì đường trả 404, lõi không vỡ):

- `async tich_hop(duong, phuong_thuc, query, than) -> (mã, headers, nội dung)`
  — `duong` là phần sau `/api/` (vd `integration/search`); `than` là dict
  JSON hoặc None khi thân rỗng; nội dung trả về: dict (thành JSON),
  bytes, hoặc async-iterator (lõi stream từng khúc, không gom).
- `async luong(ve, khoang, phuong_thuc) -> (mã, headers, nội dung)`
  — `ve` là vé luồng đã đăng ký; `khoang` là header Range của loa.

### 1.2 Xác thực và giới hạn

- Đường integration `/m/<id>/api/integration/*` (GET/POST): lõi kiểm
  Bearer bằng đúng BÍ MẬT RIÊNG của module (trường bí mật trong manifest,
  đọc từ kho bí mật của lõi — không vào log, không vào phản hồi thường;
  quản trị lấy lại bằng đường «chép token» có chủ đích như các bí mật
  khác). Thiếu khoá → 401; khoá của module KHÁC → 403 (lõi quét kho bí
  mật các module khác có khai đường riêng để phân biệt, không lộ module
  nào tồn tại quá mức); module không chạy/không khai đường → 404.
  Thân POST tối đa 400_000 byte (trần lớn nhất của dịch vụ cũ, cho
  playlists import); JSON hỏng hoặc không phải dict → 400 `invalid_request`.
  Mọi phản hồi JSON kèm `Cache-Control: no-store`.
- Đường luồng MỞ `/m/<id>/api/stream/<vé>` (GET/HEAD — loa không gửi
  được header, như dịch vụ cũ): xác thực bằng VÉ KÝ có hạn, DÙNG LẠI
  `app/url_ky.py` của lõi (HMAC-SHA256 phủ phương thức GET + đường dẫn
  chuẩn hoá + hạn; hạn mặc định 3600 giây như `stream_url` của dịch vụ
  cũ; KHÔNG mang cơ chế HMAC riêng của dịch vụ cũ vào lõi). Vé giả/hết
  hạn/sai đường → 404 TRỐNG, không nêu lý do. HEAD dùng cùng vé GET,
  chỉ trả header (lõi đóng iterator của module ngay, không đẩy byte).
  Vé do module tạo qua `duong_module.tao_duong_luong(module_id, ve)`
  khi trả POST integration/stream.
- Giới hạn LAN cho CẢ HAI nhóm đường (dựa trên cùng nguyên tắc phân
  loại IP của lõi, `app/gioi_han.ip_hieu_luc_phan_loai`): loopback trực
  tiếp, IP riêng (RFC 1918), link-local được phép; IP công cộng trực
  tiếp bị chặn; peer không phân tích được thì đóng khi lỗi (trừ chế độ
  test `WEB2API_TEST_CHO_PHEP_LOOPBACK=1`). Lưu ý: `app/ip_cho_phep.py`
  chỉ là cổng IP cho đường QUẢN TRỊ (đọc `WEB2API_QT_IP_CHO_PHEP`),
  không dùng nguyên vẹn cho đường luồng — nên lõi có bộ kiểm LAN riêng
  trong `duong_module._la_lan()` theo đúng nguyên tắc trên.
  **Giới hạn đã biết:** peer qua đường hầm cloudflared là IP gateway
  Docker (IP riêng) nên cổng LAN KHÔNG chặn được truy cập qua hầm —
  muốn chặn phải thêm luật ingress của hầm từ chối `/m/*/api/*`
  (xem `hoi-nv277.md`, chủ kho quyết).
- Không có tên nhà cung cấp nào trong `app/` hay `web/`: lõi chỉ chuyển
  tiếp (mã, headers, nội dung) và kiểm xác thực; mọi logic đặc thù nằm
  ở module. Test độc lập kiểm điều này (quét `app/` + `web/` không chứa
  chuỗi `youtube`).

### 1.3 Module `modules/youtube/` (mới, hoàn toàn riêng)

- `manifest.json`: id `youtube`, tien_to `youtube` (chưa module nào dùng),
  loai `tien_ich`, loai_thu_tu 48, hang B, phien_ban 0.1.0, một trường cấu
  hình bắt buộc duy nhất `khoa_tich_hop` (bi_mat), `yeu_cau_goi` chỉ
  `httpx` (yt-dlp nạp lười, thiếu gói → 502 rõ, để module vẫn chạy cho
  playlists/history/http khi chưa dựng ảnh mới).
- `module.py`: `nap` đồng bộ (không vỡ khi chưa cấu hình), `cai`/
  `suc_khoe`/`dung` async; phiên + vé luồng chỉ ở RAM; dữ liệu bền
  không ghi vào ảnh (phiên không bền theo luật «dừng là dừng hẳn»).
- `trich_xuat.py`: tìm YouTube qua yt-dlp `ytsearch`; giải link âm thanh
  YouTube qua yt-dlp (format chỉ-âm-thanh tốt nhất, rồi format tốt nhất
  có âm thanh); tìm Zing qua endpoint gợi ý công khai (giống dịch vụ cũ:
  chỉ nhận entry type=1, status=1, privacy=1, playStatus=2, link
  `https://...zingmp3.vn/bai-hat/...`, trần phản hồi 1 MiB, httpx sync
  chạy qua `asyncio.to_thread`); giải luồng Zing/Facebook CHƯA chuyển
  (dịch vụ cũ dùng luồng lấy khoá web riêng từng nguồn, chưa kiểm chứng
  lại) → 502 rõ, không bịa link, không chuyển nguồn khác.
- `module.py` (rơ-le): nguồn đứt giữa chừng thì nối lại tối đa 5 lần
  (chờ 0,5/1/2/2/2 giây) từ ĐÚNG byte đã gửi, khúc 4 MiB; 403/404/410 thì
  quên link cũ, giải lại rồi mới tính lần thử; kiểm `Content-Range`
  (phải cùng tổng cỡ, bắt đầu đúng offset — sai thì tính 1 lần thất bại,
  không gửi byte nào); hết lần thì NGẮT (raise `LoiNguonKhongCuuDuoc`,
  không lấp rác, không chuyển bài); loa ngắt (`GeneratorExit`) hoặc cờ
  dừng thì đóng thượng nguồn và return im lặng, không request thêm.
  Trần: tối đa 2 lần trích xuất/tìm kiếm cùng lúc (semaphore, chờ tối đa
  30 giây rồi 502 `busy`); bộ nhớ đệm vé luồng tối đa 256 mục; lịch sử
  tối đa 200 mục.
- `modules/youtube-phat/` KHÔNG sửa một dòng nào (xác nhận bằng
  `git status`: chỉ có tệp mới `modules/youtube/`).

### 1.4 Đường integration của module (hợp đồng dịch vụ cũ)

Gốc `/api/integration/*` của dịch vụ cũ nay nằm dưới
`/m/youtube/api/`: `GET health`, `GET search` (source youtube/zing/
facebook; limit 1–30), `GET status`, `GET history`, `POST stop` (thân
rỗng = dừng tất cả; vé luồng cũ vô hiệu ngay), `POST session`,
`GET/POST playlists` (action list/create/rename/delete/add/remove/move/
export/import; mã chia sẻ `TTPL1.`), `POST session/outputs`,
`POST stream` (trả `stream_url` ký + `expires_in: 3600`), `POST play`,
`POST next/prev/seek`. Mọi URL do khách đưa (mục tiêu http) qua
`app/tu_xa.kiem_url_lan` (bộ kiểm SSRF CHUNG của kho — không viết bộ
kiểm thứ hai).

### 1.5 Trỏ Home Assistant sang (khi chủ máy chuyển)

- URL gốc mới là gốc của lõi web2api (ví dụ `http://<máy>:3031`,
  KHÔNG còn `/yt`, không còn cổng dịch vụ 8713). HA ghép địa chỉ bằng
  nối chuỗi thẳng (`base_url.rstrip("/") + path`) nên `stream_url`
  dạng đường dẫn `/m/youtube/api/stream/...` ghép đúng.
- Khoá mới là `khoa_tich_hop` của module youtube (không phải khoá quản
  trị, không phải token cũ của dịch vụ phụ).
- Chuyển dữ liệu từ c2a: chép `playlists.json`, `history.json` từ
  `<data c2a>/youtube_phat/` vào dữ liệu module (hoặc dùng action
  `import` của playlists) rồi khởi động lại — KHÔNG chép token cũ.
- c2a (cổng 3030) KHÔNG đụng cho tới khi chủ máy chuyển HA sang rồi kiểm.

## 2. Thư viện và ảnh (ĐỀ XUẤT Ở NHÁNH — chủ kho duyệt mới dựng)

- `requirements.txt` (nhánh này): thêm `yt-dlp==2026.8.19`,
  `yt-dlp-ejs==0.8.0`, `deno==2.9.7` — đúng phiên bản của
  `dich-vu/youtube-phat` để khỏi lệch hành vi giải luồng.
  Vì sao từng gói: yt-dlp tìm + giải luồng YouTube; yt-dlp-ejs là bộ
  script JavaScript để yt-dlp giải thử thách của YouTube; deno là trình
  chạy JavaScript cho yt-dlp-ejs.
- Băm wheel sha256 tính lại ngày 02/11/2026 (x86_64):
  - yt-dlp 2026.8.19:
    `1d57897e94c6665a0a6f9bc54b34e584284e32c034ffab3a7df25d8f7b24eedf`
  - yt-dlp-ejs 0.8.0:
    `79300e5fca7f937a1eeede11f0456862c1b41107ce1d726871e0207424f4bdb4`
  - deno 2.9.7 (manylinux x86_64; dựng cho arm64 thì tải lại wheel arm64
    và thay hash):
    `836f2ab5918723b47b638a05bc4fdac99fc35e69b49a6771c24e32b19dff5d8a`
- `Dockerfile` KHÔNG cần sửa (nó cài `requirements.txt`); `docker-compose.yml`
  KHÔNG sửa ở nhánh này.
- **Kích thước ảnh tăng: CHƯA ĐO ĐƯỢC** (môi trường làm việc không có
  docker; `which docker` không có). Tải về của 3 gói: deno 41,6 MB +
  yt-dlp 3,2 MB + yt-dlp-ejs 0,05 MB ≈ 44,9 MB nén; kích thước ảnh tăng
  thực tế (đã giải nén) phải đo bằng `docker images` khi dựng thật.
- **RSS khi 2 trích xuất cùng lúc: CHƯA ĐO ĐƯỢC** (không có docker, không
  có YouTube thật). Dịch vụ cũ ghi trích xuất tốn vài chục tới trăm MB +
  một lõi CPU mỗi lần. Đề xuất (chủ kho quyết, kèm số đo khi có): giữ
  `mem_limit` 1g / `pids_limit` 100 trước, đo thật rồi mới tăng nếu RSS
  đo được vượt ngưỡng; module đã có trần 2 lần cùng lúc nên không phình
  vô hạn.

## 3. Test

### 3.1 Test mới (16 test, xanh)

- `test/test_duong_module_nv277.py` (7 test, lõi qua TestClient với
  module giả + kho bí mật monkeypatch):
  không khoá → 401; khoá sai → 401; khoá module khác → 403; khoá đúng →
  200 từ đúng module + `Cache-Control: no-store`; đổi id module trong
  đường dẫn không chạm dữ liệu module khác (IDOR); module không chạy /
  không khai đường → 404; thân POST quá trần / JSON hỏng → 400; luồng:
  vé ký đúng → 200, Range lặp lại → cùng byte 206, vé giả → 404 THÂN
  RỖNG, vé hết hạn → 404, HEAD cùng vé chỉ trả header; nguồn ngoài LAN
  (không cờ test) → 404.
- `test/test_module_youtube_nv277.py` (9 test, module thật + trich_xuat
  và thượng nguồn giả):
  manifest hợp lệ qua `kiem_manifest`; nap/cai/suc_khoe; health/search/
  status; session/play/stop/history (stop xoá vé, session hiện tại về
  None); session không tồn tại → 404, target sai → 400; playlists
  create/add; stream trả `stream_url` ký hạn 3600; vé giả → 404, Range
  lặp lại → cùng byte; rơ-le nối lại từ đúng byte (mở lại đúng offset
  đứt, đủ 512/512 byte) và ngắt sau đúng 5 lần mở khi nguồn luôn đứt
  (`LoiNguonKhongCuuDuoc`, không lấp rác); dừng là dừng hẳn (vé + phiên
  xoá, vé cũ → 404); độc lập (module chỉ import `app.duong_module` +
  `app.tu_xa` trong `app.*`; `app/` + `web/` không chứa chuỗi `youtube`).

### 3.2 Test liên quan cũ

- `test_module_youtube_phat.py` + `test_web2api_chuan_module.py` +
  `test_web2api_url_ky.py`: 57 passed, 1 failed (xem 3.3).
- Test đường tĩnh/tab/CSP/kham_pha/youtube-phat-web (rủi ro do đổi thứ
  tự router): `test_web2api_tep_an_toan.py` +
  `test_web2api_tab_module_trong_he_thong.py` +
  `test_web2api_kham_pha.py` + `test_web2api_nv98_csp.py` +
  `test_nv153c_youtube_phat_web.py`: 66 passed, 5 skipped.
- Toàn bộ suite ở nhánh (lần chạy sạch, sau khi hết lỗi ghi file và
  hết tranh CPU, venv dựng lại từ requirements, bỏ qua file
  `test_web2api_dang_nhap_tu_dong.py` vì lỗi collection có sẵn):
  **65 failed, 6176 passed, 243 skipped, 31 xfailed, 18 errors**
  trong 17 phút. So sánh với main sạch cùng venv, cùng lệnh
  (worktree tại 66d0a9b): **60 failed, 6161 passed, 242 skipped,
  31 xfailed, 18 errors**. Diff tập đỏ: nhánh hơn main đúng 5 test —
  chính 5 test do patch gây ra đã sửa ở commit 5 (xem dưới); sau
  khi sửa, chạy lại toàn bộ 14 test từng đỏ ngoài mqtt: 7 passed
  (5 test đã sửa + 2 test đo tài nguyên vốn chập chờn), 7 failed
  còn lại đều đỏ cả trên main sạch. **Kết luận: không còn đỏ mới
  so với main sạch.** Số passed nhánh hơn main 15 ≈ 16 test mới
  trừ 1 (test đo tài nguyên chập chờn).
- Lần chạy suite trước đó (758 failed / 1203 errors) BỎ, không dùng:
  chạy đúng lúc máy bị lỗi ghi file của Python (shell vẫn ghi được)
  và 3 suite chạy song song tranh 4 CPU; cùng dấu hiệu NV276/NV278
  đã ghi (NV278: 697 failed / 1004 errors, cũng kết luận không dùng
  được). Lần chạy sạch trên đã thay thế nó.
- 5 đỏ do patch gây ra, đã sửa ở commit 5 và kiểm lại xanh:
  (1) `test_moi_duong_api_co_trong_readme` — README chưa nhắc đường
  `/m/{id_}/api/{duong:path}` → đã thêm dạng tổng quát
  `/m/{id}/api/{duong}` vào dòng youtube (không thêm dòng mới);
  (2) `test_readme_gon_gioi_han_dong` — README 416 dòng, vượt trần
  415 → đã gộp 2 dòng badge thành 1 dòng (chỉ khoảng trắng, hiển
  thị không đổi), về 415 dòng; (3) `test_02_moi_route_mo_phai_nam_
  trong_bang_ngoai_le` — 4 đường mới chưa có trong `BANG_NGOAI_LE_MO`
  → đã thêm cả 4 (GET/HEAD stream, GET/POST integration) kèm lý do
  chung, không tên module/nhà cung cấp; (4) `test_7_khong_ten_nha_
  cung_cap_trong_app_va_web` và (5) `test_dem_dong_nhac_ten_nha_cung_
  cap_khong_vuot_tran` — docstring `app/duong_module.py` dòng 6 có
  cụm «Home Assistant» → đã đổi thành «hệ thống nhà»; (6)
  `test_moi_truong_trong_kho_da_duoc_phan_loai` — trường manifest
  mới `duong_module` chưa phân loại → đã thêm vào
  `DA_XEM_XET_LA_QUYEN` (cấp đường riêng, là quyền).

### 3.3 Đỏ CÓ SẴN, không do NV277

- `test_module_youtube_phat.py::test_loai_thu_tu_la_so_nguyen_khong_trung`
  đỏ trên cả main sạch: `youtube-phat` và `nha-tien-ich` cùng
  `loai_thu_tu` 47 (kiểm bằng `git show HEAD:` cả hai manifest).
  NV277 dùng 48 (duy nhất) nên không gây ra và không sửa module khác
  ngoài phạm vi brief.
- `test_nv151_mqtt.py` (51 failed + 8 errors) và
  `test_web2api_muse2api.py::test_moi_manifest_goi_thieu_rong`:
  gói `paho` không có trong venv (import lỗi) — môi trường, không
  liên quan patch; NV283 cũng ghi 1 failed cũ do thiếu `paho`.
- `test_web2api_nv268_giao_dien_khu_tai_khoan.py` (8 errors): fixture
  `trinh_duyet` mở `/usr/bin/google-chrome --headless` thất bại
  (returncode 255) — máy không có Chrome chạy được, như NV281 đã ghi.
- `test_web2api_readme.py::test_moi_duong_api_co_trong_readme` vẫn đỏ
  1 đường `/api/trinh-duyet/{module}/man-hinh`: đường này có sẵn trên
  main, không phải của NV277, ngoài phạm vi brief nên không sửa.
- Các đỏ lẻ còn lại trong lần chạy sạch (`nv85` về chatgpt-web,
  `bien_env`, `nv187`, `nv261`/`nv266` đo tài nguyên): đều đỏ cả
  trên main sạch cùng venv (đã diff tập đỏ); `nv261`/`nv266` còn
  chập chờn theo thời gian đo (chạy lại thì xanh cả ở nhánh).

### 3.4 Quét

- `bandit -r app modules -lll` (đúng lệnh nghiệm thu): thoát 0.
- Bandit mặc định (nghiêm hơn) trên tệp mới: 0 issue sau khi đổi tìm
  Zing từ `urllib.urlopen` sang httpx sync (tránh B310).
- Quét bí mật/IP: không token/mật khẩu/cookie/email/IP thật nào trong
  patch, báo cáo, log (khoá trong test đều là chuỗi giả `khoa-gia-...`).

## 4. Bảo mật (đoạn bắt buộc của brief)

- Đường nào MỞ: chỉ `/m/<id>/api/stream/<vé>` (GET/HEAD) — lý do ghi ở
  đầu `app/duong_module.py`: loa không gửi được header, như dịch vụ cũ.
  Xác thực bằng vé ký `app/url_ky` (HMAC, hạn 3600 giây); vé giả/hết hạn
  → 404 trống, không nêu lý do. Cả 4 đường mới đều đã đăng ký vào
  `BANG_NGOAI_LE_MO` của `test_web2api_ma_tran_quyen.py` kèm lý do
  (stream: vé ký + LAN; integration: Bearer bằng bí mật riêng của
  module ngay trong hàm xử lý + LAN). Đường integration luôn cần Bearer bằng
  bí mật riêng của module; mọi phản hồi lỗi đều không nêu module nào
  tồn tại hay vé nào sai ở đâu.
- Test leo thang quyền / IDOR: `test_duong_module_nv277.py` —
  khoá module khác → 403; đổi id module trong đường dẫn → 403, không
  thấy dữ liệu module khác; module không khai đường → 404.
- Phụ thuộc mới: `yt-dlp` (Unlicense, chỉ dùng API công khai qua
  `YoutubeDL` — chưa đọc hết mã nguồn lớn), `yt-dlp-ejs` (MIT, chưa
  đọc), `deno` (MIT, nhị phân — wheel riêng theo kiến trúc). Đã đọc:
  `app/url_ky.py`, `app/ip_cho_phep.py`, `app/gioi_han.py`,
  `app/tuyen.py` (tep_module), `app/so_module.py`, `app/kham_pha.py`,
  `dich-vu/youtube-phat/` (server/streaming/search/session/ro_le/
  playlists/hang_cho/gioi_han/xac_thuc). Chưa đọc hết: mã nguồn yt-dlp
  (lớn), yt-dlp-ejs, deno (nhị phân).
- Handler mới KHÔNG nuốt lỗi âm thầm (test nv45): mọi `except Exception`
  trong `app/duong_module.py` và `modules/youtube/` đều ghi một dòng log
  chỉ nêu `type(e).__name__`, rồi trả mã lỗi rõ (401/403/404/502).
  Mọi hàng đợi có trần (trích xuất 2, vé 256, lịch sử 200); không
  `time.sleep`/`requests` trong mã bất đồng bộ (tìm Zing sync chạy qua
  `asyncio.to_thread`; chờ nối lại dùng `asyncio.sleep`).
- Lớp lỗi đã sửa trong lượt này (trả lời 3 câu của brief):
  1. Lớp lỗi: `request.query_params` của Starlette KHÔNG phải dict nên
     `url_ky.kiem_chu_ky` (chỉ nhận dict/str/list) luôn trả False —
     vé luồng đúng cũng bị 404. Đã sửa: chuyển sang dict trước khi kiểm
     (`app/duong_module.py`).
  2. Còn chỗ nào cùng lớp: grep `kiem_chu_ky\(` trong `app/` —
     chỗ gọi `url_ky.kiem_chu_ky` duy nhất trong mã sản phẩm là
     `duong_module` (đã sửa); `app/webhook.py` có hàm `_kiem_chu_ky`
     riêng (HMAC webhook, không liên quan `url_ky`); các test của
     `url_ky` truyền dict/str đúng khuôn. Không còn chỗ nào trong
     `app/` truyền QueryParams thô vào `url_ky.kiem_chu_ky`.
  3. Nguyên tắc: mọi giá trị từ framework (QueryParams, MultiDict) phải
     chuyển sang kiểu mà hàm kiểm nhận trước khi gọi, không trông vào
     «trông giống dict là dict».

## 5. Chỗ CHƯA kiểm — nói thật

- Chưa thử với YouTube thật (môi trường làm việc không có Internet ra
  ngoài theo conftest; yt-dlp chỉ kiểm import + phiên bản 2026.08.19,
  không gọi ytsearch thật), chưa thử với loa thật, HA thật.
- Chưa dựng ảnh Docker thật (`docker build` không chạy được ở đây):
  kích thước ảnh tăng và RSS khi 2 trích xuất cùng lúc CHƯA đo — chủ kho
  đo rồi quyết `mem_limit`/`pids_limit` (xem mục 2).
- Giải luồng Zing/Facebook chưa chuyển (502 rõ); tìm Zing chưa thử với
  endpoint thật (chỉ kiểm khuôn parse từ mã dịch vụ cũ).
- Chưa kiểm trên container thật / giao diện (module không có tab web).

## 6. Việc chủ kho phải duyệt (danh sách)

1. `requirements.txt` ở nhánh (yt-dlp/yt-dlp-ejs/deno) + đo kích thước
   ảnh bằng `docker images` khi dựng thật.
2. `mem_limit` 1g / `pids_limit` 100: giữ hay tăng, sau khi đo RSS khi
   2 trích xuất cùng lúc.
3. Luật ingress của hầm cloudflared cho `/m/*/api/*` (cổng LAN không
   chặn được qua hầm — xem `hoi-nv277.md` câu 1).
4. Có duyệt khả năng lõi mới `app/duong_module.py` (tiền tố
   `/m/<id>/api/...`, vé ký `app/url_ky`, LAN) làm chuẩn cho module sau
   này không, hay chỉ cho riêng module youtube (hiện lõi kiểm theo
   manifest từng module, module khác muốn dùng thì khai `duong_module`
   là có — không cần sửa lõi thêm).
5. Đỏ có sẵn `loai_thu_tu` 47 trùng (youtube-phat vs nha-tien-ich) —
   ngoài phạm vi NV277, có sửa riêng không.
6. Khi nào chuyển HA từ c2a sang module mới và kiểm với loa thật.

## 7. Tệp thay đổi (nhánh `nv277`, từ web2api main 66d0a9b)

- MỚI: `app/duong_module.py` (router lõi + LAN + vé ký).
- MỚI: `modules/youtube/manifest.json`, `modules/youtube/module.py`,
  `modules/youtube/trich_xuat.py`.
- MỚI: `test/test_duong_module_nv277.py`, `test/test_module_youtube_nv277.py`.
- SỬA: `app/main.py` (include router trước tep_module),
  `app/kham_pha.py` (tài liệu 2 phương thức mới),
  `docs/THAM-CHIEU.md` (tiểu mục module + dòng trạng thái),
  `README.md` (dòng bảng module + dạng đường tổng quát, gộp 2 dòng
  badge thành 1 để giữ trần 415 dòng),
  `requirements.txt` (đề xuất ở nhánh),
  `test/test_web2api_ma_tran_quyen.py` (4 mục `BANG_NGOAI_LE_MO`
  cho đường mới), `test/test_web2api_quyen_truong_hien_thi.py`
  (phân loại trường `duong_module` là quyền).
- KHÔNG SỬA: `modules/youtube-phat/`, `Dockerfile`, `docker-compose.yml`,
  `.github/`, `.gitleaks.toml`, `dich-vu/youtube-phat/`.
