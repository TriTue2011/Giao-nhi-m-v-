# NV304 (d) — Port test cũ + bảng endpoint cũ-vs-mới + liệt kê điểm sai

## KẾT QUẢ

- **Mảnh (d) đã xong, nộp nhánh Giao mới `muse/nv304-d`** với
  `outbox/nv304-d.patch` (1776 dòng, 3 file, +1556/−30) và báo cáo này.
  Chỉ đẩy nhánh `muse/*`, không đẩy main, không force-push, không đẩy
  trực tiếp lên repo web2api.
- **Patch là DELTA trên cây (e), thứ tự gộp: (a) → (b) → (c) → (e) → (d).**
  Commit làm việc trong repo web2api: `7392c41` (nhánh local
  `nv304-d-lam-viec`, không đẩy lên repo web2api), diff từ `d52262d`
  (cây (e)) tới `7392c41`.
- **Test port: 76/76 xanh** trong file mới
  `test/test_module_youtube_nv304_d.py` (60 hàm + 1 test parametrize
  17 route = 76 case thu thập). Bộ liên quan 12 file: **174 passed**.
  Toàn suite: cây (d) **158 failed / 6029 passed / 273 skipped /
  31 xfailed / 17 errors**; cây nền (e) sạch **158 failed / 5953 passed /
  273 skipped / 31 xfailed / 17 errors** — failed/skipped/xfailed/errors
  giống hệt, passed tăng đúng 76 = số test (d) mới, **không có lỗi mới**,
  không có test youtube nào lỗi ở nền (e).
- **Bảng endpoint cuối: KHÔNG còn dòng «thiếu/sai».** 16 route cũ đều có
  đối chiếu (đã có / thay thế bằng gì / bỏ vì lý do gì); thêm 2 route
  mới của NV301 (pause, queue). Xem bảng ở mục 4.
- **Mục LIỆT KÊ ĐIỂM SAI (mục 6) theo phản ánh 16:29 của người dùng:**
  lệch demo D1–D8 + 9 nhóm lệch c2a/dịch vụ cũ **đã sửa trong (d)**
  (mã lỗi, health, history, artist, giới hạn tìm, stop revision, host,
  rơ-le, media_content_type) + các điểm giữ nguyên có lý do + điểm mở.
  Test port assert hành vi ĐÚNG, không port mù assertion cũ.
- **Chưa thử trên HA thật, chưa kiểm Chrome thật** (máy này không có
  Chrome). support.js **vẫn thiếu** trên Giao main mới nhất (xem mục 8).

## 1. Nền / base / delta

- Giao main lúc nộp: `82d9ff46` (không đổi trong lúc làm). File nhiệm vụ
  `inbox/NV304.md` không đổi (md5 `efdbfdcb0f0fe316cc39ebdd36f2237a`
  trước và sau).
- Nền web2api: main `5f4df48` (đã có NV300 + NV301, đã gỡ youtube-phat).
  Web2api main mới nhất lúc làm (`7d63968`) **chưa** chứa các mảnh NV304
  (kiểm: không có file `test_nv304*`, `web/khung.js` có 0 lần
  `can_xac_nhan`, log không có commit NV304) — nên (d) làm dạng DELTA
  trên cây (e), không làm trực tiếp trên main.
- Chuỗi áp đã kiểm bằng `git apply` thật, tuần tự, kiểm sau mỗi bước:
  (a) từ `~/workspace/nv304/nv304-a.patch` → 18e13c9; (b) từ
  `~/workspace/nv304/nv304-b.patch` → 2a8b05f; (c) từ
  `~/workspace/nv304/nv304-c.patch` → 9e13382; (e) từ
  `~/workspace/nv304/giao/outbox/nv304-e.patch` → d52262d. Lưu ý: kiểm
  `--check` từng patch riêng trên nền gốc sẽ FAIL cho (b)/(c)/(e) vì
  chúng là delta nối tiếp — phải áp tuần tự.
- Patch (d) đã kiểm `git apply --check` sạch trên cây (e) sạch
  (worktree `~/workspace/nv304-d/repo-nen/`, detached HEAD d52262d).

## 2. Cách đếm test cũ (đừng nhận ~125)

- Nguồn test cũ: `dich-vu/youtube-phat/` tại commit `83ddd57^` (ngay
  trước commit 83ddd57 «NV301 kiểm: gỡ module youtube-phat» — đường dẫn
  `/opt/claude-c2a/...` trong file NV304 nằm trên máy điều phối, không
  có trên máy này). 9 tệp test, 1837 dòng.
- Đếm theo hàm (`grep ^\s*def test`, 0 async): bai_ke_tua 24, bao_mat 14,
  dung_han 5, gioi_han 3, hop_dong 21, luong 10, luong_doc_loi 5,
  tim_kiem_chuyen_huong 5, xac_thuc_khong_ascii 7 → **94 hàm**.
- Đếm mở rộng parametrize (script AST, đếm phần tử list literal hoặc
  biến list module-level như `_CAC_ROUTE_CAN_BEARER`): bao_mat 15,
  hop_dong 36, tim_kiem 9, xac_thuc 9, còn lại như trên → **116 case**.
- Xác nhận bằng pytest thật trên code cũ (venv NV289, pytest 9.1.1):
  **«116 tests collected»**.
- Kết luận: **94 hàm, 116 case thu thập. Con số «~125» trong file NV304
  là ước lượng, không khớp chính xác với cả hai cách đếm (lệch 9 so
  với 116 case, 31 so với 94 hàm).** Báo cáo này dùng 94/116, không
  tự nhận ~125.

## 3. Port test theo file cũ (file (d): 60 hàm + 17-case parametrize = 76)

| File cũ (hàm / case) | Test (d) | Nội dung chính |
|---|---|---|
| test_hop_dong (21 / 36) | 17 hàm + 1 parametrize 17 route | health/search/status/session/stop/outputs/playlists/stream/play/pause/queue; bearer 401, khoá module khác 403, thân POST >400_000 → 400 |
| test_bai_ke_tua (24) | 8 | next/prev, 409 queue_start/queue_end, phát bài trong kết quả tìm rồi next theo hàng tìm, 5 next đồng thời qua asyncio.Lock → index 5, seek đặt/kẹp/lỗi, seek_url qua HTTP, tua tỉ lệ, Range thắng tua_giay |
| test_dung_han (5) | 4 | khởi động lại: playlists/history BỀN, phiên/vé chỉ RAM nên mất; tắt giữa chừng; client ngắt; hết 5 lần nối lại → LoiNguonKhongCuuDuoc |
| test_gioi_han (3) | 3 | semaphore trich_xuat tối đa 2, hết chỗ quá thời gian → TrichXuatUnavailable("busy"), cắt đệm luồng giữ 256 vé còn hạn lâu nhất |
| test_bao_mat (14 / 15) | 6 | resolve youtube chặn host lạ, facebook chỉ fbcdn, vé luồng giả → 404 trống (cũ: 403), log không lộ bí mật, tệp bền 0600 + thư mục 0700, vé ngẫu nhiên urlsafe + expires_in 3600 |
| test_luong (10) + test_luong_doc_loi (5) | 13 | qua `_luong_chiu_loi` trực tiếp với nguồn giả: cắt giữa/sau ranh giới khúc, 3 lần cắt liên tiếp, 403 → giải lại, 200 phớt Range → giải lại, Content-Range lệch/đổi tổng, 416 im lặng, quá 5 lần mở hỏng → raise, đọc lỗi giữa khúc, bên nhận đóng, đọc chậm 2 MiB miếng 64 KiB (sha256 khớp, đỉnh tracemalloc < 2 MiB) |
| test_tim_kiem_chuyen_huong (5 / 9) | 1 | tìm Facebook bằng link → 200 + id. 9 case handler redirect urllib KHÔNG port (xem mục 7) |
| test_xac_thuc_khong_ascii (7 / 9) | 2 | qua lõi: Bearer không ASCII → 401 không 500; vé luồng không ASCII → 404 không 500; health khoá đúng → 200 đối chứng |
| — (smoke bảng endpoint) | 1 | 16 route cũ đều 200 với khoá đúng + gọi hợp lệ (kể cả stream GET 1024 byte, stream HEAD 200 + thân rỗng) |
| — (khóa hành vi c2a mới) | 5 | play chỉ target link youtu.be không source; stop theo revision; history id + session artist; link dài 2048/từ khoá dài 120; volume không phải số → invalid_volume_level |

- Khung test (theo mẫu NV301/(c)): nạp `module.py` trực tiếp bằng
  importlib, `Module({}, _thu_muc_du_lieu=tmp)`, `nap({})`, trich_xuat
  giả (`tim_kiem`/`giai_am_thanh`/`lay_danh_sach_phat`), gọi
  `asyncio.run(m.tich_hop(...))` (kho chưa có pytest-asyncio). Khung lõi
  HTTP theo mẫu `test_duong_module_nv277.py`: FastAPI +
  `duong_module.router` + module youtube thật + khoá khách thật qua
  `khoa_khach.tao_khoa`, TestClient `("127.0.0.1", 50000)`,
  `WEB2API_TEST_CHO_PHEP_LOOPBACK=1`.
- Số test (d) (76) nhỏ hơn số case cũ (116) vì: (a) nhiều case
  parametrize cũ gộp thành một test lặp; (b) phần hợp đồng xác thực/
  đường luồng của lõi đã có test NV277/NV289 bao phủ — (d) không port
  lại toàn bộ, chỉ port phần tương ứng qua module youtube thật;
  (c) các case không port được liệt kê ở mục 7, không giấu.

## 4. Bảng endpoint cũ-vs-mới (không còn dòng «thiếu/sai»)

- Tiền tố đường đổi (di trú đã ghi trong tài liệu lõi, không phải
  thiếu): dịch vụ cũ ở gốc `/api/integration/*`, `/api/stream/*`;
  module mới qua lõi `/m/youtube/api/integration/*`,
  `/m/youtube/api/stream/<ve>?_het_han&_ky`.
- Xác thực đổi theo kiến trúc đã chốt (NV289/NV277, không phải thiếu):
  token tích hợp riêng của cũ → khoá khách lõi (thiếu/sai/thu hồi →
  401 `invalid_auth`; khoá quản trị/«*»/«*@m»/module khác → 403
  `forbidden`); luồng không Bearer, xác thực bằng vé ký lõi (sai/hết
  hạn → 404 trống, không lộ lý do). Thân POST trần 400_000 byte
  (bằng trần lớn nhất của cũ, cho import playlist). Cả hai nhóm đường
  chỉ chấp nhận nguồn LAN.

| Route cũ | Route mới | Trạng thái cuối |
|---|---|---|
| GET /api/integration/health | GET /m/youtube/api/integration/health | ĐÃ CÓ. Sau (d): capabilities có "play", sources và playback_sources đủ [youtube, zing, facebook, http] như c2a |
| GET /api/integration/search | GET …/integration/search | ĐÃ CÓ. Trả cả `results` (dạng NV277) lẫn `items` (dạng cũ) cùng một danh sách đã chuẩn hoá; source youtube/zing/facebook; giới hạn từ khoá 120 / link 2048 sau (d) |
| GET /api/integration/status | GET …/integration/status | ĐÃ CÓ. Đủ dạng cũ + thêm `playlists_count`; sessions chỉ phiên còn sống, mới đổi nhất trước |
| GET /api/integration/history | GET …/integration/history | ĐÃ CÓ. Trả `history` + `items` + `total`; sau (d) mỗi item có `id` (= target) như c2a |
| POST /api/integration/stop | POST …/integration/stop | ĐÃ CÓ. Theo session_id hoặc expected_revision; không khớp → 200 {stopped: False}. Khác cũ có chủ ý: body rỗng → dừng hết (hành vi NV277; khớp c2a khi không truyền thân, khác cũ ở chỗ {} cũng dừng hết) |
| POST /api/integration/session | POST …/integration/session | ĐÃ CÓ. Trả 200 (không 201) như cũ; tự ghi lịch sử. Sau (d): mã lỗi theo nguồn (xem mục 6B) |
| GET /api/integration/playlists | GET …/integration/playlists | ĐÃ CÓ |
| POST /api/integration/playlists | POST …/integration/playlists | ĐÃ CÓ. list/create/rename/delete/add/remove/move/export/import + mã chia sẻ TTPL1 (tạo bên này mở được bên kia) |
| POST /api/integration/session/outputs | POST …/integration/session/outputs | ĐÃ CÓ. Khác cũ có chủ ý, ghi rõ: phiên không sống → 200 {stopped: False} thay 404 (NV277, thân thiện tab); outputs ["den-sai"] được chấp nhận (module không kiểm định dạng thực thể — điểm mở mức thấp, mục 6D) |
| POST /api/integration/stream | POST …/integration/stream | ĐÃ CÓ. Trả `stream_url` dạng lõi + `token` + `expires_in` 3600; sau (d) khôi phục `media_content_type` (http → audio/mpeg, đã giải → content_type của nguồn) |
| POST /api/integration/play | POST …/integration/play | ĐÃ CÓ. Trả `session`/`item`/`session_revision`; phiên đã dừng → 404 không hồi sinh (NV301); play chỉ target link youtu.be không source → 200 (c2a) |
| POST /api/integration/pause | — (không có ở cũ) | MỚI từ NV301. Giữ phiên, chỉ đổi trạng thái thành paused; phiên không sống → 404 |
| POST /api/integration/next | POST …/integration/next | ĐÃ CÓ. 409 queue_start/queue_end; chuyển bài đặt lại position = 0 |
| POST /api/integration/prev | POST …/integration/prev | ĐÃ CÓ. Như next |
| POST /api/integration/seek | POST …/integration/seek | ĐÃ CÓ (từ (c)). Nhận cả `giay` lẫn `position`, kẹp theo thời lượng; `seek_url` = vé lười có ký kèm `?t=<giây>` (số nguyên, dạng `?t=30` của test cũ) |
| GET /api/integration/queue | — (không có ở cũ) | MỚI từ NV301. GET+POST hàng đợi |
| POST /api/integration/queue | — (không có ở cũ) | MỚI từ NV301 (xem dòng trên) |
| GET /api/stream/{token} | GET /m/youtube/api/stream/{ve}?_het_han&_ky | THAY THẾ bằng vé ký lõi (HMAC phủ phương thức + đường + hạn, hạn mặc định 3600). Sai/hết hạn → 404 trống thay 403 `invalid_stream_token` (thiết kế chống liệt kê của NV277). Range: hậu tố → 206 byte cuối, Range hỏng → 416 (đúng RFC; xem mục 6C) |
| HEAD /api/stream/{token} | HEAD …/stream/{ve}?_het_han&_ky | THAY THẾ như GET. Khác cũ ghi rõ: HEAD qua lõi trả thân rỗng nên Starlette ghi Content-Length 0 (cũ thăm dò bytes=0-0 trả tổng thật) — hạn chế tầng lõi, không phải hành vi module; test (d) assert Content-Type, không assert Content-Length |

## 5. Phân tích chatgpt2api (luật đứng 16:11 — clone đọc, không sửa)

- Repo công khai TriTue2011/chatgpt2api, clone tại
  `~/workspace/nv304-d/chatgpt2api`, HEAD đúng `d879b03` — chính commit
  mà header `server.py` của dịch vụ cũ trích dẫn.
- File đã đọc kỹ:
  - `api/youtube_phat.py` (745 dòng): docstring «trả ĐÚNG hợp đồng đó»
    dưới tiền tố `/yt`, chuyển từ add-on 0.6.2; `TIEN_TO="/yt"`;
    `_KHA_NANG=["history","play","search","session","sessions",
    "status","stop","youtube_stream","zing_stream"]`; `_xac_thuc`
    Bearer token riêng `DATA_DIR/youtube_phat/integration_token` bằng
    `hmac.compare_digest`, sai → 401 `invalid_auth`; `_doc_json` với
    trần theo route + body rỗng → `invalid_request`; health/search/
    status/history/stop/session/playlists GET+POST/session/outputs/
    stream/play; `_mo_luong` token rỗng/>4096 → 403, verify hỏng →
    403 `invalid_stream_token`, resolve hỏng → 502; `proxy_stream`
    GET: `.m3u8` → danh sách HLS, iOS → 302 `.m3u8`, Range sai regex →
    400 `invalid_range`, `bytes=-N` → 200 từ đầu (comment «Giữ nguyên
    đường cũ cho nó»), khúc 4 MiB, mở lại tối đa 2 lần (403/404/410 →
    forget + giải lại 1 lần), 206 khi có Range + tổng, else 200;
    `head_stream` HEAD thăm dò bytes=0-0 lấy tổng; route quản trị
    `/api/youtube-phat/*` sau `require_admin`, KHÔNG phải route
    integration.
  - `services/youtube_phat/streaming.py`: `create_stream_token`/
    `verify_stream_token` (payload JSON `{exp, source, target}` +
    HMAC-SHA256, base64url, `compare_digest`; TTL 30..7200, mặc định
    300); `YOUTUBE_STREAM_HOSTS=("googlevideo.com",)` kiểm suffix ở
    2 chỗ; `_ZingRedirectHandler` (chỉ redirect tới URL Zing đã kiểm);
    `doc_muc_luc_mp4` (sidx); `_STREAM_TOKEN_KY` regex
    `/api/stream/([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)`.
  - `services/youtube_phat/search.py`: `resolve_facebook_share` dùng
    `urlopen` TRẦN (handler chặn redirect chỉ có ở dịch vụ cũ, thêm ở
    NV153 D3, KHÔNG có trong c2a); `facebook_url_query` (watch/reel/
    videos, KHÔNG nhận /share/v/); `MAX_QUERY_LENGTH = 120` (từ khoá),
    `MAX_URL_LENGTH = 2048` (link); `parse_facebook_payload`.
  - `services/youtube_phat/playlists.py`: `SHARE_PREFIX="TTPL1."`,
    `share_code`/`read_share_code` (base64url(zlib(JSON {n, i})) — cùng
    định dạng với module mới, mã tạo bên này mở được bên kia);
    `playlist_action` (list/create/rename/delete/add/remove/move/
    export/import).
  - `services/youtube_phat/dich_vu.py::record_session` + whitelist mã:
    session: `invalid_youtube_target` / `invalid_zing_target` /
    `invalid_facebook_target` / `invalid_http_audio_target` /
    `unsupported_session_source` / `invalid_output_entity_ids` /
    `invalid_volume_level` / `invalid_session_id` /
    `playlist_not_found` → 404 / `unverified_zing_target` → 403;
    stream: `unsupported_stream_source` + các mã trên → 409
    (riêng `unverified_zing_target` → 403); search: limit sai →
    `invalid_search_query`; stop: body rỗng theo content-length 0 →
    `stop(None, None)` (dừng phiên hiện tại), body JSON {} → 400
    `invalid_session_revision`.
  - `test/test_youtube_phat_api.py` (574 dòng) +
    `test/test_youtube_phat_luong_hinh.py` (128 dòng) — định nghĩa
    «đúng» cho đối chiếu: health assert `"play" in capabilities` và
    `playback_sources == ["youtube", "zing", "facebook", "http"]`; play
    target-only không cần source; status `state` + `history_count` +
    `session["item"]`; stop không body → success + idle; stop revision
    cũ → `stopped False` + item phiên mới hơn; search link dài (>120
    ký tự từ khoá) vẫn 200, `q="x"*2049` → 400 `invalid_search_query`;
    session zing/http; stream assert `media_content_type`
    (`("youtube", "audio/mp4")`), token sai → 403, Range lạ → 400,
    nguồn lạ → 400; iOS → 302 `.m3u8`, HLS 2 khúc, sidx.
- **Kết luận đối chiếu:** module youtube mới mirror **DỊCH VỤ CŨ
  youtube-phat** (vốn là port trung thực của c2a tại d879b03 — cùng
  route, cùng mã lỗi, cùng scheme token payload.sig, cùng TTPL1, cùng
  limit 30, cùng trần playlists 400_000, cùng expires 3600, cùng quirk
  Range), KHÔNG mirror trực tiếp c2a. Những gì c2a có mà module không
  có đều thuộc 1 trong 3 nhóm: (a) giao diện web riêng của c2a (route
  quản trị `/api/youtube-phat/*`, tab YouTube của c2a) — web2api thay
  bằng tab module + thực thể HA; (b) đường video/hình (youtube_video/
  facebook_video, HLS .m3u8 cho iPhone, sidx) — module chỉ làm tiếng,
  sidx đã hoãn ở (c); (c) cơ chế xác thực/ký riêng của c2a (token tích
  hợp 1 khoá, token luồng payload.sig) — web2api thay bằng khoá khách
  lõi (NV289) + URL ký lõi (NV277) theo kiến trúc đã chốt, giữ nguyên
  tính chất bảo mật (không Bearer cho luồng, vé có hạn, sai → không
  lộ lý do).
- Tích hợp HA của c2a (`custom_components/tritue_youtube_player`)
  **không có trong clone c2a này** (không có thư mục
  `custom_components/`) — không kiểm được HA integration có rẽ nhánh
  theo mã lỗi/capabilities hay không; đối chiếu dựa trên test hợp đồng
  của c2a thay vì code HA integration. Điểm này ghi là mở (mục 6D),
  không đoán.
- Theo tinh thần đính chính 16:58 (khác c2a ≠ tự động sai): các lệch
  được khôi phục trong (d) đều là lệch **không có căn cứ kiến trúc**
  (đổi tên mã, giấu capability/nguồn, thiếu trường) và đều có test
  chứng minh đúng + khả thi (đỏ-trước-xanh, mục 9); các lệch có căn
  cứ kiến trúc đã chốt được giữ lại và ghi rõ lý do (mục 6C), không
  sửa mù cho «giống c2a».

## 6. LIỆT KÊ ĐIỂM SAI (theo phản ánh 16:29: sai so với demo + không giống c2a)

### 6A. Lệch demo (nguồn: ảnh `ANH-DUNG-Doi-song.png` đã xem trực tiếp +
### mã `Doi-song.dc.html` + trang hiện tại `modules/youtube/web/index.html`
### + `trang.js` + diff (a); demo là chuẩn theo luật đứng 15:54)

Ảnh demo mô tả để đối chiếu: thanh điều hướng Studio · Tác phẩm · Nhà
· Đời sống · Hệ thống; hàng tìm: chip YouTube (đen, đang chọn) · Zing
MP3 · Facebook + ô pill rộng placeholder «Tìm tên bài hát, ca sĩ hoặc
dán link YouTube…» + nút tròn xám kính lúp ở cuối hàng; dưới là bố cục
2 cột: TRÁI là thẻ Đang phát (ảnh bìa TRÒN gradient + nốt nhạc, chip
«Zing MP3» trên bìa, sóng âm trang trí, tiêu đề + dòng phụ, thanh tiến
độ với 0:40 / 3:08 hai đầu, nút Trước nhỏ · Phát/Tạm dừng tròn đen LỚN
· Kế nhỏ · Dừng ô vuông đỏ, nút «Nghe khi tắt màn hình», dưới vạch ngăn
là «Nhóm đang phát — bấm để điều khiển» + 1 ô nhóm gồm tên bài + loa +
0:40 / 3:08); PHẢI là «Gợi ý cho bạn 8 mục» + dòng chú «Tivi mở ứng
dụng YouTube, loa nhận tiếng.» + 8 hàng (ảnh nhỏ · tiêu đề · kênh ·
thời lượng · 3 nút tròn: Phát đen · Queue · Playlist); cuối trang là
thanh chip: Tìm kiếm (đen) · Playlist (3) · Queue (5/5) · Loa & tivi ·
Cài đặt; ghi chú «Demo: YouTube lấy từ playlist đã lưu trong nhà; bản
thật gọi tìm kiếm của YouTube.»

- **D1 (chắc chắn):** Tìm kiếm hiện là MỘT SECTION riêng có h2 «Tìm
  kiếm» + label «Từ khoá hoặc link bài, link playlist» + ghi chú «Tìm
  trên YouTube: gõ từ khoá hoặc dán link bài/playlist.» — demo KHÔNG
  có tiêu đề/label/ghi chú này, chỉ có một hàng chip + ô pill + nút
  tròn. Placeholder hiện «Tên bài, ca sĩ… hoặc dán link YouTube» gần
  đúng nhưng ngắn hơn demo.
- **D2 (chắc chắn):** Cột phải hiện tiêu đề «Kết quả» với danh sách
  rỗng lúc đầu + ô select «Playlist nhận bài khi bấm Thêm vào
  Playlist» — demo lúc đầu là «Gợi ý cho bạn 8 mục» kèm dòng chú «Tivi
  mở ứng dụng YouTube, loa nhận tiếng.»; demo KHÔNG có select playlist
  nhận bài trong cột kết quả (thêm vào playlist bằng nút playlist từng
  hàng). (e) đổi tiêu đề thành «Kết quả (N mục)» chỉ đúng SAU khi tìm,
  không đúng trạng thái đầu.
- **D3 (chắc chắn theo ảnh):** Tỉ lệ 2 cột hiện tại màn hình rộng là
  `5fr/7fr` (trái ~42%) trong `modules/youtube/web/index.html` dòng
  39; ảnh demo trái ~54% (thẻ Đang phát rộng hơn nửa). Tỉ lệ cột bị
  lệch ngược.
- **D4 (chắc chắn):** Ảnh bìa hiện tại `.bia` là chữ nhật 16:9
  (`width:100%; max-width:480px; aspect-ratio:16/9; object-fit:cover`);
  demo là ảnh TRÒN. Sóng âm trang trí của demo đã được (e) cố tình
  không sao chép — ghi là lược bỏ có chủ ý (trang trí), không tính
  là sai.
- **D5 (một phần đúng):** «Nhóm đang phát» hiện ĐÃ nằm trong thẻ Đang
  phát (đúng (e)) nhưng hiện là MỘT SECTION có h2 + đoạn giải thích +
  DANH SÁCH nhiều nhóm (`ds-nhom`); demo là 1 ô nhóm duy nhất (nhóm
  đang phát hiện tại) dưới vạch ngăn, không đoạn giải thích, có thời
  gian phải.
- **D6 (chưa xác minh được từ ảnh tĩnh):** Thanh chip dưới hiện
  `position: sticky; bottom: 0` (luôn dính); ảnh demo không cho biết
  thanh có dính hay không — ghi là chưa xác minh, không kết luận sai.
- **D7 (chắc chắn một phần):** Nhúng `?nhung=1` chỉ ẩn link «← Hệ
  thống» + H1 «YouTube»; đoạn giới thiệu `.phu` («Trình phát
  YouTube/Zing chạy thẳng trong web2api…») VẪN HIỆN khi nhúng vào Đời
  sống — demo không có đoạn này trong vùng trình phát. Sâu hơn: cơ chế
  nhúng iframe (`.khung-module` cao `calc(100vh - 220px)`, tối thiểu
  640px, thêm ở (a) qua `web/Doi-song.dc.html` + `tabNhungCua` trong
  `web/khung.js`) khác kiến trúc demo (trình phát là nội dung native
  của trang Đời sống, cuộn cùng trang, không phải iframe) — sửa triệt
  để là việc lớn hơn (d), ghi là lệch kiến trúc cần mảnh riêng, không
  sửa trong (d).
- **D8 (chưa xác minh):** Playlist/Queue/Loa & tivi/Cài đặt hiện là
  các section đầy đủ xếp chồng dưới lưới 2 cột (kèm form nhập/tạo
  playlist, form loa); ảnh demo chỉ thấy vùng trình phát + gợi ý tới
  thanh chip (phần dưới thanh chip không có trong ảnh) — không kết
  luận được các section dưới là sai hay đúng từ ảnh này; ghi là cần
  đối chiếu mã nguồn demo (vùng dưới thanh chip trong
  `Doi-song.dc.html`), không tự nhận sai.
- **(d) không sửa giao diện.** Các lệch D1–D5, D7 ghi vào đây để mảnh
  giao diện sau sửa (hoặc điều phối quyết); brief (d) là test + bảng +
  khôi phục hợp đồng backend, không tự sửa trang tab trong (d).

### 6B. Lệch c2a/dịch vụ cũ ĐÃ SỬA trong (d) (9 nhóm, đều có test khóa)

Vị trí: `modules/youtube/module.py` trừ khi ghi khác. Mỗi nhóm đều có
test (d) tương ứng; đỏ-trước-xanh xem mục 9.

1. **Mã lỗi đổi tên (NV301 gộp thành mã chung):** `_xac_thuc_muc_tieu`
   trả `invalid_target`/`invalid_source` cho mọi nguồn → khôi phục
   `_ma_loi_muc_tieu(source, ngu_canh)`: youtube →
   `invalid_youtube_target`, zing → `invalid_zing_target`, facebook →
   `invalid_facebook_target`, http → `invalid_http_audio_target`,
   nguồn lạ → `unsupported_session_source` (session) /
   `unsupported_stream_source` (stream, `_tao_luong` truyền
   `ngu_canh="stream"`). `_tao_phien` outputs →
   `invalid_output_entity_ids` (3 chỗ: `_tao_phien`, nhánh outputs,
   `_phat`); giới hạn tìm (`trich_xuat.py::_validated_query_and_limit`)
   `invalid_search_limit` → `invalid_search_query`. Bảng thông điệp
   tab (~dòng 615) thêm các mã mới. Giữ nguyên `invalid_target` ở 2
   chỗ biên: playlist rỗng sau chuẩn hoá (hang None + không mục hiện
   tại) và các passthrough `str(e) or "invalid_target"` (chỉ fallback
   khi mã nguồn rỗng — mã đúng đã đi từ nguồn).
2. **Health quảng cáo thiếu:** capabilities `[search, stream,
   playlists, history]` (thiếu "play"), sources `[youtube, zing]`
   (thiếu facebook dù module CÓ hỗ trợ facebook), playback_sources
   thiếu facebook → khôi phục đúng c2a: capabilities thêm `"play"`,
   sources `[youtube, zing, facebook]`, playback_sources `[youtube,
   zing, facebook, http]`.
3. **History thiếu `id`:** `_ghi_lich_su` chỉ ghi `{source, target,
   title}` → thêm `id = target` (mọi điểm gọi đều truyền target).
4. **Session item thiếu `artist`:** `_anh_xa_phien` chỉ có channel →
   item thêm `artist` = channel khi chưa có (chỉ ở tầng session, KHÔNG
   thêm vào kết quả tìm — đúng c2a: kết quả tìm chỉ có channel).
5. **Giới hạn tìm sai cả hai đầu:** `_validated_query_and_limit` mặc
   định max_length=500 cho mọi thứ (từ khoá quá lỏng, link quá chặt —
   link YouTube 501–2048 ký tự bị 400 oan) → nhánh search module quyết
   max_length theo query: chứa `"://"` → 2048, còn lại → 120 (đúng
   `MAX_QUERY_LENGTH`/`MAX_URL_LENGTH` của c2a). Tầng trich_xuat giữ
   mặc định 500 để khỏi mở rộng phạm vi (`search_zing` trực tiếp).
   Edge ghi chú: link không scheme dài >120 vẫn bị coi là từ khoá
   (giới hạn chấp nhận được).
6. **Stop revision-only so với BẤT KỲ phiên nào:** nhánh
   expected_revision không kèm session_id tìm phiên nào còn sống có
   revision khớp → dừng phiên đó → khôi phục đúng c2a: chỉ so với
   phiên HIỆN TẠI đang sống; revision cũ → `stopped False` + phiên
   mới hơn không bị dừng. Nhánh session_id + expected_revision của
   NV301 không đổi (test NV301 chỉ dùng dạng này).
7. **Mất lọc host YouTube:** `resolve_youtube_audio` không kiểm host
   (Facebook/Zing vẫn còn lọc) → khôi phục `YOUTUBE_STREAM_HOSTS =
   ("googlevideo.com",)` + kiểm qua `_host_la_cho_phep`, khác →
   `TrichXuatUnavailable("youtube_host_rejected")`. Không test cũ nào
   gọi trực tiếp `resolve_youtube_audio` nên sửa an toàn cho suite.
8. **Rơ-le tính ranh giới khúc sạch thành «đứt»:** bản module trước
   (d) THIẾU nhánh «đủ cả khúc đã xin thì mở khúc kế không tính thất
   bại» của ro_le cũ → mọi ranh giới khúc đều tốn 1 lần thất bại +
   backoff, luồng >5 khúc (>20 MiB với KHUC 4 MiB) sẽ raise
   `LoiNguonKhongCuuDuoc` dù thượng nguồn vẫn tốt → thêm biến
   `nhan_duoc` đếm byte phản hồi hiện tại; đủ khúc (`nhan_duoc >= den
   - tu + 1`) thì mở khúc kế KHÔNG tính thất bại, KHÔNG ngủ; chỉ khi
   thiếu mới raise `ConnectionError("thượng nguồn ngắt sớm")`.
9. **Mất `media_content_type` ở stream POST:** (e) đánh rơi khi chuyển
   sang vé lõi → khôi phục ở `_tao_luong` cả hai nhánh (http →
   "audio/mpeg", đã giải → content_type của nguồn).

### 6C. Giữ nguyên có lý do — KHÔNG phải sai (đừng sửa oan)

- Xác thực khoá khách lõi thay token tích hợp riêng (kiến trúc NV289
  đã chốt); vé ký lõi + 404 trống thay token payload.sig + 403
  (thiết kế chống liệt kê của NV277; tính chất bảo mật giữ nguyên:
  không vé đúng thì không luồng).
- Hậu tố Range → 206 byte cuối + Range hỏng → 416 (đúng RFC; quirk
  200-từ-đầu/400 của c2a chỉ là giữ đường cũ, không phải hợp đồng).
- Stop body rỗng → dừng hết (khớp c2a trường hợp không body + 1 phiên;
  đa phiên thì NV277 chọn dừng hết, đã ghi rõ).
- Outputs `["den-sai"]` được chấp nhận (mức thấp: module không kiểm
  định dạng thực thể).
- Session dừng rồi play lại → 404 không hồi sinh (hành vi NV301 đã
  chốt; c2a không có khái niệm phiên dừng vĩnh viễn này theo cùng
  cách).
- Mô hình đa phiên (mỗi nhóm loa một phiên) thay một phiên hiện tại
  duy nhất của c2a; phiên dừng giữ bản ghi cho tab; outputs phiên
  không sống → 200 stopped False (NV277, thân thiện tab).
- HEAD luồng trả Content-Length 0 (Starlette thân rỗng) thay tổng thăm
  dò — hạn chế tầng lõi (mục 4), không phải hành vi module.

### 6D. Điểm mở / chưa xác minh (ghi rõ, không đoán)

- c2a kiểm định dạng thực thể ở outputs ở mức nào — CHƯA xác minh
  được từ code đã đọc (mức thấp; (d) giữ hành vi chấp nhận).
- HA integration có rẽ nhánh theo mã lỗi/capabilities hay không —
  không có `custom_components/` trong clone c2a nên chưa kiểm được;
  đối chiếu dựa trên test hợp đồng của c2a.
- Demo D6 (sticky chip) và D8 (section dưới thanh chip) chưa xác minh
  từ ảnh tĩnh (xem 6A).

## 7. Test KHÔNG port được + lý do (không giấu)

- **Mục lục sidx MP4 để tua đúng ranh giới mảnh:** module chỉ có tua
  tỉ lệ (ước tính: chính xác với mp3 CBR, xấp xỉ với VBR/opus); port
  mục lục sidx của (c) **ĐÃ HOÃN, không có trong (d)**. Test tua của
  (d) assert tua tỉ lệ, không assert sidx.
- **Handler redirect urllib của Facebook (9 case):** `_XuLyChuyenHuongFb`
  + `_CHUYEN_HUONG_TOI_DA=5` đã bỏ; Facebook giờ giải qua yt-dlp.
  Phần bảo vệ còn lại là lọc host fbcdn + tìm Facebook chỉ nhận link
  (đã có test). Không tự viết lại handler urllib để «cho đủ test».
- **Token tích hợp + HMAC luồng riêng của cũ:** thay bằng khoá khách
  lõi + URL ký lõi (mục 4); test tương đương đã có ở
  `test_duong_module_nv277.py` (NV277/NV289), (d) chỉ port phần hợp
  đồng qua lõi với module youtube thật.
- **HLS `.m3u8` + redirect iOS 302, nguồn video youtube_video/
  facebook_video:** module chỉ làm tiếng, không làm hình.
- **Route quản trị `/api/youtube-phat/*` của c2a:** thuộc giao diện
  web c2a, web2api thay bằng tab module + thực thể HA.
- **Facebook `/share/v/`:** c2a `facebook_url_query` cũng KHÔNG nhận
  dạng này — parity, không phải thiếu.
- **Chạy lại test cũ nguyên dạng:** không làm được — test cũ import
  module cũ đã gỡ và chạy server FastAPI riêng của dịch vụ cũ. Port
  là viết lại theo khung mới, giữ ý nghĩa (mục 3).

## 8. Vấn đề mở đã biết

- **support.js VẪN THIẾU trên Giao main mới nhất 82d9ff46** (kiểm toàn
  bộ cây: `git ls-tree -r origin/main | grep -ci support` = 0; thư
  mục `inbox/tai-lieu/demo/` đủ 18 file: 10 `.dc.html` + `canvas.json`
  + `DOC-TRUOC.md` + 6 `ANH-DUNG-*.png`) dù DOC-TRUOC.md nói nó bắt
  buộc («without support.js it shows raw {{…}} text»). Demo chưa xem
  đúng được qua http.server + Chrome; cần gửi bổ sung để đối chiếu
  ảnh chụp thật sau khi dựng lại.
- NV304 nhắc `Doi-song-DUNG.png` nhưng file thực tế là
  `ANH-DUNG-Doi-song.png` (nhiều khả năng cùng một ảnh, khác tên) —
  cần xác nhận.
- (d) không sửa giao diện: các lệch D1–D5, D7 chờ mảnh giao diện sau
  hoặc điều phối quyết.

## 9. Kiểm chứng

- **File (d) mới: 76/76 xanh** (60 hàm + parametrize 17 route).
  Nhóm: hợp đồng 17, bài kế/tua 8, dung hạn 4, giới hạn 3, bảo mật 6,
  luồng 13, tìm kiếm 1, xác thực 2, smoke endpoint 1, khóa c2a mới 5.
- **Bộ liên quan 12 file: 174 passed** (NV277, NV301 giao diện/kiem_ha/
  loi/playlist, NV304 a/b/c/e, duong_module NV277, tab, (d)).
- **Đỏ-trước-xanh, đợt 1 (quan sát trực tiếp khi sửa):**
  media_content_type → KeyError trước, xanh sau; host YouTube lạ →
  không raise trước, raise sau; rơ-le ranh giới → backoff sai
  ([0.5,1,2,2] thay vì [0.5]) và raise ở offset 812 trước, xanh sau.
- **Đỏ-trước-xanh, đợt 2 (file (d) chạy trên code (e) sạch): 12 failed
  / 64 passed.** 12 đỏ khớp chính xác các hành vi đã khôi phục:
  health, search tham số (mã giới hạn), session lỗi (mã nguồn),
  outputs (mã), stream POST (KeyError media_content_type + mã),
  play (mã), resolve youtube chặn host, rơ-le cắt giữa khúc, rơ-le 3
  lần cắt, stop revision, history id + artist, link dài/từ khoá dài.
  64 xanh còn lại là hành vi vốn đã đúng ở (e). Trên code (d): 76/76.
- **Toàn suite** (cùng 8 file muse2api bỏ qua như NV300 bổ sung, do
  lỗi collect thiếu dep — giống hệt trên cả hai cây):
  cây (d) **158 failed / 6029 passed / 273 skipped / 31 xfailed /
  17 errors** (27:43); cây nền (e) sạch **158 failed / 5953 passed /
  273 skipped / 31 xfailed / 17 errors** (26:08). Failed/skipped/
  xfailed/errors giống hệt; passed tăng đúng 76 = số test (d) mới;
  danh sách FAILED ở nền (e) có đúng 158 dòng, **0 dòng nào nhắc
  youtube** — 158 lỗi là lỗi có sẵn từ nền, không lỗi nào do (d).
- **Bandit** trên 2 file nguồn sửa (`module.py`, `trich_xuat.py`):
  High 0, Medium 0, Low 0.
- **Patch áp sạch:** `git apply --check` trên cây (e) sạch (repo-nen,
  HEAD d52262d) — OK.
- **Quét patch/báo cáo:** không khoá/mật khẩu/token/cookie/email
  thật/IP thật. Test (d) chỉ dùng id video giả (`VIDEO_1`) và URL giả
  lập trong fake, không dùng dữ liệu thật.
- **Cạm bẫy đã gặp khi viết test (ghi để khỏi lặp lại):** script
  chuyển async→sync từng thay luôn `await _goi` bên trong `_tao_phien`
  → RuntimeError «asyncio.run() cannot be called from a running event
  loop» (đã sửa: giữ `await _goi` trong `_tao_phien`); `_tao_phien`
  với hàng đợi: mục tiêu phải nằm trong hàng (hoặc có `queue_index`)
  không thì hàng bị bỏ; `_anh_xa_phien` trả `session_id`, KHÔNG có
  khoá `id`; `tao_khoa` kiểm module tồn tại nên catalog khung lõi
  phải có "other"; RelayFake: hết kịch bản thì phục vụ mặc định,
  không lặp spec cuối (muốn lặp lỗi phải liệt kê đủ 5 spec); dữ liệu
  relay phải dài đúng `tong` không thì kiểm Content-Range luôn lệch;
  test tắt/ngắt giữa chừng cần KHUC=256 (không thì 1 khúc đã hết dữ
  liệu, không chứng minh được gì).

## 10. Giới hạn — điều phối / chủ máy cần biết

- **Chưa thử trên HA thật, chưa kiểm Chrome thật** (máy này không có
  Chrome): cần thử thật rằng bài Zing/Facebook phát được ra loa,
  nhập playlist Zing được, seek tua tới đúng vị trí; kiểm tab YouTube
  đã biến mất khỏi thanh Hệ thống, trình phát đã ở tab Đời sống, và
  ảnh 375px + 1280px so với ANH-DUNG-Doi-song.png.
- **Chưa đo:** sidx hoãn lại nên tua VBR/opus vẫn là ước tính tỉ lệ;
  độ trễ rơ-le không đo (test chỉ chứng minh offset/backoff đúng).
- **Thứ tự gộp bắt buộc: (a) → (b) → (c) → (e) → (d).** Patch (d) chỉ
  có nghĩa trên cây (e); đừng áp trực tiếp lên main chưa có (e).
- **Việc còn lại sau (d):** mảnh giao diện sửa D1–D5, D7 (hoặc điều
  phối quyết giữ/từ bỏ từng điểm); gửi bổ sung support.js rồi đối
  chiếu ảnh chụp thật; port sidx (đã hoãn từ (c)); kiểm thật trên
  HA/loa/Chrome sau khi gộp + dựng lại.
