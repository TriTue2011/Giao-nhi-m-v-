# NV301 mảnh lõi — phiên ngang dịch vụ cũ: KẾT QUẢ

Nộp tiếp lên nhánh `muse/nv301`, sau mảnh tab (không làm lại mảnh tab).
Nền: web2api main `8ef3ca9` + mảnh tab (commit `4582666`); mảnh này là
commit `156f5c2` trên cùng nhánh làm việc. Patch của mảnh
(`outbox/nv301-loi.patch`, 1396 dòng) là diff `4582666..156f5c2`, đã
kiểm áp sạch lên cây `4582666` bằng `git apply --check` (worktree tạm).

Chuẩn đối chiếu: mã dịch vụ cũ CÓ SẴN trong repo web2api tại
`dich-vu/youtube-phat/` (server.py, session.py, playlists.py, search.py
— trước đây tưởng không có trên máy, thực ra có). Mọi hình dạng dưới
đây đối chiếu trực tiếp với mã đó, không suy đoán.

## Đã làm (chỉ `modules/youtube/` + test)

**Siêu dữ liệu khi mở phiên** (`module.py: _tao_phien`, `_sieu_du_lieu`;
`trich_xuat.py: resolve_youtube_audio` trả thêm `channel`/`thumbnail`):
- Session POST và play trực tiếp đều tạo phiên có `item` chuẩn
  `{source, kind, id, url, title, artist, channel, album, thumbnail,
  duration, [media_content_type], [playlist_id]}`.
- Ưu tiên giá trị bên gọi đưa; thiếu title/duration thì hỏi YouTube một
  lượt giải âm thanh (qua semaphore như `_tao_luong`); hỏi hỏng thì giữ
  gợi ý, title rơi về id, ảnh YouTube rơi về `i.ytimg.com/.../hqdefault.jpg`
  (đúng quy ước dịch vụ cũ) — không bịa tên bài.
- Nguồn http: title từ tên tệp, artist «HTTP Audio», loại từ hậu tố.
  Nguồn facebook được nhận khi mở phiên (mã số hoặc link); giải luồng
  Facebook vẫn 502 như trước.

**Status đủ trường** (`integration/status`): trả đúng hình dạng dịch vụ
cũ — `success, api_version, app_version, state, item, session,
sessions, history_count` (giữ thêm `playlists_count`). Phiên trả
`session_id, revision, state, status, source, title, duration, position,
item, current_item, queue {index, items}, queue_index, playlist_id,
outputs, output_entity_ids, volume_level, auto_advance`. Không có phiên
đang chạy thì `session` là phiên «idle» (state idle, item None) thay vì
None như NV277 — HA đọc `session["item"]` không vỡ. `sessions` chỉ gồm
phiên còn sống, mới đổi nhất trước. Mọi đường trả phiên (session, play,
pause, next, prev, seek, outputs, stop) cùng hình dạng này.

**Next/prev + hàng đợi thật**:
- Phiên mang `queue` + `queue_index` + `playlist_id`. Thứ tự hàng đợi
  (theo dịch vụ cũ): hàng đợi bên gọi đưa → playlist theo `playlist_id`
  → hàng đợi phiên cũ cùng id → hàng đợi tìm gần nhất chứa mục tiêu →
  một bài duy nhất. Mục tiêu không nằm trong hàng đợi đã chọn thì hàng
  đợi đó bị bỏ, rơi xuống tầng sau; không mục tiêu thì phát bài đầu
  (phát playlist). Link playlist YouTube làm `target` được hiểu là
  `playlist_id`; link xem có `list=` thì giữ bài đó và ghi playlist_id.
- Next/prev chuyển `queue_index`, đặt lại `position = 0`, trạng thái
  playing, ghi lịch sử bài mới. Ở biên: `409 queue_end` / `409
  queue_start` (như dịch vụ cũ, không ở yên như NV277). Không còn phiên
  → `404 session_not_found`. Khoá tuần tự `_khoa` quanh đổi trạng thái.
- Một loa chỉ thuộc một phiên (loa mới vào phiên này thì rời phiên cũ;
  phiên hết loa thì kết thúc); tối đa 32 phiên, vượt thì đuổi cũ nhất.
- `integration/pause` MỚI (dịch vụ cũ không có endpoint pause — HA tạm
  dừng qua media_player): giữ phiên, trạng thái paused; play tiếp tục.
- `integration/seek` nhận cả `giay` (cũ) lẫn `position` (NV277), kẹp
  theo thời lượng, sai → `400 invalid_seek_position`; `seek_url` trả
  None có lý do (xem «chưa ngang» dưới).
- `integration/session/outputs` nhận cả `outputs` lẫn
  `output_entity_ids`; rỗng → dừng phiên (như dịch vụ cũ).
- `integration/stop` theo `session_id` / `expected_revision` (sai
  revision → `200 {stopped: False}`); body rỗng vẫn dừng hết (nới hơn
  cũ, giữ hành vi NV277). Trả thêm `state` + `session`.
- Mã HTTP theo dịch vụ cũ: session POST và create playlist trả **200**
  (không còn 201) — vì tích hợp HA kiểu cũ kiểm `ma == 200`.
- `integration/search` trả cả `results` (NV277) lẫn `items` (dịch vụ cũ)
  cùng danh sách đã chuẩn hoá (có `channel`/`thumbnail`/`kind`) +
  `total`; ghi nhớ hàng đợi tìm (mỗi nguồn tối đa 30). Link YouTube
  dán vào ô tìm: video → một mục (giải siêu dữ liệu); playlist → các
  bài trong playlist. Facebook chỉ nhận link (mã số/link): chữ thường
  → `400 invalid_search_query` (dịch vụ cũ không có đường tìm Facebook).
- `integration/history` trả thêm `items` + `total` (hình dạng cũ) bên
  cạnh `history`. Lịch sử ghi khi mở phiên (record), phát bài mới và
  next/prev; resume không ghi lại (tránh đếm đôi khi HA record rồi play).

## Test

- Mới `test/test_module_youtube_nv301_loi.py`: **12/12 xanh**.
  Đỏ-trước-xanh đã kiểm bằng stash: chưa có sửa thì **12 failed**, có
  sửa thì 12 passed (stash pop sạch, không mất thay đổi).
- Cập nhật có chủ đích `test/test_module_youtube_nv277.py` (4 chỗ):
  session POST 201→200, create playlist 201→200, status lúc chưa phát
  và sau stop: `session is None` → phiên «idle». Lý do ghi trong test.
- Liên quan chạy xanh: nv277, nv301-loi, tab, duong_module_nv277,
  youtube-phat (trừ 1), nv153c_youtube_phat_web, kham_pha,
  hang_manifest — tổng **92 passed** trong lượt chạy gộp (16 passed
  riêng kham_pha + hang_manifest).
- Đỏ có sẵn KHÔNG do mảnh này: `test_module_youtube_phat.py::
  test_loai_thu_tu_la_so_nguyen_khong_trung` — trùng `loai_thu_tu` 47
  giữa youtube-phat và nha-tien-ich; đã kiểm vẫn đỏ y hệt trên cây
  chưa có sửa (stash). Mảnh này không đụng manifest nào.
- Bandit trên 2 file sửa: sạch. README vẫn **414 dòng** (trần 415),
  không sửa README. Patch không chứa khoá/token/cookie/email/IP thật
  (giá trị test đều giả).

## Chưa ngang dịch vụ cũ / chưa kiểm (ghi rõ, không bịa)

- Giải luồng Zing/Facebook chưa chuyển (502 rõ) — như NV277.
- `seek_url` trả None: dịch vụ cũ tự tính từ mục lục sidx (`?t=`) để
  loa nhảy tới; rơ-le vé của module không có sidx và vé không mang vị
  trí bắt đầu nên không bịa URL — loa tua bằng Range trên URL luồng.
- Stop body rỗng vẫn dừng hết (nới hơn cũ: cũ đòi revision hoặc
  session_id, không thì 400).
- `session_id` bên gọi đưa không ép khuôn `[a-z0-9_-]{1,40}` của cũ
  (module tự sinh token_urlsafe có chữ hoa).
- Nhập playlist từ link/mã chia sẻ và giao diện đầy đủ: 2 mảnh tiếp
  theo của NV301, chưa làm trong mảnh này.
- **Chưa thử với loa/HA thật** (máy làm việc không có Chrome thật,
  không có YouTube/loa/HA thật): sau khi gộp, cần thử status/next/prev
  từ tích hợp HA thật và đối chiếu thẻ «Đang phát».
