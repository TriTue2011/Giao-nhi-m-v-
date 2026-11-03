# NV290 — BÁO CÁO NỘP: ĐẶC TẢ GIAI ĐOẠN 1 KHU «MẠNG NHÀ»

## KẾT QUẢ

- **Đã nộp:** nhánh `muse/nv290` với 3 file: `outbox/nv290-dac-ta.md` (đặc tả đủ A–F + mô
  hình dữ liệu + hợp đồng API + quyền RouterOS + danh sách đo thật), `outbox/nv290-mau-giao-dien.html`
  (mẫu giao diện tĩnh một trang «Mạng nhà»: khối A/B/C + dải cảnh báo D + trạng thái suy giảm +
  trạng thái chưa kết nối), và báo cáo này.
- **Giai đoạn 1 chỉ là đặc tả — không viết mã ghi lên router, không đổi module hiện có.**
  Mọi thay đổi code thuộc lượt triển khai sau khi chủ máy duyệt đặc tả.
- **Nền đối chiếu:** Giao main `82d9ff46` · web2api main `8ed35ab` (chỉ kiểm bằng ls-remote
  để tham chiếu cấu trúc module, không patch code) · chatgpt2api `d879b03` (chỉ clone đọc).

## Câu hỏi cho chủ máy (đặc tả KHÔNG tự chọn ngầm — xem mục 0 của đặc tả)

| # | Câu hỏi | Đề xuất trong đặc tả |
|---|---|---|
| Q1 | Vị trí thông tin kết nối: NV290 §1b nói Khu Tài khoản, QUY-TAC §1 (mới hơn) nói chip «Cài đặt» của module. Theo hướng nào? | Theo QUY-TAC: chip «Cài đặt» của chính module, luôn ẩn, bí mật chỉ ghi đè. |
| Q2 | Chủ sổ thiết bị mạng: lõi hay module? | Module MikroTik (kế thừa sổ NV279, mở rộng); lõi chỉ giữ hàng đợi phê duyệt + hiển thị tổng hợp. |
| Q3 | Giữ tóm tắt «dùng gì» theo máy bao lâu? (đổi quyết NV278) | Hằng số 30 ngày, không lưu toàn văn, bật/tắt từng máy. |
| Q4 | Trần tự cách ly: mấy máy/giờ thì dừng tự cách ly và báo? | Đề xuất 3 máy/giờ. |
| Q5 | Mặc định tự cách ly: bật cho camera/IoT, tắt cho NAS tới khi chủ máy xác nhận? | Giữ đúng NV290. |
| Q6 | Vị trí trang «Mạng nhà»? | Nhà ▾ → Mạng, đứng cạnh các chip module hiện có, không thay các chip đó. |
| Q7 | Mẫu luật firewall qua chat/Studio: đủ 5 mẫu hay thêm/bớt? | Đủ 5 mẫu cho giai đoạn 1. |
| Q8 | Quy tắc nền cho nhóm NAS «không có kết nối từ internet vào NAS» có chốt không? | Chốt: có (đây là điều kiện bị khai thác của ca NAS). |

## Quyết chốt trong đặc tả (đặc biệt: điểm vênh và điểm nhất quán)

- **Điểm vênh NV290 §1b vs QUY-TAC (Q1):** NV290 §1b (02/11) đặt thông tin kết nối ở Khu
  Tài khoản (nhóm riêng cho nhà/mạng); QUY-TAC §1 (03/11, mới hơn) đặt kết nối RA ngoài ở
  chip «Cài đặt» của chính module và chỉ dành Khu Tài khoản cho tài khoản AI. Đặc tả **làm
  theo QUY-TAC** và ghi Q1 để chủ máy chốt — không tự hoà giải.
- **Nhất quán với NV299 (đã đọc kỹ đặc tả NV299, `~/workspace/nv299/giao/outbox/nv299-dac-ta.md`):**
  chuyển quyền khi AdGuard lỗi lấy nguyên NV299 (chạy TRÊN ROUTER, không phụ thuộc web2api
  sống; thăm dò DNS thật + API; báo một lần; chế độ suy giảm có tên); tài khoản ghi `w2a-chan`
  nằm trong **cùng module MikroTik** (trả lời câu hỏi mở của NV290 §3: không lập module thứ
  hai — một sổ thiết bị, một kết nối, một hàng chip); thông tin kết nối trong chip «Cài đặt»,
  không ở «Bảo mật & người dùng»; sổ thiết bị mạng do module MikroTik giữ (NV299 §7.1).
  **Không có điểm vênh nào với NV299** — các điểm NV299 để mở (tài khoản ghi, vị trí kết nối)
  đều được NV290 trả lời theo đúng đáp án NV299.
- **Luật 19:30 (IP LAN bắt buộc) nhất quán với NV290 §E.6:** đường điều khiển web2api→router
  đi bằng địa chỉ IP LAN, không qua domain/WAN; cổng IP LAN của NV295 cưỡng chế luôn ở cấu
  hình. Không vênh.
- **QUY-TAC §5 vs NV295 (vênh nhỏ về cách diễn đạt, đã ghi ở mục 3 của đặc tả):** QUY-TAC
  §5 nói «hiện nút Tin chứng chỉ này» cho giá trị đo được; NV295 chốt sau đó là lần đầu tự
  ghim (không bấm gì), nút chỉ khi chứng chỉ đổi. Đặc tả áp dụng hành vi NV295.
- **Đổi quyết NV278 (Q3):** từ «không trả nhật ký truy vấn» thành mức riêng tư — chỉ tóm tắt
  (tên miền nổi bật + số lượt), giữ 30 ngày, không toàn văn, bật/tắt từng máy.
- **Trang «Thiết bị» chung vs `tuyen.phe_duyet`:** bỏ là bỏ **trang** (QUY-TAC §4); giữ là giữ
  **cơ chế hàng đợi** của lõi. Trang Mạng nhà là nơi duy nhất hiện hàng chờ duyệt mạng — không
  dựng hàng đợi thứ hai.
- **Luật firewall qua chat/Studio (F):** dùng luôn quyết chốt 02/11 21:06, không bàn lại —
  qua khả năng `nguy_hiem` + cùng lõi phê duyệt, không đường tắt riêng cho kênh; chỉ nhận
  lệnh từ chủ máy đã xác thực; KHÔNG gõ luật RouterOS thô — chỉ 5 mẫu luật tham số kiểm chặt
  (chặn máy, mở máy, cách ly, chặn cổng vào, đặt hạn giờ), xem trước, xác nhận khi ảnh hưởng
  nhiều máy, nhãn nguồn/giờ/người tạo/hạn (mặc định CÓ hạn), luôn có «hoàn tác» + nhật ký;
  luật nằm trong danh sách CỦA web2api (tiền tố `w2a-`), không đè luật gõ tay.

## Phân tích chatgpt2api (luật 16:11 — đã đọc, không chép nguyên)

- `services/mang_nha.py` (791 dòng, toàn bộ hàm chính): mẫu tốt mang sang — luật drop chặn
  đứng ĐẦU chuỗi forward (cắt cả phiên đang chạy); chặn bằng address-list + `timeout`; ép DNS
  bằng `reject` (không `drop`); đổi nguy hiểm báo trước hậu quả rồi mới làm (khoá DHCP liệt kê
  máy sẽ mất mạng, phải xác nhận); máy chờ duyệt bắt được cả khi đã khoá DHCP nhờ bảng host
  của bridge. Bẫy đã gặp: MAC ngẫu nhiên hiện như máy lạ; AP làm cầu; dải WireGuard
  `192.16.0.0/24` là dải công cộng nên c2a phải đoán WAN (w2a không đoán kiểu này); công tắc
  HA báo sai cho VPN (bật/tắt peer trong khi thứ tắt là giao diện) → w2a bật/tắt VPN phải đủ
  bộ giao diện+mangle+NAT.
- `services/routeros.py` (145 dòng, toàn bộ): client API-SSL 8729 tự viết, `CERT_NONE`, lỗi
  mang nguyên lời router. w2a đã có client tương đương (hiện chỉ lệnh đọc) — không port lại
  client, chỉ mở thêm lệnh ghi có lọc. Tài khoản c2a (nhóm `read,write,api`, chỉ đăng nhập từ
  một IP LAN cố định + luật input) là mẫu cho `w2a-chan`.
- **c2a CHƯA có phát hiện tấn công nào** (chỉ máy lạ, rớt mạng, hết hạn) — phần D của NV290 là
  **thiết kế mới, không phải port**; khác c2a ở đây không phải sai (luật 16:58).
- **Không chép nguyên c2a:** tài khoản ghi tách riêng + mặc định tắt (c2a dùng một tài khoản
  đặc quyền duy nhất); mọi ghi qua phê duyệt lõi + rủi ro `nguy_hiem`; bí mật trong kho;
  đường điều khiển bắt buộc IP LAN; không nhắc tên nhà cung cấp trong lõi.

## Nội dung đặc tả theo từng mục NV290

- **A:** một nút ngắt/nối internet cả nhà + hẹn giờ tự nối lại (mặc định 30 phút, chỉnh
  15/30/60/120, KHÔNG có vô hạn); luật filter duy nhất comment `w2a: ngắt internet cả nhà`
  (đầu forward, `src-address-list=!w2a-quan-tri` + ra WAN) + scheduler của router tự gỡ đúng
  hẹn (web2api chết vẫn tự nối lại); kiểm kết nối sau khi áp; rủi ro tự khoá + biện pháp
  (hẹn tự gỡ, luật chừa quản trị, kiểm sau khi áp, máy quản trị nên đặt IP tĩnh).
- **B:** máy mới (lease động / bridge host khi đã khoá DHCP) vào hàng chờ phê duyệt lõi
  `tuyen.phe_duyet` (GET danh sách, POST duyệt kèm step-up, POST từ chối) — không hàng chờ
  thứ hai; duyệt → lease tĩnh + nhóm + vào `w2a-duoc-phep`; luật `w2a: chỉ máy được duyệt
  mới ra internet`; khoá DHCP `static-only` chỉ cho máy MAC cố định, theo mẫu c2a (liệt kê
  trước + xác nhận); máy đổi MAC có định danh bền không tạo mục chờ mới; sơ đồ trạng thái
  `cho_duyet → duoc_phep / bi_chan` ở mục 5.3 của đặc tả.
- **C:** nguồn MikroTik (máy + tốc độ) + AdGuard (tóm tắt theo máy); phân loại «dùng gì» theo
  cấu trúc — chỉ tên miền nổi bật hoặc nhóm do AdGuard/bộ lọc của chính nó cung cấp, không
  danh sách từ khoá, không bảng tên dịch vụ tự dựng.
- **D:** thang mức chắc thấp (chỉ báo) / cao (báo + cách ly + cắt); 3 bước mức cao (báo ngay
  kèm bằng chứng ngắn + nút «Khôi phục»; cách ly qua `w2a-cach-ly` + luật đầu forward, chừa
  DNS nội bộ + đường quản trị, hẹn mở lại 24 giờ mặc định; cắt phiên + chặn tạm nguồn ngoài
  1 ngày + vô hiệu ánh xạ cổng/UPnP và báo rõ cái nào); 6 dấu hiệu cấu trúc S1–S6 kèm nguồn
  dữ liệu RouterOS/AdGuard; gác an toàn bắt buộc (danh sách bảo vệ không bao giờ tự cách ly;
  tự cách ly chỉ IoT/camera/NAS và chỉ mức cao; khôi phục một chạm; trần 3 máy/giờ đề xuất;
  công tắc tự cách ly; không tự cập nhật firmware). **Ca NAS:** chứng minh bắt được ở tầng
  mạng — tên tệp/đuôi tệp không đóng vai trò nào (router không thấy tệp bị mã hoá); quy tắc
  nền «không có kết nối từ internet vào NAS»; ánh xạ trỏ vào NAS → báo ngay + đề nghị tắt;
  nhiều IP lạ tới cổng quản trị NAS + NAS đổi hành vi → cách ly ngay + nhắc cập nhật DSM +
  kiểm sao lưu. **Ca camera Imou:** nhóm camera không ra internet mặc định, chỉ đích đã
  duyệt, không UPnP; ánh xạ do chính camera tạo → báo ngay; camera bị cách ly vẫn đọc được
  luồng nội bộ từ máy quản trị; xem từ xa chỉ qua WireGuard.
- **E:** bảng phân vai MikroTik/AdGuard (lấy NV299 §3); định danh bền ClientID → WireGuard →
  SSID/VLAN → chỉ máy MAC cố định mới duyệt-theo-MAC; bẫy nặc danh hoá DNS (router không
  được masquerade lưu lượng DNS tới AdGuard — kiểm bằng IP nguồn AdGuard thấy); dự phòng
  AdGuard lỗi lấy nguyên NV299 §4.
- **Mô hình dữ liệu (mục 10 của đặc tả):** sổ thiết bị mạng do module MikroTik giữ (lớp
  sighting từ sổ NV279 + lớp trạng thái duyệt/chặn/cách ly/nhóm/hạn + lớp định danh bền; một
  mục sổ = một thiết bị, MAC chỉ là thuộc tính); lõi giữ hàng đợi phê duyệt; module AdGuard
  giữ chính sách + tóm tắt «dùng gì»; router giữ danh sách `w2a-chan-*` (web2api đối chiếu).
- **Hợp đồng API (mục 11):** hành động ghi mới `mikrotik.ngat_ca_nha` / `noi_ca_nha` /
  `duyet_may` / `tu_choi_may` / `cach_ly` / `khoi_phuc` / `cat_ket_noi` (tất cả `nguy_hiem`,
  yêu cầu công tắc ghi đang BẬT) + hành động NV299 giữ nguyên + đường lõi `/api/phe-duyet`
  tái dùng; mã lỗi chung (thêm `khong_phai_ip_lan`, `thuoc_danh_sach_bao_ve`,
  `vuot_tran_cach_ly`, `luat_tay_mau_thuan`, …).
- **Quyền RouterOS (mục 12):** bảng từng khả năng → đường RouterOS → nhóm quyền đề xuất
  (`w2a-chan`: `api` + `read` + `write`, bù bằng giới hạn IP đăng nhập + code chỉ gọi đúng
  đường mang dấu `w2a-` + phê duyệt lõi + log) + ghi rõ nhóm RouterOS là thô nên phải đo
  thật mới chốt (M10).

## Danh sách đo thật cần chủ máy / điều phối làm (đặc tả KHÔNG đoán — mục 13 của đặc tả)

M1 phiên bản RouterOS + Kid Control + netwatch/script/scheduler; M2 giao diện WAN thật; M3
AdGuard bật nhật ký truy vấn chưa + ClientID đã gán cho máy nào; M4 luật chuyển hướng DNS có
nặc danh hoá không; M5 kênh thông báo dùng được; M6 DNS dự phòng nhà chọn; **M7 đo đường cơ
sở 24–72 giờ ở chế độ chỉ-quan-sát** (mọi ngưỡng mục 7.3 đều chốt từ đợt đo này); M8 camera mẫu
(cổng 37777 trong LAN); M9 NAS mẫu (cổng quản trị DSM, ánh xạ đang trỏ vào, phiên bản DSM);
M10 nhóm quyền RouterOS tách được tới đâu + cách phân giải tên miền trong address-list; M11
chặn DoH thực tế tới đâu; M12 kiểm Chrome thật + ảnh trước/sau 375 px + 1280 px.

## Giới hạn chưa kiểm chứng (ghi trung thực)

- Không có router/AdGuard thật để đo: mọi hành vi RouterOS, AdGuard và mọi ngưỡng phát hiện
  đều là «cần đo», không phải «đã đo».
- Không có Chrome trên máy này: ảnh trước/sau + kiểm giao diện thuộc lượt triển khai (vòng
  QUY-TAC).
- Demo chưa chạy đúng nghĩa: `support.js` vẫn thiếu trên main `82d9ff46` (đã kiểm lại ở
  NV299) — mẫu HTML bám mã nguồn `.dc.html` + ảnh + mô tả, không bịa ảnh đối chiếu.
- Mẫu HTML là phác tĩnh (CSS thuần, không JS chạy thật, không dữ liệu thật), chưa chạy qua
  trình duyệt thật.
- Ca NAS / camera là bài đăng cộng đồng chưa tự xác minh: đặc tả dựa trên hành vi chung,
  không dựa chi tiết khai thác chưa xác minh; chủ máy gửi liên kết/CVE nếu có thì đặc tả sẽ
  cập nhật.
- Không ghi bí mật/khoá/IP thật/email thật/vân tay thật/MAC thật vào đặc tả/mẫu/báo cáo/log
  (dữ liệu mẫu tự tạo, đã ghi rõ «mẫu» ở những chỗ dùng địa chỉ/MAC ví dụ).
