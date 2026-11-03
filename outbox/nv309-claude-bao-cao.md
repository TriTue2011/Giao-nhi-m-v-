KẾT QUẢ — NV309-claude: CHỨNG MINH SESSION CHO CLAUDE-WEB Ở MỨC TEST, 14/14 TEST MỚI XANH.

- Nộp: nhánh `muse/nv309-claude` (Giao, kiểm ls-remote sau khi đẩy) + `outbox/nv309-claude.patch` (2 file, 394 thêm/2 bớt) + báo cáo này.
- Nền: web2api main `8ed35ab` (kiểm ls-remote — trùng nền gốc của hai patch NV309, main không đổi). Thứ tự gộp bắt buộc: **(a) → (c) → claude**.
- Ghép (a)+(c): patch NV309-a (`muse/nv309-a` = `7b0399e5`) rồi NV309-c (`muse/nv309-c` = `8b020ce`) áp sạch theo thứ tự lên cây mới (`git apply --check` cả hai đều OK) — **không xung đột, không phải ép, không sửa patch của người khác**. Delta này đã kiểm lại trên cây mới clone: (a) → (c) → patch claude áp sạch, chạy 31 test xanh (14 claude + 11 (a) + 6 (c)).
- Không làm ChatGPT/Gemini trong lượt này, không làm NV309-d (chờ Q2), không đổi giao diện trang tài khoản AI (patch không chạm `web/`), không tài khoản thật, không đăng nhập thật — toàn bộ bằng controller GIẢ (`TrinhDuyetGia`/`TrinhDuyetChuyenDoi`) + máy chủ HTTP GIẢ + tài khoản GIẢ.

## Bằng chứng theo TỪNG TRƯỜNG HỢP (cách đăng nhập × kết quả)

| Trường hợp | Kết quả chứng minh | Test |
|---|---|---|
| Email-direct → session | `dang_nhap` loại `mat_khau` (không kèm cách) qua controller lõi cấp: mở `claude.ai/login` → điền email + mật khẩu → bấm đăng nhập → đọc `sessionKey` → kiểm phiên → trả cookie `sessionKey=…`; module dùng đúng controller được truyền | `test_email_direct_qua_controller_loi_cap_tra_session` |
| Email-direct, không controller → fail-closed | Module mới, không factory nào: trả `can_nguoi` mà chưa từng mở trình duyệt (đối tác của SAI S1 — đường này chỉ chạy được khi lõi cấp controller) | `test_email_direct_khong_co_controller_thi_can_nguoi` |
| Email-direct, CAPTCHA trước khi điền → can_nguoi | Dừng trước khi điền, không gọi `vuot_thu_thach` | `test_email_captcha_truoc_khi_dien_thi_can_nguoi_dung_truoc_khi_dien` |
| Email-direct, Cloudflare trước khi điền → can_nguoi | Như CAPTCHA — **điểm này phải SỬA mới xanh** (xem «Một sửa nhỏ» dưới) | `test_email_direct_challenge_cloudflare_thi_can_nguoi` |
| Google tái dùng hồ sơ, đi tắt → session | Hồ sơ đã có phiên: mở `claude.ai` thấy `da_dang_nhap` → đọc `sessionKey` → trả session, không bấm Google | `test_google_di_tat_tra_session` |
| Google tái dùng hồ sơ, bấm SSO → session | Hồ sơ chưa có phiên: bấm «Continue with Google» → chờ phiên hình thành → đọc `sessionKey` → trả session | `test_google_bam_continue_tra_session` |
| Google, đang giữ captcha → lượt khác bị chặn | Mã `cho_captcha_toan_cuc`, KHÔNG chạm tới trình duyệt | `test_google_dang_giu_thi_luot_khac_bi_chan_khong_cham_trinh_duyet` |
| Google, chủ hold chạy lại → gỡ hold | Đi tắt thành công → giữ captcha toàn cục được gỡ | `test_google_chu_hold_chay_lai_thanh_cong_thi_go_hold` |
| Google, CAPTCHA → can_nguoi + đặt hold | Dừng ngay, không bấm, đặt giữ captcha toàn cục cho đúng chủ hold | `test_google_captcha_thi_can_nguoi_va_dat_hold` |
| Không solver captcha | Tĩnh: module không gọi `.vuot_thu_thach(`, không gọi `vuot_thu_thach_toi_da(`, không chuỗi `2captcha`; gate `giai_captcha` giữ TẮT (module không có đường solver nào) | `test_khong_co_vuot_thu_thach_va_khong_solver_trong_module` |
| Vòng đời: module không tự đóng controller | Dù thành công hay `can_nguoi`, module không gọi `dong()` — đóng là việc của người gọi (lõi) | `test_module_khong_tu_dong_controller` |
| Vòng đời: tái dùng / tạo mới / chỉ đóng mới tạo | Hồ sơ sẵn → tái dùng (`da_tao=False`); không hồ sơ → tạo workspace mới (`da_tao=True`); `dong_workspace_moi` chỉ đóng workspace mới tạo với `(hs, False)`; hồ sơ sẵn không bao giờ bị đóng | `test_vong_doi_khoi_phuc_phien_tai_dung_khong_tao_moi` |
| NV271: T2 email + mã một lần → thành công | `khoi_phuc_tu_dong` (khoi_phuc=True): sau mật khẩu hiện 2FA → điền `ma_xac_minh` + bấm `xac_nhan_2fa` → đọc session → tang `T2` | `test_khoi_phuc_t2_email_otp_tra_thanh_cong` |
| T2 Google qua controller lõi cấp → thành công | `khoi_phuc_tu_dong` với `cach_dang_nhap="google"` + `chu_giu=email` (NV309-c): đi tắt thành công, tang `T2`, dùng đúng controller được truyền | `test_khoi_phuc_t2_google_qua_controller_loi_cap` |

Ghi chú về khuôn id hồ sơ (phát hiện trong lúc viết test, không phải lỗi production): id hồ sơ lõi phải đúng khuôn hex 16–64 ký tự (`MAU_HO_SO_TRINH_DUYET`); chuỗi `claude-web-<hash>` của `ho_so_trinh_duyet` là id xem noVNC, thuộc không gian tên khác, không dùng làm id hồ sơ lõi. Test vòng đời dùng id hồ sơ dạng hex cho đúng khuôn.

## Một sửa nhỏ (duy nhất ngoài test)

File `modules/claude-web/module.py`, hàm `_dang_nhap_bang_trinh_duyet`, nhánh `khoi_phuc=False`: điều kiện dừng trước khi điền mở rộng từ 3 tín hiệu (`captcha`, `2fa`, `xac_minh`) thành 6 tín hiệu (`captcha`, `2fa`, `xac_minh`, `cloudflare`, `thu_thach_truy_cap`).

Lý do: chú thích trong code vốn đã nói «can_nguoi cho mọi thử thách trước khi điền», nhưng code chỉ kiểm 3 tín hiệu nên Cloudflare/thử thách truy cập lọt qua bước điền rồi mới hỏng ở `khong_lay_duoc_phien` — không phải vượt (không lấy được phiên), nhưng không phải `can_nguoi` đúng nghĩa. Sau sửa, mọi thử thách trước khi điền đều `can_nguoi`, nhất quán với nhánh `khoi_phuc=True` và với đường Google (`_TIN_HIEU_CAN_NGUOI` đủ 6 tín hiệu).

Đỏ-trước-xanh: test Cloudflare FAIL trên cây chỉ-(a)+(c) (đã kiểm bằng cách stash sửa rồi chạy riêng), PASS sau khi sửa; toàn file 14/14 xanh sau sửa.

## Số test

- Mới: `test/test_nv309_claude.py` — **14/14 xanh** (venv NV289, pytest 9.1.1).
- Tập liên quan (có delta): **160 passed, 0 failed** — gồm (a) 11, (c) 6, claude 14, NV89/NV93/NV-module-tu-dong claude, NV271-dnt claude + can_nguoi, NV300 cach_dang_nhap, NV80 danh_tinh, NV102 grok-claude.
- Đối chiếu nền (a)+(c) không có delta: **146 passed** — chênh đúng +14 test mới, **0 hồi quy**.
- Toàn suite lõi: chưa chạy lại riêng cho delta này (thay đổi chỉ là 1 điều kiện trong 1 module + 1 file test mới; tập liên quan đã bao hết đường claude) — điều phối chạy toàn suite ở vòng soát/gộp nếu cần.
- Gap Google trong test = 0 nhờ `test/conftest.py` đặt `WEB2API_GOOGLE_GIAN_CACH_GIAY=0`; production mặc định **25 giây không đổi** (`GIAN_CACH_GIAY = 25.0`, không chạm).

## Chưa kiểm thật — cần làm sau gộp (MCP trước → noVNC thao tác tay)

Test controller giả chỉ chứng minh đường ống + quyết định của module, không chứng minh selector thật đúng. Các ô đều **chưa được xác nhận bằng tay** trong lượt này:

- Nút «Continue with Google» (`button[data-testid="login-with-google"]` — code ghi đã đo trên trang thật 18/10/2026, nhưng chưa có chủ máy chọn bằng tay qua noVNC ở vòng này).
- Ô email, ô mật khẩu ở `claude.ai/login` — lưu ý: module tự ghi rõ claude.ai **không có ô mật khẩu của Anthropic**; đường điền email + mật khẩu là khuôn dành cho tài khoản Google ĐÃ LIÊN KẾT (đi qua SSO) và «chi tiết SSO Google thật CHƯA KIỂM».
- Các bước popup OAuth / chọn tài khoản Google / đồng ý trong SSO thật: bộ điều khiển trừu tượng (`mo_trang`/`tin_hieu`/`dien`/`bam`/`doc_cookie`) KHÔNG có bước popup/chọn tài khoản đó — luồng SSO thật có thể cần thêm bước mà chỉ kiểm thật mới thấy.
- Ô mã 2FA (`ma_xac_minh` + `xac_nhan_2fa`) và ô «Xác minh bạn là con người» (Cloudflare) trên claude.ai.
- Trình tự kiểm thật theo luật đứng: đầu tiên qua MCP (đường Google tái dùng hồ sơ bằng tài khoản Google đã cho phép — theo kế hoạch trio Claude → Grok → Gemini của chủ máy, cần tài khoản Claude trong kho ở chế độ «dùng hồ sơ Google đã đăng nhập» + id vào danh sách cho phép MCP + dựng lại trước), rồi chủ máy thao tác tay qua noVNC chọn đúng ô (không chỉ xem thụ động).

## Quét

Không bí mật/khoá/cookie/mật khẩu/email thật/IP thật trong patch/báo cáo/log: tài khoản test dùng miền `example.com` + chuỗi giả rõ ràng (`mat-khau-gia`, `phien-gia-…`, TOTP secret base32 toàn ký tự A); không chạm `web/` (giao diện tài khoản AI giữ nguyên); không chạm ChatGPT/Gemini; không làm NV309-d.
