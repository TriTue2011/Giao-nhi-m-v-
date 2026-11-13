# icsee-docker — Loa / Mic / Video lên màn hình camera ICSee (DOSEN RPO V1)

Docker service cho camera ICSee/DOSEN RPO V1 (màn hình 2.8", gọi video
2 chiều) với HTTP API cho 3 tính năng:

| Tính năng | Trạng thái |
|---|---|
| **Mic** — nghe tiếng từ camera | ✅ Làm đầy đủ, đã test với camera DVRIP giả lập |
| **Loa** — nói ra loa camera | ✅ Làm đầy đủ, đã test với camera DVRIP giả lập |
| **Video ra màn hình camera** | ⚠️ **Dry-run only** — transcode chạy được, gửi xuống thiết bị CHƯA xong (chờ bắt gói live) |

## Vì sao không dùng FunSDK

Xem [`ARCH-BLOCKER-REPORT.md`](ARCH-BLOCKER-REPORT.md): ICSee chỉ có bản
ARM, `libFunSDK.so` là thư viện Android (cần `liblog`, `libandroid`,
`libmediandk`, `libOpenSLES`, `libEGL`, …) và APP key không trích được
từ APK. Service này **không dùng FunSDK**: nó nói thẳng giao thức
**DVRIP** (giao thức XM/XMeye, port TCP 34567) với camera, dựa trên
source go2rtc (`pkg/dvrip`) và python-dvr — cả hai khớp nhau. Chạy
được trên x86_64, không cần binary Android nào.

Cơ sở phân tích đầy đủ: `~/workspace/icsee-apk/BAO-CAO.md`,
`AV-TALK-VIDEO-SEND.md`, `AV-TALK-NATIVE.md` (phân tích APK iCSee
7.9.6_G + `libFunSDK.so`).

## Chạy

```bash
cp .env.example .env   # điền IP / user / mật khẩu camera thật
docker compose up --build -d
curl http://localhost:8080/api/health
```

Yêu cầu: Docker trên máy có thể tới được camera qua LAN (port 34567).
Nếu camera ở subnet khác với container, đổi `docker-compose.yml`
sang `network_mode: host` (xem ghi chú trong file).

### Biến môi trường (`.env`)

| Biến | Mặc định | Nghĩa |
|---|---|---|
| `ICSEE_CAM_IP` | *(bắt buộc)* | IP LAN của camera |
| `ICSEE_CAM_PORT` | `34567` | Port DVRIP TCP |
| `ICSEE_CAM_USER` | `admin` | Tài khoản camera |
| `ICSEE_CAM_PASS` | *(rỗng)* | Mật khẩu camera |
| `ICSEE_CHANNEL` | `0` | Kênh video |
| `ICSEE_STREAM` | `Main` | `Main` hoặc `Extra1` |
| `ICSEE_SN` | *(rỗng)* | Serial camera (hiện chưa dùng — DVRIP không cần SN) |
| `VIDEO_WIDTH` / `VIDEO_HEIGHT` / `VIDEO_FPS` / `VIDEO_CODEC` | `864` / `480` / `10` / `H264` | Fallback khi không đàm phán được `DecoderPram` (giống fallback của app iCSee) |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8080` | Bind của API |

**Không ghi credential thật vào code/repo** — chỉ qua `.env` (file này
không commit; xem `.env.example`).

## API

Base URL: `http://<host>:8080`. Tất cả lỗi trả JSON
`{"error": "<code>", "message": "..."}`.

### Hệ thống

| Endpoint | Mô tả |
|---|---|
| `GET /api/health` | `{"status":"ok","service":"icsee-docker","version":"0.1.0","uptime_seconds":...}` |
| `GET /api/status` | Trạng thái đầy đủ: kết nối camera, mic, talk, video (xem `video_send.implemented` — hiện là `false`) |
| `POST /api/cam/connect` | Login DVRIP vào camera. 200 `{"connected":true,"session":"0x...","device":"..."}`; 503 `camera_unreachable` nếu không tới được camera |
| `GET /api/cam/decoder-pram` | Đọc `DecoderPram` (cmdId 0x550) của camera: codec/res/fps mà camera chấp nhận cho AV talk. 200 `{"raw":{...},"params":{"codec":"H265","width":1920,"height":1080,"fps":30,"negotiated":true}}`; nếu camera không trả thì `negotiated:false` + fallback |

### Loa — nói ra loa camera

Talkback DVRIP: `OPTalk` Claim (1434) → Start (1430) → `OPTalkData`
(1432), G.711 A-law 8 kHz mono, gói 320 byte (40 ms), theo đúng
go2rtc `backchannel.go`.

| Endpoint | Mô tả |
|---|---|
| `POST /api/audio/talk/start` | Mở kênh talk. 200 `{"running":true,"packets_sent":0,...}`; 503 nếu camera không tới được |
| `POST /api/audio/talk/send?format=pcm16` | Gửi audio. Body: binary `application/octet-stream`, PCM16 LE 8 kHz mono (`format=pcm16`, mặc định) hoặc G.711 A-law thô (`format=g711a`). Hoặc JSON `{"data":"<base64>","format":"pcm16"|"g711a"}`. 200 `{"packets_sent":N,"bytes_received":M,...}`. 409 `talk_not_started` nếu chưa start |
| `POST /api/audio/talk/stop` | Đóng kênh talk |

Ví dụ — nói một file WAV 8 kHz mono ra loa:

```bash
# Chuyển bất kỳ audio nào về PCM16 8 kHz mono:
ffmpeg -i input.mp3 -ar 8000 -ac 1 -f s16le -acodec pcm_s16le - > tone.pcm
curl -X POST http://localhost:8080/api/audio/talk/start
curl -X POST -H 'Content-Type: application/octet-stream' \
  --data-binary @tone.pcm \
  'http://localhost:8080/api/audio/talk/send?format=pcm16'
curl -X POST http://localhost:8080/api/audio/talk/stop
```

### Mic — nghe tiếng camera

Monitor stream DVRIP: `OPMonitor` Claim (1413) → Start (1410), audio
trong gói media `0xFA`, G.711 A-law 8 kHz, decode sang PCM16.

| Endpoint | Mô tả |
|---|---|
| `GET /api/audio/mic?format=pcm16` | Stream chunked HTTP. `pcm16` (mặc định): PCM16 LE 8 kHz mono, `audio/L16;rate=8000;channels=1`. `wav`: thêm header WAV 44 byte. `g711a`: G.711 A-law thô. Session tự dừng khi client ngắt kết nối |
| `POST /api/audio/mic/stop` | Dừng session mic |

Ví dụ — ghi 10 giây tiếng camera ra file WAV:

```bash
curl -m 10 'http://localhost:8080/api/audio/mic?format=wav' -o mic.wav
```

### Video ra màn hình camera — ⚠️ dry-run only

Pipeline **đã chạy được**: nhận nguồn video từ bất kỳ IP nào trong LAN
(RTSP H.265 ưu tiên, chấp nhận mọi URL mà FFmpeg đọc được), decode
bằng FFmpeg về YUV420P đúng res/fps đã đàm phán (mặc định theo cam
DOSEN: H.265 1080P 30fps; không đàm phán được thì fallback 864×480 /
fps 10 / H264 như app iCSee), điều tiết theo fps.

**Phần gửi xuống thiết bị CHƯA xong.** Module `app/video_sender.py`
đã viết đầy đủ những gì đã chứng minh từ phân tích native
(`AV-TALK-NATIVE.md`): `EncodeCameraBean` JSON, frame-info
`{"timestamp","type"}`, control JSON 4 lệnh
(`video_pause`→3, `video_continue`→4, `switching_resolution`→12,
`reset_encoder_info`→13), message ID 11004 (mở/đóng) và 11006 (gửi
data) — nhưng **đóng gói DVRIP dưới `Dev_SendMsg` (opcode/framing/
byte order của payload 11006, FRAME_INFO kèm NAL) chưa biết**, nên
class `AVTalkWireSender` là stub và raise `WireProtocolNotImplemented`.
Service **không bao giờ báo video-send là chạy được**: `/api/status`
trả `video_send.implemented=false` và `POST /api/video/control` trả
501 `video_send_not_implemented`.

| Endpoint | Mô tả |
|---|---|
| `POST /api/video/start {"source":"rtsp://...","width":...,"height":...,"fps":...,"codec":"H264"\|"H265"}` | Bắt đầu pipeline transcode (dry-run: frame được decode rồi đếm và bỏ, không gửi). Không chỉ `width/height/fps/codec` thì lấy từ `DecoderPram` của camera, fallback 864×480/fps 10/H264. 200 `{"running":true,"negotiated":true,"params":{...},"video_send":{"state":"dry_run_transcode_only","implemented":false}}`; 503 nếu không tới được camera |
| `POST /api/video/stop` | Dừng pipeline |
| `GET /api/video/status` | `{"running":...,"frames_produced":N,"frames_dropped_not_sent":N,"actual_fps":...,"last_error":...,"video_send":{"state":"dry_run_transcode_only","implemented":false}}` |
| `POST /api/video/control {"command":"video_pause"\|...}` | 501 `video_send_not_implemented` (chờ wire protocol) |

Ví dụ:

```bash
curl -X POST -H 'Content-Type: application/json' \
  -d '{"source":"rtsp://192.168.1.50:554/live"}' \
  http://localhost:8080/api/video/start
curl http://localhost:8080/api/video/status   # frames_produced tăng = transcode chạy
curl -X POST http://localhost:8080/api/video/stop
```

## Kiến trúc

```
app/
  config.py       # env config, không chứa giá trị thật
  g711.py         # G.711 A-law encode/decode pure Python (chuẩn ITU-T)
  dvrip.py        # DVRIP client: login (1000), keepalive (1006),
                  #   config (1042/1360), OPMonitor (1413/1410),
                  #   OPTalk (1434/1430/1432), đọc media packet
                  #   (0xFC/0xFE video, 0xFD P-frame, 0xFA audio, 0xF9 info)
                  #   + bỏ qua JSON reply (KeepAlive) lẫn trong stream media
  audio.py        # MicSession (monitor -> PCM16 queue) + TalkSession
  video.py        # VideoPipeline: FFmpeg decode -> YUV420P, dry-run
  video_sender.py # AVTalkWireSender (STUB — chờ wire protocol),
                  #   builder EncodeCameraBean / frame-info / control JSON
  main.py         # FastAPI: /api/health, /api/status, /api/cam/*,
                  #   /api/audio/*, /api/video/*
tests/
  test_g711.py, test_dvrip_framing.py   # unit tests (pytest)
  fake_cam.py     # camera DVRIP giả lập để test không cần cam thật
Dockerfile        # python:3.12-slim + ffmpeg, chạy pytest ở build
docker-compose.yml
```

Giao thức DVRIP (header 20 byte: `0xFF`, session LE u32, seq LE u32,
opcode LE u16, payload length LE u32; payload JSON + `\n\x00`; login
dùng SofiaHash = MD5 password map 8 ký tự) — xem `app/dvrip.py`.

## Đã test gì / chưa test gì

Đã test (13/11/2026, trên VM sandbox, **không có camera thật**):

- **Unit tests: 20/20 pass** (`pytest tests/ -q`) — G.711 vector chuẩn
  (encode(0)=0xD5, decode(0xD5)=+8, …), DVRIP framing, login chunk,
  media packet H.264/H.265/audio, gói talk 320 byte, bỏ qua JSON
  reply trong stream media.
- **Service chạy trực tiếp bằng uvicorn** (Docker không chạy được
  trong sandbox này — runc bị chặn syscall, xem dưới): `/api/health`
  và `/api/status` trả đúng; endpoint lỗi trả đúng mã
  (`camera_unreachable` 503, `talk_not_started` 409,
  `video_send_not_implemented` 501).
- **Chống camera DVRIP giả lập (`tests/fake_cam.py`, port 34567):**
  login thành công (`session 0x00000001`); `DecoderPram` đàm phán
  được H265 1920×1080@30; **loa**: gửi 6400 byte PCM sine 440 Hz →
  10 gói OPTalkData, header đúng hết (BE `0x1FA`, codec 14, rate 2,
  LE length 320), decode lại khớp trong sai số lượng tử A-law;
  **mic**: stream 26 giây qua cả keepalive 20 s không lỗi, 697 gói,
  tone 440 Hz / biên độ ~12000 khớp nguồn, tự dừng khi client ngắt;
  **video**: H.265 1280×720 30fps → 180 frame YUV420P (6 s × 30 fps),
  fallback 864×480/fps 10 → 60 frame; RTSP input flags
  (`-rtsp_transport tcp -timeout`) parse đúng.
- **`docker build` CHƯA chạy được trong sandbox** (daemon chạy được
  với vfs nhưng runc fail `operation not permitted` kể cả
  `--privileged` — sandbox thiếu quyền syscall). **Build lần đầu phải
  làm trên server Proxmox của user** (`docker compose up --build`).
  Dockerfile đã được review kỹ + các bước của nó đã verify riêng
  (apt ffmpeg, pip install, pytest pass). Lần build đầu trên server
  nếu lỗi, gửi log build cho Muse.

Chưa test — cần camera DOSEN thật:

- Login DVRIP bằng mật khẩu thật, đọc `DecoderPram` thật của cam
  (xem cam có báo H265 1080P/30fps như cấu hình XMeye không).
- Mic/loa live: nghe tiếng cam, nói ra loa cam.
- Video lên màn hình: **chưa thể test cho tới khi hoàn thiện wire
  protocol** (xem dưới).

## Hoàn thiện video-send cần gì

1. **Bắt gói trong một cuộc gọi video thật từ app iCSee** (điện thoại
   gọi video tới camera, `tcpdump` trên cùng LAN + `adb logcat`):
   cần thấy rõ đóng gói DVRIP của message 11004 (mở AV talk,
   `SNetMediaControlParam` + JSON `EncodeCameraBean`) và 11006 (gửi
   frame), byte order payload, và FRAME_INFO nào kèm NAL H.265
   (Annex B? VPS/SPS/PPS kèm keyframe?).
2. Nếu bật được `Fun_IsDebug`, 4 file tạm `av_talk_data_*.dat` chứa
   YUV/PCM đầu vào và byte gửi xuống thiết bị — đối chiếu trực tiếp.
3. Sau đó implement `AVTalkWireSender` trong `app/video_sender.py`,
   bỏ stub, thêm test live, và chỉ khi đó mới đổi
   `video_send.implemented` thành `true`.

Lưu ý từ phân tích native: **không có lệnh bật màn hình / chọn nguồn
hiển thị** trong `libFunSDK.so` — màn hình được cho là tự hiển thị khi
AV talk chạy (firmware cam tự quyết). Test live sẽ xác nhận màn hình
có sáng không khi AV talk chạy.
