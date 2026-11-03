# NV295 — TỰ GHIM CHỨNG CHỈ LẦN ĐẦU QUA IP LAN (hướng 19:30) — BÁO CÁO

## KẾT QUẢ

Hướng 19:30 ngày 03/11 thay thế phương án nút «Tin chứng chỉ này» ở lần đầu
nối. Người dùng không phải tạo, lấy, dán hay bấm xác nhận gì ở lần đầu;
lớp bảo mật chống hack là **bắt buộc IP LAN** (tuyệt đối không tên miền,
không IP WAN).

- **Lần đầu nối tới IP LAN gặp chứng chỉ không kiểm được → hệ thống TỰ GHIM:**
  đo vân tay SHA-256 của chứng chỉ thiết bị trình ra, lưu vào cấu hình của
  chính module đó, rồi nối lại bằng đường ghim sẵn có (kiểm vân tay TRƯỚC
  khi gửi mật khẩu). Không hỏi người dùng, không có nút ở lần đầu.
- **Lần sau:** kiểm ghim như cũ — chứng chỉ khớp mới nối; chứng chỉ đổi thì
  DỪNG nối và chỉ lúc đó mới hiện nút «Tin chứng chỉ này» để xác nhận lại
  (nút còn, nhưng chỉ cho trường hợp đổi chứng chỉ — xem §3).
- **Cưỡng chế IP LAN ở cả hai module** (mikrotik-routeros, zte-e2633):
  tên miền bị từ chối NGAY mà không phân giải DNS; IP WAN/CGNAT/loopback/
  link-local/dải đặc biệt bị từ chối; chỉ RFC 1918 + ULA mới được nối.
- **Nộp:** nhánh Giao `muse/nv295` gồm `outbox/nv295.patch` +
  `outbox/nv295-bao-cao.md` (file này), trên nền web2api main `8ed35ab`.

## 1. CƠ CHẾ «TỰ TẠO CHỨNG CHỈ NGẪU NHIÊN» THẬT LÀ GÌ (không bịa)

Người dùng nói «tự tạo chứng chỉ ngẫu nhiên để kết nối lần đầu». Đối chiếu
code TLS hiện có (không có đoạn nào trong repo tự sinh chứng chỉ), cơ chế
triển khai đúng là:

| Câu hỏi | Trả lời đúng theo code |
|---|---|
| Chứng chỉ nào? | Chứng chỉ **do chính thiết bị trình ra** khi bắt tay TLS — với router/bộ phát dùng chứng chỉ tự cấp thì đó là chứng chỉ tự ký do firmware của thiết bị tự sinh (cặp khoá ngẫu nhiên của riêng thiết bị đó). web2api KHÔNG tự tạo ra chứng chỉ nào. |
| Ai «tạo» cái gì? | web2api chỉ «tạo» **mục ghim tin cậy** (trust entry): vân tay SHA-256 đo được từ chứng chỉ đó. Không có bước nào sinh khoá/chứng chỉ mới, không có kênh cài chứng chỉ lên thiết bị (RouterOS API và trang quản trị ZTE đều không có kênh đó trước khi đăng nhập — và đăng nhập lại cần TLS trước, nên «cài chứng chỉ rồi mới nối» là vòng tròn không làm được). |
| Lưu ở đâu? | Trong cấu hình RIÊNG của module đó (`van_tay_tls`, qua `kho.luu_cai_dat` theo `module_id`; từ lượt này có `kieu: "bi_mat"` nên giá trị đầy đủ nằm kho bí mật 0600, GET cấu hình chỉ trả dạng che `…4-ký-tự-cuối`). Không có kho tin chung toàn cục. |
| Dùng cho lần nối nào? | Mọi lần nối SAU của cùng module tới cùng thiết bị: đường ghim sẵn có kiểm vân tay TRƯỚC khi gửi mật khẩu; khác vân tay → dừng, không gửi mật khẩu. |
| Khi nào ghim? | CHỈ ở lúc lưu cấu hình (`cai()`), khi đủ 4 điều kiện: (1) chưa ghim vân tay nào, (2) còn bật kiểm chứng chỉ, (3) lỗi bắt tay ĐÚNG là lỗi xác minh chứng chỉ (`SSLCertVerificationError` trong chuỗi nguyên nhân — lỗi mạng/giao thức khác thì không ghim), (4) đích đã qua cổng IP LAN. Runtime (`nap`/`thuc_the`/`suc_khoe`) KHÔNG bao giờ tự ghim — cấu hình chưa ghim gặp chứng chỉ tự ký ở runtime vẫn hỏng fail-safe như trước (test nv111 giữ nguyên). |

**Giới hạn nói thẳng:** tự ghim lần đầu tin đúng chứng chỉ nhìn thấy ở lần
đầu. Nếu mạng LAN đã bị xâm nhập ĐÚNG lúc nối lần đầu, kẻ tấn công trên
LAN có thể chèn chứng chỉ giả và hệ thống sẽ ghim chứng chỉ giả đó. Đây
chính là mô hình tin cậy mà người dùng đã chốt («bắt buộc IP LAN là đã
bảo mật chống hack») — kẻ ngoài mạng không tới được đích LAN nên không
chèn được; kẻ đã ở trong LAN thì đã qua lớp biên này. Về sau chứng chỉ
đổi (kể cả do tấn công đổi chứng chỉ) thì dừng nối và đòi xác nhận lại
bằng nút — không tự ghim lại lặng lẽ.

**Nếu người dùng thực sự muốn web2api tự SINH một chứng chỉ** (chứ không
phải tự ghim chứng chỉ của thiết bị) thì đó là yêu cầu khác, không làm
được với hai giao thức này — cần chủ máy xác nhận lại ý này (xem §8, câu
hỏi Q2). Patch này triển khai theo cách hiểu có căn cứ trong code như
trên.

## 2. DẢI IP LAN ĐƯỢC PHÉP + ĐIỂM CƯỠNG CHẾ

Hàm lõi mới `app/tu_xa.py::kiem_ip_lan(host)` — danh sách tường minh,
không dùng `is_private` của `ipaddress` (vì nó coi cả CGNAT là private):

| Nhóm | Dải | Kết quả |
|---|---|---|
| LAN IPv4 (RFC 1918) | `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | CHO NỐI |
| LAN IPv6 (ULA) | `fc00::/7` | CHO NỐI |
| Tên miền / tên máy | bất kỳ chuỗi nào không phải IP | TỪ CHỐI, không phân giải DNS (test khóa: `getaddrinfo` mà được gọi là hỏng) |
| IP WAN / công cộng | vd `8.8.8.8`, `1.1.1.1` | TỪ CHỐI (test khóa: `create_connection` mà được gọi là hỏng) |
| CGNAT | `100.64.0.0/10` | TỪ CHỐI — dải dùng chung của nhà mạng, không phải LAN (dù `is_private` nói ngược lại) |
| Loopback | `127.0.0.0/8`, `::1` | TỪ CHỐI ở production; chỉ test mới được phép qua biến `WEB2API_TEST_CHO_PHEP_LOOPBACK=1` (máy chủ giả chạy trên loopback) |
| Link-local | `169.254.0.0/16`, `fe80::/10` | TỪ CHỐI (gồm cả metadata đám mây `169.254.169.254`) |
| Khác | unspecified, multicast, reserved, documentation (`192.0.2.0/24`…), `2001:db8::/32` | TỪ CHỐI |
| IPv6 đặc biệt | IPv4-mapped (`::ffff:192.168.1.1` → bóc ra kiểm như IPv4); 6to4/Teredo nhúng IPv4 (vd `2002:7f00:1::` nhúng `127.0.0.1`) → IPv4 nhúng cũng phải là LAN mới qua | Theo IPv4 nhúng |

Điểm cưỡng chế (cả hai đều chặn TRƯỚC mọi lần nối):

- **Mikrotik** `Module.kiem_dia_chi`: thay nhánh phân giải tên máy bằng
  từ chối ngay; IP thì qua `kiem_ip_lan`. Hàm này còn được `nap()` gọi
  lại, nên cấu hình cũ dạng tên miền/WAN sẽ hỏng lúc nạp lại (xem §8).
- **ZTE** `Module.cai`: kiểm `kiem_ip_lan(hostname)` TRƯỚC `kiem_url_lan`
  (khi URL đã có scheme http(s) + hostname, để giữ nguyên thông báo lỗi
  khuôn dạng cho URL thiếu scheme); `kiem_url_lan` phía dưới vẫn kiểm
  scheme/tài khoản như cũ.

Không đụng cổng SSRF chung `_dia_chi_bi_chan` (module từ xa vẫn cho phép
IP công cộng theo đúng mục đích của nó) và không đụng `kiem_dia_chi`
riêng của module adguard (nó còn phân giải tên máy — thuộc phạm vi NV299,
không đổi ở đây; ghi nhận để khỏi tưởng đã siết hết).

## 3. SỐ PHẬN CỦA NÚT «TIN CHỨNG CHỈ NÀY»

| Trường hợp | Trước 19:30 | Sau 19:30 |
|---|---|---|
| Lần đầu, chứng chỉ tự cấp | Hiện nút, chờ người dùng bấm | **MẤT nút — tự ghim, không hỏi** |
| Chứng chỉ đổi (đã ghim khác) | Hiện nút tin lại | **CÒN nút, giữ nguyên** (đo lại + hiện mặt nạ + vé HMAC; bấm thì đo lại, khớp mặt nạ mới lưu) |
| Tắt kiểm (`kiem_chung_chi_tls=false`) | Không đề nghị | Không đổi (không tự ghim, không nút — người dùng đã chọn bỏ kiểm) |
| Lỗi nối thật (mạng/cổng, lỗi bắt tay không phải lỗi chứng chỉ) | Lỗi thường | Không đổi (không tự ghim — test khóa `_la_loi_xac_minh_chung_chi` chỉ nhận `SSLCertVerificationError`) |

Phần còn lại của nút không đổi: endpoint `POST /api/modules/{id}/tin-chung-chi`
(quyền quản trị), vé HMAC gắn module + đích + hạn 600 giây, khối công khai
chỉ có `ly_do`/`ma_hien_thi`/`thong_bao`/vé (không host/cổng/vân tay đầy
đủ), giao diện nút trong khối kết quả lưu ở cả 4 mẫu trang. Validator
`ghep_de_nghi_tin` đã siết: chỉ `ly_do == "doi"` mới được chuyển tiếp
(`tu_ky` giờ trả None — test khóa).

## 4. VÊNH VỚI NV295.md — GHI RÕ ĐỂ CHỦ MÁY QUYẾT

| # | NV295.md nói | Hướng 19:30 làm | Trạng thái |
|---|---|---|---|
| D1 | Lần đầu tự ký → hiện mã + nút «Tin chứng chỉ này», bấm mới lưu | Lần đầu → tự ghim, không nút, không bấm | **Người dùng đã chốt hướng mới — patch theo hướng mới** |
| D2 | Không yêu cầu IP LAN tuyệt đối (chỉ «đích là địa chỉ LAN đã qua kiểm») | Bắt buộc IP LAN; tên miền/WAN bị từ chối cứng | **Người dùng đã chốt — patch theo hướng mới** |
| D3 | Ô `van_tay_tls` cho người dùng «điền» khi cần | Vẫn giữ ô nâng cao, nhưng từ lượt này là `bi_mat` (chỉ hiện dạng che) theo quy tắc hiển thị 19:26; người dùng thường không bao giờ cần điền (lần đầu tự ghim, đổi thì bấm nút) | Đã làm; chủ máy xem có muốn giữ khả năng dán tay cho trường hợp đặc biệt không (hiện vẫn dán được — ô vẫn nhận giá trị gõ vào) |
| D4 | Mô tả trường nói «bấm nút khi được hỏi» cho lần đầu | Mô tả đã viết lại: lần đầu tự tin, đổi mới bấm nút | Đã làm theo hướng mới |
| D5 | (Không nói) cấu hình cũ tên miền/WAN | Sẽ hỏng lúc lưu lại và lúc nạp lại (do `kiem_dia_chi`/`nap`) | **Cần chủ máy biết — thay đổi phá vỡ tương thích** (xem §8). Không có di trú tự động đổi tên miền → IP trong patch này (đổi tên miền thành IP là việc phải xác nhận tay, không đoán) |

## 5. ĐÃ PHÂN TÍCH CODE CHATGPT2API NÀO (luật 16:11)

Repo công khai `TriTue2011/chatgpt2api`, commit `d879b03`, chỉ clone đọc
(giữ nguyên kết luận từ lượt trước, vì hướng mới không đổi điểm này):

| File / hàm | Kết luận đối chiếu |
|---|---|
| `services/routeros.py::ket_noi` (~dòng 124–135) | c2a **KHÔNG kiểm chứng chỉ chút nào** (`CERT_NONE` không điều kiện). Không có khái niệm vân tay, ghim, tự ghim, hay cổng IP LAN. |
| `api/mqtt.py` ~223–268 (kiểm nối thử) | Chỉ thử tài khoản router/AdGuard rồi báo đạt/không — không xử lý chứng chỉ tự ký. |
| Grep toàn repo `fingerprint`/`sha256` | Không có cơ chế ghim vân tay TLS nào cho RouterOS hay thiết bị LAN. |

**Kết luận:** tự ghim + cổng IP LAN là thiết kế MỚI của w2a, không phải
port c2a — và theo luật 16:58, «khác c2a» ở đây không phải sai: c2a yếu
hơn (bỏ kiểm hẳn, nối cả WAN/tên miền không cổng LAN), w2a kiểm chặt hơn
(ghim + chỉ LAN).

## 6. LIỆT KÊ ĐIỂM SAI HIỆN TẠI (phản ánh 16:29) — trước khi sửa

Đối chiếu trên web2api main `8ed35ab` (giữ nguyên bảng lượt trước, thêm
cách giải quyết theo hướng mới):

| # | Điểm sai hiện tại | Hướng mới giải quyết ra sao |
|---|---|---|
| W1 | Chứng chỉ tự ký → chỉ báo lỗi kỹ thuật, không hiện mã, không có cách nào ngoài tự tính SHA-256 rồi dán | Tự ghim lần đầu (không cần biết vân tay là gì) |
| W2 | Vân tay đã ghim không khớp → bảo «cấu hình lại để ghim vân tay mới» nhưng không cho cách nào khác ngoài dán tay | Giữ nút tin lại cho riêng trường hợp đổi (đo lại + mặt nạ + vé) |
| W3 | Ô `van_tay_tls` đòi dán mã 64 ký tự, mô tả toàn thuật ngữ trần | Mô tả tiếng thường đã viết lại; ô thành `bi_mat` (chỉ hiện dạng che); thường không cần điền |
| W4 | ZTE tệ hơn: lưu rồi cảnh báo «đặt kiem_chung_chi_tls=false hoặc ghim» — xúi tắt kiểm hoặc dán mã | ZTE tự ghim lần đầu như mikrotik (đăng nhập thử lại với vân tay vừa đo; thành công thì hết cảnh báo, cấu hình lưu kèm vân tay); cảnh báo `TLS_TU_KY` chỉ còn khi tự ghim thất bại (không đo được hoặc thử lại vẫn hỏng) |
| W5 | ZTE ghim sai → cảnh báo «lấy lại vân tay SHA-256 đúng» — lại bắt dán | Giữ nút tin lại cho trường hợp đổi (`VAN_TAY_KHONG_KHOP`) |
| W6 | `mo_ta` nhiều trường còn thuật ngữ trần (quét chuỗi: 56 điểm nghi ngờ ở 29 module — nhiều dương tính giả, xem ghi chú lượt trước) | Viết lại toàn bộ `mo_ta` mikrotik + zte; test khóa cho 2 module này; 27 module còn lại để lượt riêng, không kết luận sai bằng quét chuỗi |
| W7 | Demo Nha «Kết nối router MikroTik» ghi tài khoản cần «read, write, api» — vênh với phân vai NV299 | KHÔNG đổi trong NV295 (thuộc NV299); ghi nhận |
| W8 (mới) | `kiem_dia_chi` mikrotik phân giải tên máy rồi nối theo IP phân giải được (mở đường DNS rebinding); IP WAN được nối bình thường (không có cổng LAN) | Cổng IP LAN cứng: tên miền từ chối không phân giải; WAN từ chối (§2) |

**Không sai (ghi rõ để khỏi sửa lùi):** kiểm vân tay TRƯỚC khi gửi mật
khẩu đã đúng và giữ nguyên; cơ chế «Nâng cao» thu gọn trường tùy chọn đã
có sẵn; runtime không tự ghim (fail-safe) là cố ý.

## 7. CÁCH LY MODULE + QUY TẮC HIỂN THỊ (19:19 + 19:26) — vẫn áp

### Cách ly mục tin

1. **Không có kho tin chung toàn cục.** `app/chung_chi_tls.py` không lưu
   vân tay nào (chỉ khoá HMAC vé của tiến trình + hàm không trạng thái).
   Vân tay đã tin chỉ nằm trong cấu hình RIÊNG của từng module; module
   không có API đọc/sửa cấu hình module khác.
2. **Vé tin gắn chặt module + đích** (chỉ còn dùng cho trường hợp đổi):
   vé sai module → từ chối, `so.cai` không được gọi (test khóa); hành
   động tin đo đúng đích TRONG VÉ, không lấy đích do người gọi gửi lên
   (test khóa: form trỏ nơi khác nhưng vân tay lưu vẫn là của đích trong
   vé — module nối sang nơi khác sau đó sẽ hỏng kiểm ghim, không tin ké).
3. **Vân tay chỉ tin đúng chứng chỉ đó** — đổi đích là hỏng kín (kiểm
   ghim trước khi gửi mật khẩu; chứng chỉ đổi giữa đo và nối lại thì lần
   nối lại hỏng, không lưu ghim sai).
4. **Đề nghị công khai không mang gì để leo thang** (chỉ `ly_do`/
   `ma_hien_thi`/`thong_bao`/vé; test khóa các khoá host/cổng/vân tay đầy
   đủ vắng mặt).
5. **Chống XSS hai lớp ở khối tin còn lại:** (a) `thong_bao` chỉ gồm câu
   cố định + mặt nạ hex (không chuỗi nào do thiết bị cung cấp; test khóa
   không chứa `<`, `>`, `&`); (b) dc-lite (`web/support.js`, hàm `thoat`)
   thoát HTML cho mọi nội suy `{{ }}`.

### Quy tắc hiển thị 19:26

- **Mã rút gọn (8…8) là mã nhận dạng, không phải bí mật đầy đủ → vẫn hiển
  thị bình thường** trong khối đề nghị đổi chứng chỉ, không cần xác thực
  lại (đúng nội dung NV295 yêu cầu hiển thị).
- **Vân tay đầy đủ thì KHÔNG hiển thị nữa.** Trước lượt này, `van_tay_tls`
  có `kieu: "chuoi"` nên GET cấu hình trả nguyên 64 ký tự hex về form.
  Nay cả hai manifest đã đổi sang `kieu: "bi_mat"`: giá trị đầy đủ vào
  kho bí mật, GET chỉ trả dạng che `…4-ký-tự-cuối` (lại là mã nhận dạng),
  form hiện «••••• đã lưu». Hành vi giữ nguyên: ô trống thì giữ giá trị
  đã tin (cùng cơ chế như `mat_khau`); tự ghim đặt vân tay qua `so.cai`
  trực tiếp, không qua form; module vẫn nhận đủ vân tay lúc chạy.
- **Không thêm đường hiển thị lại sau xác thực lại cho vân tay đầy đủ
  trong NV295** — «không bao giờ hiện đầy đủ» đã tuân thủ phần cấm của
  quy tắc 19:26. Cơ chế hiển thị-lại-sau-xác-thực-lại cho tab Bảo mật
  thuộc lượt bổ sung NV305, không đưa vào patch này.
- **Câu hỏi để chủ máy quyết (ghi rõ, KHÔNG tự thêm):** nút «Tin chứng
  chỉ này» (nay chỉ còn cho trường hợp đổi) tạo/sửa một mục tin — có nên
  yêu cầu xác thực lại (step-up: mật khẩu admin khi chưa bật 2FA / mã 2FA
  khi đã bật) ngay lúc bấm không? Hiện nút dùng cùng quyền quản trị như
  đường lưu cấu hình, không step-up riêng. Nếu chủ máy chốt «có», đó là
  một sửa nhỏ ở endpoint `tin-chung-chi`, làm ở lượt sau.

### Phần KHÔNG thuộc NV295 (đã có việc riêng, không đưa vào patch này)

Công tắc bật/tắt noVNC trong web UI như 2FA + quy tắc ẩn-hiện sau xác thực
lại cho mật khẩu noVNC/API key trong tab «Bảo mật & người dùng» thuộc lượt
bổ sung NV305.

## 8. FILE ĐỔI (patch)

| File | Đổi gì |
|---|---|
| `app/tu_xa.py` | Hàm mới `kiem_ip_lan(host)` — cổng IP LAN cứng (§2), danh sách tường minh, từ chối tên miền không phân giải |
| `app/chung_chi_tls.py` | Lõi đo/mặt nạ/vé/hành động tin (giữ từ lượt trước); `ghep_de_nghi_tin` siết chỉ nhận `ly_do == "doi"` |
| `app/so_module.py` | `_cai` chuyển tiếp khối `tin_chung_chi` (giữ từ lượt trước — nay chỉ còn cho trường hợp đổi) |
| `app/tuyen.py` | Endpoint `POST /api/modules/{id}/tin-chung-chi` (giữ — nay chỉ cho trường hợp đổi) |
| `modules/mikrotik-routeros/routeros.py` | Ngoại lệ `LoiBatTayTls` (giữ — để phân biệt lỗi bắt tay với lỗi nối) |
| `modules/mikrotik-routeros/module.py` | `kiem_dia_chi` cưỡng chế IP LAN (bỏ phân giải tên máy); `cai()` tự ghim lần đầu (chỉ khi lỗi đúng là xác minh chứng chỉ — helper `_la_loi_xac_minh_chung_chi`); `_de_nghi_tin` chỉ còn cho đổi; `van_tay_luu` vào `cau_hinh_luu` |
| `modules/mikrotik-routeros/manifest.json` | `van_tay_tls` → `bi_mat`; viết lại `mo_ta` (IP LAN + tự ghim + nút chỉ khi đổi); nhãn «Mã nhận dạng chứng chỉ» / «Kiểm tra chứng chỉ» |
| `modules/mikrotik-routeros/README.md` | Dòng `van_tay_tls` theo hướng mới |
| `modules/zte-e2633/module.py` | `cai()` kiểm IP LAN trước `kiem_url_lan`; tự ghim lần đầu (đo + đăng nhập lại với vân tay vừa đo; thành công thì hết cảnh báo); `_de_nghi_tin_zte` chỉ còn cho đổi; cảnh báo `TLS_TU_KY` sửa (chỉ còn khi tự ghim thất bại, không nhắc nút) |
| `modules/zte-e2633/manifest.json` | Như mikrotik (3 trường + `bi_mat`) |
| `modules/zte-e2633/README.md` | Dòng TLS + IP LAN theo hướng mới |
| `web/khung.js` | Form cài đặt: helper gom + hành động tin (giữ từ lượt trước — nay chỉ dùng khi đổi) |
| `web/Nha.dc.html`, `web/He-thong.dc.html`, `web/Doi-song.dc.html`, `web/Tac-pham.dc.html` | Khối nút «Tin chứng chỉ này» (giữ — nay chỉ hiện khi có đề nghị đổi) |

## 9. TEST

### Test mới — `test/test_nv295_ip_lan_tu_ghim.py` (42 test)

- **Cổng IP LAN:** chấp nhận RFC 1918 (cả biên `172.15`/`172.32` bị từ
  chối), ULA, IPv4-mapped; từ chối WAN, CGNAT, loopback (không cờ test),
  link-local, unspecified, multicast, documentation, reserved, 6to4 nhúng
  loopback; tên miền từ chối mà `getaddrinfo` không được gọi; loopback
  chỉ qua khi có cờ test.
- **Mikrotik:** `kiem_dia_chi` từ chối tên miền không phân giải; `cai`
  từ chối WAN trước khi nối (`create_connection` không được gọi); **tự
  ghim lần đầu thành công qua máy chủ RouterOS giả có TLS** (ok True,
  `cau_hinh_luu.van_tay_tls` đúng vân tay máy chủ, không có khối tin,
  mật khẩu chỉ gửi đúng 1 lần ở lượt nối lại sau ghim); helper chỉ nhận
  đúng lỗi xác minh chứng chỉ.
- **ZTE:** tự ghim lần đầu qua khách giả (lượt đầu `TLS_TU_KY` → đo →
  lượt lại mang đúng vân tay vừa đo → hết cảnh báo, lưu kèm vân tay,
  không khối tin); `cai` từ chối tên miền không phân giải và WAN.
- **Cách ly + hiển thị:** vé sai module bị từ chối (không ghi gì); hành
  động tin chỉ ghim đúng đích trong vé; khối tin đổi không chứa chuỗi
  thiết bị cung cấp (không `<`, `>`, `&`); `van_tay_tls` là `bi_mat` ở cả
  hai manifest và kho chỉ trả dạng che.

### Test cũ giữ/sửa (ghi rõ, không phải nới kiểm)

- `test/test_nv295_tin_chung_chi.py` (13 test): giữ mặt nạ/vé/đo, đề nghị
  đổi, hành động tin (thành công/từ chối khi đổi/hết hạn), ghép không lộ
  host/cổng, mô tả. **Bỏ 2 test đề nghị `tu_ky` ở lần đầu** (mikrotik +
  zte) — đã thay bằng test tự ghim ở file mới. **Thêm 1 test:**
  `tu_ky` không còn được ghép (validator siết).
- `test/test_web2api_nv150_zte_e2633.py::test_cai_tls_tu_ky_tu_ghim_khong_can_xac_nhan`
  (đổi tên từ test cảnh báo cũ, lần thứ hai đổi khẳng định theo quyết):
  lần đầu tự ký qua IP LAN → ok True, lưu đúng vân tay máy chủ thật (giả),
  không cảnh báo, không khối tin. Ý định gốc («lưu được khi gặp tự ký»)
  được giữ, khẳng định mới chặt hơn (kiểm cả vân tay đã lưu).
- `test/test_web2api_nv111_zte_e2633.py::test_cai_van_tay_sai_dinh_dang_bao_loi`:
  đổi địa chỉ test từ TEST-NET `192.0.2.1` sang IP LAN `192.168.1.1` để
  qua cổng IP LAN rồi mới tới bước kiểm định dạng (ý định gốc — kiểm
  định dạng vân tay — giữ nguyên). Test metadata `169.254.169.254` giữ
  nguyên không sửa (thông báo mới vẫn chứa chữ «chặn»).

### Tập liên quan — đều xanh

Mikrotik (`test_mikrotik_routeros.py` + 4 file NV279), ZTE (NV111 + NV150
+ NV150-sửa1), lõi (`kham_pha`, `hang_manifest`, `chuan_module`,
`duong_module_nv277`, `nv106_khung_css_tinh`) — **tổng 257 passed**
(lần chạy cuối, trước toàn suite).

### Toàn suite — ĐỐI CHIẾU NỀN SẠCH

Chạy cùng lệnh cả hai cây (bỏ 8 file muse2api lỗi thu thập có sẵn trên nền
do thiếu module google trong venv — giống NV309):

- Cây đã vá (lượt v2): **162 failed, 5980 passed, 273 skipped, 31 xfailed,
  17 errors** (`suite-patched2.log`).
- Cây sạch `8ed35ab`: **158 failed, 5929 passed, 273 skipped, 31 xfailed,
  17 errors** (`suite-clean.log`).
- Đối chiếu theo tên (phương pháp NV306): **clean-only rỗng** (mọi lỗi nền
  đều xuất hiện ở cả hai cây); **patched-only đúng 4 test** — đã điều tra
  từng test và sửa hết trong patch cuối:
  1. `test_web2api_cong_cu.py::test_7_khong_ten_nha_cung_cap_trong_app_va_web`
     + `test_web2api_doc_lap.py::test_dem_dong_nhac_ten_nha_cung_cap_khong_vuot_tran`:
     cùng một nguyên nhân — docstring `app/chung_chi_tls.py` chứa chữ
     «mikrotik», vi phạm quy tắc «không tên nhà cung cấp trong app/web».
     Đã sửa: đổi thành «module nối + đăng nhập thật» (không đổi hành vi).
  2. `test_web2api_nv45_a_nuot_loi.py::test_danh_sach_nuot_loi_khong_tang`:
     hai điểm nuốt lỗi mới `_de_nghi_tin`/`_de_nghi_tin_zte` (đo thất bại →
     None, fail-closed) chưa có trong danh sách kiểm toán NV45. Đã thêm
     vào `DA_KIEM_TOAN` kèm lý do (theo đúng quy trình của test đó).
  3. `test_web2api_nv266_do_tai_nguyen.py::test_api_do_tai_nguyen_that`:
     chạy lại đơn lẻ thì xanh — flake đo tài nguyên theo thời gian (cùng
     họ flake nhạy thời gian mà NV306 đã ghi nhận), không phải hồi quy.
- **Lưu ý trung thực về phạm vi đối chiếu:** đối chiếu toàn suite chạy
  trên cây v2; cây cuối khác v2 đúng hai chỗ nhỏ trên (một chữ trong
  docstring + hai mục trong danh sách kiểm toán test) — cả hai đều đã
  kiểm lại bằng chạy targeted (4 test trên + tập liên quan dưới, đều
  xanh). Không chạy lại toàn suite lần ba chỉ cho hai chỗ này; nếu điều
  phối muốn đối chiếu tuyệt đối trên cây cuối thì chạy lại cùng lệnh
  trên (kỳ vọng patched-only rỗng sau hai sửa trên).

### Kiểm tĩnh

- `py_compile` các file Python đổi: đạt.
- `node --check web/khung.js`: đạt (từ lượt trước, khung.js không đổi
  thêm ở lượt này).
- Thẻ `sc-if`/`sc-for` cân bằng ở 4 template đã sửa (lượt trước).
- `git diff --check`: sạch (kiểm lại trước khi đẩy).
- Quét bí mật trên patch: không mật khẩu/vân tay/chứng chỉ/IP/email thật
  nào (giá trị trong test đều giả, tạo lúc chạy hoặc chuỗi hex giả;
  địa chỉ chỉ có loopback test và IP LAN ví dụ).
- Bandit: không có trong venv máy này — điều phối chạy ở vòng soát.

## 10. CHƯA THỬ THẬT (trung thực — thuộc vòng sau gộp + dựng lại)

- **Router MikroTik thật / bộ phát ZTE thật:** chưa có ở đây. Đặc biệt
  cần thử: lần đầu tự ghim với chứng chỉ tự cấp thật của RouterOS (định
  dạng/chuỗi chứng chỉ thật có thể khác chứng chỉ openssl trong test);
  chứng chỉ đổi thật (cấp lại trên router → dừng nối + nút tin lại);
  chứng chỉ hết hạn (hiện tự ghim luôn cả hết hạn — xem §1 — cần chủ máy
  xác nhận có chấp nhận không).
- **Chrome thật (test nút khi đổi):** máy này không có Chrome — nút chỉ
  kiểm bằng `node --check` + cân bằng thẻ, chưa bấm thật. Thuộc vòng
  QUY-TAC: nộp → điều phối soát/dựng lại → kiểm bằng test Chrome.
- **Endpoint thật qua TestClient:** hành động tin mới chỉ kiểm ở mức hàm
  lõi + module (endpoint là lớp mỏng gọi đúng hàm đó).
- **Toàn suite đối chiếu nền sạch:** xem số liệu ở §9 (patched-only 4 test
  đã điều tra và sửa hết; cây cuối khác cây v2 đúng hai chỗ nhỏ đó, đã
  kiểm lại bằng chạy targeted).

## 11. GHI CHÚ CHO ĐIỀU PHỐI / CHỦ MÁY

1. **Thay đổi phá vỡ tương thích (đọc kỹ trước khi gộp):** cấu hình
   mikrotik/zte cũ dạng tên miền hoặc IP WAN sẽ **hỏng lúc lưu lại và
   lúc nạp lại** (do `kiem_dia_chi`/`nap` cưỡng chế IP LAN). Không có di
   trú tự động trong patch này — chủ máy cần báo người dùng đổi sang IP
   LAN trước khi dựng lại, hoặc quyết giữ một ngoại lệ cho cấu hình cũ
   (không tự thêm — cần quyết).
2. **Thứ tự gộp:** patch độc lập với NV299 (đặc tả, chưa có mã) và
   NV305/NV305-bo-sung (mật khẩu xem) — chỉ chạm 2 module + lõi kiểm địa
   chỉ + form cài đặt chung. Chú ý khi soát: `app/tu_xa.py` thêm hàm mới
   nhưng KHÔNG đổi `_dia_chi_bi_chan` (module từ xa không bị ảnh hưởng);
   `app/kho.py` không đổi (cơ chế `bi_mat` đã có sẵn).
3. **Test cũ đổi ý định theo quyết:** 3 test (nv150 tự ghim — lần thứ hai
   đổi khẳng định; nv111 địa chỉ test sang IP LAN; 2 test `tu_ky` bị bỏ
   thay bằng test tự ghim) — soát kỹ 3 điểm này, vì chúng đổi khẳng định
   theo đúng quyết 19:30, không phải nới kiểm để qua test.
4. **Câu hỏi còn mở cho chủ máy (không đoán):**
   - Q1: nút tin khi đổi chứng chỉ có cần step-up (mật khẩu admin / mã
     2FA) không? (xem §7)
   - Q2: «tự tạo chứng chỉ ngẫu nhiên» có thực sự chỉ là tự ghim chứng
     chỉ của thiết bị (§1) không, hay chủ máy muốn một cơ chế sinh chứng
     chỉ khác?
   - Q3: chứng chỉ HẾT HẠN có được tự ghim như tự ký không (hiện tại: có
     — vì cùng là lỗi xác minh chứng chỉ)?
   - Q4: cấu hình cũ tên miền/WAN xử lý ra sao khi dựng lại (báo trước
     cho người dùng đổi, hay ngoại lệ tạm)?
5. **demo `support.js` vẫn thiếu trên main** — NV295 bám bố cục form cài
   đặt sẵn có của khung, không bịa ảnh đối chiếu.
6. **Không đụng NV309-d:** vẫn chờ chủ máy trả Q2 (của NV309), không làm
   trong lượt này.
