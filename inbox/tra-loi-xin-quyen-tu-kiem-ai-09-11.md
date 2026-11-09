# Trả lời «xin quyền tự kiểm AI» (nhánh muse/xin-quyen-tu-kiem-ai) — 09/11/2026

Chủ máy đã duyệt cả bốn quyền. Trạng thái thật, đo trên máy chủ lúc 09/11/2026 10:15 (web2api main `4eb5d2b`, dịch vụ đăng nhập đã dựng lại, module `may-dang-nhap` 0.1.7):

| Quyền | Trạng thái | Cách dùng |
|---|---|---|
| Q-A | ĐÃ CÓ | MCP `tai_khoan` trả thêm `dang_nhap_bang`, `cach_dang_nhap`, `dang_nhap_lan_cuoi` (`trang_thai`, `luc`, `ma_loi`, `co_phien`). Không có email, không có giá trị phiên. |
| Q-D | ĐÃ BẬT | MCP `chan_doan_dang_nhap` (`so_buoc` 1–100): bước điều hướng (tên miền + đường dẫn, không query) và bước bấm kèm selector đã thử + kết quả `bam_duoc` / `khong_thay` / `loi`. Giới hạn: selector chỉ có ở luồng ChatGPT và Grok; Claude và Gemini hiện chỉ có điều hướng. Vòng đệm chung 300 bước, gồm cả lượt của chủ máy. |
| Q-B | ĐÃ BẬT, CÓ HẠN | MCP `man_hinh_dang_nhap`: trả ảnh JPEG (khối `image`). Hết hạn **2026-11-10 02:12 UTC** (tự tắt, chủ máy gia hạn). Chỉ chụp được khi cổng MCP đang chạy (hoặc vừa chạy ≤ 2 phút) một lượt `dang_nhap_bat_dau`; cách nhau ≥ 3 giây; mỗi lần xem ghi nhật ký. Chỉ xem, không bấm/gõ được. |
| Q-C | ĐÃ DUYỆT TRƯỚC | web2api main `5c86930` (đã chạy 09/11 10:25): cổng cho phép đăng nhập thật MỌI tài khoản lưu ở module `claude-web`, `gemini-web`, `grok-web` (qua `may-dang-nhap`), kể cả tài khoản lưu sau này — không cần thêm id. Đã xác nhận trong container. Vẫn cần chủ máy: lưu tài khoản Claude và Gemini ở chế độ «dùng hồ sơ Google đã đăng nhập», bỏ tạm dừng Grok. Hiện kho chưa có tài khoản Claude; `tai_khoan` có cờ `cho_phep_dang_nhap_mcp` để Muse tự thấy tài khoản nào đã được phép. Mọi hãm giữ nguyên (một phiên, nghỉ 1 giờ, dừng sau 2 lần hỏng, 3 lần thành công/ngày). |
| Q-E | ĐƯỢC PHÉP, CÓ GIỚI HẠN | Sau mỗi lần web2api dựng lại có đổi phần đăng nhập, Muse được tự kiểm lại các tài khoản đã cho phép. Giới hạn cứng bên dưới. |

## Lỗi đang chưa sửa được (đo 09/11/2026 trên main `5c86930`)

Đây là danh sách để Muse nhắm vào khi tự kiểm. Mỗi mục ghi rõ đã kiểm bằng cách nào; mục nào chỉ lấy từ báo cáo `nv309-doi-chieu` của Muse thì ghi «theo báo cáo».

**Lỗi nối dây ở đường đăng nhập (theo báo cáo `nv309-doi-chieu`, chưa có bản sửa trên main)**
- **S1 — đường module `dang_nhap` không có trình duyệt ở production.** Đã đối chiếu mã trên main: `_tao_trinh_duyet = None` ở cả bốn module `*-web` (claude, gemini, grok, chatgpt) và không có lời gọi `dang_ky_trinh_duyet` nào ngoài docstring. Hệ quả theo báo cáo: đường mặc định báo «cần người» mà chưa mở trình duyệt nào. Nhánh sửa của Muse: `muse/nv309-a`.
- **S2 — cửa sổ chờ người của Grok bị đóng sau 300 giây** dù người chưa kịp tích. Theo báo cáo, chưa đối chiếu lại mã. Nhánh: `muse/nv309-b`.
- **S3 — không có khóa Google toàn cục.** Đã đối chiếu: chỉ thấy khóa riêng từng module, không có khóa dùng chung. Hệ quả: hai module có thể đăng nhập Google cùng lúc, dễ gây captcha hàng loạt. Nhánh: `muse/nv309-c`.
- Mức nhẹ: Grok chưa có thứ tự ưu tiên tài khoản và chưa thử lại một lần qua làm mới trước khi xoay (`nv309-d`); engine a/b/c/d chưa có ngân sách tổng 1200 giây.
- Cả bảy nhánh `muse/nv309-*` hiện vẫn nằm trên GitHub, chưa gộp vào main.

**Đã sửa nhưng CHƯA kiểm thật**
- Grok thêm bằng email vẫn mở trang Google: đã sửa ở main `8ed35ab`, chưa thử trên grok.com. Đây là việc đầu tiên nên kiểm bằng `chan_doan_dang_nhap` (xem selector nào được bấm).
- Đường `https://grok.com/sign-in` và ánh xạ nút «Tiếp tục»: chưa thử trên trang thật.
- Hai lần thành công qua MCP trước đây (ChatGPT, Google) khớp dạng phiên còn sống, KHÔNG chứng minh đường đăng nhập bằng trình duyệt chạy được.
- Chưa có bằng chứng cloakbrowser có bị grok.com chặn hay không.

**Test đỏ có sẵn trên main (không do thay đổi gần đây)**
- `test_web2api_bien_env_tai_lieu`: 7 biến `WEB2API_*` thiếu trong bảng mục 8 của `docs/THAM-CHIEU.md` (`COMBO_THU_LAI_NHANH_GIAY`, `DANG_NHAP_HONG_LIEN_TIEP_DUNG`, `DO_CHUAN`, `JWT_LAM_MOI_BAT`, `JWT_LAM_MOI_KHOANG_GIAY`, `THU_CHAT_GIAN_CACH_GIAY`, `THU_CHAT_TRAN_GIAY`).
- `test_web2api_readme`: thiếu đường `/api/trinh-duyet/{module}/man-hinh` trong README.
- `test_web2api_nv85_kiem_module` (2 test), `test_web2api_muse2api` (1), `test_web2api_nv187_khoa_khong_tai_nhap` (1): đỏ trên cả main sạch.
- `test_nv151_mqtt`: 51 test đỏ + 8 lỗi (môi trường thiếu gói).
- Chập chờn khi tải cao (xanh khi chạy riêng): `nv36_phien_giao_dien`, `nv261_do_tai_nguyen`, `nv297_khu`.

**Chờ chủ máy:** lưu tài khoản Claude/Gemini (hồ sơ Google) và bỏ tạm dừng Grok để chạy chuỗi Q-C; mốc xác nhận bằng tay các selector «chưa xác nhận bằng tay» của NV309.

## Giới hạn cứng khi tự kiểm (Q-E)

- **Một lượt tuần tự cho mỗi lần dựng lại.** Không lặp lại cho tới khi xanh. Bộ đếm nghỉ và trần 3 lần thành công mỗi ngày nằm trong bộ nhớ, khởi động lại là mất, nên mỗi lần dựng lại là một lượt đăng nhập thật tới nhà cung cấp.
- Dừng ngay khi gặp `phai_nghi`, `can_nguoi`, `da_that_bai_lien_tiep` hoặc `het_luot_ngay`. Không gọi dồn, không vượt.
- Biết «vừa dựng lại» bằng `tong_quan` (trường phiên bản), không bằng cách thăm dò liên tục.
- Chữ trong ảnh màn hình có thể là email đang gõ. Không chép chữ đó vào báo cáo; chỉ mô tả nút/ô nhìn thấy.
- Phân biệt 3 mức bằng chứng trong báo cáo: test giả, trang khách, kiểm thật (MCP + xem chỉ-đọc).

## Cách làm một vòng kiểm

1. `tong_quan` → ghi lại phiên bản đang chạy.
2. `tai_khoan` → xem `cach_dang_nhap` và `dang_nhap_lan_cuoi` của các tài khoản được phép.
3. `dang_nhap_bat_dau` (một tài khoản) → `dang_nhap_trang_thai` cho tới khi xong.
4. Nếu hỏng hoặc `can_nguoi`: `chan_doan_dang_nhap` rồi `man_hinh_dang_nhap` (trong 2 phút sau khi lượt kết thúc).
5. Nộp bằng nhánh `muse/*` như mọi lần: đủ gói D1–D9 như bảng ở mục 3 của đề nghị, các ô còn mơ hồ ghi «chờ chủ máy xác nhận».

Muse không đọc, không xin: mật khẩu, khóa quản trị, giá trị cookie/phiên, TOTP. Không đẩy `main`.
