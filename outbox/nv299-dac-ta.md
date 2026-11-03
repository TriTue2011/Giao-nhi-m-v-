# NV299 — ĐẶC TẢ: PHÂN TRÁCH NHIỆM MIKROTIK / ADGUARD + TAB ADGUARD + CHUYỂN QUYỀN KHI ADGUARD LỖI

> **Trạng thái:** ĐẶC TẢ — nộp TRƯỚC mã, theo đúng yêu cầu của NV299 (như NV290).
> Mã triển khai chỉ làm sau khi chủ máy duyệt đặc tả này.
> **Base đã đối chiếu:** Giao main `82d9ff46` (file `inbox/NV299.md` + `inbox/QUY-TAC-GIAO-DIEN-W2A.md`
> + `inbox/NV290.md` mục E + `inbox/NV294.md`) · web2api main `8ed35ab` · chatgpt2api `d879b03`.
> **Nguồn thắng:** `inbox/NV299.md`. Mọi chỗ đặc tả này khác file đó đều ghi rõ là «đề xuất thêm».

## 0. Tóm tắt một dòng (hiện trong giao diện, theo NV299 §1)

> **«Ai làm gì»:** MikroTik giữ quyền cao hơn — chặn thật ở tầng mạng, không vòng qua được.
> AdGuard lo tên miền và ứng dụng theo tên. AdGuard lỗi thì MikroTik giữ phần chặn thô,
> lọc quảng cáo tạm tắt, mạng không mất.

Câu trả lời cho câu hỏi của chủ máy («MikroTik hình như không kiểm soát chặn internet hay app nữa
đúng không»): **MikroTik VẪN chặn internet / máy / cổng**; chặn **ỨNG DỤNG theo tên** chuyển cho
AdGuard; khi AdGuard lỗi, MikroTik giữ phần chặn thô (mục 4).

---

## 1. Đã phân tích code chatgpt2api nào (luật 16:11)

Repo công khai `TriTue2011/chatgpt2api`, commit `d879b03`, **chỉ clone đọc, không sửa**.

| File / hàm | Đã đọc | Kết luận đối chiếu |
|---|---|---|
| `services/mang_nha.py` (791 dòng): `chan`, `mo`, `_dam_bao_luat_chan`, `gioi_han`, `_dat_hang`, `khoa_dhcp`, `ep_dns`, `dat_vpn`, `kick`, `bo_kick`, `duyet`, `cho_duyet`, `dat_ten`, `dat_bang_thong`, `danh_sach`, `het_han`, `_quet_router`, `xu_ly` | Toàn bộ hàm chính | c2a **CÓ đầy đủ quyền ghi MikroTik** (xem mục 2, C1). Các mẫu tốt mang sang: luật drop đứng ĐẦU chuỗi forward (cắt cả kết nối đang mở); chặn bằng address-list + `timeout` cho chặn có hẹn; ép DNS bằng `reject` (không phải `drop`) để máy lỗi ngay và chuyển DNS dự phòng; đổi nguy hiểm thì **báo trước hậu quả rồi mới làm** (khoa_dhcp liệt kê máy sẽ mất mạng, ep_dns cảnh báo thiết bị cài cứng DNS) — mẫu này khớp cổng xác nhận một lần NV298 của w2a. |
| `services/routeros.py` (145 dòng): `Phien`, `ket_noi`, `cau_hinh`, `Loi` | Toàn bộ | Client RouterOS API tự viết (socket + mã độ dài nhị phân). w2a đã có client tương đương (`modules/mikrotik-routeros/routeros.py`, socket + ssl, chỉ lệnh đọc) — **không cần port lại client**, chỉ cần mở thêm lệnh ghi có lọc. |
| `api/mqtt.py` dòng ~223–268 (`_router`, `_adguard`) | Đoạn kiểm nối | c2a chỉ có **kiểm nối thử** AdGuard (lấy version + số bộ lọc) khi nhập thông tin, chưa lưu. **Không có module AdGuard** — không thống kê, không chính sách, không chuyển quyền. |
| Grep toàn repo `adguard` (không phân biệt hoa thường) | Toàn repo | Ngoài 3 chỗ trên (mqtt kiểm nối; `mang_nha.py` ghi chú «DNS DHCP = AdGuard»; `ep_dns` lấy IP AdGuard từ config), **không còn gì về AdGuard**. |
| Grep `services/mang_nha.py` với `du_phong`, `fallback`, `suc_khoe`, `health` | Toàn file | **0 kết quả — c2a KHÔNG có cơ chế dự phòng khi AdGuard lỗi.** Chuyển quyền là thiết kế MỚI của w2a, không phải port. |

**Kết luận tổng (kèm luật 16:58):** phần MikroTik-ghi thì c2a đi trước w2a và đáng học mẫu;
phần AdGuard thì c2a gần như trống — «khác c2a» ở đây **không phải sai**, w2a đã hơn c2a
(thống kê + công tắc bảo vệ). Đặc tả này **không port mù** c2a: tài khoản ghi, định danh máy,
và chuyển quyền đều thiết kế lại theo quy tắc w2a (mục 4–6).

---

## 2. LIỆT KÊ ĐIỂM SAI HIỆN TẠI — đọc trước khi xem phương án (phản ánh 16:29)

Đối chiếu trên web2api main `8ed35ab`. «SAI» ở đây nghĩa là: hiện trạng **không đáp ứng
NV299 / demo / hành vi đúng**, không phải chê code cũ viết ẩu — nhiều chỗ là thiết kế cố ý
lúc trước (chỉ đọc vì an toàn) nay đã hết phù hợp với yêu cầu mới.

### 2.1. Sai so với NV299 + demo (giao diện và hành vi người dùng thấy)

| # | Điểm sai hiện tại | Căn cứ đo được | NV299 / demo đòi hỏi |
|---|---|---|---|
| D1 | Tab AdGuard **chưa có hàng chip con**. Manifest `adguard` chỉ khai MỘT chip «DNS & chặn» (thu_tu 40); trong tab không có Tổng quan · Máy khách · Đã chặn · Trạng thái dự phòng · Cài đặt. | `modules/adguard/manifest.json` (chỉ 1 chip `dns`); `web/Nha.dc.html` chỉ render hàng chip khu chung + chip «Cài đặt» cuối (luôn ẩn) — không có khái niệm hàng chip con trong tab. | NV299 §3: hàng chip con đủ 5 mục. |
| D2 | **Không chặn dịch vụ/ứng dụng theo tên** (YouTube, TikTok…) theo máy/nhóm/giờ. Module AdGuard nói thẳng: «Không sửa bộ lọc, không xoá nhật ký», «không trả nguyên nhật ký truy vấn». | `modules/adguard/manifest.json` (mô tả) + `module.py` (chỉ 1 hành động `bao_ve`). | NV299 §1 + §3: chặn theo tên là việc của AdGuard, đặt chính sách theo máy/nhóm + giờ chặn. |
| D3 | **Bấm vào máy khách không xem được tên miền gần nhất.** Chỉ có top máy khách dạng đếm (`top_clients`), không có truy vấn gần nhất theo máy. | `modules/adguard/adguard.py::doc_thong_ke` (chỉ `top_blocked_domains`, `top_clients`). | NV299 §3, chip Máy khách: «bấm vào xem tên miền gần nhất». |
| D4 | **Không có «Trạng thái dự phòng»** — khái niệm «ai đang giữ quyền» không tồn tại ở đâu trong code (grep `du_phong`/`dang_giu` toàn `modules/adguard`, `modules/mikrotik-routeros`, `app/` = 0). | Grep trực tiếp. | NV299 §2 + §3: chip Trạng thái dự phòng + dòng «AdGuard lỗi — MikroTik đang giữ phần chặn, lọc quảng cáo tạm tắt». |
| D5 | **Không có biểu đồ nhỏ theo giờ** — chỉ có tổng truy vấn, tỉ lệ chặn, thời gian xử lý trung bình, top miền, top máy. | `adguard.py::doc_thong_ke` (không có chuỗi theo giờ). | NV299 §3, chip Tổng quan: «biểu đồ nhỏ theo giờ». |
| D6 | **Không có chuyển quyền khi AdGuard lỗi** — không thăm dò định kỳ bằng truy vấn DNS thật, không đổi DNS dự phòng, không bộ chặn dự phòng, không báo một lần, không tự trả. | Toàn bộ `modules/adguard`, `modules/mikrotik-routeros` (chỉ đọc) + grep failover = 0. | NV299 §2 (bắt buộc). |
| D7 | **Không có tài khoản ghi riêng `w2a-chan`** — module MikroTik chỉ có tài khoản đọc (manifest khuyên nhóm «read»), `yeu_cau_goi` rỗng, không có đường ghi nào. | `modules/mikrotik-routeros/manifest.json` + `module.py` (không có nhánh ghi). | NV299 §2 + NV290: hành động ghi qua tài khoản ghi riêng, mặc định tắt. |
| D8 | **Chưa có «Ai làm gì» trong giao diện** — không dòng nào nói MikroTik quyền cao hơn / AdGuard lo tên miền. | Grep giao diện + manifest (không có chuỗi này). | NV299 §1: bảng trách nhiệm hiện bằng một dòng «Ai làm gì». |

**Không sai ở vị trí đặt tab (ghi rõ để khỏi sửa lùi):** manifest `adguard` đã đặt đúng
Nhà ▾ → Mạng (`khu: nha`, `muc: mang`), chip «DNS & chặn» thứ tự 40 — sau Thiết bị (10),
Chờ duyệt (20), VPN (30) của module MikroTik, khớp thứ tự chip demo Mạng (Thiết bị · Chờ duyệt ·
VPN · Cài đặt) cộng thêm chip mới. Chip «Cài đặt» cuối (luôn ẩn) là cơ chế chung của khung
(`web/Nha.dc.html` dòng 16–17), không module nào tự khai. **Vị trí giữ nguyên, chỉ thêm nội
dung trong tab.**

### 2.2. Sai / thiếu so với chatgpt2api (hành vi)

| # | Điểm sai / thiếu | Căn cứ | Đánh giá theo luật 16:58 |
|---|---|---|---|
| C1 | **MikroTik của w2a hoàn toàn chỉ đọc**, trong khi c2a ghi được đủ thứ: chặn/mở máy (`chan`/`mo` bằng address-list `c2a_chan` + luật drop đầu forward), giới hạn băng thông, khoá DHCP `static-only`, ép DNS, VPN, kick, duyệt máy mới có hẹn. | w2a manifest: «CHỈ ĐỌC — không thực hiện hành động nào»; c2a `mang_nha.py` dòng 309–372, 523–595. | Thiếu thật, và là thiếu chặn đường NV299 §2 + NV290 (ngắt/cách ly). Nhưng «chỉ đọc» của w2a là **thiết kế an toàn cố ý lúc NV279** (tài khoản đọc), không phải lỗi viết code — nên phương án KHÔNG copy nguyên tài khoản đặc quyền duy nhất của c2a, mà tách tài khoản ghi riêng `w2a-chan` (mục 6). |
| C2 | **w2a không ép được DNS về AdGuard**, nên máy tự đặt DNS khác (8.8.8.8…) né được lọc và giám sát. c2a đã đo thực tế 90 ngày: không một truy vấn Roblox nào tới AdGuard khi không ép. | w2a: không có `ep_dns`; c2a `ep_dns` dòng 561–595 + ghi chú đo 90 ngày. | Sai thật về mặt kiểm soát. Phương án: ép DNS ở router (reject 53 udp/tcp + 853 DoT, học c2a) + ghi rõ DoH **không chặn được bằng cách này** (c2a tự thừa nhận) — DoH xử lý ở mục 7 «cần đo thật», không bịa cách chặn. |
| C3 | **Định danh máy của w2a vẫn theo MAC** (sổ thiết bị từ DHCP lease), giống c2a — mà c2a tự cảnh báo: điện thoại bật «MAC ngẫu nhiên» hiện như máy lạ, khoá DHCP làm máy chưa duyệt mất mạng. | w2a `module.py` mikrotik (sổ máy theo MAC, «tự động dọn thiết bị đã mất»); c2a `khoa_dhcp` cảnh báo MAC ngẫu nhiên. | Sai nếu copy nguyên c2a. Phương án theo NV290 §E (đã chốt): thứ tự định danh bền — (1) ClientID AdGuard qua DoH/DoT/DoQ, (2) peer WireGuard (khoá công khai), (3) SSID/VLAN theo mức tin cậy, (4) chỉ máy MAC cố định (camera/NAS/IoT) mới duyệt-theo-MAC + khoá DHCP `static-only`. |
| C4 | **c2a không có gì về AdGuard để mà «sai theo»** — không thống kê, không chính sách, không dự phòng. w2a đã có thống kê + công tắc `bao_ve` (nguy_hiem, qua phê duyệt lõi). | Grep toàn c2a (mục 1). | **Không kết luận sai.** Phần AdGuard của đặc tả này là thiết kế mới, không port c2a. Điểm nào của w2a hiện tại tốt hơn c2a thì giữ (thống kê thật, `bao_ve` có hẹn tự bật lại mặc định 5 phút). |
| C5 | c2a dùng **một phiên RouterOS đặc quyền** (`routeros.ket_noi` từ config chung) cho mọi việc ghi; w2a dùng tài khoản đọc riêng. | c2a `routeros.py::ket_noi`; w2a manifest khuyên nhóm «read». | Không copy c2a. Phương án: **hai tài khoản tách bạch** — đọc (đã có, giữ nguyên) + ghi `w2a-chan` (mới, mặc định tắt, quyền hẹp — mục 6). |

### 2.3. Chưa kết luận được — ghi rõ là «cần test chứng minh», không đoán (luật 16:58)

- **Nút `bao_ve` hiển thị hẹn tự bật lại ra sao** trên giao diện thật: code có `thoi_gian_giay`
  nhưng chưa kiểm bằng Chrome thật (máy này không có Chrome) — không khẳng định đúng/sai.
- **Trạng thái trống «Chưa có dữ liệu»**: module đặt trạng thái `None` khi không hợp lệ, nhưng
  giao diện render `None` thành gì thì chưa kiểm — đặc tả yêu cầu rõ «chưa có thì hiện
  «Chưa có dữ liệu», không số giả» (NV299 §3), phần kiểm thuộc vòng Chrome thật sau triển khai.
- **Mọi con số ngưỡng, khoảng thăm dò, cách phân giải tên miền → địa chỉ của RouterOS, cách
  chặn DoH, ClientID đã bật chưa** — thuộc «danh sách đo thật» mục 8, không bịa trong đặc tả.

---

## 3. Bảng trách nhiệm chốt (hiện trong giao diện bằng dòng «Ai làm gì» ở mục 0)

| Việc | Thuộc về | Vì sao ở đó | Lệnh của bên kia có thắng được không |
|---|---|---|---|
| Ngắt/nối internet cả nhà | MikroTik | Tầng mạng, không vòng qua được | — (quyền cao nhất) |
| Cách ly máy, cắt kết nối đang mở | MikroTik | Luật drop đứng đầu forward (học c2a) cắt cả phiên đang chạy | AdGuard **không** mở lại được máy bị MikroTik chặn |
| Chặn theo máy / địa chỉ / cổng | MikroTik | Tầng 3–4, chạy cả khi AdGuard chết | — |
| VPN WireGuard (bật/tắt peer, dải địa chỉ cho phép) | MikroTik | Peer định danh bằng khoá công khai, không phụ thuộc MAC | — |
| Máy lạ phải duyệt mới ra internet | MikroTik + AdGuard phối hợp | MikroTik khoá DHCP `static-only` (chỉ máy MAC cố định); AdGuard nhận dạng máy đổi MAC bằng ClientID (mục 6) | — |
| Giới hạn băng thông | MikroTik | Hàng đợi router | — |
| Ép mọi máy dùng DNS của AdGuard (chuyển hướng 53, chặn DoT 853 ra ngoài) | MikroTik | Chống máy tự đổi DNS để né lọc/giám sát | — |
| Chặn quảng cáo / độc hại | AdGuard | Tầng tên miền | MikroTik không can thiệp nội dung lọc này khi AdGuard khoẻ |
| Chặn dịch vụ/ứng dụng theo tên (YouTube, TikTok…) theo máy/nhóm/giờ | AdGuard | Chỉ tầng DNS mới nhìn được «ứng dụng» theo tên | MikroTik không nhìn được ứng dụng theo tên |
| «Máy nào vừa vào tên miền gì» + thống kê | AdGuard | Nhật ký truy vấn DNS | Khi AdGuard lỗi: tạm tắt, không suy đoán (mục 4) |
| Phát hiện quét cổng, dò mật khẩu, kết nối từ internet, máy tăng vọt dữ liệu | MikroTik (theo dõi kết nối) | Thấy mọi giao thức, không chỉ DNS | — |
| Phát hiện bất thường DNS (tên miền chưa từng thấy, truy vấn tăng vọt) | AdGuard | Tín hiệu sớm của máy bị chiếm | Khi AdGuard lỗi: tạm ngừng luật này, không coi «mất dữ liệu» là tấn công |

**Nguyên tắc thắng:** lệnh của MikroTik THẮNG. Máy bị MikroTik chặn thì AdGuard không mở lại
được. Ngược lại, AdGuard tắt/mở lọc không làm thay đổi lệnh chặn của MikroTik.

---

## 4. Chuyển quyền khi AdGuard lỗi (bắt buộc — cơ chế chạy NGAY trên router)

### 4.1. Nguyên tắc kiến trúc (quyết chốt)

1. **Chuyển quyền chạy trên router, không phụ thuộc web2api đang sống.** web2api chỉ làm hai
   việc: (a) **ĐỒNG BỘ trước** chính sách chặn quan trọng sang router; (b) **HIỂN THỊ** trạng
   thái + báo cho chủ máy. Cái bật/tắt chuyển đổi là cơ chế của router (netwatch/script/
   scheduler của RouterOS) — AdGuard chết mà web2api cũng chết thì nhà vẫn có mạng và vẫn giữ
   chặn. Bất kỳ thiết kế nào đặt «web2api phát hiện rồi ra lệnh chuyển» đều **sai yêu cầu**
   NV299 §2 («không phụ thuộc w2a»).
2. **Mạng thông là ưu tiên.** AdGuard lỗi KHÔNG được làm cả nhà mất internet.
3. **Chỉ đồng bộ bản sao của chính sách chủ máy đã đặt ở AdGuard.** Router không tự thêm luật
   mới, không tự suy ra chính sách.
4. **Báo một lần, tự trả.** Chủ máy nhận đúng một báo khi chuyển, một báo khi trả lại.
   Không báo dồn, không báo lặp mỗi chu kỳ thăm dò.
5. **Luật tự động dựa vào dữ liệu AdGuard tạm ngừng khi AdGuard lỗi.** «Không có dữ liệu»
   không phải là «tấn công». Nhóm cách ly/IoT giữ nguyên chặn ở router (không thả lỏng vì
   mất lọc).

### 4.2. Sơ đồ trạng thái

```
AdGuard KHOẺ ── lỗi liên tiếp quá ngưỡng ──► AdGuard LỖI — MikroTik giữ quyền
     ▲                                             │
     │            AdGuard khoẻ lại                │ (tự động, không cần bấm)
     └──────────── tự trả ◄───────────────────────┘
              (trạng thái trung gian «Đang nghi»:
               lỗi dưới ngưỡng — chỉ ghi log, chưa chuyển, chưa báo)
```

| Trạng thái | Điều kiện vào | Router làm gì | Giao diện hiện gì |
|---|---|---|---|
| Khoẻ | Thăm dò DNS thật + API đều đạt | DNS = AdGuard; bộ chặn dự phòng TẮT (đồng bộ sẵn nhưng không bật) | «AdGuard đang giữ phần chặn tên miền» |
| Đang nghi | Lỗi liên tiếp nhưng chưa quá ngưỡng | Chưa đổi gì | Không báo, chỉ ghi log (tránh báo nhầm do chập chờn) |
| Lỗi — MikroTik giữ quyền | Lỗi liên tiếp quá ngưỡng | (a) Đổi DNS sang dự phòng; (b) Bật bộ chặn dự phòng đã đồng bộ | «AdGuard lỗi — MikroTik đang giữ phần chặn, lọc quảng cáo tạm tắt» + báo MỘT lần |
| Trả lại | Thăm dò đạt lại đủ số lần liên tiếp | DNS trả về AdGuard; tắt bộ chặn dự phòng | Báo một lần «AdGuard đã khoẻ lại» + trạng thái về Khoẻ |

### 4.3. Thăm dò (hai kênh độc lập — phân biệt «DNS chết» với «API chết»)

- **Truy vấn DNS thật** qua AdGuard (tên miền kiểm chứng + tên miền phải chặn — cả hai đều
  phải trả đúng: phân giải được tên thường, chặn được tên trong danh sách chặn). Chỉ thăm dò
  bằng API là chưa đủ: API sống mà DNS chết thì nhà vẫn mất lọc.
- **Gọi API AdGuard** (trạng thái + thống kê) để lấy số liệu hiển thị và phát hiện AdGuard
  «sống nhưng không lọc».
- **Ngưỡng (giá trị ĐỀ XUẤT — chủ máy chốt khi duyệt đặc tả, không phải số đã đo):**
  thăm dò mỗi 30 giây; 3 lỗi liên tiếp → chuyển; 3 lần đạt liên tiếp → trả lại.
  Lý do chọn 3: đủ lọc chập chờn một lần, đủ nhanh để nhà không mất lọc lâu.
  Khoảng thăm dò phải đo lại theo tải của AdGuard thật trước khi chốt (mục 8).

### 4.4. DNS dự phòng (thứ tự ưu tiên)

1. AdGuard thứ hai (nếu nhà có) — giữ được lọc đầy đủ nhất.
2. DNS của chính router chuyển tiếp tới nhà cung cấp DNS mã hoá (DoT/DoH) — có mạng, mất lọc
   quảng cáo/ứng dụng nhưng giữ được chặn thô ở router.
3. Không bao giờ: để trống (mất mạng) hoặc tự ý dùng DNS công cộng không mã hoá mà chủ máy
   không chọn.

DNS dự phòng là **cấu hình do chủ máy chọn trước** (trong chip Cài đặt của tab), không phải
cái router tự đoán lúc lỗi.

### 4.5. Bộ chặn dự phòng trên MikroTik (đồng bộ sẵn, bật khi lỗi)

- web2api đồng bộ **trước** (lúc chủ máy đặt/sửa chính sách) các chính sách AdGuard được đánh
  dấu «quan trọng» sang danh sách địa chỉ của router (mỗi chính sách = một danh sách địa chỉ
  theo tên miền, tên danh sách mang tiền tố `w2a-chan-` để không lẫn luật gõ tay của chủ máy).
- Router chỉ **bật/tắt** danh sách đã đồng bộ khi chuyển quyền — không tự tạo danh sách mới.
- Đồng bộ lại mỗi khi chính sách đổi + định kỳ đối chiếu (phát hiện lệch: danh sách trên
  router khác bản AdGuard → ghi log + hiện «Đồng bộ lệch» ở chip Trạng thái dự phòng, không
  tự ghi đè luật tay).
- **Cần kiểm chứng trên RouterOS thật trước khi chốt (mục 8):** cách RouterOS phân giải tên
  miền trong danh sách địa chỉ (phân giải lúc thêm hay định kỳ tự phân giải lại; TTL; tên miền
  dùng CDN đổi IP nhanh thì chặn có còn đúng không). Nếu RouterOS không phân giải lại đủ
  nhanh, phương án dự phòng phải đổi sang đồng bộ địa chỉ IP đã phân giải kèm chu kỳ làm mới
  — đặc tả này **không chốt** điểm này khi chưa đo.

### 4.6. Báo một lần (sổ báo)

- Mỗi lần chuyển/trả chỉ tạo **một** bản ghi báo (sự kiện + thời điểm + trạng thái mới).
  Các chu kỳ thăm dò sau đó trong cùng trạng thái không tạo báo mới.
- Kênh báo: kênh thông báo đã dùng của web2api (theo cấu hình hiện có của nhà) + dòng trạng
  thái trong tab. Không thêm kênh mới trong lượt này.
- Báo ghi rõ: lúc chuyển, lý do (DNS lỗi / API lỗi / cả hai), DNS dự phòng đang dùng,
  bộ chặn dự phòng nào đang bật.

---

## 5. Tài khoản ghi riêng `w2a-chan` (quyết chốt — trả lời câu hỏi mở của NV290)

**Quyết:** tách thành **khả năng ghi riêng trong cùng module MikroTik** (không lập module thứ
hai), với **tài khoản RouterOS riêng `w2a-chan`**, **mặc định TẮT** cho tới khi chủ máy bật.

- **Vì sao không lập module thứ hai:** một sổ thiết bị, một kết nối, một hàng chip — module
  thứ hai sẽ nhân đôi sổ thiết bị và hàng chip, lệch nhau lúc đồng bộ. Khả năng ghi là thuộc
  tính của cùng một kết nối router.
- **Vì sao không dùng chung tài khoản đọc rồi cấp thêm quyền ghi:** tài khoản đọc hiện tại
  (nhóm «read») có thể đang dùng ở nhiều chỗ; cấp quyền ghi cho nó là mở rộng quyền âm thầm.
  Tài khoản ghi riêng thì tắt là tắt hết đường ghi, bật là rõ trách nhiệm.
- **Quyền hẹp (đề xuất — chốt sau khi kiểm RouterOS thật, mục 8):** chỉ đủ cho các đối tượng
  mà tính năng cần: danh sách địa chỉ firewall (`/ip/firewall/address-list`), MỘT luật filter
  chặn của w2a (nhận diện bằng comment `w2a-chan`, không sửa luật khác), cài đặt DNS
  (`/ip/dns`), và đọc trạng thái để đối chiếu. **Không** có quyền sửa user, DHCP server,
  VPN, queue, hay toàn bộ filter. Nếu RouterOS không tách được mịn tới mức này bằng nhóm
  có sẵn thì đặc tả triển khai phải ghi rõ nhóm thực tế dùng + phần nào phải kiểm tay.
- **Vị trí lưu thông tin kết nối (theo QUY-TAC, không vênh):** tài khoản + mật khẩu `w2a-chan`
  nằm trong chip «Cài đặt» của chính module MikroTik (luôn ẩn, bấm mới sửa, bí mật chỉ ghi
  đè, không trả qua API — quy tắc 1). **Không** nằm ở «Bảo mật & người dùng» (quy tắc 2 chỉ
  dành cho khoá DO web2api CẤP cho thứ gọi VÀO; đây là thông tin để web2api gọi RA router).
- **Cổng phê duyệt:** mọi hành động ghi lên router đi qua cổng xác nhận một lần NV298 và
  rủi ro `nguy_hiem` của lõi (đã có sẵn: `app/cong_cu.py`, hành động `bao_ve` của AdGuard
  đã dùng cơ chế này). Riêng **chuyển quyền tự động lúc AdGuard lỗi** không hỏi lại từng lần
  (vì đã được chủ máy bật trước bằng công tắc «Cho phép chuyển quyền tự động», mặc định
  TẮT cùng tài khoản) — nhưng mỗi lần bật công tắc đó là một lần xác nhận, và mọi lần chuyển
  đều ghi log + báo một lần.
- **Công tắc tổng:** «Cho phép ghi lên router (tài khoản w2a-chan)» — TẮT mặc định. Tắt thì
  mọi nút ghi trong tab Mạng ẩn/khoá, chỉ còn đọc + hiển thị. Bật thì mới hiện các nút ghi
  và mới cho đồng bộ bộ chặn dự phòng.

---

## 6. Tab AdGuard theo form demo (vị trí + nội dung từng chip con)

**Vị trí (không vênh với QUY-TAC):** Nhà ▾ → Mạng, chip «DNS & chặn» (đã có trong manifest,
thứ tự 40 — giữ nguyên). Trong tab, hàng chip con mới:

| Chip con | Nội dung (dữ liệu THẬT, không số giả) | Ghi chú thiết kế |
|---|---|---|
| Tổng quan | Dòng «Ai làm gì» (mục 0) · Công tắc bảo vệ bật/tắt **có hẹn giờ** (tắt kèm thời gian tự bật lại, mặc định 5 phút — đã có ở `bao_ve`) · Tổng truy vấn · Tỉ lệ chặn · Thời gian xử lý trung bình · Biểu đồ nhỏ theo giờ | Chưa có dữ liệu thì hiện «Chưa có dữ liệu», không vẽ biểu đồ giả. Số liệu lấy từ module `adguard` đã cài; biểu đồ theo giờ cần thêm nguồn chuỗi thời gian (mục 7). |
| Máy khách | Top máy (tên dễ đọc, không IP trần nếu đã có tên) · Bấm vào máy → tên miền gần nhất của máy đó · Đặt chính sách theo máy/nhóm: dịch vụ bị chặn, giờ chặn | Tên máy ưu tiên tên đã đặt / ClientID / tên DHCP; IP chỉ hiện khi không có tên. Chính sách theo máy là MỚI (D2/D3). |
| Đã chặn | Top tên miền bị chặn (tên + số lần) | Dữ liệu đã có (`top_blocked_domains`); chỉ cần trình bày theo form demo. |
| Trạng thái dự phòng | Ai đang giữ quyền (AdGuard / MikroTik) · Trạng thái thăm dò (lần kiểm cuối, lỗi liên tiếp) · DNS dự phòng đang dùng (nếu chuyển) · Bộ chặn dự phòng nào đang bật · Lần đồng bộ cuối + cảnh báo «Đồng bộ lệch» nếu có | Đây là chip MỚI hoàn toàn (D4). Khi Khoẻ thì hiện gọn một dòng, không chiếm chỗ. |
| Cài đặt | Kết nối AdGuard (địa chỉ, tài khoản, mật khẩu — ẩn, bấm mới sửa, bí mật chỉ ghi đè) · DNS dự phòng đã chọn · Công tắc «Cho phép chuyển quyền tự động» (mặc định TẮT) · Công tắc «Cho phép ghi lên router (w2a-chan)» (mặc định TẮT) | Theo QUY-TAC quy tắc 1 (kết nối RA ngoài nằm trong chip Cài đặt của module, luôn ẩn) + quy tắc 5 (mọi ô có mô tả tiếng thường: «điền gì, lấy ở đâu»). |

**Định danh máy khi MAC đổi liên tục (theo NV290 §E, bắt buộc trong đặc tả này):**
thứ tự bền vững: (1) ClientID của AdGuard qua DoH/DoT/DoQ (mỗi máy một ClientID, sống sót
qua đổi MAC và đổi IP); (2) peer WireGuard (khoá công khai, IP cố định trong dải VPN);
(3) SSID/VLAN riêng theo mức tin cậy (quyền theo MẠNG chứ không theo MAC);
(4) chỉ máy MAC cố định (camera, NAS, IoT) mới duyệt-theo-MAC + khoá DHCP `static-only`.
Máy đổi MAC đi qua con đường ClientID/VPN/VLAN thì **không** tràn tin «máy lạ» mỗi lần xoay
MAC (gộp theo tên máy chủ/dấu vân tay DHCP làm tín hiệu mềm, không thay duyệt).
**Bẫy phải kiểm (NV290 §E):** AdGuard chỉ thấy IP nguồn thật nếu router KHÔNG nặc danh hoá
(masquerade/hairpin) lưu lượng DNS từ LAN và từ WireGuard tới nó; nếu bị nặc danh hoá thì mọi
máy hiện thành «router» và chính sách theo máy vô dụng. Đặc tả triển khai phải kiểm điều này
và nêu cách cấu hình luật chuyển hướng DNS không làm mất IP nguồn. Máy VPN: đặt DNS trong
cấu hình WireGuard trỏ thẳng tới AdGuard để đi vắng nhà vẫn được lọc.

**Nguyên tắc thiết kế áp cho riêng tab này (NV299 §4 — bảng «đã áp nguyên tắc nào» sẽ nộp
kèm bản triển khai, cùng ảnh trước/sau sáng/tối 1280 + 375 px):**
- Impeccable, mode **Operate** (người dùng hoàn thành việc, không phải bị thuyết phục):
  scanability trước trang trí; nhất quán với khung `web/Nha.dc.html` + `khung.css` sẵn có;
  tinh chỉnh giữ nguyên bản sắc, không thay thế cả thế giới giao diện (refinement, không phải
  redesign); trạng thái trống/lỗi/đang tải phải có thiết kế, không để trắng.
- Taste v2, nhánh **app-screen** (không phải page run): viền lặng, nhãn nhỏ, panel lặp lại là
  bình thường; **cấm** gradient, glow, icon trong ô màu, biểu đồ cầu vồng, số liệu tự bịa;
  sáng–tối tương phản và thứ bậc ngang nhau; kiểm bằng trình duyệt thật ở 375 px và 1280 px
  (inspect.mjs cần Chrome thật — thuộc vòng sau triển khai, không bịa ảnh ở lượt đặc tả).
- QUY-TAC: không id kỹ thuật hiện cho người dùng, không trang «Thiết bị» chung, không
  «Đặt rủi ro», tiếng Việt có dấu đầy đủ, không thêm thư viện ngoài (CSS/JS thuần, CSP chặn
  nguồn ngoài).

---

## 7. Mô hình dữ liệu + hợp đồng API (ĐỀ XUẤT — chờ duyệt, chưa triển khai)

### 7.1. Mô hình dữ liệu

| Bảng / đối tượng | Chủ sở hữu | Trường chính (tiếng Việt trong giao diện, tên kỹ thuật chỉ trong code) |
|---|---|---|
| Sổ thiết bị mạng | Module MikroTik (đã có — giữ nguyên, không nhân đôi) | MAC, tên dễ đọc, trạng thái (chờ duyệt / được phép / bị chặn), lần thấy cuối, ClientID (nếu có), peer WireGuard (nếu có), SSID/VLAN. MAC chỉ là một thuộc tính, không phải khoá định danh duy nhất. |
| Chính sách AdGuard | Module AdGuard (mới) | Phạm vi (máy / nhóm), dịch vụ hoặc tên miền bị chặn, giờ chặn, mức quan trọng (thường / quan trọng → đồng bộ router), ngày tạo/sửa. |
| Danh sách chặn đồng bộ (bản sao trên router) | Router giữ, web2api đối chiếu | Tên danh sách (`w2a-chan-*`), chính sách nguồn, lần đồng bộ cuối, trạng thái (khớp / lệch). Tiền tố `w2a-chan-` để không lẫn luật gõ tay. |
| Trạng thái dự phòng | Router là nguồn sự thật («ai đang giữ quyền»); web2api chỉ soi chiếu để hiển thị | Trạng thái (khoẻ / đang nghi / lỗi-giữ-quyền), lần thăm dò cuối, lỗi liên tiếp, DNS đang dùng, bộ chặn đang bật, lần chuyển/trả cuối. |
| Sổ báo một lần | Lõi (ghi log + báo) | Sự kiện (chuyển / trả), thời điểm, lý do (DNS lỗi / API lỗi / cả hai), DNS dự phòng đã dùng, đã báo hay chưa. |

### 7.2. Hợp đồng API (đề xuất — tên hành động theo quy ước module hiện có)

| Hành động | Thuộc | Rủi ro | Mô tả |
|---|---|---|---|
| `adguard.bao_ve` | AdGuard | nguy_hiem (đã có) | Bật/tắt bảo vệ, tắt kèm hẹn tự bật lại — giữ nguyên. |
| `adguard.chinh_sach_dat` | AdGuard | nguy_hiem | Đặt/sửa chính sách chặn theo máy/nhóm/giờ (MỚI). |
| `adguard.chinh_sach_xoa` | AdGuard | nguy_hiem | Xoá chính sách (MỚI). |
| `adguard.dong_bo_router` | AdGuard | nguy_hiem | Đồng bộ ngay các chính sách «quan trọng» sang router (MỚI; bình thường đồng bộ tự động khi chính sách đổi). |
| `adguard.trang_thai_du_phong` | AdGuard | đọc | Trạng thái «ai đang giữ quyền» + thăm dò + đồng bộ (MỚI). |
| `mikrotik.chan_may` / `mikrotik.mo_may` | MikroTik | nguy_hiem | Chặn/mở internet máy (MỚI; học mẫu address-list + timeout của c2a; luật drop đứng đầu forward). Yêu cầu công tắc ghi đang BẬT. |
| `mikrotik.ep_dns` | MikroTik | nguy_hiem | Ép DNS về AdGuard (reject 53 udp/tcp + 853, học c2a; kèm cảnh báo DoH chưa chặn được) (MỚI). |
| `mikrotik.dns_du_phong` | MikroTik | nguy_hiem | Đặt DNS dự phòng + bật/tắt chuyển quyền tự động (MỚI; chuyển tự động lúc lỗi không hỏi lại từng lần vì đã bật trước — mục 5). |
| `mikrotik.dong_bo_danh_sach` | MikroTik | nguy_hiem | Đối chiếu danh sách `w2a-chan-*` trên router với bản AdGuard (MỚI). |

Mã lỗi dùng chung (đề xuất): `adguard_loi` (AdGuard không tới được), `router_khong_toi`
(router không tới được), `chua_bat_ghi` (công tắc ghi đang tắt), `chua_dat_dns_du_phong`
(chưa chọn DNS dự phòng mà đã bật chuyển tự động), `dong_bo_lech` (router khác bản AdGuard).
Mọi lỗi trả nguyên lý do, không nuốt (học c2a `_ket`: «bị từ chối phải nói vì sao»).

---

## 8. Tiêu chí nghiệm thu + kế hoạch kiểm thật

### 8.1. Nghiệm thu (NV299 §5 — kiểm được ở lượt triển khai)

1. Bảng trách nhiệm hiển thị đúng dòng «Ai làm gì» + bảng đầy đủ trong tab.
2. Mô phỏng AdGuard lỗi (lõi giả, theo NV299 §5): giao diện chuyển trạng thái → dòng
   «AdGuard lỗi — MikroTik đang giữ phần chặn, lọc quảng cáo tạm tắt» → báo đúng MỘT lần →
   AdGuard khoẻ lại → tự trả + báo một lần.
3. Đặt chính sách chặn dịch vụ theo máy/nhóm/giờ → AdGuard nhận đúng; chính sách «quan trọng»
   → đồng bộ sang router đúng danh sách `w2a-chan-*`; đổi chính sách → đồng bộ lại.
4. Tắt công tắc ghi → mọi nút ghi ẩn/khoá, chỉ còn đọc; bật → nút ghi hiện sau một lần xác
   nhận (NV298).
5. Không có dữ liệu → hiện «Chưa có dữ liệu», không số giả; test Chrome thật (sáng/tối,
   1280 + 375 px) + ảnh trước/sau + bảng «đã áp nguyên tắc nào» (Impeccable + Taste).
6. Bộ test đầy đủ cho: chuyển trạng thái, báo một lần, đồng bộ, chặn/mở, ép DNS, quyền hẹp
   của `w2a-chan` (thử lệnh ngoài phạm vi phải bị từ chối).

### 8.2. Kế hoạch kiểm: test được bằng giả lập vs cần router/AdGuard thật

| Kiểm được bằng test giả lập (không cần nhà thật) | Cần router/AdGuard thật (chủ máy / điều phối làm) |
|---|---|
| Sơ đồ trạng thái + báo một lần + tự trả (lõi giả) | Phiên bản RouterOS thật, có Kid Control không, có netwatch/script/scheduler không |
| Đồng bộ danh sách (client giả) + phát hiện lệch | Cách RouterOS phân giải tên miền trong address-list (lúc thêm / định kỳ / TTL / CDN đổi IP) |
| Quyền hẹp: lệnh ngoài phạm vi bị từ chối (client giả) | Nhóm quyền RouterOS thực tế tách được mịn tới đâu cho `w2a-chan` |
| Render tab + chip con + trạng thái trống (test giao diện) | AdGuard đã bật nhật ký truy vấn chưa; ClientID đã đặt cho máy đổi MAC chưa |
| Hợp đồng API + mã lỗi (test đơn vị) | Kiểm bẫy nặc danh hoá: AdGuard có thấy IP nguồn thật không (masquerade/hairpin) |
| — | Chặn DoH thực tế chặn được tới đâu (c2a thừa nhận không chặn được bằng filter) |
| — | Kênh thông báo dùng được để báo một lần; khoảng thăm dò theo tải AdGuard thật |
| — | Test Chrome thật + ảnh trước/sau (máy này không có Chrome) |

### 8.3. Danh sách đo thật cần chủ máy / điều phối làm (đặc tả này KHÔNG đoán)

Phiên bản RouterOS; Kid Control có hay không; AdGuard bật nhật ký truy vấn chưa; ClientID
đã gán cho máy nào; cấu hình masquerade/hairpin của luật chuyển hướng DNS; kênh thông báo
dùng được; DNS dự phòng nhà chọn (AdGuard thứ hai hay DNS mã hoá nào); ngưỡng thăm dò
chốt sau khi đo tải AdGuard.

---

## 9. Giới hạn chưa kiểm chứng của đặc tả này (ghi trung thực)

- **Không có router/AdGuard thật để đo:** mọi hành vi RouterOS (phân giải tên miền trong
  address-list, tách quyền nhóm, netwatch) và AdGuard (ClientID, nhật ký) đều là «cần đo»,
  không phải «đã đo». Đặc tả cố tình để các điểm này ở dạng đề xuất + danh sách đo (mục 8).
- **Không có Chrome trên máy này:** không chụp được ảnh trước/sau thật; ảnh + kiểm giao diện
  thuộc lượt triển khai (vòng QUY-TAC: nộp → điều phối soát/test/đẩy main/dựng lại → kiểm
  lại bằng test Chrome).
- **Demo chưa chạy đúng nghĩa:** `support.js` vẫn thiếu trên main `82d9ff46` (đã kiểm lại:
  thư mục `inbox/tai-lieu/demo/` có 10 trang `.dc.html` + `canvas.json` + ảnh `ANH-DUNG-*.png`
  nhưng **không có support.js**, dù `DOC-TRUOC.md` nói nó bắt buộc — không có thì hiện chữ
  `{{…}}` thô, đó không phải demo). Đặc tả bám theo mã nguồn `.dc.html` + ảnh `ANH-DUNG-*.png`
  + mô tả trong file, và ghi rõ giới hạn này — không bịa ảnh đối chiếu chưa có.
- **Mẫu giao diện HTML tĩnh:** kèm trong `outbox/nv299-mau-giao-dien.html` (theo NV299 §5) —
  là phác tĩnh theo token của `web/Nha.dc.html` + `khung.css`, chưa chạy qua trình duyệt thật.
- **Vị trí hàng đợi:** file NV299 ghi «sau NV297+298», nhưng lượt này làm theo lệnh kéo NV299
  lên (NV297+NV298 chưa rõ vị trí trong danh sách mới). Đặc tả không phụ thuộc vào thứ tự đó.
- **Không đổi module hiện có ở lượt này:** mọi thay đổi code (ghi router, chip con, chính sách,
  chuyển quyền) thuộc lượt triển khai sau khi duyệt đặc tả.
