# Phân tích native đường MÀN HÌNH CAM (AV talk) — libFunSDK.so

- **APK:** iCSee 7.9.6_G, package `com.xm.csee`, build 79633.
- **File phân tích:** `/tmp/icsee-avtalk/lib/arm64-v8a/libFunSDK.so` — 35.375.880 byte, SHA-256 `625ea30d4f1d612761ec034e0c27fefb43fbc2ae0e60bee3389f0e110c750482`, BuildID `bf2ae8f2c81cfc167fa056b3c9ae79af02e0a92d`, ELF arm64, stripped nhưng còn **34.393 dynamic symbol** (đủ tên C++ mangled để định vị hàm). Strings: 97.209 dòng (`/tmp/icsee-avtalk/FunSDK.strings`).
- **Bối cảnh đã đọc:** `AV-TALK-VIDEO-SEND.md`, `BAO-CAO.md`.
- **Công cụ:** `nm -D` / `readelf -r` / `strings` + disassembler tự viết bằng Capstone (`/tmp/icsee-avtalk-native/disasm.py`, AArch64, annotate symbol + resolve chuỗi .rodata). **Không có Ghidra/radare2** (không cài được trong phiên này); GNU objdump không disassembly được aarch64. Kết quả disassembly: 31 file `*.txt` trong `/tmp/icsee-avtalk-native/`.
- **Quy ước mức chứng minh:** **ĐÃ CHỨNG MINH** = đọc trực tiếp disassembly, có địa chỉ hàm/symbol/chuỗi; **SUY ĐOÁN có cơ sở** = suy ra từ hành vi code nhưng chưa thấy byte thực tế; **KHÔNG TÌM THẤY** = đã quét symbol + strings + relocation mà không có.

## Kết luận ngắn

1. **Encoder H.265 ĐÃ CHỨNG MINH:** `videoinfo.encodetype="H265"` → `ToEncodeTypeInt` = 3 → `ToFFMpegCodecID` = 173 (HEVC) → `avcodec_find_encoder(173)` = `ff_libx265_encoder`. Preset 1 → chuỗi `"ultrafast"`; riêng nhánh H.265 còn **hardcode** `preset="ultrafast"` + `tune="zero-latency"` + chuỗi `x265-params` đầy đủ (qp/crf/fps/keyint). Không có đường passthrough NAL: đầu vào bắt buộc là YUV420P thô, native encode lại bằng libx265 (software, `CFFMpegEncoder`; `CHardEncoder` không bao giờ được dùng từ đường này).
2. **Frame-info JSON chỉ có đúng 2 trường** (`timestamp`, `type`) — **ĐÃ CHỨNG MINH**.
3. **Luồng frame ĐÃ CHỨNG MINH tới tận lệnh gửi xuống thiết bị:** YUV/PCM → XMSG 5557 → device → XMSG 4009 → `CEncoderMgr::OnMsg` → `InputData` → `CFFMpegEncoder::Encode` → `AssemblyFrameInfoAndPushFrame` → XMSG 4181 → `CDeviceV2::SendNextData` → **`Dev_SendMsg(..., 11006, ...)`**. Lệnh mở/đóng AV talk là **`Dev_SendMsg(..., 11004, ...)`** với `SNetMediaControlParam` chứa JSON `EncodeCameraBean`. **Chưa chứng minh** phần đóng gói DVRIP bên dưới `Dev_SendMsg` (header/byte order của payload 11006) — cần bắt gói live.
4. **KHÔNG TÌM THẤY lệnh bật màn hình / chọn nguồn hiển thị** trong `.so`: không symbol, không string, không lệnh nào điều khiển LCD vật lý của camera. Màn hình (nếu sáng khi video call) là do **firmware của camera tự quyết** khi nhận media 11006 — SDK phía app không ra lệnh đó.
5. **DecoderPram KHÔNG có ở tầng native** (0 lần xuất hiện trong `.so`): đàm phán hoàn toàn ở tầng Java/smali; native chỉ nhận JSON `EncodeCameraBean` đã parse xong qua chuỗi của XMSG 5556.

## 1. Chọn encoder H264/H265, preset, tham số — ĐÃ CHỨNG MINH

### 1.1. Chuỗi chọn encoder

| Bước | Hàm (địa chỉ) | Bằng chứng |
|---|---|---|
| JSON → `SMediaInParams` | `InitEncodeParams` `0xd4b6b4` | map đầy đủ ở §1.2 |
| Kiểm tra tham số | `CheckEncodeParam` `0xd4b570` | xem §1.2 |
| Tạo encoder | `CEncoderMgr::InitVideoEncoder` `0xd482dc` | build `SEncoderInParam` từ `SMediaInParams`, gọi `CMediaEncoder::CreateEncoder(&param, &bSoft)` với `bSoft` khởi tạo = **1** |
| `CreateEncoder` | `CMediaEncoder::CreateEncoder` `0xe692d0` | `*bSoft==1` → `new CFFMpegEncoder` (0xb8 byte) trực tiếp; nhánh `CHardEncoder` chỉ chạy khi `bSoft==0` — **không bao giờ xảy ra từ đường này** |
| Chuỗi → số | `ToEncodeTypeInt` `0xd4b348` | so sánh không phân biệt hoa/thường (`stricmp`): `H264`→2, `H265`→3, `MJPG`→0, `G711A`→14, `G711U`→10, `AAC`→15, khác/NULL→-1 |
| Số → FFmpeg codec id | `ToFFMpegCodecID` `0xd05bf4` | 0→7 (MJPEG), 2→27 (H.264), 3→173 (H.265), 10→0x10006, 14→0x10007, 15→0x15002, mặc định→0 (NONE) |
| Số → tên preset | `GetPreSet` `0xd4cf54` | 0→`veryfast`, **1→`ultrafast`**, 2→`superfast`, 3→`veryfast`, 4→`medium`, 5→`slow`, khác→`veryfast` |

`CEncoderMgr::Init` (`0xd47ec0`) còn cho thấy: `mediatype` ở `SMediaInParams+0x14` quyết định khởi tạo video hay audio (`!=1` → `InitVideoEncoder`; `==2` (VIDEO) thì bỏ qua audio; else → `InitAudioEncoder`). Khớp enum `EAVTalkSendMediaType` ALL=0, AUDIO=1, VIDEO=2.

### 1.2. `InitEncodeParams` — map JSON → `SMediaInParams` (ĐÃ CHỨNG MINH)

Mặc định trong ngoặc. Lưu ý: **preset mặc định ở native là 3** (`→"veryfast"`), khác default 2 của Java bean; app override preset=1 cho H.265.

| Offset | JSON key | Mặc định |
|---|---|---|
| +0x00 | `protocoltype` | 0 |
| +0x04 | `version` | 0 |
| +0x08 | `channel` | -1 |
| +0x0c | `timeout` | 5000 |
| +0x10 | `maxduration` | 3000 |
| +0x14 | `mediatype` | 0 |
| +0x18 | `videoinfo/encodetype` | qua `ToEncodeTypeInt` |
| +0x1c | `videoinfo/srcwidth` | 0 |
| +0x20 | `videoinfo/srcheight` | 0 |
| +0x24 | `videoinfo/dstwidth` | 0 (≤0 → = srcwidth) |
| +0x28 | `videoinfo/dstheight` | 0 (≤0 → = srcheight) |
| +0x2c | `videoinfo/fps` | 10 |
| +0x30 | `videoinfo/gopsize` | 2 |
| +0x34 | `videoinfo/bitrate` | 0 |
| +0x38 | `videoinfo/qp` | 27 |
| +0x3c | `videoinfo/qmin` | 10 |
| +0x40 | `videoinfo/qmax` | 51 |
| +0x44 | `videoinfo/crf` | 28 |
| +0x4c | `videoinfo/preset` | **3** |
| +0x50 | `timestamp` | chuỗi → `strtoll`, 8 byte |
| +0x58 | `videoinfo/resize_mode` | 0 |
| +0x60 | `audioinfo/encodetype` | qua `ToEncodeTypeInt` |
| +0x64 | `audioinfo/channels` | 1 |
| +0x68 | `audioinfo/bit` | 16 |
| +0x6c | `audioinfo/samplerate` | 8000 |
| +0x70 | `audioinfo/fps` | 50 |

`CheckEncodeParam` (`0xd4b570`, trả về bool): mediatype==1 (AUDIO) → chỉ kiểm tra audio encode type được hỗ trợ; mediatype==2 (VIDEO) → kiểm tra dstwidth>0, dstheight>0, fps>0 và video encode type được hỗ trợ; mediatype==0 (ALL) → kiểm tra cả hai. Lỗi log ở `MediaDefines.cpp:59/65`.

### 1.3. `CFFMpegEncoder::Init` (`0xd4392c`, `FFMpegEncoder.cpp`) — ĐÃ CHỨNG MINH

Member của encoder object (đã xác minh bằng ctor `CMediaEncoder::C2` `0xe693f0`: `memcpy(this+8, param, 0x34)` — tức param copy nguyên khối, lệch +8): +0x08 codec enum, +0x0c W, +0x10 H, +0x14 Fps, +0x18 BitRate, +0x1c Gop, +0x20 qp, +0x24 QMin, +0x28 QMax, +0x2c Crf, +0x30 preset enum, +0x34 byte EnableMultithread.

- **Clamp:** Gop [1..3000] (def 2); qp [1..51] (def 27); QMin [1..31] (def 10); QMax [1..100] (def 51); Crf [1..51] (def 28).
- `codec_id = ToFFMpegCodecID(param)`; preset string = `GetPreSet(param)`. Log (dòng 187): `CFFMpegEncoder::Init[%d/%s][BitRate:%d][Fps:%d,W:%d,H:%d,Gp:%d,QMin:%d,QMax:%d,Gop:%d,Crf:%d,PreSet:%s,EnableMultithread:%d]!`.
- `avcodec_find_encoder(codec_id)` → null thì log `Can not find encoder!` (dòng 191), trả `0xfffe7960`. `avcodec_alloc_context3` → ctx ở this+0x58; null → trả `0xfffe7960`.
- ctx: codec_id +0x18; codec_type=0 (video) +0xc; width +0x74; height +0x78; pix_fmt +0x88 = MJPEG ? 12 (YUVJ420P) : 0 (YUV420P); time_base {1, fps} (MJPEG {1,25}). Số thread ctx+0x310 = (codec==H264 || EnableMultithread) ? 1 : min(2×hardware_concurrency, 16).
- **Khối generic BỊ BỎ QUA với H.265** (nhánh tại `0xd43e50`: codec id==0xad → nhảy qua): `ctx->bit_rate`, `framerate`, `qmin`, `qmax` chỉ được set cho H.264/khác, **không set cho H.265** — rate control của H.265 đi hoàn toàn qua chuỗi x265-params.
- **Nhánh H.264** (id==27): `gop_size = fps × gop`; `av_opt_set(priv_data, "x264-params", "qp=<qp>", 0)`; `av_opt_set(priv_data, "preset", <GetPreSet>, 0)`; `av_opt_set(priv_data, "tune", "zerolatency", 0)`. Log (dòng 257): `CFFMpegEncoder::Init,Params[PreSet:%s,ThreadType:%d,ThreadCount:%d,HardwareConcurrency:%d,QP:%d]`.
- **Nhánh H.265** (id==173): ctx+0x334=1; `av_opt_set(priv_data, "preset", "ultrafast", 0)` — **HARDCODE, không dùng `GetPreSet`**; `av_opt_set(priv_data, "tune", "zero-latency", 0)`; `av_opt_set(priv_data, "x265-params", <buf>, 0)` với format (0x54d3aa):
  `scenecut-bias=0:ipratio=1:qp=%d:crf=%d:psy-rd=0.0:merge=0:wpp=0:rskip=0:lookahead-slices=0:pmode=0:pme=0:temporal-mvp=0:strong-intra-smoothing=0:min-cu-size=8:max-merge=3:me=1:subme=0:sao=0:selective-sao=0:rskip=1:fast-intra=1:fps=%d/1:keyint=%d:min-keyint=2`
  (tham số: qp, crf, fps, keyint=fps×gop). Log (dòng 270): `CFFMpegEncoder::Init,Params[PreSet:%s,ThreadType:%d,ThreadCount:%d,HardwareConcurrency:%d,X265Params:%s]`.
- Cuối: `avcodec_open2(ctx, encoder, NULL)`; lỗi → log `Failed to open encoder[%d]!` (dòng 276), trả `0xfffe7960`.

**Kết luận §1:** H.265 được chọn đúng qua `ff_libx265_encoder` (data symbol `0x21b8598`; `ff_libx264_encoder` ở `0x21b84a0`); preset 1 → `ultrafast` (và H.265 hardcode `ultrafast` bất kể preset); `qp`/`gopsize`/`fps`/`resolution` đi vào x265-params (`qp=`, `keyint=fps×gop`, `fps=`); bitrate cấu hình **không** được đẩy vào `AVCodecContext` cho H.265.

### 1.4. `CFFMpegEncoder::Encode` (`0xd4326c`, 1728 byte) — đầu ra encode, ĐÃ CHỨNG MINH

- Chữ ký: `Encode(pYUV, yuvType, srcW, srcH, SEncoderResult*)`. Lazy-init: ctx null → default (fps 25 nếu ≤0; H = srcH×W/srcW nếu W≥1 else srcH; W = srcW nếu ≤0; bitrate = W×H×3 nếu ≤0) → `Init()`; lỗi → log + trả -1.
- Nếu kích thước đầu vào khác kích thước encoder → resize bằng `CFFScale::Scale` (this+0x70) vào buffer tạm (this+0xa8, cỡ this+0xb0, cấp phát theo align16(W)+16 × align16(H)+16 × 3/2).
- `av_frame_alloc`; `pts = frameCount × 1000 / fps` (frameCount ở this+0x50, tăng sau mỗi frame); `avpicture_fill(frame, data, AV_PIX_FMT_YUV420P=0, W, H)` — đầu vào luôn được coi là YUV420P.
- `avcodec_encode_video2(ctx, &pkt, frame, &got_output)` — API FFmpeg 3.x legacy (khớp `avpicture_fill`/`av_init_packet`).
- Thành công có output: giữ `AVPacket*` ở this+0x48 (free packet cũ trước); điền `SEncoderResult`: +0x00 = pkt->data, +0x08 = pkt->size, +0x0c = pkt->flags & 1 (keyframe); trả về pkt->size. Lỗi: log `av_strerror` (`FFMpegEncoder.cpp:138`), free packet, trả 0.
- **Không có code trích/xử lý SPS/PPS/VPS riêng, không thêm header/framing nào ở tầng này** — output là dữ liệu packet thô của libx264/libx265. **SUY ĐOÁN có cơ sở:** encoder mặc định xuất Annex B (start code `00 00 00 01`), SPS/PPS/VPS kèm trong keyframe; cần bắt gói live mới khẳng định byte thực tế (xem §6).

## 2. `ParseAVTalkFrameInfoJson` — ĐÃ CHỨNG MINH (chỉ 2 trường)

`ParseAVTalkFrameInfoJson` (`0xd4cbc0`, `MediaDefines.cpp`, 572 byte), chữ ký `(const char* json, int* pType, long long* pTimestamp)`:

- `"timestamp"` qua `CXJson::GetStrOfObjs` → `strtoll` cơ số 10 → `*pTimestamp`. Nếu rỗng/0 → log `Use system time` và thay bằng `OS::GetMilliseconds()` (dòng 319).
- `"type"` qua `CXJson::GetIntOfObjs("type", 0)` → `*pType`.
- Trả 0 nếu parse OK, `0xfffe7961` nếu JSON parse lỗi (log `EncodeInfoJson NULL`, dòng 311).

Hàm anh em `GetTypeByFrameInfoJson` (`0xd4cdfc`, 344 byte) chỉ parse `"type"` (def 0); input rỗng/NULL → trả 0 + log (`MediaDefines.cpp:331`).

Hai hàm parse control JSON liên quan (đều ở `MediaDefines.cpp`):

- `ParseAVTalkControlStr` (`0xd4d3f4`, 1584 byte) `(const char* json, SZString& cmd, SZString& info)`: parse `"command"` và `"info"`; command phải là 1 trong 4 chuỗi (đã xác minh qua relocation `R_AARCH64_RELATIVE` — các con trỏ trong file bằng 0, giá trị thật nằm ở addend): `video_pause` (0x556ea0), `video_continue` (0x465c2f), `switching_resolution` (0x4d17c9), `reset_encoder_info` (0x49c448). Lệnh lạ → trả `0xfffe7966` (dòng 430); input rỗng → `0xfffe7961` (dòng 421). Riêng `switching_resolution` còn parse `info/srcwidth`, `info/srcheight` (int, def 0) và yêu cầu srcwidth ≥ 1 **và** srcheight > 0, nếu không → `0xfffe7961` (dòng 442). Thành công → 0.
- `ParseAVTalkControl` (`0xd4d0d8`, 796 byte) `(const char* json, ENET_MEDIA_CONTROL&)`: parse `"command"` → type enum: `video_pause`→**3**, `video_continue`→**4**, `switching_resolution`→**12**, `reset_encoder_info`→**13**; lạ → `0xfffe7966`; rỗng → `0xfffe7961`; OK → 0.

## 3. Luồng frame YUV420P → encoder → mạng — ĐÃ CHỨNG MINH tới `Dev_SendMsg`

Chuỗi đầy đủ (message ID nội bộ trong ngoặc):

1. **`Fun_DevStartAVTalk` (`0xc6104c`)** `(hUser, devId, reqJson, timeout, seq)`: lấy device qua `CDataCenter::GetDevice(devId, 0)`; `new CAVTalkPlayer`; gửi **XMSG 5501** tới player; `CMSGObject::SetIntAttr(hPlayer, 108, 9)`. Khi debug: xóa 4 file tạm `av_talk_data_app_video.dat`, `av_talk_data_app_audio.dat`, `av_talk_data_send_dev.dat`, `av_talk_data_send_encode.dat`.
2. **`CAVTalkPlayer::Start` (`0xcb66fc`)**: đóng gói lại thành **XMSG 5556** (kèm chuỗi JSON) → đẩy tới device handle (this+0xe8). **`CAVTalkPlayer::OnStart` (`0xcb684c`)** nhận kết quả 5556 → `CMediaPlayer::SendResultToUI(5556, ...)`; lỗi (bit 31) → `DeleteSelf()`.
3. **`CDeviceV2::OnUserMsg`, nhánh 5556 (~`0xbf7600`)**: log `CDeviceV2::OnMsg,Start AVTalk,Begin!!![%s,Timeout:%d,ReqInfo:%s,pEncodeMgr:%lu]` (`DeviceV2.cpp:2607`); build `SNetMediaControlParam` (0x678 byte): **+0x10=10**, **+0x14=1** (start), +0x18=msgID, **+0x618=chuỗi JSON request**; gọi **`Dev_SendMsg(..., 11004, ...)`** (overload nhận `IReferable*` = param) → **lệnh dây 11004 (0x2afc) tới camera**. Nhánh stop (`~0xbf7820`): cùng 11004 với +0x14=0, log `CDeviceV2::StopAVTalk,Give device a stop command[...]` (`DeviceV2.cpp:2647`). Đồng thời đăng ký `SDevPtlCmdInfo` tên `"AVTalk"`.
4. **`Fun_DevSendAVTalkData` (`0xc612b0`)** `(hPlayer, frameInfoJson, pAVData, nLen)`: **không encode inline** — chỉ bọc frame thô + JSON vào `XData` rồi **XMSG 5557** → player handle. (Khi debug: ghi frame thô ra `av_talk_data_app_video.dat` nếu type≠2, `av_talk_data_app_audio.dat` nếu type==2.)
5. **`CAVTalkPlayer::OnMsg` (`0xcb6a64`)**: switch theo msg[0x20]: **5557 → forward nguyên vẹn tới device handle** (this+0xe8); **5559 → forward bằng `PushMsgHead`** tới device; **4182 → gửi XMSG 5559 tới UI** qua `UI_SendMsg(this+0xe0, ...)` (kết quả control); **11026 (0x2b12)** → log `Media link disconnect,Notify UI and DeviceV2` + `SendResultToUI(5513, ...)`; default → `CMediaPlayer::OnMsg`.
6. **`CDeviceV2::OnUserMsg`, nhánh 5557 (`0xbf7ac8`, "AVTalkToSendData")**: kiểm tra (StrLen≥1, XData≠NULL, `SAVTalkInfo` tồn tại, encoder manager ở `SAVTalkInfo+0x90` tồn tại); `GetTypeByFrameInfoJson(Str())`; **cổng media-type**: state 1 → mọi type; state 2 → chỉ type==2 (audio); state 3 → chỉ type==1 (video) — giá trị state quan sát được là 1/2/3 (khác enum 0/1/2 của `SMediaInParams`, có thể là mediatype+1 hoặc enum riêng; ghi nhận đúng như quan sát). Không đạt → log `CDeviceV2::OnMsg,AVTalkToSendData failed!!!![State:%d,pEncoderMgr:%s]` (`DeviceV2.cpp:2680/2686`). Đạt → đóng gói lại thành **XMSG 4009 (0xfa9)** → encoder manager handle.
7. **`CEncoderMgr::OnMsg` (`0xd48c48`), nhánh 4009 (`0xd49328`)**: kiểm tra (data≠NULL, nLen≥1, StrLen>0) nếu không log (`EncoderMgr.cpp:498`) và bỏ; `ParseAVTalkFrameInfoJson`; **video (type==1): độ dài frame phải đúng bằng `srcW × srcH × 3 / 2`** — sai thì log (`EncoderMgr.cpp:511`) và **drop frame**; rồi gọi virtual `InputData(data, len, type, timestamp)` (vtable+0xf0).
8. **`CEncoderMgr::InputData` (`0xd49880`)**: validate (pData≠NULL, nLen≥1, type 1 hoặc 2, timestamp≠0) else `0xfffe7961`; video → `CMediaEncoder::Encode(pData, YUVType=1, srcW, srcH, &ret)` + đo thời gian encode (thống kê ở this+0x238/0x23c; nếu hiệu năng encode đổi so với flag đã lưu this+0x240 → `UnInitVideoEncoder` + re-init — adaptive re-init); audio (type 2) → audio encoder `Encode(pData, len, 40960, &ret)`; thành công → `AssemblyFrameInfoAndPushFrame`.
9. **`AssemblyFrameInfoAndPushFrame` (`0xd49d2c`)**: build `FRAME_INFO` (mediaType, độ dài, timestamp, encodetype, dstW/H, fps, cờ keyframe + thời điểm keyframe, bộ đếm frame); `CEncodedFrameProcessor::PushFrame` (queue ở this+0xe0); gửi **XMSG 4181** tới handle this+0x20c (device).
10. **`CDeviceV2::OnUserMsg`, nhánh 4181 (`0xbf7e10`)** → **`CDeviceV2::SendNextData` (`0xc05980`)**: lấy `SAVTalkInfo` + encoder manager; nếu `msg[0x24]≠0` → lỗi; **nếu msgID vào == 11006 → set cờ `SAVTalkInfo+4 = 1`**; nếu cờ==0 → log `WaitSendData[bWaitSendData:%d,MsgID:%d]!!!!` (`DeviceV2.cpp:8903+`) và **không gửi**; nếu cờ==1 → `CEncodedFrameProcessor::PopFrame()` → cổng media-type lần nữa (state 1: mọi loại; 2: frame type phải ==2; 3: phải ==1) → log `CDeviceV2::OnMsg,AVTalk[%d],SendNextData,ToDevice--->[%d,%d-%d-%d][%lu]Time:%04d-...-->[rate=%d][%d,%d][%llu][%lu,MsgID:%d]` (`DeviceV2.cpp:8889`) → **`Dev_SendMsg(..., 11006, 10, SAVTalkInfo+0x24, <chuỗi số>, frameData, frameLen, seq)`** → **lệnh dây 11006 (0x2afe)**; đồng thời ghi byte đã gửi ra `av_talk_data_send_dev.dat` (debug). Chuỗi số kia là `SAVTalkInfo+0x20` format `"%d"` bằng helper ở `0xbe4760` (chưa định danh — SUY ĐOÁN: chỉ số channel/seq dạng chuỗi).
11. **`SendNextData` còn được gọi từ `CDeviceV2::OnDeviceMsg` (`0xbf0990`)** với một message phía thiết bị — case này đi bằng fall-through/jump-table nên **chưa xác định được msgID cụ thể** (xem §6). **SUY ĐOÁN có cơ sở:** thiết bị gửi 11006 như yêu cầu "gửi frame tiếp theo" (flow-control); XMSG 4181 ("frame đã sẵn sàng") và yêu cầu 11006 của thiết bị gặp nhau ở `SendNextData` qua cờ `bWaitSendData`.
12. **Dưới `Dev_SendMsg` là MNetSDK** (`CNetDevice::OnMsg` xử lý 11006 ở `0xf7102c`/`0xf7b87c`; `CMediaChannel::OnMsg` `0xf88514`; `CDssChannel` `0xf8c840`; `CGWMChannel` `0xf8d028`) → media channel → gói DVRIP. **Đóng gói DVRIP của payload 11006 (header, thứ tự byte, FRAME_INFO nào được serialize kèm NAL) CHƯA được phân tích** — code channel MNetSDK chưa disassembly (xem §6).

**Lệnh dây đã xác định:** 11004 (0x2afc) = media control (start/stop AV talk, realplay…); 11006 (0x2afe) = media data (frame đã encode); 11001 (0x2af9) = device control (login/init); 11026 (0x2b12) = media link disconnect. 11006 cũng là lệnh data chung của SDK (dùng cho realplay, download, record…), không riêng AV talk.

**Nhánh control 5559 (bổ sung, ĐÃ CHỨNG MINH):** device nhận 5559 → `ParseAVTalkControl` → **XMSG 4183** (`PushMsgHead`) → `CEncoderMgr::OnMsg` nhánh 4183 (`0x1057`): `video_pause` → `SetNeedToCheckVideoFrameSent(false)` + `UnInitVideoEncoder`; `video_continue` → flag true + `InitVideoEncoder`; `switching_resolution` → flag true + `UnInitVideoEncoder` + `SetSwitchingResolutionInfo(info)` + `InitVideoEncoder` + gửi 4182/4187; `reset_encoder_info` → `UnInit()` + `InitPartial(info)` + gửi 4182/4187. **4182** về `CAVTalkPlayer::OnMsg` → forward 5559 tới UI; **4187** về device (handler `0xbf8560`, chưa đọc chi tiết).

**Bản đồ message ID nội bộ:** 5501 = start (player nội bộ, `Fun_DevStartAVTalk` → `CAVTalkPlayer::Start` chuyển thành 5556); 5556 = start AV talk; 5557 = gửi frame; 5558 = stop; 5559 = control; 4009 = frame tới encoder manager; 4181 = frame đã encode sẵn sàng; 4182 = kết quả control; 4183 = lệnh control tới encoder; 4187 = thông báo control tới device; 5513 = kết quả lỗi gửi UI; 11026 = media link disconnect.

## 4. Dấu vết điều khiển MÀN HÌNH — KHÔNG TÌM THẤY

Đã quét có hệ thống symbol table (34.393 symbol) + toàn bộ strings (97.209 dòng) + relocation:

- Chuỗi `DecoderPram`: **0 lần** (xem §5).
- Chuỗi `VideoWidget`: **0 lần**. Không có chuỗi `ScreenOn`/`ScreenOff`/`TurnOnScreen`/`SetDisplay`/`DisplaySource`/`VideoOutput` nào phía thiết bị.
- 55 symbol chứa `lcd|screen|display|panel|osd` — **tất cả đều không liên quan**, gồm:
  - `FUN_MediaSetDisplayBCSG` (`0xc5e498`) / `Java_com_lib_FunSDK_MediaSetDisplayBCSG` (`0xe4b87c`) — chỉnh **brightness/contrast/saturation/gray của player phía app** (`Fun_MediaSetDisplayBCSG[hPlayer:%u,Brightness:%d,Contrast:%d,Saturation:%d,Gray:%d]`), không phải màn hình camera.
  - `Java_com_xmgl_vrsoft_VRSoftJNI_multiSetScreenNumber` / `setTwoLensesScreen` / `getTwoLensesScreen` / `displayRect` / `displayTarget` — VR/dual-lens phía app.
  - FreeType `FT_Library_SetLcdFilter*`, FFmpeg/x265 `av_display_rotation_*`, `av_mastering_display_metadata_*`, `display-window`, `lcddefault`/`lcdnone`/`lcdlegacy`/`lcdlight` (tham số LCD filter của x265) — thư viện bên thứ ba.
  - Còn lại là `*ToSDKError` (chứa chuỗi con "osd" trong "ToSDK").
- API lệnh config chung `FUN_DevCmdGeneral` / `FUN_DevCmdGeneralEx` / `FUN_DevCmdGeneral_Obj` (`0xc50bc0`/`0xc50690`/`0xc50a54`) **có tồn tại**, nhưng không tìm thấy chuỗi lệnh nào về màn hình đi qua nó.
- Trường chưa map duy nhất có thể liên quan: `SNetMediaControlParam+0x10 = 10` (hardcode khi start) — **không có bằng chứng** nào cho thấy nó liên quan tới hiển thị; ghi nhận là câu hỏi mở cho lần bắt gói live.

**Kết luận §4:** SDK phía app **không có** hàm/lệnh bật màn hình LCD camera hay chọn nguồn hiển thị. Video AV talk được đưa tới camera dưới dạng media data (11006); việc hiển thị lên màn hình 2.8" là quyết định của **firmware camera**, không nằm trong `.so` này. Cách duy nhất để xác minh là gọi video thật từ app iCSee và quan sát màn hình vật lý (kèm bắt gói để thấy trao đổi 11004/11006).

## 5. `DecoderPram` ở tầng native — KHÔNG TÌM THẤY (ĐÃ CHỨNG MINH phủ định)

- Chuỗi `DecoderPram` xuất hiện **0 lần** trong toàn bộ strings của `libFunSDK.so`; không có symbol nào chứa `DecoderPram` hay cmdId 0x550/1360 ở tầng native.
- Native chỉ nhận **JSON `EncodeCameraBean` đã parse xong** dưới dạng chuỗi của XMSG 5556 → copy vào `SNetMediaControlParam+0x618` rồi gửi đi bằng lệnh 11004.
- Chuỗi format duy nhất nhắc tới `Enc` là `"%-23s %s Kx=%-8s Au=%-4s Enc=%-9s Mac=%-4s"` (dòng 68955) — format in thông tin thiết bị (kết quả search/info), **không phải** parse `DecoderPram`.
- Hệ quả: các trường đàm phán (Enc, Res W/H/FPS, Audio SR) chỉ tồn tại ở tầng Java/smali; muốn biết camera trả về gì trong `DecoderPram` phải đọc logcat/smali hoặc bắt gói lúc mở video call — native không giúp thêm.

## 6. Còn thiếu — cần bắt gói live (tcpdump + logcat) trong một cuộc gọi video thật

1. **Đóng gói DVRIP của 11004 và 11006:** `SNetMediaControlParam` được serialize ra dây như thế nào (JSON có đi nguyên văn không?); payload 11006 là NAL thuần hay có header FunSDK/DVRIP (những trường nào của `FRAME_INFO` — timestamp, cờ keyframe, fps, W/H — được gửi kèm, thứ tự byte ra sao?). Phân tích code channel MNetSDK (`CMediaChannel::OnMsg` `0xf88514`, `CNetDevice::OnMsg`) chưa làm — cần Ghidra để decompile cho nhanh, hoặc bắt gói trực tiếp.
2. **Byte thực tế của frame H.265:** có đúng Annex B `00 00 00 01` với VPS/SPS/PPS (`40/42/44`) kèm keyframe không; keyframe đầu tiên có mang VPS/SPS/PPS không; `keyint=fps×gop` thể hiện ra sao trên dây.
3. **Flow-control:** message phía thiết bị nào gọi `SendNextData` từ `CDeviceV2::OnDeviceMsg` (`0xbf0990`) — kiểm chứng giả thuyết "thiết bị gửi 11006 để xin frame tiếp theo". Cần xem log `WaitSendData` / `SendNextData,ToDevice` trong logcat khi gọi thật.
4. **Màn hình vật lý có sáng không** khi AV talk chạy — câu hỏi sản phẩm cốt lõi, chỉ quan sát trực tiếp mới trả lời được.
5. **Ý nghĩa `SNetMediaControlParam+0x10 = 10`** (và các trường còn lại của struct 0x678 byte) — đối chiếu với gói 11004 bắt được.
6. **Đường tắt bằng file debug:** nếu bật được `Fun_IsDebug` (thiết bị đã root/emulator), 4 file tạm sẽ chứa toàn bộ dữ liệu không cần tcpdump: `av_talk_data_app_video.dat` (YUV thô vào), `av_talk_data_app_audio.dat` (PCM thô vào), `av_talk_data_send_encode.dat` (sau encode — **writer của file này chưa được định vị trong lần phân tích này**), `av_talk_data_send_dev.dat` (byte gửi xuống thiết bị — writer đã xác minh ở `SendNextData` `0xc05c64`).
7. Chưa phân tích sâu trong lần này (không chặn đường màn hình, ghi nhận để tránh ngộ nhận là đã xong): handler 4187 (`0xbf8560`), `CEncoderMgr::Encode` (`0xd48a2c`), audio encoder (G.711) chi tiết, helper `0xbe4760` (format số thành chuỗi `"%d"`), `CEncodedFrameProcessor` (queue/chống trễ frame, `SetNeedToCheckVideoFrameSent`, `SetCacheFrameMaxDuration`, `SetFrameRate`).

## Phụ lục A — Bảng hàm đã phân tích

| Hàm | Địa chỉ | Cỡ | Nguồn | Kết quả chính |
|---|---|---|---|---|
| `Fun_DevStartAVTalk` | 0xc6104c | 612 B | FunSDK.cpp:3974 | tạo player, XMSG 5501 → 5556 |
| `Fun_DevSendAVTalkData` | 0xc612b0 | 496 B | FunSDK.cpp | bọc frame thô → XMSG 5557 (không encode inline) |
| `Fun_DevStopAVTalkData` | 0xc614a0 | 144 B | FunSDK.cpp | (đã định vị, chưa đọc chi tiết) |
| `Fun_DevControlAVTalk` | 0xc61530 | 348 B | FunSDK.cpp | XMSG 5559 |
| `CAVTalkPlayer::Start` | 0xcb66fc | 336 B | MediaPlayer.cpp | 5501 → 5556 |
| `CAVTalkPlayer::OnStart` | 0xcb684c | 224 B | MediaPlayer.cpp:2490 | kết quả 5556 → UI; lỗi → tự hủy |
| `CAVTalkPlayer::OnMsg` | 0xcb6a64 | 1356 B | MediaPlayer.cpp:2519/2535 | dispatch 4182/5557/5559/11026 |
| `CAVTalkPlayer::Close` | 0xcb692c | 312 B | MediaPlayer.cpp | (đã định vị; XMSG 5558 ở 0xcb69c8) |
| `CDeviceV2::OnUserMsg` | 0xbf0f78 | ~66 KB | DeviceV2.cpp | dispatch trung tâm; đã đọc các nhánh 5556/5557/4181/4182/4183/4187 |
| `CDeviceV2::SendNextData` | 0xc05980 | 1932 B | DeviceV2.cpp:8889–8903 | PopFrame → `Dev_SendMsg` 11006 |
| `CDeviceV2::OnDeviceMsg` | 0xbe6ecc | — | DeviceV2.cpp | chỉ đọc vùng gọi SendNextData (0xbf0984); dispatch jump-table chưa phân tích |
| `CEncoderMgr::C2` (ctor) | 0xd47ba0 | — | EncoderMgr.cpp | gọi `Init`; được `CDeviceV2::OnUserMsg` tạo ở 0xbf74ec |
| `CEncoderMgr::Init` | 0xd47ec0 | 556 B | EncoderMgr.cpp | đọc config, `InitEncodeParams`, chọn video/audio encoder |
| `CEncoderMgr::InitVideoEncoder` | 0xd482dc | 436 B | EncoderMgr.cpp:265 | build param → `CreateEncoder` (bSoft=1) |
| `CEncoderMgr::InitAudioEncoder` | 0xd48490 | 316 B | EncoderMgr.cpp | (đã định vị từ lần trước) |
| `CEncoderMgr::InitPartial` | 0xd48694 | 364 B | EncoderMgr.cpp | re-init từng phần (dùng cho `reset_encoder_info`) |
| `CEncoderMgr::Encode` | 0xd48a2c | 540 B | EncoderMgr.cpp | (chưa đọc chi tiết) |
| `CEncoderMgr::OnMsg` | 0xd48c48 | 2276 B | EncoderMgr.cpp:498/511/515 | dispatch 4009 (frame) / 4183 (control) |
| `CEncoderMgr::InputData` | 0xd49880 | 1196 B | EncoderMgr.cpp:533 | validate → Encode → `AssemblyFrameInfoAndPushFrame` |
| `CEncoderMgr::AssemblyFrameInfoAndPushFrame` | 0xd49d2c | 1020 B | EncoderMgr.cpp | build FRAME_INFO, PushFrame, XMSG 4181 |
| `CEncoderMgr::SetSwitchingResolutionInfo` | 0xd4952c | 852 B | EncoderMgr.cpp | (đã định vị, chưa đọc chi tiết) |
| `ParseAVTalkFrameInfoJson` | 0xd4cbc0 | 572 B | MediaDefines.cpp:311/319 | chỉ 2 trường timestamp/type |
| `GetTypeByFrameInfoJson` | 0xd4cdfc | 344 B | MediaDefines.cpp:331 | chỉ trường type |
| `ParseAVTalkControl` | 0xd4d0d8 | 796 B | MediaDefines.cpp:385/413 | command → enum 3/4/12/13 |
| `ParseAVTalkControlStr` | 0xd4d3f4 | 1584 B | MediaDefines.cpp:421/430/442/447 | command + info; validate resolution |
| `InitEncodeParams` | 0xd4b6b4 | 2048 B | MediaDefines.cpp | map JSON → SMediaInParams |
| `CheckEncodeParam` | 0xd4b570 | 324 B | MediaDefines.cpp:59/65 | validate theo mediatype |
| `ToEncodeTypeInt` | 0xd4b348 | 400 B | MediaDefines.cpp | H264→2, H265→3, … |
| `ToFFMpegCodecID` | 0xd05bf4 | 208 B | — | 2→27, 3→173 |
| `GetPreSet` | 0xd4cf54 | 388 B | MediaDefines.cpp | 1→ultrafast, 2→superfast, 3→veryfast… |
| `CMediaEncoder::CreateEncoder` | 0xe692d0 | 288 B | — | bSoft=1 → CFFMpegEncoder |
| `CMediaEncoder::C2` (ctor) | 0xe693f0 | 92 B | — | memcpy param→this+8 (52 B) |
| `CMediaEncoder::ToFFMPGEType` | 0xe694c8 | — | — | (đã định vị) |
| `CFFMpegEncoder::Init` | 0xd4392c | 2464 B | FFMpegEncoder.cpp:187/191/199/257/270/276 | x264-params / x265-params |
| `CFFMpegEncoder::Encode` | 0xd4326c | 1728 B | FFMpegEncoder.cpp:138 | scale, av_frame, avcodec_encode_video2 |
| `CFFEncoderBase::Init` | 0xd445b8 | 468 B | — | (đã định vị) |
| `CFFEncoderBase::OpenCodecCtxDst` | 0xd44af4 | 1368 B | — | (đã định vị) |
| `CFFEncoderBase::InputData` | 0xd448c0 | 160 B | — | (đã định vị) |
| `CEncodedFrameProcessor::PopFrame` | 0xd46ca4 | — | — | được `SendNextData` gọi |

## Phụ lục B — Mã lỗi gặp trong đường AV talk

| Mã | Ý nghĩa (theo code) |
|---|---|
| `0xfffe7960` | Không tìm thấy encoder / alloc ctx lỗi / open encoder lỗi (`CFFMpegEncoder::Init`) |
| `0xfffe7961` | JSON parse lỗi / input rỗng / tham số resolution không hợp lệ / `InputData` validate lỗi |
| `0xfffe7966` | Lệnh control không biết / `InitVideoEncoder` lỗi |
| `0xffed162a` | AV talk chưa login / không tìm thấy AVTalkInfo / encoder null (device trả 4182) |

## Phụ lục C — Giới hạn của lần phân tích này

- Không dùng Ghidra/radare2 (chưa cài); phân tích bằng Capstone disassembly thủ công nên các struct lớn (FRAME_INFO, SNetMediaControlParam, SAVTalkInfo) chỉ map được từng phần qua offset sử dụng, không có layout đầy đủ.
- Không chạy code, không đăng nhập tài khoản, không gửi dữ liệu — mọi kết luận đều từ đọc tĩnh `.so`.
- Không phân tích code MNetSDK channel (đóng gói DVRIP), jump-table dispatch của `CDeviceV2::OnDeviceMsg`, audio encoder chi tiết, handler 4187, `CEncoderMgr::Encode`.
- Các chuỗi con trỏ trong `.data.rel.ro` có giá trị 0 trong file (relocation `R_AARCH64_RELATIVE`) — đã khôi phục bằng addend của `readelf -r` (vd: 4 lệnh control ở 0x2191d70–0x2191d88 và 0x2191d90–0x2191da8).
