# NV307 — R1: PHÁT NHẠC VÀ TTS TRÊN CÙNG MỘT ĐƯỜNG (TRỘN TRONG TÍCH HỢP) — BÁO CÁO

## KẾT QUẢ

**Xong, đã đẩy nhánh Giao `muse/nv307`** (tip commit ghi ở cuối báo cáo nộp; kiểm
`ls-remote` sau khi đẩy). Patch `outbox/nv307.patch` (971 dòng, 12 file,
+739/−7) áp sạch lên R1 main `b2c5096` (0.13.0) và đã kiểm lại trên cây mới
clone từ main (18/18 test xanh).

Nhạc đang phát qua AirPlay thì tin báo (TTS/announce) được **trộn vào chính
luồng PCM của phiên nhạc đó**: một phiên RAOP duy nhất, nhạc tự hạ **12 dB
bằng phần mềm** (không đổi âm lượng loa), không tạm dừng, không đổi URI,
không next bài, hết tin nhạc về mức cũ mượt (ramp 150 ms). Tin lỗi không làm
đứt nhạc, không làm nhạc phát lại.

- Tuỳ chọn mới: **«Trộn tin báo vào luồng nhạc (một đường AirPlay)»**
  (`tron_tin_airplay`), có trên cả hộp tuỳ chọn và thẻ Cài đặt (công tắc
  `switch.r1_tron_tin`). **Mặc định TẮT.**
- Khi bật cùng `tts_song_song_airplay` (NV287/NV303) thì **đường trộn THẮNG**
  khi nhạc ở AirPlay — một đường tốt hơn hai đường song song, và không phụ
  thuộc vào việc loa có trộn được DLNA + RAOP hay không (điểm NV303 còn
  chưa đo).
- `assist_satellite.py` **không sửa**. Các đường NV287/NV292/NV303 không đổi
  hành vi (test của chúng vẫn xanh, xem mục Test).
- **Chưa thử trên loa/HA thật** (xem mục «Chưa thử thật» ở cuối).

## PHÂN TÍCH CHATGPT2API TRƯỚC KHI LÀM (luật 16:11 — bắt buộc)

Repo đối chiếu: `TriTue2011/chatgpt2api`, chỉ clone đọc, không sửa.
Đã phân tích:

- Grep toàn repo `airplay|raop|amix|sidechain` (mọi file `.py`):
  **không có** bộ gửi AirPlay/RAOP, không có trộn PCM, không có
  `amix`/`sidechaincompress` cho âm thanh. Hit duy nhất là
  `services/video_dub.py` (ghép voiceover vào video bằng ffmpeg — việc
  khác hẳn, không liên quan loa).
- `services/voice/announce.py` (`giu_cho`, `phat_cho`, `_run`,
  `_tra_am_luong_sau_khi_phat`): tin báo của c2a là **phát nối tiếp từng
  lượt + vặn âm lượng loa rồi trả mức cũ** — tức mẫu «đường thường +
  ducking bằng âm lượng» chứ không phải trộn.
- `services/voice/speakers.py` (`_play_cast`, `_play_dlna`, `set_volume`,
  `get_volume`, `KINDS = ("cast", "dlna", "ha", "r1")`): mỗi loại loa có
  một lệnh phát riêng, không có đường nào cộng hai luồng PCM lại.
- `services/voice/__init__.py` (`play_on`, `play_text_on`): điều phối phát
  theo từng loa, không trộn.
- ffmpeg trong c2a chỉ dùng cho camera/video (`api/camera.py`,
  `services/camera_nha.py`, `services/video_dub.py`) — không dùng để trộn
  tiếng cho loa.

**Kết luận đối chiếu: phần này KHÔNG CÓ tương đương trong chatgpt2api.**
Trộn trong tích hợp chỉ khả thi vì R1 có bộ gửi RAOP riêng (`airplay.py`,
ffmpeg giải mã trên máy HA, PCM đưa vào tay tích hợp) — đúng tiền đề mà
file NV307 nêu. Thiết kế vì vậy bám theo `airplay.py`/`media_player.py`
của R1, không port gì từ c2a. Khác c2a ở đây là khác có căn cứ (đường
riêng của R1), không phải sai — và đã có test chứng minh hành vi (theo
tinh thần đính chính 16:58: khác ≠ sai, test mới là chuẩn).

## CƠ CHẾ TRỘN (đọc `airplay.py` / `media_player.py` / `playback.py` trước)

- Luồng PCM hiện tại: `media_player._phat_airplay` → `_mo_airplay` mở
  `PhienAirPlay` với nguồn `tao_nguon(url, bat_dau)` (ffmpeg giải mã mọi
  định dạng ra PCM16 LE 44,1 kHz stereo). `PhienAirPlay._phat` kéo từng
  khúc, chia gói 352 khung (1408 byte, ~8 ms) và gửi đúng nhịp thời gian
  thật (sớm `DAN_DAU` 0,25 s; loa đệm `Audio-Latency` ~2 s rồi mới phát).
  Nhịp này **không đổi**: bộ trộn chỉ thay khúc PCM đưa vào, không đụng
  tới vòng gửi gói, đồng bộ, hay gửi lại của RAOP.
- Điểm trộn: file mới `custom_components/r1_speaker/tron_tin.py`,
  class `TronTin`. `_mo_airplay` luôn bọc nguồn nhạc bằng một `TronTin`
  (kể cả khi công tắc TẮT — lúc đó nó chuyển tiếp nguyên khúc, không tính
  toán đáng kể) để bật công tắc giữa chừng vẫn trộn ngay mà không phải
  phát lại nhạc. Quyết định trộn nằm ở lúc có tin, không nằm ở lúc mở
  phiên.
- Khi có tin (`async_play_media`, nhánh NV307 đặt TRƯỚC nhánh NV303):
  điều kiện là công tắc bật + nhạc đang phát qua AirPlay + bộ trộn của
  phiên còn sống. Tin được giải mã bằng **một tiến trình ffmpeg thêm**
  (`tao_nguon` như mọi nguồn AirPlay khác) rồi bơm nền vào hàng đợi có
  trần (32 khúc ≈ 4 giây tiếng, ≈ 720 KB). Bộ trộn chỉ lấy những gì đã có
  sẵn trong hàng đợi — **không bao giờ chờ tin mà làm khựng nhạc**:
  tin chậm/chưa tới thì khúc đó chỉ có nhạc (đang hạ), tin lỗi thì nhạc
  tiếp tục ở mức cũ.
- Cộng mẫu trong Python (không dùng `amix`/`sidechaincompress` của
  ffmpeg): trộn trong Python mới chen tin vào đúng luồng nhạc đang chạy
  mà không mở lại phiên; ffmpeg thứ hai chỉ giải mã tin, không trộn.
  Tổng kẹp trong [-32768, 32767] nên biên độ tổng không vượt 0 dBFS.
- Hết tin: nhạc ramp về mức cũ trong 150 ms ngay trong các khúc kế;
  watcher nền (`_theo_doi_tin_tron`) báo `talk.announce_done()` khi mức
  đã về (hoặc khi tin lỗi/bị thay/hết hạn `ANNOUNCE_MAX` — hết hạn thì
  huỷ tin chứ không dừng nhạc). Tin mới thay tin cũ: bơm cũ bị huỷ,
  watcher cũ được báo xong ngay, không kẹt.
- Byte lẻ cuối khúc (nửa khung) được giữ sang khúc sau, không mất tiếng.
- Tua (seek) = mở phiên AirPlay mới với bộ trộn mới (đường cũ); tin đang
  trộn theo phiên cũ tự kết thúc cùng phiên.

## MỨC HẠ N dB VÀ CÁCH CHỌN

- **N = 12 dB**, hệ số biên độ `10^(-12/20) ≈ 0,2512`, mã cứng có tên
  (`tron_tin.HA_DB`) kèm lý do trong code. 12 dB là mức ducking phát
  thanh thường dùng (10–15 dB): lời rõ hẳn lên mà nhạc vẫn nghe nền,
  và với nhạc đã hạ 12 dB thì tổng nhạc + tin hiếm khi chạm trần kẹp.
- Ramp vào/ra **150 ms** tuyến tính theo từng khung (gain dùng trước rồi
  mới bước, hết ramp gắn đúng đích để không tích sai số float). 150 ms
  đủ ngắn để tin vào nhanh, đủ dài để không nghe «cụp».
- Vào/ra tin ở mức bộ trộn ≤ một khúc ffmpeg (~128 ms, khúc
  `DOC_FFMPEG` 22528 byte) + ramp 150 ms ≈ **278 ms**. Con số này KHÔNG
  tính thời gian tổng hợp TTS, ffmpeg mở nguồn, và bộ đệm ~2 giây của
  loa — những thứ này cũng đúng với mọi đường AirPlay khác (xem «Chưa
  thử thật»).

## CÁC FILE ĐỔI (patch trên R1 main b2c5096)

- `custom_components/r1_speaker/tron_tin.py` (MỚI, 266 dòng): `TronTin`
  + hàm thuần `tron_khung` (để test trực tiếp).
- `custom_components/r1_speaker/media_player.py`: bọc nguồn AirPlay bằng
  `TronTin` ở `_mo_airplay`; nhánh NV307 trước NV303 trong
  `async_play_media`; `_tin_co_the_tron` / `_tin_tron` /
  `_theo_doi_tin_tron`; huỷ watcher khi gỡ thực thể.
- `const.py` (`CONF_TRON_TIN = "tron_tin_airplay"`, mặc định `False`),
  `settings.py` (`tron_tin(entry)`), `config_flow.py` (ô tuỳ chọn),
  `thuc_the_tuy_chon.py` (công tắc `tron_tin` → `switch.r1_tron_tin`),
  `strings.json` + `translations/en.json` + `translations/vi.json`
  (tên công tắc + mô tả tuỳ chọn), `docs/CAI-DAT-CHI-TIET.md` (1 dòng).
- `tests/test_nv307_tron_tin.py` (MỚI) + `tests/test_tuy_chon.py`
  (cập nhật danh sách trường form đúng lệ NV287/NV292: thêm
  `tron_tin_airplay` — tập trường vẫn liệt kê chính xác, không nới lỏng).
- Không sửa `assist_satellite.py`, `airplay.py`, `giu_nhac.py`,
  `playback.py`, `dmr.py`.

## TEST

Chạy bằng venv test của NV306 (`~/workspace/nv306/.venv`, HA + pytest 9).
Đỏ-trước-xanh: test mới chạy lần đầu trên mã chưa sửa → lỗi collection
(thiếu module `tron_tin`); sau khi viết mã thì xanh.

**Test mới `tests/test_nv307_tron_tin.py`: 17/17 xanh**, hai tầng:

- Tầng trộn (không cần HA, 12 test): cộng có kẹp 0 dBFS; tin ngắn hơn
  thì đuôi chỉ còn nhạc đã hạ; byte lẻ giữ sang khúc sau; nhạc liên tục
  đúng số khúc vào = số khúc ra; ramp xuống/lên đơn điệu, đúng -12 dB
  sau 150 ms; tin có mặt ngay ở khúc nhạc kế (vào/ra ≤ ~300 ms ở mức
  bộ trộn); tin lỗi (ffmpeg giả ném lỗi giữa chừng) không đứt nhạc và
  vẫn báo xong; tin mới thay tin cũ không chồng nhau; hàng đợi có trần
  32 khúc, bơm được dọn (không rò tác vụ); chen tin khi chưa có luồng
  trả None.
- Tầng thực thể (renderer DLNA giả + RAOP giả + nguồn giả khúc NHỎ
  8 gói/khúc để bộ trộn kịp trộn ngay trong lúc test — nguồn NV287 trả
  một khúc khổng lồ nên `_phat` phải phát hết khúc đó mới kéo khúc kế,
  không quan sát được trộn; 5 test): tin trộn thì đúng một phiên RAOP
  (không RECORD mới, không FLUSH/TEARDOWN), không đụng DLNA, thực thể
  vẫn `playing`/`duong_phat=airplay`, không idle_reason, tin chỉ giải mã
  một lần, nhạc không phát lại; công tắc TẮT thì tin đi đường ngược NV303
  như cũ; nhạc DLNA + công tắc bật vẫn đi NV287 như cũ (không có bộ
  trộn); tin lỗi thì nhạc không đứt, không phát lại, vẫn báo xong;
  công tắc mặc định TẮT, bật/tắt ghi đúng `entry.options` (về mặc định
  thì khoá biến mất như các công tắc khác).

**Liên quan: 90 passed / 14 failed** ở lượt chạy tập hẹp (NV287, NV303,
AirPlay song song, NV302, tuỳ chọn) — 14 lỗi gồm 1 lỗi form tuỳ chọn
(đã sửa bằng cách cập nhật test như trên) và 13 lỗi AirPlay/DMR do
sandbox chặn UDP (xem dưới).

**Toàn suite đối chiếu nền sạch** (R1 main b2c5096, cùng máy, cùng venv):

- Nền sạch (stash toàn bộ patch): **17 failed, 823 passed, 12 skipped.**
- Đã sửa (patch NV307): **21 failed, 836 passed, 12 skipped.**
- Tập lỗi chung: 15 test (7 `test_airplay.py` + 6
  `test_airplay_song_song.py` + 1 `test_dmr.py` + 1 `test_r1den`).
  Chênh lệch chỉ nằm ở `test_r1den_chay_that.py` (đèn giả chạy script
  shell có timeout): nền sạch lỗi 2 test, đã sửa lỗi 6 test, **tập
  khác nhau giữa các lần chạy** — chạy riêng file này trên mã đã sửa
  lại lỗi 3 test khác nữa (1 trùng phía đã sửa, 2 trùng phía nền sạch).
  Đây là flake tải/timeout của file đèn (log nền sạch tự ghi
  `TimeoutExpired` của script đèn giả), không phải hồi quy: patch
  không đụng code đèn, và không có test NV307/NV287/NV303/NV302/tuỳ
  chọn nào lỗi ở lượt đã sửa. 836 − 823 = 13 passed tăng thêm = 17 test
  mới − 4 test đèn flake đổi chiều (khớp đúng số học).
- Bandit trên các file đổi: High 0, Medium 0; Low 1 duy nhất là sẵn có
  ở `config_flow.py:64` (không do patch). Quét bí mật: sạch (test chỉ
  dùng địa chỉ giả `*.example`, không token/IP/email thật).
- Kiểm trên cây mới: patch áp sạch lên bản clone mới từ main b2c5096,
  chạy `test_nv307_tron_tin.py` + `test_form_co_du_truong`: **18/18
  xanh**.

## GỘP VỚI NV306

Patch này làm trực tiếp trên R1 main b2c5096, không phụ thuộc NV306
(chưa gộp). So với `nv306.patch`: chỉ chồng **1 file docs**
(`docs/CAI-DAT-CHI-TIET.md`, hai bên thêm dòng ở mục khác nhau —
điều phối gộp tay 1 dòng nếu `git apply` báo xung đột ngữ cảnh);
mọi file code đều rời nhau nên thứ tự gộp NV306/NV307 không ảnh hưởng
code.

## CHƯA THỬ THẬT (cần vòng lặp với chủ máy sau khi gộp)

- **Chưa thử trên loa/HA thật.** Đặc biệt cần nghe thử: nhạc có hạ đúng
  12 dB và về mức cũ mượt không; lời có rõ không; có méo/kẹp nghe được
  khi nhạc + tin cùng đỉnh không; độ trễ từ lúc gọi TTS tới lúc nghe
  thấy tin (gồm tổng hợp TTS + ffmpeg + đệm loa ~2 s); đồng bộ có trôi
  khi tin dài không; và trường hợp tin tới đúng lúc nhạc tạm dừng rồi
  phát tiếp (bơm tin đầy hàng đợi rồi chờ — thiết kế là chờ, không tràn,
  nhưng chưa nghe thử).
- Chưa kiểm Chrome thật cho công tắc mới trên thẻ (tên/mô tả đã có đủ
  3 file dịch; thẻ dùng thực thể chuẩn như các công tắc khác).
- Chưa đo trên loa trộn DLNA + RAOP — nhưng đường trộn này chính là
  cách **tránh** câu hỏi đó (chỉ một đường RAOP), nên sau khi nghe thử
  đường trộn, NV303 có thể giữ làm đường dự phòng thay vì đường chính
  khi nhạc ở AirPlay.

## XÁC MINH NỘP

- Nhánh Giao: `muse/nv307` (chỉ nhánh này, không main, không force-push).
  Tip chốt của nhánh được ghi trong tin báo kèm theo sau khi kiểm
  `ls-remote` (file này không tự ghi tip của chính nó để tránh lệch như
  NV303 trước đây).
- File nộp: `outbox/nv307.patch` + `outbox/nv307-bao-cao.md` (báo cáo này).
- Nền nộp: R1 main `b2c5096`, Giao main `82d9ff46` lúc đẩy.
