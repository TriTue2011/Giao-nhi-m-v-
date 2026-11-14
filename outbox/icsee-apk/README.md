# ICSee — phân tích APK + Docker service (loa / mic / video ra màn hình cam)

Ngày: 13/11/2026. Camera: DOSEN RPO V1 (dùng app ICSee 7.9.6_G, màn hình 2.8" + gọi video 2 chiều).

## Mục lục

- `BAO-CAO.md` — phân tích APK iCSee 7.9.6_G: đường local cho cam / mic / màn hình (RTSP, port, API nội bộ).
- `AV-TALK-VIDEO-SEND.md` — đường gửi video lên màn hình cam qua AV talk (FunSDK): đàm phán, format dữ liệu gửi, checklist viết client.
- `AV-TALK-NATIVE.md` — phân tích native `libFunSDK.so`: encoder H.265, luồng frame tới lệnh gửi xuống thiết bị, tìm lệnh điều khiển màn hình.
- `BUTTON-PRESS-EVENT.md` — event/trạng thái nút bấm gọi video trên thân camera (chiều camera → app): đường cloud MPS, FunSDK P2P, DVRIP qua LAN.
- `../icsee-docker/` — Docker service (DVRIP-native, x86_64): API loa / mic / video ra màn hình cam, kèm `ARCH-BLOCKER-REPORT.md` (vì sao đường FunSDK bị chặn trên x86_64).

## Kết luận chính

- Live view qua FunSDK proprietary (`MediaRealPlay`, theo serial thiết bị); **không có** URL RTSP / HTTP-FLV / HLS local dùng được, **không có** HTTP API trên camera, ONVIF chỉ là cấu hình phía thiết bị (app không có ONVIF client).
- Talkback 2 chiều có qua FunSDK, codec **G.711 A-law, 8 kHz mono**, chung kênh media P2P.
- Video lên màn hình cam đi qua AV talk: app gửi **video YUV420P thô + audio PCM 8 kHz** (không phải NAL H.264/H.265), native encode lại; **H.265 đã chứng minh ở tầng encode** (`ff_libx265_encoder`, preset `ultrafast`, tune `zero-latency`); transcode là bắt buộc.
- **Không tìm thấy** lệnh bật màn hình / chọn nguồn hiển thị trong APK lẫn `.so` — màn hình do firmware cam tự quyết khi nhận media.
- Đường FunSDK **bị chặn trên x86_64**: ICSee không có bản x86_64, không có FunSDK cho Linux, `.so` Android cần lib Android-only, APP key không trích được từ APK.
- Phương án thay thế **DVRIP-native (không cần FunSDK)**: mic + loa khả thi trên x86_64 (monitor stream có audio; talkback `OPTalkData`, G.711 A-law 8 kHz, gói 320 byte); **video-send chưa xong** — đóng gói DVRIP của 11004/11006 chưa biết, cần bắt gói live trong một cuộc gọi video thật.
- Docker service đã build + test với camera DVRIP giả lập (unit 20/20, mic/loa/video dry-run); video-send báo rõ `implemented=false` (stub, trả 501), không giả vờ chạy được; Docker build chưa chạy được trong sandbox, cần build lần đầu trên server Proxmox.
- **Event nút bấm trên camera lấy được:** qua cloud MPS (message 6007 `MC_ON_AlarmCb` → `AlarmInfo`, mở màn hình cuộc gọi đến) và qua **DVRIP LAN** (subscribe opcode 1500 `AlarmSet` → cam đẩy JSON opcode 1504 `AlarmInfo`, push-based); event của nút bấm nhiều khả năng là `LocalAlarm` (cần test live bấm nút thật để xác nhận). **Không tìm thấy** đường FunSDK P2P trực tiếp, và **không poll được trạng thái nút** (event là push-only). Service Docker hiện chưa nhận event (chưa có code alarm).

## Lưu ý

- Không có file XAPK/APK, thư mục decompiled, hay `libFunSDK.so` trong outbox này (chỉ báo cáo + code service).
- Không có credential thật nào (mật khẩu cam, SN, APP key, token) — cấu hình qua biến môi trường, xem `../icsee-docker/.env.example`.
