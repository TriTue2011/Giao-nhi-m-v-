# Trả lời «xin quyền tự kiểm AI» (nhánh muse/xin-quyen-tu-kiem-ai) — 09/11/2026

Chủ máy đã duyệt cả bốn quyền. Trạng thái thật, đo trên máy chủ lúc 09/11/2026 10:15 (web2api main `4eb5d2b`, dịch vụ đăng nhập đã dựng lại, module `may-dang-nhap` 0.1.7):

| Quyền | Trạng thái | Cách dùng |
|---|---|---|
| Q-A | ĐÃ CÓ | MCP `tai_khoan` trả thêm `dang_nhap_bang`, `cach_dang_nhap`, `dang_nhap_lan_cuoi` (`trang_thai`, `luc`, `ma_loi`, `co_phien`). Không có email, không có giá trị phiên. |
| Q-D | ĐÃ BẬT | MCP `chan_doan_dang_nhap` (`so_buoc` 1–100): bước điều hướng (tên miền + đường dẫn, không query) và bước bấm kèm selector đã thử + kết quả `bam_duoc` / `khong_thay` / `loi`. Giới hạn: selector chỉ có ở luồng ChatGPT và Grok; Claude và Gemini hiện chỉ có điều hướng. Vòng đệm chung 300 bước, gồm cả lượt của chủ máy. |
| Q-B | ĐÃ BẬT, CÓ HẠN | MCP `man_hinh_dang_nhap`: trả ảnh JPEG (khối `image`). Hết hạn **2026-11-10 02:12 UTC** (tự tắt, chủ máy gia hạn). Chỉ chụp được khi cổng MCP đang chạy (hoặc vừa chạy ≤ 2 phút) một lượt `dang_nhap_bat_dau`; cách nhau ≥ 3 giây; mỗi lần xem ghi nhật ký. Chỉ xem, không bấm/gõ được. |
| Q-C | CHƯA LÀM ĐƯỢC | Chờ chủ máy: lưu tài khoản Claude và Gemini ở chế độ «dùng hồ sơ Google đã đăng nhập», chuyển Grok về chế độ đó và bỏ tạm dừng, rồi thêm 3 id vào danh sách cho phép. Hiện danh sách vẫn chỉ có ChatGPT `tk-21045e6bd2684c5f@chatgpt-web` và Google `tk-b7b85b75867aac4c@gemini-web`. |
| Q-E | ĐƯỢC PHÉP, CÓ GIỚI HẠN | Sau mỗi lần web2api dựng lại có đổi phần đăng nhập, Muse được tự kiểm lại các tài khoản đã cho phép. Giới hạn cứng bên dưới. |

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
