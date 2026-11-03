# NV305-bao-mat — Bảo mật tab «Bảo mật & người dùng» + công tắc màn hình xem

## KẾT QUẢ

- Nhánh Giao: `muse/nv305-bao-mat` (tip kiểm bằng ls-remote sau khi đẩy — xem báo cáo nộp).
- Patch: `outbox/nv305-bao-mat.patch` — 1918 dòng, 16 file (+1556/−42), delta trên NV305 →
  NV305-bo-sung, nền web2api `8ed35ab`; đã kiểm áp sạch theo đúng chuỗi NV305 → bo-sung →
  bổ sung này trên cây mới clone từ main, test mới xanh tại đó.
- Thứ tự gộp bắt buộc: NV305 → NV305-bo-sung → bổ sung này.
- Test mới: lõi `test/test_nv305_bao_mat.py` (30 test) + dịch vụ
  `dich-vu/may-dang-nhap/test_novnc_bat_tat.py` (10 test, module thuần stdlib) — đều xanh.
  Test dịch vụ NV305 cũ 21/21 xanh, test entrypoint (`test_c2a_dockerfile.py`) xanh kèm kiểm cờ
  bền mới; tổng 47/47 xanh trên cây kiểm mới.
- Toàn suite lõi vs nền sạch (bỏ 8 file muse2api lỗi thu thập sẵn có trên nền vì thiếu module
  `google` trong venv): nền sạch 161 failed / 5947 passed / 273 skipped / 31 xfailed / 17 errors;
  cây đã sửa 160 failed / 5978 passed / 273 skipped / 31 xfailed / 17 errors — KHÔNG lỗi mới
  (lỗi chỉ-có-ở-cây-đã-sửa: 0; 1 lỗi nền được sửa xanh nhờ bổ sung tài liệu: test README).
  Xem mục 6.
- Thi hành đủ phương án mới 19:19 ngày 03/11 + chốt hiển thị 19:26 («Chỉ hiện khi dùng mk admin
  hoặc 2fa», không ngoại lệ cho mật khẩu noVNC). Quyết 18:00 vẫn giữ: mật khẩu noVNC CHỈ tạo
  trong web UI, KHÔNG đặt trong container.

## 1. Quy tắc xác thực lại áp cho những thao tác nào (a)

Cơ chế: step-up sẵn có (`kiem_tra_step_up` + `POST /api/toi/xac-nhan-lai`), mở rộng thêm trường
`ma_2fa`. Không chế cơ chế xác thực mới.

| Thao tác trong tab | Trước | Sau |
|---|---|---|
| Tạo khoá khách `POST /api/khoa-khach` | không cần step-up | cần step-up |
| Xoá khoá khách `DELETE /api/khoa-khach/{id}` | không cần step-up | cần step-up |
| Xoay khoá | đã có step-up | giữ nguyên |
| Tạo người dùng `POST /api/nguoi-dung` (mọi vai) | chỉ tạo admin mới cần step-up | MỌI tạo đều cần step-up |
| Sửa người dùng (đổi vai/bật) | đã có step-up | giữ nguyên |
| Đặt lại mật khẩu người khác | đã có step-up | giữ nguyên |
| Xoá tài khoản `DELETE /api/nguoi-dung/{id}` | không cần step-up | cần step-up |
| Đặt mật khẩu VNC `PUT /api/trinh-duyet/mat-khau-vnc` | đã có step-up | giữ nguyên |
| Bật/tắt noVNC `POST /api/trinh-duyet/man-hinh/bat-tat` (mới) | — | cần step-up |
| Đổi mật khẩu chính mình `POST /api/toi/mat-khau` | luôn cần mật khẩu cũ | 2FA bật → CHỈ cần mã 2FA, không cần mật khẩu cũ (mật khẩu cũ gửi kèm bị bỏ qua); 2FA tắt → giữ nguyên |
| Tắt 2FA hộ `POST /api/nguoi-dung/{id}/tat-2fa` | chỉ cần admin + CSRF | GIỮ NGUYÊN (không gắn step-up — xem mục 8) |

Quy tắc bằng chứng ở `/xac-nhan-lai` (và hộp thoại của `khung.js` đã hỏi đúng loại):
- Chưa bật 2FA → nhập lại mật khẩu admin (như cũ).
- Đã bật 2FA → CHỈ mã 2FA (TOTP hoặc mã khôi phục, kèm chống phát lại sẵn có); mật khẩu gửi lên
  bị từ chối ngay với mã `can_ma_2fa` (không xác minh mật khẩu, không đếm sai đăng nhập).
- Khoá quản trị Bearer vẫn được chấp nhận ở `/xac-nhan-lai` (bí mật gốc, không phải mật khẩu) —
  ghi rõ, không giấu. Riêng đường HIỂN THỊ thì không có miễn trừ này (mục 2).

Giao diện: `khung.js` đổi hộp thoại step-up thành `hoiBangChungXacNhanLai()` — hỏi mã 2FA khi
người hiện tại đã bật 2FA (`/api/toi` nay trả thêm cờ `bat_2fa`, fail-closed = true khi kho hỏng),
hỏi mật khẩu khi chưa bật. Test cũ `test_web2api_nv182_step_up_hanh_dong.py` cập nhật theo tên hàm
mới + khẳng định cả hai nhánh (mật khẩu và mã 2FA), vẫn cấm innerHTML.

## 2. Ẩn sau khi tạo + hiện sau xác thực lại (b) — thay never-return của NV305

- Mật khẩu noVNC: sau khi đặt thì ẩn. Hiển thị lại qua `POST /api/trinh-duyet/mat-khau-vnc/hien`
  (mới) với bằng chứng TƯƠI trong chính body lời gọi — mật khẩu admin khi chưa bật 2FA, CHỈ mã
  2FA khi đã bật 2FA (mật khẩu bị từ chối, không xác minh). KHÁC step-up ở hai điểm có chủ đích:
  (1) không dùng cửa sổ step-up (cửa sổ có thể đã mở từ trước); (2) không miễn Bearer quản trị —
  mọi lời gọi hiển thị đều phải kèm bằng chứng trong body, đúng chốt 19:26 «không có đường hiển
  thị nào khác». Giới hạn tần suất 10 lần/60 giây/người gọi (chung bộ đếm với đường đặt).
  Lõi chuyển qua module `may-dang-nhap` tới `GET /v1/novnc/mat-khau` của dịch vụ; không có tệp
  đánh dấu (chưa đặt qua giao diện) thì dịch vụ trả 400. Đây là phản hồi DUY NHẤT trong lõi chứa
  mật khẩu VNC; nhật ký chỉ ghi sự kiện, không ghi giá trị.
- Khoá khách + mã khôi phục 2FA KHÔNG hiển thị lại được — không phải ngoại lệ của quy tắc mà là
  không thể lấy lại được: khoá khách chỉ lưu băm SHA-256 (khoá thô chỉ trả một lần lúc tạo trong
  chính lời gọi đã xác thực lại, sau đó danh sách không lộ), mã khôi phục chỉ lưu băm SHA-256.
  Muốn có lại thì xoay khoá / tạo lại mã. Báo cáo nêu rõ để khỏi hiểu là «quy tắc chừa hai loại».
- Giao diện: mục VNC có nút «Hiện» (chỉ khi đã đặt) → hộp thoại riêng của trang (mật khẩu che ký
  tự khi chưa bật 2FA, mã 2FA khi đã bật) → mật khẩu hiện ở khoá riêng `vncHien`, nút «Ẩn» xoá
  ngay khỏi state. Ô nhập `vncMk` không bao giờ nhận giá trị từ máy chủ (test tĩnh khóa).
- Văn bản cũ sai sự thật ở mục VNC đã sửa: bỏ câu «Mật khẩu chỉ ghi đè, không xem lại được.»
  và câu «màn hình xem đang dùng mật khẩu do máy tự sinh» (sau bo-sung đã không còn mật khẩu
  ngẫu nhiên sinh trong container; chưa đặt thì màn hình xem báo chưa đặt).

## 3. Công tắc noVNC runtime trong web UI (c)

- Vị trí: trong mục mật khẩu VNC của «Bảo mật & người dùng», checkbox + dòng trạng thái
  («Đang bật — đang chạy» / «Đang tắt — không mở được»), chịu step-up như mọi thao tác tạo/xoá
  (K.goi tự hỏi bằng chứng khi gặp 403 step_up_required).
- Đường đi: lõi `POST /api/trinh-duyet/man-hinh/bat-tat` (quản trị, step-up, giới hạn tần suất,
  «bat» phải là bool thật — chuỗi "true"/số 1 bị 400) → module `may-dang-nhap` (`bat_tat_novnc`)
  → dịch vụ `PUT /v1/novnc/bat-tat` (khoá dịch vụ, nhóm `dang_nhap`).
- Dịch vụ (`src/novnc_bat_tat.py`, chỉ stdlib): ghi cờ bền `/khoa/novnc-bat` («bat»/«tat», ghi
  nguyên tử 0600 — cờ này không phải bí mật, chỉ nói «muốn xem hay không») rồi khởi động/dừng
  x11vnc + websockify: do supervisor quản (conf novnc) thì `supervisorctl start/stop`, nếu không
  thì spawn/kill trực tiếp (lệnh đúng như supervisord-novnc.conf: x11vnc `-passwdfile`, không
  `-nopw`; websockify `0.0.0.0:6080 → 127.0.0.1:5900`; PID file trong `/khoa`, khi tắt chỉ giết
  PID khớp lệnh qua `/proc/<pid>/cmdline` để khỏi giết nhầm PID tái sử dụng). Bật khi chưa đặt
  mật khẩu → 400 (không chạy xem không mật khẩu). Tắt không đổi/xoá mật khẩu. Cờ chỉ ghi khi
  chạy đủ cả hai chương trình; bật dở dang thì báo 502, cờ giữ nguyên.
- Bền qua khởi động lại: entrypoint ưu tiên cờ bền trước biến môi trường `CAPTCHA_SOLVER_BAT_NOVNC`
  (chưa có cờ thì dùng biến môi trường như cũ); lifespan của dịch vụ tự khởi động lại chương
  trình xem nếu cờ nói «bật» (trường hợp dịch vụ khởi động lại trong container đang chạy mà
  entrypoint không chạy lại); hỏng thì chỉ ghi log, không dừng dịch vụ.
- Trạng thái: `GET /api/trinh-duyet/man-hinh/trang-thai` (lõi) và `GET /v1/novnc/trang-thai` (dịch vụ)
  chỉ trả bool (cờ bật, đang chạy, đã đặt mật khẩu), không cần step-up vì không có bí mật.

## 4. Cách ly module (d)

- Endpoint công tắc/hiển thị/trạng thái nằm trên router `/api/trinh-duyet` (chỉ quản trị, kiểm tra
  phía server); endpoint hiển thị đòi thêm phiên web + bằng chứng tươi (mục 2).
- Công tắc/hiển thị KHÔNG có tham số module: lõi luôn đi qua đúng module `may-dang-nhap` cố định,
  module khác không có đường gọi tới (không thể bật/tắt noVNC, không đọc được bí mật tab Bảo mật
  qua lõi; khoá dịch vụ chỉ lõi/module đó có).
- Không tin client: «bat» phải là bool thật (400 nếu không); bằng chứng hiển thị chỉ xác minh phía
  server; mọi chuỗi hiển thị trong tab đi qua bộ dựng `support.js` vốn thoát HTML theo cấu trúc
  (chữ qua `thoat`, thuộc tính qua `thoatTT`) — test tĩnh khóa cả hai điểm chèn; trang Bảo mật
  không dùng innerHTML cho dữ liệu (chỉ có một chú thích nhắc không dùng innerHTML).
- Module không ảnh hưởng nối của module khác: công tắc chỉ dừng/khởi động x11vnc + websockify của
  chính dịch vụ may-dang-nhap, không động vào hồ sơ/phiên của module nào khác.

## 5. Kiểm tra rò rỉ theo chốt 19:26 (không đường hiển thị nào khác)

| Điểm kiểm | Kết quả |
|---|---|
| `GET /api/khoa-khach` (danh sách) | chỉ bản ghi đã lược (`_sach_khoa`: bỏ `bam`, `bam_cu`); test khẳng định không có `w2a_` và không có `bam` trong phản hồi |
| `GET /api/nguoi-dung`, `GET /api/toi` | `ban_ghi_sach` — không `bam_mat_khau`; `/api/toi` thêm cờ `bat_2fa` (bool, không phải bí mật) |
| `GET /api/trinh-duyet/mat-khau-vnc/trang-thai`, `GET /api/trinh-duyet/man-hinh/trang-thai` | chỉ bool |
| Giá trị điền sẵn | ô mật khẩu VNC chỉ nhận `''` ban đầu hoặc tay người gõ (test tĩnh khóa mọi phép gán `vncMk`); mật khẩu hiện lại nằm ở khoá riêng `vncHien`, chỉ gán trong handler hiển thị thành công và xoá bởi nút «Ẩn» |
| Log/phản hồi | đường đặt VNC, đường hiển thị, đường bật/tắt đều chỉ ghi sự kiện + bool, không ghi giá trị; test khẳng định phản hồi đặt không chứa mật khẩu và phản hồi hiển thị chứa mật khẩu đúng một trường `mat_khau` |
| Hiển thị mặc định | không có: mọi hiển thị đều sau xác thực lại; trạng thái «••••• đã đặt» chỉ là dấu hiệu, không phải bí mật |

## 6. Test

- Mới lõi `test/test_nv305_bao_mat.py`: 30/30 xanh (đỏ-trước-xanh: 23 đỏ / 7 xanh trên nền
  NV305+bo-sung, các đỏ đúng tại điểm tính năng thiếu — endpoint chưa có, mật khẩu vẫn được
  chấp nhận khi đã bật 2FA, đổi mật khẩu vẫn đòi mật khẩu cũ).
- Mới dịch vụ `dich-vu/may-dang-nhap/test_novnc_bat_tat.py`: 10/10 xanh (cờ bền, từ chối bật khi
  chưa đặt mật khẩu, lệnh spawn đúng và không `-nopw`, không spawn lại khi đang chạy, đường
  supervisorctl, giết đúng PID + xoá cờ, trạng thái chỉ bool, đọc mật khẩu đòi tệp đánh dấu).
- Dịch vụ NV305 cũ `test_nv305_mat_khau_vnc.py`: 21/21 xanh. Entrypoint (`test_c2a_dockerfile.py`):
  xanh kèm kiểm cờ bền mới (cờ thắng biến môi trường, xét cờ trước).
- Liên quan lõi (NV305, 2FA, step-up, người dùng, xem noVNC, khu tài khoản, NV45, NV182, NV197b,
  NV267, NV144, NV268-phần-không-cần-Chrome, NV297, va1): 283 passed, 15 skipped, 0 failed;
  7 error ở nv268 là thiếu `/usr/bin/google-chrome` trên máy này (giới hạn môi trường, không phải
  do patch — các test đó cần Chrome thật).
- Toàn suite lõi vs nền sạch (cùng tập, bỏ 8 file muse2api lỗi thu thập sẵn có): nền sạch
  161 failed / 5947 passed / 273 skipped / 31 xfailed / 17 errors; cây đã sửa 160 failed /
  5978 passed / 273 skipped / 31 xfailed / 17 errors. Chênh: +31 passed (30 test mới đều xanh
  + 1 test README cũ được sửa xanh nhờ bổ sung tài liệu 6 đường), −1 failed, 0 lỗi mới
  (đối chiếu theo tên: lỗi chỉ-có-ở-cây-đã-sửa = 0; lỗi chỉ-có-ở-nền = đúng test README).
  160 lỗi còn lại trùng tên 100% với nền sạch (mqtt, sao lưu, đa phương thức, responses/chuyển
  tiếp nhị phân, NV273/NV141, NV85/NV32, độc lập, đo tài nguyên, NV187/NV109, biến env,
  ảnh/video — đều là lỗi sẵn có, không liên quan tab Bảo mật). 17 errors cả hai bên là test
  nv268 cần `/usr/bin/google-chrome` (thiếu trên máy này).
- Lần chạy đối chiếu giữa chừng (trước khi sửa C6/README): cây đã sửa 162 failed / 5976 passed,
  lỗi chỉ-có-ở-cây-đã-sửa đúng 1 test C6 — đã sửa xong (đổi tên route/identifier, mục 8.6) và
  kiểm lại xanh trước khi chạy suite cuối.
- Tĩnh: `py_compile` các file Python sửa; script trang qua `node --check`; thẻ `sc-if` 101/101,
  `sc-for` 22/22 cân bằng; `sh -n` entrypoint.sh; quét bí mật: chỉ hằng test tự tạo, không khoá/
  mật khẩu/mã 2FA/IP/email thật nào trong patch/báo cáo/log.
- Test cũ cập nhật theo hành vi mới có chủ đích (ghi rõ, không nới kiểm để qua): (1) CSRF
  (`test_web2api_nguoi_dung.py::test_14_...`) thêm bước xác nhận lại trước ca «đúng CSRF → 200»
  vì tạo user thường nay cũng cần step-up; (2) `test_web2api_nv182_step_up_hanh_dong.py` theo tên
  hàm dialog mới + khẳng định nhánh mã 2FA.

## 7. Chưa thử thật (thuộc vòng sau gộp + lên server)

- Chrome thật (máy này không có Chrome): hộp thoại hỏi mã 2FA của khung.js, hộp thoại hiển thị
  của trang, checkbox công tắc noVNC (trạng thái bật/tắt, dòng trạng thái, thông báo khi bật mà
  chưa đặt mật khẩu), ảnh 375 px + 1280 px.
- Bật/tắt noVNC thật trên dịch vụ (máy này không có docker): spawn/stop x11vnc + websockify khi
  đang chạy conf base, supervisorctl start/stop khi đang chạy conf novnc, cờ bền qua khởi động
  lại container, lifespan tự khởi động lại khi dịch vụ khởi động lại trong container đang chạy.
- Luồng 2FA thật: mã TOTP từ ứng dụng thật + mã khôi phục thật qua hộp thoại mới (test chỉ dùng
  TOTP sinh nội bộ với đồng hồ giả).
- Hành vi container thật sau khởi động lại với cờ bền (entrypoint đọc cờ) — kết luận từ mã
  entrypoint + test tĩnh, chưa chạy container thật.
- Toàn suite lõi trên máy điều phối nếu cần (RAM máy này chật khi chạy song song — chỉ chạy tập
  liên quan + toàn suite một lần, xem mục 6).

## 8. Quyết định đã đổi so với brief / điểm cần chủ máy biết

1. **Tắt 2FA hộ KHÔNG gắn step-up** (đổi so với bản làm việc ban đầu): tắt 2FA hộ không nằm trong
   «tạo/xoá» theo nghĩa hẹp, và là đường khôi phục khi kho 2FA hỏng — gắn step-up sẽ khoá chết
   đường này đúng lúc cần nó nhất (xác nhận lại cũng đọc kho 2FA và sẽ 503 khi kho hỏng; test
   `test_kho_2fa_hong_khong_bo_qua_cong_2fa` khóa đúng hành vi này). Bảo vệ còn lại: chỉ admin +
   CSRF (phiên web) hoặc khoá quản trị. Nếu chủ máy vẫn muốn step-up cho nút này thì nói một câu,
   sẽ gắn thêm (kèm ngoại lệ fail-open cho kho hỏng).
2. **Bearer quản trị miễn step-up cho thao tác nhưng KHÔNG miễn cho hiển thị**: thao tác (tạo/xoá/
   bật/tắt) giữ miễn trừ Bearer như mọi đường chạm bí mật khác (khoá quản trị là bí mật gốc);
   hiển thị thì không có miễn trừ nào (chốt 19:26). Hai mức này khác nhau có chủ đích, test khóa cả hai.
3. **Khoá khách + mã khôi phục không hiển thị lại được** (mục 2): do chỉ lưu băm, không phải do
   quy tắc chừa ra — muốn có lại thì xoay/tạo lại.
4. **Sửa văn bản mục VNC sai sự thật** (mục 2): câu mật khẩu ngẫu nhiên đã lỗi thời từ bo-sung.
5. **Test cũ cập nhật** (mục 6): chỉ hai chỗ, đều do hành vi mới có chủ đích, không nới kiểm.
6. **Tên route lõi dùng `man-hinh`, không dùng `novnc`**: quy ước tĩnh C6 cấm chữ «novnc» ngoài
   5 file cho phép (kể cả trong trang web và chuỗi URL) — NV305 đã từng sửa theo hướng này nên
   lượt này làm theo: route lõi là `/api/trinh-duyet/man-hinh/bat-tat` và
   `/api/trinh-duyet/man-hinh/trang-thai`, identifier trang là `manHinh*`. Route dịch vụ giữ
   `/v1/novnc/*` như NV305 (nằm ngoài phạm vi grep của C6: chỉ `app` và `web`).
