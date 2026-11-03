# KẾT QUẢ — NV302: Đưa cài đặt hay dùng lên thẻ «Cài đặt» (loa R1)

**Nền:** repo `TriTue2011/assist-phicom-R1`, nhánh NV288 (commit `4e8e633`) — patch
này là **delta so với cây đã có NV288**, không chứa lại thay đổi NV288. **Thứ tự gộp:
NV288 trước, rồi NV302.** Patch áp sạch lên cây đã có NV288 (đã kiểm bằng
`git apply --check`). **Chưa thử trên loa/HA thật** (chỉ test với loa giả + `hass` giả
+ mô hình thẻ bằng Node; không có Chrome thật trên máy này nên không chụp màn hình
thẻ ở 375 px — file NV302 yêu cầu «nếu chạy được»).

**Nộp:** nhánh Giao `muse/nv302`: `outbox/nv302.patch` (delta so với NV288),
`outbox/nv302-bao-cao.md` (file này). Không có file hỏi riêng (không còn câu hỏi mở
ngoài các câu đã nằm trong `hoi-nv288.md`).

## Làm được gì

### 1. Mục «Phát nhạc & tin báo» trong tab Âm thanh của thẻ

* Thêm vào thẻ một `<section>` sau điều khiển âm thanh chính, trước mục nâng cao:
  chọn đường phát (`duong_phat`: DLNA / DLNA trước / AirPlay trước / AirPlay), công
  tắc «Tin báo song song AirPlay», công tắc «Hạ nhạc nền khi loa nói» + thanh «Số
  nấc hạ» (1–14), và ô «Cổng AirPlay» (1–65535).
* Mỗi mục có một dòng giải thích tiếng thường, trong đó hai công tắc chưa đo ghi rõ
  «Chưa đo trên loa thật: chỉ bật khi muốn thử» (tin song song) và «Chỉ có tác dụng
  khi tin song song bật. Chưa đo trên loa thật» (hạ nhạc nền).
* **Phần thêm ngoài danh sách liệt kê ở mục 1 của file:** ô «Cổng AirPlay»
  (`airplay_port`). Lý do: phần mở đầu của file nêu rõ thẻ «chưa có chỗ chỉnh»
  `airplay_port`, và nó cùng khuôn với «Số nấc hạ» (cùng là number ghi tuỳ chọn).
  Ghi rõ ở đây để chủ máy biết và có thể yêu cầu gỡ nếu không muốn.

### 2. Tab mới «Khởi động lại» trên thẻ (mục «Khởi động lại loa» của file)

* Tab thứ 4 bên cạnh Âm thanh / Ánh sáng / Kết nối: công tắc lịch, ô giờ
  (`<input type="time">`), 7 ô chọn ngày T2…CN, công tắc «Tự khởi động lại khi loa
  treo» đặt trong `<details>` «Nâng cao» thu gọn, nút «Khởi động lại ngay» (nối lại
  nút đã có từ trước), dòng «Lần khởi động lại cuối: <giờ> (lý do: lịch/treo/bấm)»,
  và dòng trạng thái cảm biến phản hồi (có/không + lý do: bình thường / treo / mất
  mạng).
* Thẻ được viết phòng thủ: thực thể lịch vắng mặt (trường hợp gộp trước NV288) thì
  điều khiển tương ứng bị vô hiệu, hiện dòng «Chưa có thực thể lịch (cần gộp NV288
  trước)», không vỡ và không gọi dịch vụ ma (đã có test cho trường hợp này).

### 3. Một nguồn duy nhất với hộp tuỳ chọn HA (đúng mục 3 của file)

* Mỗi cài đặt là một thực thể chuẩn do tích hợp tạo, ghi vào `entry.options` qua
  helper `dat_tuy_chon` (giá trị bằng mặc định thì không lưu, theo quy tắc
  `_overrides`): `select.r1_duong_phat`, `switch.r1_tts_song_song`,
  `switch.r1_ha_nhac_xuong`, `number.r1_so_nac_ha_nhac`,
  `number.r1_cong_airplay`, cùng các thực thể lịch của NV288. Đổi ở đâu cũng thấy ở
  kia. **Không dựng cơ chế lưu thứ hai.**
* Các cài đặt phát nhạc được đọc trực tiếp mỗi lần dùng (đã đối chiếu
  `media_player.py`), nên đổi ở thẻ có hiệu lực ngay, **không cần nạp lại tích hợp**.
  (Ngoại lệ duy nhất là cài đặt nâng cao đọc lúc nạp — không thuộc phạm vi này.)
* Thẻ chỉ đọc/ghi qua thực thể và `sensor.r1_cai_dat`, không gọi loa — giữ nguyên
  khuôn cũ và lệnh cấm trong JS (không `fetch`/`WebSocket`/URL/IP cứng/`eval`).
* **Không thêm** thực thể cho Chế độ đóng ADB, nguồn phím, cách nối ADB — chúng vẫn
  chỉ ở hộp tuỳ chọn; tab «Kết nối» của thẻ đã có nút «Mở tuỳ chọn».

### 4. Bố cục thẻ (mục 4 của file, theo nguyên tắc NV294)

* Tab thứ 4 nên `.tabs` thêm `flex-wrap:wrap` (không tràn ngang ở 375 px),
  `.row` thêm `min-height:44px` (chạm ≥ 44 px), `ha-card` thêm `font-size:14px`
  (chữ ≥ 14 px trên điện thoại), checkbox 22×22 px, hàng chọn ngày tự xuống dòng.
* Tăng BUILD của thẻ lên `2026-11-03.1` để trình duyệt lấy bản mới.
* Hai assertion tab con 3→4 đã cập nhật có lý do (`test_the_cai_dat.py`,
  `test_giao_dien_the_gop.py`); các test Chrome này skip trên máy này (không có
  Chrome thật) — cần chủ máy hoặc CI có Chrome kiểm lại.

### 5. Tài liệu

* `docs/CAI-DAT-CHI-TIET.md`: thêm dòng cho 5 thực thể mới (đường phát, tin song
  song, hạ nhạc nền, số nấc hạ, cổng AirPlay) — bắt buộc vì test tài liệu yêu cầu
  mọi tên thực thể phải có mặt trong tài liệu.
* Không tăng version trong `manifest.json` (vẫn 0.12.0; host phát hành mới tăng).

## Kiểm chứng

* Đỏ-trước-xanh: thẻ cũ (NV288) có `TABS = ["audio","light","conn"]` — test tab thứ 4
  đỏ trên thẻ cũ, xanh sau khi thêm tab.
* Test mới: `tests/test_nv302_thuc_the.py` (4 test: select/switch/number ghi tuỳ chọn
  và ngược lại qua nạp lại mục) và `tests/test_nv302_the.py` (5 test Node: mô hình đủ
  mục phát + khởi động, gọi đúng dịch vụ qua thực thể, HTML có đủ điều khiển, thiếu
  thực thể lịch thì vô hiệu không vỡ, dữ liệu ngoài qua `esc()`).
* `node --check` cho JS: sạch. Test liên quan: `test_the_cai_dat.py`,
  `test_tai_lieu_cai_dat.py` — tất cả xanh (26 passed, 1 skipped là test Chrome).
* Toàn bộ test: `python -m pytest tests -q -p no:sugar` — **757 passed, 20 failed,
  11 skipped, 1 error** (chạy 979 giây; máy lúc đó còn chạy song song agent NV292 nên
  chậm hơn bình thường). Phân tích: 20 lỗi đều thuộc tập lỗi nhạy thời gian đã biết
  từ nền sạch (AirPlay 7, AirPlay song song 6, DMR 1, đèn `r1den_chay_that` 6 biến thể
  tham số — tập biến thể thay đổi theo từng lần chạy, kể cả khi chạy riêng file đó;
  patch NV302 không đụng mã AirPlay/đèn/DMR); 1 error là lỗi teardown
  `ConnectionResetError` ở test thẻ đàm thoại khi máy quá tải — chạy riêng file đó
  thì 4 passed, 4 skipped (Chrome), sạch. **Không có lỗi mới nào do NV302 gây ra.**
  Patch delta đã kiểm `git apply --check` sạch trên cây NV288.
* Bandit trên các file Python đổi/mới: severity High 0, Medium 0. Không có bí mật/IP
  thật trong patch.

## Chưa kiểm (ghi rõ)

* Chưa thử trên loa/HA thật; chưa mở tab trên Chrome thật; chưa chụp màn hình thẻ ở
  375 px (không có Chrome trên máy này).
* Chưa kiểm bố cục thật ở 375 px bằng mắt — chỉ kiểm bằng CSS (wrap, min-height,
  font-size) và test Node.

## Thứ tự trong đợt và thứ tự gộp

Trong đợt này NV288 làm trước, NV302 xếp chồng lên trên (đúng mục 5 của file NV302:
«Nếu NV288 đã nộp trước thì NV302 chỉ làm phần thẻ và thực thể còn thiếu» — ở đây
NV288 nộp trước, NV302 làm phần thẻ + thực thể phát nhạc, dùng lại thực thể lịch của
NV288). Người dùng chốt «NV302+NV288 trước» vẫn giữ nguyên; chỉ đổi thứ tự nội bộ
trong đợt vì mục «Khởi động lại loa» trên thẻ ràng buộc vào đúng thực thể của NV288.
**Gộp NV288 trước rồi mới NV302.**
