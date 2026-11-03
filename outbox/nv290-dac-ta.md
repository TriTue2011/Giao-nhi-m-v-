# NV290 — ĐẶC TẢ GIAI ĐOẠN 1: KHU «MẠNG NHÀ» (ĐẶC TẢ + MÔ HÌNH DỮ LIỆU + MẪU GIAO DIỆN)

> **Trạng thái:** ĐẶC TẢ — nộp TRƯỚC mã, theo đúng yêu cầu của NV290 (như NV299).
> Giai đoạn 1 CHỈ có đặc tả + mô hình dữ liệu + mẫu HTML tĩnh. **Không viết mã ghi lên
> router, không đổi module hiện có.**
> **Base đã đối chiếu:** Giao main `82d9ff46` (file `inbox/NV290.md` + `inbox/QUY-TAC-GIAO-DIEN-W2A.md`
> + `inbox/NV299.md` mục E) · web2api main `8ed35ab` · chatgpt2api `d879b03` (chỉ clone đọc, không sửa).
> **Nguồn thắng:** `inbox/NV290.md`. Mọi chỗ đặc tả này khác file đó đều ghi rõ là «đề xuất thêm»
> hoặc «điểm vênh — chờ chủ máy quyết».

## 0. KẾT QUẢ

- **Một trang «Mạng nhà» duy nhất theo ý định, không theo module:** 3 khối chính A (ngắt/nối
  internet cả nhà một nút + hẹn giờ tự nối lại), B (thiết bị mới phải duyệt mới ra internet),
  C (ai vừa dùng mạng, dùng gì) + một dải cảnh báo D (phát hiện xâm nhập → báo → cách ly →
  cắt đường) gọn ở đầu trang khi có sự kiện. Mẫu tĩnh kèm trong `outbox/nv290-mau-giao-dien.html`.
- **Chủ sổ thiết bị mạng là module MikroTik** (kế thừa sổ đã có từ NV279, mở rộng thêm trạng
  thái duyệt + định danh bền — không nhân đôi sổ). Lõi chỉ giữ cơ chế hàng đợi phê duyệt
  `tuyen.phe_duyet` (tái dùng nguyên, không dựng hàng đợi thứ hai) và khung hiển thị tổng hợp.
- **Khả năng ghi nằm trong cùng module MikroTik** (khớp đáp án NV299): tài khoản RouterOS riêng
  `w2a-chan`, mặc định TẮT, quyền hẹp, mọi ghi qua cổng xác nhận một lần NV298 + rủi ro
  `nguy_hiem`. Không lập module thứ hai.
- **Chuyển quyền khi AdGuard lỗi và phân vai MikroTik/AdGuard: lấy nguyên NV299** (chuyển chạy
  TRÊN ROUTER, không phụ thuộc web2api sống; MikroTik thắng; AdGuard lỗi thì lọc tên tạm tắt,
  chặn thô vẫn giữ) — đặc tả này không viết lại, chỉ nêu điểm nối với khu Mạng nhà.
- **Định danh khi MAC đổi liên tục:** ClientID AdGuard → peer WireGuard → SSID/VLAN riêng →
  chỉ máy MAC cố định (camera/NAS/IoT) mới duyệt-theo-MAC + khoá DHCP `static-only`. Máy đổi
  MAC đi qua ClientID/VPN/VLAN thì không tràn tin «máy lạ» mỗi lần xoay MAC.
- **Luật đứng 19:30 ngày 03/11 được tôn trọng:** đường điều khiển web2api→router bắt buộc bằng
  IP LAN, tuyệt đối không qua domain, không IP WAN — nhất quán với NV290 §E.6 (đi bằng địa
  chỉ IP, không qua DNS) và với cổng IP LAN của NV295.
- **Ngưỡng phát hiện KHÔNG đoán:** mọi ngưỡng ở mục 7 chỉ nêu tham số + cách đo trên mạng thật
  24–72 giờ; giá trị chốt sau khi đo (danh sách đo ở mục 11).

### Câu hỏi cho chủ máy (đặc tả này KHÔNG tự chọn ngầm)

| # | Câu hỏi | Đề xuất trong đặc tả (chủ máy chỉ cần nói «đúng» hoặc sửa) |
|---|---|---|
| Q1 | **Vị trí thông tin kết nối:** NV290 §1b (02/11) nói nằm ở Khu Tài khoản (nhóm riêng cho nhà/mạng); QUY-TAC (03/11, mới hơn) nói kết nối RA ngoài nằm trong chip «Cài đặt» của chính module (Khu Tài khoản chỉ cho tài khoản AI). Theo hướng nào? | Theo QUY-TAC: MikroTik/AdGuard nằm trong chip «Cài đặt» của chính module đó, luôn ẩn, bí mật chỉ ghi đè. Trang Mạng nhà khi chưa kết nối chỉ hiện dòng «Chưa kết nối — thêm ở Cài đặt của module …» + liên kết đúng dòng. |
| Q2 | **Chủ sổ thiết bị mạng:** lõi hay module? | Module MikroTik (kế thừa sổ NV279, mở rộng — mục 9); lõi chỉ giữ hàng đợi phê duyệt + hiển thị tổng hợp. |
| Q3 | **Giữ tóm tắt «dùng gì» theo máy bao lâu?** (đổi quyết NV278 «không trả nhật ký truy vấn» thành chỉ lấy tóm tắt) | Hằng số 30 ngày, không lưu toàn văn, chủ máy bật/tắt từng máy. |
| Q4 | **Trần tự cách ly:** giới hạn mấy máy bị cách ly trong một giờ thì dừng tự cách ly và báo? | Đề xuất 3 máy/giờ; chạm trần thì dừng tự cách ly, chỉ báo, chờ chủ máy. |
| Q5 | **Mặc định tự cách ly:** bật cho camera/IoT, tắt cho NAS tới khi chủ máy xác nhận (đúng NV290)? | Giữ đúng NV290: bật báo cho tất cả; tự cách ly bật cho camera/IoT, tắt cho NAS. |
| Q6 | **Vị trí trang «Mạng nhà»:** đặt ở đâu trong thanh chính? | Nhà ▾ → Mạng, đứng cạnh các chip module hiện có (Thiết bị · Chờ duyệt · VPN · DNS & chặn), không thay các chip đó. |
| Q7 | **Mẫu luật firewall qua chat/Studio:** đủ 5 mẫu (chặn máy, mở máy, cách ly, chặn cổng vào, đặt hạn giờ) hay cần thêm/bớt? | Đủ 5 mẫu cho giai đoạn 1; thêm mẫu phải qua duyệt đặc tả, không tự thêm lúc triển khai. |
| Q8 | **Quy tắc nền cho nhóm NAS:** «không có kết nối từ internet vào NAS» có chốt thành quy tắc nền (vi phạm là báo ngay) không? | Chốt: có. Đây chính là điều kiện bị khai thác của ca NAS (mục 7.4). |

---

## 1. Đã phân tích code chatgpt2api nào (luật 16:11)

Repo công khai `TriTue2011/chatgpt2api`, commit `d879b03`, **chỉ clone đọc, không sửa**
(bản đọc tại `~/workspace/nv299/c2a/`).

| File / hàm | Đã đọc | Kết luận đối chiếu |
|---|---|---|
| `services/mang_nha.py` (791 dòng): `quet`, `cho_duyet`, `duyet`, `khoa_dhcp`, `chan`, `mo`, `gioi_han`, `kick`, `bo_kick`, `ep_dns`, `dat_vpn`, `het_han`, `danh_sach`, `dat_ten`, `_may_dang_doi`, `_dam_bao_luat_chan`, `_dat_hang`, `_ip_trong`, `_quet_router` | Toàn bộ hàm chính | c2a **CÓ đầy đủ quyền ghi MikroTik** — mẫu tốt mang sang: (1) luật drop cho danh sách chặn đứng **ĐẦU chuỗi forward**, trước cả «Established» → chặn là cắt luôn kết nối đang mở; (2) chặn bằng address-list + `timeout` cho chặn có hẹn (router tự mở lại); (3) ép DNS bằng `reject` (không phải `drop`) để máy lỗi ngay và chuyển DNS dự phòng; (4) đổi nguy hiểm thì **báo trước hậu quả rồi mới làm** (khoá DHCP liệt kê máy sẽ mất mạng lần đầu, phải xác nhận mới làm — khớp cổng xác nhận một lần NV298 của w2a); (5) máy chờ duyệt bắt được cả khi đã khoá DHCP nhờ bảng host của bridge (máy lạ không có lease vẫn còn dấu ở bridge). |
| `services/routeros.py` (145 dòng): `Phien`, `ket_noi`, `cau_hinh`, `Loi` | Toàn bộ | Client RouterOS API tự viết (socket + mã độ dài nhị phân, API-SSL 8729, `CERT_NONE` + không kiểm tên máy chủ, timeout 8 giây, lỗi mang **nguyên lời router** — «bị từ chối phải nói vì sao»). w2a đã có client tương đương (`modules/mikrotik-routeros/routeros.py`, socket + ssl, hiện chỉ lệnh đọc) — **không cần port lại client**, chỉ cần mở thêm lệnh ghi có lọc. Tài khoản c2a: nhóm `read,write,api`, chỉ đăng nhập được từ một IP LAN cố định + luật input «c2a API SSL» — mẫu này mang sang cho `w2a-chan` (mục 10). |
| `services/mang_nha.py` — phần **không** có | Grep + đọc toàn file | **c2a CHƯA có phát hiện tấn công nào** — chỉ có máy lạ, rớt mạng, hết hạn. Phần D của NV290 là **thiết kế mới, không phải port**. Các bẫy c2a đã gặp và w2a phải tránh: (a) điện thoại bật «MAC ngẫu nhiên» hiện như máy lạ → khoá DHCP làm máy chưa duyệt mất mạng; (b) AP làm cầu nên MAC từng máy chỉ hiện trong bảng host của bridge; (c) dải WireGuard nhà dùng (`192.16.0.0/24`) là dải công cộng nên c2a phải đoán WAN bằng «giao diện nhận nhiều dữ liệu nhất» — w2a không đoán kiểu này, WAN lấy từ cấu hình rõ ràng; (d) công tắc HA báo sai cho VPN (bật/tắt peer trong khi thứ tắt là giao diện) → w2a bật/tắt VPN phải đủ bộ (giao diện + mangle + NAT đi kèm) như `dat_vpn` của c2a. |

**Kết luận tổng (kèm luật 16:58):** phần MikroTik-ghi thì c2a đi trước w2a và đáng học mẫu
lệnh; phần phát hiện xâm nhập thì c2a trống — «khác c2a» ở đây **không phải sai**. Đặc tả này
**không chép nguyên c2a**: tài khoản ghi tách riêng + mặc định tắt (c2a dùng một tài khoản
đặc quyền duy nhất), mọi ghi qua phê duyệt lõi + rủi ro `nguy_hiem`, bí mật trong kho, đường
điều khiển bắt buộc IP LAN, không nhắc tên nhà cung cấp trong lõi.

---

## 2. LIỆT KÊ ĐIỂM SAI HIỆN TẠI — đọc trước khi xem phương án (phản ánh 16:29)

Đối chiếu trên web2api main `8ed35ab`. «SAI» ở đây nghĩa là: hiện trạng **không đáp ứng
NV290**, không phải chê code cũ viết ẩu — nhiều chỗ là thiết kế cố ý lúc trước (chỉ đọc vì an
toàn, không trả nhật ký vì riêng tư) nay đã hết phù hợp với yêu cầu mới.

| # | Điểm sai hiện tại | Căn cứ đo được | NV290 đòi hỏi |
|---|---|---|---|
| W1 | **Không ngắt/nối internet cả nhà một nút.** Chỉ có chặn từng máy (chưa có — module MikroTik hiện chỉ đọc) và công tắc `bao_ve` của AdGuard (tầng DNS, không chặn được lưu lượng đi thẳng bằng IP). | `modules/mikrotik-routeros/manifest.json`: «CHỈ ĐỌC — không thực hiện hành động nào»; `modules/adguard/manifest.json`: chỉ 1 hành động `bao_ve`. | A: một nút + hẹn giờ tự nối lại + chừa quản trị. |
| W2 | **Thiết bị mới chưa bị giữ lại thật.** Sổ thiết bị hiện chỉ đọc lease/host và «tự động dọn thiết bị đã mất»; không có luật nào chặn máy ngoài danh sách được phép ra internet. | `modules/mikrotik-routeros/module.py` (đọc lease + host, sổ máy vắng); không có đường ghi nào. | B: MAC lạ bị giữ, duyệt mới cấp, tái dùng `tuyen.phe_duyet`. |
| W3 | **Không xem được «dùng gì» theo máy.** Module AdGuard nói thẳng: «Không trả nguyên nhật ký truy vấn». | `modules/adguard/manifest.json` + `adguard.py::doc_thong_ke` (chỉ top miền, top máy). | C: tóm tắt theo máy (tên miền nổi bật + số lượt) — đổi quyết NV278 theo mức riêng tư ở mục 6. |
| W4 | **Không có phát hiện xâm nhập, không cách ly, không cắt kết nối đang mở.** Không có khái niệm «mức chắc», «danh sách bảo vệ», «cách ly». | Grep toàn `modules/mikrotik-routeros`, `modules/adguard`, `app/` = 0 kết quả cho cách ly / mức chắc. | D: đủ 3 bước báo → cách ly → cắt + gác an toàn bắt buộc. |
| W5 | **Không có chuyển quyền khi AdGuard lỗi** (đã nêu ở NV299 D6) — nhắc lại vì khu Mạng nhà phải hiện đúng trạng thái suy giảm, không thể hiện «mọi thứ bình thường» khi AdGuard chết. | Như NV299 D6. | E: chế độ suy giảm có tên, hiện đúng dòng (lấy nguyên NV299 §4). |
| W6 | **Không đặt được luật firewall qua chat/Studio.** Không có mẫu luật nào, không nhãn nguồn/hạn/hoàn tác. | Không có module mạng ghi nào; kênh chat/Studio không có công cụ mạng. | F: 5 mẫu luật tham số kiểm chặt qua cùng lõi phê duyệt. |
| W7 | **Định danh vẫn theo MAC** (sổ thiết bị từ DHCP lease), giống c2a — vỡ với máy đổi MAC liên tục (hiện như máy lạ, tràn tin duyệt). | `modules/mikrotik-routeros/module.py` (sổ máy theo MAC). | E: thứ tự định danh bền ClientID → WireGuard → SSID/VLAN → chỉ máy MAC cố định mới duyệt-theo-MAC. |
| W8 | **Chưa có trang «Mạng nhà» theo ý định.** Chỉ có các tab module rời (Thiết bị · Chờ duyệt · VPN · DNS & chặn), không có trang tổng hợp A/B/C/D. | `web/Nha.dc.html` (chip module, không trang ý định). | Trang một trang «Mạng nhà» (mục 3 + mẫu HTML). |

**Không sai ở vị trí các chip hiện có (ghi rõ để khỏi sửa lùi):** Nhà ▾ → Mạng với chip
Thiết bị · Chờ duyệt · VPN của MikroTik và chip «DNS & chặn» của AdGuard (thứ tự 40) đã đúng
form demo — **giữ nguyên, chỉ thêm trang «Mạng nhà» đứng cạnh**, không thay các chip đó.

---

## 3. Trang «Mạng nhà» — nguyên tắc + vị trí + trạng thái chưa kết nối

**Nguyên tắc 1 của NV290 (áp cho mọi loại sau này, mạng là ví dụ đầu tiên):**
- Trang xây theo **ý định của chủ máy**, không theo từng module. Chỉ hiện mục cần cho ý định;
  chi tiết kỹ thuật gấp lại dưới «Nâng cao».
- Mọi hành động GHI (ngắt mạng, cấp mạng, cách ly, đặt luật…) là `nguy_hiem` theo cấu trúc,
  đi qua phê duyệt của lõi (cổng xác nhận một lần NV298). Không có đường tắt cho kênh nào.
- Không hiện id kỹ thuật ở dòng chính: dòng chính chỉ có tên dễ đọc + trạng thái + nút hành
  động. Địa chỉ MAC/IP đầy đủ nằm trong «Nâng cao» của từng máy (gấp lại mặc định) — đúng
  QUY-TAC §4 (không id kỹ thuật hiện cho người dùng) và §1a (chi tiết kỹ thuật gấp lại).
- Tiếng Việt có dấu đầy đủ, mọi ô có mô tả «điền gì, lấy ở đâu» bằng tiếng thường (QUY-TAC §5).
- Không thêm thư viện ngoài (CSS/JS thuần, CSP chặn nguồn ngoài) — như NV299 §6.

**Vị trí (Q6):** Nhà ▾ → Mạng, trang «Mạng nhà» đứng cạnh các chip module hiện có. Trang này
là trang **tổng hợp theo ý định** (đọc từ module MikroTik + module AdGuard, ghi qua khả năng
ghi của module MikroTik); các tab module giữ nguyên nội dung chuyên sâu của chúng.

**Trạng thái chưa kết nối (NV290 §1c + Q1):** chưa có kết nối thì trang chỉ hiện một dòng
«Chưa kết nối — thêm ở Cài đặt của module MikroTik» (và dòng tương tự cho AdGuard nếu thiếu)
kèm liên kết đúng dòng cần thêm; có kết nối rồi mới hiện chức năng. **Điểm vênh Q1:** NV290
§1b nói thông tin kết nối nằm ở Khu Tài khoản; QUY-TAC §1 (mới hơn, 03/11) nói kết nối RA
ngoài nằm trong chip «Cài đặt» của chính module, Khu Tài khoản chỉ cho tài khoản AI. Đặc tả
này **làm theo QUY-TAC** (mới hơn) và ghi Q1 để chủ máy chốt — không tự hoà giải.
- Thông tin kết nối (địa chỉ IP LAN của router/AdGuard, tài khoản, mật khẩu/khoá) nằm trong
  chip «Cài đặt» của chính module đó, **luôn ẩn** sau khi cài; bấm mới mở sửa; bí mật chỉ ghi
  đè («••••• đã lưu»), **không bao giờ trả lại qua API** — đúng NV290 §1b về mặt «xem để đổi»,
  chỉ khác vị trí đặt (chip Cài đặt thay vì Khu Tài khoản).
- **Không** nằm ở «Bảo mật & người dùng» (QUY-TAC quy tắc 2 chỉ dành cho khoá DO web2api CẤP
  cho thứ gọi VÀO; đây là thông tin để web2api gọi RA router/AdGuard).
- **Lần đầu nối tới router (NV295 đã chốt):** tự ghim chứng chỉ — đo vân tay của chứng chỉ
  thiết bị trình ra, lưu vào cấu hình riêng của module, nối lại bằng đường ghim (kiểm vân tay
  TRƯỚC khi gửi mật khẩu). Người dùng không tạo, lấy, dán hay bấm xác nhận gì. Nút «Tin chứng
  chỉ này» chỉ còn cho trường hợp chứng chỉ ĐỔI. (Ghi chú: cách diễn đạt «hiện nút Tin chứng
  chỉ này» ở QUY-TAC §5 ra trước quyết 19:30 của NV295; hành vi chốt là tự ghim lần đầu +
  nút chỉ khi đổi.)
- **Đường điều khiển bắt buộc IP LAN (luật 19:30):** địa chỉ router/AdGuard trong cấu hình
  phải là IP LAN (cổng IP LAN của NV295 từ chối tên miền và IP WAN ngay, không phân giải
  DNS). Đường điều khiển web2api→router đi bằng địa chỉ IP, không qua tên miền/DNS, để chính
  sự cố DNS không làm mất khả năng cách ly — nhất quán với NV290 §E.6.

**Trạng thái suy giảm (nối từ NV299):** khi AdGuard lỗi, đầu trang hiện đúng một dòng có tên:
«AdGuard lỗi — đang dùng DNS dự phòng: lọc quảng cáo và theo dõi “dùng gì” tạm tắt; cách
ly/ngắt mạng/phát hiện xâm nhập qua router vẫn hoạt động». Không hiện «mọi thứ bình thường»
khi AdGuard chết; luật dựa vào AdGuard tạm ngừng, không coi «không có dữ liệu» là tấn công.

---

## 4. A — NGẮT / NỐI INTERNET CẢ NHÀ: MỘT NÚT + HẸN GIỜ TỰ NỐI LẠI

**Ý định (nguyên văn NV290):** «ngắt internet» — một nút, có hẹn giờ tự nối lại, luôn chừa
đường vào web2api, Home Assistant và máy quản trị, hiện rõ «đang ngắt, còn N phút».

### 4.1. Hành vi

| Trạng thái | Giao diện hiện | Nút chính |
|---|---|---|
| Đang có mạng | «Internet cả nhà đang mở» | **«Ngắt internet cả nhà»** + ô chọn hẹn giờ (mặc định 30 phút, chỉnh được: 15 / 30 / 60 / 120 phút — không có «vô hạn») |
| Đang ngắt | «Đang ngắt internet cả nhà, còn N phút — tự nối lại lúc HH:MM» | **«Nối lại ngay»** (nối trước hẹn) |

- Bấm «Ngắt» → hộp xác nhận một lần (NV298) nêu rõ: «Ngắt internet cả nhà trong N phút.
  Máy quản trị, web2api và Home Assistant vẫn nối được. Hết hẹn tự nối lại.» → mới áp.
- **Không có chế độ ngắt vô hạn.** Mọi lần ngắt đều có hẹn; hết hẹn mà web2api chết thì
  router vẫn tự nối lại (xem 4.2 — hẹn nằm ở router, không phụ thuộc web2api sống).
- Nút này chỉ chặn **internet (ra WAN)**, không chặn LAN nội bộ: máy trong nhà vẫn nói chuyện
  với nhau, vẫn tới web2api/HA, vẫn xem camera nội bộ. Ngắt LAN nội bộ là việc khác, không
  nằm trong nút này.
- Công tắc ghi `w2a-chan` đang TẮT → nút ngắt khoá (hiện «Bật “Cho phép ghi lên router” ở
  Cài đặt của module MikroTik để dùng»), chỉ còn xem trạng thái.

### 4.2. Cơ chế thi hành (đề xuất — chốt ở lượt triển khai sau khi đo RouterOS thật)

Học mẫu «luật drop đứng đầu forward» của c2a, nhưng cho cả nhà thay vì một máy:

1. **Danh sách quản trị `w2a-quan-tri`** (tiền tố `w2a-` để không lẫn luật gõ tay): chứa địa
   chỉ IP của máy chạy web2api, máy chạy Home Assistant, và máy quản trị của chủ máy (chủ máy
   khai trong Cài đặt của module MikroTik; mặc định đã có IP của web2api/HA do module tự đo
   từ kết nối hiện tại). Danh sách này **không bao giờ bị ngắt**.
2. **Một luật filter duy nhất, comment `w2a: ngắt internet cả nhà`**, đứng ở đầu chuỗi
   `forward` (trước cả «Established» để cắt cả phiên đang chạy, như c2a): điều kiện
   `src-address-list=!w2a-quan-tri` + `out-interface-list=WAN` (hoặc giao diện WAN đã cấu
   hình rõ ràng — không đoán WAN bằng «nhận nhiều dữ liệu nhất» như c2a), hành động `drop`.
   Luật chỉ tồn tại trong lúc ngắt; nối lại = gỡ luật.
3. **Hẹn giờ nằm ở router:** cùng lúc tạo luật, tạo một mục scheduler của RouterOS tới giờ
   hẹn sẽ tự gỡ luật (và ghi log). Hết hẹn mà web2api còn sống thì web2api gỡ trước và xoá
   scheduler; web2api chết thì scheduler của router vẫn gỡ đúng giờ. **Không dùng hẹn phía
   web2api làm cơ chế duy nhất** — vì ngắt mạng có thể làm chính web2api mất đường báo.
4. **Kiểm kết nối sau khi áp (chống tự khoá):** sau khi áp luật, module kiểm lại ngay: (a)
   vẫn tới được router qua API; (b) một địa chỉ trong `w2a-quan-tri` vẫn ra được WAN (kiểm
   bằng chính router, ví dụ ping từ router tới một địa chỉ ngoài qua giao diện WAN — nếu
   router không ra được thì luật đã sai, tự gỡ luật và báo lỗi ngay, không để nhà mất mạng
   oan). Nếu kiểm này không làm được trên RouterOS thật thì lượt triển khai phải ghi rõ
   phương án thay thế — không bỏ qua bước kiểm.
5. **Rủi ro tự khoá và biện pháp (ghi rõ theo NV290 §3):**
   - Quên máy quản trị trong `w2a-quan-tri` → chủ máy tự khoá mình ngoài: biện pháp = hẹn
     giờ tự gỡ (mục 3) + luật chừa quản trị (mục 1) + kiểm sau khi áp (mục 4).
   - IP máy quản trị đổi (DHCP) → máy quản trị rớt khỏi danh sách: biện pháp = máy quản trị
     nên đặt IP tĩnh (ghi rõ trong mô tả ô nhập); module cảnh báo khi IP của máy quản trị
     trong danh sách không còn thấy trong lease.
   - Hai lần ngắt chồng nhau: lần ngắt sau thay hẹn của lần trước (không tạo luật thứ hai);
     giao diện luôn hiện đúng một hẹn đang chạy.

### 4.3. Trạng thái

| Trường | Ý nghĩa |
|---|---|
| `dang_ngat` (bool) | Có luật `w2a: ngắt internet cả nhà` đang bật không |
| `con_phut` / `noi_lai_luc` | Hẹn còn lại + giờ tự nối lại |
| `quan_tri` (danh sách IP) | Máy được chừa (hiện tên dễ đọc, IP nằm trong «Nâng cao») |

---

## 5. B — THIẾT BỊ MỚI PHẢI ĐƯỢC DUYỆT MỚI RA INTERNET

**Ý định (nguyên văn NV290):** «thiết bị mới thì hỏi tôi có đồng ý không rồi mới cấp
internet» — máy chưa có trong sổ (MAC lạ) bị giữ lại, không ra internet; chủ máy nhận câu
hỏi qua kênh thông báo đã có của nhà và bấm Đồng ý / Từ chối; chỉ khi Đồng ý mới cấp.
**Tái dùng cơ chế «Chờ duyệt» của trang Thiết bị (`tuyen.phe_duyet`), đừng dựng hàng đợi
duyệt thứ hai.**

### 5.1. Máy nào là «máy mới»

Máy mới = thiết bị **chưa có trong sổ thiết bị mạng** (mục 9) và **chưa được duyệt**, thấy
được qua một trong hai nguồn (học c2a `_may_dang_doi`):
- Lease DHCP **động** (khi DHCP chưa khoá), hoặc
- Mục trong **bảng host của bridge** mà không có lease nào (khi DHCP đã khoá
  `static-only`, máy lạ không nhận được IP nên chỉ còn dấu ở đây — đúng trường hợp AP làm
  cầu của nhà này).

**Máy đổi MAC không tràn tin «máy lạ»:** máy đã có định danh bền (ClientID AdGuard, peer
WireGuard, hoặc SSID/VLAN riêng — mục 8) thì lần xoay MAC mới **không** tạo mục chờ duyệt
mới: hệ thống gộp theo định danh bền; tên máy chủ (hostname) và dấu vân tay DHCP chỉ là tín
hiệu mềm để gợi ý «có thể là máy X», **không thay duyệt**. Chỉ máy **không có định danh bền
nào** và có MAC chưa từng thấy mới vào hàng chờ duyệt. Điện thoại bật «MAC ngẫu nhiên» mà
chưa có ClientID thì vẫn hiện như máy lạ — giao diện ghi rõ cách tắt MAC ngẫu nhiên cho
wifi nhà (bẫy c2a đã gặp), và chủ máy duyệt một lần thì các MAC sau của cùng máy (cùng
hostname/dấu vân tay) được gợi ý gộp, không hỏi lại từng MAC.

### 5.2. Giữ máy mới lại bằng gì (cơ chế thi hành, đề xuất)

Theo đúng NV290 §3: dùng **danh sách địa chỉ «được phép ra internet» + luật firewall chặn
máy ngoài danh sách**:
1. **Danh sách `w2a-duoc-phep`** (tiền tố `w2a-`): chứa IP của mọi máy đã duyệt (và của danh
   sách quản trị `w2a-quan-tri`). Máy duyệt xong thì IP của nó được thêm vào đây.
2. **Một luật filter, comment `w2a: chỉ máy được duyệt mới ra internet`**, đứng trong chuỗi
   `forward`, sau luật cách ly (mục 7) và sau luật ngắt cả nhà (mục 4): điều kiện
   `src-address-list=!w2a-duoc-phep` + `out-interface-list=WAN`, hành động `drop`. Máy
   ngoài danh sách không ra được WAN nhưng vẫn ở trong LAN (nhận IP, thấy trang duyệt,
   tới được web2api để chủ máy duyệt — không bị «mất mạng hoàn toàn không hiểu vì sao»).
3. **Khoá DHCP `static-only` chỉ áp cho máy MAC cố định** (camera/NAS/IoT — mục 8): khi bật,
   DHCP chỉ phát IP cho lease tĩnh. Bật khoá DHCP phải theo mẫu c2a: **lần đầu chỉ liệt kê
   máy sẽ mất mạng** (lease động hiện có), phải xác nhận mới làm — vì điện thoại MAC ngẫu
   nhiên chưa duyệt sẽ mất mạng khi hết hạn lease. Khoá DHCP là lớp bổ sung, **không thay**
   luật chặn ở mục 2 (máy tự đặt IP tay vẫn bị luật chặn giữ lại).
4. Thứ tự luật trong chuỗi `forward` (từ trên xuống — luật trên thắng trước):
   1. `w2a: chặn máy cách ly` (mục 7 — cắt cả phiên đang chạy)
   2. `w2a: ngắt internet cả nhà` (mục 4 — chỉ tồn tại lúc ngắt)
   3. `w2a: chỉ máy được duyệt mới ra internet` (mục này)
   4. Các luật của chủ máy gõ tay (không đụng tới — luật w2a không bao giờ sửa/xoá luật
      không mang comment `w2a:`).

### 5.3. Luồng duyệt — tái dùng `tuyen.phe_duyet` (không hàng đợi thứ hai)

Cơ chế lõi đã có (web2api main `8ed35ab`): `GET /api/phe-duyet` (danh sách hàng chờ qua
`thiet_bi_mod.lay_hang_cho_hien_thi`), `POST /api/phe-duyet/{pd_id}/duyet` (kèm step-up +
vân tay thiết bị `bam` nếu có), `POST /api/phe-duyet/{pd_id}/tu-choi`. Trang «Mạng nhà»
chỉ **hiển thị hàng chờ này + gọi đúng 3 đường đó**; không tạo bảng hàng chờ riêng, không
tạo đường duyệt riêng. (Ghi chú QUY-TAC §4: trang «Thiết bị» chung bị bỏ, nhưng **cơ chế
hàng đợi phê duyệt vẫn giữ** — trang Mạng nhà là nơi duy nhất hiện hàng chờ duyệt mạng.)

```
Máy mới thấy được (lease động / bridge host)
  → vào hàng chờ phê duyệt (lõi, tuyen.phe_duyet)
  → báo qua kênh thông báo đã có của nhà:
    «Máy lạ <tên / nhà sản xuất / lúc nào> xin vào mạng, cho phép?»
  → chủ máy bấm Đồng ý / Từ chối (trang Mạng nhà, hoặc kênh đã có)
  → Đồng ý: tạo/cố định lease tĩnh + đặt tên + gán nhóm + thêm IP vào
     w2a-duoc-phep + ghi sổ (người duyệt, lúc duyệt, hạn nếu có)
     → máy ra được internet
  → Từ chối: ghi sổ trạng thái «bị chặn» + (tuỳ chọn) kick: lease
     block-access + chặn IP 1 ngày theo mẫu c2a kick
     → máy không ra được internet
  → Hết hạn (nếu duyệt có hạn): gỡ lease tĩnh + chặn IP thêm 1 ngày
     (đúng lease-time, máy còn nhớ IP cũ tới lúc xin lại) + gỡ hàng đợi
     tốc độ — theo mẫu c2a het_han; máy muốn vào lại phải duyệt lại
```

**Sơ đồ trạng thái duyệt máy mới:**

```
            thấy lần đầu
  (chưa có trong sổ) ─────────────► CHO_DUYET ─── Đồng ý ───► DUOC_PHEP
      ▲                              │   ▲                    │  │
      │                              │   │                    │  │ hết hạn
      │                           Từ chối│                    │  ▼
      │                              ▼   │                 BI_CHAN (tạm, có hẹn)
      │                           BI_CHAN ─── chủ máy mở lại ──┘
      │                              │
      └──── máy quay lại sau khi ────┘
             bị từ chối (vẫn là máy
             mới cho tới khi duyệt)
```

- Trạng thái trong sổ (mục 9): `cho_duyet` / `duoc_phep` / `bi_chan` (kèm lý do + hẹn mở
  lại nếu có). Máy `bi_chan` hết hẹn tự về `cho_duyet` (hỏi lại), không tự thành
  `duoc_phep`.
- Máy đã duyệt mà đổi MAC nhưng có định danh bền → giữ `duoc_phep`, cập nhật MAC quan sát
  được vào danh sách MAC của mục sổ (không hỏi lại).
- Máy đã duyệt mà đổi nhóm (ví dụ khách → người nhà) → đổi hàng đợi tốc độ + chính sách
  AdGuard theo nhóm mới; ghi log đổi nhóm.

### 5.4. Câu hỏi duyệt — nội dung tin báo

«Máy lạ **<tên / nhà sản xuất / lúc nào>** xin vào mạng, cho phép?» — kèm 2 nút Đồng ý /
Từ chối. Tên lấy từ hostname/DHCP comment (nếu có), nhà sản xuất suy từ tiền tố MAC (OUI —
chỉ để hiển thị gợi ý, không dùng làm căn cứ duyệt), lúc nào là lần thấy đầu tiên. Tin báo
không chứa MAC/IP ở dòng chính (nằm trong «Nâng cao» của mục chờ duyệt).

---

## 6. C — AI VỪA DÙNG MẠNG VÀ DÙNG GÌ

**Ý định (nguyên văn NV290):** «thiết bị nào vừa sử dụng mạng, sử dụng gì» — danh sách thiết
bị hoạt động gần đây (tên dễ đọc, lúc nào, tốc độ) và dưới mỗi máy một dòng tóm tắt «dùng
gì» (vài nhóm dịch vụ / tên miền nổi bật gần nhất). Nguồn: MikroTik (máy + tốc độ, đã có từ
NV279) và AdGuard (truy vấn theo từng máy).

### 6.1. Đổi quyết định NV278 — mức riêng tư chốt cho C

NV278 quyết «không trả nhật ký truy vấn» (vì riêng tư). Khả năng C **cần** truy vấn theo
từng máy nên đặc tả này **đổi quyết đó theo mức riêng tư sau** (chủ máy chốt ở Q3):
- Chỉ lấy **TÓM TẮT theo máy**: tên miền nổi bật (top N tên miền gần nhất của máy đó) + số
  lượt truy vấn + số lượt bị chặn. **Không lưu toàn văn nhật ký** (không lưu từng truy vấn
  kèm giờ giấc đầy đủ, không lưu nội dung).
- Giữ tóm tắt **30 ngày** (hằng số đề xuất — Q3). Quá hạn tự xoá.
- Chủ máy **bật/tắt từng máy**: máy nào tắt thì không lấy tóm tắt của máy đó (chỉ còn tốc
  độ + trạng thái từ MikroTik, không có dòng «dùng gì»).
- Tóm tắt «dùng gì» chỉ hiện trong trang Mạng nhà cho chủ máy đã xác thực; không xuất ra
  kênh chat, không đưa vào tin báo, không dùng làm căn cứ tự cách ly một mình (xem mục 7 —
  tín hiệu DNS chỉ là một trong nhiều tín hiệu cấu trúc).

### 6.2. Phân loại «dùng gì» theo cấu trúc — không danh sách từ khoá, không bảng tên dịch vụ tự dựng

Theo ranh giới NV290 §4: **không thêm danh sách từ khoá**, không tự dựng bảng «tên miền →
tên dịch vụ». Cách phân loại duy nhất được phép:
- **Hiện tên miền nổi bật** (vd: top tên miền của máy trong 24 giờ qua) — người đọc tự hiểu.
- **Nhóm theo danh sách do AdGuard / bộ lọc của chính nó cung cấp** (nếu AdGuard trả về
  nhóm cho một tên miền thì hiện nhóm đó; không thì chỉ hiện tên miền).
- Không suy ra «máy đang xem YouTube / chơi game» từ tên miền bằng bảng tự dựng. Nếu chủ
  máy muốn chặn «ứng dụng theo tên» thì đó là chính sách AdGuard (NV299 §3, chip Máy khách),
  không phải suy luận của trang Mạng nhà.

### 6.3. Nguồn dữ liệu + hiển thị

| Cột hiển thị | Nguồn | Ghi chú |
|---|---|---|
| Tên dễ đọc | Sổ thiết bị mạng (mục 9) | Ưu tiên tên chủ máy đặt > hostname DHCP > nhà sản xuất (OUI) > «Máy chưa đặt tên» |
| Lúc nào (lần thấy cuối / đang hoạt động) | MikroTik lease + bridge host + tốc độ | «Đang hoạt động» = có lưu lượng gần nhất trong vòng quét cuối |
| Tốc độ (lên/xuống hiện tại) | MikroTik (đã có từ NV279) | Chưa đo được thì hiện «—», không số giả |
| Dòng «dùng gì» | AdGuard tóm tắt theo máy (mục 6.1) | Dạng: «gần nhất: <tên miền 1> (N lượt), <tên miền 2> (N lượt) · bị chặn M lượt» |
| Trạng thái duyệt | Sổ thiết bị mạng | Chờ duyệt / Được phép / Bị chặn / Cách ly (dải D) |

- Khi AdGuard lỗi: dòng «dùng gì» tạm tắt toàn trang (theo chế độ suy giảm mục 3), không
  hiện dữ liệu cũ như dữ liệu mới — nếu hiện dữ liệu cũ phải ghi rõ «dữ liệu lúc HH:MM,
  AdGuard đang lỗi nên chưa cập nhật».
- Thứ tự sắp xếp mặc định: máy đang hoạt động trước (theo lưu lượng gần nhất), rồi tới máy
  không hoạt động theo lần thấy cuối.

---

## 7. D — PHÁT HIỆN XÂM NHẬP → BÁO NGAY → CÁCH LY → CẮT ĐƯỜNG ĐANG XÂM NHẬP

**Ý định (NV290, chủ máy 02/11 21:00):** «nếu có dấu hiệu tấn công mạng nhà thì báo ngay, và
ngắt kết nối tránh bị hack như Synology và Imou đang rầm rộ»; «cách ly, ngắt kết nối đường
truyền đang xâm nhập». **c2a chưa có gì ở đây** — toàn bộ mục này là thiết kế mới.

### 7.1. Thang xử lý theo mức chắc chắn (dựa trên CẤU TRÚC hành vi, không danh sách tên/từ khoá)

| Mức | Nghĩa | Hành động | Ai quyết |
|---|---|---|---|
| **Thấp — «nghi»** | Một dấu hiệu đơn lẻ, chưa đủ kết luận | **Chỉ báo ngay** (không cách ly, không cắt). Tin kèm bằng chứng ngắn + nút «Khôi phục» không cần thiết ở mức này (chưa làm gì) + nút «Cách ly ngay» để chủ máy tự quyết. | Hệ thống báo; chủ máy quyết có cách ly không |
| **Cao — «chắc»** | Nhiều dấu hiệu cấu trúc cùng trỏ vào một máy / một đường, hoặc một dấu hiệu đủ mạnh (mục 7.3) | **Báo ngay + cách ly máy + cắt đường đang xâm nhập** (mục 7.2), trong cùng một lượt xử lý. | Hệ thống tự làm nếu chủ máy bật tự cách ly cho nhóm đó (mục 7.5); nếu tắt thì chỉ báo + nút «Cách ly ngay» |

- **Báo ngay, không dồn/giãn nhịp:** khác với cảnh báo thiết bị hỏng của c2a (dồn/giãn nhịp
  để khỏi spam), tấn công báo **tức thì** từng sự kiện. Chống spam bằng cách khác: cùng một
  máy + cùng một dấu hiệu trong một cửa sổ ngắn thì gộp thành một tin có đếm («đã thấy N lần
  từ HH:MM»), không gửi N tin rời — nhưng tin đầu tiên vẫn đi ngay, không chờ đủ N.
- Mọi tin báo kèm **bằng chứng ngắn** (dạng: «từ 14 IP công cộng lạ tới cổng quản trị của NAS
  trong 10 phút» — số liệu thật từ nguồn ở mục 7.3, không suy đoán) + nút «Khôi phục» (khi
  đã cách ly) + nút «Cách ly ngay» (khi mới báo).
- **Khôi phục một chạm:** một nút «Khôi phục» trên tin báo và trên trang Mạng nhà: gỡ máy
  khỏi danh sách cách ly + mở lại kết nối + ghi log khôi phục (ai khôi phục, lúc nào). Khôi
  phục không xoá hồ sơ sự kiện (để điều tra lại được).

### 7.2. Ba bước khi ở mức cao

**Bước 1 — Báo ngay:** qua kênh thông báo đã có của nhà + dải cảnh báo đầu trang Mạng nhà.
Nội dung: máy nào, mức nào, dấu hiệu nào (bằng chứng ngắn), đã làm gì (cách ly + cắt),
nút «Khôi phục».

**Bước 2 — Cách ly máy bị nghi:** đưa máy vào danh sách `w2a-cach-ly` trên router với luật
filter comment `w2a: chặn máy cách ly` đứng **đầu chuỗi forward** (trước cả luật ngắt cả nhà
và luật duyệt — thứ tự ở mục 5.2):
- Chặn máy ra internet **và** chặn máy sang các máy khác trong nhà (cả hai chiều khởi tạo từ
  máy bị cách ly).
- **Chỉ chừa:** DNS nội bộ (để máy còn phân giải tên khi điều tra) và **đường quản trị**:
  máy trong danh sách quản trị `w2a-quan-tri` vẫn khởi tạo tới máy bị cách ly được (để
  web2api/HA đọc luồng nội bộ của camera bị cách ly, để chủ máy điều tra). Chiều ngược lại
  (máy bị cách ly khởi tạo ra ngoài) vẫn chặn.
- Cách ly là **tạm thời có hẹn mặc định** (đề xuất: 24 giờ, sau đó tự mở lại + báo «đã tự mở
  lại sau 24 giờ, kiểm tra lại trước khi tin máy này» — chủ máy có thể nối dài hoặc mở sớm
  bằng «Khôi phục»). Hẹn này khác hẹn của chặn máy thường (mục 5) vì nó gắn với sự kiện
  xâm nhập, không phải duyệt.
- Mỗi lần cách ly ghi nhật ký: lý do + bằng chứng + ai/what đã kích (tự động hay chủ máy
  bấm) + hẹn mở lại.

**Bước 3 — Cắt đường đang xâm nhập:**
- Xoá các kết nối đang mở của cặp nguồn–đích đó trong bảng theo dõi kết nối của router
  (`/ip/firewall/connection/remove` theo cặp nguồn–đích) — để phiên tấn công đang chạy đứt
  ngay, không đợi hết timeout.
- Chặn tạm địa chỉ nguồn bên ngoài: thêm IP nguồn vào danh sách `w2a-chan-nguon` với
  `timeout` (đề xuất: 1 ngày — theo mẫu chặn có hẹn của c2a; hết hẹn tự mở, tránh chặn
  nhầm vĩnh viễn một IP dùng chung).
- Nếu đường vào là cổng đã mở (chuyển cổng / ánh xạ UPnP / NAT-PMP): **vô hiệu ánh xạ ấy**
  (disable mục NAT/UPnP tương ứng, không xoá hẳn để còn dấu điều tra) và **báo rõ cái nào**
  («đã tắt ánh xạ cổng X trỏ vào NAS — cổng này do UPnP tạo lúc HH:MM»). Ánh xạ do chủ máy
  tạo tay trước đó thì chỉ báo + đề nghị tắt, không tự tắt (trừ khi chủ máy bật chế độ tự xử
  lý — xem ca NAS ở mục 7.4).

### 7.3. Dấu hiệu cấu trúc — mỗi dấu hiệu nêu rõ nguồn dữ liệu trên RouterOS

**Ngưỡng phải ĐO trên mạng thật 24–72 giờ rồi mới đặt, không đoán.** Bảng dưới nêu tham số
cần đo + nguồn dữ liệu; giá trị số chốt sau khi đo (mục 11). «Đường cơ sở của chính máy»
nghĩa là hồ sơ hành vi bình thường của đúng máy đó trong 24–72 giờ đo (đích thường gặp,
mức dữ liệu thường, máy trong nhà thường nói chuyện, tên miền thường hỏi) — không phải
ngưỡng chung cho cả nhà.

| # | Dấu hiệu cấu trúc | Nguồn dữ liệu (RouterOS / AdGuard) | Lên mức cao khi nào (cấu trúc, chưa phải số) |
|---|---|---|---|
| S1 | Kết nối TỚI từ internet vào máy trong nhà mà mình không mở | Bảng NAT (`/ip/firewall/nat/print`) + bảng UPnP (`/ip/upnp/...` hoặc mục NAT do UPnP tạo) + bảng theo dõi kết nối (`/ip/firewall/connection/print`): có kết nối vào từ IP công cộng tới máy trong nhà mà không có ánh xạ nào do chủ máy tạo | Ánh xạ UPnP/NAT-PMP **mới xuất hiện** trỏ vào máy nhóm IoT/camera/NAS, hoặc máy nhóm đó nhận kết nối vào từ nhiều IP công cộng lạ (không phải một IP quen) |
| S2 | Một nguồn thử nhiều cổng hoặc nhiều máy trong thời gian ngắn (quét cổng) | Bảng theo dõi kết nối: đếm cổng đích khác nhau / máy đích khác nhau theo từng IP nguồn trong một cửa sổ | Một IP nguồn chạm tới nhiều cổng/máy vượt đường cơ sở của mạng (tham số: cửa sổ + số cổng/máy — đo rồi chốt) |
| S3 | Nhiều kết nối ngắn lặp lại tới cùng một cổng đăng nhập của một máy (dò mật khẩu) | Bảng theo dõi kết nối (kết nối ngắn, lặp lại, cùng cổng đích) + nhật ký đăng nhập của máy đích nếu có (nhật ký RouterOS `/log` cho chính router) | Chuỗi kết nối ngắn lặp lại tới cùng cổng đăng nhập vượt đường cơ sở — **đây chính là cách botnet tấn công NAS/camera dùng mật khẩu yếu** |
| S4 | Máy IoT/camera/NAS đổi hành vi so với đường cơ sở của CHÍNH nó | Bảng theo dõi kết nối (đích mới, lượng dữ liệu gửi đi) + AdGuard (tên miền chưa từng thấy, lượng truy vấn) | Một máy đồng thời: kết nối ra nhiều đích mới + tăng vọt dữ liệu gửi đi + nói chuyện với nhiều máy trong nhà mà trước đó không bao giờ + hỏi tên miền chưa từng thấy (càng nhiều dấu hiệu cùng lúc càng chắc) |
| S5 | Đăng nhập thất bại lặp lại vào chính router | Nhật ký RouterOS (`/log` — sự kiện đăng nhập thất bại) | Chuỗi thất bại lặp lại trong một cửa sổ (tham số đo rồi chốt); thất bại từ IP công cộng thì nặng hơn từ LAN |
| S6 | Máy trong nhà bị dùng làm bàn đạp (tấn công ngang) | Bảng theo dõi kết nối: máy trong nhà khởi tạo tới nhiều máy trong nhà khác mà trước đó không bao giờ (đặc biệt tới cổng quản trị/chia sẻ tệp của NAS) | Máy nhóm IoT/camera/NAS bắt đầu quét/chạm tới cổng quản trị của nhiều máy khác — kết hợp với S4 thì lên mức cao ngay |

- **Không dùng danh sách từ khoá, tên miền độc hại, hay tên sản phẩm làm căn cứ.** Tên miền
  chỉ dùng ở dạng «chưa từng thấy đối với chính máy này» (S4) — tức là so với đường cơ sở
  của máy, không phải so với danh sách đen.
- **Mất nguồn dữ liệu không phải là tấn công:** AdGuard lỗi → luật S4-phần-DNS tạm ngừng
  (mục 3); router không đọc được bảng kết nối → luật S1/S2/S3/S6 tạm ngừng + báo «đang mù
  dữ liệu theo dõi kết nối», không tự cách ly vì «không thấy gì».
- **Đo đường cơ sở như thế nào (mục 11):** chạy chế độ chỉ-quan-sát 24–72 giờ trên mạng thật
  (ghi lại, không chặn, không cách ly): đếm cho từng máy — số đích mới/giờ, dữ liệu gửi
  đi/giờ, số máy trong nhà nói chuyện/giờ, số tên miền chưa từng thấy/giờ; số cổng/máy một IP
  nguồn chạm tới trong các cửa sổ 1/5/15 phút; số lần đăng nhập router thất bại/giờ. Từ đó
  đặt ngưỡng sao cho mạng bình thường không chạm ngưỡng, rồi mới bật tự cách ly.

### 7.4. Hai ca thực làm chuẩn (nguồn: bài đăng cộng đồng 02/11, CHƯA tự xác minh)

**Nguyên tắc chung cho cả hai ca:** thiết kế dựa trên **hành vi chung** (dò mật khẩu, cổng mở
ra internet, máy đổi hành vi), **không dựa tên sản phẩm, không dựa tên tệp/đuôi tệp, không
đoán chi tiết khai thác**. Chủ máy sẽ gửi liên kết/CVE nếu có; cho tới lúc đó, các chi tiết
CVE/tên tệp dưới đây chỉ là «bài đăng nói vậy», không phải căn cứ thiết kế.

**Ca 1 — NAS Synology/Xpenology bị mã hoá tống tiền (bài đăng nói: dấu hiệu tệp đòi tiền
«read-me3.txt» ở mọi thư mục và đuôi «.L0CK3D»; điều kiện bị khai thác theo bài đăng: NAS mở
cổng đăng nhập web DSM ra internet và DSM cũ — từ 7.2.1-69057 Update 5 trở xuống,
CVE-2024-10441; khuyến cáo trong bài: ngắt mạng NAS ngay rồi cập nhật DSM).**

**Chứng minh hệ thống bắt được ca này ở tầng mạng (router KHÔNG thấy tệp bị mã hoá):**
- **Tệp/đuôi tệp không đóng vai trò nào.** Router chỉ thấy gói tin, không thấy tên tệp trong
  lưu lượng đã mã hoá — nên «read-me3.txt» / «.L0CK3D» không bao giờ là tín hiệu phát hiện.
  Ai thiết kế «quét tên tệp» cho ca này là sai tầng.
- **Quy tắc nền cho nhóm NAS (Q8): KHÔNG có kết nối từ internet vào NAS.** Cổng quản trị
  của NAS chỉ truy cập được từ LAN và từ WireGuard. Đây là quy tắc nền được giám sát liên
  tục, không phải gợi ý.
- **Dấu hiệu điều kiện bị khai thác → báo NGAY:** phát hiện ánh xạ chuyển cổng/UPnP trỏ vào
  NAS (đặc biệt trỏ vào cổng quản trị DSM) ⇒ báo ngay «cổng quản trị NAS đang mở ra
  internet — đây là điều kiện bị khai thác», đề nghị tắt; nếu chủ máy bật chế độ tự xử lý
  thì tự tắt ánh xạ đó. Đây là bước chặn TRƯỚC khi tấn công xảy ra.
- **Dấu hiệu đang bị tấn công → cách ly NAS ngay:** kết nối vào từ nhiều IP công cộng lạ
  tới cổng quản trị NAS (S1+S3) và/hoặc sau đó NAS đổi hành vi (S4+S6: đọc/ghi hàng loạt
  tới các máy khác trong nhà qua chia sẻ tệp, tăng vọt dữ liệu ra ngoài) ⇒ **cách ly NAS ngay
  (đúng khuyến cáo «ngắt mạng NAS»)**, kèm lời nhắc: cập nhật DSM, kiểm tra sao lưu có bị
  mã hoá không, và nhắc rõ «vì NAS chứa sao lưu nên mất sao lưu tạm thời nhẹ hơn mất dữ
  liệu» để chủ máy quyết khôi phục.
- **Không tự cập nhật DSM từ web2api** (ngoài phạm vi, rủi ro cao); chỉ nhắc.
- Vì NAS thường chứa sao lưu: với NAS, mức thấp **không** tự cách ly (Q5 — tắt mặc định tới
  khi chủ máy xác nhận); mức cao thì cách ly vì mất sao lưu tạm thời nhẹ hơn mất dữ liệu.

**Ca 2 — Camera Imou IPC-G42P bị chiếm khi đang BẬT P2P (bài đăng nói: tin tặc tạo tài khoản
quản trị mà chủ không xoá được, chỉ đặt lại cứng mới sạch).**
- **Bài học cho thiết kế nhóm camera:** camera/IoT **không được ra internet mặc định** —
  nhóm camera chỉ cho tới đích đã duyệt (danh sách đích cho phép theo camera, đặt trong
  chính sách nhóm), **không UPnP** (mọi ánh xạ UPnP/NAT-PMP do chính camera tạo đều là dấu
  hiệu S1 → báo ngay, và tự tắt nếu bật tự xử lý).
- **Phát hiện ánh xạ do chính camera tạo:** bảng NAT/UPnP ghi rõ máy nội bộ tạo ánh xạ (địa
  chỉ nguồn nội bộ = IP camera) — đối chiếu với sổ thiết bị: ánh xạ có nguồn nội bộ thuộc
  nhóm camera ⇒ dấu hiệu.
- **Khi camera bị cách ly thì web2api chỉ còn đọc luồng nội bộ:** theo định nghĩa cách ly ở
  mục 7.2 (đường quản trị chừa lại), máy quản trị/web2api/HA vẫn khởi tạo tới camera để đọc
  luồng nội bộ; camera không khởi tạo ra ngoài được. Xem từ xa phải qua **WireGuard**, không
  qua P2P/đám mây của hãng.
- **Nhóm camera mẫu (theo NV290):** nhà chủ máy CÓ camera họ Dahua/Imou (một camera cổng
  37777 trong LAN) — đặc tả lấy đây làm nhóm camera mẫu khi đo đường cơ sở (mục 11): camera
  này bình thường chỉ nói chuyện với ai (đầu ghi / HA / app nội bộ), có bao giờ tự tạo ánh
  xạ UPnP không, có bao giờ ra internet trực tiếp không.

### 7.5. Gác an toàn — BẮT BUỘC (không có thì không được bật tự cách ly)

| Gác | Nội dung |
|---|---|
| Danh sách bảo vệ | **Không bao giờ bị tự cách ly:** router, máy chạy web2api, Home Assistant, máy quản trị của chủ máy. Máy trong danh sách này mà có dấu hiệu thì chỉ báo (kèm bằng chứng), không tự cách ly, không tự cắt — vì cách ly nhầm máy quản trị là tự khoá mình ngoài. |
| Nhóm được tự cách ly | **Chỉ nhóm IoT/camera/NAS** (và chỉ khi chủ máy bật tự cách ly cho nhóm đó). Máy nhóm chủ nhà/người nhà/khách không bao giờ tự cách ly — chỉ báo + nút «Cách ly ngay» cho chủ máy bấm. |
| Mức mới được tự cách ly | **Chỉ mức cao.** Mức thấp chỉ báo, không tự làm gì. |
| Khôi phục một chạm | Nút «Khôi phục» trên tin báo và trên trang Mạng nhà: gỡ cách ly + mở lại + ghi log (ai, lúc nào). |
| Trần số máy cách ly/giờ | **Đề xuất 3 máy/giờ (Q4).** Chạm trần → dừng tự cách ly, chỉ báo, chờ chủ máy. Chống lỗi dây chuyền cách ly cả nhà khi một luật sai hoặc một đợt quét quét trúng nhiều máy cùng lúc. |
| Công tắc tự cách ly | Chủ máy bật/tắt được chế độ tự cách ly (theo từng nhóm). Mặc định đề xuất (Q5): **bật báo cho tất cả; tự cách ly bật cho camera/IoT, tắt cho NAS** tới khi chủ máy xác nhận. |
| Nhật ký đầy đủ | Mỗi lần cách ly/cắt/khôi phục ghi: lý do + bằng chứng + ai/what kích + hẹn mở lại. Không có log thì không được coi là đã xử lý. |
| Không tự cập nhật firmware | web2api không tự cập nhật DSM/firmware camera/NAS; chỉ nhắc chủ máy cập nhật. |

---

## 8. E — PHÂN VAI MIKROTIK / ADGUARD + ĐỊNH DANH BỀN + DỰ PHÒNG

### 8.1. Bảng phân vai (nhất quán với NV299 §3 — đặc tả này không viết lại NV299)

| Việc | Đặt ở | Lý do |
|---|---|---|
| Ngắt/nối internet cả nhà, cách ly máy, cắt kết nối đang mở, chặn nguồn ngoài, tắt ánh xạ cổng/UPnP | MikroTik | Cưỡng chế tầng 3–4, chạy được cả khi AdGuard chết |
| Bật/tắt từng peer WireGuard, giới hạn dải địa chỉ cho phép của peer | MikroTik | Peer định danh bằng KHOÁ CÔNG KHAI, không phụ thuộc MAC |
| Phát hiện quét cổng, dò mật khẩu, kết nối vào từ internet, máy tăng vọt dữ liệu gửi đi | MikroTik (theo dõi kết nối) | Thấy mọi giao thức, không chỉ DNS |
| Ép mọi máy dùng DNS của AdGuard (chuyển hướng cổng 53, chặn DoT/DoH ra ngoài) | MikroTik | Chống máy tự đổi DNS để né lọc/giám sát |
| Chính sách theo từng máy/nhóm (chặn quảng cáo, tên miền xấu, kiểm soát con trẻ, giờ giấc), «máy này vừa truy cập tên miền gì» | AdGuard | Nhận dạng ở tầng DNS, nhìn được tên miền |
| Phát hiện bất thường DNS (tên miền chưa từng thấy, lượng truy vấn tăng vọt) | AdGuard | Tín hiệu sớm của máy bị chiếm |

**Nguyên tắc thắng:** lệnh của MikroTik THẮNG. Máy bị MikroTik chặn/cách ly thì AdGuard không
mở lại được. Ngược lại, AdGuard tắt/mở lọc không làm thay đổi lệnh chặn của MikroTik.
AdGuard KHÔNG chặn được lưu lượng đi thẳng bằng IP nên không được là chỗ duy nhất cho ngắt
mạng/cách ly.

### 8.2. Định danh bền khi MAC đổi liên tục (điểm mấu chốt)

MAC **không** dùng làm định danh cho điện thoại/máy cá nhân. Thứ tự định danh bền hơn
(áp theo đúng thứ tự này; cái trên có thì dùng cái trên, không rơi xuống MAC):

1. **ClientID của AdGuard qua DoH/DoT/DoQ** — mỗi máy một ClientID, sống sót qua đổi MAC và
   đổi IP. Máy đổi MAC nhưng giữ ClientID thì vẫn là cùng một máy trong sổ và trong chính
   sách AdGuard.
2. **Peer WireGuard** — khoá công khai, IP cố định trong dải VPN. Máy đi qua VPN thì định
   danh bằng peer, không bằng MAC.
3. **Tách mạng theo mức tin cậy (SSID/VLAN riêng cho nhà/khách/IoT)** — quyền theo MẠNG chứ
   không theo MAC. Máy vào SSID/VLAN IoT thì mang quyền của nhóm IoT dù MAC có đổi.
4. **Chỉ máy có MAC CỐ ĐỊNH (camera, NAS, thiết bị IoT — chính là mục tiêu bị tấn công)
   mới dùng duyệt-theo-MAC và khoá DHCP `static-only`** của c2a.

Máy đổi MAC đi qua con đường ClientID/VPN/VLAN thì **không** tràn tin «máy lạ» mỗi lần xoay
MAC (gộp theo tên máy chủ/dấu vân tay DHCP làm tín hiệu mềm, không thay duyệt — mục 5.1).

**Bẫy giữ được nhận dạng ở AdGuard (bắt buộc kiểm — mục 11):** AdGuard chỉ thấy IP nguồn thật
nếu router **KHÔNG nặc danh hoá (masquerade/hairpin)** lưu lượng DNS từ LAN và từ WireGuard
tới nó; nếu bị nặc danh hoá thì mọi máy hiện thành «router» và chính sách theo máy vô dụng.
Đặc tả triển khai phải kiểm điều này và nêu cách cấu hình luật chuyển hướng DNS không làm
mất IP nguồn (luật dst-nat tới AdGuard phải giữ địa chỉ nguồn gốc; kiểm bằng cách: một máy
LAN hỏi DNS qua AdGuard, AdGuard phải thấy IP của máy đó, không phải IP của router). Máy
VPN: đặt DNS trong cấu hình WireGuard trỏ thẳng tới AdGuard để đi vắng nhà vẫn được lọc.

### 8.3. Dự phòng khi AdGuard lỗi (lấy nguyên NV299 §4 — chỉ nêu điểm nối)

- **Chuyển quyền chạy TRÊN ROUTER, không phụ thuộc web2api sống.** web2api chỉ (a) đồng bộ
  trước chính sách «quan trọng» sang danh sách `w2a-chan-*` trên router và (b) hiển thị trạng
  thái + báo. Cơ chế bật/tắt chuyển đổi là netwatch/script/scheduler của RouterOS.
- **Giám sát:** thăm dò định kỳ AdGuard bằng một truy vấn DNS thật + API; lỗi liên tiếp quá
  ngưỡng thì coi là «AdGuard lỗi», báo MỘT lần (và báo khi có lại), không báo dồn. Ngưỡng đề
  xuất của NV299 (chủ máy chốt khi duyệt NV299): 30 giây × 3 lỗi → chuyển, 3 lần đạt → trả.
- **Mạng thông là ưu tiên:** AdGuard lỗi KHÔNG được làm cả nhà mất internet. DNS dự phòng là
  cấu hình do chủ máy chọn trước (AdGuard thứ hai, hoặc DNS của chính router chuyển tiếp tới
  nhà cung cấp DNS mã hoá).
- **Chế độ suy giảm có tên** (hiện ở đầu trang Mạng nhà — mục 3): «AdGuard lỗi — đang dùng
  DNS dự phòng: lọc quảng cáo và theo dõi “dùng gì” tạm tắt; cách ly/ngắt mạng/phát hiện xâm
  nhập qua router vẫn hoạt động».
- **Luật dựa vào dữ liệu AdGuard tạm ngừng khi AdGuard lỗi** (phát hiện bất thường DNS,
  «dùng gì»); nhóm cách ly/IoT giữ nguyên chặn ở router (không thả lỏng vì mất lọc).
- **Đường điều khiển web2api→router đi bằng địa chỉ IP LAN, không qua tên miền/DNS** — để
  chính sự cố DNS không làm mất khả năng cách ly (nhất quán NV290 §E.6 + luật 19:30).

---

## 9. F — ĐẶT LUẬT FIREWALL QUA KÊNH CHAT VÀ STUDIO (ĐÃ CHỐT 02/11 21:06 — DÙNG LUÔN, KHÔNG BÀN LẠI)

**Quyết chốt (NV290 §F + quyết 02/11 21:06):** được phép. Mọi thao tác firewall là khả năng
`nguy_hiem` của module mạng, gọi được từ (1) công cụ MCP/Studio và (2) kênh chat
(Zalo/Telegram) **qua cùng lõi phê duyệt, KHÔNG có đường tắt riêng cho kênh**. Ràng buộc này
không bàn lại ở lượt triển khai.

### 9.1. Ràng buộc bắt buộc

- **Chỉ nhận lệnh từ chủ máy đã xác thực.** Lệnh từ kênh chưa xác thực là chủ máy, hoặc từ
  người khác, thì từ chối ngay (không hỏi lại, không làm một nửa).
- **KHÔNG cho gõ luật RouterOS thô.** Không nhận chuỗi `/ip/firewall/...` tự do, không nhận
  luật viết tay qua chat. Chỉ nhận **mẫu luật có tham số kiểm chặt** (mục 9.2) — tham số sai
  định dạng, sai miền giá trị, hoặc trỏ vào danh sách bảo vệ thì từ chối kèm lý do.
- **Xem trước «sẽ thay đổi gì»:** trước khi áp, hệ thống trả bản xem trước bằng tiếng thường
  («Chặn internet máy Camera sân (nhóm camera) trong 2 giờ — luật này chỉ ảnh hưởng 1 máy,
  không ảnh hưởng máy quản trị») — chủ máy thấy đúng mới xác nhận.
- **Xác nhận khi ảnh hưởng nhiều máy:** mẫu ảnh hưởng 1 máy thì xác nhận một lần (NV298);
  mẫu ảnh hưởng nhiều máy (ngắt cả nhà, chặn cả nhóm) thì xác nhận nêu rõ số máy ảnh hưởng
  + danh sách tên máy (không chỉ đếm số).
- **Nhãn bắt buộc trên mỗi luật tạo qua đường này:** nguồn (chat/Studio + kênh nào), giờ
  tạo, người tạo, **hạn (mặc định CÓ hạn)** — hết hạn luật tự gỡ (dùng `timeout` của
  address-list hoặc scheduler gỡ luật, như c2a). Luật không hạn chỉ tạo được khi chủ máy nói
  rõ «không hạn» và xác nhận thêm một lần nữa.
- **Luôn có «hoàn tác» và nhật ký:** mỗi luật tạo qua đường này có nút «Hoàn tác» (gỡ đúng
  luật đó, không đụng luật khác) + bản ghi nhật ký (ai, lúc nào, mẫu nào, tham số nào, xem
  trước đã hiện gì). Hoàn tác không cần xác nhận lại (vì hoàn tác là gỡ nguy hiểm, không
  phải thêm nguy hiểm) — nhưng vẫn ghi log.
- **Luật nằm trong danh sách CỦA web2api, không đè luật gõ tay:** mọi luật tạo qua đường này
  mang comment/tiền tố `w2a-` (danh sách `w2a-chan-*`, luật comment `w2a: ...`). Hệ thống
  **không bao giờ sửa/xoá** luật không mang dấu `w2a-` — luật chủ máy gõ tay giữ nguyên, dù
  nó mâu thuẫn với luật web2api (khi mâu thuẫn, giao diện báo rõ «luật tay X có thể thắng
  luật này vì đứng trước», không tự sửa luật tay).

### 9.2. Mẫu luật cho giai đoạn 1 (Q7 — đủ 5 mẫu, thêm mẫu phải qua duyệt đặc tả)

| # | Mẫu | Tham số (kiểm chặt) | Thi hành ở router |
|---|---|---|---|
| T1 | Chặn máy | Máy (tên/IP/MAC trong sổ — phải khớp đúng 1 máy, không đoán) + hạn (mặc định 2 giờ) | Thêm IP vào `w2a-chan` (+ `timeout` = hạn); luật drop đầu forward đã có sẵn cắt phiên đang chạy |
| T2 | Mở máy | Máy (khớp đúng 1 máy) | Gỡ IP khỏi `w2a-chan` + gỡ khỏi `w2a-cach-ly` nếu có (mở máy = mở cả hai, báo rõ nếu máy đang bị cách ly) |
| T3 | Cách ly máy | Máy (khớp đúng 1 máy, không thuộc danh sách bảo vệ — thuộc thì từ chối) + hạn (mặc định 24 giờ) | Thêm vào `w2a-cach-ly` + cắt kết nối đang mở của máy (mục 7.2) |
| T4 | Chặn cổng vào | Cổng (số 1–65535) + giao thức (tcp/udp) + máy đích (tùy chọn — bỏ trống = mọi máy) + hạn | Tắt/vô hiệu ánh xạ NAT/UPnP tương ứng nếu có; nếu chưa có ánh xạ thì thêm luật drop cho cổng vào đó (comment `w2a:`) |
| T5 | Đặt hạn giờ | Máy hoặc nhóm + khung giờ (giờ bắt đầu–kết thúc, ngày trong tuần) | Đặt chính sách AdGuard theo giờ (nếu là chặn theo tên) và/hoặc hàng đợi + luật chặn theo giờ ở router (dùng scheduler bật/tắt luật — router giữ, không phụ thuộc web2api sống) |

- Mẫu T1/T3 từ chối ngay nếu máy thuộc danh sách bảo vệ (router, web2api, HA, máy quản trị).
- Mẫu T4 từ chối ngay nếu cổng là cổng quản trị của chính router/web2api/HA (tự khoá).
- Mọi mẫu đều trả xem trước trước khi áp; mọi mẫu đều ghi log + nhãn nguồn/giờ/người tạo/hạn.

---

## 10. MÔ HÌNH DỮ LIỆU — «SỔ THIẾT BỊ MẠNG»

### 10.1. Ai là chủ sổ (Q2 — đề xuất: module MikroTik)

| Đối tượng | Chủ sở hữu | Lý do |
|---|---|---|
| **Sổ thiết bị mạng** (mục 10.2) | **Module MikroTik** | Đây là sổ đã có từ NV279 (đọc lease + host, tự dọn máy vắng) — mở rộng nó, không nhân đôi. Module MikroTik là điểm cưỡng chế duy nhất (luật chặn/cách ly/duyệt đều ở router) nên sổ phải sống cùng kết nối router. NV299 §7.1 đã chốt như vậy cho sổ này. |
| Hàng đợi phê duyệt (chờ duyệt / đã duyệt / từ chối) | **Lõi** (`tuyen.phe_duyet` — đã có) | Hàng đợi là cơ chế chung của lõi (dùng cho cả thiết bị khác, không riêng mạng). Trang Mạng nhà chỉ hiển thị + gọi đường lõi, không giữ hàng chờ riêng. |
| Chính sách AdGuard (theo máy/nhóm/giờ) | Module AdGuard (mới — theo NV299 §7.1) | Chính sách tầng tên miền sống cùng kết nối AdGuard. |
| Tóm tắt «dùng gì» theo máy | Module AdGuard (đọc từ nhật ký AdGuard, tóm tắt rồi mới lưu — mục 6.1) | Nguồn là AdGuard; module AdGuard chịu trách nhiệm tóm tắt + giữ 30 ngày + bật/tắt từng máy. |
| Danh sách chặn đồng bộ trên router (`w2a-chan-*`) | Router giữ, web2api đối chiếu | Bản sao của chính sách «quan trọng» (NV299 §4.5); web2api không phải nguồn sự thật của bản sao này. |
| Trạng thái dự phòng («ai đang giữ quyền») | Router là nguồn sự thật; web2api chỉ soi chiếu để hiển thị | Theo NV299 §7.1. |
| Sổ báo / nhật ký (cách ly, cắt, ngắt, luật chat/Studio, chuyển quyền) | Lõi (ghi log + báo) | Nhật ký là bằng chứng chung, không thuộc riêng module nào; trang Mạng nhà đọc từ lõi để hiện lịch sử. |
| Hồ sơ đường cơ sở hành vi (mục 7.3) | Module MikroTik (tính từ bảng kết nối + AdGuard tóm tắt) | Hồ sơ này gắn với máy trong sổ MikroTik; tính lại định kỳ sau mỗi chu kỳ đo. |

**Liên hệ với sổ thiết bị MikroTik đã có:** sổ hiện có (lease + host + «sổ máy vắng» tự
dọn) trở thành **lớp sighting** (thấy máy ở đâu, lúc nào). Sổ mở rộng thêm **lớp trạng thái**
(duyệt/chặn/cách ly/nhóm/hạn/người duyệt) và **lớp định danh bền** (ClientID, peer WireGuard,
SSID/VLAN, danh sách MAC quan sát được). Một mục sổ = một **thiết bị** (định danh bền), không
phải một MAC: máy đổi MAC vẫn là một mục sổ, MAC chỉ là một thuộc tính trong danh sách MAC
quan sát được. Chỉ máy MAC cố định (camera/NAS/IoT) mới có MAC làm khoá phụ chính.

### 10.2. Mục sổ thiết bị mạng (một mục = một thiết bị)

| Trường | Ý nghĩa | Nguồn |
|---|---|---|
| `id_thiet_bi` | ID nội bộ của mục sổ (không hiện cho người dùng ở dòng chính) | Module tự sinh khi thấy thiết bị lần đầu |
| `ten` | Tên dễ đọc | Chủ máy đặt > hostname DHCP > nhà sản xuất (OUI) > «Máy chưa đặt tên» |
| `nhom` | Nhóm: chủ nhà / người nhà / khách / IoT / camera / NAS | Chủ máy gán lúc duyệt (mặc định: khách cho máy mới chưa rõ — chờ duyệt vẫn là «chưa có nhóm») |
| `trang_thai` | `cho_duyet` / `duoc_phep` / `bi_chan` / `cach_ly` | Sổ + luật router đối chiếu (sổ là ý định, router là thực thi — lệch thì báo) |
| `dinh_danh_ben` | ClientID AdGuard (nếu có) / peer WireGuard (nếu có) / SSID-VLAN (nếu có) | AdGuard / WireGuard / cấu hình mạng — theo thứ tự mục 8.2 |
| `mac_quan_sat` | Danh sách MAC đã thấy của thiết bị này (kèm lần thấy cuối từng MAC) | Lease + bridge host |
| `ip_hien_tai` | IP hiện tại (nằm trong «Nâng cao», không hiện ở dòng chính) | Lease |
| `lan_thay_cuoi` | Lần thấy cuối (lease/host/lưu lượng gần nhất) | MikroTik |
| `duyet_boi` / `duyet_luc` / `het_han` | Người duyệt, lúc duyệt, hạn dùng mạng (nếu có) | Hàng đợi phê duyệt lõi + sổ |
| `tom_tat_dung_gi_bat` | Bật/tắt lấy tóm tắt «dùng gì» cho máy này (mặc định bật; chủ máy tắt được) | Cấu hình trang Mạng nhà |
| `duong_co_so` | Hồ sơ hành vi bình thường của máy (đích thường, mức dữ liệu thường, máy trong nhà thường nói chuyện, tên miền thường hỏi) | Tính từ 24–72 giờ đo (mục 7.3) — chỉ dùng để so lệch, không hiện chi tiết cho người dùng |

### 10.3. Các bản ghi khác

| Bản ghi | Trường chính |
|---|---|
| Sự kiện xâm nhập | Máy, mức (thấp/cao), dấu hiệu (S1–S6), bằng chứng ngắn, lúc phát hiện, hành động đã làm (báo/cách ly/cắt), hẹn mở lại, người khôi phục (nếu có) |
| Luật firewall (chat/Studio + tay qua trang) | Mẫu (T1–T5), tham số, nguồn (chat/Studio/trang), giờ tạo, người tạo, hạn, trạng thái (đang bật / hết hạn / đã hoàn tác) |
| Lần ngắt cả nhà | Lúc ngắt, hẹn nối lại, người ngắt, lý do (nếu nhập), đã nối lại lúc nào (tự động hay bấm tay) |
| Lần chuyển quyền AdGuard | Theo NV299 §4.6 (sự kiện chuyển/trả, thời điểm, lý do, DNS dự phòng đã dùng, đã báo hay chưa) |

---

## 11. HỢP ĐỒNG API (ĐỀ XUẤT — CHỜ DUYỆT, CHƯA TRIỂN KHAI)

Quy ước: hành động module theo tên hiện có (`mikrotik.*`, `adguard.*`); mọi hành động ghi
là `nguy_hiem` qua cổng xác nhận một lần NV298; đường hàng đợi phê duyệt **tái dùng nguyên**
của lõi, không tạo đường mới.

### 11.1. Đọc (trang Mạng nhà tổng hợp từ các nguồn đã có — không thêm đường lõi mới)

| Nguồn đọc | Dùng để hiện |
|---|---|
| Sổ thiết bị mạng (module MikroTik) + tốc độ + trạng thái luật | Khối C (máy + tốc độ + trạng thái) + khối B (máy chờ duyệt) + dải D (máy cách ly) |
| Tóm tắt «dùng gì» (module AdGuard) | Dòng «dùng gì» dưới mỗi máy (mục 6) |
| Hàng đợi phê duyệt (`GET /api/phe-duyet`) | Khối B (danh sách chờ duyệt + nút Đồng ý/Từ chối gọi đường lõi) |
| Trạng thái dự phòng (module AdGuard — theo NV299) | Dòng suy giảm ở đầu trang (mục 3) |
| Nhật ký lõi (sự kiện xâm nhập, ngắt, luật) | Lịch sử ở «Nâng cao» của trang |

### 11.2. Hành động ghi mới (module MikroTik — tất cả `nguy_hiem`, yêu cầu công tắc ghi đang BẬT)

| Hành động | Tham số chính | Mô tả |
|---|---|---|
| `mikrotik.ngat_ca_nha` | `phut` (15/30/60/120, mặc định 30; không có «vô hạn») | Tạo luật `w2a: ngắt internet cả nhà` + scheduler tự gỡ (mục 4) |
| `mikrotik.noi_ca_nha` | — | Gỡ luật ngắt + xoá scheduler (nối trước hẹn) |
| `mikrotik.duyet_may` | `id_thiet_bi`, `ten`, `nhom`, `het_han` (tùy chọn) | Qua đường lõi `/api/phe-duyet/{pd_id}/duyet` (step-up + vân tay nếu có); sau đó module: cố định lease + gán nhóm + thêm IP vào `w2a-duoc-phep` + ghi sổ |
| `mikrotik.tu_choi_may` | `id_thiet_bi`, `kick` (bool, tùy chọn) | Qua đường lõi `/api/phe-duyet/{pd_id}/tu-choi`; sau đó module: ghi sổ `bi_chan` (+ kick nếu chọn: block-access + chặn IP 1 ngày) |
| `mikrotik.cach_ly` | `id_thiet_bi`, `phut` (mặc định 1440 = 24 giờ) | Thêm vào `w2a-cach-ly` + cắt kết nối đang mở của máy (mục 7.2) |
| `mikrotik.khoi_phuc` | `id_thiet_bi` | Gỡ khỏi `w2a-cach-ly` (một chạm — mục 7.1) |
| `mikrotik.cat_ket_noi` | `id_thiet_bi`, `dich` (IP/cổng đích, tùy chọn) | Xoá kết nối đang mở của cặp nguồn–đích trong bảng theo dõi kết nối (mục 7.2 bước 3) |
| `mikrotik.chan_may` / `mikrotik.mo_may` | Như NV299 §7.2 (chặn/mở internet máy) | Giữ nguyên NV299 — trang Mạng nhà dùng chung, không tạo hành động riêng |
| `mikrotik.ep_dns` | Như NV299 §7.2 | Giữ nguyên NV299 |
| Mẫu luật chat/Studio T1–T5 | Theo mục 9.2 | Gọi qua công cụ MCP/Studio hoặc kênh chat → cùng các hành động trên + ghi nhãn nguồn/hạn/hoàn tác |

Hành động AdGuard (`adguard.chinh_sach_dat`, `adguard.chinh_sach_xoa`,
`adguard.dong_bo_router`, `adguard.trang_thai_du_phong`, `adguard.bao_ve`) lấy nguyên NV299
§7.2 — đặc tả này không định nghĩa lại.

### 11.3. Mã lỗi (dùng chung — thêm vào mã lỗi NV299)

| Mã lỗi | Nghĩa |
|---|---|
| `chua_bat_ghi` | Công tắc ghi `w2a-chan` đang tắt (NV299 đã có) |
| `router_khong_toi` | Không tới được router qua IP LAN đã cấu hình |
| `khong_phai_ip_lan` | Địa chỉ cấu hình không phải IP LAN (cổng NV295 từ chối) |
| `thiet_bi_khong_biet` | Không khớp đúng 1 máy trong sổ (không thấy hoặc nhiều máy cùng khớp — trả danh sách để hỏi lại, không đoán, học c2a `tim_may`) |
| `thuoc_danh_sach_bao_ve` | Máy thuộc danh sách bảo vệ — từ chối cách ly/chặn |
| `vuot_tran_cach_ly` | Đã chạm trần số máy cách ly/giờ (Q4) — dừng tự cách ly, chỉ báo |
| `adguard_loi` | AdGuard không tới được (NV299 đã có) |
| `dong_bo_lech` | Danh sách trên router khác bản AdGuard (NV299 đã có) |
| `luat_tay_mau_thuan` | Luật tay của chủ máy đứng trước và có thể thắng luật web2api — chỉ cảnh báo, không tự sửa luật tay |

Mọi lỗi trả nguyên lý do, không nuốt (học c2a `_ket`: «bị từ chối phải nói vì sao»).

---

## 12. QUYỀN ROUTEROS CHO TỪNG KHẢ NĂNG + CÁCH THI HÀNH AN TOÀN

**Lưu ý trung thực về RouterOS:** nhóm quyền có sẵn của RouterOS là thô (không có ACL theo
từng lệnh). Bảng dưới nêu nhóm tối thiểu theo thang nhóm có sẵn + lớp kiểm chặt bằng code
(chỉ cho phép đúng đối tượng mang dấu `w2a-`). Nếu đo trên RouterOS thật thấy không tách
được mịn hơn thì lượt triển khai phải ghi rõ nhóm thực tế dùng + phần nào kiểm tay — đúng
cách NV299 §5 đã dặn. Nhóm `write` là cần thiết cho mọi lệnh ghi dưới đây; bù lại bằng 3 lớp
khác: (a) tài khoản chỉ đăng nhập được từ IP LAN của máy chạy web2api (giới hạn ở
`/ip/service api-ssl` + luật input, học c2a); (b) code chỉ gọi đúng các đường trong bảng, từ
chối mọi lệnh ngoài danh sách cho phép; (c) mọi ghi qua phê duyệt lõi + ghi log.

| Khả năng | Đường RouterOS (đọc / ghi) | Nhóm quyền đề xuất | Cách thi hành an toàn |
|---|---|---|---|
| Đọc sổ máy, tốc độ, trạng thái | `/ip/dhcp-server/lease/print`, `/interface/bridge/host/print`, `/interface/print`, `/system/resource/print` | Tài khoản đọc đã có (nhóm `read`, giữ nguyên NV279) | Chỉ đọc; không đổi gì |
| Ngắt/nối cả nhà (A) | Ghi: `/ip/firewall/filter/add` + `/remove` (luật comment `w2a: ngắt internet cả nhà`), `/system/scheduler/add` + `/remove` (tự gỡ đúng hẹn) | `w2a-chan`: `api` + `read` + `write` | Chỉ tạo đúng 1 luật mang comment `w2a:`; hẹn nằm ở scheduler của router (web2api chết vẫn tự nối lại); kiểm kết nối sau khi áp (mục 4.2); luật chừa `w2a-quan-tri` |
| Duyệt máy mới (B) | Ghi: `/ip/dhcp-server/lease/make-static` + `/set` (comment = tên), `/ip/firewall/address-list/add` (danh sách `w2a-duoc-phep`), `/queue/simple/add` (hàng đợi tên `w2a: ...` nếu nhóm có trần tốc độ) | `w2a-chan` | Chỉ qua đường lõi `/api/phe-duyet` (step-up); không sửa chú thích lease chủ máy đã đặt trừ khi chủ máy đặt tên mới lúc duyệt (học c2a); khoá DHCP `static-only` chỉ sau liệt kê + xác nhận |
| Chặn/mở máy (T1/T2) | Ghi: `/ip/firewall/address-list/add` + `/remove` (danh sách `w2a-chan`, `timeout` cho chặn có hẹn) | `w2a-chan` | Luật drop đầu forward đã có sẵn (đảm bảo 1 lần, không tạo lại nếu đã có — học c2a `_dam_bao_luat_chan`); chặn có hẹn dùng `timeout`, hết hẹn router tự mở |
| Cách ly / khôi phục (D) | Ghi: `/ip/firewall/address-list/add` + `/remove` (danh sách `w2a-cach-ly`), `/ip/firewall/connection/remove` (cắt phiên), `/ip/firewall/filter/add` + `/remove` (luật comment `w2a: chặn máy cách ly`, tạo 1 lần) | `w2a-chan` | Từ chối máy thuộc danh sách bảo vệ; trần cách ly/giờ (Q4); hẹn mở lại 24 giờ mặc định; chiều quản trị chừa lại (mục 7.2) |
| Cắt đường xâm nhập (D bước 3) | Ghi: `/ip/firewall/connection/remove` (theo cặp nguồn–đích), `/ip/firewall/address-list/add` (danh sách `w2a-chan-nguon`, `timeout` 1 ngày), `/ip/firewall/nat/set` (disable ánh xạ — không xoá, để còn dấu) | `w2a-chan` | Chỉ disable ánh xạ do UPnP/NAT-PMP tạo hoặc do chủ máy bật tự xử lý; ánh xạ tay của chủ máy chỉ báo + đề nghị, không tự tắt |
| Ép DNS về AdGuard | Ghi: `/ip/firewall/filter/add` + `/remove` (luật comment `w2a: ép DNS`, `reject` 53 udp/tcp + 853, ngoại trừ IP AdGuard) | `w2a-chan` | Học c2a: `reject` chứ không `drop` (máy lỗi ngay, chuyển DNS dự phòng); cảnh báo trước: thiết bị cài cứng DNS khác có thể mất mạng; DoH chưa chặn được bằng cách này — ghi rõ, không bịa |
| Bật/tắt peer WireGuard | Ghi: `/interface/wireguard/peers/set` (`disabled`), `/interface/wireguard/set` + mangle + NAT đi kèm (chỉ cho đường VPN RA ngoài — học c2a `dat_vpn`: một đường ra một lúc) | `w2a-chan` | Peer vào nhà (truy cập từ xa) thì chỉ tắt/bật peer; đường ra ngoài thì đủ bộ giao diện+mangle+NAT (công tắc HA báo sai — không dùng công tắc HA cho việc này) |
| Giới hạn băng thông theo nhóm | Ghi: `/queue/simple/add` + `/remove` (tên `w2a: ...`, đặt TRƯỚC hàng đợi tĩnh đầu tiên — học c2a `_dat_hang`: hàng đợi đơn khớp theo thứ tự, đứng sau «Global-QoS» là không tới lượt) | `w2a-chan` | Chỉ hàng đợi mang tiền tố `w2a:` được tạo/xoá; nhóm không có trần thì không tạo hàng đợi |
| Đồng bộ bộ chặn dự phòng | Ghi: `/ip/firewall/address-list/add` + `/remove` (danh sách `w2a-chan-*`) | `w2a-chan` | Chỉ đồng bộ chính sách chủ máy đã đánh dấu «quan trọng»; đối chiếu định kỳ, lệch thì báo «Đồng bộ lệch», không tự ghi đè luật tay (NV299 §4.5) |
| Chuyển DNS dự phòng | Ghi: `/ip/dns/set` (chỉ khi chuyển quyền — cơ chế netwatch/script/scheduler của router tự làm, web2api chỉ cấu hình trước) | `w2a-chan` (chỉ lúc cấu hình) | DNS dự phòng do chủ máy chọn trước; chuyển tự động lúc lỗi không hỏi lại từng lần vì đã bật trước bằng công tắc (NV299 §5) |

**Rủi ro tự khoá — tổng hợp (theo NV290 §3, áp cho mọi khả năng ghi):** hẹn giờ tự gỡ luật
(scheduler router / `timeout` address-list); luật chừa quản trị `w2a-quan-tri`; kiểm kết nối
sau khi áp; từ chối máy/cổng trong danh sách bảo vệ; không sửa/xoá luật không mang dấu
`w2a-`; mọi ghi qua phê duyệt lõi + ghi log để lần ngược được.

---

## 13. DANH SÁCH «ĐO THẬT CẦN CHỦ MÁY / ĐIỀU PHỐI LÀM» (ĐẶC TẢ NÀY KHÔNG ĐOÁN)

Muse không vào được LAN nên **không đoán** bất kỳ mục nào dưới đây. Các mục này phải đo
trước khi lượt triển khai chốt hành vi:

| # | Cần đo / xác nhận | Vì sao cần |
|---|---|---|
| M1 | Phiên bản RouterOS thật; có Kid Control không; có netwatch/script/scheduler không | Quyết định cơ chế chuyển quyền (NV299) + hẹn tự gỡ luật (mục 4.2) + Kid Control có dùng được không |
| M2 | Giao diện WAN thật là giao diện nào (tên + danh sách giao diện) | Luật ngắt/duyệt dùng `out-interface-list=WAN` — không đoán WAN như c2a |
| M3 | AdGuard đã bật nhật ký truy vấn chưa; ClientID đã gán cho máy nào (điện thoại đổi MAC đã có ClientID chưa) | Quyết định khả năng C + định danh bền (mục 8.2) có dùng được ngay không |
| M4 | Luật chuyển hướng DNS hiện tại có nặc danh hoá (masquerade/hairpin) lưu lượng DNS tới AdGuard không — kiểm: máy LAN hỏi DNS, AdGuard thấy IP nguồn là IP máy hay IP router | Bẫy mục 8.2: bị nặc danh hoá thì chính sách theo máy vô dụng |
| M5 | Kênh thông báo dùng được để báo duyệt máy mới + báo xâm nhập ngay (kênh nào, tới được chủ máy khi đang ở ngoài không) | Tin duyệt (B) và tin tấn công (D) đều qua kênh này; kênh chết thì cả hai cùng mù |
| M6 | DNS dự phòng nhà chọn (AdGuard thứ hai hay DNS mã hoá nào) | Cấu hình chuyển quyền (NV299) — không tự chọn thay chủ máy |
| M7 | **Đo đường cơ sở 24–72 giờ ở chế độ chỉ-quan-sát** (không chặn, không cách ly): cho từng máy — số đích mới/giờ, dữ liệu gửi đi/giờ, số máy trong nhà nói chuyện/giờ, số tên miền chưa từng thấy/giờ; cho từng IP nguồn — số cổng/máy chạm tới trong cửa sổ 1/5/15 phút; số lần đăng nhập router thất bại/giờ | Đặt mọi ngưỡng mục 7.3 sao cho mạng bình thường không chạm ngưỡng rồi mới bật tự cách ly |
| M8 | Camera mẫu (Dahua/Imou, cổng 37777 trong LAN): bình thường nói chuyện với ai, có bao giờ tự tạo ánh xạ UPnP không, có bao giờ ra internet trực tiếp không | Đường cơ sở riêng cho nhóm camera (mục 7.4 ca 2) |
| M9 | NAS mẫu: cổng quản trị DSM là cổng nào, có ánh xạ nào đang trỏ vào NAS không (chuyển cổng tay / UPnP), DSM đang ở phiên bản nào | Kiểm quy tắc nền «không có kết nối từ internet vào NAS» (Q8) có đang bị vi phạm sẵn không |
| M10 | Nhóm quyền RouterOS thực tế tách được mịn tới đâu cho `w2a-chan` (mục 12) + cách RouterOS phân giải tên miền trong address-list (NV299 §4.5) | Chốt bảng quyền + cách đồng bộ bộ chặn dự phòng |
| M11 | Chặn DoH thực tế chặn được tới đâu trên RouterOS nhà (c2a thừa nhận không chặn được bằng filter) | Không bịa cách chặn DoH trong đặc tả triển khai |
| M12 | Kiểm giao diện thật: Chrome thật + ảnh trước/sau sáng/tối 375 px + 1280 px (máy này không có Chrome) | Vòng QUY-TAC: nộp → điều phối soát/test/đẩy main/dựng lại → kiểm lại bằng test Chrome |

---

## 14. TIÊU CHÍ NGHIỆM THU (KIỂM ĐƯỢC Ở LƯỢT TRIỂN KHAI)

1. Trang «Mạng nhà» hiện đủ A/B/C + dải D khi có sự kiện + dòng suy giảm khi AdGuard lỗi;
   chưa kết nối thì chỉ hiện dòng «Chưa kết nối — thêm ở Cài đặt …» + liên kết đúng dòng.
2. Ngắt cả nhà: bấm → xác nhận → luật + scheduler ở router; hết hẹn tự nối lại kể cả khi
   web2api chết (mô phỏng bằng cách tắt web2api trong lúc ngắt — kiểm trên router thật);
   máy quản trị/web2api/HA vẫn nối được trong lúc ngắt.
3. Máy mới: xuất hiện trong hàng chờ phê duyệt lõi (không hàng chờ thứ hai); Đồng ý → lease
   tĩnh + vào `w2a-duoc-phep` + ra được internet; Từ chối → không ra được; hết hạn → bị chặn
   lại + phải duyệt lại; máy đổi MAC có ClientID không tạo mục chờ mới.
4. «Dùng gì»: tóm tắt theo máy đúng dạng (tên miền nổi bật + số lượt), không toàn văn; quá
   30 ngày tự xoá; tắt từng máy thì mất dòng «dùng gì» của máy đó; AdGuard lỗi thì dòng tạm
   tắt + ghi rõ dữ liệu cũ lúc nào.
5. Xâm nhập (mô phỏng bằng router giả + bảng kết nối giả): S1–S6 kích đúng mức; mức thấp chỉ
   báo; mức cao cách ly + cắt + báo kèm bằng chứng; máy trong danh sách bảo vệ không bao giờ
   tự cách ly; chạm trần 3 máy/giờ thì dừng tự cách ly; nút «Khôi phục» mở lại một chạm.
6. Ca NAS (mô phỏng): ánh xạ trỏ vào NAS → báo ngay + đề nghị tắt; nhiều IP lạ tới cổng quản
   trị NAS + NAS đổi hành vi → cách ly NAS ngay + nhắc cập nhật DSM + kiểm sao lưu; tên tệp
   không xuất hiện trong bất kỳ luật phát hiện nào.
7. Ca camera (mô phỏng): ánh xạ UPnP do camera tạo → báo ngay; camera bị cách ly vẫn đọc
   được luồng nội bộ từ máy quản trị; xem từ xa chỉ qua WireGuard.
8. Luật chat/Studio: 5 mẫu T1–T5 chạy qua cùng lõi phê duyệt; tham số sai thì từ chối kèm lý
   do; xem trước hiện đúng; luật có nhãn nguồn/giờ/người tạo/hạn; «Hoàn tác» gỡ đúng luật đó;
   luật tay không mang dấu `w2a-` không bị đụng tới.
9. Công tắc ghi tắt → mọi nút ghi ẩn/khoá, chỉ còn đọc; bật → nút ghi hiện sau một lần xác
   nhận (NV298). Không có dữ liệu → hiện «Chưa có dữ liệu», không số giả.
10. Test Chrome thật (sáng/tối, 1280 + 375 px) + ảnh trước/sau + bảng «đã áp nguyên tắc nào»
    (Impeccable + Taste) nộp kèm bản triển khai.

---

## 15. NHẤT QUÁN / VÊNH VỚI NV299, QUY-TAC VÀ LUẬT ĐỨNG (GHI RÕ, KHÔNG TỰ HOÀ GIẢI)

| Điểm | Trạng thái | Ghi chú |
|---|---|---|
| Chuyển quyền khi AdGuard lỗi (NV299 §4) | **Nhất quán — lấy nguyên** | Chạy trên router, không phụ thuộc web2api sống; thăm dò DNS thật + API; báo một lần; chế độ suy giảm có tên. Đặc tả này không định nghĩa lại. |
| Tài khoản ghi `w2a-chan` trong cùng module MikroTik, mặc định TẮT (NV299 §5) | **Nhất quán — lấy nguyên, trả lời câu hỏi mở của NV290** | NV290 §3 hỏi «tách khả năng/tài khoản ghi riêng hay một module thứ hai» — chọn khả năng ghi riêng trong cùng module, lý do như NV299: một sổ thiết bị, một kết nối, một hàng chip; module thứ hai nhân đôi sổ và lệch đồng bộ. |
| Thông tin kết nối trong chip «Cài đặt» của module, không ở «Bảo mật & người dùng» (QUY-TAC §1 + NV299 §5) | **Nhất quán** | Áp cho cả MikroTik và AdGuard. |
| Vị trí thông tin kết nối: NV290 §1b nói Khu Tài khoản, QUY-TAC §1 nói chip «Cài đặt» của module | **VÊNH — Q1, chờ chủ máy quyết** | Đặc tả làm theo QUY-TAC (mới hơn, 03/11). Nếu chủ máy muốn Khu Tài khoản thì đổi ở lượt triển khai, không phải lỗi đặc tả. |
| Nút «Tin chứng chỉ này» (QUY-TAC §5) vs tự ghim lần đầu (NV295, quyết 19:30) | **Vênh nhỏ về cách diễn đạt — đã ghi rõ ở mục 3** | Hành vi chốt: lần đầu tự ghim (không bấm gì); nút chỉ khi chứng chỉ đổi. QUY-TAC §5 ra trước quyết NV295. Không phải câu hỏi chặn — chỉ ghi để khỏi hiểu lầm khi đọc QUY-TAC. |
| Đường điều khiển bằng IP LAN, không domain/WAN (luật 19:30) vs NV290 §E.6 (đi bằng IP, không qua DNS) | **Nhất quán** | Cả hai cùng yêu cầu; cổng IP LAN của NV295 cưỡng chế luôn ở cấu hình. |
| «Không trả nhật ký truy vấn» (NV278) vs «dùng gì» theo máy (NV290 C) | **ĐỔI QUYẾT CÓ CHỦ Ý — Q3** | Đổi thành mức riêng tư: chỉ tóm tắt (tên miền nổi bật + số lượt), giữ 30 ngày, không toàn văn, bật/tắt từng máy. Chủ máy chốt N và mức này khi duyệt. |
| Trang «Thiết bị» chung bị bỏ (QUY-TAC §4) vs tái dùng `tuyen.phe_duyet` (NV290 B) | **Nhất quán — phân biệt rõ** | Bỏ là bỏ **trang** chung; giữ là giữ **cơ chế hàng đợi** của lõi. Trang Mạng nhà là nơi duy nhất hiện hàng chờ duyệt mạng. |
| Không id kỹ thuật ở dòng chính (QUY-TAC §4) vs duyệt máy cần MAC/IP | **Nhất quán — gấp lại** | MAC/IP đầy đủ nằm trong «Nâng cao» của từng máy, không ở dòng chính; tin báo duyệt chỉ có tên/nhà sản xuất/lúc nào. |
| Phân loại «dùng gì» | **Nhất quán với ranh giới NV290 §4** | Không danh sách từ khoá, không bảng tên dịch vụ tự dựng; chỉ tên miền nổi bật hoặc nhóm do AdGuard/bộ lọc của chính nó cung cấp. |

---

## 16. GIỚI HẠN CHƯA KIỂM CHỨNG CỦA ĐẶC TẢ NÀY (GHI TRUNG THỰC)

- **Không có router/AdGuard thật để đo:** mọi hành vi RouterOS (nhóm quyền tách được tới đâu,
  cách phân giải tên miền trong address-list, netwatch/scheduler, Kid Control), AdGuard
  (ClientID, nhật ký truy vấn, bẫy nặc danh hoá) và mọi ngưỡng phát hiện đều là «cần đo»
  (mục 13), không phải «đã đo». Đặc tả cố tình để các điểm này ở dạng đề xuất + danh sách đo.
- **Không có Chrome trên máy này:** không chụp được ảnh trước/sau thật; ảnh + kiểm giao diện
  thuộc lượt triển khai (vòng QUY-TAC: nộp → điều phối soát/test/đẩy main/dựng lại → kiểm
  lại bằng test Chrome).
- **Demo chưa chạy đúng nghĩa:** `support.js` vẫn thiếu trên main `82d9ff46` (đã kiểm lại ở
  NV299: thư mục `inbox/tai-lieu/demo/` có 10 trang `.dc.html` + ảnh `ANH-DUNG-*.png` nhưng
  **không có support.js**, dù `DOC-TRUOC.md` nói nó bắt buộc). Mẫu HTML tĩnh kèm theo bám
  mã nguồn `.dc.html` + ảnh + mô tả trong file, không bịa ảnh đối chiếu chưa có.
- **Mẫu giao diện HTML tĩnh:** kèm trong `outbox/nv290-mau-giao-dien.html` — là phác tĩnh
  (CSS thuần, không JS chạy thật, không dữ liệu thật), chưa chạy qua trình duyệt thật.
- **Không đổi module hiện có ở lượt này:** mọi thay đổi code (ghi router, trang Mạng nhà,
  chính sách, chuyển quyền, mẫu luật chat/Studio) thuộc lượt triển khai sau khi duyệt đặc tả.
- **Ca NAS / camera là bài đăng cộng đồng chưa tự xác minh:** đặc tả dựa trên hành vi chung,
  không dựa chi tiết khai thác chưa xác minh; chủ máy gửi liên kết/CVE nếu có thì đặc tả sẽ
  cập nhật.
