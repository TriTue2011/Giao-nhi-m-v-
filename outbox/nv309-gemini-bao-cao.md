KẾT QUẢ — NV309-gemini: CHỨNG MINH SESSION CHO GEMINI-WEB Ở MỨC TEST, 23/23 TEST MỚI XANH.

- Nộp: nhánh `muse/nv309-gemini` (Giao, kiểm ls-remote sau khi đẩy) + `outbox/nv309-gemini.patch` (2 file, 530 thêm/2 bớt) + báo cáo này.
- Nền: web2api main `8ed35ab` (kiểm ls-remote — main không đổi). Thứ tự gộp bắt buộc: **(a) → (c) → gemini**.
- Ghép (a)+(c): patch NV309-a (`muse/nv309-a` = `7b0399e5`) rồi NV309-c (`muse/nv309-c` = `8b020ce`) áp sạch theo thứ tự lên cây mới (`git apply --check` cả hai đều OK) — **không xung đột, không phải ép, không sửa patch của người khác**. Delta claude (`muse/nv309-claude`) là nhánh riêng cho module claude-web, **không áp chung** — delta này chỉ chạm module gemini-web + test mới. Đã kiểm lại trên cây mới clone: (a) → (c) → patch gemini áp sạch, chạy 40 test xanh (23 gemini + 11 (a) + 6 (c)).
- Không làm ChatGPT trong lượt này, không làm NV309-d (chờ Q2), không đổi giao diện trang tài khoản AI (patch không chạm `web/`), không tài khoản thật, không đăng nhập thật — toàn bộ bằng controller GIẢ (`TrinhDuyetGia`/`TrinhDuyetChuyenDoi`) + máy chủ HTTP GIẢ (client `_tao_client` chích giả) + tài khoản GIẢ.

## Bằng chứng theo TỪNG TRƯỜNG HỢP (cách đăng nhập × kết quả)

| Trường hợp | Kết quả chứng minh | Test |
|---|---|---|
| Google tái dùng hồ sơ, đi tắt → session | Hồ sơ đã có phiên Google (cookie `__Secure-1PSID` → quy tắc cho `da_dang_nhap`): mở `gemini.google.com/` thấy đã đăng nhập → đọc cookie → kiểm phiên + khám phá model → trả cookie phiên, không bấm, không điền | `test_google_di_tat_tra_session` |
| mat_khau mang cach_dang_nhap='google' → đường tái dùng | NV300: lần gọi `mat_khau` mang cách tường minh `google` thì đổi sang đường tái dùng hồ sơ, không điền mật khẩu | `test_mat_khau_cach_google_thanh_duong_tai_dung` |
| T2 Google qua controller lõi cấp → thành công | `khoi_phuc_tu_dong` với `cach_dang_nhap="google"` + `ho_so_google` + `chu_giu=email` (NV309-c): đi tắt thành công, tang `T2`, dùng đúng controller được truyền | `test_khoi_phuc_t2_google_qua_controller_loi_cap` |
| Google SSO bấm lại → session | Hồ sơ chưa có phiên: bấm «Đăng nhập» (`_BO_CHON_DANG_NHAP`) → chọn tài khoản Google (`_BO_CHON_GOOGLE`) → chờ phiên hình thành → đọc cookie → trả session; không điền gì (đường tái dùng KHÔNG BAO GIỜ `dien()` theo hợp đồng NV92-P3) | `test_google_bam_sso_tra_session` |
| Tái dùng, CAPTCHA → can_nguoi + đặt hold | Dừng ngay, không bấm, đặt giữ captcha toàn cục cho đúng chủ hold | `test_tai_dung_captcha_thi_can_nguoi_va_dat_hold` |
| Tái dùng, Cloudflare → can_nguoi + đặt hold | Cloudflare thuộc `TIN_HIEU_CAPTCHA` của khóa lõi (không chỉ riêng `'captcha'`) nên cũng đặt hold | `test_tai_dung_cloudflare_thi_can_nguoi_va_dat_hold` |
| Tái dùng, 2FA → can_nguoi, KHÔNG đặt hold | 2FA không thuộc `TIN_HIEU_CAPTCHA` — hold chỉ dành cho thử thách chống bot, không phải xác minh người dùng | `test_tai_dung_2fa_thi_can_nguoi_khong_dat_hold` |
| Email, Cloudflare trước khi điền → thu_thach | Dừng trước khi điền, không gọi `vuot_thu_thach`, trả `thu_thach_truoc_khi_dien` | `test_email_cloudflare_truoc_khi_dien_thi_thu_thach_dung_truoc_khi_dien` |
| Email, thử thách truy cập trước khi điền → thu_thach | Như trên cho tín hiệu `thu_thach_truy_cap` — **điểm này phải SỬA mới xanh** (xem «Một sửa nhỏ» dưới) | `test_email_thu_thach_truy_cap_truoc_khi_dien_thi_thu_thach` |
| Email, xác minh thiết bị trước khi điền → thu_thach | Như trên cho tín hiệu `xac_minh_thiet_bi` — **điểm này phải SỬA mới xanh** | `test_email_xac_minh_thiet_bi_truoc_khi_dien_thi_thu_thach` |
| Email, thử thách sau mật khẩu → thu_thach | Kiểm sau mật khẩu gặp `thu_thach_truy_cap` thì trả `thu_thach_truoc_khi_dien`, không trôi tới `khong_lay_duoc_phien` — **điểm này phải SỬA mới xanh** | `test_email_thu_thach_sau_mat_khau_thi_thu_thach` |
| Khôi phục: thu_thach → can_nguoi + hoãn | `khoi_phuc_tu_dong` map `thu_thach_truoc_khi_dien` → `can_nguoi=True` + đặt hoãn captcha riêng của module; thử lại ngay → `captcha_hoan`, chưa chạm trình duyệt | `test_khoi_phuc_thu_thach_thanh_can_nguoi_va_hoan` |
| Không solver captcha | Tĩnh: module không gọi `.vuot_thu_thach(`, không gọi `vuot_thu_thach_toi_da(`, không chuỗi `2captcha`, không gate `giai_captcha` (gate giữ TẮT — gặp thử thách chỉ có đường `can_nguoi`/`thu_thach_truoc_khi_dien`) | `test_khong_co_vuot_thu_thach_va_khong_solver_trong_module` |
| Google, đang giữ captcha → lượt khác bị chặn | Mã `cho_captcha_toan_cuc`, KHÔNG chạm tới trình duyệt | `test_google_dang_giu_thi_luot_khac_bi_chan_khong_cham_trinh_duyet` |
| Google, chủ hold chạy lại → gỡ hold | Đi tắt thành công → giữ captcha toàn cục được gỡ | `test_google_chu_hold_chay_lai_thanh_cong_thi_go_hold` |
| Google, hai lượt tuần tự đều xong | Khóa serial nhả đúng sau mỗi lượt (không kẹt khóa) | `test_google_hai_luot_tuan_tu_deu_xong` |
| Vòng đời: module không tự đóng controller | Dù thành công hay `can_nguoi`, module không gọi `dong()` — đóng là việc của người gọi (lõi) | `test_module_khong_tu_dong_controller` |
| Vòng đời: tái dùng / tạo mới / chỉ đóng mới tạo | Hồ sơ sẵn → tái dùng (`da_tao=False`); không hồ sơ → tạo workspace mới (`da_tao=True`); `dong_workspace_moi` chỉ đóng workspace mới tạo với `(hs, False)`; hồ sơ sẵn không bao giờ bị đóng | `test_vong_doi_khoi_phuc_phien_tai_dung_khong_tao_moi` |
| Tái dùng, không controller → can_nguoi | Fail-closed: điểm chặn mới của (c), chưa từng mở trình duyệt | `test_tai_dung_khong_controller_thi_can_nguoi` |
| Email, không controller → trinh_duyet_none | Fail-closed ở đường email (đối tác của SAI S1 — đường này chỉ chạy được khi lõi cấp controller) | `test_email_khong_controller_thi_trinh_duyet_none` |
| Email trực tiếp → session | Đường email còn nguyên: điền email + mật khẩu → đọc `__Secure-1PSID` → kiểm phiên bằng `init()` → trả cookie | `test_email_truc_tiep_tra_session` |
| T2 email → thành công | Đăng nhập lại bằng mật khẩu đã truyền qua controller lõi cấp → tang `T2` | `test_khoi_phuc_t2_email_tra_thanh_cong` |
| T2 email không mật khẩu → thieu | Không truyền mật khẩu, kho riêng rỗng → `thieu_mat_khau`, không vỡ, không tự bịa mật khẩu | `test_khoi_phuc_t2_email_khong_mat_khau_thi_thieu` |

Ghi chú về khuôn id hồ sơ (như delta Claude): id hồ sơ lõi phải đúng khuôn hex 16–64 ký tự (`MAU_HO_SO_TRINH_DUYET`); chuỗi `gemini-web-<hash>` của `ho_so_trinh_duyet` là id xem noVNC, thuộc không gian tên khác, không dùng làm id hồ sơ lõi. Test vòng đời dùng id hồ sơ dạng hex cho đúng khuôn.

Ghi chú về tập hold (phát hiện trong lúc viết test, không phải lỗi production): chú thích trong code nói «chỉ tín hiệu captcha mới đặt hold toàn cục», nhưng code dùng `khoa_google.TIN_HIEU_CAPTCHA` = {`captcha`, `cloudflare`, `thu_thach_truy_cap`} (3 tín hiệu). Test khóa đúng hành vi thật: cloudflare đặt hold, 2fa không đặt hold. Chú thích có thể sửa cho chính xác ở lượt sau, không đổi hành vi trong lượt này.

## Một sửa nhỏ (duy nhất ngoài test)

File `modules/gemini-web/module.py`, hàm `_dang_nhap_bang_trinh_duyet`: điều kiện dừng trước khi điền và sau mật khẩu mở rộng từ 3 tín hiệu (`captcha`, `xac_minh`, `cloudflare`) thành tập 5 tín hiệu thử thách (`captcha`, `xac_minh`, `xac_minh_thiet_bi`, `cloudflare`, `thu_thach_truy_cap`), qua hằng mới `_TIN_HIEU_THU_THACH_TRUOC_KHI_DIEN`.

Lý do: chú thích trong code vốn đã nói «CAPTCHA/2FA/xác minh thiết bị → dừng», nhưng kiểm thành viên tập hợp theo tên chính xác nên `'xac_minh_thiet_bi'` không khớp `'xac_minh'`, và `'thu_thach_truy_cap'` vốn không có trong điều kiện — hai tín hiệu này lọt qua bước điền rồi mới hỏng ở `khong_lay_duoc_phien`. Đã đo thật bằng controller giả trước khi sửa: với `thu_thach_truy_cap` trước khi điền, module điền cả email + mật khẩu rồi bấm đăng nhập, sau đó mới hỏng — không phải vượt (không lấy được phiên), nhưng không phải `thu_thach_truoc_khi_dien` đúng nghĩa, và tệ hơn là đã đưa thông tin đăng nhập vào trang đang có thử thách. Sau sửa, mọi thử thách trước/sau khi điền đều dừng đúng mã. KHÔNG đưa `'2fa'` vào tập dừng: 2fa giữ kênh TOTP riêng như cũ (không TOTP → `thu_thach_truoc_khi_dien`; có TOTP → `_xu_ly_2fa`).

Đỏ-trước-xanh: chạy file mới trên cây chỉ-(a)+(c) cho **3 failed / 20 passed** đúng 3 test thử thách; kiểm lại bằng stash sửa rồi chạy riêng 3 test đó cũng **3 failed**; sau sửa toàn file **23/23 xanh**.

## Số test

- Mới: `test/test_nv309_gemini.py` — **23/23 xanh** (venv NV289, pytest 9.1.1).
- Tập liên quan (có delta): **232 passed, 1 failed** — gồm (a) 11, (c) 6, gemini 23, NV89 gemini, NV93 gemini, gemini-web, gemini, module gemini tự động, NV94 phần 2, NV134 gemini tools, NV300 cach_dang_nhap, NV102 web gemini.
- Đối chiếu nền (a)+(c) không có delta (cùng tập, trừ file mới): **209 passed, 1 failed** — chênh đúng +23 test mới, **0 hồi quy**.
- Lỗi 1 failed duy nhất (cả hai cây, có sẵn trên nền, KHÔNG do delta này): `test_web2api_nv94_phan2.py::TestGrokWebBoLuuPhienGoogle::test_che_do_google_dung_tai_dung_ho_so` — grok-web T2 gọi `tai_dung_ho_so(..., chu_giu=email)` theo (c) nhưng fake `tai_dung_gia()` của test NV94 cũ không nhận kwarg `chu_giu` → `TypeError`. Đây là lệch (c)-vs-test-cũ thuộc vòng soát/gộp của (c), ngoài phạm vi delta này (delta này chỉ chạm gemini-web + test mới) nên không tự sửa.
- Lỗi thu thập `test_web2api_dang_nhap_tu_dong.py` (`ModuleNotFoundError: test.gia`) cũng có sẵn trên nền (a)+(c) không có delta — không liên quan, đã loại khỏi tập liên quan.
- Toàn suite lõi: chưa chạy lại riêng cho delta này (thay đổi chỉ là 1 điều kiện trong 1 module + 1 file test mới; tập liên quan đã bao hết đường gemini) — điều phối chạy toàn suite ở vòng soát/gộp nếu cần.
- Gap Google trong test = 0 nhờ `test/conftest.py` đặt `WEB2API_GOOGLE_GIAN_CACH_GIAY=0`; production mặc định **25 giây không đổi** (`GIAN_CACH_GIAY = 25.0`, không chạm).

## Chưa kiểm thật — cần làm sau gộp (MCP trước → noVNC thao tác tay)

Test controller giả chỉ chứng minh đường ống + quyết định của module, không chứng minh selector thật đúng. Các ô đều **chưa được xác nhận bằng tay** trong lượt này:

- Nút «Đăng nhập» (`_BO_CHON_DANG_NHAP` = `a[data-test-id="sidenav-error-action-link"], a[href*="accounts.google.com"]` — code ghi đã đo trên trang khách THẬT 18/10/2026, nhưng chưa có chủ máy chọn bằng tay qua noVNC ở vòng này).
- Nút chọn tài khoản Google (`_BO_CHON_GOOGLE` = `[data-identifier]`).
- Các bước popup OAuth / chọn tài khoản Google / đồng ý trong SSO thật: bộ điều khiển trừu tượng (`mo_trang`/`tin_hieu`/`dien`/`bam`/`doc_cookie`) KHÔNG có bước popup/chọn tài khoản đó — luồng SSO thật có thể cần thêm bước mà chỉ kiểm thật mới thấy. Module tự ghi rõ «CHƯA KIỂM với trang đăng nhập Google thật» và «luồng đăng nhập Google tay trên web thật có thể cần thêm bước».
- Ô email, ô mật khẩu ở trang đăng nhập Google (`accounts.google.com/signin/v2/identifier`).
- Ô «Xác minh bạn là con người» (Cloudflare) trên trang đăng nhập Google.
- Trình tự kiểm thật theo luật đứng: đầu tiên qua MCP (đường Google tái dùng hồ sơ bằng tài khoản Google đã cho phép — theo kế hoạch trio Claude → Grok → Gemini của chủ máy, cần tài khoản Gemini trong kho ở chế độ «dùng hồ sơ Google đã đăng nhập» + id vào danh sách cho phép MCP + dựng lại trước), rồi chủ máy thao tác tay qua noVNC chọn đúng ô (không chỉ xem thụ động).

## Quét

Không bí mật/khoá/cookie/mật khẩu/email thật/IP thật trong patch/báo cáo/log: tài khoản test dùng miền `example.com` + chuỗi giả rõ ràng (`mat-khau-gia`, `psid-gia-…`, `psidts-gia-…`); không chạm `web/` (giao diện tài khoản AI giữ nguyên); không chạm ChatGPT; không làm NV309-d.
