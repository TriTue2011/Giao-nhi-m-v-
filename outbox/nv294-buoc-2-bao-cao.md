KẾT QUẢ — NV294 BƯỚC 2: BẢNG KIỂM THEO TỪNG TRANG, XẾP THEO MỨC ẢNH HƯỞNG, KHÔNG SỬA GIAO DIỆN

- Đã đẩy: nhánh `muse/nv294-buoc-2` (Giao main không đổi `82d9ff46`).
- Nền: web2api main `8ed35ab` (như bước 1).
- Patch: `outbox/nv294-buoc-2.patch` (178 dòng, 1 file mới, +171/−0).
  Patch chỉ chứa tài liệu kiểm, không chạm code giao diện; áp sạch lên
  cây mới clone từ main, và áp chung với patch bước 1 cũng sạch (hai
  patch không trùng file nên thứ tự gộp không quan trọng).
- File nộp kèm: `outbox/nv294-buoc-2-bao-cao.md` (báo cáo này).
- Tài liệu kiểm đầy đủ nằm trong patch:
  `docs/KIEM-GIAO-DIEN-NV294.md`.

## Phương pháp và phạm vi

Kiểm tĩnh bằng mã nguồn (máy này không có Chrome thật): đọc toàn bộ
`web/khung.css`, toàn bộ `web/*.dc.html`, `web/khung.js`,
`web/support.js`; đo tương phản bằng công thức WCAG từ hex trong mã;
grep các mẫu (gradient, emoji, chào mừng, `tabular-nums`,
`prefers-color-scheme`, trạng thái trống/lỗi/đang tải). Theo Taste v2,
màn hình quản trị được xử lý theo run app-screens (không phải run trang
đọc); theo Impeccable, dùng khung critique/audit cho màn hình vận hành
(Operate).

**Loại trừ, ghi rõ lý do:**

- `web/He-thong-AI.dc.html` (NV282): tệp trên main có mã đánh dấu NV282
  (khu «Tài khoản» theo demo bản 9), nhưng `git log` của main không có
  commit nào nhắc NV282 hay NV280 nên không xác nhận được NV282 đã gộp
  theo đúng nghĩa nhánh hay chưa. Theo brief («nếu chưa rõ thì loại»),
  loại cả trang này khỏi phạm vi kiểm.
- Bảng chi tiết Module (NV280): khối `chiTiet(x)` trong
  `web/He-thong.dc.html` (dòng ~1601). Phần còn lại của trang Hệ thống
  vẫn được kiểm.

## Phát hiện xếp hạng (tóm tắt — chi tiết trong tài liệu kiểm)

**CAO:**

- **C1. Tiêu đề trang không thống nhất; 8/11 màn hình giấu `h1`.**
  Hệ thống, Bảo mật, Phiên, Tích hợp, Trợ giúp, khung Module và cả ba
  trang khu đều dùng `h1` ẩn (`.an-chu`); chỉ Đăng nhập và Thiết lập có
  tiêu đề nhìn thấy (20px, kiểu nhãn mục) và Studio có tiêu đề chào
  46px căn giữa. Token `.tieu-de` 38px không trang nào dùng. Giai đoạn 3
  chốt một thang tiêu đề hiển thị.
- **C2. Chế độ tối chỉ có ở một khối, chưa phải hệ thống.** Toàn `web/`
  chỉ có đúng hai chỗ `prefers-color-scheme: dark`, cả hai trong khối
  làn (NV255) của trang Hệ thống; còn lại chỉ có sáng. Đây là quyết
  định phạm vi phải chốt với chủ máy trước mọi sửa khác (làm tối hệ
  thống hay ghi rõ «chỉ sáng» và bỏ hai chỗ lẻ).

**TRUNG BÌNH:**

- **T1. Không có trạng thái đang tải giữ khung** ở các trang dữ liệu
  (chỉ trang định tuyến có «Đang mở web2api…», chữ «Đang đo…» khi đo,
  nút submit khoá khi gửi). Giai đoạn 3 thêm «Đang tải…» giữ bố cục
  trước, rồi mới tính thanh xương.
- **T2. Số không dùng `tabular-nums`** ngoài trang AI (và một chỗ làn);
  số ở bảng và ô số liệu có thể nhảy ngang khi cập nhật. Giai đoạn 3
  thêm class số chung nhưng phải kiểm bằng Chrome rằng Be Vietnam Pro
  thực sự có chữ số bảng.
- **T3. Nhãn IN HOA có giãn chữ dùng ở nhiều chỗ** (`.nhan-muc` +
  `.bang-tb-dau`) vượt giới hạn «tối đa một nhãn in hoa có giãn mỗi màn
  hình» của chuẩn app-screens. Giai đoạn 3 gom về một loại.
- **T4. Mốc điện thoại 1023px của demo chưa từng đo ở 375px.** Tĩnh
  thấy nhiều chỗ bẻ dòng tốt (hàng bảng `flex-wrap`, bảng markdown
  cuộn trong khung, ô khu tối thiểu 230px nên ở 375px thành một cột),
  nhưng chưa có ảnh chụp nào; menu nổi 200px, hàng chip dài, cột chat
  880px, khung Module vẫn là điểm rủi ro.

**THẤP:** chữ 10px ở nhãn thanh dưới (máy tính để bàn; cảm ứng đã nâng
12px); chữ 11px rải rác; không có hộp thoại xác nhận thống nhất (không
có `<dialog>` nào, xác nhận rải rác như `window.confirm`); token chết
`.tieu-de`/`.nhan-tren` trong CSS (đã ghi trong `docs/DESIGN.md`).

**Điểm mạnh giữ nguyên, đừng sửa lùi:** tương phản chữ đạt AA toàn bộ
(bảng số đo trong `docs/DESIGN.md`); 0 gradient, 0 emoji chào mừng;
bóng chỉ ở menu nổi; nút chính màu mực; báo lỗi phủ rộng và nằm trong
khối; trạng thái trống có câu chữ thật; mục bấm 44px + ô nhập 16px trên
cảm ứng; viền focus 2px teal rõ; bí mật ẩn/ghi đè.

## Bảng theo từng trang

Có đủ trong `docs/KIEM-GIAO-DIEN-NV294.md`: 11 màn hình trong phạm vi
(Đăng nhập, Thiết lập, Studio, Hệ thống trừ khối NV280, Bảo mật,
khung Module, Phiên, Tích hợp, Trợ giúp, ba trang khu chung markup)
với 7 cột theo brief — mẫu AI slop, tương phản/khoảng cách/chữ, trống,
lỗi, đang tải, sáng–tối, điện thoại 375px — cộng một dòng cho trang
định tuyến `index.html` (không phải màn hình, nhưng có trạng thái tải
tốt «Đang mở web2api…»).

## Thứ tự sửa cho giai đoạn 3 (đã xếp sẵn trong tài liệu kiểm)

1. Chụp trước toàn bộ trang (sáng + tối hệ điều hành, 375px + 1280px).
2. Chốt phạm vi chế độ tối (C2) với chủ máy trước mọi sửa khác.
3. Chốt thang tiêu đề hiển thị (C1) + xử lý token chết cùng lúc.
4. Thêm «Đang tải…» giữ bố cục (T1).
5. Thêm class số bảng, kiểm phông thật (T2).
6. Gom nhãn IN HOA về một loại (T3) + nâng sàn chữ lên 12px.
7. Chụp sau, đối chiếu từng trang, rồi mới tính mẫu xác nhận thống nhất.

## Ranh giới và giới hạn

- Không sửa một dòng giao diện nào ở bước này: patch bước 2 chỉ có
  tài liệu kiểm. Không đụng trang AI (NV282) và khối chi tiết Module
  (NV280). Không đổi hành vi, id phần tử hay văn bản test khẳng định.
  Không thêm phụ thuộc, không thêm thư viện ngoài. Không ghi bí mật,
  khoá, IP thật, email thật hay vân tay thật (đã quét nhanh tài liệu
  mới: sạch).
- **Giới hạn lớn nhất: kiểm tĩnh, chưa nhìn bằng mắt.** Mọi dòng «chưa
  chụp» trong tài liệu kiểm đều có thể đổi kết luận khi có ảnh thật —
  nhất là bố cục 375px, hành vi lúc tải, và chữ số bảng của Be Vietnam
  Pro. Giai đoạn 3 bắt buộc chụp trước/sau (sáng/tối, 375px + 1280px)
  theo nghiệm thu NV294 trước khi chốt sửa.
- Giai đoạn 3 không làm trong lượt này, đúng brief, vì máy này không có
  Chrome thật.
