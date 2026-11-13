# BÁO CÁO PHÂN TÍCH APK iCSee 7.9.6_G — ĐƯỜNG LOCAL CHO CAM / MIC / MÀN HÌNH

**Ngày:** 13/11/2026
**File phân tích:** `~/workspace/icsee-apk/icsee-7.9.6_G.xapk` — 127.278.310 byte (121,4 MB),
SHA-256 `6d94ae7b80e722df55d89348b62d70a848e0596f5defceda53d4c6a023e2951a` (khớp APKPure),
package `com.xm.csee`, version 7.9.6_G, version code 79633, nhà phát triển Zhejiang JAIFY Co., Ltd.
**Phương pháp:** chỉ đọc, không sửa APK, không đăng nhập tài khoản nào, không gửi dữ liệu đi.
**Đã phân giải:** XAPK → `xapk/` (base `com.xm.csee.apk` 54,7 MB + split `config.arm64_v8a.apk` 55,5 MB
+ split locale/xxhdpi); apktool 2.12.1 xong hoàn toàn (`decompiled/apktool/`, 690 MB, 68.310 file smali);
jadx 1.5.2 chạy tới ~87% (30.743 class, 26.855 xong) thì bị OOM-kill ở bước cuối nhưng đã ghi
35.230 file `.java` (248 MB) trong `decompiled/jadx/sources/` — đủ phân tích.
Native `libFunSDK.so` (34 MB, arm64) trích từ split arm64, `strings` 97.209 dòng.
**Lưu ý:** tên class Java bị obfuscate 1 ký tự nhưng string còn nguyên; một số method callback
(`TalkManager.OnFunSDKResult`, `DeviceManager.OnFunSDKResult`) bị lỗi decompile nên không đọc được từ Java.

---

## 0. KẾT LUẬN TỔNG QUÁT — TRẢ LỜI NGẮN GỌN

| Câu hỏi | Kết luận | Mức chứng minh |
|---|---|---|
| Có đường xem camera local không qua cloud không? | **CÓ, một phần** — media có thể đi LAN trực tiếp qua FunSDK, nhưng app **bắt buộc khởi tạo nền tảng cloud XM** mới chạy (`XMCloundPlatformInit`, thiếu thì throw lỗi) và cần P2P DNS `secu100.net:8765` để bắt tay. Không có đường nào trong app hoàn toàn offline. | ĐÃ CHỨNG MINH (code Java + native) |
| Có URL RTSP local để VLC/ffmpeg/HA kéo stream không? | **KHÔNG tìm thấy URL hoàn chỉnh nào.** RTSP client có trong native SDK (`CRtspClient`, FFmpeg rtsp demuxer) nhưng `MediaRtspPlay` **zero caller Java**, không có URL mẫu, không có port 554 gắn với camera. | ĐÃ CHỨNG MINH (grep toàn cây) |
| Có HTTP-FLV / HLS local không? | **KHÔNG.** `.flv` = 0 kết quả cả Java lẫn `.so`. HLS/m3u8 chỉ cho xem lại video cloud (`pub-dss-hls.secu100.net:8080`). | ĐÃ CHỨNG MINH |
| Có ONVIF không? | **Chỉ ở dạng cấu hình phía thiết bị** (bật/tắt + mật khẩu), app **không có ONVIF client**, không có port ONVIF trong code, chuỗi `onvif` **không có** trong `libFunSDK.so`. Mục ONVIF trên UI đang bị ẩn (`visibility="gone"`). | ĐÃ CHỨNG MINH |
| Có HTTP API local trên camera không? (`/cgi-bin`, `/api/`, snapshot.cgi…) | **KHÔNG tìm thấy.** Không có URL `http://192.168…`, `:80/:8080/:8000/:37777`, `/cgi-bin`, `/api/` hay `snapshot.cgi` nào trỏ tới camera. Điều khiển qua lệnh JSON P2P theo DevId/SN (`DevCmdGeneral`). | ĐÃ CHỨNG MINH |
| Có talkback / mic 2 chiều local không? | **CÓ** — qua FunSDK (`DevStartTalk` → `DevSendTalkData` → `DevStopTalk`), codec **G.711 A-law, 8 kHz mono**, chung kênh media P2P, **không có port/kênh riêng cho audio**. | ĐÃ CHỨNG MINH |
| Có API nào cho client ngoài lấy audio/ảnh local không? | **KHÔNG.** App chỉ là client FunSDK P2P. Snapshot = chụp frame đã giải mã trong player (`MediaSnapImage` → JPEG), không qua HTTP. | ĐÃ CHỨNG MINH |
| Discovery LAN kiểu gì? | **Broadcast DVRIP trong native libFunSDK** (`H264_DVR_SearchDevice` + `NET_SendBroadcastData`), **không** mDNS/SSDP/UPnP. **Port UDP discovery và format gói tin CHƯA xác định được** — không bịa. | ĐÃ CHỨNG MINH (cơ chế); CHƯA CHỨNG MINH (port/format) |
| Port local duy nhất gắn chắc với camera | **34567** (login TCP khi camera ở chế độ AP: `192.168.10.1:34567`) và **9001** (loại socket/bulb: `172.16.10.1:9001`), login `admin` / mật khẩu rỗng. | ĐÃ CHỨNG MINH |
| Thứ tự ưu tiên LAN → P2P → relay? | **CHƯA CHỨNG MINH.** `connectType` mặc định = IP(2) nhưng không có code Java nào đọc/ghi ngoài giá trị mặc định; việc chọn transport nằm trong `.so` đã strip. | SUY ĐOÁN có cơ sở, chưa chứng minh |

---

## 1. STREAM CAMERA LOCAL

### 1.1. Đường xem live chính — FunSDK proprietary qua device SN (ĐÃ CHỨNG MINH)

App xem live **không dùng RTSP/HTTP-FLV/HLS trực tiếp tới camera**. Đường live duy nhất có caller trong Java:

- `sources/com/manager/device/media/monitor/MonitorManager.java:223` — `startMonitor()`:
  `FunSDK.MediaRealPlay(this.f12473h, this.f12474i.getDevId(), this.f12474i.getChnnel(), this.f12474i.getStreamType(), this.f12472g, 0);`
  (`getDevId()` = device SN/ID, `getChnnel()` = kênh, `getStreamType()` = chất lượng theo
  `sources/com/lib/EDEV_STREM_TYPE.java`: `FD=0, SD=1, HD=2, FHD=3, SUD=4`.)
- `sources/com/lib/FunSDK.java:929-931` — `MediaRealPlayEx(..., boolean bEnableSharedMediaLink, ...)`
  (annotation "实时预览,兼容MediaRealPlay" — xem trước thời gian thực). Caller: `sources/a7/C0820b.java:806,864`.
- `MonitorManager.java:211` — stream thô: `FunSDK.DevReturnRealStream(hUser, devId, channel, streamType, 0)`.
- Login thiết bị theo SN, không theo IP: `FunSDK.java:349` `DevLogin(hUser, szDevId, user, pwd, seq)`;
  `:498` `DeviceLoginEx(hUser, szDevId, seq)`; `:430,490-495` `DevStartLocalDevWakeUp` / `DevWakeUp` / `DevWakeUpExt`
  (wake-up thiết bị, msg 5142). Lưu ý: grep `FunSDK.DevLogin` / `DevGetConnectType` không thấy caller Java trực tiếp —
  lời gọi đi qua lớp `DeviceManager`/`DevDataCenter` đã obfuscate hoặc qua native; bản thân các hàm native thì có thật.
- Wrapper Java chính: `sources/com/lib/FunSDK.java` (~1.695 dòng khai báo native), `com/lib/sdk/*`, `com/manager/*`.
  (Thư mục `demo/xm/com/libxmfunsdk/` chỉ chứa các file `R$*.java`, không phải wrapper thật.)

**Transport do native tự chọn, Java không quyết định (ĐÃ CHỨNG MINH):**

- Kiểu kết nối (`sources/com/manager/db/Define.java:13-19`): `CONNECT_TYPE_P2P = 0`, `CONNECT_TYPE_TRANSMIT = 1`
  (relay/chuyển tiếp), `CONNECT_TYPE_IP = 2`, `CONNECT_TYPE_RPS = 5`, `CONNECT_TYPE_RTS_P2P = 6`, `CONNECT_TYPE_RTS = 7`.
  Mặc định trong `sources/com/lib/sdk/struct/SDBDeviceInfo.java:38`: `public int connectType = 2;` (= IP).
  **Nhưng không tìm thấy code Java nào đọc/ghi `connectType` ngoài giá trị mặc định này** → việc chọn P2P vs IP vs relay nằm trong native.
- Native `.so` chứa cả 3 transport: `MNetSDK::CNetTCP`, `CNetXMP2P`, `CNetTransport`, `CNetServerP2P`
  (kèm `SetP2PServerInfo`, `InitP2PServer`, `SP2PServerInfo`, `GetNetIPBySN`),
  `Fun_SetP2PDataEncryptEnable` (`FunSDK.java:1189-1190`, annotation "设置p2p数据交互加密开关 *默认:加密*" — P2P mặc định mã hoá),
  `EFUN_ATTR.java:70-71,82` `QUERY_P2P_STATUS_ENABLE`, `SET_P2P_PROXY_SUPPORT_HD`.
- Cache credential local trong native: `Fun_DevSetLocalUserNameAndPwd`, `Fun_DevGetLocalPwd`, `Fun_DevSetLocalEncToken`,
  `Fun_DevGetLocalPwd`…; message hệ thống: `DEV_GET_CONNECT_TYPE`=5151, `DEV_GET_LAN_ALARM`=5132,
  `GET_LOCAL_DEVINFO`=8943, `SYS_GET_LOCAL_DEV_STATE`=5215, `ADD/REMOVE_DEVICES_TO/FROM_LAN_IP_BLOCK_LIST`=5168/5169.

**Bắt buộc cloud thì SDK mới chạy (ĐÃ CHỨNG MINH):**

- `sources/com/manager/XMFunSDKManager.java:222-271` `initXMCloudPlatform()` đọc `APP_UUID`/`APP_KEY`/`APP_SECRET`/`APP_MOVECARD`
  từ manifest meta-data rồi gọi `FunSDK.XMCloundPlatformInit(...)` (`FunSDK.java:1615`); thiếu thì throw
  "XM云平台初始化（必须调用，否则无法正常使用SDK）… https://oppf.xmcsrv.com/ …".
  → App không có chế độ hoàn toàn offline; ít nhất bước khởi tạo + P2P DNS vẫn cần cloud.

### 1.2. RTSP (ĐÃ CHỨNG MINH — client có trong SDK, app không dùng để xem live)

- `sources/com/lib/FunSDK.java:938` — native `MediaRtspPlay(int, String url, int, String, Object, int)` tồn tại,
  nhưng **grep toàn bộ sources: ZERO caller Java** (ngoài định nghĩa).
- `sources/com/lib/FunSDK.java:922` — `MediaPlayByURL` / `MediaPlayByURLEx` / `MediaPlayByURLV2` cũng **zero caller Java**.
- Chuỗi `rtsp://` duy nhất trong Java là pattern của AndroidX, không liên quan camera:
  `sources/androidx/core/text/util/LinkifyCompat.java:110`, `androidx/core/util/PatternsCompat.java:26`.
  ("rtsp" xuất hiện trong 22 file Java — phần lớn là tên hằng/bean như `NET_RTSP`, `MainRtspUrl` — không phải URL.)
- Trong `libFunSDK.so` (strings): class `CRtspClient` đầy đủ (symbols `DoOption/DoDescribe/DoSetup/DoPlay/DoPause/DoTeardown/OnMediaData`),
  FFmpeg `ff_rtsp_demuxer/muxer`, format string `rtsp://%[^:]:%d/`, `rtsp://%[^/]/`.
  → RTSP client tồn tại trong SDK (phục vụ `MediaRtspPlay` và/hoặc kênh decoder), nhưng **không tìm thấy URL mẫu hoàn chỉnh nào,
  không tìm thấy port mặc định 554** — port chỉ là placeholder `%d`.
- `sources/com/lib/sdk/bean/Decoder.java:14,20` — bean cấu hình phía thiết bị có `MainRtspUrl`, `SubRtspUrl`, `IPAddress`,
  `Port`, `Protocol`, `UserName`, `PassWord`. **Không có code Java nào đọc các getter này**
  (grep `getMainRtspUrl`/`getSubRtspUrl`: không kết quả) → đây là cấu hình để NVR/decoder của XiongMai kéo stream RTSP
  từ IPC bên ngoài, không phải đường xem live của app.
- `sources/com/lib/ECONFIG.java:212,346` — `NET_RTSP` (config id); `sources/com/lib/SDKCONST.java:1189,1273,1489` —
  `SDK_NET_SERVER_TYPES_RTSP`, `SDK_OTHER_RTSP_CLIENT_SUPPORT`, `E_SDK_CONFIG_NET_RTSP = 81`. Chỉ là hằng số capability/config.
- **KHÔNG TÌM THẤY:** URL dạng `rtsp://<ip-cam>:554/...` hoàn chỉnh; port 554 gắn với camera.
- **SUY ĐOÁN (chưa chứng minh):** RTSP client trong `.so` có thể được native SDK dùng nội bộ cho một số kênh decoder/NVR;
  không có bằng chứng nó được app gọi cho live view camera iCSee.

### 1.3. HTTP-FLV / HLS / HTTP stream

- **HTTP-FLV: KHÔNG TÌM THẤY** — grep `.flv`/`flv://` toàn sources và toàn bộ `.so`: 0 kết quả.
- **HLS/m3u8: chỉ cho phát lại cloud, không phải live local — ĐÃ CHỨNG MINH:**
  - `sources/com/lib/FunSDK.java:889,922` — `MediaDownloadM3u8ByUrl`, `MediaPlayM3u8ByUrl`
    (annotation "通过M3u8 url播放视频"), **zero caller Java**.
  - `.so` strings: `CloudMediaSearchCssHls`, `MC_CloudMediaSearchCssHls`, `CM3u8UrlTalker`, `AS_QueryCloudVideoHlsUrl`,
    và URL **`http://pub-dss-hls.secu100.net:8080`** (dòng 37001, cạnh `caps.jftechws.com:80`). DSS/CSS = cloud storage → HLS dùng cho xem lại video cloud.
- Không có URL HTTP live nào trỏ tới camera; các URL `http(s)://` trong Java đều là API cloud (mục 6).

### 1.4. ONVIF (ĐÃ CHỨNG MINH — capability/cấu hình phía THIẾT BỊ, app không có ONVIF client)

Đúng 9 file chứa `onvif`:

- `com/lib/ECONFIG.java` (`ABILITY_ONVIF_SUB_PROTOCOL`, `:425`, id 154),
  `com/lib/sdk/bean/JsonConfig.java:358-359` (`NetWork.OnvifPwdCheckout`, "onvif密码检查开关配置" — công tắc kiểm tra mật khẩu ONVIF)
  và `:382` (`OEM_CFG_Correspondent`, "Onvif服务配置"),
  `com/lib/sdk/bean/NetWorkOnvifPwdCheckout.java`,
  `com/lib/sdk/bean/SystemFunctionBean.java:55,72,174,209` (`NetServerFunction.ChangeOnvifEnable`, `OnvifPwdCheckout`;
  `OtherFunction.SupportOnvifClient`, `Supportonviftitle`),
  `com/lib/SDKCONST.java:1224,1259` (`SDK_OTHER_ONVIF_CLIENT_SUPPORT`, `SDK_OTHER_SUPPORT_CHANGE_ONVIF_PORT`),
  `com/manager/db/DevDataCenter.java:829-830,884-885` (`isSupportSupportOnvifClient()` đọc `OtherFunction.SupportOnvifClient`),
  `com/xm/csee/R.java:9610`, `p4/C3847w.java:76-77`.
- UI: `apktool/res/layout/activity_nvr_pc_connect.xml:13` — item `lsiOnvifEnable` (title `TR_OnvifEnableOnvif`) trên màn hình
  **"NVR PC connect"** (nối NVR với phần mềm PC), và `android:visibility="gone"` — **đang bị ẩn**.
- **KHÔNG TÌM THẤY:** chuỗi `onvif` trong `libFunSDK.so` và toàn bộ `.so` còn lại (grep 0 kết quả);
  không có port ONVIF nào (không có số port nào gắn với ONVIF trong code); không có code discovery/client ONVIF.
- **SUY ĐOÁN:** `SupportOnvifClient` nghĩa là một số đầu NVR/base station của XM có thể làm ONVIF client kéo IPC khác;
  còn camera iCSee thì expose ONVIF server để bật/tắt + đặt mật khẩu — app chỉ cấu hình, không tự xem qua ONVIF.
  → Muốn biết camera nhà Việt có bật ONVIF ở port nào, phải probe trực tiếp trên mạng LAN (nmap/ONVIF probe), code APK không cho biết.

### 1.5. Port local của camera

| Port | Kết quả |
|---|---|
| **34567** | **ĐÃ CHỨNG MINH** — AP trực tiếp của camera: `XMWifiManager.java:646-647` (`192.168.10.1:34567`) và strings `libFunSDK.so:52546`. Đây là port duy nhất gắn chắc với camera. Xem mục 3.2. |
| **9001** | **ĐÃ CHỨNG MINH** — AP trực tiếp, AP type 1/2/3 (socket/bulb): `XMWifiManager.java:643-644` (`172.16.10.1:9001`). |
| 554 | **KHÔNG TÌM THẤY** gắn với camera (chỉ xuất hiện trong các resource ID dạng `2131820554` — không phải port). |
| 80 / 8080 / 8000 / 9000 / 37777 / 34599 / 8800 | **KHÔNG TÌM THẤY** làm port camera. `8080` chỉ là port cloud HLS (`pub-dss-hls.secu100.net:8080`); `8800/9000/5554/5540-5549` là **message ID nội bộ** `EUIMSG.java` (vd `SHADOW_SERVICE_GET_DEV_CONFIGS = 8800`, `DETECT_IPV6_ONLY_NETWORK = 9000`), không phải port TCP. |
| Cloud ports (`.so` strings) | `secu100.net` access: 6602/6603/6609/6614/6616; `pub-status.secu100.net`: 7700–7706; `pub-cfg`: 8086; `pub-dsm`: 8380; `pub-dss-hls`: 8080; `new-shadow-server`: 8386; `upgrade`: 8083. |

---

## 2. MIC / ÂM THANH 2 CHIỀU (TALKBACK)

### 2.1. Talkback / đàm thoại 2 chiều — ĐÃ CHỨNG MINH (cả 3 tầng: capability → UI → FunSDK)

- Capability thiết bị: `com/lib/sdk/bean/SystemFunctionBean.java:205` `SupportTwoWayVoiceTalk`, `:222` `Talk`, `:106` `NotSupportTalk`;
  `com/manager/db/DevDataCenter.java:889` `isSupportTalk()`, `:694` `isSupportNotSupportTalk()`.
  Quyền chia sẻ: `com/lib/sdk/bean/share/Permission.java:13` `DEVICE_PERMISSION_INTERCOM = "DP_Intercom"`,
  `com/lib/sdk/struct/SDBDeviceInfo.java:188` `hasPermissionIntercom()`.
  Chế độ kết nối: `com/lib/SDKCONST.java:97` `ConnectMode.talkbackconn = 1`;
  máy trạng thái `SDKCONST.java:1650` `VoiceIntercomState` (INIT_S/PREPARE_S/RECORDING/PAUSE…).
- UI live: `com/xworld/activity/monitor/listener/MonitorBottomContract$IMonitorBottomPresenter.java:33` `isSupportIntercom()`,
  `IMonitorBottomView.java` `setIntercomTouchListener/setIntercomEnable/clearIntercomState`;
  `MonitorManager.java:56` tạo `TalkManager`, `:240–274` `start/stopTalkByDoubleDirection/HalfDuplex`, `:102` xử lý message `5501` (kết quả mở talk).

**Luồng mic → camera (uplink), class chính `com/manager/device/media/TalkManager.java` (extends `XMAudioManager`):**

- Mở talk: `TalkManager.java: s()` → `FunSDK.DevStartTalk(userId, devId, G.ObjToBytes(new SDevTalkParams()), 0)`;
  tham số `com/lib/sdk/struct/SDevTalkParams.java`: `st_3_nSampleRate = 8000`, `st_4_nSampleBits = 16`, `st_5_nChannels = 1`, `st_1_nDevChannel = -1`.
- Gửi tiếng: `TalkManager.java:108` `sendAudioToDev()` → `FunSDK.DevSendTalkData(devId, pcmBytes, len)` (chỉ gửi khi đang talk).
- Dừng: `sendStopTalkCommand()` → `FunSDK.DevStopTalk(hTalkHandle)` + `MediaSetSound(hTalkHandle, 0, 0)` + `SetFunIntAttr(6, -1)`.
- API native trong `com/lib/FunSDK.java`: `DevStartTalk` `:435` ("开启对讲功能，异步消息id=5501"), `DevSendTalkData` `:374`,
  `DevStopTalk` `:475`, `DevStarTalk` `:412` (deprecated, "使用DevStartTalk代替"),
  và biến thể video-intercom `DevStartAVTalk` `:421` (DEV_START_AV_TALK=5556), `DevSendAVTalkData` `:372` (5557),
  `DevStopAVTalkData` `:464` (5558), `DevControlAVTalk` `:277` (5559).

**Thu mic trong app — `com/manager/device/media/audio/XMAudioManager.java`:**

- `:112` `new AudioRecord(7, sampleRate, channel, format, minBufferSize)` — source `7` = `VOICE_COMMUNICATION`,
  format `2` = PCM 16-bit; sample rate mặc định `f12537p = EUIMSG.JPEG_TO_MP4_ON_PROGRESS = 8000` (`com/lib/EUIMSG.java:148`);
  đọc từng khung **640 byte** (= 320 mẫu 16-bit mono @8 kHz = 40 ms).
- `:118–124` `AcousticEchoCanceler.create(sessionId)` + `setEnabled(true)`; `:128–130` `AudioManager.setMode(2)` (MODE_IN_COMMUNICATION), `setSpeakerphoneOn(false)`.
- Chống vọng WebRTC: `initWebRTCAudio()` `:263–289` — video-intercom `FuncBit=7`, one-way `FuncBit=6`, two-way `FuncBit=7` + AEC;
  `k()` gọi `WebRtcAudio.Process()` (`com/lib/WebRtcAudio/WebRtcAudio.java`: `Init/Process/AecProcess/AgcProcess/NsProcess/UnInit`, toàn native).
  Thêm đổi giọng SoundTouch: `i()`/`setSpeakerType()` — nam −4, nữ +4 semitone (`AudioProcess.STInit/STChangeVoice`).
- 2 chế độ: `TalkManager.startTalkByDoubleDirection()` (`f12524c=2`, full-duplex, hằng `XMAudioManager.FULL_DUPLEX=2`)
  và `startTalkByHalfDuplex()` (`f12524c=1`, tắt tiếng downlink `MediaSetSound(handle,0,0)` rồi `t()` gửi `OPTalkBean.Action="PauseUpload"` /
  `u()` `"ResumeUpload"` qua `DevCmdGeneral(…, EDEV_JSON_ID.OPTALK_REQ, …)`).
- Gate tiết kiệm pin: `XMAudioManager.n()` — thiết bị low-power mà mức âm < 15 dB thì khung bị hủy
  (log "If the score is lower than 15, the audio data is discarded.").

### 2.2. Codec âm thanh — ĐÃ CHỨNG MINH: G.711 A-law, 8 kHz mono

- Java: `com/lib/sdk/bean/encode/EncodeAudioBean.java:7` `encodetype = "g711a"`, `channels = 1`, `bit = 16`, `sampleRate = 8000`;
  `com/lib/sdk/bean/OPFileBean.java:49` `AudioFormat.encodeType = "G711_ALAW"`.
- Native `libFunSDK.so` (strings): `CAudioDec::Encode_g711a / Encode_g711u`, `g711a_Decode / g711u_Decode`, `ulaw2linear2`,
  class `CAudioDec_G711a / CAudioDec_G711u`, `XENCODE::CAudioEnc_G711a / CAudioEnc_G711u`, `Fun_PcmEncodeToG711`,
  và 2 buffer tên `s_szAppTalkPcm` / `s_szDevTalkPcm`. Java cũng có `FunSDK.java:1087` `PcmEncodeToG711(byte[], int)` (native).
- **SUY ĐOÁN (có cơ sở, chưa chứng minh điểm chuyển đổi):** PCM 16-bit từ `AudioRecord` được mã hoá thành G.711 A-law trong native
  trước khi `DevSendTalkData` đẩy đi. Cơ sở: 3 chứng cứ trên khớp nhau. Nhưng **không tìm thấy caller Java nào của `PcmEncodeToG711`**
  (grep toàn `com/` trừ `FunSDK.java` = 0 kết quả), và `SDevTalkParams` không có trường codec — nên không khẳng định được việc encode
  xảy ra ở Java hay trong native `DevSendTalkData`.
- Codec khác có mặt trong native nhưng **không gắn với talkback**: bộ giải ADPCM (`CAudioDec::adpcm_decoder`, `ms_adpcm_dec`),
  bộ mã AAC dùng faac (`XENCODE::CAudioEncEnc_AAC`, `faacEncOpen/faacEncEncode/faacEncClose`), MP3 (`AP_PCMEncoder2MP3`, `FUN_Mp3Decoder2PCM`).
  **Không tìm thấy** symbol codec Opus nào trong `libFunSDK.so`; chuỗi `audio/opus` chỉ xuất hiện trong code quảng cáo Google/Media3 ở tầng Java,
  không liên quan FunSDK. **Không tìm thấy** `AAC`/`OPUS` nào trong code talkback Java.

### 2.3. Luồng audio local — ĐÃ CHỨNG MINH: chung kênh media P2P của FunSDK, không có kênh/port riêng cho audio

- Uplink và downlink đều đi qua FunSDK bằng `devId` + handle, **không có socket/IP/port nào trong code Java**.
- Downlink (nghe camera): `MonitorManager.java:223` `FunSDK.MediaRealPlay(hUser, devId, channel, streamType, surface, 0)` tạo play-handle
  cho luồng live; bật/tắt tiếng camera bằng `FunSDK.MediaSetSound(playHandle, 100/0)` — `MediaManager.java:712` `openVoiceBySound()`,
  `:484` `closeVoiceBySound()`, `:909` `EOA_PCM_SET_SOUND=100`. Tức audio về cùng luồng real-time với video, giải mã trong native
  (`CStream::AudioInfoOpr/SetAudioFrameDate`, `CDecoder::OnAudioData`, `CAudioDecBase::InitAudioDec/Decode`, struct `FRAME_INFO`).
- **KHÔNG TÌM THẤY** port/protocol riêng cho audio (grep `554/8800/34567/37777` trong strings không ra port audio;
  chỉ có template RTSP `rtsp://%[^:]:%d/` không kèm port cố định). RTSP trong native là **client** của app
  (`CRtspClient::OnMediaData`, `FunSDK.java:938` `MediaRtspPlay`), không phải server audio của camera.

### 2.4. Thu âm / ghi âm — ĐÃ CHỨNG MINH một phần; KHÔNG có file ghi riêng cho đàm thoại

- **Không có `MediaRecorder` trong toàn bộ `com/manager`, `com/lib`, `com/xworld`** (grep = 0). Không có code nào lưu riêng cuộc đàm thoại thành file audio.
- Ghi hình live (kèm tiếng nếu đang mở): `MediaManager.java:1139–1150` `startRecord(dir)` → `setTempSaveVideoPath(dir + "/" + yyyyMMddHHmmss + ".mp4")`
  → `FunSDK.MediaStartRecord(playHandle, path, 0)`; `stopRecord()` `:1173–1185` → `MediaStopRecord`.
  **SUY ĐOÁN:** audio của talk có thể nằm trong file MP4 này (do ghi từ cùng play-handle) — chưa chứng minh vì muxing nằm trong native.
  Ngoài ra `MonitorManager.java:178` `saveRealTimeStream()` → `FunSDK.DevSaveRealTimeStream()` (lưu stream thô, định dạng do caller quyết).
- Thu mic vào bộ nhớ (không ghi file): `XMRecordingManager.java` / `XMRecordingManagerV2.java` — `AudioRecord(1=MIC, 8000, mono, PCM16)`,
  gom vào `ByteBuffer`, trả qua `onComplete(ByteBuffer, size)`; `AudioEncodeManager.java` thu mic rồi đẩy PCM thô qua
  `OnAudioEncodeListener.onAudioDataResult` (consumer chưa truy vết). `com/xworld/manager/RecordingManager.java:55` tương tự (`AudioRecord(7, …)`).
  Các class này phục vụ voice-message / audio tuỳ chỉnh, không phải ghi đàm thoại.
- Helper chuyển đổi tồn tại nhưng chưa gắn với talk: `AudioProcess.PCMEncoder2MP3`, `STProcessWavFile` (PCM→MP3/WAV).

### 2.5. Quyền — ĐÃ CHỨNG MINH (manifest + check), KHÔNG TÌM THẤY chỗ xin quyền runtime

- `apktool/AndroidManifest.xml:53` `<uses-permission android:name="android.permission.RECORD_AUDIO"/>`, `:58` `MODIFY_AUDIO_SETTINGS`;
  `:389` có activity `com.xworld.devset.idr.AudioAndVideoActivity`.
- Check quyền duy nhất tìm thấy: `XMAudioManager.java:107–110` — `ContextCompat.checkSelfPermission(ctx, "android.permission.RECORD_AUDIO") != 0`
  → log `"Record Permission Not Open"`, trả `false`, không mở luồng talk.
- **KHÔNG TÌM THẤY** lệnh `requestPermissions` / `PermissionUtils` xin `RECORD_AUDIO` trong code app (`com/xworld`, `com/manager`, `com/mobile`);
  chỉ thấy nhóm `MICROPHONE = {RECORD_AUDIO}` trong thư viện blankj (`com/blankj/utilcode/constant/PermissionConstants.java:22`)
  mà không lần ra call-site trong app. Kết luận: app khai báo + kiểm tra quyền, nhưng điểm xin quyền runtime không xác định được
  từ bản decompile này (có thể nằm trong code obfuscate chưa lần ra — không khẳng định là "không có").

### 2.6. API cho client ngoài lấy audio local — KHÔNG TÌM THẤY

- Không có HTTP endpoint, socket server, hay API nào trong app cho client ngoài lấy audio từ camera. App chỉ là client FunSDK P2P.
- Những gì có liên quan nhưng **không phải** API audio cho bên ngoài: `FunSDK.java:938` `MediaRtspPlay` (app phát một URL RTSP với tư cách client);
  `com/lib/sdk/bean/Decoder.java` `MainRtspUrl/SubRtspUrl` (bean cấu hình decoder/NVR);
  `ECONFIG.NET_RTSP`, `JsonConfig` `NetWork.OnvifPwdCheckout`, `SystemFunctionBean` `SupportOnvifClient/Supportonviftitle/ChangeOnvifEnable`,
  `SDKCONST` `SDK_OTHER_RTSP_CLIENT_SUPPORT / SDK_OTHER_ONVIF_CLIENT_SUPPORT / SDK_OTHER_SUPPORT_CHANGE_ONVIF_PORT`.
  **Không tìm thấy** giá trị port RTSP/ONVIF nào trong Java (`RtspPort`/`OnvifPort` = 0 kết quả).
- **SUY ĐOÁN:** client ngoài muốn lấy audio phải dùng RTSP/ONVIF server của bản thân camera (nếu thiết bị bật)
  hoặc phiên FunSDK P2P — cả hai đều không do app này cung cấp, và APK không chứa bằng chứng nào về việc app relay audio ra ngoài.

---

## 3. LAN DISCOVERY + ENDPOINT LOCAL + MÀN HÌNH / PREVIEW

### 3.1. LAN discovery — ĐÃ CHỨNG MINH: broadcast DVRIP trong native libFunSDK, KHÔNG phải mDNS/SSDP/UPnP

**Điểm vào Java:**

- `com/manager/device/DeviceManager.java:729-732` — `searchLanDevice(OnSearchLocalDevListener)` → `FunSDK.DevSearchDevice(this.f12317g, 0, 0);`
  (không tham số IP/port/timeout ở tầng Java)
- `DeviceManager.java:127-129` — callback `OnSearchLocalDevListener.onSearchLocalDevResult(List<XMDevInfo> list)`
- `com/lib/FunSDK.java:367` — `public static native int DevSearchDevice(int, int, int);`
- `com/lib/FunSDK.java:347` — `DevLANSearch` — annotation: "[sync]局域网搜索设备", param `(String szDevId, int nTimeout, byte[] pDevInfo)`
- `com/lib/FunSDK.java:344` — `DevIsSearched` — "[sync]判断设备是否在局域网内（不进行局域网搜索" (kiểm tra LAN mà không search)
- `com/lib/EUIMSG.java:102` — `DEV_SEARCH_DEVICES = 5126` (mã message trả kết quả search)

**Trong `libFunSDK.so` (đã chứng minh):**

- `CDataCenter::SearchDevices`, `CDataCenter::RigorousSearchDevices`, `CDeviceBase::SearchDevices / SearchDevicesEx`,
  `Dev_SearchDevices`, `CConfigAPDev::SearchDevicesBySn`, `CLocServer::GetDevByName/GetDevById`
- `NET_SendBroadcastData`, `DVRIP_MSG_HEAD_T`, và qua `nm -D`: `H264_DVR_SearchDevice` (0xc23924), `H264_DVR_SearchDeviceEX`,
  `H264_DVR_SearchDevice_V2` — đây là API search kiểu DVRIP của XiongMai
- Log chứng minh cơ chế socket broadcast: `"CDeviceV2::SearchDevices:setsockopt error=%d"`,
  `"CDeviceV2::SearchDevices:Server_socket error=%d"`, `"CDeviceV2::SearchDevices:bind error=%d,strerror=%s"`,
  `"CDeviceV2::SearchDevices[MAC:%s][SN:%s][IP:%d.%d.%d.%d]"`, `"CDeviceBase::SearchDevices Return From Buffer,Level[SearchOnDev:%d,%s]"`
- Chuỗi `255.255.255.255` có đúng **1 lần** trong `.so` (offset 5339049, gần `CDecoder::OnFrameInfo` — ngữ cảnh không gắn trực tiếp
  vào hàm search, nên chỉ chứng minh địa chỉ broadcast tồn tại trong lib, không chứng minh nó là đích của gói search)

**KHÔNG TÌM THẤY:**

- `NsdManager` / mDNS / Bonjour / SSDP / UPnP-discovery: grep toàn bộ 35.230 file Java — SSDP 0 file, UPnP 0, mDNS 0, Bonjour 0,
  `MulticastLock` 0, `NsdManager` chỉ 1 file là `androidx/core/content/ContextCompat.java:261` (map tên service của AndroidX,
  không phải code app dùng). `255.255.255.255` 0 file Java, `239.255` 0 file.
  UPnP chỉ xuất hiện dạng config thiết bị `com/lib/sdk/struct/SDK_NetUPNPConfig.java` (port-mapping của camera, không phải discovery).
- **Port UDP của gói discovery: KHÔNG TÌM THẤY** dưới dạng literal trong Java hay strings của lib. Chuỗi `34567` xuất hiện 21 lần dạng byte
  trong `.so` nhưng phần lớn nằm trong vùng FFmpeg/libc không liên quan; không có bằng chứng nào gắn `34567` với broadcast search.
  **Không được kết luận discovery dùng port 34567.**
- **Format gói tin discovery: KHÔNG TÌM THẤY** — không có magic/format-string nào trong strings; chỉ có tên struct `DVRIP_MSG_HEAD_T`,
  `SDK_CONFIG_NET_COMMON_V2`. Cần disassembly `H264_DVR_SearchDevice` mới xác định được (ngoài phạm vi grep lần này).
- **SUY ĐOÁN (chưa chứng minh):** đây là giao thức DVRIP broadcast đặc trưng của XM (XiongMai) — dựa trên tên hàm `H264_DVR_SearchDevice` +
  `NET_SendBroadcastData` + log MAC/SN/IP. Không dùng để khẳng định port hay format gói.

**Hạn chế:** `DeviceManager.OnFunSDKResult` (nơi nhận kết quả search) **không decompile được**
(`DeviceManager.java:204-209` throws `UnsupportedOperationException`); và **không tìm thấy caller Java nào của `searchLanDevice`**
trong cây decompiled (UI gọi nó nằm ở code obfuscate/smali, chưa truy vết).

**Phát hiện LAN online riêng (đã chứng minh, khác với search):** native probe TCP tới IP:port của thiết bị — log libFunSDK:
`"CDataCenter::IsDetectTCPServiceV1, LAN online[%s/%s:%d]"`, `"TCP Connect Success[%s/%s:%d]"`, `"LAN offline[%s]"`,
`"TCP Connect Failed, Retry[%s/%s:%d]"`; Java: `FunSDK.java:338` `DevIsDetectTCPService(byte[], int)` (không tìm thấy caller Java).
Ngoài ra có LAN IP blocklist: `FunSDK.java:148-152,1127-1128` `Add/RemoveDevicesToLANIPBlocklist` (msg 5168/5169),
`CDataCenter::AddDevicesToLANIPBlocklist`.

### 3.2. Endpoint local duy nhất có IP:port cụ thể — chế độ AP của camera (ĐÃ CHỨNG MINH)

`com/utils/XMWifiManager.java:637-652` `setAPDeviceInfo()`:

- Loại socket/bulb (`getXMDeviceAPType` = 1/2/3) → `st_0_Devmac = "172.16.10.1:9001"`, `st_2_Devip = "172.16.10.1"`
- Các loại còn lại → `st_0_Devmac = "192.168.10.1:34567"`, `st_2_Devip = "192.168.10.1"`, login `admin` / password rỗng
  (Lưu ý: trường tên `st_0_Devmac` thực chất chứa chuỗi `"IP:port"`)
- Cùng 2 literal này có trong libFunSDK (`192.168.10.1:34567` kề log `Fun_DeviceLoginEx`; `172.16.10.1:9001` kề `Fun_SysAppInfoQuery`).
  **Port 34567 được chứng minh ở đây là port TCP login của camera khi ở AP-mode, không phải port discovery.**

**Endpoint / API local khác — ĐÃ CHỨNG MINH: không có HTTP API trên camera:**

- **KHÔNG TÌM THẤY:** không có URL `http://192.168…`, `http://10.…`, `:80/:8080/:8000/:37777`, `/cgi-bin`, `/api/` hay `snapshot.cgi`
  nào trỏ tới camera trong code Java của app. Các hit duy nhất đều không phải camera:
  - `FunSDK.java:1257` — `http://10.2.11.100/pages/viewpage.action?pageId=25902177` là link wiki nội bộ trong annotation, không phải endpoint thiết bị
  - `com/manager/device/bind/qrcode/serverinteraction/QRConfigServerInteraction.java:11` — `https://pairing.jftechws.com/api/` (cloud)
  - `/api/ad/…`, `/api/appCaps/…` là quảng cáo (ByteDance/Vungle)
- Trong libFunSDK: chỉ có format HTTP generic (`"%s http://%s:%d%s"`, `"%s://%s:%d/webservice/v940/%s&%lld&%s"`,
  `"%s://%s:%d/jni/pvcchecker.jsp?code=%s"`) — trỏ tới server cloud, không có path CGI/snapshot của camera.
  RTSP client FFmpeg đầy đủ trong lib (`rtsp://`, `OPTIONS/DESCRIBE/SETUP/PLAY`, `RtspClient.cpp`) và Java có `FunSDK.java:938`
  `MediaRtspPlay(...)`, nhưng **không tìm thấy caller Java nào** và literal `rtsp://` = 0 trong code Java của app → RTSP tồn tại trong SDK,
  chưa chứng minh app dùng.
- **Thay cho HTTP, app điều khiển camera qua lệnh JSON P2P theo DevId/SN (đã chứng minh):** `FunSDK.DevCmdGeneral(...)` —
  ví dụ `DeviceManager.java:307` (StoreSnap), `:712` (Reboot qua `OPMachine`), `DevLogin/DevGetConfigByJson/DevSetConfigByJson`.
  Manifest: `usesCleartextTraffic="true"`.

### 3.3. Màn hình / preview local — ĐÃ CHỨNG MINH: cùng một API `MediaRealPlay` cho cả LAN lẫn cloud

- `com/manager/device/media/monitor/MonitorManager.java:223` `startMonitor()` → `FunSDK.MediaRealPlay(hUser, devId, channel, streamType, SurfaceView, 0)`;
  `FunSDK.java:926` `MediaRealPlay`, `:928-929` `MediaPlayEx(…, boolean bEnableSharedMediaLink, …)` ("实时预览,兼容MediaRealPlay").
  **Không tìm thấy nhánh rẽ LAN-vs-cloud nào trong code Java của màn hình monitor** — cùng một call cho mọi trường hợp;
  việc chọn đường trực tiếp LAN hay relay P2P nằm trong native (có `FunSDK.java:899` `MediaGetRealPlayModel(String)` nhưng không có caller Java).
- Manifest có gợi ý duy nhất về khác biệt LAN: `AndroidManifest.xml:103`
  `<meta-data android:name="STREAM_TYPE_IN_LAN" android:value="Main"/>` — trong LAN dùng luồng Main. Nơi đọc meta-data này chưa truy vết được.
- **Snapshot lấy qua kênh P2P/frame, không qua HTTP (đã chứng minh):** `FunSDK.MediaSnapImage(playHandle, "<đường dẫn>.jpg", 0)` —
  `com/xworld/media/XMMediaPlayer.java:1278,1318` (file `<devId>_<chn>_<millis>.jpg`), `:1365` (tham số 100, file `…_WatchPoint.jpg`,
  yêu cầu video đang phát — kiểm tra `TR_Need_Video_Play_Can_Operation`);
  `com/manager/device/media/MediaManager.java:454` (file `yyyyMMddHHmmss… .jpg`, hoặc `.fyuv` với mắt cá 180/360°).
  Native: `FUN_MediaSnapImage`, `CConvertToJPEG / CHYUVToJPEG::Convert` (chuyển YUV của frame đang phát → JPEG) — chứng minh snapshot là chụp frame đã decode trong player.
- **Thumbnail:** `FunSDK.java:903` `MediaGetThumbnail(playHandle, path, -1)` — `MonitorManager.java:81` (gọi khi nhận frame đầu,
  lưu `<devId>_<chn>.jpg` qua `setSaveThumbnailPath`); `FunSDK.java:656` `GetMediaThumbnail(src, dst)` —
  `com/xworld/utils/AbstractC2105k.java:111` (tạo thumbnail `.jpg` cho file video).
- **Snapshot phía thiết bị (khác với snapshot app, đã chứng minh):** `DeviceManager.java:303-311` `captureFromDevAndSaveToDev()` →
  `DevCmdGeneral(…, CAPTURE_FROM_DEV_AND_SAVE_TO_DEV, …, "{\"Name\":\"StoreSnap\",\"StoreSnap\":{\"Channle\":n}}")` — lệnh camera tự chụp và lưu trên thiết bị.
- Hỗ trợ LAN-only trong SDK nhưng chưa thấy app gọi: `FunSDK.java:507` `DisableConnectExtranet()` — annotation:
  "禁止需要连接外网相关服务，为了局域网环境的设备，减少流量消耗" (cấm dịch vụ cần Internet, cho môi trường LAN). Không có caller Java.

### 3.4. Service / Receiver trong AndroidManifest — ĐÃ CHỨNG MINH: không có service/receiver nào cho discovery hay kết nối local

`decompiled/apktool/AndroidManifest.xml` (799 dòng). Toàn bộ service/receiver của app:

- `com.xworld.service.push.AlarmPushService` (L242, push báo động, `foregroundServiceType="remoteMessaging"`, persistent)
- `com.xworld.service.XMNotificationListenerService` (L243, `:push`)
- `com.xworld.service.VideoDownLoadService` (L252)
- `com.xm.device.idr.IDRSleepService` + `InnerService` (L273-274)
- `com.xm.csee.MyFireBaseMessagingService` (L275)
- Receiver duy nhất của app: `com.xworld.service.NotificationClick` (L256). Còn lại là Firebase/WorkManager/Google Play services.
- **Không có service/receiver NSD, discovery, LAN hay P2P nào.**

Các Activity liên quan (manifest): `SearchDevActivity` (L413), `SearchDevApActivity` (L262), `AddDeviceByIPActivity` (L362),
`AddDeviceByBlueToothActivity` (L414), `SearchDeviceByBleActivity` (L417), `Add4GDeviceByBlueToothActivity` (L505),
`APConfigNetWorkTip` (L264), `WifiConfigActivity` (L306), `QuickConfigResultActivity` (L215), `RouteSettingActivity` (L209).
Lưu ý: file Java decompiled của `SearchDevActivity`/`AddDeviceByIPActivity` không có trong cây `sources/com/xworld/activity/adddevice/`
(chỉ còn vài file) — logic UI của chúng nằm ở code obfuscate, chưa truy vết.

Quyền liên quan trong manifest (L46-86): `CHANGE_WIFI_MULTICAST_STATE`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`,
`NEARBY_WIFI_DEVICES`, `ACCESS_FINE_LOCATION`, `OVERRIDE_WIFI_CONFIG`,
`BLUETOOTH/BLUETOOTH_ADMIN/BLUETOOTH_SCAN/BLUETOOTH_ADVERTISE/BLUETOOTH_CONNECT`.

### 3.5. Bluetooth / WiFi-direct / SoftAP — ĐÃ CHỨNG MINH: có BLE (provisioning + reset) và SoftAP (cấu hình WiFi); không có WiFi Direct, không stream qua BLE

**Bluetooth — có, chỉ để cấp phát cấu hình và reset, không truyền video:**

- `com/lib/BluetoothClient/BluetoothClient.java:8-23` — native `Connect/Disconnect/IsConnected/SendData/StartSearch/StopSearch`;
  native tương ứng `Java_com_lib_BluetoothClient_BluetoothClient_StartSearch/StopSearch` trong libFunSDK
- `FunSDK.java:168,171,211,531,553` — `BleEncrypt/BleDecrypt/GenBleToken/EncBleToken/DecBleToken`; lib có log `CDataCenter::EncBleToken`
- `com/utils/BleDistributionUtil.java` — BLE distribution (cấp phát WiFi qua BLE; `b()` L91+ mã hoá IP thành hex qua `InetAddress.getByName`);
  `com/lib/sdk/bean/bluetooth/XMBleHead.java`, `XMBleData.java` (frame BLE + checksum)
- Activity: `AddDeviceByBlueToothActivity`, `SearchDeviceByBleActivity`, `Add4GDeviceByBlueToothActivity`;
  reset qua BLE: `com/xworld/devset/reset/listener/DevResetByBluetoothContract.java:13` `searchResetBluetooth(...)`

**SoftAP — có, là đường cấu hình WiFi chính (đã chứng minh):**

- Camera phát AP riêng; phone quét WiFi và nhận diện SSID: `XMWifiManager.java:274-279` `isXMDeviceWifi()` — prefix
  `robot_/Robot_/card_/car_/seye_/NVR_/DVR_/beye_/IPC_/IPC/Camera_/camera_/xmjp_/feye_/bullet_/drum_/socket_/BOB_/dev_cz_idr_`;
  `getXMDeviceAPType()` L212+ phân loại 0–21; `startScan()` L659+ lọc `ScanResult` theo SSID trên
- Sau khi join AP, cấu hình WiFi cho camera: `DeviceManager.java:787+` `startQuickSetWiFi()` →
  `FunSDK.DevStartAPConfig(…, "S:<ssid>P:<pwd>T:<encType>", "gateway:… ip:… submask:… dns1:… dns2:… mac:…", …)`;
  `startQuickSetWiFiByDevLogin()` L836+ → `DevStartWifiConfigByAPLogin`; native `CConfigAPDev`:
  `xmmulticastconfigsend / xmmulticastconfigsend2 / xmmulticastconfigsend3`, `Thread_XMSend`, `Thread_34571`,
  `Thread_DevSearch`, `Thread_ap_net_wifi_cfg`, `Thread_local_net_wifi_cfg` — tức cấu hình AP dùng cả multicast-config
  và kênh TCP 34571 (wakeup/config), sau đó login vào IP cố định ở §3.2
- **WiFi Direct: KHÔNG TÌM THẤY** bằng chứng nào trong code đã grep; cơ chế duy nhất được chứng minh là phone join SoftAP của camera.

---

## 4. DOMAIN / SERVER CLOUD (để phân biệt cloud vs local)

**ĐÃ CHỨNG MINH (Java + `.so`):**

- Tài khoản/RS API: `https://rs.xmeye.net/` (`Define.java:54-55`, `AccountServerInteraction.java:15`, `ShareManagerServerInteraction.java:15`);
  `https://fdbs.jftechws.com/` (`Define.java:16`); `https://rds.bcloud365.net` (`Define.java:53`);
  `https://pairing.jftechws.com/api/` (`QRConfigServerInteraction.java:11`);
  `https://upgrade.secu100.net/` (`DevFirmwareCheckServerInterface.java:12`);
  `https://d.jfapp.net` (link tải app, `DevShareQrCodeInfo.java:7-9`).
- Nền tảng mở XM: `https://oppf.xmcsrv.com/` (`XMFunSDKManager.java:235`, `XMCloundPlatformInit`).
- Server cloud trong Java `com/xworld/utils/I.java:50-100` (`SysSetServerIPPort`, mặc định khi region trống):
  `MI_SERVER https://ams.jftechws.com:443`, `CAPS_SERVER https://caps.jftechws.com:443`, `AI_SERVER https://api.jftechws.com:443`,
  `P2P_DNS_SERVER secu100.net:8765`, `STATUS_* https://pub-status.secu100.net:7601/7603/7605/7606/7700`,
  `CONFIG_SERVER https://pub-cfg.secu100.net:8186`, `UPGRADE_SERVER https://upgrade.secu100.net:9083` (+ `AMS_KCP_SERVER` từ region).
  `com/mobile/main/MyApplication.java:744-747` `FunSDK.InitExV2(…, p2pDns, 8765)`; `FunSDK.java:1189-1190` `SetP2PDataEncryptEnable` (mặc định mã hoá P2P).
- Trong `libFunSDK.so` (strings): `*.secu100.net` (access-alc/cfs/css/pms/tps, pub-cfg/dsm/dss-hls/logweb/pms-pic/status, shadow, upgrade,
  `xmcloud.xmsecu.com:80`), `*.jftechws.com` (api/ams/caps/jvss/rs/viot-ws…), `*.xmeye.net` (`mi.xmeye.net` — log
  "Get server ip by default value <MI_XMEYE mi.xmeye.net>", `vmscloud`, `xmcfs-cdn`, `adpub`), `*.bcloud365.net` (`voes`, `jfdrive`),
  `*.xm030.net/cn/com` (`www.xm030.cn`, `square.xm030.net`, `m-v.xm030.net`).
- `res/values/strings.xml` (1.069 dòng): gần như không có URL server — chỉ có Firebase `https://xmcsee.firebaseio.com` (L432),
  `xmcsee.appspot.com` (L439), Google client ID (L407, L438), và `libfunsdk_main_bottom_cloud_service` = "云服务" (L519).
  Không có `secu100`/`jftechws`/`xmeye` trong strings.xml.
- `assets/`: `supplierconfig.json` chỉ có appid push (vivo/xiaomi/huawei/oppo); `network_debug_*.json` là bảng ad-network, không có server camera.
- **KHÔNG TÌM THẤY** `*.xiongmaitech.com` trong Java lẫn strings của `libFunSDK.so` (đã grep cả hai nơi).
- Trong libFunSDK (bổ sung): `tdev.xmeye.net:34565/34566/34678`, `vmscloud.xmeye.net`, `pub-dss-hls.secu100.net:8080`,
  `pub-cfg.secu100.net:8086`, `access-*/pub-*` các `*.secu100.net` (port 6502–8480), `jfmq-v2.jftechws.com:1883` (MQTT),
  `caps.jftechws.com`, `api.jftechws.com`, `https://www.xm030.cn`, `adpub.xmeye.net`.

Mọi domain trên đều là HTTPS/API hoặc media cloud; không có domain nào trong số đó là địa chỉ LAN.
Đường duy nhất không qua cloud mà code chứng minh được là AP trực tiếp `192.168.10.1:34567` (lúc setup)
+ LAN search/wake-up trong native SDK (chưa chứng minh được caller) + probe TCP LAN online.

---

## 5. BẢNG TỔNG HỢP — TỪNG MỤC CÓ/KHÔNG ĐƯỜNG LOCAL

| Hạng mục | Kết luận | Bằng chứng chính |
|---|---|---|
| Stream live local | **CÓ (qua FunSDK P2P/LAN, không qua URL)** | `MonitorManager.java:223` `MediaRealPlay(hUser, devId, channel, streamType, surface)`; transport trong native (`CNetTCP`, `CNetXMP2P`, `CNetServerP2P`) |
| RTSP local | **KHÔNG có URL dùng được** (client tồn tại trong SDK, zero caller) | `FunSDK.java:938` `MediaRtspPlay` zero caller; `CRtspClient` trong `.so`; không có port 554 |
| HTTP-FLV | **KHÔNG** | grep `.flv` = 0 cả Java lẫn `.so` |
| HLS local | **KHÔNG** (chỉ xem lại cloud) | `pub-dss-hls.secu100.net:8080`; `MediaPlayM3u8ByUrl` zero caller |
| ONVIF | **KHÔNG dùng được từ app** (chỉ cấu hình phía thiết bị) | 9 file, `onvif` = 0 trong `.so`, UI `visibility="gone"` |
| HTTP API / snapshot.cgi | **KHÔNG** | Không có `/cgi-bin`, `/api/`, `snapshot.cgi` trỏ camera; điều khiển qua `DevCmdGeneral` JSON P2P |
| Talkback 2 chiều | **CÓ** | `DevStartTalk` → `DevSendTalkData` → `DevStopTalk`; `TalkManager.java`; msg 5501 |
| Codec talkback | **G.711 A-law, 8 kHz mono** | `EncodeAudioBean.java:7` `g711a`; `OPFileBean.java:49` `G711_ALAW`; encoder/decoder G711a/u trong `.so` |
| Kênh audio riêng / port audio | **KHÔNG** | Audio chung kênh media P2P; `MediaSetSound` bật/tắt tiếng trên play-handle |
| Ghi âm đàm thoại riêng | **KHÔNG** | Không có `MediaRecorder`; chỉ ghi live `.mp4` (`MediaStartRecord`) và thu mic vào RAM |
| API ngoài lấy audio/ảnh | **KHÔNG** | App chỉ là client FunSDK; snapshot = `MediaSnapImage` chụp frame đã decode |
| Discovery LAN | **CÓ — broadcast DVRIP** | `DevSearchDevice` → `H264_DVR_SearchDevice` + `NET_SendBroadcastData`; không mDNS/SSDP/UPnP |
| Port UDP discovery / format gói | **CHƯA XÁC ĐỊNH** | Không có literal trong Java/strings; cần disassembly `H264_DVR_SearchDevice` |
| AP-mode camera | **CÓ — `192.168.10.1:34567`, `172.16.10.1:9001`** | `XMWifiManager.java:637-652`; login `admin` / rỗng |
| Preview LAN vs cloud | **Cùng 1 API**, khác biệt trong native | `MediaRealPlay`; manifest `STREAM_TYPE_IN_LAN=Main`; `DisableConnectExtranet()` (không có caller) |
| BLE | **CÓ — provisioning + reset, không stream** | `BluetoothClient.java`, `BleDistributionUtil.java`, `GenBleToken` |
| SoftAP cấu hình WiFi | **CÓ** | SSID prefix `xmjp_/IPC_/robot_/…`; `DevStartAPConfig`; multicast-config + TCP 34571 |
| WiFi Direct | **KHÔNG TÌM THẤY** | Chỉ có phone join SoftAP của camera |
| Chế độ hoàn toàn offline | **KHÔNG** (app bắt buộc cloud init) | `XMCloundPlatformInit` bắt buộc; P2P DNS `secu100.net:8765` |

---

## 6. HẠN CHẾ / CHƯA CHỨNG MINH ĐƯỢC — VÀ BƯỚC TIẾP THEO ĐỀ XUẤT

1. **Thứ tự ưu tiên transport (LAN → P2P → relay) và port P2P thực tế** nằm trong `libFunSDK.so` đã strip — cần phân tích
   disassembly sâu hơn (ngoài phạm vi grep strings/Java này). Không suy đoán thứ tự.
2. **`MediaRtspPlay` / `MediaPlayByURL` / `MediaPlayM3u8ByUrl` tồn tại nhưng zero caller Java** — có thể được gọi từ native hoặc từ
   code obfuscate qua JNI khác; không kết luận chúng "chết".
3. **Port UDP discovery DVRIP + format gói tin** chưa xác định — cần disassembly `H264_DVR_SearchDevice` (địa chỉ 0xc23924 trong `.so`)
   hoặc bắt gói tin thật khi app search LAN (tcpdump/Wireshark trên mạng nhà).
4. **Điểm chuyển đổi PCM → G.711 A-law** chưa xác định (Java hay native) — không tìm thấy caller Java của `PcmEncodeToG711`.
5. **Điểm xin quyền `RECORD_AUDIO` runtime** không lần ra trong bản decompile (có thể nằm trong code obfuscate).
6. **Camera thật có bật ONVIF/RTSP server ở port nào không** — code APK không cho biết. Đề xuất probe trực tiếp trên mạng LAN:
   `nmap` IP camera (tìm port mở, đặc biệt 554/80/8000/34567/37777), thử ONVIF probe (vd `onvif-cli` / `python-onvif`),
   thử `rtsp://<ip-cam>:554/...` với các path thường gặp của XM. Chỉ kết quả probe live mới kết luận được.
7. **Muốn xem local không qua app iCSee:** hướng khả thi nhất theo code là dùng SDK FunSDK P2P theo device SN (cần tài khoản XM +
   `APP_UUID/APP_KEY/APP_SECRET` của app — không có trong APK ở dạng dùng được trực tiếp), hoặc probe RTSP/ONVIF trên camera thật (mục 6).
   Không có URL/port local nào trong APK cho phép VLC/ffmpeg/HA kéo stream ngay.

---

## 7. NGUỒN / FILE THAM CHIẾU

- APK gốc: `~/workspace/icsee-apk/icsee-7.9.6_G.xapk`; giải nén: `~/workspace/icsee-apk/xapk/`
- Java: `~/workspace/icsee-apk/decompiled/jadx/sources/` (35.230 file)
- Smali/manifest/res: `~/workspace/icsee-apk/decompiled/apktool/` (`AndroidManifest.xml` 799 dòng)
- Native: `libFunSDK.so` arm64 34 MB (trích từ `xapk/config.arm64_v8a.apk`); strings 97.209 dòng (`/tmp/icsee-so/FunSDK.strings`)
- Chi tiết bước tải: `~/workspace/icsee-apk/STATUS.md` (nội dung cũ nói chưa tải được — đã lỗi thời, file đã có và đã xác minh SHA-256)
- Báo cáo này: `~/workspace/icsee-apk/BAO-CAO.md`
