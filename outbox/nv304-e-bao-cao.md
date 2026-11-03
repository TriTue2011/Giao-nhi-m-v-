# NV304 mảnh (e) — BÁO CÁO

## KẾT QUẢ

Mảnh (e) XONG, đã đẩy nhánh Giao `muse/nv304-e` (xem «Xác minh nộp» cuối
báo cáo): **trang tab trình phát bám sát demo `ANH-DUNG-Doi-song.png`
+ mã `Doi-song.dc.html`, và lỗi HTTP 409 khi Phát/Dừng/Tìm đã có đường
sửa đúng quy tắc NV298** (xác nhận một lần lúc gọi, trong chính tab
module). Patch là **DELTA trên mảnh (c)**, không chứa lại (a)/(b)/(c).
Thứ tự gộp: **(a) → (b) → (c) → (e) → (d)** — (e) chèn trước (d) vì (d)
chỉ port test cũ của module, không đụng trang tab.

## Nền và nguồn thắng

- Nền web2api: main `5f4df48` (như (a)–(c)).
- File nhiệm vụ kiểm lại lúc nộp: Giao main `3d5c37b0`, `inbox/NV304.md`
  bản «CẬP NHẬT 03/11 CHIỀU» (demo + ảnh hiện trạng + yêu cầu sửa 409).
- Demo đã đọc: `inbox/tai-lieu/demo/DOC-TRUOC.md`,
  `Doi-song.dc.html` (mã nguồn, breakpoint 1023px, nút 40px, thẻ bo
  14px) và ảnh `ANH-DUNG-Doi-song.png` (đã xem trực tiếp: chip nguồn +
  ô tìm viên thuốc + nút tìm tròn xám ở trên cùng; thẻ đang phát bên
  trái chứa cả nhóm; «Gợi ý cho bạn N mục» bên phải; chip dưới Tìm
  kiếm · Playlist (n) · Queue (a/b) · Loa & tivi · Cài đặt có biểu
  tượng).
- **support.js VẪN THIẾU** (đã kiểm toàn bộ cây main `3d5c37b0`, không
  có file nào tên đó) nên demo chưa chạy được đúng nghĩa bằng
  http.server + Chrome từ máy này — mảnh (e) bám theo mã `.dc.html` +
  ảnh `ANH-DUNG-*` + mô tả file NV304, và vẫn cần điều phối/chủ máy gửi
  bổ sung support.js để đối chiếu ảnh chụp thật sau khi dựng lại (câu
  hỏi mở, không chặn (e)). File NV304 nhắc `Doi-song-DUNG.png` nhưng
  file thực tế là `ANH-DUNG-Doi-song.png` (nhiều khả năng cùng một ảnh,
  khác tên).

## Đã làm — bám demo

Chỉ sửa `modules/youtube/web/index.html` + `trang.js` (không đụng lõi
hay module):

1. **Ô tìm viên thuốc + nút tìm tròn xám:** input tìm thêm lớp
   `.o-tim-tron` (bo 999px, nền nhạt); nút «Tìm» chữ đổi thành nút tròn
   xám 40px có kính lúp SVG (`aria-label="Tìm"`, giữ nguyên id `nut-tim`
   nên dây nối JS không đổi).
2. **Nút vận chuyển tròn có biểu tượng:** Bài trước / Bài kế thành nút
   tròn 40px SVG; Phát thành nút tròn đen LỚN 56px (đúng demo: nút Phát
   nổi bật giữa hàng vận chuyển) với hai SVG phát/tạm dừng đổi nhau qua
   `hidden` + `aria-label` (không dùng `innerHTML`, không dùng emoji
   làm biểu tượng); Dừng thành ô vuông đỏ 40px có hình vuông đỏ (đúng
   demo: nút Dừng là ô vuông đỏ, không tròn).
3. **Nhóm nằm trong thẻ Đang phát:** mục «Nhóm đang phát» dời từ thẻ
   riêng thành mục con bên trong `<section>` Đang phát (đúng demo: thẻ
   đang phát chứa cả nhóm bên dưới nút vận chuyển). Mọi id giữ nguyên
   nên test (b) về cột trái vẫn xanh.
4. **Chip dưới có biểu tượng:** 5 chip (Tìm kiếm, Playlist (n),
   Queue (a/b), Loa & tivi, Cài đặt) thêm SVG biểu tượng (kính lúp,
   nốt nhạc, hàng đợi, loa, bánh răng — lấy đúng đường nét của demo
   cho 4 cái đầu); số lượng Playlist/Queue vốn đã có từ NV301, giữ
   nguyên.
5. **Tiêu đề kết quả có số mục:** sau mỗi lần tìm, tiêu đề đổi thành
   «Kết quả (N mục)» (đúng dạng «Gợi ý cho bạn 8 mục» của demo; trang
   thật chỉ có kết quả tìm, không có nguồn gợi ý nên giữ chữ «Kết
   quả»).
- Những điểm demo KHÔNG sao chép (ghi rõ lý do): sóng âm trang trí
  trong thẻ đang phát (demo minh hoạ, không phải dữ liệu thật); ảnh
  bìa tròn + tên kênh demo (trang thật dùng ảnh bìa 16:9 của bài);
  thanh chính Studio · Tác phẩm · Nhà · Đời sống · Hệ thống (đó là
  khung chung, không phải trang tab; tab YouTube biến mất khỏi thanh
  Hệ thống đã làm ở (a) bằng `an_khoi_thanh`, chỉ chờ điều phối dựng
  lại là thấy — ảnh hiện trạng 409 chụp TRƯỚC khi (a) gộp nên vẫn còn
  tab cũ).

## Đã làm — sửa HTTP 409

### Nguyên nhân đã xác định từ mã (không đoán mò)

- Lõi `app/thiet_bi.py` (`thuc_hien_hanh_dong_loi`, bước 7): thực thể
  có rủi ro hiệu lực `nguy_hiem` mà lệnh quản trị không kèm
  `xac_nhan: true` → **409 `can_xac_nhan`**. Ngoài ra
  `app/tuyen.py` còn bắt step-up cho phiên cookie (thiếu → 403
  `step_up_required`, không phải 409).
- Trang tab (NV301) gọi lệnh ghi trực tiếp, KHÔNG kèm `xac_nhan`, cũng
  KHÔNG xem rủi ro thực thể — nên trên server nào đã nâng rủi ro của
  `youtube.dieu_khien` (qua giao diện đặt rủi ro của NV298), Phát/Dừng
  đều ăn 409. Trang còn giấu mất thân lỗi (chỉ hiện «HTTP 409») nên
  không phân biệt được 409 `can_xac_nhan` với 409 `queue_end` của
  module.
- Với rủi ro mặc định (`xem` = doc, `dieu_khien` = ghi) thì không có
  409 — đường sửa dưới đây KHÔNG đổi hành vi mặc định, chỉ thêm đường
  xác nhận khi rủi ro là nguy hiểm.

### Đường sửa (đúng mẫu NV298 trong `web/khung.js`)

- `timThucThe` lưu thêm `rui_ro` hiệu lực của hai thực thể (danh sách
  thực thể của lõi đã trả trường này).
- Lệnh GHI (`hanhDong`): nếu `dieu_khien` đang nguy hiểm thì hỏi xác
  nhận TRƯỚC khi gọi (hộp `hoi-xac-nhan` trong trang: chữ + nút «Xác
  nhận» / «Thôi»); bấm Xác nhận mới gửi kèm `xac_nhan: true`.
- Dự phòng khi rủi ro đổi sau khi trang đã tải: gặp 409 có
  `error.code === 'can_xac_nhan'` thì hỏi rồi gửi lại kèm
  `xac_nhan: true` (cả lệnh đọc lẫn lệnh ghi).
- Mọi lỗi khác hiện **thông điệp của server** (`error.message`) thay
  vì chỉ mã HTTP — để 403 step-up («Thao tác quản trị yêu cầu xác nhận
  lại») và 409 `queue_end` («đã ở đầu/cuối hàng đợi») hiện rõ nghĩa.
- Từ chối xác nhận thì không làm gì (trả `daHuy`, bên gọi bỏ qua,
  không hiện lỗi); ba điểm gọi đọc chính (`taiTrangThai`, `timKiem`,
  `taiPlaylist`) kiểm tra `daHuy` để không vẽ dữ liệu rỗng sai.
- Lệnh ĐỌC không hỏi trước (quy tắc NV298 chỉ bắt xác nhận cho lệnh
  GHI); step-up 403 vẫn cần người dùng xác nhận lại trong giao diện
  quản trị (trang tab không tự làm step-up được — chỉ hiện rõ thông
  điệp để người dùng biết).

## Kiểm chứng

- Test mới `test/test_module_youtube_nv304_e.py`: **7/7 xanh** (đỏ
  trước: 6/7 đỏ khi chưa có code). Nội dung: ô tìm tròn + nút tìm tròn
  có SVG; nút vận chuyển tròn có SVG + nhãn (Phát lớn 56px, Dừng ô
  vuông đỏ); nhóm nằm trong thẻ Đang phát (parser cây section); 5 chip
  dưới đều có SVG; tiêu đề kết quả có số mục; hộp xác nhận +
  `can_xac_nhan` + `xac_nhan` trong mã; không `innerHTML`.
- Bộ liên quan: (e) + (c) + (a) + (b) + NV301 giao diện/tab/lõi/
  playlist + NV277 + route NV277 + doc_lap + khu NV297 = **105 passed,
  8 skipped** (lý do skip sẵn có). `node --check trang.js` sạch. Taste
  lint `--app` trên hai tệp trình phát: **0 FAIL, 3 WARN** — giữ
  nguyên có lý do (zero-padding là định dạng đồng hồ; «—» là dấu câu
  tiếng Việt, số lượng tăng do câu chữ mới thêm trong (e) nhưng vẫn
  chỉ là dấu câu).
- Patch áp nối tiếp (a) → (b) → (c) → (e) lên nền `5f4df48` bằng
  `git apply` THẬT trên worktree nền sạch: sạch.
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật.

## Chưa làm / cần chủ máy (ghi rõ, không nhận vơ)

- **Chưa thử trên HA thật, chưa kiểm Chrome thật** (máy này không có
  Chrome): sau khi điều phối dựng lại, cần kiểm trên HA thật rằng:
  (1) Phát/Dừng/Tìm chạy được — đặc biệt trên server đã nâng rủi ro
  (hộp xác nhận phải hiện đúng một lần rồi lệnh chạy); (2) tab
  «YouTube» đã biến khỏi thanh Hệ thống và trình phát hiện trong tab
  Đời sống; (3) chụp ảnh trang tab ở 375px + 1280px đối chiếu với
  `ANH-DUNG-Doi-song.png` (cần support.js bổ sung để chạy demo đúng
  nghĩa nếu muốn đối chiếu pixel).
- Nếu trên server rủi ro KHÔNG phải nguy hiểm mà vẫn 409: báo lại mã
  lỗi trong thân phản hồi (nay trang đã hiện thông điệp server) để
  xác định tiếp — đừng kết luận vội là do xác nhận.

## Xác minh nộp

- Nhánh Giao: `muse/nv304-e` = `3fbdd8a55ab698743bbffc45c1c66ed07fe9e16b`
  (kiểm bằng ls-remote; Giao main lúc đẩy không đổi `3d5c37b0`).
- Patch: `outbox/nv304-e.patch` trên nhánh (385 dòng, 3 tệp).
- Commit repo: `a6b7686` «NV304e: bam demo (o tim tron, nut tron, nhom
  trong the phat) + sua 409 xac nhan», cha là commit (c) `d4c4483`.
- Thứ tự gộp: (a) → (b) → (c) → (e) → (d); (e) là delta trên (c).
