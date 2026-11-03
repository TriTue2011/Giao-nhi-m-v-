# NV306 — R1: KHỞI ĐỘNG LẠI LOA QUA APK, KHÔNG QUA ADB — BÁO CÁO

## KẾT QUẢ

Đã xong và nộp nhánh Giao `muse/nv306` với `outbox/nv306.patch` (675 dòng, 15 file, +447/−16).
Nền: repo loa R1 main `b2c5096` (0.13.0, đã gồm NV288/NV302/NV303/NV291/NV292).
File nhiệm vụ đọc từ Giao main `ad2842f5`; nhánh nộp tách từ Giao main mới nhất lúc nộp `82d9ff4`
(chỉ thêm file NV309 và đồng bộ khác, patch NV306 không đụng các file đó).
**Chưa thử trên loa/HA thật** — đặc biệt chặng APK → localhost:8080 là chặng mới, chưa từng thử
(xem «Chưa thử» cuối báo cáo). **Binary APK 1.4 chưa được dựng trên máy này** — điều phối bắt buộc
phải dựng lại trước khi nhãn 1.4 thành thật (xem «Phần APK: đã làm / chưa làm»).

## Đường apk/adb chọn theo cấu hình ra sao

Hàm mới `duong_khoi_dong_lai(entry)` trong `custom_components/r1_speaker/khoi_dong_lai.py`:
trả `"apk"` khi tuỳ chọn chế độ «đóng ADB» (`adb_tu_dong_dong`) đang BẬT, `"adb"` khi tắt —
cùng quy tắc chọn đường như đèn (`LightsRouter`). Nút «Khởi động lại loa» và lịch NV288 dùng
chung đường này qua `KhoiDongLai._gui_lenh` (không thêm tuỳ chọn mới, không thêm thực thể mới).

- Đường APK: HA gửi khung `{"type":"khoi_dong_lai"}` qua kết nối mic tới APK; APK chuyển tiếp tới
  shell cục bộ qua websocket `127.0.0.1:8080` với đúng khung phẳng của HA
  (`{"type":"shell","type_id":"ha","shell":"stop adbd&&start adbd&&adb reboot"}`).
  Cả hai chặng (HA→APK qua TCP mic, APK→8080 qua loopback) đều không phải ADB mạng (cổng 5555).
- Đường ADB: giữ nguyên hành vi NV288 (ADB trước, hỏng thì qua cổng 8080).
- Tự phục hồi khi treo giữ nguyên chỉ-ADB (`chi_adb=True`): loa treo thì kết nối APK cũng chết
  nên đường APK không cứu được; chế độ đóng ADB bật thì đã báo «cần rút điện».
- Đường APK hỏng thì BÁO RÕ và DỪNG, không tự mở ADB, không rớt về ADB: APK chưa nối về HA qua
  mic; APK chưa báo khả năng (chưa rõ có hỗ trợ không); APK cũ chưa có khả năng `khoi_dong_lai`
  (báo cần APK 1.4 trở lên, cài bản mới qua ADB một lần sau khi rút điện). Điểm này khác mẫu đèn
  (đèn rớt về ADB khi APK cũ) một cách có chủ đích: rớt về ADB lúc ADB đang bị đóng vì bảo mật
  sẽ phá đúng mục đích của chế độ đóng.
- Ngữ nghĩa «ok»: HA ghi «ok» nghĩa là «đã gửi lệnh tới APK» (fire-and-forget), cùng ngữ nghĩa
  với đường ADB — loa khởi động lại thì kết nối tự đứt, không có xác nhận riêng. Cổng khả năng
  (`kha_nang` gồm `khoi_dong_lai`, gửi ngay khi APK nối) là điểm chặn trường hợp APK cũ nhận
  khung lạ rồi bỏ qua trong im lặng.

## Phần APK: đã làm / chưa làm (ranh giới)

ĐÃ LÀM (mã nguồn APK trong `apk/nguon`, repo R1):

- Mới `apk/nguon/src/vn/r1/bodam/KhoiDongLai.java`: nhận đúng một dạng khung
  `{"type":"khoi_dong_lai"}`; tạo handshake WebSocket RFC 6455 (Base64 viết tay vì android.jar
  API 22 không có `java.util.Base64`); tạo khung văn bản client có mask; chuyển tiếp tới
  `127.0.0.1:8080` trên luồng daemon `r1-khoi-dong-lai` (không chặn luồng đọc mic); lỗi chỉ ghi
  logcat (HA không nhận xác nhận riêng). Lệnh shell đồng bộ với `client.py` REBOOT_SHELL.
- `DieuKhienGhi.java`: vòng đọc khung HA→APK kiểm `KhoiDongLai.laLenh` sau `LenhPhu`, trước
  fallback đèn; khung lạ/hỏng vẫn bị bỏ như cũ, không đứt kết nối mic.
- `BaoCao.java`: `PHIEN_BAN` 1.3 → 1.4, `KHA_NANG` thêm `"khoi_dong_lai"`.
- Manifest release + kiểm thử: versionCode 4 → 5, versionName 1.3 → 1.4.
- `bo-cai.json` (bodam): `phien_ban` 1.4, `mo_ta` thêm câu về khởi động lại qua APK.
- Tài liệu: `docs/HOP-DONG-PHIA-LOA.md` thêm khung `khoi_dong_lai` + mục NV306 (giữ nguyên phát
  hiện «APK không reboot trực tiếp được» — cơ chế mới là chuyển tiếp, không mâu thuẫn);
  `docs/CAI-DAT-CHI-TIET.md` cập nhật 2 hàng (khởi động lại không còn thuộc nhóm «cần ADB khi
  đóng»; hàng nút mô tả cả hai đường).

CHƯA LÀM ĐƯỢC TRÊN MÁY NÀY — ĐIỀU PHỐI DỰNG (đúng trường hợp file NV306 dự liệu):

- Máy này không có JDK, không có Android SDK, không có toolchain (`~/workspace/android-toolchain`
  không tồn tại) nên **không build được binary APK 1.4**. Nộp mã nguồn + lệnh build:
  `./build.sh release` trong `apk/nguon` (cần JDK 17 + SDK platform android-22 + build-tools
  30.0.3, biến môi trường xem `apk/nguon/README-BUILD.md`).
- Sau khi dựng: thay CẢ HAI bản sao APK (`apk/vn-r1-bodam.apk` và
  `custom_components/r1_speaker/apk/vn-r1-bodam.apk`) + file `.sha256` + trường `sha256` trong
  bo-cai.json bằng sha256 của binary mới. Hiện `sha256` trong bo-cai.json vẫn là của binary 1.3
  cũ — tới khi dựng xong thì nhãn 1.4 mới thành thật. Trước đó thực thể «Cập nhật» có thể hiện
  1.4 cho binary 1.3 (lệch nhãn có giới hạn): không mời cập nhật sai vì logic so từng byte với
  bản đi kèm, và cài đặt vẫn verify đúng sha nên không vỡ.
- Cài APK mới lên loa cần ADB MỘT LẦN: chủ máy rút điện rồi cắm lại để cổng 5555 tự mở lúc
  khởi động, cài qua ADB, sau đó chế độ đóng ADB tự đóng lại sau 2 phút kể từ khi APK nối lại.
- Test Java thuần mới (8 mục `(k)` trong `KiemTra.java`: nhận dạng lệnh, Base64, khung có mask,
  handshake, khung shell, vòng lặp thật qua loopback, cổng đóng → báo lỗi) CHƯA CHẠY ĐƯỢC trên
  máy này (không có JDK) — điều phối chạy khi dựng; kỳ vọng trong README đã cập nhật 47 → 55.

## Các quy tắc NV288 được giữ nguyên

Lịch mặc định TẮT; hoãn khi loa bận; lượt mỗi ngày chỉ chạy một lần, nhớ qua khởi động lại HA;
tự phục hồi khi treo mặc định TẮT. Không sửa `assist_satellite.py`. Không thêm phụ thuộc mới.
Không đổi giao thức phía loa ngoài khung `khoi_dong_lai` mà file yêu cầu.

## Kiểm thử

Môi trường: Python 3.13 cài bằng `uv` (`~/.local/bin/uv python install 3.13`), venv
`~/workspace/nv306/.venv` cài `requirements-test.txt` (HA 2026.2.3,
pytest-homeassistant-custom-component 0.13.316). Lưu ý môi trường: pip ghi file tạm vào /tmp
(tmpfs) liên tục lỗi `ENOSPC` khi tải wheel lớn dù đĩa còn trống — phải đặt `TMPDIR` sang thư
mục trên đĩa thì cài mới xong; nếu điều phối dựng lại trên máy này thì dùng cùng cách.

- Test Python mới `tests/test_nv306_khoi_dong_lai_apk.py`: **8/8 xanh** — gửi đúng khung; đường
  apk khi đóng ADB bật (không gọi ADB); APK chưa nối / APK cũ / chưa rõ khả năng đều báo lỗi
  chứa «APK» và không gửi khung; đường adb khi đóng ADB tắt; đường adb hỏng → 8080 đúng 1 khung
  `shell`; lịch dùng đường apk khi đóng ADB bật. Đỏ-trước-xanh: stash code HA (chỉ giữ test) thì
  6 đỏ / 2 xanh (2 xanh là test hồi quy đường ADB cũ, không cần code mới); có code thì 8/8.
  Một chi tiết test: file NV288 có fixture autouse `_mui_gio` đặt múi giờ `Asia/Ho_Chi_Minh` —
  file NV306 phải có cùng fixture thì lịch 04:00 giờ VN mới tới (để UTC thì lịch không chạy).
- Tập liên quan (NV306 + NV288 + mic_server + lenh_apk + apk_dong_goi + cai_ung_dung):
  **97 passed, 0 failed**. Hai test `cai_ung_dung` hardcode phiên bản 1.3 đã được cập nhật lên
  1.4 theo đúng lần tăng version (giữ nguyên khẳng định so sha256 với tệp thật); một chỗ mô
  phỏng loa đang cài bản đi kèm vẫn giữ 1.3 kèm chú thích vì file binary đi kèm hiện vẫn là
  bản 1.3 thật.
- Toàn bộ suite R1: lần 1 có vá 15 failed / 833 passed / 12 skipped; lần 2 có vá 20 failed /
  828 passed / 12 skipped / 1 error; nền sạch `b2c5096` 19 failed / 821 passed / 12 skipped /
  1 error. Chênh lệch 8 passed giữa có vá và nền sạch đúng bằng 8 test mới. Mọi lỗi ở cả hai
  bên đều chỉ thuộc 4 file nhạy thời gian (`test_airplay.py`, `test_airplay_song_song.py`,
  `test_dmr.py`, `test_r1den_chay_that.py`); đối chiếu theo tên: 15 lỗi trùng nhau, phần còn lại
  đổi nhau giữa các lần chạy trong cùng file đèn (`patched-only` 5, `clean-only` 4) — là flake
  do tải máy, không phải hồi quy do NV306. Không lỗi nào ở vùng NV306/NV288/mic/lenh_apk/
  dong_goi/cai_ung_dung. 1 error không gắn tên test xuất hiện ở cả hai bên (lỗi teardown dưới
  tải, giống các NV trước).
- Bandit trên 2 file nguồn đã đổi: High 0, Medium 1 (B104 bind-all-interfaces có sẵn tại
  `mic_server.py:149`, không phải code mới). 19 High khi quét kèm file test chỉ là B101
  `assert_used` của pytest (giống mọi file test khác).
- Quét bí mật trên patch: sạch (chỉ có `127.0.0.1` loopback, không IP LAN, không token/khoá).

## Ghi chú về luật đứng 16:11 (phân tích kỹ trước khi làm)

NV306 thuộc repo tích hợp R1, không phải module web2api nên chatgpt2api (tham chiếu cho
đăng nhập/trình duyệt web2api) không có phần tương đương cho đường reboot của loa — đã đối
chiếu và ghi rõ: toàn bộ đường reboot nằm trong tích hợp R1 + APK bodam, cả hai đều đã đọc kỹ
trước khi làm (chuỗi NV288: `khoi_dong_lai.py`, `client.py` REBOOT_SHELL, `tu_dong_dong_adb.py`,
`adb_client.py`, `settings.py`; kênh HA→APK: `mic_server.py`, `DieuKhienGhi.java`,
`BaoCao.java`, `docs/HOP-DONG-PHIA-LOA.md` kèm phát hiện đã đo 28/10/2026). Thiết kế bám mẫu
chọn đường sẵn có của đèn (`den_apk.py`/`LightsRouter`), chỉ khác ở điểm đã nêu: khởi động lại
không rớt về ADB.

## Chưa thử / cần kiểm sau khi gộp

- Chưa thử trên loa/HA thật, chưa kiểm Chrome thật. Đặc biệt: chặng APK → localhost:8080 chưa
  từng thử (chặng HA → 8080 từ LAN đã thử 28/10/2026: loa tắt sau ~10 giây, lên lại sau ~30
  giây; nhưng APK → loopback là chặng mới — cần thử thật: nút bấm khi đóng ADB bật, lịch tới
  giờ, APK cũ phải báo rõ chứ không im lặng, và sau khi khởi động lại thì APK tự nối lại).
- Chưa chạy test Java thuần (không có JDK) — chạy `KiemTra` khi dựng APK, kỳ vọng 55 passed.
- Sau khi dựng binary 1.4 + thay sha256: kiểm thực thể «Cập nhật» hết lệch nhãn và loa cài
  bản mới qua ADB một lần rồi đóng ADB lại bình thường.

## Xác minh nộp

- Patch áp sạch lên nền sạch R1 `b2c5096` (`git apply --check` trên worktree tách riêng: OK,
  15 file).
- Commit làm việc local trong clone R1 (không đẩy lên repo loa): nhánh `nv306-lam-viec`,
  commit `587c48f`.
- Nhánh Giao `muse/nv306` (không force-push, không đẩy main Giao hay main repo loa).
