# Báo cáo P0 — Module Telegram mới `telegram-user` trên web2api

Ngày: 2026-11-04. Nền: web2api main `8ed35ab` (đã kiểm lại bằng `git ls-remote`
trước khi viết code — main chưa nhích kể từ nền thiết kế, caveat trong thiết
kế đã được giải quyết). Chỉ viết code, không đăng nhập, không dùng
api_id/api_hash/token/OTP thật, không gửi tin hay gọi tới bất kỳ ai, không
sửa một dòng nào của `telegram-bot`.

## 1. Phạm vi đã làm

Module MỚI `telegram-user` (hạng A, tiền tố `telegram_user`, loại `tien_ich`,
nhóm con `nhan-tin-va-kenh`), chạy trong tiến trình lõi, theo phương án B
(TDLib báo hiệu + NTgCalls media) và hợp đồng đường `/m` NV277:

- `modules/telegram-user/manifest.json` — khả năng `kenh_ra` + `hoi_vong` +
  `duong_module`, `hoi_vong.chu_ky_giay` 5, `duong_module` {}, tab
  `web/index.html`, trường Cài đặt đủ §7.1 (xem mục 4).
- `modules/telegram-user/module.py` (710 dòng) — `Module`: `nap`/`cai`/
  `suc_khoe`/`dung` + `kenh_ra`/`gui_tin` (mock) + `hoi_vong` (mock) +
  `tich_hop` dispatch + `luong` stub (404) + `KhoPhien` (phiên TDLib trên đĩa)
  + bộ lọc log `_LocBiMat`.
- `modules/telegram-user/web/index.html` — tab tĩnh trung thực về trạng thái
  P0 + đường dẫn tới form Cài đặt chung của lõi.
- `modules/telegram-user/README.md` — điều kiện cài, bố cục phiên, bảng đường.
- `test/test_web2api_telegram_user_p0.py` — 13 test mock (xem mục 2).
- Khung integration mỏng phía HA: giao kèm trong outbox tại
  `ha-telegram-user/` (component HACS riêng: config flow kiểm `health`,
  service `send_message`, sensor tài khoản) — KHÔNG nằm trong patch web2api
  vì nó là repo HACS riêng, và KHÔNG nằm trong `modules/telegram-user/` vì
  file `.py` của HA sẽ làm hỏng quét `kiem_module` (import ngoài khai báo).
  Khung này chưa kiểm trên HA thật (cần máy chủ w2a thật).

### Đường /m đã có ở P0 (qua `tich_hop`, lõi xác thực khoá khách + LAN-only)

| Đường | P0 |
|---|---|
| `GET health` | `{status, version, accounts_total, accounts_online}` |
| `GET accounts` | Chỉ đọc `{tai_khoan: [{id, phone, display_name, status}]}` — không bí mật. Không có đường thêm tài khoản/mã/2FA qua HA. |
| `POST send_message` | Thân `{account?, peer, message, quote_message_id?, ttl?}` → ghi hộp thư mock, trả `{ok, tin_id, account, peer}`. |
| `GET events?since=` | Poll fallback `{events, cursor}`, id đơn điệu tăng, giữ tối đa 10000 event. |
| `call`, `answer_call`, `hangup_call`, `calls` | 501, giai đoạn P1/P3. |
| `history`, `contacts`, `groups`, `send_media`, `send_voice` | 501, giai đoạn P4. |
| `audio/in`, `audio/stream-url`, `audio/upload` | 501, giai đoạn P2. |
| Đường lạ → 404, sai phương thức → 405, thân POST không phải dict → 400. |

### Phiên TDLib trên đĩa (lựa chọn của P0, cần chốt với lõi)

`<WEB2API_DATA>/telegram-user/tdlib/<id-tài-khoản>/`: `khoa` (32 byte hex,
0600), `files/` (0700, P0 để trống), `tai_khoan.json` (sổ mock, 0600). Gốc lấy
từ `WEB2API_DATA` (mặc định `/data`), cùng quy ước `app/kho.py`. Lõi hiện
chưa có quy ước thư mục dữ liệu riêng cho module nên đây là lựa chọn của P0,
không phải quy ước đã chốt.

## 2. Test đã chạy + kết quả

Môi trường: venv riêng `~/workspace/telegram-p0/venv` (pytest 9.2.0,
tdjson 1.8.69, ntgcalls 3.0.6 — đúng pin T0/T0-B). Không mạng, không tài khoản thật.

- **pytest 13/13 xanh** (`test/test_web2api_telegram_user_p0.py`, 0,56 s):
  manifest hợp chuẩn; vòng đời; `cai()` thiếu/sai (10 trường hợp) và hợp lệ;
  `gui_tin` mock đủ mã lỗi + thành công; `tich_hop` health/accounts (không lộ
  bí mật)/send_message/events (cursor, since, since sai); 404/405/501 + `luong`
  stub; `hoi_vong` xả + đúng khuôn 4 trường; phiên bền qua «restart» (tạo lại
  Module + nap trên cùng `WEB2API_DATA` → tài khoản + khóa còn nguyên, quyền
  0600/0700 đúng); event < 5 s (đo thời gian dispatch sau khi nạp mock);
  pin gói; log không lộ bí mật (bộ lọc che thành «••••»).
- **`scripts/kiem_module.py`: ĐẠT, mã thoát 0, 0 vi phạm, 0 cảnh báo** (cả dạng
  văn bản và `--json`): quét 1 tệp `.py`, 12 import (stdlib + `tdjson` +
  `ntgcalls` — cả hai đều khai trong `yeu_cau_goi`), 0 tên miền (module không
  hardcode URL nào; DCs do TDLib tự phân giải), không subprocess/eval/pickle/
  `verify=False`, không chuỗi giống bí mật, không IP nội bộ.
- **Probe nạp qua lõi (`app.kham_pha.nap_ma`): ĐẠT** — `kiem_manifest` None,
  `goi_thieu` rỗng (wheels đã cài), nạp thành công, đủ `nap`/`cai`/`suc_khoe`/
  `dung` + `tich_hop`/`luong`/`hoi_vong`/`kenh_ra`/`gui_tin`.
- **Chưa chạy:** toàn suite lõi (delta chỉ thêm module + test mới, không sửa
  file cũ nào nên không có hồi quy từ patch này); kiểm trên máy chủ w2a thật,
  trên HA thật, trên máy ARM thật (xem mục 5).

## 3. Tiêu chí ra P0 — đạt/chưa đạt từng mục (trung thực)

| Tiêu chí (theo brief P0: khung + mock, không đăng nhập thật) | Kết quả |
|---|---|
| Cài được từ fork | **ĐẠT Ở MỨC MODULE:** nạp qua `nap_ma` của lõi thành công, `kiem_manifest` + `kiem_module` đạt. **CHƯA ĐẠT Ở MỨC MÁY CHỦ THẬT:** chưa có máy chủ w2a để cài từ fork; cần host cài wheels (mục 6) + đăng ký nguồn git fork. |
| Thêm tài khoản (mock) qua tab | **ĐẠT Ở MỨC MOCK:** `KhoPhien` tạo thư mục + khóa + sổ; tab tĩnh + đường `accounts` chỉ đọc. **Đăng nhập OTP/2FA/QR thật là P1, chưa có** (đúng brief P0 «chỉ khung + mock»). |
| Restart lõi không mất session | **ĐẠT Ở MỨC MOCK:** tạo lại Module + nap trên cùng thư mục dữ liệu → tài khoản + khóa còn nguyên; `dung()` không xóa phiên. **Restart lõi thật chưa kiểm.** |
| HA gửi tin qua cả /m và /api/gui (mock) | **ĐẠT Ở MỨC DISPATCH:** `tich_hop("send_message")` và `gui_tin()` đều ghi hộp thư mock (test khóa cả hai đường). **HA thật chưa gửi** (integration chưa kiểm trên HA, chưa có máy chủ). |
| Event < 5 s (mock) | **ĐẠT Ở MỨC MOCK:** event nạp mock → `tich_hop("events")` trả ngay, đo < 5 s. **Event thật từ TDLib + webhook HA chưa có.** |

## 4. Điểm thiết kế được điều chỉnh ở P0 (lý do cụ thể)

- **D-P0-1 — giới hạn 120 req/phút/khoá KHÔNG thực thi được ở tầng module:**
  lõi không truyền danh tính khoá vào `tich_hop(duong, phuong_thuc, query,
  than, goc)` nên module không phân biệt được khoá nào. P0 không đặt giới
  hạn giả; đường `/api/gui` vẫn chịu trần 20 tin/phút/khoá của lõi. Cần lõi
  truyền danh tính khoá hoặc giới hạn ở tầng lõi — chốt lúc triển khai.
- **D-P0-2 — `cai()` P0 chỉ kiểm định dạng:** thiết kế §7.1 nói `cai()` kiểm
  «tính gọi được của DCs»; P0 không có client thật nên không kiểm được qua
  mạng. Kiểm DCs đi cùng client thật ở P1.
- **D-P0-3 — `yeu_cau_goi`:** phác thiết kế chứa chuỗi mô tả («tdjson 1.8.69
  (…)», «ntgcalls (media; …)», «ffmpeg (…)») — chuỗi đó KHÔNG qua được
  `kiem_manifest` (chỉ nhận tên gói trần, chữ/số/`_`). P0 dùng
  `["tdjson", "ntgcalls"]`; version pin ghi trong `tai_nguyen.ghi_chu`,
  README module và test pin. `ffmpeg` là nhị phân hệ thống, không phải gói
  pip, nên không khai trong `yeu_cau_goi` (khai sẽ làm `goi_thieu` từ chối
  nạp trên mọi máy).
- **Thêm trường `dich`:** phác manifest không có nhưng §4.3 bắt buộc có danh
  sách đích riêng cho `kenh_ra` nên P0 thêm (kiểu `chuoi`, JSON, peer MTProto,
  không dùng chung với `telegram-bot`).
- **Thêm `tts_rate`, `queue_timeout`, `queue_depth`, `cho_phep_ha_goi_di`,
  `tu_dong_nghe_may`:** thuộc chip Cài đặt §7.1 mà phác lược bớt; P0 thêm đủ.
  Công tắc dạng `chuoi` «bat»/«tat» vì lõi chỉ có kiểu `chuoi`/`bi_mat`/
  `danh_sach_bi_mat`, không có kiểu bool.
- **Tab:** P0 giao tab tĩnh + form Cài đặt chung của lõi (tab generic dựng từ
  `truong_cau_hinh`). Tab hiển thị dữ liệu trực tiếp (tài khoản/cuộc gọi/log
  qua JS) cần quyết đường tab→module (khoá khách trong trình duyệt hay route
  lõi) — để P1, vì tab JS hiện chỉ gọi được route lõi `/api/*` (mẫu youtube),
  không gọi được `/m` (cần khoá khách).
- **`mang_ra`:** giữ đúng chuỗi mô tả trong thiết kế (DCs do TDLib tự phân
  giải). `kiem_manifest` chỉ yêu cầu danh sách chuỗi nên qua được, nhưng
  chuỗi này không phải tên miền — cần chủ máy/lõi xác nhận lúc duyệt quyền.

## 5. Còn chờ tài khoản thật / máy chủ thật để kiểm

1. Cài module từ fork lên máy chủ w2a thật (cần wheels + nguồn git fork).
2. Đăng nhập tài khoản phụ thật qua tab (OTP/2FA/QR) + session bền qua 3 lần
   restart lõi thật (P1).
3. Gửi tin thật qua cả `/m` và `/api/gui`; event thật < 5 s tới HA (webhook +
   poll fallback không mất/không trùng).
4. Import tdjson/ntgcalls trên máy ARM thật (T0/T0-B mới xác minh aarch64 bằng
   readelf, chưa chạy thử).
5. Glue TDLib → NTgCalls chạy thật + định dạng PCM gọi riêng tư (T1, sau P0/P1).
6. Đường dẫn dữ liệu module + giới hạn tốc độ `/m` + hạng A với native wheel:
   chốt với lõi/chủ máy lúc triển khai.
7. Kiểm integration HA mỏng trên HA thật (config flow, service, sensor).
8. Toàn suite lõi trên máy chủ (P0 chỉ chạy test mới + quét + probe nạp).

## 6. Cách áp patch + điều kiện tiên quyết

Patch: `telegram-p0.patch` (5 file, 1137 dòng thêm, nền 8ed35ab, chỉ thêm mới,
không sửa file cũ nào). Áp lên checkout web2api sạch rồi đẩy lên fork; máy
chủ kéo bản mới theo quy trình nguồn git như các module khác.

Trước khi cài module trên máy chủ, phải có: `tdjson==1.8.69`,
`ntgcalls==3.0.6` (glibc ≥ 2.28), `ffmpeg` (nhị phân hệ thống). Thiếu wheel →
lõi từ chối nạp sạch với «thiếu gói Python» (hợp đồng lõi, không phải lỗi).

## 7. Ranh giới đã giữ

Không đăng nhập tài khoản Telegram nào; không api_id/api_hash/token/OTP thật;
không gửi tin, không gọi tới bất kỳ ai; không sửa `telegram-bot`; không đẩy
main, không đẩy sang repo web2api (nhánh dưới đây nằm trên repo Giao).
Mọi chuỗi bí mật trong test đều GIẢ rõ ràng. Không có bí mật nào trong patch,
báo cáo hay khung HA.
