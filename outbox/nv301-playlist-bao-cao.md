# NV301 mảnh playlist — nhập từ link/mã chia sẻ: KẾT QUẢ

Nộp tiếp lên nhánh `muse/nv301`, sau mảnh lõi (không làm lại mảnh tab,
mảnh lõi). Nền: mảnh lõi commit `156f5c2`; mảnh này là commit `dc8b3e8`
trên cùng nhánh làm việc. Patch của mảnh (`outbox/nv301-playlist.patch`,
632 dòng) là diff `156f5c2..dc8b3e8`, đã kiểm áp sạch lên cây `156f5c2`
bằng `git apply --check` (worktree tạm).

Chuẩn đối chiếu: `dich-vu/youtube-phat/playlists.py` và
`playlist_action` trong `dich_vu.py` của dịch vụ cũ (có sẵn trong repo).

## Đã làm (chỉ `modules/youtube/module.py` + test)

**Import playlist** (`integration/playlists` POST, action `import` với
`text`, tên ghi đè tùy chọn qua `name`):
- Mã chia sẻ `TTPL1.`: giải đúng định dạng dịch vụ cũ —
  base64url(zlib(JSON `{n: tên, i: [[source, id, url, title, channel,
  duration, thumbnail], ...]}`)), kèm trần (mã 300.000 ký tự, JSON
  2.000.000 byte, 500 bài, tên 80 ký tự). Mã tạo ở dịch vụ cũ mở được
  ở module và ngược lại (test dựng/giải mã độc lập bằng zlib/base64,
  không qua hàm của module).
- Link playlist YouTube: trang `/playlist` hoặc link xem có `list=`
  (đúng `youtube_playlist_id` của cũ) → lấy qua yt-dlp flat (thư viện,
  không chạy tiến trình con), tối đa 500 bài. Playlist nhập về phát
  được ngay qua `playlist_id` (nối mảnh lõi: hàng đợi + next/prev).
- Mã lỗi rõ, không tạo playlist rỗng giả: link lạ →
  `400 invalid_playlist_link`; mã hỏng → `400 invalid_share_code`;
  playlist lấy về rỗng → `400 playlist_empty`; lấy playlist hỏng (kể
  cả hết chỗ trích xuất) → `502 playlist_unavailable`; link
  album/playlist Zing → `502 playlist_unavailable` (dịch vụ cũ lấy qua
  API web có khoá ký riêng, module không có khoá đó — xem «chưa ngang»).
- Import dạng cũ (`playlists`, thay toàn bộ kho, hành vi NV277) vẫn giữ
  khi body không có `text`.

**Export** (action `export`): trả `code` là mã `TTPL1.` của playlist
(trước đây chỉ trả lại danh sách, không có mã). Mã export giải lại
được đúng tên/bài bằng zlib/base64 độc lập.

**Create/add chuẩn hoá** (như `PlaylistStore` của cũ): mục lưu vào kho
giờ qua `_chuan_hoa_muc` (id đúng khuôn từng nguồn, URL chuẩn, channel
từ channel/artist, thời lượng số), khử trùng theo (source, id), trần
500 bài/playlist và 100 playlist (`400 playlist_full` /
`400 too_many_playlists`). Create nhận thêm `items`; add nhận cả một
`item` (sai → `400 invalid_item`) lẫn danh sách `items` (bỏ mục sai,
trả `added`). Mục cũ không có `source` vẫn đọc được: suy ra YouTube
khi id 11 ký tự hoặc link YouTube (để kho thời NV277 không vỡ — chính
là chỗ test NV277 `test_tich_hop_playlists_va_stream` từng đỏ khi mảnh
này mới làm chặt `add`; đã sửa theo hướng suy luận này thay vì sửa test).

**Remove/move theo chỉ số kiểu cũ**: `remove {index}` / `move
{from, to}` (nhận cả `index` thay `from`), sai kiểu/vượt biên →
`400 invalid_playlist_index`. Dạng NV277 (`item_id`) vẫn giữ cho remove.
Rename/delete nhận cả `playlist_id` lẫn `id` (kiểu cũ).

## Test

- Mới `test/test_module_youtube_nv301_playlist.py`: **8/8 xanh**.
  Đỏ-trước-xanh đã kiểm bằng stash: chưa có sửa thì **7 failed**
  (1 passed là import dạng cũ vốn đã có sẵn), có sửa thì 8 passed.
- Bộ liên quan sau khi sửa suy luận source: nv277, nv301-loi,
  nv301-playlist, tab, duong_module_nv277 — **56 passed**.
- Bandit trên file sửa: sạch. README vẫn **414 dòng** (trần 415).
  Patch không chứa khoá/token/cookie/email/IP thật.

## Chưa ngang / chưa kiểm (ghi rõ, không bịa)

- Nhập album/playlist Zing: 502 `playlist_unavailable` — cần khoá API
  web Zing (ký HMAC theo cookie web) như dịch vụ cũ; module không có
  và không tự xin khoá.
- Giao diện đầy đủ: mảnh tiếp theo của NV301, chưa làm trong mảnh này.
- **Chưa thử với loa/HA thật.**
