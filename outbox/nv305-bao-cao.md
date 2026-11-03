# NV305 — BÁO CÁO (bản làm việc, chưa chốt số liệu test liên quan)

## KẾT QUẢ

- Nộp: nhánh Giao `muse/nv305` (chốt sau khi test liên quan xong) gồm `outbox/nv305.patch` (764 dòng,
  9 file, +631/−12, áp sạch lên nền sạch web2api `8ed35ab`) + `outbox/nv305-bao-cao.md`.
- Nền: web2api main `8ed35ab` (kiểm lúc làm); Giao main `82d9ff46` (không đổi lúc làm).
- Phạm vi: đúng đặc tả NV305, tối thiểu — 1 ô mật khẩu trong «Bảo mật & người dùng», 1 đường PUT lõi,
  1 cặp đường dịch vụ, 2 phương thức module, 1 thay đổi entrypoint (ghi rõ dưới), tài liệu README §3.2.
- Không đẩy main, không force-push, không bí mật/mật khẩu/IP/email thật trong patch/báo cáo/log.
  Mọi mật khẩu trong test đều tự tạo cho test (dạng `Nv305-T1`), KHÔNG dùng và KHÔNG chép lại bất kỳ
  mã/mật khẩu nào người dùng từng gửi trong chat — NV305 là để chủ máy TỰ ĐẶT mật khẩu mới trong giao diện.

## 1. CHỌN ĐÚNG VỊ TRÍ — ô mật khẩu đặt ở đâu, và vì sao đúng

**Vị trí: trang «Bảo mật & người dùng» (`web/He-thong-Bao-mat.dc.html`), tab «Bảo mật», chỉ quản trị
(admin), mục mới «Mật khẩu xem trình duyệt đăng nhập» (id `mat-khau-xem-trinh-duyet`), đặt ngay sau mục
«Xác thực hai bước (2FA)», trước mục «Khoá đăng nhập».**

Lý do đúng theo CẢ HAI nguồn:

1. **Đặc tả NV305 nói thẳng vị trí này** («trong «Bảo mật & người dùng» có một ô nhỏ», «một ô trong
   `web/He-thong-Bao-mat.dc.html` (theo quy tắc: tạo/đổi khoá do w2a quản ở đây)»).
2. **Quy tắc QUY-TAC-GIAO-DIEN-W2A.md không vênh với đặc tả ở đây:**
   - Quy tắc 1 (kết nối RA ngoài nằm trong chip «Cài đặt» của chính module) KHÔNG áp dụng: đây không phải
     kết nối ra ngoài tới dịch vụ khác — `may-dang-nhap` là dịch vụ của chính web2api, và mật khẩu này là
     bí mật do web2api quản để mở màn hình xem của chính nó.
   - Quy tắc 2 («Bảo mật & người dùng» dành cho khoá do web2api cấp cho thứ gọi VÀO) là họ gần nhất:
     mật khẩu VNC là bí mật do web2api quản để vào màn hình xem của chính nó — khác khoá tự sinh ở chỗ
     nó do chủ máy tự đặt (chủ máy yêu cầu rõ «cho phép tôi tự đặt»), nhưng cùng vị trí quản lý.
   - Quy tắc 5 (mọi ô có mô tả tiếng thường): mục mới có đoạn mô tả đầy đủ — mật khẩu này để làm gì
     (mở màn hình xem, không phải mật khẩu tài khoản AI), giới hạn 8 ký tự và lý do (VNC chỉ dùng 8 ký tự
     đầu), ghi đè không xem lại được.
3. **Không có điểm vênh đặc tả-vs-quy tắc nào cần chủ máy quyết ở vị trí này.** Nếu sau này chủ máy muốn
   dời sang chip «Cài đặt» của module may-dang-nhap thì đó là quyết mới, không phải sửa lỗi vị trí.

## 2. PHÂN TÍCH chatgpt2api (luật đứng 16:11) — file/hàm đã đọc, kết luận đối chiếu

Repo `TriTue2011/chatgpt2api@d879b03`, chỉ clone đọc, không sửa:

- `deploy/supervisord.conf:71-74` — c2a khóa noVNC/x11vnc BẰNG BIẾN MÔI TRƯỜNG `VNC_PASSWORD` trên
  container (`x11vnc -passwd "$VNC_PASSWORD"`); không đặt biến thì chạy `-nopw` (KHÔNG mật khẩu).
- `api/app.py:76-81` — c2a chỉ CẢNH BÁO lúc khởi động khi `VNC_PASSWORD` trống («noVNC :6080 có thể
  không mật khẩu. Đặt VNC_PASSWORD trong docker-compose»), không có đường nào đặt lại lúc chạy.
- `HUONG_DAN.md:202`, `README.md:68` — tài liệu c2a ghi `VNC_PASSWORD` là «mật khẩu noVNC (cổng 6080)»
  đặt trong docker-compose; không có UI/API đặt mật khẩu.
- `api/novnc_proxy.py` + `services/novnc_ve.py` — c2a bảo vệ noVNC ở TẦNG PROXY (cookie phiên
  `c2a_novnc`, path=/novnc, vé/phiên riêng), khác web2api (vé một lần 60 giây + sandbox `/novnc/s/…`).
- `captcha-solver/src/auto_login.py`, `browser_pool.py`, `chatgpt_login.py`, `claude_web_login.py` —
  nhắc noVNC chỉ như nơi NGƯỜI GÕ tay (captcha, xác minh), không có code đặt mật khẩu VNC.

**Kết luận: c2a KHÔNG có tương đương «chủ máy tự đặt mật khẩu xem trong giao diện» — mật khẩu VNC của
c2a chỉ đặt bằng biến môi trường lúc dựng container, thậm chí mặc định không mật khẩu.** NV305 vì vậy là
điểm web2api HƠN c2a (giữ bắt buộc mật khẩu như hiện tại, nhưng cho chủ máy tự đặt lúc chạy thay vì
docker exec đọc mật khẩu máy sinh), không phải port mù theo c2a. Khác c2a ở đây là khác có chủ đích,
đã test chứng minh (mục 4), đúng luật 16:58 (khác chưa chắc là sai).

## 3. HÀNH VI MẬT KHẨU (đã làm)

- **Độ dài/hiệu lực:** 1–8 ký tự, ASCII in được (`[!-~]`), không khoảng trắng, không dấu, không ký tự
  điều khiển. Dài hơn 8, rỗng, có dấu/cách → 400 (lõi và dịch vụ cùng kiểm; lõi kiểm trước để báo nhanh,
  dịch vụ là nơi quyết cuối). Không cắt ngầm thành 8: người gõ phải biết chính xác mật khẩu hiệu lực.
- **Ghi-đè-không-đọc-lại:** giao diện chỉ biết bool «đã đặt hay chưa» qua
  `GET /api/trinh-duyet/mat-khau-vnc/trang-thai` (xem điểm bổ sung dưới); sau khi đặt thành công ô
  trống lại và hiện «••••• đã đặt» + nút «Đổi». Không đường nào trả mật khẩu qua API, log, nhật ký.
- **Step-up khi ghi:** `PUT /api/trinh-duyet/mat-khau-vnc` gọi `kiem_tra_step_up` trước mọi việc khác
  (phiên web phải xác nhận lại; Bearer quản trị được miễn như mọi đường chạm bí mật). Giao diện dùng
  `K.goi` nên 403 `step_up_required` tự mở hộp hỏi mật khẩu xác nhận lại rồi thử lại một lần.
- **Giới hạn tần suất:** tối đa 10 lần đặt / 60 giây cho mỗi người gọi (tính sau khi qua step-up); vượt → 429.
  Chống bấm liên tục làm x11vnc khởi động lại liên tục.
- **Đường đi:** giao diện → lõi PUT → module `may-dang-nhap.dat_mat_khau_vnc` (khoá dịch vụ đã cấu hình,
  qua `dich_vu_url`) → dịch vụ `PUT /v1/novnc/mat-khau` (khoá dịch vụ, nhóm `dang_nhap` mặc định bật).
  Mật khẩu chỉ đi trong RAM của lời gọi; lõi không lưu.
- **Dịch vụ ghi gì:** `src/mat_khau_vnc.py::ghi_mat_khau_vnc` ghi nguyên tử (tệp tạm + `os.replace`)
  `/khoa/mat-khau-vnc` (0600) + tệp đánh dấu rỗng `/khoa/mat-khau-vnc-chu-dat` (0600), rồi
  `supervisorctl -c /etc/supervisor/supervisord-novnc.conf restart x11vnc`. Trả `{"ok": true,
  "da_nap_lai": bool}`. Nạp lại hỏng (noVNC đang tắt, thiếu supervisorctl) → vẫn 200 với
  `da_nap_lai: false` + câu báo rõ trong giao diện («mật khẩu sẽ có hiệu lực khi bật lại noVNC»),
  vì mật khẩu ĐÃ ghi và sẽ có hiệu lực khi x11vnc khởi động lại — không báo hỏng oan thành 502.
- **Chưa đặt thì sao:** vẫn dùng mật khẩu ngẫu nhiên cũ của dịch vụ (đúng đặc tả); giao diện báo rõ
  «Chưa đặt qua giao diện này — màn hình xem đang dùng mật khẩu do máy tự sinh».
- **Thay đổi entrypoint (có chủ đích, ghi rõ):** trước đây biến `CAPTCHA_SOLVER_MAT_KHAU_VNC` (nếu đặt)
  ghi đè tệp MỖI LẦN khởi động → mật khẩu đặt qua giao diện sẽ bị mất khi restart container. Nay
  entrypoint chỉ ghi khi CHƯA CÓ tệp: tệp đã có thì giữ nguyên; biến môi trường chỉ còn là mật khẩu
  ban đầu. Muốn đổi thì đặt qua giao diện. Đã ghi vào README §3.2.
- **Bổ sung nhỏ ngoài «MỘT đường PUT» của đặc tả:** thêm `GET …/trang-thai` (lõi) và
  `GET /v1/novnc/mat-khau/trang-thai` (dịch vụ) — chỉ trả bool, không bí mật — vì không có nó thì
  giao diện không thể hiện trung thực «••••• đã đặt» sau khi tải lại trang. Đây là phần bắt buộc để
  đúng yêu cầu hiển thị của chính đặc tả, không phải phình phạm vi.

## 4. TEST (đỏ-trước-xanh)

- Test mới lõi `test/test_nv305_mat_khau_vnc.py`: 17 test — 401 không khoá, 404 chưa cài module,
  400 cho 7 dạng sai (rỗng, 9 ký tự, khoảng trắng, dấu, xuống dòng, không phải chuỗi, thiếu trường) và
  không gọi module, 200 + không lộ mật khẩu trong thân phản hồi, 1 ký tự cũng được, lỗi dịch vụ → 502,
  phiên web chưa step-up → 403 `step_up_required` và module không được gọi, lần đặt thứ 11 trong 60 giây
  → 429, GET trạng thái chỉ trả bool, 401/404 cho trạng thái, kiểm tĩnh giao diện (id mục, chỉ quản trị,
  ghi chú 8 ký tự, đường PUT, «••••• đã đặt»).
- Test mới dịch vụ `dich-vu/may-dang-nhap/test_nv305_mat_khau_vnc.py`: 20 test — kiểm định dạng,
  ghi tệp 0600 + tệp đánh dấu, ghi đè nội dung cũ, nạp lại hỏng vẫn ghi tệp nhưng `da_nap_lai: false`
  (cả mã thoát ≠ 0 và supervisorctl vắng mặt), chưa đặt → false, sai định dạng không ghi tệp, log không
  chứa mật khẩu, kiểm tĩnh main.py có đủ hai đường gắn nhóm `dang_nhap`.
- Đỏ-trước-xanh đã chạy: trước khi viết mã, test lõi 16 lỗi + 1 hỏng (thiếu `_GIOI_HAN_MK_VNC`, thiếu
  đường), test dịch vụ lỗi thu thập (thiếu `src.mat_khau_vnc`); sau khi viết mã: lõi 17/17, dịch vụ 20/20.
- Kiểm tĩnh khác: `py_compile` đủ file đổi; thẻ `sc-if` 96/96 và `sc-for` 22/22 cân bằng; script
  `text/x-dc` của trang qua `node --check`.
- Tập liên quan: `test_nv276_xem_novnc`, `test_web2api_c6`, `test_nv145b_may_dang_nhap`,
  `test_nv51_step_up`, `test_nv182_step_up`, `test_va1_stepup` — lần chạy đầu trên cây có vá: 119 passed,
  2 skipped, 1 failed duy nhất là `test_web2api_c6.py::test_grep_tu_khoa_trong_app_va_web` (quy ước C6:
  chữ `novnc` trong `app`/`web` chỉ được ở 5 file cho phép — câu mô tả trong mục mới dùng chữ «noVNC» nên
  phạm quy). Đã sửa: toàn bộ câu chữ trong trang Bao-mat dùng «màn hình xem» thay cho «noVNC» (chữ
  `novnc` trong trang về 0); chạy lại test grep C6 + toàn bộ test NV305 lõi: 18/18 xanh. Đối chiếu nền
  sạch (stash toàn bộ thay đổi): 120 passed, 2 skipped, 0 failed — đúng bằng tập liên quan sau khi sửa,
  không lệch nào khác do NV305. 5 file liên quan còn lại không đọc trang Bao-mat nên sửa chữ không ảnh
  hưởng chúng.
- Bandit không chạy được ở đây (venv lõi không có bandit) — điều phối chạy ở vòng soát/gộp. Mã mới không
  dùng shell với dữ liệu người dùng (ghi tệp bằng Python, `supervisorctl` với argv cố định, không nội suy
  mật khẩu vào lệnh/log).
- CHƯA test được ở đây (ghi trung thực): endpoint thật của dịch vụ qua TestClient (máy này thiếu
  `patchright` nên không import được `src.main` trong venv lõi; test dịch vụ dừng ở mức hàm thuần +
  kiểm tĩnh đấu nối); toàn suite (RAM máy lúc làm chỉ còn ~300 MB khả dụng vì 3 agent khác đang chạy
  song song — điều phối chạy toàn suite ở vòng soát/gộp); Chrome thật (máy này không có Chrome);
  server thật / MCP → noVNC thật (xem mục 5).

## 5. KẾ HOẠCH KIỂM THẬT SAU KHI GỘP + LÊN SERVER (không tự nhận đã kiểm)

Thuộc vòng lặp với điều phối/chủ máy sau khi dựng lại, theo đúng trình tự đã chốt:

1. **Qua MCP trước:** chạy lượt đăng nhập tự động (Grok rồi Claude như NV293 khi đủ điều kiện) qua MCP
   như bình thường — NV305 không đổi luồng đăng nhập, chỉ đổi cách vào màn hình xem.
2. **Theo dõi + thao tác tay qua noVNC sau:** chủ máy mở xem qua vé noVNC của lõi, nhập mật khẩu
   VỪA ĐẶT QUA GIAO DIỆN NV305 ở hộp nhập của noVNC (không còn đọc bằng docker exec), rồi THEO DÕI và
   THAO TÁC TAY qua noVNC để CHỌN ĐÚNG Ô cho việc đăng nhập (ô email, nút Tiếp tục, ô mật khẩu, nút
   «Sign in with Google», …) — theo tinh chỉnh 17:38 ngày 03/11, noVNC không chỉ để xem thụ động mà để
   chủ máy tự tay chọn đúng ô, rồi từ đó mới xác định đích tự động hóa. Các ô nào còn cần xác nhận tay
   thì ghi lại, không đoán từ code.
3. Kiểm thêm: đặt mật khẩu mới khi đang có người xem → người xem phải nhập lại mật khẩu mới; tắt noVNC
   rồi đặt → báo «chưa nạp lại được», bật lại noVNC → mật khẩu mới có hiệu lực; khởi động lại container
   → mật khẩu đặt qua giao diện còn nguyên (không bị biến môi trường ghi đè).

## 6. HỒ SƠ FILE (patch)

- `app/novnc.py` — 2 endpoint + giới hạn tần suất + chú thích vị trí.
- `modules/may-dang-nhap/module.py` — `dat_mat_khau_vnc`, `trang_thai_mat_khau_vnc`.
- `dich-vu/may-dang-nhap/src/mat_khau_vnc.py` (mới) — kiểm định dạng, ghi nguyên tử 0600, nạp lại x11vnc.
- `dich-vu/may-dang-nhap/src/main.py` — `PUT /v1/novnc/mat-khau`, `GET /v1/novnc/mat-khau/trang-thai`.
- `dich-vu/may-dang-nhap/entrypoint.sh` — chỉ ghi mật khẩu lần đầu, giữ tệp đã có.
- `dich-vu/may-dang-nhap/README.md` — §3.2: đường mới + hành vi entrypoint.
- `web/He-thong-Bao-mat.dc.html` — mục mới + state + phương thức + ánh xạ view.
- `test/test_nv305_mat_khau_vnc.py` (mới), `dich-vu/may-dang-nhap/test_nv305_mat_khau_vnc.py` (mới).
