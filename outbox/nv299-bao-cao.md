# NV299 — BÁO CÁO ĐẶC TẢ (nộp TRƯỚC mã)

## KẾT QUẢ

Đặc tả NV299 đã viết xong, **chưa viết mã triển khai** nào (đúng yêu cầu «đặc tả nộp TRƯỚC
mã»). Nộp nhánh Giao `muse/nv299` (xem «Xác minh nộp» cuối báo cáo).

- `outbox/nv299-dac-ta.md` — đặc tả đầy đủ (bảng trách nhiệm, sơ đồ chuyển quyền, tài khoản
  ghi, tab theo demo, mô hình dữ liệu, hợp đồng API đề xuất, nghiệm thu + kế hoạch kiểm thật,
  giới hạn chưa kiểm chứng).
- `outbox/nv299-mau-giao-dien.html` — mẫu giao diện HTML tĩnh theo NV299 §5 (token của
  `web/Nha.dc.html` + `khung.css`; dữ liệu trong mẫu chỉ minh hoạ bố cục, bản triển khai phải
  thay bằng dữ liệu thật, chưa có thì «Chưa có dữ liệu»).
- `outbox/nv299-bao-cao.md` — báo cáo này.

**Base đã đối chiếu:** Giao main `82d9ff46` · web2api main `8ed35ab` · chatgpt2api `d879b03`
(cùng commit c2a mà bảng NV309 đã đối chiếu).

## Đã phân tích chatgpt2api file/hàm nào (luật 16:11)

Repo công khai `TriTue2011/chatgpt2api`, commit `d879b03`, **chỉ clone đọc, không sửa**:

- `services/mang_nha.py` (791 dòng, toàn bộ hàm chính): `chan`, `mo`, `_dam_bao_luat_chan`,
  `gioi_han`, `khoa_dhcp`, `ep_dns`, `dat_vpn`, `kick`, `duyet`, `cho_duyet`, `dat_ten`,
  `dat_bang_thong`, `danh_sach`, `het_han` — c2a **có đầy đủ quyền ghi MikroTik**.
  Mẫu tốt mang sang: luật drop đứng đầu forward; chặn bằng address-list + timeout; ép DNS
  bằng `reject` (không phải `drop`); đổi nguy hiểm thì báo trước hậu quả rồi mới làm.
- `services/routeros.py` (145 dòng): `Phien`, `ket_noi`, `cau_hinh` — w2a đã có client tương
  đương (chỉ lệnh đọc), không cần port lại client.
- `api/mqtt.py` dòng ~223–268: c2a chỉ có **kiểm nối thử** AdGuard (version + số bộ lọc).
- Grep toàn repo `adguard`: ngoài 3 chỗ trên, **không còn gì** — c2a **không có module AdGuard**,
  không thống kê, không chính sách, không dự phòng.
- Grep `mang_nha.py` với `du_phong`/`fallback`/`suc_khoe`/`health`: **0 kết quả** — c2a
  **không có chuyển quyền khi AdGuard lỗi**. Đây là thiết kế mới của w2a, không phải port.

**Kết luận theo luật 16:58 (khác c2a chưa chắc sai):** phần MikroTik-ghi thì c2a đi trước và
đáng học mẫu; phần AdGuard thì w2a đã hơn c2a (thống kê + công tắc `bao_ve`) nên đặc tả
**không port mù** — tài khoản ghi, định danh máy, chuyển quyền đều thiết kế lại theo quy tắc w2a.

## Các điểm sai hiện tại đã liệt kê (phản ánh 16:29 — liệt kê TRƯỚC phương án)

So với NV299 + demo (8 điểm D1–D8 trong đặc tả §2.1): tab AdGuard chưa có hàng chip con
(Tổng quan · Máy khách · Đã chặn · Trạng thái dự phòng · Cài đặt); không chặn dịch vụ theo tên
theo máy/nhóm/giờ; bấm máy khách không xem được tên miền gần nhất; không có «Trạng thái dự
phòng»; không có biểu đồ theo giờ; không có chuyển quyền khi AdGuard lỗi; không có tài khoản
ghi `w2a-chan`; không có dòng «Ai làm gì».

So với chatgpt2api (5 điểm C1–C5 trong đặc tả §2.2): MikroTik w2a hoàn toàn chỉ đọc trong khi
c2a ghi đủ thứ (thiếu chặn đường NV299 §2 + NV290 — nhưng «chỉ đọc» là thiết kế an toàn cố
ý lúc NV279, nên phương án tách tài khoản ghi riêng thay vì copy tài khoản đặc quyền của c2a);
w2a không ép được DNS về AdGuard (c2a đo 90 ngày: không ép thì máy né hết); định danh theo
MAC vỡ với MAC ngẫu nhiên (c2a tự cảnh báo — phương án theo NV290 §E: ClientID → WireGuard →
SSID/VLAN → chỉ máy MAC cố định mới duyệt-theo-MAC); c2a không có gì về AdGuard để mà «sai
theo» (không kết luận sai); c2a một tài khoản đặc quyền duy nhất (không copy).

**Không sai ở vị trí đặt tab (ghi rõ để khỏi sửa lùi):** manifest `adguard` đã đặt đúng
Nhà ▾ → Mạng, chip «DNS & chặn» thứ tự 40, sau Thiết bị/Chờ duyệt/VPN, khớp thứ tự chip demo.
Vị trí giữ nguyên, chỉ thêm nội dung trong tab.

## Vị trí tab/chip + lý do (không vênh với QUY-TAC)

- Nhà ▾ → Mạng, chip «DNS & chặn» (đã có — giữ nguyên) + hàng chip con mới
  Tổng quan · Máy khách · Đã chặn · Trạng thái dự phòng · Cài đặt (Cài đặt cuối, luôn ẩn).
- Thông tin kết nối + tài khoản `w2a-chan` nằm trong chip «Cài đặt» của chính module
  (QUY-TAC quy tắc 1: kết nối RA ngoài nằm trong module, luôn ẩn, bí mật chỉ ghi đè).
  **Không** nằm ở «Bảo mật & người dùng» (quy tắc 2 chỉ dành cho khoá DO web2api CẤP cho thứ
  gọi VÀO; đây là thông tin để web2api gọi RA router) — điểm này dễ nhầm nên đặc tả nêu rõ.
- Tài khoản ghi: quyết **khả năng ghi riêng trong cùng module MikroTik** (không lập module
  thứ hai — tránh nhân đôi sổ thiết bị và hàng chip), tài khoản RouterOS riêng `w2a-chan`,
  **mặc định TẮT**, quyền hẹp (chỉ danh sách địa chỉ + MỘT luật filter `w2a-chan` + DNS +
  đọc đối chiếu), mọi ghi qua cổng xác nhận một lần NV298 + rủi ro `nguy_hiem`. Trả lời câu
  hỏi mở của NV290 (tách khả năng hay module thứ hai): chọn tách khả năng, lý do trong đặc tả §5.

## Quyết kiến trúc quan trọng nhất: chuyển quyền chạy TRÊN ROUTER

web2api chỉ (a) đồng bộ trước chính sách «quan trọng» sang danh sách địa chỉ `w2a-chan-*`
của router và (b) hiển thị + báo. Cái bật/tắt chuyển đổi là cơ chế router (netwatch/script/
scheduler) — AdGuard chết mà web2api cũng chết thì nhà vẫn có mạng và vẫn giữ chặn.
Bất kỳ thiết kế nào đặt «web2api phát hiện rồi ra lệnh chuyển» đều sai yêu cầu NV299 §2.
Thăm dò hai kênh độc lập (truy vấn DNS thật + API) để phân biệt «DNS chết» với «API chết»;
ngưỡng đề xuất 30 giây × 3 lỗi liên tiếp → chuyển, 3 lần đạt → trả (chủ máy chốt khi duyệt,
không phải số đã đo). Báo đúng một lần mỗi lần chuyển/trả; luật dựa vào dữ liệu AdGuard tạm
ngừng khi AdGuard lỗi (không coi «mất dữ liệu» là tấn công); nhóm cách ly/IoT giữ nguyên
chặn ở router.

## Phần nào chưa kiểm chứng được và vì sao

- **Không có router/AdGuard thật:** mọi hành vi RouterOS (phân giải tên miền trong
  address-list, tách quyền nhóm, netwatch) và AdGuard (ClientID, nhật ký) đều là «cần đo»,
  không phải «đã đo» — đặc tả để ở dạng đề xuất + «danh sách đo thật» (§8.3), không bịa.
- **Không có Chrome trên máy này:** không chụp ảnh trước/sau thật; ảnh + kiểm giao diện
  thuộc lượt triển khai (vòng QUY-TAC).
- **support.js vẫn thiếu trên main `82d9ff46`** (kiểm lại: thư mục demo có 10 trang `.dc.html`
  + `canvas.json` + ảnh `ANH-DUNG-*.png` nhưng không có `support.js`, dù `DOC-TRUOC.md` nói
  bắt buộc). Đặc tả bám mã nguồn `.dc.html` + ảnh `ANH-DUNG-*.png`, không bịa ảnh đối chiếu.
- **Mẫu HTML là phác tĩnh**, chưa chạy qua trình duyệt thật.
- File NV299 ghi «sau NV297+298» nhưng lượt này làm theo lệnh kéo NV299 lên (NV297+NV298 chưa
  rõ vị trí trong danh sách mới); đặc tả không phụ thuộc thứ tự đó.
- **Không đổi module hiện có ở lượt này** — mọi thay đổi code thuộc lượt triển khai sau khi
  duyệt đặc tả. NV290 đọc kết quả này được: bảng trách nhiệm, sơ đồ chuyển quyền, mô hình dữ
  liệu, hợp đồng API đề xuất đều đủ để NV290 dùng.

## Xác minh nộp

- Nhánh: `muse/nv299` — kiểm `ls-remote` sau khi đẩy (tip + trạng thái main ghi ở đây khi
  đẩy xong; nếu tip khác với báo cáo thì tip ls-remote là chuẩn).
- Không đẩy main, không force-push, không bí mật/token/mật khẩu/IP thật/email thật trong
  đặc tả/báo cáo/mẫu (dữ liệu mẫu trong file HTML là minh hoạ bố cục, không phải dữ liệu thật).
