NV297 + NV298 — KẾT QUẢ (cây làm việc, chưa commit/push)
==========================================================
Cây: /tmp/claude-0/-opt-claude-c2a/99de6e4e-2d2d-4661-9468-892f33c7e2c3/scratchpad/w2a-nv297 (worktree tách khỏi w2a-merge HEAD 6ee1d92)
Ảnh chụp: /tmp/claude-0/-opt-claude-c2a/99de6e4e-2d2d-4661-9468-892f33c7e2c3/scratchpad/anh-nv297/ (demo-nha-mang.png là demo; còn lại do test Chrome chụp)

1. BẢNG ÁNH XẠ module → tab (suy từ cấu trúc manifest, KHÔNG bảng tên module) — app/kham_pha.py `giao_dien_cua`
   - manifest khai `giao_dien` {khu, muc, nhan, chip[]} thì dùng nó (trường MỚI, tuỳ chọn; chuẩn hoá như `nhom_con`: sai thì cảnh báo rồi bỏ).
     Lý do thêm: AdGuard và MikroTik cùng `loai: thiet_bi`, `nhom_con: null` — không trường nào có sẵn nói «đây là Mạng».
     KHÔNG dùng lại `nhom_con` (nó là làn của tab Module, tab đó không đổi).
   - không khai thì suy: loai «nha»/«thiet_bi» → Nhà; loai «tien_ich» + nhom_con {doi-song-va-giai-tri, van-phong-va-tai-lieu} → Đời sống;
     cung_cap có anh/anh_sua/video → Tác phẩm; còn lại (AI chỉ chat, kênh nhắn tin) → không vào tab nào.
   - lõi đếm mã «khu_nha / khu_doi_song / khu_tac_pham» cùng chỗ với loại/cung_cap trong /api/tinh-nang → khung vẫn dùng MỘT hàm `thieu`.
   - Mục demo chưa có module cấp: «Pin», «Khuôn mặt», «Học hỏi» (Nhà); YouTube/Zing/Facebook thật (Đời sống: module youtube-phat có, chưa dựng chip riêng);
     thư viện ảnh của Tác phẩm (chưa có nơi lưu tác phẩm — Studio giữ ảnh trong trang) → «Chưa có dữ liệu», không vẽ mục giả.

2. LÀM ĐƯỢC (có test Chrome thật, xem bên dưới)
   - Thanh chính: Studio · Tác phẩm ▾ · Nhà ▾ · Đời sống ▾ … Hệ thống; tab chỉ hiện khi có module đã cài; gỡ module cuối thì biến mất; gõ tay trang hết module → về Module kèm lời giải thích.
     Menu ▾ liệt kê MỤC (Nhà → Mạng). Điện thoại: thanh dưới tối đa 5 (Studio, Tác phẩm, Nhà, Đời sống, Hệ thống), menu thả có mũi nhọn.
   - Nhà → Mạng với AdGuard + MikroTik thật: chip Thiết bị · Chờ duyệt · VPN · DNS & chặn · Cài đặt (thứ tự do `thu_tu` trong manifest). Số liệu = thực thể thật của module;
     chưa đo được thì «Chưa có dữ liệu»; máy không tên → «Máy chưa đặt tên» + IP (lõi điền ten = id khi trống — đã chặn lộ id). «Chờ duyệt» chưa module nào cấp (NV290) → báo rỗng thật.
   - «Cài đặt» luôn ẩn tới khi bấm; dùng lại K.cauHinh.vm thu gọn: «••••• đã lưu» + Đổi, bí mật không bao giờ trả lại. Module chưa nối: mở sẵn MỘT form ngắn trong chính module, Lưu xong về số liệu và cài đặt tự thu gọn.
   - BỎ: web/He-thong-Thiet-bi.dc.html, mục «Thiết bị» ở thanh Hệ thống, lọc/nút Đọc-Ghi-Nguy hiểm, «Đặt rủi ro», «Chờ duyệt thực thể», id kỹ thuật, «Chưa phân khu».
   - Hàng chờ phê duyệt của khoá khách (cổng lõi 202) chuyển thành khối «Chờ bạn duyệt» ở đầu trang khu — không mồ côi.
   - Đời sống, Tác phẩm: cùng bộ dựng (Khung.khu) — chip theo module, ô số liệu thật; Tác phẩm hiện rỗng thật (không ảnh mẫu).

3. LÕI (NV298 #3) — app/thiet_bi.py `tinh_rui_ro_hieu_luc`
   Thực thể CHỈ ĐỌC (khai «doc» VÀ không có hành động) coi như đã xác nhận ngay lúc cài, tính tại chỗ (không ghi sổ) nên cổng/máy mới phát hiện sau cũng không quay lại «chờ».
   Thực thể có hành động giữ nguyên cổng SEC-004f: hành động GHI/nguy hiểm vẫn xác nhận MỘT lần lúc gọi (ngay trong ô, nút «Xác nhận»; lõi vẫn đòi step-up mật khẩu cho quản trị); khách vẫn vào hàng chờ 202.
   API /rui-ro và /xac-nhan giữ nguyên (test lõi dùng); chỉ bỏ giao diện. Chủ máy có thể bỏ nốt cổng hành động sau.
   Thêm trường tuỳ chọn `nhom` của thực thể (qua danh sách trắng của lõi) để module chia chip (MikroTik: may/router/cong/vpn).

4. TEST ĐÃ SỬA THEO THIẾT KẾ MỚI (chỉ test khẳng định GIAO DIỆN cũ; test an ninh/lõi KHÔNG nới)
   - xoá test_web2api_giao_dien_thiet_bi.py (trang đã bỏ); nv155: bỏ 2 test giao diện trang Thiết bị, giữ 3 test lõi (cho_xac_nhan) nguyên văn.
   - nv98_csp, nv56, dang_nhap_giao_dien, nv106, nv47_xss, thiet_bi test_3: thay trang Thiết bị bằng ba trang khu; nv47: khẳng định mới (trang khu không nghe SSE, không innerHTML).
   - test_web2api_tinh_nang: hai dòng khẳng định hình dạng đầy đủ thêm `khu_tac_pham` / `giao_dien` (hợp đồng /api/tinh-nang rộng thêm).
   - MỚI test/test_web2api_nv297_khu.py: 4 test lõi + 8 test Chrome (cài/gỡ theo loại, Nhà→Mạng, Cài đặt ẩn, chưa nối, hành động nguy hiểm, hàng chờ, 375px, Đời sống/Tác phẩm, ?da_cai).

5. ĐO «BAO NHIÊU BƯỚC» từ «cài module mạng» tới «thấy số liệu» (đếm theo mã, không đo người)
   - trước: Cài → mở chi tiết module → tab Kết nối → điền → Lưu → Hệ thống → Thiết bị → mỗi thực thể «chờ xác nhận» phải bấm xác nhận/đặt rủi ro (AdGuard 6–7 ô) ≈ 8 lần bấm + 7 nữa.
   - sau: Cài (tự chuyển sang Nhà → Mạng) → điền MỘT form hiện sẵn → Lưu = 2 lần bấm; đã nối sẵn thì Cài = thấy ngay.
