# Báo cáo Telegram P1 + P2 — module web2api + gateway Docker (đẩy outbox)

**Ngày:** 2026-11-05. **Lệnh:** người dùng ra lệnh trực tiếp «viết code rồi đẩy
github zalo, tele» (02:21 +07 05/11) — làm ngay.
**Nhánh outbox:** `muse/telegram-p1` trên repo `TriTue2011/Giao-nhi-m-v-`
(Giao main kiểm trước khi làm: `82d9ff46`, không đổi lúc push).
**Phạm vi:** CHỈ viết code + test offline/mock. KHÔNG tài khoản thật, KHÔNG
gửi tin/gọi thật, KHÔNG api_id/api_hash/token/OTP/mật khẩu thật nào trong
code/patch/báo cáo/log (mọi bí mật trong test đều GIẢ rõ ràng).

## 1. Nội dung outbox

| File | Nội dung |
|---|---|
| `outbox/telegram-p1.patch` | Delta module `telegram-user` trên P0 (2729 dòng, 5 file): `module.py`, `README.md`, `web/index.html`, test P0 (sửa 2 assertion giai đoạn, xem §4), test P1 mới. Nền web2api 8ed35ab + P0. Thứ tự gộp: P0 → P1. |
| `outbox/telegram-gateway-p1/` | Toàn bộ cây gateway đã cập nhật (trừ `venv/`, `__pycache__/`, `*.log`, `data/`, file `.env` thật — không có file `.env` thật trong cây). Kèm workflow `.github/workflows/build-test.yml` (đã có từ trước, không đổi). |
| `outbox/telegram-p1-bao-cao.md` | Báo cáo này. |

## 2. P1 + P2 module `telegram-user` (delta trên P0)

Nền: checkout web2api 8ed35ab đã áp patch P0 (`muse/telegram-p0` = 0853f3de).
Không sửa một dòng nào của `telegram-bot`.

**P1 — đăng nhập + gửi qua TDLib:**
- Đăng nhập TDLib qua tab module (số → OTP → 2FA → QR tùy chọn; KHÔNG qua
  đường `/m`, KHÔNG qua `cai()`); client TDLib qua tdjson 1.8.69 với vòng
  trạng thái authorization; session bền: file `khoa` 0600 + thư mục `files/`
  0700, không qua API, không vào log.
- 3 mã sai khóa login 15 phút, log chỉ đếm lần thử, không ghi mã/OTP/2FA.
- Gửi tin/media/voice: dispatch + interface client TDLib thật, fake ở test
  (xem hạn chế §6: bước phân giải peer → user_id/chat_id qua vòng update
  TDLib còn chờ T1).
- Events: poll fallback cursor đơn điệu + đẩy webhook HA (`X-Gateway-Token`,
  retry 3 lần). Đủ mã lỗi: 409 ACCOUNT_BUSY/CALL_NOT_ACTIVE/ENDPOINT_BUSY,
  429 FLOOD_WAIT kèm `retry_after_seconds` từ Telegram, 502, 503.
- Công tắc «Cho phép HA gọi đi» mặc định TẮT (HA gọi → 403, tab vẫn gọi được).

**P2 — gọi đi + audio qua `/m`:**
- State machine dialing → active → ended; bận → hàng đợi FIFO sâu 10,
  timeout 120s, ưu tiên alarm > normal, thăng hạng khi cuộc trước kết thúc;
  ENDPOINT_BUSY cả khác tài khoản.
- Glue `callStateReady` → NTgCalls đúng map T0-B (servers→`connect_p2p`,
  protocol→versions/`p2p_allowed`, `encryption_key`→`skip_exchange`,
  `custom_parameters` giữ nguyên, signaling 2 chiều bằng bytes,
  JSON-encode ở biên tdjson).
- TTS Edge mặc định (interface inject được) + file TTS HA qua `audio/upload`
  (khối ≤300KB, xóa sau cuộc gọi/1 giờ).
- `audio/in`: khối JSON `{call_id, seq, pcm_b64, sample_rate, channels}`;
  mất khối chèn im lặng + đếm, quá tải 429, khối >400KB thân → 400.
- `audio/stream-url`: vé gắn 1 call_id; `luong()` trả 404 khi cuộc kết thúc;
  hỗ trợ Range. Vé ký bằng `app.duong_module.tao_duong_luong()` của lõi
  (đã đối chiếu chữ ký `(module_id, ve, goc)` trong checkout); URL chưa ký
  chỉ xuất hiện khi chạy tách rời khỏi lõi (test harness) — lõi thật từ
  chối URL chưa ký, nên không rò audio.
- PCM engine tập trung ở hằng `PCM_ENGINE` = s16le 48kHz mono (tiền lệ
  group call — định dạng gọi riêng tư CHƯA xác minh, TODO T1, không claim
  đã đúng).

## 3. P1 + P2 gateway Docker

- `gateway/tdclient.py` (mới): client TDLib thật qua tdjson 1.8.69 —
  setTdlibParameters → checkDatabaseEncryptionKey → OTP → 2FA → QR; gửi
  tin/media/voice qua MTProto; FLOOD_WAIT parse số giây từ message Telegram;
  request JSON-encode sang bytes, trường bytes là base64.
- `gateway/login.py`: login_id → OTP → 2FA → QR, session bền, chống flood
  như module. KHÔNG có endpoint đăng nhập nào dưới `/api/*` (có test quét
  route khẳng định); đăng nhập chỉ qua web UI nội bộ LAN-only.
- `gateway/engine.py`: glue thật `map_ready(callStateReady)` +
  `GlueSession` nối signaling 2 chiều.
- `gateway/calls.py`: thêm trạng thái `ringing`, `tts_audio_id`; giữ
  dialing→active→ended, queue, 409 ACCOUNT_BUSY trước ENDPOINT_BUSY.
- `gateway/audio.py` + `gateway/tts.py` (mới): `FrameQueue` (khối 200ms mặc
  định, mất khối = im lặng + đếm, đầy 50 khối → backpressure, khối quá cũ
  >~2s → bỏ); `PipeSource`/`PipeSink` đầy đủ; R1/USB chỉ interface + tài
  liệu (cần phần cứng); `POST /api/audio/in` (mic HA theo khối, đầy → 429)
  và `POST /api/audio/upload` (TTS HA theo khối ≤300KB → `tts_audio_id`,
  xóa sau cuộc gọi/1 giờ); TTS Edge mặc định qua interface inject được.
- Engine thật chỉ bật khi `GATEWAY_MOCK=0` và có `TELEGRAM_API_ID`/
  `TELEGRAM_API_HASH`; mặc định mock (`GATEWAY_MOCK=1`) giữ hành vi khung P0
  và trả `mock: true` rõ ràng (xem §6).
- Defaults giữ nguyên: ring 45s, attempts 2, interval 15s, max 180s,
  queue 120s/10, rate limit 120 req/phút/token, mã lỗi đủ bộ.
- Không đổi: Dockerfile, docker-compose.yml, .env.example, workflow
  build-test.yml, VERSION. Đổi duy nhất ở đóng gói: thêm `edge-tts` vào
  `requirements.txt` (xem §4) — vì P2 đặt TTS mặc định là Edge TTS.
- `docker-compose.vm.yml` trong cây chỉ dùng cho VM thử nghiệm, KHÔNG dùng
  trên server (server dùng `docker-compose.yml`).

## 4. Kiểm thử + xác minh của parent (tự chạy lại, không tin mù báo cáo con)

- **Module:** test P0 + P1 = **36/36 xanh** (13 P0 + 23 P1, venv P0,
  0,51s); `scripts/kiem_module.py` đạt (mã 0, 0 vi phạm, 0 cảnh báo).
  Patch đã kiểm `git apply --check` + áp thật lên bản copy mới của
  checkout 8ed35ab đã áp P0, sau đó test lại 36/36 trên bản đó.
- **Gateway:** **34/34 xanh** (15 cũ + 19 mới, venv gateway, 8,81s); boot
  smoke ngoài Docker: `GET /health` 200 (`degraded`, 0 tài khoản,
  `mock_mode: true`), `POST /api/call` chưa có tài khoản → 503
  `ACCOUNT_OFFLINE`, `GET /api/accounts` 200 rỗng. Không thử `docker
  build` (Docker trên VM này không chạy được container — đã kết luận
  21:51 04/11).
- **2 sửa của parent lúc kiểm chứng (đã vào patch/cây):**
  1. Test P0 rớt 1 assertion giai đoạn (P0 đặt `call` → 501/P1 và
     `audio/in` → 501/P2 làm placeholder; P1/P2 theo định nghĩa thay thế
     chúng): đã sửa 2 assertion đó sang hành vi P1/P2 thật với cùng
     input (`call` tts thiếu text → 400 `TTS_THIEU`; `audio/in` thiếu
     seq/pcm → 400 `SEQ_SAI`, vì kiểm khuôn thân chạy trước khi tra cứu
     cuộc gọi). Các assertion 501 còn lại (`answer_call` → P3,
     `history` → P4) giữ nguyên. File test P0 không bị sửa gì khác.
  2. Thêm `edge-tts` vào gateway `requirements.txt` (lý do ở §3).
- Quét bí mật trên patch + cây gateway: sạch. Không có file `.env` thật.

## 5. Cách áp dụng + điều kiện tiên quyết

- Module: áp `telegram-p1.patch` lên checkout web2api 8ed35ab ĐÃ áp patch
  P0 (thứ tự P0 → P1), chạy test như §4, rồi đẩy lên fork theo quy trình
  nguồn git như các module khác. Cần trên máy chủ: `tdjson==1.8.69`,
  `ntgcalls==3.0.6`, `edge-tts`, ffmpeg.
- Gateway: lấy cây `telegram-gateway-p1/`, build image (workflow
  build-test.yml đã có sẵn, tag `test`), chạy bằng `docker-compose.yml`
  trên server, đặt `GATEWAY_TOKEN` sinh mới + `TELEGRAM_API_ID`/
  `TELEGRAM_API_HASH` + `GATEWAY_MOCK=0` khi muốn engine thật.

## 6. Hạn chế trung thực — phần này CHƯA xong, đừng đọc là «gọi được rồi»

1. **Module:** `KhachTdlib.tao_cuoc_goi`/`gui_tin_nhan`/`gui_media`/
   `gui_voice` còn raise `NotImplementedError` vì cần phân giải peer →
   user_id/chat_id qua vòng nhận update TDLib. Dispatch/interface/fake đã
   đủ và test xanh, nhưng «gửi/gọi thật» chỉ hoàn tất khi T1 nối xong
   bước này + vòng lặp update TDLib + mic live qua nguồn NTgCalls
   EXTERNAL + decode mp3/wav → PCM/resample (module không được gọi tiến
   trình con theo bộ quét, nên decode/resample này chưa có).
2. **Gateway:** route `/call` chạy state machine + bộ đệm phát TTS, nhưng
   khởi động engine NTgCalls thật với peer thật (async runtime) thuộc T1;
   glue đã test với fake. `send_media` gửi dạng `inputMessageDocument`
   chung, chưa phân loại ảnh/video theo mime (để P4).
3. **Cả hai:** định dạng PCM gọi riêng tư chưa xác minh (chỉ có tiền lệ
   group call s16le 48kHz); `RTCServer` constructor và server có chấp
   nhận layer 232 + layer gọi NTgCalls không đều chờ T1.
4. **Chưa làm:** T1 gọi thật tài khoản phụ ↔ tài khoản test; triển khai
   lên máy chủ w2a thật; build image Docker thật + chạy trên server;
   P3 chiều nhận; P4 phủ Zalo còn lại; P5 alarm policy + hardening;
   integration HA mỏng; đăng nhập tài khoản phụ thật + session bền qua
   restart.
5. **Cảnh báo kiến trúc (giữ nguyên):** một tài khoản MTProto KHÔNG chạy
   cùng lúc cả module web2api lẫn gateway — mỗi đường một tài khoản phụ
   riêng, hoặc chỉ chạy một đường tại một thời điểm.
