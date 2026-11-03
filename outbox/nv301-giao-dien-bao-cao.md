# NV301 — mảnh giao diện: trình phát YouTube đầy đủ + dedup (2)(3)

## KẾT QUẢ

- Mảnh thứ ba (cuối trong phạm vi 3 mảnh đã chốt) của NV301 đã xong và đẩy
  lên nhánh `muse/nv301`: patch `outbox/nv301-giao-dien.patch` (1.986 dòng),
  nền web2api main `8ef3ca9`, trên commit mảnh playlist `dc8b3e8` →
  commit mảnh giao diện `64a3837`. Patch áp sạch lên cây `dc8b3e8`
  (kiểm bằng `git apply --check` trong worktree tạm, test mới 9/9 trên cây
  đã áp).
- Tab YouTube giờ là trình phát đầy đủ đúng mô tả demo trong file NV301
  (không còn trang chỉ-đọc của mảnh tab), gọi lõi qua hành động thực thể
  bằng phiên quản trị + CSRF — không gọi thẳng đường integration, không
  dùng khoá tích hợp Bearer của HA, không thẻ audio tự phát (tiếng ra loa
  qua HA), không số/bài giả.
- Hai yêu cầu (2) «chỉ một tab YouTube» và (3) «module chỉ-công-cụ không
  tạo tab» của file NV301 được làm NGAY TRONG mảnh này (không mở mảnh thứ
  tư): cơ chế `giao_dien: false` + `thay_the` từ bản khởi đầu, mở rộng sang
  cả danh sách `tab` của lõi.

## ĐÃ LÀM

### 1. Trình phát ở tab riêng của module youtube

`modules/youtube/web/index.html` + `web/trang.js` viết lại hoàn toàn:

- Thẻ ĐANG PHÁT: ảnh bìa 16:9, chip nguồn, tên bài, kênh, «Trên \<loa\>»,
  thanh tiến độ bấm để tua, thời gian, nút Trước / Phát–Tạm dừng / Sau /
  Dừng hẳn, chip «Nghe khi tắt màn hình». Vị trí hiển thị tự tick +1 giây
  khi đang phát; vị trí máy chủ mới là chuẩn khi tải lại.
- «Nhóm đang phát — bấm để điều khiển»: các loa/tivi trong phiên, bấm để
  chọn lại loa cho phiên đang chạy.
- Tìm kiếm: chip nguồn YouTube · Zing MP3 · Facebook + ô tìm + ghi chú
  theo nguồn; kết quả có nút Phát · Thêm vào Queue · Thêm vào Playlist +
  ô chọn «Playlist nhận bài». Link YouTube dán vào ô tìm được hiểu là
  video/playlist (như mảnh lõi).
- Playlist: nhập link/mã chia sẻ `TTPL1.` (+ tên ghi đè), tạo mới, danh
  sách playlist với Phát / Xem bài / Xoá, xem bài trong playlist với
  «Phát từ đây». Xoá playlist hỏi xác nhận một lần (`window.confirm`).
- Hàng đợi: tóm tắt «Bài a/b», danh sách với «Phát từ đây» / «Xoá».
  «Phát từ đây» dùng hành động riêng `phat_tu_hang_doi` — phát từ vị trí
  đó và GIỮ NGUYÊN hàng đợi (không phát bài lẻ làm mất hàng đợi).
- Loa & tivi: checkbox từ module home-assistant + «Áp dụng cho phiên
  đang chạy». «Trên \<loa\>» ánh xạ `media_player.<phòng>` sang tên từ
  danh sách HA; không có tên thì hiện hậu tố phòng, không hiện id kỹ thuật
  đầy đủ.
- Cài đặt: luôn thu gọn kiểu `muc-gap-nut`. Module không có trường cài
  đặt nào cần nhập; trang chỉ hướng dẫn khoá HA ở Hệ thống → Bảo mật &
  người dùng, khoá KHÔNG hiện ở trang này.
- Thanh chip dưới sticky: Tìm kiếm · Playlist (n) · Queue (a/b) · Loa &
  tivi · Cài đặt, bấm để cuộn tới mục, số đếm cập nhật khi tải lại.
- Tự làm mới trạng thái mỗi 20 giây (như mảnh tab). Trang dùng DOM API +
  `textContent`, không `innerHTML` với dữ liệu ngoài.

### 2. Thực thể điều khiển + endpoint hàng đợi (module youtube)

- `thuc_the()` trả HAI thực thể theo khuôn NV181 của youtube-phat:
  `youtube.xem` (rủi ro `doc`: `trang_thai`, `tim`, `danh_sach_playlist`,
  `cac_phien`) và `youtube.dieu_khien` (rủi ro `ghi`: `phat`, `dung`,
  `tam_dung`, `bai_ke`, `bai_truoc`, `tua`, `doi_loa`, `tao_playlist`,
  `xoa_playlist`, `phat_playlist`, `nhap_playlist`, `them_vao_playlist`,
  `them_vao_hang_doi`, `xoa_khoi_hang_doi`, `phat_tu_hang_doi`).
  Lược đồ tham số theo khuôn youtube-phat (`type: object`,
  `additionalProperties: False`, `required` ⊆ `properties`); lõi kiểm theo
  lược đồ SEC-004a nên tab chỉ gửi đúng trường đã khai.
- `thuc_hien()` điều phối qua `tich_hop` nội bộ (không qua HTTP); lỗi trả
  dict `{"ok": False, "loi": <tiếng thường>, "ma_loi": <code>}`, KHÔNG ném
  (try/except ngoài cùng chỉ log kiểu lỗi). `nhap_playlist` /
  `them_vao_playlist` / `tao_playlist` / `xoa_playlist` tự ghi
  `playlists.json` sau khi gọi đường `tich_hop` (đường đó mới tự ghi).
- `integration/queue` GET (`?session_id=` → `{session_id, queue,
  queue_index}`, phiên không sống → 404) và POST (`action: add` thêm mục
  đã chuẩn hoá, ≥ 500 bài → `400 queue_full`; `action: remove` xoá theo
  chỉ số, sai → `400 invalid_queue_index`; xoá trước chỉ số hiện tại thì
  chỉ số giảm 1, xoá đúng bài đang phát thì vị trí về 0 và bài kế thành
  bài hiện tại).
- `_tao_phien` nhận thêm `queue_index`: bên gọi chỉ rõ vị trí trong hàng
  đợi đưa thì dùng thẳng vị trí đó, khỏi tìm theo mục tiêu — đúng cả khi
  hàng đợi có bài trùng nhau (trước đây tìm theo id sẽ rơi về lần xuất
  hiện đầu tiên). `phat_tu_hang_doi` dùng cơ chế này: tạo phiên mới với
  cùng hàng đợi + cùng loa, tại đúng vị trí chọn; phiên cũ mất loa thì
  tự kết thúc theo luật «một loa chỉ thuộc một phiên».
- Cổng xác nhận: 409 `can_xac_nhan` chỉ áp cho hành động rủi ro
  `nguy_hiem` (`app/thiet_bi.py` bước 7); các hành động `ghi` của tab
  (phiên quản trị) không cần luồng xác nhận — giống youtube-phat (thực
  thể điều khiển của nó cũng `ghi`). Không hành động nào của module khai
  `nguy_hiem`.

### 3. Dedup lõi — yêu cầu (2) + (3) của file NV301

- `app/kham_pha.py`: `_chuan_hoa_giao_dien` giữ nguyên `False` (trước đây
  coi là sai định dạng rồi bỏ trường — module chỉ-công-cụ tự khai không
  có giao diện bị suy lại thành có mục); thêm `_chuan_hoa_thay_the`
  (tối đa 8 id, id hợp lệ, bỏ chính mình, giữ thứ tự; sai → cảnh báo và
  bỏ trường, không chặn nạp); `giao_dien_cua` trả None khi
  `giao_dien is False`; `kiem_manifest` gọi thêm `_chuan_hoa_thay_the`
  (bao phủ cả catalog vì `doc_manifest` gọi tới đây). Không allowlist
  chặn trường lạ — hai trường mới đi qua được.
- `app/so_module.py` `tinh_nang()`: tính `bi_thay` từ `thay_the` của mọi
  manifest trong catalog trước vòng lặp; mục: `None` khi module nằm trong
  `bi_thay`; danh sách `tab`: bỏ tab của module bị thay theo cùng quy
  tắc (bản khởi đầu chỉ ẩn mục — mảnh này mở rộng sang cả `tab`, nếu
  không tab «YouTube phát» vẫn hiện).
- Manifest: `modules/doc-viettat/manifest.json` thêm `"giao_dien": false`
  (module này chỉ có thực thể công cụ `chuan_hoa_doc`, không có trang
  hay thực thể cho người dùng); `modules/youtube/manifest.json` thêm
  `"thay_the": ["youtube-phat"]`.

## QUYẾT ĐỊNH TRUNG THỰC (ghi rõ để điều phối khỏi suy đoán)

1. **Quy tắc «đã cài thì thắng» cho `thay_the`**: module bị thay ẩn mục +
   tab khi module thay thế đã nằm trong `catalog` (đã cài), KỂ CẢ khi
   module thay thế chưa chạy. Cạnh này có test riêng: thay thế trong
   catalog nhưng chưa chạy → tab cũ vẫn ẩn; muốn tab cũ hiện lại thì gỡ
   module thay thế. Lý do: tránh trường hợp module thay thế đã cài nhưng
   tạm dừng mà tab cũ hiện lại gây hai tab YouTube.
2. **Chip «Nghe khi tắt màn hình» chỉ là ghi chú, không phải hành vi nền
   thật**: bấm thì hiện ghi chú rằng tab điều khiển loa/tivi nên tắt màn
   hình vẫn nghe được, không cần giữ tab mở sau khi đã phát. Không bịa
   hành vi nền (service worker / giữ tab) mà trang không có.
3. **Zing/Facebook phát được ghi phiên nhưng luồng 502**: trang hiện cảnh
   báo vàng rõ khi bài đang phát có nguồn Zing/Facebook — module chưa
   giải được luồng phát nên loa chưa phát được bài này (lỗi 502 khi lấy
   luồng), phiên chỉ ghi nhận bài. Không giấu trạng thái này.
4. **Ô Đời sống vẫn là ô trạng thái, trình phát đầy đủ nằm ở tab riêng**:
   không sửa `web/Doi-song.dc.html` và không đưa chữ «youtube» vào
   `app/`/`web/` (test doc_lap TRAN=0 vẫn xanh; một comment trong
   `app/kham_pha.py` từng nhắc tên module đã sửa lại cho khỏi vượt trần).
5. **Cài đặt không có trường nào**: theo QUY-TAC, bí mật chỉ ghi đè và
   khoá HA nằm ở «Bảo mật & người dùng», không hiện ở trang module.

## TEST ĐÃ CHẠY

- Mới `test/test_module_youtube_nv301_giao_dien.py`: **9/9 xanh**,
  đỏ-trước-xanh đã kiểm bằng stash (chưa có sửa thì 9 failed, có sửa thì
  9 passed, stash pop sạch). Bao phủ: `giao_dien: false` + `thay_the`
  chuẩn hoá; `tinh_nang()` ẩn mục/tab khi thay thế trong catalog (cả hai
  trạng thái: thay thế trong catalog → ẩn; gỡ thay thế → hiện lại);
  manifest thật doc-viettat/youtube; 2 thực thể + lược đồ tham số + không
  lộ khoá; vòng điều khiển trọn (tim/phat/tam_dung/tiếp tục/tua/doi_loa/
  cac_phien/dung + lỗi phiên không còn); playlist qua thực thể (tạo/thêm/
  trùng không thêm/phat_playlist/them_vao_hang_doi/phat_tu_hang_doi với
  bài trùng/xoa_khoi_hang_doi/xoa_playlist); nhập mã `TTPL1.` qua thực
  thể; endpoint queue GET/POST add/remove + lỗi biên; kiểm tĩnh trang
  tab (đủ id/chữ theo demo, không `innerHTML` với dữ liệu, không khoá,
  JS chỉ gọi hành động module đã khai).
- Bộ liên quan: mới + nv277 + nv301-loi + nv301-playlist + tab +
  duong_module_nv277 + kham_pha + hang_manifest + doc_lap =
  **87 passed**. Trong lúc làm, 2 test cũ đỏ đã sửa có lý do ghi rõ:
  (a) `test_web2api_doc_lap` TRAN=0 — comment trong `app/kham_pha.py`
  nhắc tên module, đã sửa comment (không sửa test, không miễn trừ);
  (b) test tab mảnh 1 khẳng định phần tử `trang-thai` của trang chỉ-đọc
  cũ — trang đó đã được viết lại thành trình phát theo đúng file NV301
  nên cập nhật khẳng định sang thẻ Đang phát (`ten-bai` +
  `thanh-tien-do`), giữ nguyên các khẳng định về bí mật và gọi qua thực
  thể.
- Bandit trên 3 file sửa (`module.py`, `kham_pha.py`, `so_module.py`):
  3 High — giống hệt base (kiểm bằng stash), có sẵn từ trước, không do
  mảnh này.
- Đỏ có sẵn KHÔNG do mảnh này: `test_module_youtube_phat.py::
  test_loai_thu_tu_la_so_nguyen_khong_trung` (trùng `loai_thu_tu` 47 giữa
  youtube-phat và nha-tien-ich; mảnh này không đụng manifest nào ngoài
  doc-viettat/youtube).
- README vẫn **414 dòng** (trần 415). Lõi không chứa tên module
  (`grep youtube app/ web/` trống ngoài youtube-phat).

## CHƯA NGANG / CHƯA KIỂM (không bịa là đã xong)

- **Chưa kiểm bằng Chrome thật**: máy làm việc không có Chrome thật nên
  không chụp ảnh đối chiếu demo được; file demo `/opt/claude-c2a/` cũng
  không có trên máy này — đối chiếu demo = mô tả demo trong file NV301.
  Sau khi gộp, cần mở tab YouTube trên trình duyệt thật ở 1280 px và
  375 px để đối chiếu hiển thị và kiểm ô Đời sống không còn vẽ thẻ thực
  thể thô.
- **Chưa thử với loa/HA thật.**
- Ngoài phạm vi 3 mảnh (ghi rõ, không khẳng định đã ngang dịch vụ cũ):
  giải luồng Zing/Facebook (502 rõ); `seek_url` trả None (rơ-le vé không
  có sidx — loa tua bằng Range); tự chuyển bài phía server không triển
  khai — HA mới là bên gọi next khi hết bài (module ghi rõ «chuyển bài
  là việc của HA»); lịch sử nghe lại chưa đưa vào trang tab (mục kết quả
  chỉ hiện sau khi tìm, không vẽ «Gợi ý cho bạn» giả).
- Mã chia sẻ `TTPL1.` đã xong ở mảnh playlist; nhập album/playlist Zing
  vẫn 502 (cần khoá API web Zing của dịch vụ cũ).
