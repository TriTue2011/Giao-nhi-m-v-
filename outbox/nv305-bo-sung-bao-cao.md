# NV305 bổ sung — Bỏ hẳn biến môi trường mật khẩu VNC, chỉ tạo trong web UI

## KẾT QUẢ

- Nộp: nhánh Giao `muse/nv305-bo-sung` gồm `outbox/nv305-bo-sung.patch` (294 dòng, 9 file, +144/−30)
  + `outbox/nv305-bo-sung-bao-cao.md` (file này).
- Thứ tự gộp: **NV305 trước, rồi bổ sung này** (patch này là DELTA trên patch NV305, nền web2api
  `8ed35ab` + `outbox/nv305.patch` của NV305; đã kiểm áp sạch theo đúng chuỗi đó trên cây mới).
- Quyết người dùng thi hành (17:59 + 18:00 ngày 03/11, chọn tuỳ chọn «Bỏ hẳn biến môi trường, chỉ tạo
  trong web UI»): mật khẩu noVNC **CHỈ tạo trong web UI, KHÔNG đặt trong container** — vì bảo mật
  hiện tại tạm đủ tốt. Bổ sung này bỏ hẳn cơ chế biến môi trường làm mật khẩu ban đầu của NV305.
- Không đổi gì khác của NV305: ô mật khẩu vẫn trong «Bảo mật & người dùng» (ngay sau 2FA, chỉ quản
  trị), 1–8 ký tự ASCII in được, ghi-đè-không-đọc-lại, step-up khi ghi, giới hạn 10 lần/phút.

## Đã bỏ biến môi trường ở những file nào

1. `dich-vu/may-dang-nhap/entrypoint.sh` — bỏ HẲN khối tạo mật khẩu (cả hai nhánh: biến môi trường
   `CAPTCHA_SOLVER_MAT_KHAU_VNC` và sinh ngẫu nhiên `tr -dc … < /dev/urandom`). Entrypoint giờ KHÔNG
   BAO GIỜ tạo `/khoa/mat-khau-vnc`, không đụng vào tệp đã có trên đĩa. Chú thích trong file ghi rõ
   điều này và vẫn nhắc đường dẫn tệp (để test `test_c2a_dockerfile.py` biết tệp ở `/khoa`, không ở
   `/data`) — nhưng không còn lệnh ghi nào vào tệp đó.
2. `dich-vu/may-dang-nhap/README.md` §3.2 — viết lại mục mật khẩu VNC: bỏ đoạn «entrypoint sinh ngẫu
   nhiên», bỏ câu «chủ máy đọc mật khẩu bằng docker exec … cat /khoa/mat-khau-vnc», bỏ gạch đầu dòng
   «biến môi trường chỉ còn là mật khẩu ban đầu»; thay bằng gạch NV305-bo-sung (biến đã bỏ hẳn,
   entrypoint không tạo tệp, tệp đã có được giữ nguyên) + gạch «chưa từng đặt thì màn hình xem báo
   chưa đặt». Mục khoá dịch vụ (`khoa-dich-vu`, vẫn tự sinh ngẫu nhiên) KHÔNG đụng — đó là bí mật
   khác, không phải mật khẩu VNC.
3. Các chú thích mô tả cơ chế cũ đã sửa cho đúng hiện tại (không đổi hành vi): `src/main.py` (đường
   PUT: «Trước NV305 … từ NV305-bo-sung, entrypoint không còn tạo mật khẩu trong container»),
   `src/mat_khau_vnc.py` (tệp đánh dấu phân biệt với «tệp cũ còn sót từ trước»),
   `modules/may-dang-nhap/module.py` (ghi chú: chưa đặt thì lõi chặn ở đường `/xem`).

## Hành vi khi CHƯA đặt mật khẩu qua UI (điểm cần chủ máy biết rõ)

Đối chiếu đặc tả NV305: đặc tả có câu «Nếu mật khẩu chưa từng đặt thì vẫn dùng mật khẩu ngẫu nhiên
cũ». Bổ sung này hiểu câu đó theo quyết mới 18:00 như sau — và ghi rõ ở đây để chủ máy quyết nếu
muốn khác:

- «Mật khẩu ngẫu nhiên cũ» = **tệp mật khẩu đã có sẵn trên đĩa** (đặt qua giao diện từ trước, hoặc
  còn sót từ bản cũ từng để entrypoint sinh). Tệp đó được GIỮ NGUYÊN, không bị xoá hay ghi đè khi
  khởi động lại container.
- **Không tạo mới bất kỳ mật khẩu nào trong container**: không biến môi trường, không sinh ngẫu nhiên.
  Đây là điểm quyết mới đảo ngược đặc tả cũ (đặc tả cũ mặc định entrypoint luôn sinh một cái).
- **Chưa có tệp nào + chưa từng đặt qua giao diện** → x11vnc (đọc `-passwdfile`, không `-nopw`)
  không khởi động được và nằm FATAL cho tới khi chủ máy đặt mật khẩu qua giao diện; đường PUT khi
  đó nạp lại x11vnc (`supervisorctl restart x11vnc`) nên mật khẩu mới có hiệu lực ngay. **Không chạy
  x11vnc `-nopw` ngầm.**
- **Màn hình xem báo «chưa đặt mật khẩu»**: lõi từ chối cấp vé xem — `POST /api/trinh-duyet/{module}/xem`
  trả 400 «Chưa đặt mật khẩu xem trình duyệt — hãy đặt trong «Bảo mật & người dùng» trước khi mở màn
  hình xem.» — cho tới khi chủ máy đặt qua giao diện. Chặn này chỉ kích hoạt khi module trả lời dứt
  khoát `da_dat is False`; module không hỗ trợ trạng thái, hoặc hỏi trạng thái lỗi, thì đi đường cũ
  (fail-open có chủ đích: không chặn oan khi dịch vụ chập chờn; lỗi — nếu có — hiện ở bước mở xem).
  Lưu ý: tệp cũ còn sót nhưng chưa từng đặt qua giao diện thì xem vẫn bị chặn (mật khẩu cũ không ai
  biết thì mở cũng không vào được — cứ đặt mới qua giao diện là xong).
- Chỗ này **ghi rõ để chủ máy quyết nếu muốn khác**: nếu chủ máy muốn quay lại «chưa đặt thì vẫn
  dùng mật khẩu ngẫu nhiên cũ (tự sinh trong container)», đó là đảo ngược quyết 18:00 và cần nói rõ.

## Đảo ngược quy tắc kiểm entrypoint cũ (cần biết khi soát)

`dich-vu/may-dang-nhap/test_c2a_dockerfile.py::kiem_entrypoint` trước đây BẮT BUỘC entrypoint sinh
mật khẩu VNC 8 ký tự (`head -c 8` + `A-Za-z0-9`) — quy tắc đó chính là hành vi quyết 18:00 bỏ đi, nên
kiểm tra này đã đảo theo: giờ nó CẤM biến môi trường, CẤM sinh ngẫu nhiên (`urandom`/`tr -dc`), CẤM
ghi tệp (`> /khoa/mat-khau-vnc`); các kiểm còn lại giữ nguyên (tạo `/tmp/.X11-unix` 1777, cấm
`od -tx1`, cấm in mật khẩu ra stdout). Test đột biến `test_dot_bien_entrypoint` được thêm 2 ca: dùng
lại biến môi trường và sinh ngẫu nhiên lại đều phải bị phát hiện. Đây là sửa kiểm theo quyết, không
phải nới kiểm để qua test.

## Test (đỏ-trước-xanh, đã chạy)

- Mới: dịch vụ 1 test entrypoint (không biến môi trường, không sinh ngẫu nhiên, không lệnh ghi tệp)
  + lõi 4 test xem (chặn khi chưa đặt + không gọi `trinh_duyet_xem_mo`; mở được khi đã đặt; không
  chặn khi module không có trạng thái; không chặn khi hỏi trạng thái lỗi).
- Đỏ-trước-xanh: trên nền chỉ-NV305, test entrypoint mới FAIL (biến còn đó) và test chặn-xem mới
  FAIL (xem vẫn mở 200); 3 test xem còn lại đã xanh từ trước (hành vi đi đường cũ giữ nguyên).
- Sau sửa: file dịch vụ NV305 **21/21 xanh** (NV305: 20 + 1 mới); file lõi NV305 **21/21 xanh**
  (NV305: 17 + 4 mới).
- Tập liên quan: lõi (NV305 + NV276 xem + NV276 xem-trình-duyệt + NV25/NV54 noVNC + C6 + NV274 +
  NV271) **125 passed, 2 skipped, 0 failed**; dịch vụ (NV305 + c2a_dockerfile + c2a_trinh_duyet_that)
  **41 passed, 1 skipped, 0 failed**.
- Đối chiếu nền sạch (cùng tập, cây chỉ-NV305 qua worktree riêng): lõi 121 passed / 2 skipped, dịch
  vụ 40 passed / 1 skipped — chênh đúng +4 lõi +1 dịch vụ = đúng số test mới, **không lệch nào khác
  do bổ sung này**.
- Kiểm tĩnh: `py_compile` các file Python đổi, `sh -n` entrypoint.sh, patch áp sạch theo chuỗi
  NV305 → bổ sung trên cây mới.
- Quét: tên biến môi trường chỉ còn trong README (câu «biến đã bỏ hẳn») và trong test (khẳng định
  nó vắng mặt) — không còn chỗ nào dùng nó làm mật khẩu. Không mật khẩu thật nào trong patch/báo
  cáo/log; test chỉ dùng mật khẩu tự tạo; không dùng, không chép lại bất kỳ mã/mật khẩu nào người
  dùng từng gửi trong chat.

## Chưa thử thật (trung thực, thuộc vòng sau gộp + lên server)

- Endpoint thật của dịch vụ qua TestClient (máy này thiếu `patchright` nên không import được
  `src.main` — giống giới hạn của NV305; test dịch vụ dừng ở hàm thuần + kiểm nội dung entrypoint).
- Toàn suite lõi (RAM lúc làm chật vì các agent khác chạy song song; chỉ chạy tập liên quan + đối
  chiếu nền sạch như trên).
- Chrome thật (máy này không có Chrome); bandit (không có trong venv — điều phối chạy ở vòng soát).
- Hành vi container thật: entrypoint mới + x11vnc FATAL-cho-tới-khi-đặt chưa chạy trong container
  thật ở đây (kết luận từ `supervisord-novnc.conf`: x11vnc `-passwdfile`, `autorestart=true`,
  `startretries` mặc định → sau vài lần hỏng sẽ FATAL; PUT nạp lại bằng `supervisorctl restart`).
  Sau khi gộp + lên server, cần thử: (1) container lên với volume `/khoa` trống + noVNC bật → xem
  báo chưa đặt; (2) đặt qua giao diện → xem mở được bằng mật khẩu vừa đặt; (3) khởi động lại
  container → mật khẩu vẫn dùng được, không bị ghi đè; (4) volume cũ còn tệp ngẫu nhiên → xem báo
  chưa đặt cho tới khi đặt mới qua giao diện.
