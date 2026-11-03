# KẾT QUẢ — NV309-b: hồ sơ Grok need_manual vào diện chờ người (SAI S2)

> Base: web2api main 8ed35ab. Nhánh nộp: muse/nv309-b — CHỈ nhánh muse/*,
> không đẩy main, không force-push. Bảng đối chiếu: outbox/nv309-doi-chieu.md
> trên nhánh muse/nv309-doi-chieu. Nhiệm vụ gốc: inbox/NV309.md.
> Trạng thái kiểm thật: CHƯA THỬ TRÊN TRÌNH DUYỆT THẬT (xem «Kế hoạch kiểm thật»).
> Mảnh này độc lập với (a) (vùng khác: dịch vụ may-dang-nhap, không phải
> lõi/modules); thứ tự gộp chung vẫn là (a) → (b) → (c).

## 1. Vấn đề — code tự mâu thuẫn với ý đồ của nó (không phải «khác c2a nên sai»)

Theo đính chính 16:58 ngày 03/11: khác c2a không tự động là sai; mỗi điểm phải
được test chứng minh. S2 qua được tiêu chuẩn đó bằng mâu thuẫn nội tại:

- `dich-vu/may-dang-nhap/src/grok_web_login.py::_chay` CỐ Ý GIỮ cửa sổ ở trạng
  thái `need_manual` (comment: «chủ máy sắp vào noVNC tích ô xác minh, đóng đi
  là đóng đúng thứ họ cần») và chỉ dọn khi `success`/`failed`.
- Nhưng `finally` gọi `pool.xong_dang_nhap` gỡ cờ đang-đăng-nhập, nên hồ sơ
  không còn cờ nào → vòng quét `browser_pool._quet_nhan_roi` nhánh thường đóng
  cửa sổ sau 300 giây nhàn rỗi theo `last_used` (không tính `last_view`).
- Hậu quả: chủ máy vào noVNC muộn hơn 5 phút thì cửa sổ đã mất, dù thông điệp
  nói «Cửa sổ vẫn đang mở» — thông điệp sai, không phải chỉ khác c2a.
- UI tài khoản AI KHÔNG ĐỔI (đang đúng, giữ nguyên theo đính chính).

## 2. Cách sửa — dùng diện chờ người ĐÃ CÓ trong cùng file

Không port nguyên xi c2a, không bịa hạn mới: diện chờ người (600 giây + tính
`last_view`, `HAN_KHONG_HOAT_DONG_GIAY`) đã tồn tại trong `browser_pool.py`
cho hồ sơ đang-đăng-nhập/mở tay từ NV300. Mảnh này chỉ xếp `need_manual` vào
đúng diện đó:

- Pool thêm cờ `_cho_nguoi` + `danh_dau_cho_nguoi` / `dang_cho_nguoi`, theo
  đúng mẫu `_dang_dang_nhap` / `_manual_profiles` sẵn có.
- `_quet_nhan_roi`: `co_co` = đang-đăng-nhập HOẶC mở tay HOẶC chờ người;
  hạn chờ người = 600 giây (hàm `_han_khong_hoat_dong` đã trả 600 cho hồ sơ
  không phải mở tay — không đổi hạn nào). Quá hạn → đóng + bỏ cờ (không giữ
  vô thời hạn gây tràn RAM). Cờ được bỏ cùng mọi điểm dọn cờ khác
  (evict, close_profile, context tự đóng, stop).
- `_giu_cho_ngu_canh` (nhả chỗ khi chạm trần 2 ngữ cảnh): không nhả hồ sơ chờ
  người để lấy chỗ — việc của người đang chờ không bị giết vì áp lực trần.
- `_chay` (grok_web_login): sau `xong_dang_nhap`, nếu state là `need_manual`
  thì đánh dấu chờ người.
- Thông điệp: cả hai điểm `need_manual` (Cloudflare ở trang chủ và ở màn đăng
  nhập) mang hạn thật — «Cửa sổ giữ tối đa 10 phút nếu không có hoạt động
  (xem màn hình sẽ gia hạn)» — tính từ `HAN_KHONG_HOAT_DONG_GIAY`, không gõ
  cứng số rời rạc. Không đổi ngữ nghĩa challenge → can_nguoi (Q4).
- Phạm vi: chỉ Grok `need_manual`. Các luồng khác có trạng thái cần người mà
  CHỦ Ý đóng trình duyệt (NV209: selfie/phone/lock → need_human + đóng) giữ
  nguyên, không đụng.

## 3. Thay đổi (file đầy đủ — xem patch kèm theo)

- `dich-vu/may-dang-nhap/src/browser_pool.py`: cờ `_cho_nguoi`, 2 phương
  thức mới, `co_co` ở 2 lượt kiểm của `_quet_nhan_roi`, bỏ cờ khi evict,
  loại chờ-người khỏi ứng viên nhả trần, bỏ cờ ở `_attach_close_handler` /
  `close_profile` / `stop`.
- `dich-vu/may-dang-nhap/src/grok_web_login.py`: import
  `HAN_KHONG_HOAT_DONG_GIAY`, đánh dấu chờ người trong `_chay`, 2 thông điệp
  `need_manual` mang hạn.
- Mới: `dich-vu/may-dang-nhap/test_nv309_b.py` (4 test, xem §4).

## 4. Test — đỏ-trước-xanh, khẳng định hành vi đúng

- Mới: `dich-vu/may-dang-nhap/test_nv309_b.py` — 4 test, đỏ trước (3 test quét:
  `AttributeError: danh_dau_cho_nguoi`; 1 test `_chay`: cờ chưa được đánh dấu),
  xanh sau:
  - need_manual nhàn 301 giây theo `last_used` nhưng vừa có người xem
    (`last_view` mới) → KHÔNG đóng.
  - need_manual quá 600 giây không hoạt động (cả 2 mốc đều cũ) → đóng + bỏ cờ.
  - `last_view` mới gia hạn qua 600 giây `last_used` → giữ.
  - `_chay` kết thúc ở `need_manual` (trang bị chặn Cloudflare) → pool mang cờ
    chờ người và thông điệp chứa «10 phút».
- Liên quan hiện có: 71 test xanh (vòng đời NV300, grok cach, NV231, NV209,
  NV271) + 48 test lõi chạm dịch vụ xanh (nv145b, nv276, nv210).
- Toàn suite lõi: không chạy lại cho mảnh này (vùng đổi chỉ nằm trong dịch vụ
  may-dang-nhap; các file lõi chạm dịch vụ chạy ở trên). Dịch vụ không có
  suite riêng toàn cục ngoài các file test trong `dich-vu/may-dang-nhap/`.

## 4b. Chứng minh theo từng loại — luật thứ tự 17:52 ngày 03/11

Luật: làm phần đăng nhập trước, xong mỗi loại = lấy được cookie/session;
tuần tự từng loại một, Grok trước (ca lỗi nêu đầu trong NV309 + NV293 thử
Grok trước rồi mới Claude). Áp vào mảnh này:

- **Grok — XONG Ở MỨC TEST**: cờ chờ người + thông điệp hạn đã chứng minh
  bằng 4 test tự động (§4). Kiểm thật MCP → noVNC thao tác tay (§5) chờ vòng
  sau gộp (cần tài khoản cho phép + bản dựng mới).
- **Các loại khác — CHƯA TỚI LƯỢT / NGOÀI PHẠM VI (b)**: mảnh này chỉ sửa
  Grok `need_manual`. Các luồng khác có trạng thái cần người mà chủ ý đóng
  trình duyệt (NV209) giữ nguyên, không nhận đã xong hay đã sửa.

## 5. Kế hoạch kiểm thật — MCP trước, noVNC THAO TÁC TAY sau

Chưa kiểm thật ở đây (không có tài khoản cho phép + bản dựng mới; không nhận
đã kiểm thật khi chưa kiểm). Theo phương pháp 17:38 ngày 03/11, noVNC là để
chủ máy THAO TÁC TAY, không chỉ xem. Sau khi điều phối gộp + dựng lại:

1. **MCP trước**: chạy lượt Grok onboard thật qua MCP tới trạng thái
   `need_manual` (Cloudflare chặn), xác nhận lượt trả đúng state + thông điệp
   mang hạn 10 phút.
2. **noVNC thao tác tay sau**: chủ máy vào noVNC muộn hơn 5 phút (vượt 300
   giây cũ) và xác nhận cửa sổ VẪN MỞ; tự tích ô «Xác minh bạn là con người»
   bằng tay, rồi gọi lại onboard và xác nhận lượt tiếp tục được (cửa sổ không
   bị đóng giữa chừng). Đồng thời xác nhận: không hoạt động quá 10 phút thì
   cửa sổ đóng thật (tránh tràn RAM), và xem màn hình gia hạn được hạn.
   Lưu ý: chính mảnh này là điều kiện để phương pháp 17:38 thực hiện được —
   nếu cửa sổ vẫn đóng sau 300 giây thì chủ máy vào muộn không còn gì để
   thao tác tay.
3. Cơ chế xem noVNC dùng mật khẩu NV305 sau khi triển khai — agent không dùng,
   không sao chép bất kỳ mã nào người dùng đã gửi.

### 5.1. Các ô CHƯA được xác nhận bằng tay qua noVNC

Mảnh này KHÔNG thêm/sửa selector nào (chỉ vòng quét + thông điệp). Các ô cần
chủ máy chọn đúng bằng tay ở vòng kiểm thật (selector sẵn có, test giả KHÔNG
chứng minh selector thật):

- Ô «Xác minh bạn là con người» (Cloudflare) trên grok.com — ô mà cả luồng
  need_manual này chờ người tích.
- Các ô đăng nhập Grok (email, Tiếp tục, mật khẩu, «Sign in with Google») —
  xem danh sách đầy đủ ở báo cáo (a); không ô nào được coi là «đã xác nhận»
  cho tới khi chủ máy thao tác tay qua noVNC.

## 6. Câu hỏi chủ máy trong bảng (ghi lại, KHÔNG đoán đáp án)

- Q1: lịch nền giữ BẬT mặc định 1800 giây hay học c2a TẮT mặc định + 3 giờ?
- Q2: thứ tự ưu tiên tài khoản có cấu hình được không? (mảnh (d) đang chờ Q2.)
- Q3: sau lượt MCP thành công có đóng thật workspace không (hiện chỉ đóng
  controller, giữ workspace để tái dùng)?
- Q4: gặp challenge thì giữ «challenge → can_nguoi» hay học c2a «cf_chan ≠ het,
  vẫn dùng cookie cũ»? (Mảnh này KHÔNG đổi ngữ nghĩa đó.)
- Mảnh (d) (xoay vòng theo thứ tự ưu tiên + thử lại 1 lần qua làm mới, SAI S4)
  vẫn đang chờ Q2 — không làm trong lượt này, không tự đoán thiết kế.
