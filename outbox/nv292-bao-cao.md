# KẾT QUẢ — NV292: Đàm thoại giữa loa với loa (cặp và nhóm)

**Chưa thử trên loa thật.** Toàn bộ kiểm chứng dưới đây là test loa giả / mic giả /
phát giả trên máy làm việc; host có 4 loa (1–4) thì thử theo cặp 1–2, 3–4 rồi nhóm
3 loa trở lên theo kịch bản ở mục 6.

## 1. Đã làm gì

Mô hình «kênh đàm thoại» rồi làm theo đúng file (đặc tả trong code
`custom_components/r1_speaker/kenh.py`, docstring đầu file):

- **Cấu hình ở tuỳ chọn từng loa** (không gõ IP tay): `kenh` = tên kênh (trống =
  không vào kênh nào), `kenh_kieu` = `ptt` (bấm-để-nói, mặc định) hoặc `voice`
  (tự bật khi có tiếng). Các loa khai cùng tên thì thành một kênh; cặp 1–2,
  3–4 và nhóm nhiều loa đều khớp (nhóm = nhiều loa cùng tên).
- **Đường tiếng tái dùng đúng bộ đàm** (`intercom.py`, không giao thức thứ hai,
  không bộ trộn song công): mic loa nguồn PCM16 16 kHz → hạ tần số về 8 kHz
  (lấy mẫu chẵn) → `R1Intercom.feed` của từng loa đích (cổng thoại `Gate` +
  phát qua `R1Playback` + giữ mic chống vọng + đuôi giữ mic). Nguồn không bao
  giờ được đưa tiếng của chính mình; một người nói một lúc trong mỗi kênh.
- **Loa đích bận** thì toàn bộ lượt nói bị từ chối trước khi chiếm loa nào,
  bằng câu nêu rõ ai đang giữ (xem mục 2 — phần nhãn NV291). Nhạc ở loa đích
  tạm dừng rồi trả lại bằng `MusicKeeper.hold()` sẵn có của NV287 — **không
  sửa `giu_nhac.py`**, không dùng ducking (ducking chỉ cho tin song song).
- **Điều khiển**: dịch vụ HA `r1_speaker.noi_kenh` / `r1_speaker.dung_kenh`
  (nguồn là một thực thể bất kỳ của loa, phân giải qua entity registry như
  `hoi_thoai`), một công tắc mỗi loa có kênh (bật = mở kênh, tắt = đóng kênh;
  trạng thái đồng bộ giữa các loa cùng kênh qua listener của quản lý kênh).
  Thuộc tính công tắc mang `kenh`, `kieu`, `thanh_vien`, `nguoi_dang_noi`,
  `dang_mo`; sự kiện `r1_speaker_kenh` bắn khi mở/đóng/nói/dừng.
- **Giới hạn**: tối đa 8 kênh, mỗi kênh tối đa 6 loa, kênh mở tối đa 30 phút
  rồi tự đóng, đóng khi còn dưới 2 loa, nguồn mất mic thì dừng nói ngay,
  kiểu voice nhả quyền nói sau `silence_s` im (mặc định 1,5 s từ
  `TalkSettings`). Hàng đợi tiếng có trần sẵn trong `R1Intercom`
  (`PLAY_QUEUE_CHUNKS` + `hang_doi.day_bo_cu_nhat`), không thêm hàng đợi mới.
- **Riêng tư**: kênh mặc định TẮT (không nhớ qua khởi động lại HA); mở kênh
  phát một tiếng bip sine 880 Hz, 0,2 s tới các loa thành viên có kênh phát;
  loa chưa cấu hình kênh phát thì bỏ bip, không lỗi, kênh vẫn mở.

## 2. Phần nhãn NV291 đã nằm trong NV292 (để NV291 sau này không làm trùng)

Lúc làm NV292, cơ chế nhãn «ai đang giữ phiên» của NV291 chưa có trong nền
(nền `2e0c913` chưa có NV291). NV292 đã triển khai phần nhãn cần thiết ngay
trong patch này, theo đúng mô tả NV291:

- `Session` thêm trường `holder`; `claim(kind, holder=…)` và
  `async_start(kind, holder=…)` nhận nhãn; nhãn làm sạch lúc nhận (bỏ ký tự
  điều khiển, cắt 64 ký tự).
- Câu từ chối mới (qua `tu_choi(kind)`, `_refuse` cũ giữ nguyên vai trò gọi
  nó): «Loa R1 đang được dùng bởi \<nhãn\> (\<loại phiên\> — đã mở N giây):
  phiên «…» bị từ chối. …». Không biết nhãn thì ghi «một thiết bị không xác
  định», không bịa, không đoán theo IP, không danh sách tên.
- `EVENT_SESSION_REFUSED` thêm trường `nhan`; thuộc tính thực thể thêm
  `nhan_giu_phien`. Nhãn không đưa vào log INFO (câu từ chối vẫn log WARNING
  như trước).
- Lượt nói kênh chiếm phiên đích với `holder` = tên loa nguồn (tên thiết bị
  khai báo trong tích hợp, không phải IP).
- **NV291 còn lại phải làm sau**: phần thẻ Lovelace hiện câu từ chối mới
  (NV292 không đụng thẻ), và rà soát các chỗ mở phiên khác có nên kèm nhãn
  (người dùng HA / tên máy khách khai báo) hay không. **Đừng làm lại phần
  nhãn trong NV291.**

## 3. Thay đổi so với câu từ chối cũ (cố ý, có test cập nhật theo)

Câu cũ «Loa R1 đang có phiên đàm thoại (nguồn: …)» đã thay bằng câu mới ở
mục 2. Một test cũ ghim cụm cũ
(`test_dam_thoai_ha.py::test_phien_thu_hai_qua_nut_bi_tu_choi_co_thong_bao`)
đã cập nhật regex sang «đang được dùng bởi» kèm ghi chú NV292; test
`test_dam_thoai.py` cũ (kiểm tra loại phiên đầu, loại bị từ chối, chữ «từ
chối», event `ban`/`bi_tu_choi`) giữ nguyên và vẫn xanh — không đổi hành vi
đó, chỉ đổi câu chữ.

## 4. File đổi (patch `outbox/nv292.patch`, 1564 dòng, 15 file)

- Mới: `custom_components/r1_speaker/kenh.py` (quản lý kênh, hạ tần số, bip,
  gộp định nghĩa, dịch vụ), `tests/test_nv292_kenh.py` (23 test).
- Sửa: `dam_thoai.py` (nhãn holder + câu từ chối + event/attribute),
  `const.py` (khoá tuỳ chọn + giới hạn kênh), `settings.py`
  (`kenh_ten`/`kenh_kieu`), `config_flow.py` (2 trường form chính),
  `switch.py` (công tắc kênh), `__init__.py` (đăng ký dịch vụ, gộp định
  nghĩa khi nạp mục, rời kênh khi dỡ/xoá mục), `services.yaml`,
  `strings.json`, `translations/vi.json`, `translations/en.json`,
  `docs/CAI-DAT-CHI-TIET.md` (dòng thực thể + dịch vụ — test tài liệu bắt
  buộc), `tests/test_tuy_chon.py` (form thêm 2 trường, ghi chú NV292),
  `tests/test_dam_thoai_ha.py` (regex câu từ chối mới, ghi chú NV292).
- Không đụng: `assist_satellite.py`, `giu_nhac.py` (NV287, chỉ đọc),
  `intercom.py`, `playback.py`, `mic.py`, `mic_server.py`, giao thức phía loa
  (APK). Không thêm phụ thuộc.

## 5. Kiểm chứng (lệnh `python -m pytest tests -q -p no:sugar`, đọc EXIT CODE)

- Test mới đỏ trước: chạy `tests/test_nv292_kenh.py` trước khi có code thì
  lỗi collection (`ImportError: cannot import name 'kenh'`) — đỏ đúng nghĩa.
- Test mới sau code: **23/23 xanh**, gồm: hạ tần số giữ mẫu chẵn; bip 3200
  byte, mức trên −45 dB; gộp kênh theo tên (cặp giữ kiểu, nhóm thành hình,
  tên trống bỏ, kiểu lạ bỏ cả định nghĩa, thiếu kiểu về `ptt`); nhãn
  (nêu rõ người giữ + loại phiên, event `nhan`, attribute `nhan_giu_phien`,
  không biết nhãn → «một thiết bị không xác định», làm sạch ký tự điều
  khiển + cắt 64 ký tự); mở kênh cần ≥ 2 loa, bip đủ thành viên, bỏ bip khi
  chưa có kênh phát; PTT đưa tiếng đã hạ tần tới đúng đích (nguồn không nghe
  lại mình), chiếm phiên đích `kind="kenh"` + `holder` tên nguồn, giữ nhạc
  đích, nhả cả hai khi dừng; nhóm 3 loa đưa tới cả 2 loa còn lại; chưa mở
  kênh thì nói bị từ chối; một người nói một lúc (người thứ hai bị từ chối
  kèm tên người đang nói, nói lại được sau khi dừng); đích bận bị từ chối
  kèm «đang được dùng bởi» + loại phiên, phiên cũ nguyên vẹn, không đặt
  người nói; nguồn mất mic thì dừng nói + nhả nhạc/phiên; dừng khi không ai
  nói thì im lặng; voice tự mở khi có tiếng (khúc mở đầu bị bỏ, khúc sau
  mới đưa — xem mục 7), im quá `silence_s` thì nhả quyền; quá 6 loa thì mở
  lỗi; gỡ người nói rồi gỡ thêm loa → kênh còn dưới 2 loa thì đóng.
- Bộ liên quan: `test_bo_dam.py`, `test_dam_thoai.py`,
  `test_nv287_giu_nhac.py`, `test_tuy_chon.py`, `test_quy_tac_tai_nguyen.py`
  — **75/75 xanh** (đường thẻ→loa cũ hồi quy qua `test_bo_dam.py`).
- Toàn bộ (sau khi sửa 2 lỗi do NV292 gây ra, xem dưới): **751 passed,
  15 failed, 11 skipped**. Đối chiếu nền sạch `2e0c913` (worktree riêng,
  cùng lệnh): **727 passed, 16 failed, 11 skipped**. 777 − 754 = 23 = đúng
  số test mới; tập lỗi còn lại chỉ thuộc họ đã biết hay thay đổi theo lượt
  chạy (AirPlay 7, AirPlay song song 6, DMR 1, đèn 1–2 test khác tên giữa
  các lượt — đúng họ «nhạy thời gian» mà NV288/NV302 đã ghi). **Không còn
  lỗi nào do NV292 gây ra.**
- 2 lỗi do NV292 gây ra lúc đầu và đã sửa (không giấu): (a) test tài liệu
  đỏ vì thực thể/dịch vụ mới chưa có trong `docs/CAI-DAT-CHI-TIET.md` — đã
  thêm dòng «Kênh đàm thoại» (kèm `noi_kenh`/`dung_kenh`); (b) test HA ghim
  câu từ chối cũ — đã cập nhật regex kèm ghi chú NV292 (mục 3).
- Bandit trên các file đổi: High 0, Medium 0; Low 2 đều là mẫu có sẵn từ
  trước (try/except pass ở `_thu_adb`, assert ở `dam_thoai` giữ từ `_refuse`
  cũ), không phải code mới của NV292.
- Patch áp sạch lên nền `2e0c913` (`git apply --check` trên worktree nền
  sạch, đã kiểm).

## 6. Cách thử trên loa thật (host có 4 loa)

1. Đặt Tuỳ chọn loa 1 + loa 2 cùng `kenh` = «cap-1-2» (kiểu `ptt`); loa 3 + 4
   cùng «cap-3-4». Bật công tắc «Kênh đàm thoại» ở một loa trong cặp → cả
   cặp nghe bip → gọi `r1_speaker.noi_kenh` (kenh = tên cặp, nguon = một
   thực thể của loa nguồn) → nói vào loa nguồn, loa đích phải nghe; gọi
   `dung_kenh` thì dừng; nhạc đang phát ở đích phải tạm dừng rồi trả lại.
2. Nhóm: đặt 3 loa cùng tên kênh, mở kênh, nói từ một loa → cả 2 loa còn
   lại nghe, loa nguồn không nghe lại mình.
3. Đích bận: mở Assist ở loa đích rồi nói từ loa nguồn → phải bị từ chối
   kèm câu nêu tên loa nguồn (không phải câu chung chung).
4. Kiểu `voice`: đặt kênh kiểu `voice`, mở kênh, nói vào một loa → loa
   kia nghe sau một nhịp; im ~2 s → quyền nói nhả; loa khác nói được.
5. Nếu chỉ có 2 loa thật: thử cặp + nhóm 2 loa; nhóm 3 loa thử sau khi có
   loa thứ ba (kịch bản test giả đã phủ nhóm 3).

## 7. Giới hạn và lưu ý cho host (đọc trước khi gộp)

- **Chưa thử trên loa thật; chưa đo độ trễ.** Ước tính một chiều khoảng
  0,2–0,5 s (khúc mic 64 ms + hàng đợi bộ đàm + kênh phát TCP) — là ước
  tính từ kích thước khúc, không phải số đo. Ngưỡng voice (`threshold_db`
  −45 dBFS, `silence_s` 1,5 s) mượn từ bộ đàm, chưa đo trên loa R1.
- **Một loa chỉ ở một kênh (v1).** Muốn một loa vào nhiều kênh thì cần đổi
  tuỳ chọn thành danh sách — chưa làm.
- **Chưa làm nút bấm (button) riêng cho kênh.** File cho phép «switch HOẶC
  button»; NV292 làm switch + dịch vụ, đủ chữ nhưng chưa có button.
- **Kiểu voice bỏ khúc mở đầu**: khúc tiếng đầu tiên chỉ dùng để mở lượt
  nói (đã chiếm phiên + giữ nhạc xong mới đưa khúc sau); cổng thoại ở đích
  giữ `preroll_s` nên đầu câu không mất hẳn, nhưng khúc đầu tiên đó không
  được đưa đi. Chấp nhận được cho bộ đàm, ghi rõ để host khỏi ngạc nhiên.
- **Phiên của loa nguồn không bị chiếm**: lượt nói kênh chỉ chạm vào luồng
  mic của nguồn và chiếm phiên ở các đích; nguồn vẫn có thể mở Assist cùng
  lúc (Assist sẽ giữ mic nguồn theo luật riêng). Đây là lựa chọn thiết kế,
  không phải yêu cầu file — nếu host muốn nguồn cũng bị khoá thì nói rõ.
- **Tương tác gộp với NV288/NV302**: nền NV292 là R1 main `2e0c913`, CHƯA
  có NV288/NV302. Khi gộp, kiểm tra bằng tay 2 hunk chạm file chung:
  `config_flow.py` (NV292 thêm 2 trường form chính; NV288 thêm bước lịch)
  và `switch.py` (NV292 thêm công tắc kênh; NV302 thêm thực thể) — patch
  NV292 không chứa thay đổi NV288/NV302 nên gộp theo thứ tự nào cũng được,
  nhưng 2 file này cần xem xung đột văn bản lúc áp.
- **Không có phần thẻ Lovelace mới**: card hiện tại không vẽ kênh; muốn
  hiện «kênh đang mở + ai đang nói» trên thẻ thì làm thêm ở NV291 hoặc
  NV riêng (dữ liệu đã có sẵn ở thuộc tính công tắc + event
  `r1_speaker_kenh`).
- Không có khoá/mật khẩu/token/cookie/email thật/IP thật trong patch, báo
  cáo hay log.

## 8. Nộp

- Nền: R1 main `2e0c913` (0.12.0, đã gồm NV286 + NV287, chưa có NV288/NV302).
- File nhiệm vụ: Giao main `8b00fcecb671c62da1fbea7545eba51fc5d1d99e`,
  `inbox/NV292.md` blob `8ece4a24e27ed10026d72725311d9da1d7d52e0b` — kiểm lại
  lúc nộp, file không đổi trong lúc làm.
- Nhánh Giao: `muse/nv292` (chỉ nhánh `muse/*`, không đẩy main, không
  force-push), gồm `outbox/nv292.patch` + `outbox/nv292-bao-cao.md`.
- Công việc R1 làm ở nhánh làm việc `nv292-lam-viec` (commit `e812cea`,
  local, không đẩy lên repo R1).
