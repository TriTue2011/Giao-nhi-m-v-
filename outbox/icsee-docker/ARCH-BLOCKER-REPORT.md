# ICSee Docker service — KẾT LUẬN KIẾN TRÚC: DỪNG (không có libFunSDK.so x86_64)

**Ngày:** 13/11/2026
**Nhiệm vụ gốc:** Docker service cho camera ICSee (DOSEN RPO V1) với HTTP API:
(1) bất kỳ IP LAN nào gửi video lên màn hình cam; (2) mic + loa qua API.
**Kết quả bước 1 (bắt buộc): KHÔNG CÓ thư viện FunSDK x86_64. DỪNG theo đúng chỉ thị —
không build image giả vờ chạy được.** Tài liệu này ghi lại toàn bộ bằng chứng và
phương án thay thế đã xác minh được tới đâu.

Báo cáo nền: `~/workspace/icsee-apk/BAO-CAO.md`, `~/workspace/icsee-apk/AV-TALK-VIDEO-SEND.md`.

---

## 1. Kết luận ngắn

| Hạng mục | Kết quả | Mức chứng minh |
|---|---|---|
| libFunSDK.so x86_64 từ APK ICSee | **KHÔNG TỒN TẠI** — ICSee chỉ phát hành arm64-v8a + armeabi-v7a, không có bản x86/x86_64 | ĐÃ CHỨNG MINH (APKPure variants + Captain Droid + XAPK đã tải chỉ có split `config.arm64_v8a.apk`) |
| FunSDK cho Linux x86_64 (XM open platform / GitHub) | **KHÔNG TÌM THẤY nguồn công khai** — org `xmeye-team` trên GitHub chỉ còn 2 repo demo rỗng (size 0 KB, push cuối 2018-03-30); search web không ra SDK Linux | ĐÃ CHỨNG MINH (GitHub API + search) |
| Dùng .so Android x86_64 (nếu có) trên Linux glibc | **KHÔNG CHẠY ĐƯỢC** — libFunSDK.so cần lib Android-only: `liblog.so`, `libandroid.so`, `libmediandk.so`, `libOpenSLES.so`, `libEGL.so`, `libGLESv3.so`, `libvrsoft.so` + bionic libc | ĐÃ CHỨNG MINH (`readelf -d` trên .so arm64 đã trích; .so x86_64 — nếu có — link cùng các lib này) |
| APP key (APP_UUID/APP_KEY/APP_SECRET/APP_MOVECARD) lấy từ APK | **KHÔNG CÓ trong APK** — cả binary `AndroidManifest.xml` (check cả UTF-8 và UTF-16) lẫn manifest đã decode đều không chứa 4 key này | ĐÃ CHỨNG MINH (byte search trong APK gốc) |
| Mic (nghe tiếng cam) trên x86_64 không cần FunSDK | **KHẢ THI** — DVRIP monitor stream có audio (go2rtc `producer.go` demux cả H.264/H.265 + audio `0xFA`); RTSP 554 cũng được ghi nhận hoạt động trên cam XM | ĐÃ CHỨNG MINH (đọc source go2rtc `pkg/dvrip/producer.go`; hass-xmeye protocol doc, đã verify live trên NBD8008R-U) — **chưa verify trên cam DOSEN thật** |
| Loa (nói ra loa cam) trên x86_64 không cần FunSDK | **KHẢ THI** — DVRIP talkback audio: go2rtc `backchannel.go` gửi PCMA/PCMU 8 kHz, gói 320 byte, opcode `OPTalkData`, header `0x1FA`; sofiactl có lệnh `Talk` (file G.711 A-law) | ĐÃ CHỨNG MINH (đọc source go2rtc `pkg/dvrip/backchannel.go`; sofiactl docs) — **chưa verify trên cam DOSEN thật** |
| Video lên màn hình cam (AV talk) trên x86_64 không cần FunSDK | **CHƯA CÓ ĐƯỜNG NÀO ĐÃ BIẾT** — backchannel của go2rtc chỉ có audio (grep video trong `backchannel.go` = 0 kết quả); không có opcode gửi video nào trong DVRIP open-source | ĐÃ CHỨNG MINH (không tìm thấy trong go2rtc/python-dvr/sofiactl/hass-xmeye) |
| Chạy trên host ARM thay cho x86_64 | **KHÔNG TỰ NÓ GIẢI QUYẾT** — .so arm64 vẫn cần các lib Android-only trên; phải kèm Android runtime (Waydroid) hoặc shim libhybris — cả hai đều chưa xác minh | SUY LUẬN từ `readelf -d`; chưa thử nghiệm |

---

## 2. Bằng chứng chi tiết (bước 1)

### 2.1. Thư viện hiện có là arm64, cần lib Android-only

```
/tmp/icsee-avtalk/lib/arm64-v8a/libFunSDK.so:
  ELF 64-bit LSB shared object, ARM aarch64, stripped,
  BuildID sha1=bf2ae8f2c81cfc167fa056b3c9ae79af02e0a92d
  NEEDED: libGLESv3.so, libvrsoft.so, liblog.so, libmediandk.so,
          libOpenSLES.so, libandroid.so, libEGL.so,
          libm.so, libdl.so, libc.so
```

`liblog`, `libandroid`, `libmediandk`, `libOpenSLES`, `libEGL`, `libGLESv3`,
`libvrsoft` là lib của Android (bionic), không có trên Linux glibc — kể cả trên
host ARM. Chỉ riêng chuyện này đã đủ kết luận: **không thể `ctypes`-load .so này
trong container Linux**, bất kể arch.

### 2.2. ICSee không có bản x86_64

- XAPK 7.9.6_G đã tải (SHA-256 đã khớp APKPure) chỉ chứa split native duy nhất
  `config.arm64_v8a.apk` (55,5 MB). Không có `config.x86_64.apk`.
- APKPure liệt kê variants của mọi phiên bản iCSee/Pro: chỉ `arm64-v8a` và
  `armeabi-v7a`.
- Captain Droid: "iCSee supports arm64-v8a, armeabi-v7a. This build does not
  support x86/x86_64 processors."

### 2.3. Không có FunSDK Linux công khai

- GitHub API `orgs/xmeye-team/repos`: chỉ 2 repo — `FunSDKDemo_Android`,
  `FunSDKDemo_iOS`. Repo Android: size 0 KB, push cuối 2018-03-30, cây git rỗng.
- Search web "FunSDK Linux SDK / libFunSDK.so x86_64": không có kết quả liên quan
  (chỉ ra Solana pumpfun SDK, Vulkan SDK, v.v.).

### 2.4. APP key không trích được từ APK

`XMFunSDKManager.initXMCloudPlatform()` đòi 4 meta-data `APP_UUID`, `APP_KEY`,
`APP_SECRET`, `APP_MOVECARD` trong manifest. Kiểm tra binary
`AndroidManifest.xml` trong APK gốc (cả UTF-8 và UTF-16): cả 4 đều vắng mặt
(`APP_KEY` chỉ match chuỗi con trong `FLYME_APP_KEY`/`MIUI_APP_KEY` — không phải
key của XM). Hệ quả: **client FunSDK độc lập cần user tự đăng ký app trên
XM open platform (https://oppf.xmcsrv.com) để lấy key riêng** — không dùng được
key của app ICSee vì key đó không nằm trong APK.

### 2.5. Môi trường đã kiểm tra ở đây

- Host x86_64, Docker 29.1.3 + Compose 2.40.3, Python 3.12.3, FFmpeg 8.1.2
  (có decoder HEVC + encoder libx265/libx264 — đủ cho bước transcode).
- `pip install python-dvr` (OpenIPC) thành công trên x86_64; `DVRIPCam` import
  được, có `login`, `get_info`, `get_encode_info`, `start_monitor`/`stop_monitor`,
  `snapshot`, `ptz`, `reboot`, `send`/`recv_json` — **không có** hàm talk/audio-send.

---

## 3. Phương án thay thế — DVRIP-native (không cần FunSDK)

Đây là hướng đã được cộng đồng open-source chứng minh trên x86_64 Linux.
Nó bao phủ **mic + loa + cấu hình**, nhưng **KHÔNG bao phủ video lên màn hình**.

### 3.1. Đã xác minh được (đọc source trực tiếp)

| Chức năng | Cơ chế | Nguồn xác minh |
|---|---|---|
| Login + cấu hình cam | DVRIP TCP **34567**: header 20 byte (`0xFF` + session/seq/msg-id/len) + JSON body; login msg 1000, config get 1042 / set 1040, keepalive | OpenIPC/python-dvr (đã cài + import OK ở đây); hass-xmeye `docs/protocol.md` (verify live trên NBD8008R-U, fw V4.03.R11); xmcam-py 0.1.0 (PyPI, 10/11/2026) |
| Mic — nghe tiếng cam | DVRIP monitor stream (`start_monitor`) demux được cả video H.264/H.265 + audio (`0xFA`); hoặc RTSP `rtsp://HOST:554/user=USER&password=PASS&channel=1&stream=0.sdp?real_stream` | go2rtc `pkg/dvrip/producer.go`; hass-xmeye protocol doc |
| Loa — nói ra loa cam | DVRIP talkback: opcode `OPTalkData`, audio **G.711 A-law (PCMA) 8 kHz**, gói **320 byte**, header 8 byte (`0x1FA` BE + codec byte 14=PCMA/10=PCMU + rate byte 2=8000 + len LE) | go2rtc `pkg/dvrip/backchannel.go` (đã đọc source); sofiactl lệnh `Talk` (file G.711 A-law headless) |
| Phát hiện cam trên LAN | DVRIP broadcast (như BAO-CAO §3.1) hoặc ONVIF WS-Discovery | xmcam-py; BAO-CAO |

### 3.2. Chưa có đường nào — video lên màn hình cam

- `backchannel.go` của go2rtc: **chỉ audio** (grep video/h264/h265/yuv/frame = 0).
- python-dvr: không có hàm gửi video; chỉ `start_monitor` (nhận) + `send` generic.
- sofiactl / hass-xmeye / xmcam-py: không có tính năng gửi video lên thiết bị.
- Kết luận: **AV talk (DevStartAVTalk/DevSendAVTalkData với YUV420P) hiện chỉ
  tồn tại trong FunSDK**, chưa ai implement lại trên DVRIP công khai.

### 3.3. Các hướng khác cho video lên màn hình (chưa xác minh, chỉ là đề xuất)

1. **Bắt gói tin live (khả thi nhất):** gọi video thật từ app iCSee tới cam DOSEN,
   tcpdump/Wireshark trên LAN + logcat app. Mục tiêu: tìm opcode DVRIP/P2P của
   bước đàm phán `DecoderPram` + luồng media gửi đi (codec/bitstream trên dây),
   rồi implement lại bằng Python như go2rtc đã làm với DVRIP. Cần: cam thật +
   app + quyền bắt gói tin trên mạng nhà.
2. **ARM host + Android runtime (Waydroid):** chạy app iCSee thật trong Waydroid
   trên host ARM, rồi tự động hoá cuộc gọi video + đưa video nguồn vào camera
   ảo của Waydroid. Chưa xác minh, phức tạp, độ trễ cao.
3. **Wine + DLL Windows của XMeye PC client:** CMS trên máy Dell của user dùng
   DLL FunSDK cho Windows (x86_64). Chạy DLL đó dưới Wine trong Docker x86_64
   là hướng có thể thử, nhưng chưa xác minh DLL nào expose API AV talk, và vẫn
   cần APP key của CMS.
4. **Đăng ký XM open platform** (https://oppf.xmcsrv.com) lấy APP key riêng rồi
   xin SDK Linux/Windows chính thức từ XM — chỉ giải quyết key, không chắc có
   bản Linux.

---

## 4. Đề xuất thứ tự bước tiếp theo

1. **User quyết:** có chấp nhận làm service DVRIP-native cho **mic + loa + cấu hình**
   trước (2/3 tính năng, chạy được trên x86_64 ngay), để riêng video lên màn hình
   làm giai đoạn 2 — hay dừng toàn bộ tới khi có đường video?
2. **Probe live trên cam DOSEN thật** (cần làm trước khi viết code gửi video):
   nmap cam (port 554/34567/80), thử RTSP theo URL mẫu ở §3.1, thử DVRIP login
   bằng python-dvr (`DVRIPCam(ip, user='admin', password=...)`), đọc
   `DecoderPram` — để biết cam này thực sự mở những đường nào.
3. **Nếu vẫn muốn video lên màn hình:** làm bước bắt gói tin (hướng 1 ở §3.3)
   trong một cuộc gọi video thật — đây là việc nghiên cứu giao thức, không phải
   viết service ngay.
4. **Nếu chọn DVRIP-native:** xây service Python (FastAPI + python-dvr + FFmpeg +
   go2rtc-style backchannel) theo API đã gợi ý trong nhiệm vụ gốc, với module
   video-send để trống và ghi rõ `NOT_IMPLEMENTED: no DVRIP video-send opcode
   known`. Test được ở đây: docker build, `/api/health`, các endpoint không cần
   cam; test live (login/monitor/talk) cần user chạy với cam thật.

---

## 5. Ghi chú trung thực về phạm vi báo cáo này

- **Đã làm:** xác minh kiến trúc (arch .so, NEEDED libs, variants APK, GitHub
  xmeye-team, APP key trong manifest, FFmpeg HEVC, python-dvr import + method
  list, đọc source go2rtc `backchannel.go`/`producer.go`).
- **Không làm:** không build Docker image của service FunSDK (theo đúng chỉ thị
  dừng); không test live với cam thật (không có cam + credential ở đây); không
  khẳng định DVRIP talk/monitor chạy trên cam DOSEN cụ thể (chỉ mới chứng minh
  trên các model/firmware khác trong tài liệu open-source).
- **Không có credential thật nào** trong tài liệu này (SN, mật khẩu cam, APP key
  đều không được ghi).
