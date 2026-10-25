# NV270 — Báo cáo hợp nhất A + C (bản nộp)

Nền: `f712834..HEAD` trên nhánh `muse/nv270` của `TriTue2011/calendar`.
Patch nộp: `nv270.patch` (42 KB, 826 dòng, 5 file, 615 thêm / 39 bớt).
Kiểm hợp nhất: `git diff --check` OK, `node --check` OK cho mọi
`custom_components/lich_viet/frontend/*.js`, `git am --3way` trên bản
clone sạch từ `f712834` ÁP ĐƯỢC, cây sạch, stat trùng bản hợp nhất.
Test đã chạy (venv, `--noconftest`, vì conftest cần plugin Home Assistant):
`tests/test_nv269_xuong_cho.py` 18 passed + `tests/test_nv270_bo_ve.py`
7 passed = **25 passed**.

## KẾT QUẢ

### A — Chó (test động học, luồng A)
- (a) Tỉ lệ quãng di chuyển chân xa/chân gần: sau **1,068**, trước **1,003**,
  đều ≥ 0,8 — ĐẠT.
- (b) Bước đều: min/max bốn chân **0,829** ≥ 0,8 — ĐẠT, sát ngưỡng.
  Lệch trượt khỏi đường thẳng trong pha chạm đất: **≤ 1,49 px** ≤ 5 px — ĐẠT.
- File chó: 18 passed. Test đỏ khi đổi biên độ cả hai chân trước lên 0,5
  và khi đặt biên độ chân xa về 0. xfail cũ đã bỏ.
- Hàm mới trong `lich-bloc-xua-xuong.js`: `capChan`,
  `quangDuongBanChan`, `quangDuongBonChan`, `tiLeChanXaGan`,
  `doDeuBuoc`, `lechTruotTiepXuc`, `khoangCachChanToiThieu`.

### C — Bộ vẽ 2 chân, không chân, demo (luồng C)
- `loaiXuong` (bon-chan / hai-chan / khong-chan), sóng không chân
  `y' = y + A(x)·sin(k·x − ω·t)` (`bienDoSong`, `dichChuyenSong`,
  `taoXuongSong`), xương phụ đuôi/tay ≤ 0,07 rad cho lớp 1 chân.
- `hinhThu` tải theo từng khoá, không còn gắn cứng con chó; khoá chưa đủ
  `<khoa>.json` + ảnh lớp vẫn giữ đường sprite dự phòng.
- Một vòng rAF cho cả thẻ, hủy canvas khi đổi ngày/con, tạm dừng theo
  class `dung`, bánh răng `toc_do` / `chay_giay` / `nghi_giay` như sprite.
- Demo: `demo/lich-viet-demo.html` (lưới 12 con dùng chung `hinhThu`).
- Test mới `tests/test_nv270_bo_ve.py`: **7/7 passed**.

### B — Ảnh 11 con còn lại (ảnh NGUỒN, chưa phải lớp xương)
Ảnh dưới đây mới là ảnh nguồn, **CHƯA** qua `lam_lop.py` để tạo
`<khoa>.json` + `<khoa>-chinh.webp` / `<khoa>-xa.webp`, nên **ĐỪNG**
đưa các con này vào `THU_XUONG`, **đừng** tuyên bố 11 con đã chạy bằng
xương. Hiện tại chỉ chó chạy bằng xương; 11 con còn lại vẫn sprite.

| Khoá | Trạng thái ảnh nguồn |
|---|---|
| suu, dan, mao, ngo, mui, heo | Đạt chuẩn (4 chân, tách rời, bàn chân phẳng) |
| ty, ga | Đạt chuẩn (2 chân, xa sẫm lùi sau, gần tiến trước, khe trắng rõ) |
| ran | Đạt chuẩn (0 chân, thân S nhẹ, đầu phải, không cuộn chồng) |
| thin | Đạt với lưu ý: 0 chân, không chi phụ, nhưng đầu/cổ vẫn nhấc cao hơn thân |
| than | Chưa đạt chuẩn nghiêm ngặt: bản đúng xa/gần có gót chân gần hơi nhấc; bản vẽ lại đảo xa/gần nên không dùng |

Tổng bản chuẩn 11 con: ~1,74 MB (< 4 MB cho 12 con). Kích thước thực
tế xấp xỉ 1536×1024 (1408×1584 đến 1920×1280), cần chuẩn hoá khi làm lớp.

### Hợp nhất A + C
Có xung đột thật ở `lich-bloc-xua-xuong.js`: cả A và C đều sửa
`khoangCachChan` và phần đầu file. Đã hợp nhất bằng tay: giữ cả hàm FK
của A và `loaiXuong` / sóng / xương phụ của C, không bỏ chức năng nào.
Patch C phần còn lại (card, demo, test) áp trực tiếp được, không xung đột.

## ĐIỂM CHƯA ĐẠT
- (c) Chưa kết luận bằng hình vẽ thật: khoảng cách gần–xa nhỏ nhất theo
  động học thuận (điểm khớp) của cặp sau là **93,8 px**, thiếu 0,2 px so
  với ngưỡng `rong` 94 px, trong khi số hình vẽ thật của điều phối là
  142 px. Hai thước đo khác nhau (điểm khớp vs tâm bàn chân trên ảnh),
  nên không dùng số FK này để kết luận (c) — (c) phải đo bằng `do_chan.py`.
- `than` chưa đạt chuẩn nghiêm ngặt (xem bảng B và `hoi-nv270-anh.md`).
- `thin` đầu/cổ nhấc cao, chưa đúng tuyệt đối "đầu, thân, đuôi gần như
  cùng một mức ngang".

## CHƯA KIỂM
- `do_chan.py` + đo độ mượt chưa chạy được: không có Chrome thật /
  `ui_chung` / `cv2` trong VM; Chrome headless ở đây không ra kết quả
  ngay cả với trang test đơn giản. Vì vậy số (a)(b) trên là số động học
  thuận, không phải số hình vẽ thật, và chưa có bảng 120 khung / 60 fps.
- Chưa chụp chuỗi 8 tư thế mỗi con (không có Chrome).
- `pytest` toàn bộ `tests/` chưa chạy: conftest cần plugin
  `pytest_homeassistant_custom_component` (thiếu Home Assistant); chỉ chạy
  được 2 file trên với `--noconftest`.
- Chưa tạo `json` / `chinh` / `xa` cho 11 con, chưa chạy `lam_lop.py`,
  chưa cân khớp cho các con đó.
- CHƯA chạy trên WebView Android của Home Assistant, CHƯA xem trên điện
  thoại. Chỉ Chrome headless (SwiftShader) cũng chưa chạy được ở đây,
  nên chủ máy cần xem demo trên điện thoại rồi mới phát hành.

## CÂU HỎI
1. Chấp nhận `thin` với lưu ý đầu nhấc cao, hay chờ vẽ lại thin cho đầu
   gần ngang thân?
2. Chấp nhận `than` bản lượt 3 (gót hơi nhấc) tạm thời, hay chờ ảnh than
   mới từ điều phối theo `hoi-nv270-anh.md` rồi mới làm lớp xương cho than?
