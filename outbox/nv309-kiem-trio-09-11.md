# KẾT QUẢ — Kiểm thật trio Gemini → Claude → Grok qua MCP (NV309 / xin quyền tự kiểm AI) — 09/11/2026

- **Đã đẩy nhánh `muse/nv309-kiem-trio-09-11`** (chỉ nhánh `muse/*`, không main, không
  force-push). Báo cáo này + thư mục bằng chứng
  `outbox/nv309-kiem-trio-09-11/` (bản ghi MCP thô).
- **Mức bằng chứng: kiểm thật (MCP + xem chỉ-đọc).** Không phải test giả, không phải
  trang khách. Lượt này chạy trên web2api thật qua cổng MCP, tài khoản thật đã
  được chủ máy cho phép (Q-C duyệt trước).

## Kết quả chính (từng tài khoản)

| Tài khoản | Mã kết quả cuối | Phiên | Thời gian chạy | Bước hỏng |
|---|---|---|---|---|
| Gemini `tk-b7b85b75867aac4c@gemini-web` | `thanh_cong`, `ma_loi: ""` | Có (`co_phien: true`) | Bắt đầu 2026-11-09T03:36:27Z, kết thúc 03:36:40Z — **13 giây** (10:36:27–10:36:40 +07) | Không có |
| Claude | **KHÔNG CÓ TÀI KHOẢN — không kiểm được** | — | — | Kho không có tài khoản `claude-web` nào (0/38 tài khoản) |
| Grok `tk-533b0186b574db97@grok-web` | **KHÔNG KIỂM (dừng ở Claude theo quy trình)** | — | — | Live: vẫn `tam_dung`, lần cuối `can_xu_ly` / `gap_captcha` |

## Quy trình đã chạy (đúng thư trả lời 09/11)

1. `tools/list` — 8 tool, có cả hai công cụ mới `chan_doan_dang_nhap` (Q-D) và
   `man_hinh_dang_nhap` (Q-B).
2. `tong_quan` — `phien_ban: "0.1.0-khung"`, máy chủ ok, 12 module đang chạy
   (trong đó `gemini-web`, `may-dang-nhap` đang chạy; `claude-web` và
   `grok-web` KHÔNG chạy), kho tài khoản ok. Lưu ý: `tong_quan` báo
   `so_tai_khoan_cho_phep_dang_nhap: 2` (xem nhận xét).
3. `tai_khoan` — tổng 38 tài khoản: `chatgpt-web` 30, `gemini-web` 7,
   `grok-web` 1, `claude-web` 0. Có 9 tài khoản `cho_phep_dang_nhap_mcp:
   true` (1 ChatGPT + 7 Gemini + 1 Grok) — Q-C duyệt trước đã có hiệu lực ở
   mức cờ cho phép. Nhưng: Claude 0 tài khoản; Grok vẫn `tam_dung`; cả 7 tài
   khoản `gemini-web` đều `cach_dang_nhap: email` (không có tài khoản nào ở
   chế độ hồ sơ Google), `dang_nhap_bang: ""` (trống).
4. Gemini (`tk-b7b85b75867aac4c`) — tài khoản Gemini được chỉ định từ trước
   (nằm trong danh sách cho phép gốc): `dang_nhap_bat_dau` → `phien_id:
   13d4454070ace898`, `trang_thai: dang_chay`. `dang_nhap_trang_thai` poll 1
   (sau ~5 giây) `dang_chay`, poll 2 (sau ~24 giây) `thanh_cong`,
   `ma_loi: ""`, `thu_lai_sau_giay: 3573` (~60 phút trước lượt kế).
5. `tai_khoan` lại — lần đăng nhập gần nhất của Gemini đã cập nhật: `ok`,
   `luc: 1794195397`, `co_phien: true`.
6. `chan_doan_dang_nhap` (`so_buoc: 50`) — 8 bước trong vòng đệm chung (2 bước
   `chatgpt.com/` từ lượt ChatGPT trước + 6 bước của lượt Gemini:
   `www.google.com/` ×4 và `myaccount.google.com/` ×2, tất cả `ok`, chỉ
   điều hướng, không có bước bấm/điền nào → không selector nào được thử).
7. Không gọi `man_hinh_dang_nhap` — chỉ dùng khi hỏng hoặc `can_nguoi`;
   Gemini thành công nên không có điểm hỏng để chụp.
8. Claude — xác nhận lại bằng `tai_khoan` mới (10:37): tổng 38,
   `claude-web` 0, không có chữ «claude» trong bất kỳ tài khoản nào. **DỪNG
   ở Claude theo quy trình** (không đoán, không tự tạo tài khoản). Không
   chuyển sang Grok.
9. Grok — không kiểm trong lượt này (dừng ở Claude). Live:
   `tk-533b0186b574db97` vẫn `tam_dung`, lần cuối `can_xu_ly` /
   `gap_captcha` / `co_phien: null`.

## Gói D1–D9 (theo bảng mục 3 của đề nghị xin quyền)

| # | Dữ liệu cần | Kết quả lượt này |
|---|---|---|
| D1 | Tài khoản: provider, module, chế độ đăng nhập, cờ có mật khẩu/TOTP | Gemini `tk-b7b85b75867aac4c@gemini-web`; `cach_dang_nhap: email`; `dang_nhap_bang: ""` (trống — xem ghi chú); `co_mat_khau: true`, `co_totp: true`, `cho_phep_dang_nhap_mcp: true`. Claude: không có tài khoản. Grok `tk-533b0186b574db97@grok-web`; `cach_dang_nhap: email`; `trang_thai: tam_dung`; `cho_phep: true` (chưa kiểm) |
| D2 | Đường đã đi + bước cuối tới được | Gemini: 6 bước điều hướng (`www.google.com/` ×4, `myaccount.google.com/` ×2, tất cả `ok`), không bấm/điền. Đây là kiểm phiên (T0): phiên còn sống nên xong luôn, không đi qua bước đăng nhập lại. Claude/Grok: không có đường đi (không kiểm) |
| D3 | Selector đã thử ở mỗi bước và kết quả | Không có bước bấm nào trong lượt Gemini → không selector nào được thử. Đúng giới hạn đã biết: Claude và Gemini hiện chỉ có điều hướng trong nhật ký bước |
| D4 | Ảnh màn hình tại điểm hỏng | Không có điểm hỏng ở Gemini nên không chụp. Không gọi `man_hinh_dang_nhap`. Claude/Grok không có điểm hỏng vì không kiểm |
| D5 | Tín hiệu thử thách đang hiện lúc hỏng | Không có (Gemini không hỏng; `ma_loi: ""`, không captcha/2FA/xác minh). Grok lần cuối trước đây: `gap_captcha` (dữ liệu cũ, không phải lượt này) |
| D6 | Kết quả cuối: mã + phiên có lấy được không | Gemini: `thanh_cong`, `ma_loi: ""`, `co_phien: true`; `dang_nhap_lan_cuoi` cập nhật `ok` lúc 1794195397. Claude: không có tài khoản. Grok: không kiểm |
| D7 | Trạng thái cổng: hold captcha / `phai_nghi` | Gemini: `thu_lai_sau_giay: 3573` (~60 phút) trước lượt kế. Không gặp `phai_nghi`, không có hold captcha trong lượt này |
| D8 | Phiên bản code đang chạy | `tong_quan` `phien_ban: "0.1.0-khung"`; web2api main `4eb5d2b`, module `may-dang-nhap` 0.1.7 (thư trả lời đo 10:15 09/11) |
| D9 | Hành vi kỳ vọng ở bước đó | Gemini khớp T0 (kiểm phiên trước, phiên sống thì xong) — cùng dạng với lượt ChatGPT 10:21 (8 giây) và hai lần thành công NV275. Lượt này **không** chứng minh được T2 (đăng nhập lại bằng mật khẩu+TOTP) qua MCP — xem nhận xét |

## Nhận xét trung thực

- **Gemini chỉ chứng minh T0 (phiên còn sống), KHÔNG chứng minh T2
  (đăng nhập lại đầy đủ bằng email + mật khẩu + TOTP).** Phiên của tài khoản
  đã sống sẵn từ lần trước nên module chỉ cần điều hướng tới
  `google.com`/`myaccount.google.com` để xác nhận, xong trong 13 giây. Muốn
  chứng minh T2 qua MCP cần một lượt mà phiên đã hết (hoặc một tài khoản chưa
  có phiên), lúc đó module mới đi qua bước điền/bấm — lượt đó chưa xảy ra.
- **Claude: kho vẫn chưa có tài khoản nào.** User báo «có rồi đó» nhưng
  `tai_khoan` live (10:36 và 10:37) đều cho 0 tài khoản `claude-web`, không
  có chữ «claude» trong bất kỳ tài khoản nào trong 38 tài khoản. Dừng ở
  Claude theo quy trình; cần chủ máy lưu tài khoản Claude rồi mới kiểm được.
  «Chờ chủ máy xác nhận» xem tài khoản Claude đã lưu ở đâu (có thể lưu chưa
  xong hoặc lưu vào chỗ khác).
- **Grok: vẫn `tam_dung`.** User báo đã bỏ tạm dừng nhưng `tai_khoan` live
  cho `trang_thai: tam_dung`, lần cuối `can_xu_ly` / `gap_captcha` /
  `co_phien: null`. Không kiểm Grok trong lượt này (dừng ở Claude). Cần chủ
  máy bỏ tạm dừng thật rồi mới kiểm được.
- **Gemini: 7 tài khoản, tất cả đều `cach_dang_nhap: email`.** Không có tài
  khoản `gemini-web` nào ở chế độ «dùng hồ sơ Google đã đăng nhập» theo
  trường `cach_dang_nhap`; `dang_nhap_bang` trống (`""`) cho cả 7. Tôi kiểm
  tài khoản được chỉ định từ trước (`tk-b7b85b75867aac4c`, nằm trong danh sách
  cho phép gốc). 6 tài khoản còn lại không kiểm trong lượt này: 5 chưa bao
  giờ đăng nhập (`chua`), 1 lần cuối `can_xu_ly` / `blocked_captcha_window`
  (`tk-f18c5153591199c1`).
- **Q-C duyệt trước đã có hiệu lực ở mức cờ cho phép:** 9 tài khoản
  `cho_phep_dang_nhap_mcp: true` (trước Q-C chỉ có 2). Nhưng `tong_quan`
  vẫn báo `so_tai_khoan_cho_phep_dang_nhap: 2` — bộ đếm này có vẻ chưa cập
  nhật theo Q-C (hoặc đếm khác). «Chờ chủ máy xác nhận» xem bộ đếm
  `tong_quan` đếm theo gì.
- **Không lặp lại lượt này cho tới khi xanh** (Gemini đã xanh) và không gọi
  dồn: `thu_lai_sau_giay: 3573` — lượt kế sớm nhất sau ~60 phút, và theo Q-E
  chỉ một lượt tuần tự cho mỗi lần dựng lại.
- **Quét:** không mật khẩu, không khóa quản trị, không giá trị cookie/phiên,
  không TOTP, không email, không IP trong báo cáo và bằng chứng (id tài khoản
  `tk-…` là định danh đã che, do MCP trả về; không có dữ liệu riêng nào khác).
