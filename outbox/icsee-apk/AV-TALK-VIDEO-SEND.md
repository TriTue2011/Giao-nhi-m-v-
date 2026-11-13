# BÁO CÁO — ĐƯỜNG GỬI VIDEO LÊN MÀN HÌNH CAMERA QUA AV TALK (iCSee 7.9.6_G)

**Ngày:** 13/11/2026
**APK:** iCSee 7.9.6_G (`com.xm.csee`), đã phân giải ở `~/workspace/icsee-apk/`
**Phương pháp:** chỉ đọc, không sửa file, không đăng nhập tài khoản nào, không gửi dữ liệu đi.
**Phạm vi:** đường VIDEO-INTERCOM (AV talk) — phía **GỬI** video từ app lên camera để hiển thị
trên màn hình tích hợp của camera (VD: DOSEN RPO V1, màn hình 2.8" + gọi video 2 chiều).
**Lưu ý phương pháp:** class `VideoEncodeManager` **không có trong bản decompile Java của jadx**
(jadx OOM ở ~87%); toàn bộ luồng gửi video dưới đây được truy vết từ **smali**
(`decompiled/apktool/smali_classes4/com/manager/device/media/encode/VideoEncodeManager*.smali`)
+ bean Java + strings của `libFunSDK.so` (34 MB, arm64, trích từ `xapk/config.arm64_v8a.apk`,
strings 97.209 dòng ở `/tmp/icsee-avtalk/FunSDK.strings`).

Báo cáo tổng trước đó: `~/workspace/icsee-apk/BAO-CAO.md` (stream live, talkback audio G.711,
FunSDK P2P/LAN, bắt buộc cloud init).

---

## 0. KẾT LUẬN NGẮN

| Câu hỏi | Kết luận | Mức chứng minh |
|---|---|---|
| Có gửi được video từ app lên màn hình cam không? | **CÓ — qua AV talk (FunSDK):** `DevStartAVTalk` (5556) → `DevSendAVTalkData` (5557) → `DevStopAVTalkData` (5558), điều khiển bằng `DevControlAVTalk` (5559). Đây đúng là cơ chế màn hình cam hiển thị video từ điện thoại khi gọi video 2 chiều. | ĐÃ CHỨNG MINH (smali + native) |
| Dữ liệu gửi lên là gì? | **Video: YUV420P thô (không phải H.264/H.265 NAL).** App lấy frame YUV_420_888 từ Camera2 qua `ImageReader`, chuyển thành `byte[]` YUV420P (`w*h*3/2` byte/khung), gửi kèm JSON `{"timestamp":"...","type":1}`. **Audio: PCM 16-bit 8 kHz mono, khung 640 byte**, gửi kèm `{"timestamp":"...","type":2}`. Native SDK (`CEncoderMgr`/`CFFMpegEncoder`) mã hoá lại trước khi truyền tới thiết bị. | ĐÃ CHỨNG MINH (Java app gửi YUV/PCM thô); SUY ĐOÁN có cơ sở mạnh (native encode lại — xem §5) |
| Có gửi video từ **nguồn LAN bất kỳ** (VD: stream RTSP từ IP khác) lên màn hình cam được không? | **Được về nguyên tắc, nhưng phải TRANSCODE:** interface `DevSendAVTalkData` chỉ nhận frame thô (YUV/PCM), **không nhận NAL H.264/H.265 có sẵn**. Nguồn video LAN phải được **giải mã → YUV → gửi**, rồi native encode lại theo codec đã đàm phán với camera. Không có đường passthrough NAL nào được tìm thấy. | ĐÃ CHỨNG MINH (không có API nhận NAL); SUY ĐOÁN có cơ sở (điểm encode trong native) |
| AV talk có hỗ trợ **H.265 (HEVC)** không? | **CÓ — ở tầng đàm phán + tầng encode native.** Thiết bị báo khả năng giải mã qua `DecoderPram.Video[].Enc` (`"H264"`/`"H265"`); app gửi `videoinfo.encodetype="H265"` + `preset=1` khi thiết bị báo H265. Native có cả encoder `libx264` **và** `libx265` (FFmpeg build trong `.so`), `CFFMpegEncoder` có tham số `X265Params`, log lỗi `Cannot open libx265 encoder.` | ĐÃ CHỨNG MINH (đàm phán + encoder tồn tại); SUY ĐOÁN có cơ sở mạnh (nhánh chọn libx265 theo `encodetype` — chưa disassembly) |
| Camera/màn hình có decode H.265 không? | **Thiết bị nào báo `Enc="H265"` trong `DecoderPram` thì decode được H.265** — đó chính là mục đích của bước đàm phán. Cờ capability `SUP_HISI_H265_DEC` (HiSilicon H.265 decode) tồn tại trong SDK. **Đường render lên màn hình LCD là firmware phía thiết bị, không thấy trong APK.** | ĐÃ CHỨNG MINH (cơ chế đàm phán); KHÔNG TÌM THẤY (pipeline render LCD) |
| Nguồn H.265 mà AV talk chỉ nhận H.264 thì sao? | **Bắt buộc transcode H.265 → YUV → H.264.** Trường hợp thiết bị đàm phán H.265 thì vẫn phải decode H.265 → YUV rồi encode lại H.265 (không passthrough). | ĐÃ CHỨNG MINH (interface chỉ nhận frame thô) |
| Luồng này có đi LAN trực tiếp được không? | **Chưa chứng minh riêng cho AV talk.** AV talk đi chung transport FunSDK với `MediaRealPlay` (P2P/LAN/relay do native chọn, mặc định mã hoá P2P). App bắt buộc `XMCloundPlatformInit` + P2P DNS `secu100.net:8765` mới chạy SDK (xem BAO-CAO §1.1). Native log `Start AVTalk,NotLogin` chứng minh phải login thiết bị trước. | SUY ĐOÁN (LAN trực tiếp) — cần bắt gói tin live để chứng minh |
| Có lệnh nào bật màn hình / chọn nguồn hiển thị trên cam không? | **KHÔNG TÌM THẤY** lệnh/config nào phía app để bật màn hình hay chọn nguồn hiển thị. Chỉ có config OSD `AVEnc.VideoWidget` (không phải LCD). Màn hình hiển thị video peer được cho là tự động khi AV talk chạy (firmware). | KHÔNG TÌM THẤY — cần test live |

---

## 1. BẢNG HÀM / CALLER (file:dòng)

### 1.1. Điểm vào native — `com/lib/FunSDK.java`

| Hàm native | Dòng | Annotation (nguyên văn) | Tham số |
|---|---|---|---|
| `DevStartAVTalk(int, String, String, int, int)` | 421 | 开启音视频对讲(Client-->Dev) / DEV_START_AV_TALK = 5556 | `hUser, szDevID, szReqJson, nTimeout, nSeq` |
| `DevSendAVTalkData(int, String, byte[], int)` | 372 | 发送音视频对讲数据(Client-->Dev) / DEV_AV_TALK_SEND_DATA = 5557 | `hUser, szFrameInfo, pAVData, nSeq` |
| `DevStopAVTalkData(int)` | 464 | 关闭音视频对讲(Client-->Dev) / DEV_STOP_AV_TALK = 5558 | `hPlayer` |
| `DevControlAVTalk(int, String, int)` | 277 | 控制音视频对讲(Client-->Dev) / DEV_CONTROL_AV_TALK = 5559 | `hPlayer, szCtrlJson, nSeq` |

Message ID (`com/lib/EUIMSG.java`): `DEV_START_AV_TALK = 5556` (:112),
`DEV_AV_TALK_SEND_DATA = 5557` (:62), `DEV_STOP_AV_TALK = 5558` (:119),
`DEV_CONTROL_AV_TALK = 5559` (:68).

**Kết quả grep quan trọng:** 4 hàm trên **chỉ xuất hiện trong `FunSDK.java` ở cây Java** —
không có caller Java nào trong bản decompile jadx. Caller thật nằm ở smali
(`VideoEncodeManager`, xem §1.2) vì jadx không decompile được class này.

### 1.2. Caller — `smali_classes4/com/manager/device/media/encode/VideoEncodeManager.smali` (4.950 dòng)

| Call site | Dòng smali | Ngữ cảnh |
|---|---|---|
| `DevStartAVTalk(l, m, Gson(EncodeCameraBean), 5000, 0)` | 4480 | trong `startVideoTalk(TextureView, EncodeCameraBean, int, boolean)` (:4270–4508); kết quả gán vào field `n` (AV talk handle) |
| `DevSendAVTalkData(n, frameInfoJson, yuvBytes, yuvBytes.length)` | 903 của `VideoEncodeManager$b.smali` | trong `onImageAvailable` (ImageReader listener) — đường VIDEO |
| `DevSendAVTalkData(n, frameInfoJson, audioBytes, len)` | 4075 | trong `onAudioDataResult(byte[], int)` (:3988–4083) — đường AUDIO |
| `DevControlAVTalk(n, ctrlJson, seq)` | 3823 | trong `controlDevAvTalk(String, int)` (:3811–3830) |
| `DevStopAVTalkData(n)` | 4552 | trong `stopVideoTalk()` (:4530–4567); sau đó `n = 0` |

**Quy ước handle (ĐÃ CHỨNG MINH):** `DevStartAVTalk` trả về handle, lưu vào field `n`;
mọi lệnh sau (`DevSendAVTalkData` / `DevControlAVTalk` / `DevStopAVTalkData`) đều dùng `n`
làm tham số đầu tiên — dù annotation ghi `hUser`/`hPlayer`. Field `l` = `hUser`
(đăng ký qua `FunSDK.GetId(l, this)` ở constructor :90–259), field `m` = device SN/ID.

### 1.3. Các class quản lý video call

| Class | Vai trò | Bằng chứng |
|---|---|---|
| `VideoEncodeManager` (smali, implements `VideoEncodeManagerInterface`) | Quản lý toàn bộ AV talk phía gửi: mở camera, encode, gửi frame, điều khiển, dừng | `smali_classes4/.../encode/VideoEncodeManager.smali`; interface Java `com/manager/device/media/encode/VideoEncodeManagerInterface.java` (`startVideoTalk(TextureView, EncodeCameraBean, int, boolean)`, `controlDevAvTalk`, `createControlCommand`, `openCamera`, `closeCamera`, `startAudioRecord`, `stopVideoTalk`…) |
| `VideoEncodeManager$a` | `CameraDevice.StateCallback` — `onOpened` → `H()` (tạo ImageReader) + `z()` (tạo capture session) | `VideoEncodeManager$a.smali:88` |
| `VideoEncodeManager$b` | `ImageReader.OnImageAvailableListener` — lấy frame YUV → gửi `DevSendAVTalkData` type=1 | `VideoEncodeManager$b.smali` toàn file (985 dòng) |
| `VideoEncodeManager$c` | `CameraCaptureSession.StateCallback` | `VideoEncodeManager$c.smali:1-2` |
| `AudioEncodeManager extends XMAudioManager` | Thu mic → forward PCM qua `OnAudioEncodeListener.onAudioDataResult` | `com/manager/device/media/encode/AudioEncodeManager.java` (`sendAudioToDev` chỉ forward, không encode) |
| `XMAudioManager` | Thu mic `AudioRecord(VOICE_COMMUNICATION, 8 kHz, PCM16)`, khung 640 byte; `WebRtcAudio.Process` (AEC/AGC/NS); gate <15 dB cho thiết bị low-power | `com/manager/device/media/audio/XMAudioManager.java:112` (`k()` :300–324 gọi `sendAudioToDev`) |
| `TalkManager extends XMAudioManager` | Chỉ làm talkback **audio** (`DevStartTalk`/`DevSendTalkData`/`DevStopTalk`, msg 5501) — **không** dùng AV talk | `com/manager/device/media/TalkManager.java` (xem BAO-CAO §2.1) |
| `VideoCallActivity` / `VoiceCallActivity` | UI gọi video 2 chiều / gọi thoại: đàm phán `DecoderPram`, dựng `EncodeCameraBean`, gọi `startVideoTalk`, gửi lệnh `video_pause`/`video_continue` | `smali_classes5/com/xworld/activity/video_call/VideoCallActivity.smali`, `VoiceCallActivity.smali` |
| `MonitorFragment` | Mở `VideoCallActivity` khi có cuộc gọi video | `smali_classes5/.../monitor/view/MonitorFragment.smali:17106` (`"VIDEO_CALL startActivity VideoCallActivity"`) |

### 1.4. Bean tham số

| Bean | Nội dung | File |
|---|---|---|
| `EncodeCameraBean` | `audioinfo`, `mediatype`, `timestamp` (luôn null → Gson bỏ qua), `videoinfo`, `protocoltype = 0`, `channel = 0`, `version = 0`, `timeout = 5000` | `com/lib/sdk/bean/encode/EncodeCameraBean.java` |
| `EncodeVideoBean` | `encodetype = "H264"`, `fps = 10`, `gopsize = 2`, `qp = 27`, `preset = 2`, `srcwidth/srcheight/dstwidth/dstheight` (mặc định 0) | `com/lib/sdk/bean/encode/EncodeVideoBean.java` |
| `EncodeAudioBean` | `encodetype = "g711a"`, `channels = 1`, `bit = 16`, `sampleRate = 8000` (`EUIMSG.JPEG_TO_MP4_ON_PROGRESS`) | `com/lib/sdk/bean/encode/EncodeAudioBean.java` |
| `DecoderPramBean` (device báo về) | `Video[].Enc` (String), `Video[].Res[].W/H/FPS`; `Audio[].Enc`, `Audio[].SB[]`, `Audio[].SR[]` | `com/lib/sdk/bean/decode/DecoderPramBean.java` |
| `AVTalkBean` / `AVTalkInnerBean` | Wrapper JSON `{"Name":…, "AVTalk":{"Action":…}}` — **không tìm thấy caller nào** (cả Java lẫn smali, chỉ có file bean) → coi như dead code trong bản này | `com/lib/sdk/bean/encode/AVTalkBean.java`, `AVTalkInnerBean.java` |

Hằng điều khiển (`com/lib/SDKCONST.java`): `AVTalkControl` :49–53 —
`kAVTalkCtrlResetEncoderInfo = "reset_encoder_info"`,
`kAVTalkCtrlVideoContinue = "video_continue"`,
`kAVTalkCtrlVideoPause = "video_pause"`,
`kAVTalkCtrlVideoSwitchingResolution = "switching_resolution"`;
`EAVTalkSendMediaType` :198–202 — `ALL = 0`, `AUDIO = 1`, `VIDEO = 2`.

---

## 2. LUỒNG GỬI VIDEO TỪNG BƯỚC (ĐÃ CHỨNG MINH)

### Bước 0 — Đàm phán capability: hỏi thiết bị decode được gì

`VideoCallActivity.d3()` (`VideoCallActivity.smali:7045–7175`):

- Tạo `DevConfigInfo` với `cmdId = 0x550` (1360), `jsonName = "DecoderPram"`,
  gửi qua `DeviceManager.getDevConfigManager(devId).setDevCmd(...)`.
- Callback `VideoCallActivity$initVideoChat$devConfigInfo$1.smali`: parse JSON trả về
  thành `DecoderPramBean` (`HandleConfigData.getDataObj(json, DecoderPramBean.class)`).
- Lỗi → retry (đếm `r2`, gọi lại `d3()`); hết lượt retry → log
  "获取DecoderPram失败,使用默认分辨率开启音视频对讲" (lấy DecoderPram thất bại,
  dùng độ phân giải mặc định mở AV talk) rồi vẫn tiếp tục với giá trị mặc định.

### Bước 1 — Dựng `EncodeCameraBean` theo capability thiết bị

Trong `VideoCallActivity` (phương thức chứa `startVideoTalk`, `VideoCallActivity.smali:9960–10480`):

- Nếu có `DecoderPramBean`: `initCameraSize(Video[0].Res[0].W, Video[0].Res[0].H)`;
  `EncodeVideoBean.fps = Video[0].Res[0].FPS` (mặc định bean = 10 nếu không có).
- `qp = 0x1b` (27); `encodetype = Video[0].Enc`, nếu null → `"H264"`.
- **Nếu `encodetype == "H265"` thì `preset = 1`** (`:10206–10238`,
  `const-string v2, "H265"` ở :10211); ngược lại giữ `preset = 2` (mặc định bean).
- `EncodeAudioBean.sampleRate = max(8000, max(Audio[0].SR[]))` (`0x1f40` = 8000).
- `mediatype = 0` khi cờ video `L = true` (mặc định `true`), `= 1` khi `L = false`
  (khớp `EAVTalkSendMediaType`: 0 = ALL, 1 = AUDIO — đây là suy đoán có cơ sở, xem §6).
- `VoiceCallActivity` làm tương tự (`VoiceCallActivity.smali:4497–5001`).

### Bước 2 — `startVideoTalk`: setup rồi `DevStartAVTalk`

`VideoEncodeManager.startVideoTalk(TextureView, EncodeCameraBean, cameraLensType, boolean)`
(`VideoEncodeManager.smali:4270–4508`):

1. Kiểm tra null (`textureView`, `encodeCameraBean`, `CameraManager`); nếu `audioinfo.sampleRate > 0`
   thì gán vào field `w`.
2. `G(cameraLensType)` (:2431–2529): duyệt `CameraManager.getCameraIdList()`, chọn camera theo
   `LENS_FACING`; rồi `B()` (:682–747) đọc `SENSOR_ORIENTATION` → field `q` (góc xoay).
3. `D(EncodeCameraBean, boolean)` (:1210–1596): lấy `StreamConfigurationMap.getOutputSizes(MediaRecorder.class)`,
   chọn kích thước khớp nhất qua `E()` rồi **ghi đè vào bean** `srcwidth/srcheight/dstwidth/dstheight`
   (hoán đổi rộng/cao theo hướng dọc/ngang); `fps > 0` → field `j` (fps gửi);
   **ghi đè `qp = 0x32` (50) và `gopsize = 4`** — bất chấp Activity đã set `qp = 27`, `gopsize = 2`.
4. `new Gson().toJson(EncodeCameraBean)` → `szReqJson`; gọi
   `DevStartAVTalk(hUser=l, devId=m, szReqJson, timeout=0x1388=5000, nSeq=0)` (:4480);
   kết quả (handle) lưu vào field `n`. Lỗi `CameraAccessException` → trả `false`.

**JSON `szReqJson` thực tế gửi đi** (Gson, field null bị bỏ — `timestamp` không xuất hiện):

```json
{
  "audioinfo": {"encodetype": "g711a", "channels": 1, "bit": 16, "sampleRate": 8000},
  "mediatype": 0,
  "videoinfo": {
    "dstheight": 480, "dstwidth": 864, "srcheight": 480, "srcwidth": 864,
    "encodetype": "H264",
    "fps": 10, "gopsize": 4, "qp": 50, "preset": 2
  },
  "protocoltype": 0, "channel": 0, "version": 0, "timeout": 5000
}
```

(Giá trị 864×480 là mặc định constructor khi thiết bị không báo `DecoderPram`;
`encodetype`/`preset` đổi thành `"H265"`/`1` khi thiết bị báo H265; `fps` theo thiết bị.)

### Bước 3 — Kết quả 5556: chỉ mở camera khi AV talk đã mở thành công

`VideoEncodeManager.OnFunSDKResult` (:2633+), nhánh `0x15b4` = 5556 (`:2684`, `cond_6`):

- `arg1 >= 0` → kiểm tra quyền `CAMERA` → `CameraManager.openCamera(cameraId, StateCallback $a, null)`,
  log "打开摄像头" (mở camera). `arg1 < 0` → log "视频对讲初始化失败:<code>" (khởi tạo AV talk thất bại).
- `onOpened` (`$a.smali:88`) → `H()` + `z()`.
- Cuối cùng báo `OnVideoEncodeListener.onStartCameraResult(boolean, w, h, …)` về Activity;
  Activity gọi `VideoEncodeManager.startAudioRecord(int)` (`VideoCallActivity.smali:8279`).

### Bước 4 — Capture: Camera2 → 2 surface song song

`H()` (:2530–2632): `ImageReader.newInstance(w, h, 0x23, 1)` — format `0x23` = 35 =
`ImageFormat.YUV_420_888`, `maxImages = 1`; gắn listener `$b`.

`z()` (:4568+): `createCaptureRequest(3)` (`TEMPLATE_RECORD`) → add 2 target:
surface của `ImageReader` (để lấy frame gửi đi) + surface của `TextureView`
(preview tự xem trên điện thoại); `C()` (:748–1210) set `CONTROL_AE_TARGET_FPS_RANGE`
từ dải FPS của camera; `createCaptureSession(...)` với callback `$c`.

### Bước 5 — Gửi VIDEO: YUV420P thô + JSON frame-info

`$b.onImageAvailable` (`VideoEncodeManager$b.smali`, toàn file):

1. `acquireLatestImage()`; điều tiết tốc độ: tính `needSendInterval z` từ fps thực tế
   (field `j` = fps, `z` mặc định 2, `C` = bộ đếm khung, `D` = timestamp bắt đầu) —
   chỉ gửi khi `A % z == 0` (field `A` = bộ đếm khung gửi).
2. `ImageYuvUtils.getBytesFromImageAsType(image, 0, q)` —
   `com/utils/ImageYuvUtils.java:11`: đọc 3 plane YUV_420_888, ghép thành `byte[]`
   kích thước `w*h*3/2`; tham số `i10 = 0` → **YUV420P planar** (Y + U + V tách riêng;
   `i10 = 1` → NV12, `i10 = 2` → NV21 — không dùng ở đây); `i11 = q` =
   `SENSOR_ORIENTATION` (xoay 90/180/270 nếu khác 0).
3. Dựng `HashMap` frame-info → Gson JSON: `{"timestamp":"<System.currentTimeMillis()>","type":1}`
   (`type = 1` = `SEND_DATA_VIDEO`).
4. `DevSendAVTalkData(handle=n, frameInfoJson, yuvBytes, yuvBytes.length)` (`$b.smali:903`).
   Lưu ý: tham số thứ 4 (khai báo là `nSeq`) thực tế được truyền bằng **độ dài `byte[]`**.

### Bước 6 — Gửi AUDIO: PCM 8 kHz + JSON frame-info

`XMAudioManager` thu mic → `k()` (:300–324): `WebRtcAudio.Process` (AEC/AGC/NS khi
full-duplex) → gate <15 dB cho thiết bị low-power → `sendAudioToDev(pcm, len)`.
`AudioEncodeManager.sendAudioToDev` forward nguyên vẹn tới
`VideoEncodeManager.onAudioDataResult(byte[], int)` (:3988–4083):

- frame-info JSON: `{"timestamp":"<millis>","type":2}` (`type = 2` = `SEND_DATA_AUDIO`).
- `DevSendAVTalkData(handle=n, frameInfoJson, pcmBytes, len)` (:4075).
- Khung PCM: 640 byte = 320 mẫu 16-bit mono @8 kHz = 40 ms (xem BAO-CAO §2.1).

### Bước 7 — Điều khiển trong lúc gọi

`controlDevAvTalk(String, int)` (:3811–3830) → `DevControlAVTalk(n, ctrlJson, seq)` (:3823),
chỉ gọi khi `n != 0`. JSON lệnh do `A(String, int, int)` (:554–681) dựng bằng fastjson:

```json
{"command": "video_pause" | "video_continue" | "switching_resolution" | "reset_encoder_info"
 [,"info": {"srcwidth": W, "srcheight": H, "dstwidth": W, "dstheight": H}]}
```

(`"info"` chỉ có khi đổi độ phân giải với w/h > 0.) Caller:
`VideoCallActivity$initListener$5$1.smali:118–188` (pause/continue khi bấm nút),
`VideoCallActivity.smali:1586–1606` (continue), `VideoEncodeManager.smali:2742, 3578–3726`
(`switching_resolution` khi đổi camera/resolution).
Kết quả 5559 (`OnFunSDKResult` `:2703`, `cond_0`): `arg1 < 0` và `seq < 2` → **tự retry**
`controlDevAvTalk(str, seq+1)`; `arg1 >= 0` và chuỗi chứa `"video_pause"` →
`listener.onVDPauseResult(true)`, ngược lại `onVDResumeResult(true)`.

### Bước 8 — Dừng

`stopVideoTalk()` (:4530–4567): `closeCamera()` → `stopAudioRecord()` →
nếu `n != 0`: `DevStopAVTalkData(n)` (:4552), `n = 0`.
Kết quả 5558 (`:2695`, `cond_4`): log "停止视频对讲:<code>" →
`listener.onStopCameraResult(arg1 >= 0)`.

---

## 3. FORMAT DỮ LIỆU GỬI — TÓM TẮT

| Kênh | Dữ liệu `pAVData` | `szFrameInfo` (JSON) | Tần suất / kích thước |
|---|---|---|---|
| Video | **YUV420P thô**, `w*h*3/2` byte/khung, đã xoay theo `SENSOR_ORIENTATION`; **không phải NAL H.264/H.265** | `{"timestamp":"<millis>","type":1}` | Mỗi `z` khung mới gửi 1 (z thích ứng theo fps; mặc định 2); mặc định 864×480, fps theo thiết bị (mặc định bean 10) |
| Audio | **PCM 16-bit mono 8 kHz thô**, 640 byte/khung (40 ms), đã qua WebRTC AEC | `{"timestamp":"<millis>","type":2}` | Liên tục khi đang talk |
| Mở phiên | — | `szReqJson` = Gson(`EncodeCameraBean`) — xem §2 bước 2 | 1 lần, timeout 5000 ms |
| Điều khiển | — | `szCtrlJson` = `{"command":…[,"info":{…}]}` | Khi bấm pause/continue/đổi res |

**Không có MediaCodec encoder nào trong code Java của đường AV talk** (grep `MediaCodec`/
`video/avc`/`video/hevc` trong `com/manager/device/media/encode/` = 0 kết quả).
Việc mã hoá nằm trong native (xem §5).

---

## 4. H.265 (HEVC) — PHÂN TÍCH BỔ SUNG

### 4.1. Kết luận H.265

1. **AV talk hỗ trợ H.265 ở cả 3 tầng: đàm phán → encode native → decode phía app.**
   Thiết bị báo `"H265"` trong `DecoderPram.Video[].Enc` thì app gửi
   `videoinfo.encodetype="H265"` + `preset=1`; native encode bằng **libx265**.
2. **Camera decode H.265 khi nó tự báo `Enc="H265"`** — đó là ý nghĩa của bước đàm phán
   `DecoderPram`. Cờ capability `SUP_HISI_H265_DEC` (HiSilicon H.265 decode) tồn tại trong SDK.
3. **Nhưng interface gửi vẫn chỉ nhận YUV thô.** Nguồn video H.265 (VD: stream RTSP H.265
   từ một IP LAN khác) **không thể đưa thẳng NAL H.265 vào `DevSendAVTalkData`**.
   Phải **decode H.265 → YUV420P → gửi**, rồi native encode lại (H.264 hoặc H.265
   tuỳ đàm phán). **Transcode là bắt buộc, không có passthrough.**

### 4.2. Bằng chứng H.265 (file:dòng)

**Tầng app Java — đàm phán + decode phía app:**

| Bằng chứng | File:dòng | Nội dung |
|---|---|---|
| `encodetype == "H265"` → `preset = 1` | `smali_classes5/.../video_call/VideoCallActivity.smali:10206–10238` (`const-string "H265"` ở :10211) | Lấy `Enc` từ `DecoderPram.Video[0]`; nếu `"H265"` thì `setPreset(1)`, ngược lại giữ mặc định `2` |
| Tương tự | `VoiceCallActivity.smali:4742` (`const-string "H265"`) | Cùng logic ở màn gọi thoại |
| Decoder app chơi được HEVC | `com/lib/decoder/XMediaDec.java:156` | `StartDec`: type `2` → `"video/avc"`, type `3` → `"video/hevc"` (MediaCodec decoder) |
| Cờ capability thiết bị | `com/lib/EFUN_ATTR.java:87` | `SUP_HISI_H265_DEC = 35` (không tìm thấy caller Java — cờ chỉ đọc phía native/config) |
| Hằng codec | `com/lib/SDKCONST.java:661,776` | `SDK_CAPTURE_COMP_H265 = 8`, `SDK_CAPTURE_VIDEO_FORMAT_H265 = 8` (không tìm thấy caller Java) |
| Bean đàm phán | `com/lib/sdk/bean/decode/DecoderPramBean.java` | `Video[].Enc` là String — nơi thiết bị báo `"H264"`/`"H265"` |

**Tầng native `libFunSDK.so` (strings, `/tmp/icsee-avtalk/FunSDK.strings`):**

| Bằng chứng | Dòng strings | Nội dung |
|---|---|---|
| FFmpeg build config | 38520 | `--enable-encoder=libx264 --enable-encoder=libx265 … --enable-decoder=h264 --enable-decoder=hevc --enable-decoder=h264_mediacodec --enable-decoder=hevc_mediacodec --enable-parser=h264 --enable-parser=hevc --enable-bsf=hevc_mp4toannexb … --enable-libx264 --enable-libx265` — **cả 2 encoder + cả 2 decoder đều có trong lib** |
| Encoder symbols | 23435–23436 | `ff_libx264_encoder`, `ff_libx265_encoder` |
| Decoder symbols | 23442, 23483 | `ff_hevc_decoder`, `ff_hevc_mediacodec_decoder` |
| x265 runtime | 24091, 37742 | `x265_api_get_169`; log `Cannot open libx265 encoder.` — chứng minh code **thử mở libx265 lúc chạy** |
| SPS/NAL H.265 | 1945–1946, 6269, 6468 | `FUNSDK_LIB::h265_decode_sps`, `h265_parse_sps`, `CMediaFile::GetH265WH`, `CMediaFile::GetNalu_H265` |
| Encoder manager | 3676, 7397–7427 | `XENCODE::CEncoderMgr` — `Init`, `InitVideoEncoder`, `InitAudioEncoder`, `Encode`, `InputData`, `AssemblyFrameInfoAndPushFrame`, `SetSwitchingResolutionInfo`, `IsEncodingPerformanceSufficient` |
| FFmpeg encoder | 7296–7309 | `XENCODE::CFFMpegEncoder` — `Encode(const unsigned char*, EMediaYUVType, int, int, SEncoderResult*)` (**đầu vào là YUV**), `Init`, `Close` |
| Log init encoder | 39486, 43048 | `CFFMpegEncoder::Init,Params[PreSet:%s,…,X265Params:%s]`; `Init[%d/%s][BitRate:%d][Fps:%d,W:%d,H:%d,Gp:%d,QMin:%d,QMax:%d,Gop:%d,Crf:%d,PreSet:%s,…]` |
| Preset | 7305, 40681, 40686, 37025 | `XENCODE::GetPreSet(EPreSet)`; preset name `"ultrafast"`, `"veryfast"`; tune `"zerolatency"` |
| Key JSON native parse | 63309, 59756, 40684, 56169, 59754, 62183, 35836, 56168 | `videoinfo/encodetype`, `videoinfo/preset`, `videoinfo/srcwidth`, `videoinfo/dstwidth`, `videoinfo/dstheight`, `videoinfo/srcheight`, `audioinfo/encodetype`, `mediatype` |
| Log AV talk start | 44157 | `CDeviceV2::OnMsg,Start AVTalk,Begin!!![%s,Timeout:%d,ReqInfo:%s,pEncodeMgr:%lu]` — encoder manager tạo từ `ReqInfo` (JSON `EncodeCameraBean`) |
| Log gửi | 46546, 39396 | `CDeviceV2::OnMsg,AVTalk[%d],SendNextData,ToDevice--->…[rate=%d]…`; `AVTalkToSendData failed!!!![State:%d,pEncoderMgr:%s]` |

### 4.3. Suy luận về nhánh chọn encoder (SUY ĐOÁN có cơ sở mạnh — chưa chứng minh bằng disassembly)

Chuỗi bằng chứng: (a) Java gửi `videoinfo.encodetype` (`"H264"`/`"H265"`) trong `ReqInfo`;
(b) native parse đúng key `videoinfo/encodetype`; (c) `CEncoderMgr::Init(ReqInfo)` tạo
video encoder; (d) `CFFMpegEncoder` hỗ trợ cả `libx264`/`libx265` và có log lỗi riêng
khi mở libx265 thất bại; (e) `preset` từ Java (`1` cho H265, `2` cho H264) đi qua
`videoinfo/preset` → `GetPreSet(EPreSet)` → tên preset (`ultrafast`/`veryfast`).
→ Kết luận có cơ sở mạnh: **native chọn libx265 khi `encodetype="H265"`, libx264 khi `"H264"`.**
Chưa chứng minh: phép so sánh chuỗi chính xác + ánh xạ `preset 1/2` → tên preset nào
(cần disassembly `CEncoderMgr::InitVideoEncoder` / `CFFMpegEncoder::Init`, xem §7).

### 4.4. Hệ quả cho nguồn video H.265 từ LAN

| Tình huống | Cần làm |
|---|---|
| Nguồn LAN là H.265, camera đàm phán **H.264** | **Transcode H.265 → YUV420P → H.264**: decode H.265 (FFmpeg `hevc` decoder có sẵn trong `.so`, hoặc MediaCodec `video/hevc`), gửi YUV qua `DevSendAVTalkData` type=1, native encode lại libx264. |
| Nguồn LAN là H.265, camera đàm phán **H.265** | Vẫn phải **decode H.265 → YUV → encode lại H.265** (libx265). Không có đường đưa NAL H.265 gốc thẳng lên thiết bị — `DevSendAVTalkData` chỉ nhận frame thô, và `CFFMpegEncoder::Encode` nhận `EMediaYUVType`. |
| Nguồn LAN là H.264 | Tương tự: decode H.264 → YUV → encode lại theo đàm phán. |
| Nguồn LAN là YUV/RGB thô (VD: frame đã decode sẵn) | Chuyển về YUV420P đúng kích thước/fps đã đàm phán rồi gửi thẳng — không cần bước decode. |

**Không tìm thấy** API nào nhận NAL pre-encoded (grep `DevSendAVTalkData` chỉ có 2 call site
đều truyền YUV/PCM thô; không có hàm `DevSendAVTalkData` biến thể nhận codec data).

---

## 5. PHÍA NATIVE — NHỮNG GÌ XẢY RA SAU `DevSendAVTalkData` (SUY ĐOÁN có cơ sở mạnh)

Java chỉ đẩy frame thô vào native; các bước sau suy ra từ symbol + log của `libFunSDK.so`:

1. `Fun_DevSendAVTalkData` (strings :4805; JNI `Java_com_lib_FunSDK_DevSendAVTalkData` :9876)
   → `XENCODE::ParseAVTalkFrameInfoJson` (:7420) parse `{"timestamp","type"}`.
2. `CEncoderMgr::InputData` (:7421) nhận frame → `CFFMpegEncoder::Encode` (YUV → bitstream).
   Video encode bằng FFmpeg `libx264`/`libx265` (preset `ultrafast`/`veryfast`, tune
   `zerolatency`, `X265Params`, `BitRate/Fps/W/H/Gop/QP/Crf` từ `ReqInfo`).
   Audio encode theo `audioinfo.encodetype` (`g711a` — encoder `CAudioEnc_G711a` đã biết
   từ BAO-CAO §2.2; điểm chuyển PCM→G711 vẫn chưa xác định Java hay native).
3. Gửi tới thiết bị qua kênh media FunSDK (log `SendNextData,ToDevice`, strings :46546);
   yêu cầu đã login (`Start AVTalk,NotLogin`, :46533).
4. Phía thiết bị nhận qua `CAVTalkPlayer` (`OnStart`/`OnMsg`, :5778–5781) — **nhưng đây là
   class phía client SDK**; firmware trong camera decode + render lên LCD là phần không có trong APK.

**Chưa chứng minh:** codec/bitstream thực tế truyền trên dây (H.264 hay H.265 NAL, có SPS/PPS
kèm không), có mã hoá P2P không (mặc định `SetP2PDataEncryptEnable` = mã hoá, BAO-CAO §1.1),
điểm encode audio chính xác. Cần bắt gói tin live khi gọi video thật (xem §7).

---

## 6. MÀN HÌNH CAM — CƠ CHẾ HIỂN THỊ (KHÔNG TÌM THẤY lệnh điều khiển)

- **KHÔNG TÌM THẤY** trong Java lẫn `.so`: lệnh bật/tắt màn hình, chọn nguồn hiển thị,
  hay config nào gắn với LCD của camera trong đường AV talk. Hit duy nhất gần nghĩa:
  `com/lib/sdk/bean/JsonConfig.java:138` `CFG_WIDEOWIDGET = "AVEnc.VideoWidget"` — đây là
  config OSD/widget của luồng encode, **không phải** điều khiển màn hình.
- **Suy đoán hợp lý (chưa chứng minh):** khi `DevStartAVTalk` thành công, firmware camera
  tự decode luồng peer (H.264/H.265 theo đàm phán) và render lên LCD của nó; app không
  gửi thêm lệnh màn hình nào. Cần test live trên camera thật (gọi video rồi quan sát màn hình)
  để xác nhận.
- Ngược lại, phía app hiển thị video của camera bằng `MediaRealPlay` lên `SurfaceView`
  (BAO-CAO §3.3) — đường này độc lập với AV talk.

---

## 7. CÁC BƯỚC CÒN THIẾU ĐỂ VIẾT CLIENT GỬI VIDEO TỪ LAN IP LÊN MÀN HÌNH CAM

Client giả lập app (VD: chạy trên server/PC, lấy video từ 1 IP LAN rồi đẩy lên màn hình cam)
cần lần lượt:

1. **Khởi tạo SDK như app:** `XMCloundPlatformInit` (cần `APP_UUID`/`APP_KEY`/`APP_SECRET` —
   xem BAO-CAO §1.1; giá trị lấy từ manifest, không có sẵn dạng dùng trực tiếp) +
   P2P DNS `secu100.net:8765`. Không có bước này SDK không chạy.
2. **Login thiết bị theo SN:** `DevLogin(hUser, devId, user, pwd, seq)` — phải login trước
   (native từ chối AV talk khi chưa login: `Start AVTalk,NotLogin`).
3. **Hỏi `DecoderPram`:** `DevConfigInfo` cmdId `0x550` (1360), jsonName `"DecoderPram"` →
   lấy `Video[0].Enc/Res[0].W/H/FPS`, `Audio[0].SR[]`. Fallback: 864×480, fps 10, H264.
4. **Dựng `EncodeCameraBean` JSON** đúng §2 bước 2 (nhớ `qp` cuối cùng là **50**,
   `gopsize` **4** — do `D()` ghi đè; `preset = 1` nếu H265 else `2`).
5. **`DevStartAVTalk(hUser, devId, reqJson, 5000, 0)`** → giữ handle `n`; **chờ message
   5556 `arg1 >= 0`** rồi mới gửi frame (app chỉ mở camera sau bước này).
6. **Chuẩn bị nguồn video LAN:** mở stream từ IP LAN (VD: RTSP) → **decode về YUV420P**
   đúng `srcwidth×srcheight` đã đàm phán (xoay theo hướng nếu cần) → gửi từng khung qua
   `DevSendAVTalkData(n, {"timestamp":"<millis>","type":1}, yuvBytes, yuvBytes.length)`,
   điều tiết theo fps (gửi mỗi `z` khung, z thích ứng). **Nếu nguồn là H.265: decode trước
   (FFmpeg `hevc` decoder / MediaCodec `video/hevc`), rồi encode lại theo đàm phán —
   xem §4.4. Không passthrough NAL.**
7. **Audio (nếu cần):** PCM 16-bit mono 8 kHz, khung 640 byte → `DevSendAVTalkData(n,
   {"timestamp":"<millis>","type":2}, pcm, len)`. Native encode G711a (theo `audioinfo`).
8. **Điều khiển:** `DevControlAVTalk(n, {"command":"video_pause"|"video_continue"|
   "switching_resolution"|"reset_encoder_info"[,"info":{…}]}, seq)`; 5559 lỗi + `seq < 2`
   → retry `seq+1`.
9. **Dừng:** `DevStopAVTalkData(n)`, chờ 5558.
10. **Chưa rõ, cần xác minh live:** transport thực tế cho AV talk có đi LAN trực tiếp
    không (hay bắt buộc P2P/relay qua cloud); bitstream trên dây là H.264 hay H.265
    khi đàm phán H265; màn hình cam có tự bật khi AV talk mở không; `mediatype`
    (0 = ALL / 1 = AUDIO) có đúng như suy đoán không.

---

## 8. BƯỚC TIẾP THEO ĐỀ XUẤT

1. **Probe live (ưu tiên cao nhất):** gọi video thật từ app tới camera DOSEN RPO V1,
   bắt gói tin trên LAN (tcpdump/Wireshark) + đọc logcat `LogUtils "[APP_VIDEO_ENCODE]->"`:
   xác nhận (a) AV talk có đi LAN trực tiếp không, (b) bitstream trên dây là H.264 hay
   H.265 NAL (khi thiết bị báo `Enc="H265"`), (c) màn hình cam hiển thị từ lúc nào,
   (d) `DecoderPram` thật của camera này báo gì (độ phân giải/fps/codec).
2. **Disassembly native (khi cần chắc chắn 100% nhánh encoder):**
   `CEncoderMgr::InitVideoEncoder` + `CFFMpegEncoder::Init` trong `libFunSDK.so`
   (xác nhận so sánh `encodetype` → libx264/libx265, ánh xạ `preset 1/2` → tên preset),
   và `ParseAVTalkFrameInfoJson` (xác nhận chỉ parse `timestamp`/`type`).
3. **Hỏi `DecoderPram` trên camera thật** qua `DevConfigInfo` (cmdId 1360) để biết chính
   xác camera DOSEN báo `Enc` nào — quyết định có cần transcode H.265→H.264 hay không.
4. **Thử nghiệm client tối giản:** dùng FunSDK (hoặc FFmpeg riêng cho bước decode nguồn)
   theo checklist §7, nguồn đầu tiên nên là YUV thô từ file (bỏ qua bước decode RTSP)
   để tách lỗi encode/decode nguồn khỏi lỗi AV talk.
5. **Không làm:** đừng giả định passthrough NAL H.265; đừng giả định màn hình cam có API
   bật/tắt riêng; đừng dùng `MediaRtspPlay`/`MediaPlayByURL` cho đường này (zero caller —
   xem BAO-CAO §1.2).

---

## 9. NGUỒN / FILE THAM CHIẾU

- Báo cáo tổng: `~/workspace/icsee-apk/BAO-CAO.md`
- Java: `~/workspace/icsee-apk/decompiled/jadx/sources/com/lib/FunSDK.java`,
  `com/lib/sdk/bean/encode/{EncodeCameraBean,EncodeVideoBean,EncodeAudioBean,AVTalkBean,AVTalkInnerBean}.java`,
  `com/lib/sdk/bean/decode/DecoderPramBean.java`,
  `com/manager/device/media/encode/{VideoEncodeManagerInterface,AudioEncodeManager}.java`,
  `com/manager/device/media/audio/XMAudioManager.java`, `com/utils/ImageYuvUtils.java`
- Smali: `~/workspace/icsee-apk/decompiled/apktool/smali_classes4/com/manager/device/media/encode/VideoEncodeManager{,$a,$b,$c}.smali`,
  `smali_classes5/com/xworld/activity/video_call/{VideoCallActivity,VideoCallActivity$initVideoChat$devConfigInfo$1,VoiceCallActivity}.smali`,
  `smali_classes5/com/xworld/activity/monitor/view/MonitorFragment.smali`
- Native: `libFunSDK.so` (trích `xapk/config.arm64_v8a.apk` → `/tmp/icsee-avtalk/lib/arm64-v8a/libFunSDK.so`,
  35.375.880 byte); strings 97.209 dòng `/tmp/icsee-avtalk/FunSDK.strings`
- Báo cáo này: `~/workspace/icsee-apk/AV-TALK-VIDEO-SEND.md`
