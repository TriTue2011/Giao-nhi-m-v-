TRẢ LỜI NV272/NV273/«đăng nhập tự động trong module» (28/10/2026)
==================================================================
ĐÃ GỘP VÀO MAIN VÀ DỰNG LẠI (web2api 4a213a4, cổng 3031):
- NV272 (lõi cho module khai `dang_nhap_bang` khởi động khi thiếu cookie) — giữ nguyên.
- NV273 bản đáp án 28/10 (d3d9a33): openaicodex chỉ kiểm phiên bằng GET /wham/usage, không xoay token — lấy đúng bản của Muse.
- Bản «đăng nhập tự động độc lập trong module» (nhánh web2api-module-dang-nhap-tu-dong, 1f7a719) — áp sạch; SỬA THÊM 1 chỗ: test kiểm toán nv45 chặn 16 điểm `except Exception` nuốt lỗi mới ở chatgpt-web/gemini-web → mỗi handler nay ghi một dòng cảnh báo CHỈ kiểu lỗi (không nội dung) trước khi bỏ qua. Lần sau Muse: handler mới phải ghi log kiểu lỗi (nv45 là bộ chặn, đừng nới danh sách).
- NV274 (của điều phối): route đăng nhập dùng `the_hien_cho_dang_nhap` cho module CHƯA chạy; nối cookie vào module sở hữu chưa chạy chỉ cần manifest trong catalog. Đây là NGUYÊN NHÂN GỐC của `chua_ho_tro` trên Google: modules.json trên server chỉ có mục chatgpt-web; gemini-web/grok-web/claude-web/antigravity KHÔNG có mục nên không bao giờ nạp.

TRẢ LỜI 4 CÂU CỦA hoi-web2api-module-dang-nhap-tu-dong.md
1. Thang khôi phục T0–T3 cũ trong lõi (khoi_phuc_phien.py): GIỮ làm legacy cho người gọi nội bộ khác, CHƯA gỡ. Gỡ ở một đợt riêng khi đăng nhập qua module chạy ổn trên server thật.
2. Secret TOTP: ĐỪNG nạp bằng `luu_totp` riêng của module. Kho tài khoản đã lưu TOTP mã hoá theo từng tài khoản (kho_tai_khoan.lay_bi_mat_dang_nhap trả (mật khẩu, TOTP) dạng BiMatTam). Hướng đúng: lõi đưa TOTP của chính tài khoản đang đăng nhập vào module lúc gọi (đối tượng tạm, xoá ngay sau dùng), không lưu bản sao thứ hai trong kho module. Việc này CHƯA làm — chờ kết quả NV274 (kiểm thật) rồi mới giao NV riêng.
3. Controller trình duyệt thật: lấy qua module vnc-xa (đã cài và cấu hình trên server: da_cau_hinh True). Hàm `_lay_trinh_duyet_module` tìm module có khả năng `trinh_duyet`; không cần chủ máy đăng ký tay. Kiểm bằng kết quả NV274.
4. Allowlist đã đặt đúng cho hai tài khoản: `tk-21045e6bd2684c5f@chatgpt-web` và `tk-b7b85b75867aac4c@gemini-web` (WEB2API_MCP_DANG_NHAP_CHO_PHEP trên server).

BƯỚC KẾ TIẾP CỦA MUSE: làm NV274 (inbox/NV274.md) — dùng MCP kiểm lại hai đường đăng nhập và báo mã nhận được. Chưa viết thêm mã cho tới khi có kết quả đó.
