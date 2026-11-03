# KẾT QUẢ — NV288: Khởi động lại theo lịch + cảm biến «Loa phản hồi» (loa R1)

**Nền:** repo `TriTue2011/assist-phicom-R1`, main `2e0c913` (tag `v0.12.0`, đã gồm
NV286+NV287). Patch áp sạch lên nền này. **Chưa thử trên loa thật** (và chưa thử trên
HA thật — chỉ test với loa giả + `hass` giả).

**Nộp:** nhánh Giao `muse/nv288`: `outbox/nv288.patch` (diff so với main `2e0c913`),
`outbox/nv288-bao-cao.md` (file này), `outbox/hoi-nv288.md` (3 câu hỏi).

## Làm được gì

### 1. Khởi động lại theo lịch (mặc định TẮT, phòng ngừa)

* Tuỳ chọn tích hợp mới (một nguồn duy nhất với hộp tuỳ chọn HA): `lich_khoi_dong_lai`
  (bật/tắt, mặc định TẮT), `lich_gio` (`"HH:MM"`, mặc định `"03:00"`), `lich_ngay`
  (danh sách thứ 0–6, Thứ 2 = 0, mặc định mọi ngày), `tu_phuc_hoi_khi_treo` (mặc định
  TẮT). Thêm bước `lich` vào options flow (ô «lich» ở form chính, như khuôn ô
  «nang_cao»); giờ sai dạng `HH:MM` báo lỗi `gio_sai`, không lưu; bỏ qua bước lịch thì
  giữ nguyên lịch cũ (đã sửa một lỗi tiềm ẩn: bước nâng cao dùng một mình trước đây sẽ
  làm rơi các khoá không nằm trong bước chính — nay `_luu()` giữ riêng các khoá lịch).
* Nhịp 60 giây (`khoi_dong_lai.py`, giờ/bận/khởi động có thể tiêm cho test, không ngủ
  thật): tới giờ + đúng ngày + chưa chạy hôm nay → kiểm loa bận (phiên Assist
  `talk.session`, đàm thoại song công `duplex.active`, hoặc media_player của loa đang
  `playing`/`buffering`) → bận thì hoãn tối đa 30 phút (`LICH_HOAN_TOI_DA_PHUT`); quá
  hạn mà vẫn bận thì **bỏ lịch hôm đó**, không reboot vào giữa phiên. Cờ «đã chạy hôm
  nay» + lần khởi động lại cuối lưu bền bằng `Store` (khoá theo entry_id) nên HA khởi
  động lại giữa chừng cũng không chạy hai lần; qua nửa đêm đổi ngày đúng, không chạy bù
  ngày cũ.
* Đường khởi động lại dùng chung với nút bấm (đã tách helper `khoi_dong_lai_loa`: ADB
  trước, hỏng thì cổng 8080; nút bấm giữ nguyên hành vi cũ, chỉ thêm ghi lý do `bam`
  khi lệnh đã chạy).

### 2. Cảm biến nhị phân «Loa phản hồi» (`binary_sensor.r1_loa_phan_hoi`)

* Tổng hợp nhiều tín hiệu độc lập: lần cuối get_info thành công (coordinator nay ghi
  `lan_cuoi_thanh_cong` + `lan_cuoi_get_info`), nhịp tim APK `speaker_alive`, trạng
  thái ADB, và thử TCP 8080 **chỉ khi get_info đã im** (không thử lúc loa khoẻ).
* Phân loại: get_info mới hơn 30 giây (`PHAN_HOI_BINH_THUONG_S`) = bật/`binh_thuong`;
  im 30–120 giây = giữ trạng thái cũ (không dao động); im quá 120 giây
  (`PHAN_HOI_TREO_S`) thì TCP nối được mà nhịp tim im = tắt/`treo`, TCP không nối được
  = tắt/`mat_mang`, nhịp tim còn sống = giữ trạng thái cũ (chưa đủ «mọi tín hiệu ứng
  dụng im»). Thuộc tính kèm thời điểm lần cuối từng tín hiệu còn sống
  (`lan_cuoi_get_info`, `lan_cuoi_nhip_tim`, `adb_noi`, `tcp_8080`, `nguong_treo_s`).
* Log WARNING **một lần** mỗi lần đổi `ly_do` (vào treo/mất mạng/hồi phục), không spam
  mỗi nhịp. **Diễn giải yêu cầu 2d:** các thực thể điều khiển của loa (theo coordinator)
  vốn đã `unavailable` khi vòng hỏi hỏng; riêng cảm biến phản hồi **cố tình luôn khả
  dụng** vì chính nó là thứ báo loa có tới được không.
* Đánh giá lại mỗi lần coordinator hỏi xong, khi APK báo nhịp tim, và mỗi 30 giây.

### 3. Tự phục hồi khi treo (mặc định TẮT, công tắc riêng)

* Treo kéo dài quá 300 giây (`PHUC_HOI_SAU_S`) + công tắc bật + ADB còn nghe được
  (thử bắt tay TCP cổng 5555 bằng `AdbDevice.con_nghe_mang()`, không nói giao thức
  ADB) → HA khởi động lại loa **một lần bằng ADB**, rồi nghỉ ít nhất 4 giờ
  (`PHUC_HOI_NGHI_GIO`) mới được tự phục hồi lần nữa — không bao giờ vòng lặp.
* Mất mạng thì không tự phục hồi (HA không tới được loa từ xa). Trường hợp ADB chưa
  từng nối (`duong` = None) nhưng thực ra nối được thì tự phục hồi bỏ qua — lựa chọn
  bảo thủ, xem câu hỏi 1 trong `hoi-nv288.md`.

### 4. Thực thể mới (một nguồn duy nhất với hộp tuỳ chọn, luôn khả dụng)

* `switch.r1_lich_khoi_dong_lai`, `switch.r1_tu_phuc_hoi_khi_treo`, 7 công tắc ngày
  (`switch.r1_lich_thu_2` … `switch.r1_lich_chu_nhat`), `time.r1_lich_gio`,
  `binary_sensor.r1_loa_phan_hoi`, `sensor.r1_lan_khoi_dong_lai_cuoi` (TIMESTAMP +
  thuộc tính `ly_do`: `lich`/`treo`/`bam`). Nền tảng `TIME` mới (`time.py`).
* Ghi tuỳ chọn qua thực thể dùng helper `dat_tuy_chon` (giá trị bằng mặc định thì không
  lưu, theo quy tắc `_overrides`); **không nạp lại tích hợp** khi thực thể ghi — các
  cài đặt này được đọc trực tiếp mỗi lần dùng (đã đối chiếu: `OptionsFlowWithReload`
  chỉ tự nạp lại khi options flow kết thúc, `async_update_entry` gọi trực tiếp không tự
  nạp lại).
* Tài liệu: `docs/CAI-DAT-CHI-TIET.md` thêm mục 2a (lịch + cảm biến + ngưỡng + diễn giải
  2d) và các dòng thực thể mới.

### 5. Ranh giới giữ nguyên

* Không sửa `assist_satellite.py` (chỉ đọc khi cần, đúng ranh giới NV286/NV288).
* Không đổi firmware/APK; không thêm phụ thuộc mới; không tự bật tính năng mặc định
  (cả lịch và tự phục hồi đều TẮT).
* Không tăng version trong `manifest.json` (hiện 0.12.0; host phát hành mới tăng).

## Ngưỡng chọn và vì sao (tất cả CHƯA ĐO — theo đính chính của chủ máy 02/11/2026)

Chủ máy đã nói rõ: nhật ký HA hôm đó (loa không ping được, 8080/5555 từ chối) KHÔNG
phải bằng chứng loa treo — chủ máy đã chủ động rút nguồn loa từ hôm qua. Chưa có số đo
nào về một lần treo thật, nên mọi ngưỡng dưới đây chỉ là điểm bắt đầu hợp lý, không
phải số đo; cảm biến ghi lại bằng chứng (thời điểm lần cuối từng tín hiệu còn sống)
để lần treo thật sau này có số liệu:

| Hằng số | Giá trị | Lý do chọn |
|---|---|---|
| `lich_gio` mặc định | 03:00 | Giờ ít dùng nhất trong nhà, trùng giờ bảo trì thường gặp |
| `LICH_HOAN_TOI_DA_PHUT` | 30 phút | Đủ cho một phiên Assist/nghe nhạc ngắn xong; quá thì bỏ chứ không reboot muộn vào phiên khác |
| `PHAN_HOI_BINH_THUONG_S` | 30 giây | Gấp 3 nhịp hỏi coordinator (10 giây) — một hai nhịp hỏng không kết luận vội |
| `PHAN_HOI_TREO_S` | 120 giây | Bằng `WAKE_ALIVE_S` của nhịp tim APK: quá thời gian này mà mọi tín hiệu ứng dụng im thì mới kết luận |
| `PHUC_HOI_SAU_S` | 300 giây | Gấp 2,5 lần ngưỡng treo — tránh reboot vì một thoáng mất tín hiệu kéo dài |
| `PHUC_HOI_NGHI_GIO` | 4 giờ | Đủ lâu để loa ổn định sau reboot; một ngày tối đa ~6 lần tự phục hồi nếu treo dai dẳng (vẫn là trần, không phải vòng lặp) |

## Kiểm chứng

* Đỏ-trước-xanh: test mới đỏ trên mã cũ vì thiếu module (`ModuleNotFoundError`), xanh
  sau khi triển khai — không có đỏ giả.
* Test mới: `tests/test_nv288_lich_khoi_dong.py` (19 test: lịch đúng một lần, ngày không
  chọn thì không chạy, qua nửa đêm, hoãn khi bận + quá hạn thì bỏ lượt, mất mạng ≠
  treo, tự phục hồi không lặp + nghỉ, ghi lý do) và `tests/test_nv288_thuc_the.py`
  (6 test: bước lịch lưu đúng + giờ sai báo lỗi, bỏ qua bước lịch thì giữ lịch cũ,
  công tắc/giờ ghi tuỳ chọn và ngược lại, cảm biến treo rồi hồi phục ở mức tích hợp,
  nút bấm ghi `bam`).
* Test liên quan: `tests/test_tuy_chon.py` (12 test, đã cập nhật tập trường form chính
  thêm `"lich"` có lý do) — tất cả xanh.
* Toàn bộ test: `python -m pytest tests -q -p no:sugar` — **750 passed, 18 failed,
  11 skipped** (chạy 424 giây). Phân tích 18 lỗi: 17 lỗi là **có sẵn từ nền sạch**
  (đối chiếu bằng worktree của main `2e0c913`: cùng các file `test_airplay`,
  `test_airplay_song_song`, `test_dmr`, `test_r1den_chay_that` — toàn test nhạy thời
  gian thực; tập lỗi thay đổi theo từng lần chạy, kể cả khi chạy riêng file đó, và
  patch NV288 không đụng tới mã AirPlay/đèn/DMR); 1 lỗi còn lại là test tài liệu
  (`test_tai_lieu_cai_dat`: tên từng ngày trong tuần phải có mặt trong tài liệu) —
  **đã sửa** (liệt kê đủ 7 ngày trong `docs/CAI-DAT-CHI-TIET.md`), kiểm lại 3/3 xanh.
  Toàn bộ sau sửa tài liệu không chạy lại (chỉ đổi tài liệu + test tài liệu đã xanh).
* Trong quá trình làm đã bắt và sửa một lỗi do chính patch gây ra: callback timer của
  cảm biến gọi `hass.async_create_task` trực tiếp bị HA gắn cờ sai luồng lúc teardown
  (10 lỗi `test_bao_thuc`), còn lambda trả về coroutine thì bị HassJob xếp loại
  Callback nên coroutine không được await. Cách sửa đúng theo chữ ký của HA: đưa thẳng
  coroutine function (`self._danh_gia`, `self.tick`) cho `async_track_time_interval`
  để HA tự tạo task — sau sửa, các file liên quan 48 passed, 0 lỗi, 0 warning.
* Bandit trên các file đổi/mới: severity High 0, Medium 0; một Low là code cũ sẵn có
  (`_thu_adb` dọn dẹp, không đụng). Không có bí mật/IP thật trong patch (test chỉ dùng
  `127.0.0.1` và dải ví dụ).

## Chưa kiểm (ghi rõ)

* Chưa thử trên loa thật, chưa thử trên HA thật (chỉ loa giả + `hass` giả).
* Chưa chụp màn hình thẻ ở 375 px — phần thẻ thuộc NV302, làm ngay sau NV288 trong
  cùng đợt.
* Hai câu hỏi mở (ngưỡng, thăm dò ADB, bỏ lượt khi quá hạn) nằm trong
  `outbox/hoi-nv288.md` — chủ máy trả lời thì sửa trong lần nộp sau, không chặn gộp
  vì mọi tính năng đều mặc định TẮT.

## Thứ tự gộp

NV288 nộp trước, NV302 xếp chồng lên trên (thẻ NV302 dùng đúng các thực thể lịch của
NV288). Gộp NV288 trước rồi mới NV302.
