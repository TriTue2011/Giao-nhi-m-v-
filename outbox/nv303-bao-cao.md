# KẾT QUẢ — NV303: tin báo (TTS) đi đường ngược với nhạc

**Chưa thử trên loa thật.** Nối tiếp NV287: nhạc đang ở AirPlay thì tin báo đi DLNA song song (không tạm dừng nhạc, không đụng phiên AirPlay); nhạc ở DLNA thì tin đi AirPlay song song như NV287 đã làm. Cùng một công tắc, đổi tên cho đúng nghĩa hai chiều, mặc định TẮT.

## Nộp

- Nhánh Giao: `muse/nv303` (xem mục «Xác minh nộp» cuối báo cáo).
- Patch: `outbox/nv303.patch` (678 dòng, 12 file, 440 thêm / 30 bớt, áp sạch lên cây nền đã kiểm bằng `git apply --check` trên worktree nền sạch).
- Báo cáo này: `outbox/nv303-bao-cao.md`.
- Không đẩy gì lên repo loa trực tiếp, không force-push, không đụng main nào.
- File nhiệm vụ kiểm lại lúc nộp: Giao main `ac3d9350`, `inbox/NV303.md` không đổi so với bản đọc lúc bắt đầu (đã đối chiếu bằng `diff` với `origin/main`).

## Nền và thứ tự gộp — DELTA, không phải trực tiếp lên main

- R1 main lúc làm vẫn là `2e0c913` (v0.12.0). NV288, NV302, NV292 đều **chưa** vào R1 main (điều phối báo đang tích hợp vào R1 0.13.0).
- Patch này là **DELTA trên cây đã có NV288 + NV302** (cây nền commit `38dc516` trong workdir, = R1 main `2e0c913` + `nv288.patch` + `nv302.patch`, áp theo đúng thứ tự đó; NV302 không áp được lên main sạch, đúng như báo cáo NV302 đã ghi).
- **Thứ tự gộp: NV288 → NV302 → NV303.** Không làm lại NV288/NV302 trong patch này.
- NV292: không làm lại, không đụng. NV292 không chạm các file chính của NV303 (`media_player.py`, `giu_nhac.py`, thẻ JS), nhưng **chung 4 file cần điều phối xem tay khi gộp**: `strings.json`, `translations/en.json`, `translations/vi.json` (NV292 thêm mục công tắc kênh, NV303 đổi tên mục `tts_song_song` + mô tả tuỳ chọn — khác vùng, khác mục) và `docs/CAI-DAT-CHI-TIET.md` (NV292 thêm 1 dòng, NV303 sửa 1 dòng khác). Ngoài 4 file đó, NV292 gộp độc lập với NV303.
- Lưu ý thứ tự thực tế lệch file: file NV303 ghi `NV288+NV302 → NV303 → NV291 → NV292`, nhưng NV292 đã nộp trước NV303 (nhánh `muse/nv292`, 14:25 ngày 03/11) theo quyết chạy song song của người dùng. NV291 tới sau NV303, phần nhãn của NV291 đã xong trong NV292 nên NV291 chỉ còn thẻ Lovelace + rà soát chỗ mở phiên — không làm trong lượt này.
- Workdir riêng `~/workspace/nv303/` (clone R1 tại `r1/`, clone Giao tại `giao/`), nhánh làm việc local `nv303-lam-viec` (không đẩy lên repo loa). Không dùng lại workdir/clone của NV300 bổ sung, NV292 hay NV302/NV288.

## Đã làm

- **Chiều ngược trong `media_player.py`** (đối xứng nhánh NV287):
  - Điều kiện mới `_tin_co_the_dlna_song_song()`: nhạc đang phát qua AirPlay (`_duong == "airplay"` và trạng thái đang phát) thì tin mới đi DLNA song song được.
  - `_bat_dau_tin_dlna()`: giải địa chỉ tin, tin mới thay tin cũ, bật DLNA nếu chưa bật (`set_dlna_open`), chờ renderer lên (`DLNA_READY_TIMEOUT`), phát bằng `_dmr.async_phat`, rồi chờ renderer thật sự phát bằng cách hỏi thẳng `_dmr.async_doc()` trong `ANNOUNCE_START_WAIT` (6 giây). **Không dùng `_phat_dlna`** (nó dừng AirPlay trước rồi mới phát DLNA) và **không đụng `_ap`/`_duong`/`_uri`/`_ly_do`/trạng thái thực thể** — trạng thái đó vẫn là nhạc AirPlay.
  - `_theo_doi_tin_dlna(giu)`: chờ tin DLNA xong bằng chính trạng thái DLNA (hỏi thẳng `_dmr`, không qua `_doc()`/`_ap_dung` — cổng AirPlay chặn hỏi DLNA để khỏi đè trạng thái nhạc thật); hết hạn `ANNOUNCE_MAX` (120 giây) thì dừng renderer; cuối cùng luôn báo vệ tinh (`announce_done`) và nhả lượt giữ.
  - Lỗi hoặc không bắt đầu được (renderer từ chối lệnh, mãi không phát, hỏi hỏng): dừng renderer dọn sạch rồi **về đường thường** đúng mẫu NV287 (nhả lượt giữ duck, giữ lại kiểu tạm dừng, phát tin, khôi phục).
  - `_dung_tin_dlna()`: tin mới thay tin cũ, người dùng Stop, phát nhạc/tin mới — huỷ tác vụ theo dõi (finally của nó nhả lượt giữ + báo vệ tinh) rồi tắt renderer DLNA. Gọi thêm trong `async_media_stop` (sau `_dung_tin_song_song`) và đầu `_phat` (nhạc/tin mới thay tin đang nói); huỷ tác vụ trong `_huy_airplay` khi thực thể bị gỡ.
- **Chống vòng lặp (NV303 mục 3)**: trong lúc tin DLNA còn đang chạy, renderer về idle được khai `idle_reason=dang_giu` (điều kiện `_ap_dung` mở rộng thêm cờ `_tin_dlna_dang_chay`), không phải `finished` — bộ điều khiển đọc `finished` là sang bài kế. Cần cờ riêng vì lượt giữ lúc này là duck (nhạc không tạm dừng) nên `se_phat_lai` của NV287 sai ở đây. Ghi chú: phiên AirPlay hết thật giữa lúc tin đang nói vẫn khai `finished` ở đường `_chay_ap` — đó là nhạc hết thật, không phải vòng lặp, nên không đổi đường đó.
- **Ducking cả hai chiều**: dùng đúng `hold(duck=True)` sẵn có của NV287 (không sửa `giu_nhac.py`): nhạc AirPlay nhỏ đi `ha_nhac_nac` nấc trong lúc tin DLNA nói, trả đúng mức cũ khi bên cuối cùng nhả, kể cả khi tin lỗi; không đọc được mức cũ thì về tạm dừng như cũ.
- **Đổi tên công tắc cho đúng nghĩa** (giữ nguyên khoá tuỳ chọn `tts_song_song_airplay` và translation key `tts_song_song` để khỏi vỡ cấu hình/thực thể cũ): tên hiển thị thành «Tin báo đi đường ngược với nhạc» / "Announcements take the opposite path from music" (switch, `strings.json`, `translations/vi.json`, `translations/en.json`, thẻ JS); mô tả tuỳ chọn viết lại cho cả hai chiều; thẻ JS ghi rõ «Nhạc AirPlay thì tin qua DLNA và ngược lại» (cả vi + en, đúng NV303 mục 4).
- **Tài liệu**: `docs/PHAT-RA-LOA.md` thêm hàng A2 (chiều DLNA song song, cách theo dõi, cách chống vòng lặp); `docs/CAI-DAT-CHI-TIET.md` sửa hàng công tắc theo tên mới.
- **Không đụng**: `assist_satellite.py`, giao thức phía loa (APK), `giu_nhac.py`, `intercom.py`, `playback.py`, `mic.py`; không thêm phụ thuộc.

## Kiểm chứng

- **Đỏ-trước-xanh**: test mới chạy trên code chưa sửa: 4 fail đúng các test hành vi mới (tin DLNA, Stop, ducking, chống vòng lặp), 3 test đường thường/fallback vẫn xanh (chúng là hành vi cũ, giữ làm lưới an toàn).
- **Test mới `tests/test_nv303_tin_dlna.py`: 7/7 xanh** (renderer DLNA giả + RAOP giả): nhạc AirPlay ⇒ tin qua DLNA, không có Pause/Stop/FLUSH/TEARDOWN tới phiên AirPlay, không phát lại nhạc, trạng thái thực thể vẫn là nhạc AirPlay suốt lúc tin nói (kể cả sau một lần hỏi lại trạng thái); tin DLNA lỗi ⇒ về đường thường (MUSIC, TTS, MUSIC); tin không bắt đầu được (renderer nhận lệnh mà không phát, chờ bắt đầu rút còn 0,3 giây trong test) ⇒ về đường thường; công tắc tắt ⇒ hành vi cũ, DLNA không nhận tin; Stop giữa lúc tin nói ⇒ renderer im + AirPlay đóng + giữ nhạc về 0 + idle `stopped`; ducking chiều DLNA qua đường âm lượng thật (`volume_set` → `mic_server`) hạ 10 → 5 rồi trả 10, không tạm dừng; idle của renderer giữa lúc tin chạy ⇒ `dang_giu`, không `finished`.
- **Test cũ đổi theo hành vi mới (đúng file, không phải gian lận test)**: `test_nv287_giu_nhac.py::test_tin_song_song_khi_nhac_o_airplay_thi_ve_duong_thuong` viết lại thành `..._thi_qua_dlna` kèm ghi chú NV303 (trước NV303 nó về đường thường, nay đi DLNA song song); `tests/test_nv302_the.py` cập nhật nhãn thẻ mới.
- **Bộ liên quan xanh**: `test_nv303_tin_dlna.py` + `test_nv287_giu_nhac.py` + `test_nv302_the.py` + `test_nv302_thuc_the.py` + `test_tuy_chon.py` = **43 passed**.
- **Toàn bộ suite, đối chiếu theo tên test**: cây đã vá **770 passed / 14 failed / 11 skipped**; cây nền sạch (NV288+NV302, không có NV303) **763 passed / 14 failed / 11 skipped** (770 − 763 = 7 = đúng số test mới). `diff` danh sách test lỗi giữa hai cây: **không lệch** — 14 lỗi đều thuộc họ nhạy thời gian/môi trường đã có từ nền sạch (7 test AirPlay UDP/ffmpeg, 6 test AirPlay song song khẳng định `raop.audio` — sandbox chặn gửi UDP nên không bao giờ đầy, chính file test NV287 đã ghi nhận — và 1 test SSDP `test_dmr.py`). **Không lỗi nào do NV303 gây ra.**
- `node --check` thẻ JS: sạch. Bandit trên file đổi (`media_player.py`, `settings.py`, `const.py`): High 0, Medium 0, Low 0 (một Low `try/except/pass` lúc đầu đã sửa thành log debug).
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật (tên miền `.example` trong test là giả, như các test cũ).

## Giới hạn cần host biết (chưa đo, đều mặc định an toàn)

- **Chưa thử trên loa/HA thật; chưa đo loa có trộn được DLNA + RAOP cùng lúc hay không** — công tắc mặc định TẮT, chỉ bật sau khi đo theo `docs/PHAT-RA-LOA.md` (giống NV287).
- Tin DLNA chờ bắt đầu tối đa 6 giây (`ANNOUNCE_START_WAIT`) rồi về đường thường; tin chạy tối đa 120 giây (`ANNOUNCE_MAX`) rồi dừng renderer.
- Một tin DLNA mới thay tin cũ (không hai tin cùng nói); Stop dừng cả tin DLNA lẫn nhạc AirPlay.
- Nhạc AirPlay hết thật giữa lúc tin DLNA đang nói vẫn khai `finished` ở đường kết thúc phiên AirPlay (đó là nhạc hết thật, không phải vòng lặp) — xem mục «Đã làm».

## Xác minh nộp

- `git ls-remote` sau khi đẩy: nhánh Giao `muse/nv303 = 043d445a47071084a38b1c5b218e7c8e82c83444`; Giao main lúc đẩy là `8e611363` (nhánh nộp tách từ main `8b00fce` lúc clone; main đã nhích lên `ac3d9350` rồi `8e611363` trong lúc làm — hai lần nhích đó chỉ sửa file trả lời, `inbox/NV303.md` đã đối chiếu lại và không đổi).
- Không force-push, không đẩy main, không đẩy trực tiếp lên repo loa.
