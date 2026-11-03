# NV304 mảnh (c) — BÁO CÁO

## KẾT QUẢ

Mảnh (c) XONG, đã đẩy nhánh Giao `muse/nv304-c` (xem «Xác minh nộp» cuối
báo cáo): **giải luồng Zing, giải luồng Facebook, nhập playlist Zing và
`seek_url` đã có trong module youtube** — 4 mục còn thiếu so với dịch vụ
cũ ở mục 3 của file NV304. Patch là **DELTA trên mảnh (b)**, không chứa
lại thay đổi của (a)/(b). Thứ tự gộp: **(a) → (b) → (c) → (d)**.

## Nền và nguồn thắng

- Nền web2api: main `5f4df48` (đã có NV300 + NV301, đã gỡ youtube-phat).
- File nhiệm vụ kiểm lại lúc nộp: Giao main `3d5c37b0`, `inbox/NV304.md`
  đã ĐỔI so với lúc làm (a)/(b) — thêm đoạn «CẬP NHẬT 03/11 CHIỀU» (demo
  đưa vào `inbox/tai-lieu/demo/` + ảnh hiện trạng + yêu cầu sửa HTTP 409).
  Mảnh (c) làm đúng mục 3 cũ (không đổi); hai yêu cầu mới (bám demo từng
  chi tiết, sửa 409) thuộc mảnh tiếp theo, KHÔNG nhét vào (c) — xem
  «Việc còn lại» cuối báo cáo.
- LƯU Ý VỀ DEMO (ghi rõ, không nhận vơ): `support.js` BỊ THIẾU trên main
  `3d5c37b0` — đã kiểm toàn bộ cây main, không có file support.js nào,
  dù `DOC-TRUOC.md` nói nó bắt buộc («không có support.js thì hiện chữ
  {{…}} thô — đó KHÔNG phải demo»). Vì vậy demo CHƯA chạy được đúng
  nghĩa bằng http.server + Chrome từ máy này; mảnh (c) không đối chiếu
  bố cục với ảnh demo thật. Ngoài ra file NV304 nhắc ảnh
  `Doi-song-DUNG.png` nhưng file thực tế là `ANH-DUNG-Doi-song.png`
  (nhiều khả năng là cùng một ảnh, khác tên). Cả hai điểm này cần điều
  phối/chủ máy gửi bổ sung hoặc xác nhận — là câu hỏi mở, không chặn
  mảnh (c) và (d).

## Đã làm

### 1. Giải luồng Zing — `modules/youtube/trich_xuat.py`

Port từ `dich-vu/youtube-phat/streaming.py`, chuyển urllib sang httpx
(module đã dùng httpx cho search Zing; httpx tự giải nén gzip nên chỉ
chặn theo độ dài nội dung đã giải nén):

- Khoá API web KHÔNG nằm trong mã: `fetch_zing_web_keys` GET trang chủ
  zingmp3.vn (giới hạn 1 MiB) → tìm bó `main.min.js` trên host
  `*.zmdcdn.me` → GET bó (giới hạn 8 MiB) → trích cặp apiKey/secret bằng
  đúng regex của dịch vụ cũ. Zing đổi khoá thì tự theo.
- `_build_zing_api_url`: canonical `key=value` xếp theo key → sha256 hex
  → HMAC-SHA512 trên `path + digest` (đã đối chiếu lại bằng hashlib/hmac
  độc lập trong test).
- `resolve_zing_stream`: kiểm đích (host zingmp3.vn, path `/bai-hat/`,
  id 8 ký tự; id trần 8 ký tự cũng nhận, dựng URL chuẩn), GET đích theo
  chuyển hướng (kiểm host cuối), gọi API bài hát có ký, lấy URL 320
  trước rồi 128, chỉ nhận host CDN (`zmdcdn.me`, `zadn.vn`, `zing.vn`,
  `zingmp3.vn`), trả kèm header `Referer` + `User-Agent` (CDN Zing cần
  Referer) và `content_type` theo đuôi file.
- `TrichXuat` đệm khoá web trong instance, TTL 3600 s (như lõi cũ đệm
  `zing_keys`); `giai_am_thanh` thêm nhánh zing.
- Không giải được → `TrichXuatUnavailable` → 502 rõ, không bịa link.

### 2. Giải luồng Facebook — `modules/youtube/trich_xuat.py`

- `resolve_facebook_audio` qua yt-dlp trên địa chỉ chuẩn
  `https://www.facebook.com/watch/?v=<id>` (phủ cả reel lẫn video thường;
  dịch vụ cũ từng dùng `/video.php?v=` rồi kết luận sai «chỉ dành cho
  người dùng đã đăng ký»).
- Ưu tiên luồng chỉ-tiếng (acodec khác none, vcodec none) nếu có, không
  có thì tệp gộp mp4 «sd» rồi «hd» — chọn theo MÃ ĐỊNH DẠNG vì yt-dlp
  báo codec/chiều cao đều NA với tệp gộp của Facebook. Chỉ nhận host
  `fbcdn.net`.
- `tim_kiem` facebook KHÔNG đổi: dịch vụ cũ và module mới đều chỉ nhận
  link, không tìm theo từ khoá (chữ không phải link → 400 như cũ).

### 3. Module — `modules/youtube/module.py`

- `_nhap_nguon_playlist`: nhánh Zing thay vì raise `playlist_unavailable`
  — gọi `trich_xuat.lay_danh_sach_phat("zing", ...)` qua semaphore trích
  xuất, chuẩn hoá mục, trả (tên, các bài, text). `lay_danh_sach_phat`
  thêm nhánh zing qua `fetch_zing_playlist` (chỉ bài `streamingStatus`
  1, bài VIP status 2 bị bỏ như dịch vụ cũ, link `/bai-hat/`, id 8 ký
  tự).
- `_sieu_du_lieu`: với zing/facebook thiếu title/duration thì giải qua
  trich_xuat (qua semaphore, hỏng thì giữ gợi ý) để điền duration (và
  title/channel/thumbnail nếu nguồn cho); KHÔNG bịa tên/ảnh.
- `_tao_luong`: vé ghi thêm `headers` (Zing cần Referer) và `duration`,
  `content_type` từ kết quả giải.
- `_mo_khuc` trong `luong`: gộp header của vé vào header yêu cầu thượng
  nguồn (cùng với Range) để luồng Zing qua được CDN cần Referer; tương
  thích ngược với `mo_nguon` giả trong test (chỉ thêm key vào dict).
- `_giai_lai_link`: mở rộng từ chỉ youtube sang cả zing/facebook (giải
  lại qua trich_xuat, cập nhật cả url lẫn headers); http giữ nguyên.

### 4. `seek_url` — handler seek + rơ-le + route

- Handler `integration/seek`: sau khi cập nhật `position`, nếu phiên
  hiện tại có mục với source thuộc {youtube, zing, facebook, http} và
  có id mục tiêu thì đăng ký MỘT vé luồng mới theo kiểu «lười» (lazy,
  giống token của dịch vụ cũ — ký vé mà chưa giải ngay): bản ghi vé chứa
  `{source, target, duration}` (http: `url = target` thẳng, không lười);
  `seek_url = stream_url_của_vé + "?t=<position>"` (số nguyên thì không
  có `.0`, đúng dạng `?t=30` của test cũ).
- **Điểm kỹ thuật quan trọng:** `t` phải ký CÙNG URL — chữ ký lõi
  (`app/url_ky.py`) phủ cả query nên gắn thêm `&t=` vào URL đã ký sẽ
  làm hỏng xác minh. Vì vậy seek_url được ký lại từ đường chưa ký có
  sẵn `?t=` (qua `url_ky_mod.ky_url`), không gắn thêm vào URL của
  `_dang_ky_luong`.
- `luong(ve, khoang, phuong_thuc, tua_giay=None)`: vé lười (chưa có
  `url`) thì giải ngay lúc mở qua trich_xuat (qua semaphore); hỏng thì
  502. Nếu có `tua_giay` mà KHÔNG có Range thì kiểm `tua_giay` là số ≥
  0 (không thì 400); cần `duration` > 0 và tổng cỡ tệp: mở thăm dò
  thượng nguồn bằng Range `bytes=0-0` qua `_mo_khuc` rồi đọc
  `Content-Range`/`Content-Length` để lấy tổng, đóng lại; offset =
  round(tua_giay / duration × tổng), kẹp trong [0, tổng-1]; sau đó phục
  vụ từ offset đó với 206 + `Content-Range`. Range tường minh thắng
  `?t=`. Không tính được (thiếu duration/tổng) → 400, giống dịch vụ cũ
  trả 400 `invalid_seek`.
- Route `app/duong_module.py` `luong_cua_module` truyền thêm `?t=` vào
  `luong` (gọi 4 tham số, fallback TypeError về gọi 3 tham số để module
  khác sau này nếu chỉ cài `luong` 3 tham số thì không vỡ — TypeError do
  sai chữ ký xảy ra TRƯỚC khi thân hàm chạy nên không có tác dụng phụ;
  TypeError thật trong thân hàm thì lần gọi lại cũng ném lại rồi rơi về
  404 như trước). Chỉ youtube cài `luong` trong repo hiện tại (đã grep)
  nên đổi này an toàn.
- **Giới hạn trung thực (không giấu):** offset theo tỉ lệ chỉ là ước
  tính (chính xác với mp3 CBR, xấp xỉ với VBR/opus). Dịch vụ cũ dùng mục
  lục sidx của MP4 để đáp đúng ranh giới mảnh — port sidx
  (`doc_muc_luc_mp4` của dịch vụ cũ) được HOÃN lại, chưa có trong (c).

### 5. Trang tab — bỏ cảnh báo cũ

- `modules/youtube/web/trang.js` + `index.html`: bỏ khối `baoNguon`
  («module chưa giải được luồng Zing/Facebook… lỗi 502») và phần tử
  `<p id="bao-nguon-chua-ho-tro">`; cập nhật `ghiChu` nguồn (bỏ câu cảnh
  báo Zing/Facebook). Test NV301 cũ không assert id này nên vẫn xanh.

### 6. Văn bản kèm theo

- Cập nhật docstring đầu `module.py` (bỏ câu «giải luồng Zing/Facebook
  chưa chuyển», «seek_url trả None»), docstring `_la_link_playlist_zing`
  và `mo_ta` trong `manifest.json` (giữ nguyên định dạng một dòng) cho
  đúng sau (c).

## Kiểm chứng

- Test mới `test/test_module_youtube_nv304_c.py`: **14/14 xanh**
  (đỏ trước: 13/13 đỏ khi chưa có code — các hàm chưa tồn tại; 1 test
  route viết sau cùng, xanh ngay vì route chỉ là nối dây đã có sẵn
  hành vi module). Nội dung: trich_xuat thuần (trích khoá web, ký URL
  API đối chiếu hashlib/hmac độc lập, id playlist, lấy khoá qua client
  giả, giải Zing chọn 320 + lọc CDN, lỗi API → 502, nhập playlist lọc
  VIP, Facebook chọn tiếng riêng rồi tệp gộp sd); module với
  `TrichXuatGia` (seek → `seek_url` chứa `/api/stream/` và `?t=30`,
  rơ-le tua tới byte tỉ lệ 141/1000 với tổng 1000, thiếu duration →
  400, nhập playlist Zing, siêu dữ liệu Zing điền duration); route thật
  bằng TestClient (vé ký kèm `?t=30` qua xác minh và tới `luong` với
  t="30"; module cũ 3 tham số vẫn phục vụ được vé có `?t=`; t không có
  trong chữ ký → 404).
- 2 test NV301 cũ ĐỔI THEO HÀNH VI MỚI (ghi chú NV304c trong test, không
  sửa lén): `test_seek_giay_position_kep_va_loi` (seek_url không còn
  None mà là vé ký kèm `?t=213` theo vị trí đã kẹp) và
  `test_import_loi_ro_rang` (link Zing giờ qua trich_xuat: fake rỗng →
  `playlist_empty`, fake có playlist → 200 với đúng item).
- Bộ liên quan: (c) + (a) + (b) + NV301 giao diện/tab/lõi/playlist +
  NV277 + route NV277 + doc_lap + khu NV297 = **98 passed, 8 skipped**
  (lý do skip sẵn có, không đổi). `node --check` cả `trang.js` và
  `khung.js` sạch. Taste lint `--app` trên hai tệp trình phát: **0
  FAIL, 3 WARN** — đã xem và GIỮ NGUYÊN có lý do (zero-padding là định
  dạng đồng hồ phút:giây; dấu «—» là dấu câu tiếng Việt).
- Patch áp nối tiếp (a) → (b) → (c) lên nền `5f4df48` bằng `git apply`
  THẬT trên worktree nền sạch: sạch.
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật
  (chữ «token»/«cookie» chỉ là tên biến và tên cookie phiên bản web
  `zmp3_app_version.1` trong test giả).

## Chưa làm / cần chủ máy (ghi rõ, không nhận vơ)

- **Chưa thử trên HA thật, chưa kiểm Chrome thật** (máy này không có
  Chrome): sau khi điều phối dựng lại, cần thử thật rằng bài Zing/
  Facebook phát được ra loa, nhập playlist Zing được, và seek tua tới
  đúng vị trí (offset tỉ lệ là ước tính — nghe thử với mp3 CBR và
  VBR/opus để biết độ lệch thực tế).
- **Chưa đối chiếu bố cục với ảnh demo thật** (support.js thiếu nên
  demo chưa chạy đúng nghĩa; xem «Nền và nguồn thắng»). Việc bám demo
  từng chi tiết + sửa HTTP 409 thuộc mảnh tiếp theo, không có trong
  (c).
- **Bảng endpoint cũ vs mới còn nợ sang mảnh (d)** (mục tiêu: không còn
  dòng «thiếu/sai» sau (d)); mảnh (c) không lập bảng này.
- Port sidx cho tua đúng ranh giới mảnh: hoãn lại (xem «Giới hạn trung
  thực» ở trên).

## Việc còn lại

- Mảnh (d): port 9 tệp test cũ trong `dich-vu/youtube-phat/test_*.py`
  + bảng endpoint cũ vs mới (tổng đếm được trong repo là 94 hàm test,
  không phải ~125 như file ghi — sẽ ghi rõ cách đếm trong báo cáo (d)).
- Mảnh tiếp theo (ngoài (a)–(d), theo cập nhật file NV304 chiều 03/11):
  bám demo từng chi tiết (2 cột, chip nguồn + ô tìm tròn trên cùng, nút
  tròn SVG, thanh chip dưới có số lượng Playlist/Queue) + sửa HTTP 409
  khi Phát/Dừng/Tìm từ trang; cần support.js bổ sung để chạy demo đúng
  nghĩa và đối chiếu ảnh.

## Xác minh nộp

- Nhánh Giao: `muse/nv304-c` = `bb2b9ec9e9cc3253506e303933f6a65783c5ab47`
  (kiểm bằng ls-remote; Giao main lúc đẩy không đổi `3d5c37b0`).
- Patch: `outbox/nv304-c.patch` trên nhánh (1198 dòng, 9 tệp).
- Commit repo: `d4c4483` «NV304c: giai luong Zing/Facebook, nhap
  playlist Zing, seek_url ?t=», cha là commit (b) `b26c5a8`.
- Thứ tự gộp: (a) → (b) → (c) → (d); (c) là delta trên (b).
