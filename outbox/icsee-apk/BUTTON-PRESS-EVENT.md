# BÁO CÁO — EVENT/TRẠNG THÁI NÚT BẤM TRÊN CAMERA ICSee (chiều camera → app)

**Ngày:** 14/11/2026
**APK:** iCSee 7.9.6_G (`com.xm.csee`), đã phân giải ở `~/workspace/icsee-apk/`
**Phạm vi:** khi có người bấm nút gọi video trên thân camera (VD: DOSEN RPO V1, nút bên hông),
app nhận được sự kiện gì, và một client ngoài (service DVRIP-native trong
`~/workspace/icsee-docker/`) có nhận được sự kiện đó qua LAN không.
**Phương pháp:** chỉ đọc, không sửa file, không đăng nhập tài khoản nào, không gửi dữ liệu đi.
**Báo cáo liên quan:** `BAO-CAO.md` (tổng), `AV-TALK-VIDEO-SEND.md` (chiều app → camera:
gửi video lên màn hình — báo cáo này làm chiều ngược lại), `AV-TALK-NATIVE.md`,
`../icsee-docker/ARCH-BLOCKER-REPORT.md` (DVRIP-native).

---

## 0. KẾT LUẬN NGẮN

| Câu hỏi | Kết luận | Mức chứng minh |
|---|---|---|
| Có lấy được event khi bấm nút trên camera không? | **CÓ — có 2 đường đã chứng minh cơ chế, nhưng event của đúng nút bấm này thì chưa chứng minh tên gọi.** | Xem dưới |
| Đường 1 — app nhận qua cloud MPS (cách app đang làm) | **ĐÃ CHỨNG MINH.** Nút bấm → thiết bị đẩy alarm lên cloud MPS (đã subscribe qua `MpsClient.LinkDev`/`LinkByUserID`) → native FunSDK giao JSON qua message **6007 (`MC_ON_AlarmCb`)** → `AlarmPushService` parse thành `AlarmInfo` → mở màn hình cuộc gọi đến (`IDRVisitorActivity`) hoặc notification. Event dạng chuỗi: `IncomingCall`, `FamilyCall`, `LocalAlarm`, `RemoteCallAlarm`, `DoorBell`, … | ĐÃ CHỨNG MINH (Java + smali, xem §2) |
| Đường 2 — FunSDK P2P trực tiếp (LAN, không cloud) | **KHÔNG TÌM THẤY.** Trong `libFunSDK.so` (182.911 dòng strings) có **0** chuỗi `IncomingCall`/`DoorBell`; API `DevSetAlarmListener` / `DevGetAlarmState` / message `DEV_GET_LAN_ALARM = 5132` tồn tại nhưng **0 caller** trong toàn bộ Java + smali. Không có bằng chứng thiết bị đẩy yêu cầu gọi qua kênh P2P tới app. | KHÔNG TÌM THẤY (bằng chứng âm tính, xem §3) |
| Đường 3 — DVRIP qua LAN (không cần FunSDK/cloud) | **CƠ CHẾ ĐÃ CHỨNG MINH, EVENT CỦA NÚT BẤM CHƯA CHỨNG MINH.** `AlarmSet` opcode **1500** để subscribe, thiết bị đẩy `AlarmInfo` opcode **1504** (JSON) trên chính TCP connection đã login — push-based, không poll. Đã chứng minh bằng source `python-dvr` + tài liệu `hass-xmeye` (đo live trên NBD8008R-U). Nhưng **chưa chứng minh** nút gọi video của DOSEN RPO V1 sinh ra event `AlarmInfo` nào, với `Event` bằng gì — khả năng cao nhất là `LocalAlarm`, cần test live. | ĐÃ CHỨNG MINH (cơ chế); CHƯA CHỨNG MINH (event nút bấm, xem §4) |
| Có poll được TRẠNG THÁI nút (đang bấm/không bấm) không? | **KHÔNG TÌM THẤY cách nào.** Event là push-only; không có API/state nào đọc được trạng thái nút. `DevGetAlarmState` tồn tại nhưng 0 caller, ngữ nghĩa không xác định. | KHÔNG TÌM THẤY |
| Service Docker DVRIP-native hiện tại có nhận được event không? | **CHƯA — chưa có code alarm nào.** Service chỉ có login/monitor/talk/video. Cần thêm: connection alarm riêng + subscribe 1500 + parser 1504 + endpoint event (VD: SSE/WebSocket). Chi tiết §5. | ĐÃ CHỨNG MINH (grep = 0 kết quả) |

---

## 1. BẢNG EVENT / MESSAGE ĐÃ TÌM THẤY (file:dòng)

### 1.1. Event dạng chuỗi — phía app (cloud MPS / `AlarmInfo.Event`)

`com/xworld/manager/XMPushManager.java` — `b(String event, AlarmInfo)` (:175), map event → text hiển thị:

| Event (`AlarmInfo.Event`) | Hiển thị / ý nghĩa | Dòng |
|---|---|---|
| `IncomingCall` | `TR_Video_Call_On` — yêu cầu gọi video đến | :182 |
| `FamilyCall` | `TR_Video_Call_On` — gọi từ người nhà | :184 |
| `LocalAlarm` | `Caller` — người gọi đến (chuông cửa / nút bấm local) | :186 |
| `RemoteCallAlarm` | `TR_RemoteCallAlarm` — gọi từ xa | :188 |
| `HangUp` | `TR_Video_Call_Off` — cúp máy | :178 |
| `FamilyCallOff` | `TR_Video_Call_Off` | :190 |
| `ForceDismantleAlarm` | `IDR_MSG_FORCE_DISMANTLE` — cạy phá | (trong `b()`/`h()`) |
| `PIRAlarm` | `Video_Motion` — PIR | (trong `b()`/`h()`) |
| `LowBatteryAlarm` | `Alarm_Low_Battery` | (trong `b()`/`h()`) |
| `IntervalWakeAlarm` / `ReserveWakeAlarm` | `IDR_MSG_INTERVAL_WAKE` / `IDR_MSG_RESERVER_WAKE` — đánh thức theo lịch | (trong `b()`/`h()`) |

`h()` (:~340–520) map thêm theo `TYPE_*` (`com/manager/push/XMPushManager`, chỉ có ở smali):
`TYPE_DOOR_BELL` + `MSG_TYPE_DOOR_BELL` → `libfunsdk_alarm_type_door_bell_ring` (:510);
`TYPE_LOCAL_ALARM` → `IDR_MSG_MISS_CALL`; `TYPE_RECEIVED_CALL` → `IDR_MSG_RECEIVED_CALL`;
`TYPE_REMOTE_CALL_ALARM` → `TR_RemoteCallAlarm`.

Loại thiết bị chuông cửa: `com/manager/device/idr/IdrDefine.java:153` `isDoorbell(int)` =
type `21`, `26`, `286457857` (`DEV_CZ_IDR`); `isIDR()` gồm thêm doorlock/low-power.

### 1.2. Message ID — FunSDK / MPS

| ID | Tên | Vai trò | Nguồn |
|---|---|---|---|
| **6007** (`0x1777`) | `MC_ON_AlarmCb` | Native giao JSON alarm cho app (callback chung, thay thế các subscribe riêng) | `com/lib/EUIMSG.java:167`; `MpsClient.java` (`LinkDevGeneral`); `AlarmPushService.smali:5090` (nhánh `0x1777`) |
| 6000 | `MC_LinkDev` / `DevAlarmSubscribe` | Subscribe alarm của 1 thiết bị (cloud MPS) | `MpsClient.java`; `EUIMSG.java` |
| 6001 | `MC_UnlinkDev` | Hủy subscribe | `MpsClient.java` |
| 6011 | `MC_INIT_INFO` (`InitV2`) | Khởi tạo dịch vụ alarm với SMC token | `MpsClient.java`; `XMPushManager.r()` |
| 6015 | `MC_OnRecvAlarmJsonData` | Cổng nhận alarm JSON từ server thứ ba | `MpsClient.java`; `EUIMSG.java:172` |
| 6019 / 6020 | `LinkDevsBatch` / `UnLinkDevsBatch` | Subscribe/hủy hàng loạt | `MpsClient.java` |
| 6003 / 6032 | `SearchAlarmInfo` / `DevAlarmMsgQuery` | Truy vấn lại lịch sử alarm trên cloud (không phải push) | `MpsClient.java` |
| **5132** (`0x140c`) | `DEV_GET_LAN_ALARM` | Lấy alarm qua LAN — tồn tại nhưng **0 caller** | `com/lib/EUIMSG.java:84` |
| — | `DevSetAlarmListener(hUser, nSeq)` | Đăng ký listener alarm trong FunSDK — **0 caller** | `com/lib/FunSDK.java:376` |
| — | `DevGetAlarmState(hUser, nSeq)` | Đọc trạng thái alarm — **0 caller**, ngữ nghĩa không rõ | `com/lib/FunSDK.java:311` |
| — | `SysOpenWXAlarmListen` / `SysThirdPartyOpenAlarmListen` | Nghe alarm qua WeChat / server thứ ba (cloud relay) — **0 caller** Java | `com/lib/FunSDK.java:1436,1529` |

### 1.3. Opcode DVRIP — đường LAN (không FunSDK)

| Opcode | Tên | Vai trò | Nguồn |
|---|---|---|---|
| **1500** | `AlarmSet` | Subscribe nhận alarm (gửi 1 lần sau login) | `python-dvr` `dvrip.py` (`QCODES`, `alarmStart()` :422); `hass-xmeye/docs/protocol.md` §4 |
| **1504** | `AlarmInfo` | Thiết bị **đẩy** JSON event về (push, không cần poll) | `python-dvr` `alarm_thread()` :431–449; `hass-xmeye` README/protocol |
| 1506 | `OPNetAlarm` | Bật/tắt alarm từ xa (`{"Event":0,"State":…}`) | `python-dvr` `set_remote_alarm()` :457 |

---

## 2. LUỒNG 1 — APP NHẬN EVENT QUA CLOUD MPS (ĐÃ CHỨNG MINH)

Đây là cách app iCSee đang làm hôm nay. Toàn bộ chuỗi đã truy vết được tới tận màn hình cuộc gọi:

**Bước 0 — Subscribe (lúc app chạy, 1 lần).**
`XMPushManager.r(SMCInitInfoV2, int)` → `MpsClient.InitV2(...)` + `MpsClient.LinkByUserID(userId, …)`
(`XMPushManager.java`, cuối file); `A()`/`z()` → `MpsClient.LinkDevEx(sn, …)` cho từng thiết bị.
Subscribe gắn thiết bị + tài khoản + app token (SMC token) vào dịch vụ MPS cloud của XM.
`AlarmPushService` (foreground service, `AndroidManifest.xml:242`) giữ kênh push sống.

**Bước 1 — Nút bấm → thiết bị đẩy alarm lên MPS cloud.**
Thiết bị sinh event (VD: `IncomingCall` / `LocalAlarm`) và gửi lên cloud MPS. (Điểm này suy
ra từ cơ chế subscribe + callback 6007; bản thân gói tin thiết bị → cloud không có trong APK.)

**Bước 2 — Native giao JSON alarm cho app: message 6007.**
`AlarmPushService.OnFunSDKResult` (`smali_classes5/.../push/AlarmPushService.smali:5090`,
implements `IFunSDKResult`): nhánh `what == 0x1777` (6007, `MC_ON_AlarmCb`) và `0x1778` —
lấy `msgContent.pData` → string, log `AlarmPushService收到报警消息 :` (nhận được tin báo động),
rồi `G(json)` → `CustomPushBean` (`:4226`).

**Bước 3 — Phân loại và mở màn hình cuộc gọi / notification.**
- `n(CustomPushBean)` (`:11297`): nếu đã xử lý (VD: màn hình gọi đã mở — code kiểm tra
  `VideoCallActivity`/`VoiceCallActivity` có đang chạy không, `:2115`, `:9506`, `:13923`) thì thôi;
  nếu không thì notification qua `a0.e/d`.
- `A(json, …)` (`:2814`): parse JSON → `new AlarmInfo()` + `AlarmInfo.onParse(json)` (`:3275`),
  rồi `z(AlarmInfo, SDBDeviceInfo, String)` (`:15898`, gọi ở `:3720`).
- `y(SDBDeviceInfo, AlarmInfo, String)` (`:15569`) → `r(String devId, int, AlarmInfo)` (`:12622`,
  gọi ở `:15703`).
- Cả `r()` (`:12899`) và `z()` (`:16762`) đều gọi `XMPushManager.B(context, devId, int,
  event, originJson, …, id, startTime, alarmInfo)`.

**Bước 4 — `XMPushManager.B()` quyết định mở UI gọi.**
`B()` (`XMPushManager.java`, `x()` ở :727, cờ `v()` ở :716):
- Chỉ mở màn hình cuộc gọi đến `IDRVisitorActivity.E0(...)` khi event thuộc
  `LocalAlarm` (và `AbstractC4154a.r(type)` đúng — loại thiết bị chuông/IDR),
  `RemoteCallAlarm`, `DoorLockCall`, `ForceDismantleAlarm`, **và** cờ từng-thiết-bị
  `SP_K_OPEN_CALL_UI` đang bật (`v()` đọc SharedPreferences, mặc định `true`).
- Các event khác (gồm `IncomingCall` thuần) không đi qua nhánh mở `IDRVisitorActivity` trong
  `B()` — chúng hiển thị bằng text (`b()`, :175) và/hoặc notification; việc nhấc máy gọi video
  2 chiều chạy qua `VideoCallActivity` sau khi người dùng chạm vào thông báo/màn hình gọi.

**Payload kèm theo event** (`AlarmInfo` bean, `com/lib/sdk/bean/alarm/AlarmInfo.java`):
`event`, `eventEx`/`exevent`, `channel`, `sn` (serial thiết bị), `id` (alarm ID),
`startTime`, `status`, `title`, `content`, `originJson` (JSON gốc), `linkCenterExt`
(`msgType`, `alarmEvent`, `videoUrl`, `thumbnail`, …), `pic`/`image` (ảnh báo động nếu có).

**Kết luận luồng 1:** event nút bấm lấy được — nhưng **chỉ qua cloud MPS**, cần tài khoản XM +
subscribe + `AlarmPushService` chạy + (thường) Firebase/FCM làm kênh phụ. Không lấy được bằng
cách nói chuyện trực tiếp với camera qua LAN theo đường này.

---

## 3. LUỒNG 2 — FUNSDK P2P TRỰC TIẾP (KHÔNG TÌM THẤY)

- Grep toàn bộ `libFunSDK.so` vừa trích lại từ `xapk/config.arm64_v8a.apk`
  (35.375.880 byte, 182.911 dòng strings, `/tmp/icsee-btn/FunSDK.strings`):
  **`IncomingCall` = 0 kết quả, `DoorBell`/`door_bell`/`doorbell` = 0 kết quả.**
  Native SDK không có khái niệm yêu cầu gọi đến / chuông cửa.
- `DevSetAlarmListener` (`FunSDK.java:376`), `DevGetAlarmState` (`:311`),
  `SysOpenWXAlarmListen` (`:1436`), `SysThirdPartyOpenAlarmListen` (`:1529`),
  `DEV_GET_LAN_ALARM = 5132` (`EUIMSG.java:84`): tồn tại trong SDK nhưng **không có caller
  nào** trong toàn bộ cây Java lẫn smali (chỉ có định nghĩa). App không dùng chúng.
- `MonitorFragment` mở `VideoCallActivity` khi **người dùng chủ động** gọi đi
  (`AV-TALK-VIDEO-SEND.md` §1.3) — không có nhánh nhận cuộc gọi đến qua P2P.
- **Kết luận:** không có bằng chứng thiết bị đẩy event nút bấm qua kênh FunSDK P2P/LAN tới app.
  Muốn khẳng định chắc chắn 100% cần bắt gói live (tcpdump + logcat) khi bấm nút thật và xem
  có message FunSDK nào ngoài 6007 không — nhưng với 0 chuỗi native + 0 caller, khả năng này
  rất thấp.

---

## 4. LUỒNG 3 — DVRIP QUA LAN, KHÔNG CẦN FUNSDK/CLOUD (CƠ CHẾ ĐÃ CHỨNG MINH)

### 4.1. Cơ chế subscribe + nhận event (đã chứng minh bằng source đọc trực tiếp)

**`python-dvr` 0.0.1** (`/tmp/dvr-pkg/python-dvr-0.0.1/dvrip.py`, đã tải về để đọc):

```python
QCODES = { …, "AlarmInfo": 1504, "AlarmSet": 1500, …, "OPNetAlarm": 1506, … }

def setAlarm(self, func):            # :416 — đăng ký callback
    self.alarm_func = func

def alarmStart(self):                # :422 — subscribe
    self.alarm = threading.Thread(target=self.alarm_thread, args=[self.busy])
    self.alarm.start()
    return self.get_command("", self.QCODES["AlarmSet"])   # gửi opcode 1500

def alarm_thread(self, event):       # :431 — lắng nghe trên chính TCP connection đã login
    while True:
        event.acquire()
        (head, version, session, sequence_number, msgid, len_data) = \
            struct.unpack("BB2xII2xHI", self.socket_recv(20))
        reply = json.loads(self.socket_recv(len_data)[:-2])
        if msgid == self.QCODES["AlarmInfo"] and self.session == session:
            if self.alarm_func is not None:
                self.alarm_func(reply[reply["Name"]], sequence_number)  # callback nhận dict AlarmInfo
```

- Subscribe: **1 gói opcode 1500** (`AlarmSet`, body `{"Name": "", "SessionID": "0x…"}` theo
  code `get_command`), gửi trên TCP connection đã login (port 34567).
- Sau đó thiết bị **tự đẩy** JSON opcode **1504** (`AlarmInfo`) về trên cùng connection đó,
  không cần poll. Callback nhận nguyên dict `reply["AlarmInfo"]`.
- `alarm_thread` dùng chung socket điều khiển với các lệnh khác (khóa bằng `self.busy` Condition);
  monitor media chạy trên connection riêng.

**Xác nhận độc lập — `hass-xmeye`** (Home Assistant integration cho camera XM/DVRIP):
- README: alarm events là **push-based (`local_push`)** — "the integration maintains a
  persistent TCP connection and receives alarm notifications in real time with no polling delay".
  Binary sensor: motion, video loss, video blind/tamper, alarm input, I/O alarm, cross-line, intrusion.
- `docs/protocol.md` §4 (đo live trên NBD8008R-U, firmware `V4.03.R11.061B0197`):
  `1500 / 1504 / 1506 | AlarmSet / AlarmInfo / OPNetAlarm`.
- Từ vựng event DVRIP (commit `1a84880`): `"VideoMotion" → "MotionDetect"`,
  `"LocalAlarm" → "AlarmLocal"` (alias theo variant firmware), `appEventHumanDetectAlarm`,
  `FaceDetect`, …

### 4.2. Nút gọi video sinh ra event DVRIP nào? — CHƯA CHỨNG MINH

- **Chưa có bằng chứng trực tiếp** nào cho thấy nút gọi video của DOSEN RPO V1 sinh ra
  `AlarmInfo` (1504), và nếu có thì `Event` bằng gì. Không có trong APK (nút bấm là hành vi
  firmware), không có trong `python-dvr`/`hass-xmeye` (họ không có loại event "video call request").
- **Suy đoán có cơ sở mạnh nhất: `LocalAlarm`.** Căn cứ: (a) nút bấm trên thiết bị XM là một
  ngõ vào alarm local của firmware — đúng loại event mà DVRIP `AlarmInfo` mang
  (`hass-xmeye` map `LocalAlarm` → sensor `AlarmLocal`); (b) phía app, event `LocalAlarm`
  được dịch thành `Caller` và **là event duy nhất (cùng nhóm chuông cửa) mở màn hình gọi đến**
  (`XMPushManager.x()`, :727); (c) `TYPE_DOOR_BELL`/`MSG_TYPE_DOOR_BELL` tồn tại riêng cho
  chuông cửa. Nhưng đây vẫn là suy đoán — firmware của đúng mẫu RPO V1 có thể dùng event khác
  (VD: một event riêng không có trong từ vựng DVRIP đã biết), hoặc chỉ gửi qua cloud MPS mà
  không phát 1504.
- **Phân biệt rõ 2 loại "event nút bấm" dễ nhầm:**
  - `LocalAlarm` (DVRIP 1504 / cloud): chuông/nút bấm local — **có thể lấy qua LAN**.
  - `IncomingCall` (chỉ thấy ở tầng cloud MPS / `AlarmInfo.Event` của app): yêu cầu gọi video
    2 chiều do thiết bị khởi xướng — **chưa thấy đường LAN nào mang event này**; có thể nó chỉ
    tồn tại sau khi cloud MPS dịch từ alarm gốc của thiết bị.
- **Cần test live để kết luận** (xem §6): subscribe 1500 vào cam DOSEN thật, bấm nút, ghi lại
  payload 1504 nhận được (kèm timestamp). Nếu không thấy 1504 nào khi bấm → nút này không đi
  qua DVRIP alarm, chỉ còn đường cloud 6007.

---

## 5. SERVICE DOCKER HIỆN TẠI — THIẾU GÌ ĐỂ NHẬN EVENT

Service trong `~/workspace/icsee-docker/` (`app/dvrip.py`, `app/main.py`):

- **Hiện tại: 0 code alarm.** Grep `alarm` trong `app/` + `README.md` = 0 kết quả.
  Các endpoint hiện có: `/api/health`, `/api/status`, `/api/cam/connect`,
  `/api/cam/decoder-pram`, `/api/audio/talk/*`, `/api/audio/mic`, `/api/video/*` — không có
  endpoint event nào.
- **Cần thêm (đề xuất cụ thể):**
  1. **Connection alarm riêng:** `DVRIPClient` hiện dùng 1 socket duy nhất (`self.sock`,
     `dvrip.py:110-121`); vòng lặp monitor chiếm socket đó (`monitor_claim_start`, :266).
     Mở thêm 1 TCP connection tới cam (port 34567) sau login — tái dùng `SessionID`
     trên connection mới (mẫu đã chứng minh trong `hass-xmeye/docs/protocol.md` §9:
     login là theo session, không theo socket; giới hạn `TCPMaxConn` mặc định 10) —
     hoặc 1 reader thread chia sẻ socket điều khiển theo mẫu `python-dvr` (`busy` Condition).
  2. **Subscribe:** gửi opcode **1500** (`AlarmSet`) sau login.
  3. **Parser 1504:** đọc header DVRIP 20 byte, `msgid == 1504` → parse JSON → dict `AlarmInfo`
     (`Event`, `Channel`, `StartTime`, …). Lưu ý: `_skip_json_replies()` (`dvrip.py:287`)
     hiện **vứt bỏ** mọi JSON trong luồng monitor — alarm KHÔNG đi qua connection monitor
     mà đi qua connection điều khiển, nên parser phải đặt ở connection alarm riêng, không
     dùng chung hàm skip này.
  4. **API endpoint mới:** VD `GET /api/events` (SSE stream) hoặc WebSocket, kèm
     `POST /api/events/subscribe` / `POST /api/events/stop`; mỗi event trả về nguyên JSON
     `AlarmInfo` + `received_at`. Thêm trường `video_call_button` suy ra khi
     `Event == "LocalAlarm"` (đánh dấu là suy đoán, không khẳng định).
  5. **Không cần** FunSDK, APP key, cloud, hay tài khoản XM cho đường này — chỉ cần IP cam +
     user/password DVRIP (đã có trong `.env` của service).
- **Giới hạn còn lại sau khi làm xong (4):** vẫn chưa biết chắc event của nút RPO V1 là gì
  cho tới khi test live (§6). Service chỉ có thể báo "đã nhận event X", không thể tự kết luận
  "đây là nút gọi video" nếu firmware dùng tên event lạ.

---

## 6. CÁCH XÁC MINH (LIVE TEST, CẦN CAM THẬT)

1. **Test DVRIP alarm (quyết định):** chạy `python-dvr` (đã tải ở `/tmp/dvr-pkg/`) hoặc
   service Docker sau khi thêm endpoint event → `login()` → `setAlarm(callback ghi log)` →
   `alarmStart()` → **bấm nút trên cam** → ghi lại mọi JSON 1504 nhận được trong ~10 s
   (kèm giờ bấm). Nếu thấy `Event: "LocalAlarm"` (hoặc tên khác) đúng lúc bấm → đã chứng minh.
   Lặp lại 2–3 lần để loại trừ alarm motion ngẫu nhiên.
2. **Test cloud (đối chiếu):** cùng lúc bấm nút, xem app iCSee có đổ chuông/mở màn hình gọi
   không + `adb logcat` lọc `AlarmPushService` (log `收到报警消息`, message 6007) để đối chiếu
   event cloud (`IncomingCall`/`LocalAlarm`) với event DVRIP 1504 cùng một lần bấm.
3. **Test trạng thái (nếu muốn chắc):** thử `DevGetAlarmState` qua FunSDK (cần app key) hoặc
   query config `AlarmInfo` qua DVRIP opcode 1042 — kỳ vọng: không có trạng thái nút;
   chỉ ghi nhận kết quả, không giả định trước.
4. **Nếu 1504 không xuất hiện khi bấm nút:** kết luận nút này chỉ đi cloud (6007); khi đó
   muốn lấy event từ ngoài app chỉ còn cách chạy service MPS giả (đăng ký `LinkDev` bằng
   token tài khoản — cần nghiên cứu thêm, ngoài phạm vi báo cáo này).

---

## 7. NGUỒN / FILE THAM CHIẾU

- APK Java: `~/workspace/icsee-apk/decompiled/jadx/sources/com/xworld/manager/XMPushManager.java`
  (`b()`:175, `x()`:727, `v()`:716); `com/lib/sdk/bean/alarm/AlarmInfo.java`;
  `com/lib/Mps/MpsClient.java` (6000/6001/6007/6011/6015/6019/6020/6032);
  `com/lib/EUIMSG.java` (`DEV_GET_LAN_ALARM`:84, `MC_ON_AlarmCb`:167);
  `com/lib/FunSDK.java` (`DevGetAlarmState`:311, `DevSetAlarmListener`:376,
  `SysOpenWXAlarmListen`:1436); `com/manager/device/idr/IdrDefine.java:153` (`isDoorbell`).
- APK smali: `~/workspace/icsee-apk/decompiled/apktool/smali_classes5/com/xworld/service/push/AlarmPushService.smali`
  (`OnFunSDKResult`:5090, nhánh 6007; `G()`:4226; `A()`:2814; `AlarmInfo` mới:3275,14528;
  `z()`:15898; `r()`:12622; `y()`:15569; `B()` tại :12899, :16762);
  `smali_classes4/com/manager/push/XMPushManager.smali` (`TYPE_DOOR_BELL`…);
  `smali_classes3/com/xm/device/idr/ui/visitor/view/IDRVisitorActivity.smali` (`E0`:158).
- Native: `libFunSDK.so` trích lại từ `xapk/config.arm64_v8a.apk` → `/tmp/icsee-btn/`
  (35.375.880 byte; strings 182.911 dòng `/tmp/icsee-btn/FunSDK.strings`;
  `IncomingCall`/`DoorBell` = 0 kết quả; `FUN_DevSetAlarmListener`,
  `FUN_SysOpenWXAlarmListen`, `CMpsClientV2` có tồn tại).
- DVRIP: `python-dvr` 0.0.1 (`/tmp/dvr-pkg/python-dvr-0.0.1/dvrip.py`:
  `QCODES` AlarmSet 1500 / AlarmInfo 1504 / OPNetAlarm 1506; `setAlarm`:416;
  `alarmStart`:422; `alarm_thread`:431–449); `hass-xmeye` README (local_push) +
  `docs/protocol.md` §4 (1500/1504/1506, đo live NBD8008R-U) — nguồn web, đã trích dẫn trong báo cáo.
- Docker service: `~/workspace/icsee-docker/app/dvrip.py` (monitor :266, `_skip_json_replies` :287,
  media packet :318–340; không có code alarm), `app/main.py` (endpoint hiện có).
- Báo cáo này: `~/workspace/icsee-apk/BUTTON-PRESS-EVENT.md`
