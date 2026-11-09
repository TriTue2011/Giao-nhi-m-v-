# Tổng hợp zca-js — Docs + Code (đọc trực tiếp từ repo)

Ngày đọc: 09/11/2026. Người đọc: Muse (theo lệnh của Việt).
Mục đích: làm tài liệu tham chiếu để sửa app Zalo PC (`zalo-pc-app/`, nhánh `muse/zalo-addon-pivot`) — đặc biệt lỗi gọi đi không đổ chuông (nghi phạm số 1: codec trong 11301), gọi đến chưa xử lý (11303), chưa có tiếng (SRTP chưa nối), gửi thoại 114 + STT 13394 chưa test live.

## 0. Nguồn đã đọc (provenance)

| Nguồn | Phiên bản / commit | Ghi chú |
|---|---|---|
| Docs | https://softtyos.github.io/zca-js-docs/ | Đọc các trang: chủ, `guide/getting-started`, `guide/architecture`, `guide/call-engine`, `guide/cookbook`, `guide/listeners`, `api/call`, `api/chat`, `api/group`, `api/media`, `api/models` |
| Code (GitHub) | repo `softtyos/zca-js`, clone tại `~/workspace/zca-js-softtyos`, HEAD `e1c09a98a1c9cee35377a8d392ac9b5688a7d1de` (2026-11-05, «docs: remove company branding and standardize open-source metadata»), package `@softtynet/zca-js` **v2.3.13** | **Đây là repo gốc của docs** — có đủ `src/call-engine/` và `src/apis/call/` |
| Code (NPM) | `@softtynet/zca-js@2.3.13` từ NPM Registry (tải bằng `npm pack`, giải nén tại `/tmp/zca-npm/package`) | Cùng version 2.3.13, code build (`dist/`) khớp với repo GitHub — dùng để đối chiếu chéo |
| Cài đặt | `npm install @softtynet/zca-js` (hoặc `bun add` / `pnpm add`) — yêu cầu Node.js `>= 20` hoặc Bun `>= 1.1`, TypeScript `>= 5` khuyến nghị | Theo trang getting-started |

**Cảnh báo về repo cũ:** repo `RFS-ADRENO/zca-js` (v2.2.0, HEAD `2a7e3602`, cũng clone tại `~/workspace/zca-js`) là bản cũ, **không có call engine** (không có `src/call-engine/`, không có `api.call`, chỉ 159 file API phẳng). Mọi phần về gọi thoại trong báo cáo này lấy từ bản **softtyos 2.3.13**, không phải bản RFS-ADRENO. Đừng dùng bản RFS-ADRENO làm tham chiếu cho gọi thoại.

**Lưu ý về số liệu trên docs:** số API mỗi domain **không nhất quán giữa các trang** (ví dụ trang chủ ghi `api.call` 30 / `api.chat` 52 / `api.group` 46 / `api.media` 8; trang architecture ghi `call` 27 / `group` 47 / `sync` 11 / `zcloud` 17; trang getting-started ghi số khác hẳn). Con số dùng trong báo cáo này lấy theo **trang API reference từng domain** và **đếm file code thực tế** (ví dụ `src/apis/call/` có đúng 30 file: 28 API + `createRtcSession` + `createController`).

**Tính chất:** zca-js là SDK **không chính thức** (unofficial, reverse-engineered). Zalo có thể khóa tài khoản dùng nó — **chỉ dùng tài khoản phụ**, giống quy tắc đã chốt cho mọi thử nghiệm Zalo.

## 1. Tổng quan zca-js là gì

`@softtynet/zca-js` là bộ SDK Zalo API cho Node.js / TypeScript / Bun: **333 API trên 12 phân hệ (domain)**, thiết kế theo Domain-Driven Design, lazy memoized getters, hỗ trợ đầy đủ TypeScript IntelliSense. Mọi phương thức gọi được theo phân hệ `api.<domain>.<method>()` hoặc gọi phẳng `api.<method>()` (alias tương thích ngược).

### 1.1. Kiến trúc 5 tầng (trang `guide/architecture`)

```
Tầng 5: 12 phân hệ nghiệp vụ (333 API)
Tầng 4: WebSocket realtime — Listener (watchdog 50s, ping/pong, xoay endpoint, 18 events)
Tầng 3: Điều phối dịch vụ — service-router (zpw_service_map_v3 + fallback), zcloud-client
Tầng 2: Lõi mật mã — AES-CBC (params), WS AES-GCM 128-bit + Pako, ZCloud 98yS (AES-256-CBC),
        ZDB 4.0 (RSA-2048 + chunk 64KB)
Tầng 1: Hằng số giao thức — zpw_type=30, zpw_ver=689, voicecall=24;
        preParseJsonIds / JSONBig (bảo toàn UID 19 chữ số)
```

- **Bảo toàn số nguyên 64-bit (`preParseJsonIds`):** nhiều API Zalo trả UID 19 chữ số dạng JSON Number không có ngoặc kép. `JSON.parse()` thường làm tròn mất 3 chữ số cuối (vượt `Number.MAX_SAFE_INTEGER`). zca-js chuyển các trường ID 16+ chữ số (`owner_id`, `group_id`, `uidFrom`, `idTo`, `globalMsgId`, `cliMsgId`…) sang string trước khi parse — giống cơ chế `preParse` trong `app.asar` của Zalo PC. App Python cần giữ nguyên tắc tương tự (UID luôn là string, không parse thành số).
- **Lỗi chuẩn hóa:** mọi lỗi server đều thành `ZaloApiError` kèm `code` số (ví dụ 215 bị chặn, 222 đối phương đã gửi lời mời trước). Lớp con: `ZaloApiLoginQRAborted`, `ZaloApiLoginQRDeclined`, `ZaloApiMissingImageMetadataGetter`.

### 1.2. 12 phân hệ (domain)

| Phân hệ | Số API (theo trang API ref) | Nội dung chính |
|---|---|---|
| `api.auth` | 14 | Xác thực, QR, phiên (`exportSession`), thiết bị (`getListDevice`), giải mã `globalId` (`encryptGids`/`decryptGids`), `getNoisedIds` |
| `api.chat` | 52 | Tin nhắn 1-1/nhóm/OA, ảnh/video/voice/card, thu hồi, dịch AI, đã nhận/đã xem |
| `api.group` | 46 | Nhóm/Cộng đồng, thông tin nhóm V1–V4, lịch sử Cloud, trạng thái thành viên, phân quyền |
| `api.friend` | 37 | Bạn bè, danh bạ V2, lời mời, biệt danh, chặn, kiểm tra online PC/Web |
| `api.profile` | 22 | Hồ sơ, Mini Profile, avatar, quyền riêng tư, Emoji Status, EKYC |
| `api.sync` | 10–11 | Đồng bộ Mobile ZDB 4.0 (RSA-2048, AES-256-CBC multi-chunk), backup, cross-DB |
| `api.zcloud` | 16–17 | ZCloud/ZFamily, ViewerKey 98yS, link tải hàng loạt |
| `api.call` | 30 | Gọi thoại/video 1-1, gọi nhóm, Call Engine (ZaloRtcSession UDP/SRTP 2 chiều) |
| `api.media` | 8 | Kho lưu trữ Media/File/Link, `uploadAttachment`, `voiceToText` |
| `api.sticker` | 24 | Nhãn dán, GIF Giphy/Guggy/Tenor, hiệu ứng tin nhắn |
| `api.board` | 38 | Ghim, ghi chú, bình chọn, nhắc hẹn, Zalo To-Do |
| `api.business` | 36 | Zalo OA, nhãn CRM, tin nhắn nhanh, trả lời tự động, catalog, ngân hàng |

## 2. Cách dùng / khởi tạo (getting-started + cookbook)

### 2.1. Cài đặt

```bash
npm install @softtynet/zca-js
# hoặc: bun add @softtynet/zca-js / pnpm add @softtynet/zca-js
```

### 2.2. Đăng nhập lần đầu bằng QR + lưu phiên

```ts
import { Zalo } from "@softtynet/zca-js";
import fs from "node:fs/promises";

const zalo = new Zalo({
    selfListen: true,   // nhận cả sự kiện do chính tài khoản mình gửi từ thiết bị khác
    logging: true,
    requestTimeout: 30000,
});
const api = await zalo.loginQR({ qrPath: "./qr.png" });
console.log("Đăng nhập thành công UID:", api.getOwnId());

// Lưu phiên để tái sử dụng, không cần quét lại QR
const session = api.auth.exportSession(); // {cookie, imei, userAgent, language, uid}
await fs.writeFile("./zalo-session.json", JSON.stringify(session, null, 2));
```

### 2.3. Khôi phục phiên đã lưu

```ts
const zalo = new Zalo({ selfListen: true, requestTimeout: 30000 });
const savedSession = JSON.parse(await fs.readFile("./zalo-session.json", "utf-8"));
const api = await zalo.login(savedSession);
```

### 2.4. Lắng nghe sự kiện realtime

```ts
api.listener.on("connected", () => {
    api.listener.sendPingActive();
    api.listener.requestLastDeliverSeen();
});
api.listener.on("message", (msg) => { /* msg.data.uidFrom, msg.data.content */ });
api.listener.on("call_event", (ev) => { /* ev.act, ev.callId, ev.fromUid */ });
api.listener.start({ retryOnClose: true });
```

### 2.5. Công thức thực hành quan trọng (cookbook — 10 kịch bản)

1. **Lưu/khôi phục phiên** — thử `login(savedSession)` trước, lỗi thì mới `loginQR()` rồi `exportSession()` lưu lại.
2. **Đa tài khoản** — mỗi tài khoản một proxy riêng + `userAgent` và `imei` cố định (`agent`, `polyfill: node-fetch`).
3. **Quét dữ liệu lớn** — phân trang bằng `nextCursor`/`last_id` + nghỉ 300–350 ms giữa các trang để bảo vệ tài khoản.
4. **WebSocket bền bỉ 24/7** — `Listener` + KeepAlive + 4 outbound WS request khi `connected`.
5. **Xử lý lỗi tập trung** — bắt `ZaloApiError`, rẽ nhánh theo `err.code`.
6. **Gọi thoại/video** — xem mục 4 dưới đây.
7. **Zalo OA** — `preloadConversations().pageMessages`, sự kiện `oa_message` / `oa_event`, `blockOA`/`unblockOA`.
8. **Dịch AI** — 5 API `zpw_type=30`: `translateMessageManual` (13397), `translateMessageAuto` (13398), `translateMessageSuggest` (13399), `getTranslateSetting` (13395), `updateTranslateSetting` (13396); kết quả async về qua `translate_event`.
9. **Zalo To-Do / nhắc hẹn / bảng tin** — `verifyTodo`, `createTodo`, `getListOneOneBoard`, sự kiện `todo_event` / `poll_event`.
10. **GIF / hiệu ứng / nhãn CRM** — `getTrendingGiphyGifs`, `searchGuggyGifs`, `getMessageEffects`, `getConversationLabels`.

## 3. API chính (bảng)

### 3.1. `api.call` — 30 API (đầy đủ, từ trang `api/call`)

| Phương thức | HTTP | Endpoint | Lệnh / signal | Mô tả |
|---|---|---|---|---|
| `requestVoiceCall` | GET | `/api/voicecall/requestcall` | **11300** / 401 | Bước 1 gọi 1-1: xin cấp phát phòng gọi (trả `callId`, `sessId`, `rtpServer`, `rtcpServer`, `zrtpKey`, `codec`) |
| `sendRequestVoiceCall` | GET | `/api/voicecall/request` | **11301** / 416 | Bước 2 gọi 1-1: gửi gói mời gọi kèm `extendData` ZRTC để máy đối phương đổ chuông |
| `ringRingVoiceCall` | GET | `/api/voicecall/ringring` | **11302** / 407 | Báo thiết bị đang đổ chuông cho cuộc gọi 1-1 đến |
| `answerVoiceCall` | GET | `/api/voicecall/answer` | **11303** / 402 | Bắt máy cuộc gọi 1-1 đến |
| `answerAckVoiceCall` | GET | `/api/voicecall/answerack` | **11304** / 408 | Xác nhận hoàn tất bắt tay nhận cuộc gọi 1-1 |
| `cancelVoiceCall` | GET | `/api/voicecall/cancel` | **11305** / 405 | Hủy cuộc gọi 1-1 đang đổ chuông trước khi đối phương bắt máy |
| `endVoiceCall` | GET | `/api/voicecall/endcall` | **11306** / 404 | Kết thúc cuộc gọi 1-1 đang diễn ra / từ chối cuộc gọi đến |
| `holdVoiceCall` | GET | `/api/voicecall/holdreq`, `/holdresp` | 11307 / 11308, signal 411/412 | Tạm giữ / phản hồi tạm giữ |
| `unholdVoiceCall` | GET | `/api/voicecall/unholdreq`, `/unholdresp` | 11309 / 11310, signal 413/414 | Khôi phục / phản hồi khôi phục |
| `logEndVoiceCall` | GET | `/api/voicecall/logendcall` | **11311** / 406 | Thống kê chất lượng cuộc gọi (QoS/Billing) sau khi kết thúc |
| `updateCallMediaState` | GET | `/api/voicecall/conf` | 12006 | Đồng bộ trạng thái Mic/Camera trong cuộc gọi 1-1 |
| `requestAudioToVideoCall` | GET | `/api/voicecall/requestaudio2video` | 12056 | Nâng cấp thoại → video (hoặc phản hồi) |
| `requestShareScreenCall` | GET | `/api/voicecall/requestsharescreen` | 12064 | Yêu cầu bắt đầu/kết thúc chia sẻ màn hình |
| `requestGroupCall` | GET | `/api/voicecall/group/requestcall` | 12433 | Bước 1 gọi nhóm: xin cấp phát phòng gọi nhóm |
| `sendRequestGroupCall` | GET | `/api/voicecall/group/request` | 12434 | Bước 2 gọi nhóm: phát tín hiệu mời gọi tới thành viên |
| `addUserGroupCall` | GET | `/api/voicecall/group/adduser` | 12435 | Mời thêm thành viên vào cuộc gọi nhóm đang diễn ra |
| `answerGroupCall` | GET | `/api/voicecall/group/answer` | 12436 | Chấp nhận tham gia cuộc gọi nhóm |
| `cancelGroupCall` | GET | `/api/voicecall/group/cancel` | 12437 | Hủy lời mời gọi nhóm |
| `endGroupCall` | GET | `/api/voicecall/group/endcall` | 12438 | Rời khỏi / từ chối lời mời gọi nhóm |
| `ringRingGroupCall` | GET | `/api/voicecall/group/ringring` | 12439 | Báo đang đổ chuông cho lời mời gọi nhóm |
| `joinGroupCall` | GET | `/api/voicecall/group/join` | 12043 | Tham gia cuộc gọi nhóm đang diễn ra từ banner |
| `shareScreenGroupCall` | GET | `/api/voicecall/group/sharescreen` | 12044 | Bắt đầu/dừng chia sẻ màn hình trong gọi nhóm |
| `getGroupCallState` | GET | `/api/voicecall/group/state` | 12445 | Truy vấn trạng thái + danh sách thành viên phòng gọi nhóm |
| `finishGroupCall` | GET | `/api/voicecall/group/finish` | 12446 | Kết thúc hoàn toàn phòng gọi nhóm cho mọi thành viên |
| `notifyGroupCall` | GET | `/api/voicecall/group/notify` | 12447 | Gửi thông báo sự kiện gọi nhóm vào luồng chat nhóm |
| `pingGroupCall` | GET | `/api/voicecall/group/ping` | 12097 | Nhịp tim duy trì kết nối thành viên trong gọi nhóm |
| `broadcastGroupCallState` | GET | `/api/voicecall/group/broadcast` | 12098 | Quảng bá trạng thái Mic/Camera/Screen Share tới thành viên |
| `createRtcSession` | — | (local) | — | Tạo phiên gọi thoại/video 2 chiều `ZaloRtcSession` (UDP ZRTPPacket + SRTP + H.264) |
| `createController` | — | (local) | — | Tạo `ZaloCallController` quản lý vòng đời gọi đi/đến + kênh IPC cục bộ |
| `sendVoiceCall` | GET | `/api/voicecall/requestcall` + `/request` | 11300 + 11301 | Gọi 1-1 trọn gói (tự chạy 2 bước 11300 + 11301) |

### 3.2. `api.chat` — 52 API (chọn hàm liên quan tới app)

| Phương thức | HTTP | Endpoint | Mô tả |
|---|---|---|---|
| `sendMessage` | POST | `/api/message`, `/api/group` | Gửi văn bản, trích dẫn, @mention, đính kèm (ảnh/file/GIF) tới cá nhân/nhóm |
| `sendVoice` | POST | `/api/message/forward`, `/api/group/forward` | Gửi tin nhắn thoại (Voice / Audio MP3 / AAC) — xem mục 5.1 |
| `sendVideo` | POST | `/api/message/forward`, `/api/group/forward` | Gửi video kèm thumbnail + thời lượng |
| `sendSticker` | POST | `/api/message/sticker`, `/api/group/sticker` | Gửi nhãn dán |
| `sendCard` | POST | `/api/message/forward`, `/api/group/forward` | Gửi danh thiếp liên hệ (Contact Card / QR) |
| `sendLink` | POST | `/api/message/link`, `/api/group/sendlink` | Gửi tin nhắn kèm link preview |
| `forwardMessage` | POST | `/api/message/mforward`, `/api/group/mforward` | Chuyển tiếp tin nhắn tới nhiều hội thoại |
| `undo` / `undoMultiMessage` | POST | `/api/message/undo`, `/api/group/undomsg` | Thu hồi 1 / nhiều tin nhắn |
| `addReaction` | POST | `/api/message/reaction`, `/api/group/reaction` | Thả biểu cảm (Tim, Like, Haha, Wow, Buồn, Giận) |
| `sendSeenEvent` / `sendDeliveredEvent` | POST | `/api/message/seenv2`, `/deliveredv2` (+ `/group/…`) | Xác nhận Đã xem / Đã nhận |
| `sendTypingEvent` | POST | `/api/message/typing`, `/api/group/typing` | Tín hiệu đang soạn tin |
| `getLastSeen` | GET | `/api/preloadconvers/get-last-seen` | Trạng thái đã xem cuối cùng (command 12009) |
| `getDirectMessageStatus` | POST | `/api/message/getStatusMsg` | Trạng thái deliver/seen 1-1 (command 12016) |
| `preloadConversations` | GET | `/api/preloadconvers/get-last-msgs` | Tải trước tin nhắn cuối + trạng thái đọc (command 10053) |
| `getGroupChatHistory` | GET | `/api/cm/getrecentv2` (12506), `/api/cm/getoldv2` (12507) | Lịch sử tin nhắn nhóm từ Cloud (nằm ở cả chat và group) |
| `renewMessageLink` | POST | `/api/message/renewlink` | Gia hạn link tải file đã hết hạn (command 12094) |
| `translateMessage*` | POST | `/api/aifeatures/translate/v1/*` | Dịch AI: manual 13397, auto 13398, suggest 13399; setting 13395/13396 |

### 3.3. `api.media` — 8 API (đầy đủ)

| Phương thức | HTTP | Endpoint | Lệnh | Mô tả |
|---|---|---|---|---|
| `getConversationMedia` | GET | `/api/mediastore/list` | 11841 | Kho lưu trữ nhóm (media/file/link) |
| `getMediaStorePreview` | POST | `/api/mediastore/preview` | 11843 | Xem trước nhanh kho lưu trữ nhóm |
| `getPersonalMedia` | GET | `/api/media/oneone/list` | 12220 | Kho lưu trữ Cloud của tôi (Send2Me) |
| `getPersonalMediaPreview` | POST | `/api/media/oneone/preview` | 12221 | Xem trước nhanh kho Send2Me |
| `removeConversationMedia` | POST | `/api/mediastore/remove` | 11842 | Xóa mục khỏi kho lưu trữ nhóm |
| `removePersonalMedia` | POST | `/api/media/oneone/remove` | 12222 | Xóa mục khỏi kho Send2Me |
| `uploadAttachment` | POST | `/api` | — | Tải file (ảnh/video/file) lên server Zalo, trả `fileUrl`/`fileId` trước khi gửi; tham số chunk: `totalChunk`, `chunkId`, `clientId`, `totalSize`, `isE2EE`, `jxl` |
| `voiceToText` | POST | `/api/aifeatures/voice2text` | **13394** | STT bằng Zalo AI — xem mục 5.2 |

### 3.4. `api.group` — 46 API (chọn hàm chính; app hiện tập trung gọi 1-1 + nhắn tin nên chỉ tóm tắt)

`createGroup` (POST `/api/group/create/v2`), `getAllGroups` (GET `/api/group/getlg/v4`), `getGroupInfo` (POST `/api/group/getmg-v2`), `getGroupInfoV2` (GET `/api/group/getgi`, `/getgi/v2`, command 11162), `getGroupListV3` (11161), `getGroupChatHistory` (`getrecentv2` 12506 / `getoldv2` 12507), `getGroupMessageStatus` (POST `/api/group/getStatusMsg`, 12017), `addUserToGroup` (POST `/api/group/invite/v2`), `removeUserFromGroup` (POST `/api/group/kickout`), `changeGroupName` / `changeGroupAvatar` / `changeGroupOwner`, `getGroupBlockedMember`, `addGroupDeputy`/`removeGroupDeputy`, `getPendingGroupMembers`/`reviewPendingMemberRequest`, `enableGroupLink`/`disableGroupLink`/`joinGroupLink`, `leaveGroup`, `disperseGroup`, `upgradeGroupToCommunity`, `analyseGroup` (12407).

### 3.5. `api.auth` — các hàm chính

`loginQR` (QR + callback `QRCodeGenerated`/`QRCodeExpired`/`QRCodeScanned`/`QRCodeDeclined`/`GotLoginInfo`), `login` (khôi phục phiên), `exportSession`, `getListDevice`, `getQR` (lấy mã QR của user), `getCookie`, `getContext`, `keepAlive`, `decryptGids`/`encryptGids`, `getNoisedIds`, `scanURL`.

### 3.6. Model / enum quan trọng

```ts
// CallType — src/apis/call/sendVoiceCall.ts
enum CallType { Audio = 1, Video = 3, GroupAudio = 5, GroupVideo = 6 }
// Chuẩn hóa loại gọi nhóm: GroupAudio (5) hoặc 0 → 0 (thoại nhóm);
// GroupVideo (6), Video (3) hoặc 1 → 1 (video nhóm).

// CallEventType — src/models/CallEvent.ts
enum CallEventType {
    REQUEST = "request", ANSWER = "answer", ANSWER_ACK = "answer_ack",
    CANCEL = "cancel", END = "end", RINGRING = "ringring",
    ONOFF_CAMERA = "onoff_camera", MUTE_AUDIO = "mute_audio",
    AUDIO_TO_VIDEO = "audio_to_video", SHARE_SCREEN = "share_screen",
    GROUP_REQUEST = "group_request", GROUP_RINGRING = "group_ring_ring",
    GROUP_ANSWER = "group_answer", GROUP_ANSWER_ACK = "group_answer_ack",
    GROUP_CANCEL = "group_cancel", GROUP_END = "group_end_call",
    GROUP_ADD_USER = "group_add_user", GROUP_JOIN = "group_join_call",
    GROUP_NOTIFY = "group_notify", GROUP_BROADCAST = "group_broadcast",
    GROUP_BROADCAST_CONFIG = "group_broadcast_config", UNKNOWN = "unknown",
}
type TCallEventData = {
    callId?: number; call_id?: number; uidN?: string | number;
    callerId?: string | number; calleeId?: string | number;
    session?: string; sessId?: string; status?: number;
    callType?: number; codec?: string;
    params?: string | Record<string, unknown>; ts?: number | string;
    [key: string]: unknown;
};
type CallEvent = { type: CallEventType; act: string; act_type: string; data: TCallEventData };
```

Các enum khác: `ThreadType` (User/Group), `Reactions`, `GroupEventType`, `FriendEventType`, `BoardType`, `SyncEventType`, `Gender`, `DestType`. Lỗi: `ZaloApiError` (`code: number | null`), `ZaloApiLoginQRAborted`, `ZaloApiLoginQRDeclined`.

## 4. Call Engine — chi tiết đầy đủ (phần quan trọng nhất cho app)

Nguồn: trang `guide/call-engine`, code `src/call-engine/` (`ZaloRtcSession.ts` 5948 dòng, `ZRTPPacketCodec.ts` 1094 dòng, `ZaloSrtpSession.ts` 570 dòng, `ZaloCallController.ts` 956 dòng, `ZaloCallTransport.ts` 311 dòng) + `src/apis/call/`.

Bộ máy: `ZaloRtcSession` — UDP `ZRTPPacket` + `SRTP AES-CM-128-HMAC-SHA1-80` + `Opus 16kHz` + `H.264 Annex-B FU-A`, chạy độc lập trên Node.js / Bun / Electron / Server Gateway, không phụ thuộc ứng dụng Zalo PC.

### 4.1. Hai tầng

| Tầng | Thành phần |
|---|---|
| **1. Báo hiệu (Signaling)** — HTTP `zpw_type=24` + WebSocket `cmd=601/604` | Gọi 1-1: `requestVoiceCall` (11300) → `sendRequestVoiceCall` (11301). Gọi nhóm: `requestGroupCall` (12433) → `sendRequestGroupCall` (12434). Sự kiện WS `call_event`: `request`, `ringring`, `answer`, `group_request`, `group_answer`, `group_broadcast`… Đồng bộ trạng thái: `updateCallMediaState` (12006), `pingGroupCall` (12097), `broadcastGroupCallState` (12098) |
| **2. Media (ZaloRtcSession UDP/SRTP)** | Bắt tay UDP: Echo (`cmd=248`) → InitCall (`cmd=1`) / InitZaviPing (`cmd=53`) → ZaviRoomUpdated (`cmd=50`). Audio: Opus 16kHz Mono (PT=112, SSRC 32-bit). Video: H.264 Constrained Baseline (PT=97/98, Annex-B FU-A `0x1c`, extension `0xBEDE` 24B). Gọi nhóm qua Zavi SFU: tự tách `CSRC[0]` → partnerId (UID 19 chữ số) |

### 4.2. Khởi tạo + sự kiện

```ts
const session = api.call.createRtcSession({
    autoAttachListener: true,  // tự lắng nghe call_event từ api.listener
    autoKeepaliveMedia: true,  // tự gửi gói giữ kết nối UDP/RTP + RTCP Receiver Report
});
session.on("state", (s) => {}); // idle|allocating|handshaking_udp|inviting|ringing|
                                 // answering|active|ending|ended
session.on("audio_frame", (f) => {}); // f.payload: Buffer Opus 16kHz Mono 20/40ms;
                                      // f.ssrc (32-bit VoIP UID người nói), sequenceNumber, timestamp
session.on("video_annexb_frame", (f) => {}); // f.annexB: Buffer (00 00 00 01 + SPS/PPS/IDR/P-Slice);
                                              // f.isKeyframe (NAL type 5 IDR); f.partnerId (UID 19 chữ số)
session.on("media_state_change", (ev) => {}); // rawAct: conf|audio2video|group_answer|
                                              // group_broadcast|group_join|group_leave; partnerId;
                                              // isMicMuted, isCameraOn, isScreenSharing
session.on("ended", (reason) => {});
```

### 4.3. Gọi đi 1-1 — flow đầy đủ (`ZaloRtcSession.startOutgoingCall`, `src/call-engine/ZaloRtcSession.ts:1902`)

```
1. requestVoiceCall (11300, signal 401): {calleeId, callId, codec, typeRequest, imei}
   → trả sessId, rtpaddr, rtcpaddr, zrtpKey, codec
   → applyServerInfo(): nếu serverInfo.codec khác "[]" thì DÙNG codec server trả về
   → nếu có srtpKey (dài ≥ 40) và srtpMode != 0: lập ZaloSrtpSession
2. Mở socket UDP + bắt tay ZRTP InitCall (0x01 0x7e, cmd=11) tới rtpaddr → nhận routingToken
   (bỏ qua nếu signalingOnly: true — khi đó routingToken = callId >>> 0)
3. sendRequestVoiceCall (11301, signal 416): {calleeId, rtcpAddress, rtpAddress,
   codec, session, callId, imei, extendData, subCommand: 3} → máy đối phương đổ chuông
4. Duy trì UDP Ping (0x01 0x7e, cmd=2/5/32) + sẵn sàng truyền/nhận RTP/SRTP
```

```ts
const connParams = await session.startOutgoingCall(targetUid, { callType: CallType.Audio /* hoặc Video */ });
// connParams: { callId, rtpAddress, udpHandshakeVerified, ... }
// Điều khiển trong cuộc gọi:
await session.setMicMuted(true);            // tắt mic (tự gửi /api/voicecall/conf + gói UDP AudioCodec)
await session.setCameraEnabled(true);       // bật camera (tự phát lại SPS/PPS)
await session.upgradeAudioToVideoCall(true);// nâng cấp thoại → video (cmd 12056)
await session.setScreenShareEnabled(true);  // chia sẻ màn hình (cmd 12064)
await session.holdCall(true);               // tạm giữ (cmd 11307 / 11309)
await session.reconnectUdp();               // đổi mạng WiFi/4G không đứt cuộc gọi
await session.endCall("local_end");         // tự chọn cancelVoiceCall (chưa bắt máy) / endVoiceCall (đang gọi)
```

### 4.4. ★ CODEC — định dạng thật của engine (nghi phạm số 1 của app)

**Đây là phát hiện quan trọng nhất của bản tổng hợp này.**

`src/call-engine/ZRTPPacketCodec.ts:279` — chuỗi codec Opus chuẩn mà `ZaloCall` tạo trong `sendSignal 416`:

```ts
export const DEFAULT_ZALO_AUDIO_CODEC = JSON.stringify([
    { dynamicFptime: 0, frmPtime: 20, name: "opus/16000/1", payload: 112 },
]);
// → '[{"dynamicFptime":0,"frmPtime":20,"name":"opus/16000/1","payload":112}]'

export const DEFAULT_ZALO_VIDEO_CODEC = JSON.stringify([
    { dynamicFptime: 0, frmPtime: 20, name: "opus/16000/1", payload: 112 },
]);
// (codec video nằm trong extendData.video — xem 4.5)
```

Quy tắc dùng codec trong zca-js:

| Vị trí | Giá trị codec |
|---|---|
| `requestVoiceCall` (11300) — `src/apis/call/requestVoiceCall.ts:34` | `options.codec ?? "[]"` (mặc định chuỗi `"[]"`) |
| `sendRequestVoiceCall` (11301) — `src/apis/call/sendRequestVoiceCall.ts:46` | `options.codec ?? "[]"` (mặc định chuỗi `"[]"`) |
| `ZaloRtcSession.startOutgoingCall` | `this.codec = options.codec ?? DEFAULT_ZALO_AUDIO_CODEC` — engine **luôn** truyền chuỗi JSON list Opus vào **cả 11300 và 11301** |
| `ZaloRtcSession.applyServerInfo` | nếu `serverInfo.codec` (11300 trả về) khác `"[]"` thì `this.codec = serverInfo.codec` — **codec server trả về thắng**, dùng cho 11301 |
| `answerVoiceCall` (11303) | `options.codec ?? ""` (mặc định chuỗi rỗng) |
| UDP AudioCodec (`cmd=1`, byte[21]) | `codecType = 3` (Opus Unmute) / `9` (Mute) — `buildAudioCodecMutePacket` |

Media trên dây: **Opus 16kHz Mono, PT=112, SSRC 32-bit, khung 20 ms = 320 samples (hoặc 40 ms = 640 samples)**. Video: H.264 Constrained Baseline Profile Level 3.0 (`avc1.42001e`), 360×640 dọc hoặc 640×360 ngang, 15–24 fps, bitrate 200.000–450.000 bps, xuất `annexb` (bắt đầu `00 00 00 01`); `sendH264AnnexBFrame` tự trích SPS (NAL 7) + PPS (NAL 8) chèn trước mỗi IDR (NAL 5), phân mảnh khung > 1135 byte theo Zalo Annex-B FU-A (`0x1c`, `origNalType = 0`); gọi nhóm đính kèm extension RFC 5285 `0xBEDE` 24 byte (`0x32` AbsoluteSendTime, `0x51` TransportSequenceNumber, `0xc2` VideoGroupCall, `0xd6` CaptureNtpTime).

### 4.5. extendData chuẩn (`buildZrtcExtendData`, `ZRTPPacketCodec.ts:313`)

```ts
{
    callType: 0,            // 0 thoại / 1 video (KHÔNG phải enum typeRequest 1/3/5/6)
    fecTP: 0, gccAudio: 0, gccEarlyCall: 0, gccMode: 0, gccSVLR: 0,
    maxFT: 120, newZrtc: 1, packetMode: 2,   // packetMode mặc định 2 (gọi 1-1)
    platform: 2,            // mặc định 2 trong zca-js
    sP2P: 0,
    serverAddr: [{ rtcp, rtcpIPv6: `::FFFF:${rtcp}`, rtp, rtpIPv6: `::FFFF:${rtp}`, tpType: 0 }],
    spTcp: 0, srtcp: 0, srtpMode: 0,       // srtpMode = 1 + srtpKey nếu có SRTP session
    supportCallBusy: 0, supportHevcDecode: 0, tpType: 0,
    // + srtpKey (base64) nếu có
    video: { codec: [{ name: "h264", payload: 97 }] }, // LUÔN đính kèm (để nâng cấp thoại → video)
}
// ZaloRtcSession còn thêm ngoài buildZrtcExtendData:
{ rtcpDiff: 0, rtcp: [{ ip, port }], rtp: [{ ip, port }], status: 0 }
```

### 4.6. Gọi đến 1-1 (app hiện chưa có — xem đối chiếu mục 7)

```ts
api.listener.on("call_event", async (ev) => {
    if (ev.act === "request") {
        await session.ringIncomingCall(ev);                    // 11302 ringring, signal 407
        const params = await session.acceptIncomingCall(ev, { skipRingRing: true });
        // 11303 answer, signal 402 + mở kết nối UDP/SRTP 2 chiều
        // hoặc: await session.rejectIncomingCall(ev);        // 11306 endcall (báo máy bận)
    }
});
```

### 4.7. Gọi nhóm qua Zavi SFU

`startGroupCall(groupId, memberUids, { callType: CallType.GroupVideo | GroupAudio, groupName })` → 12433 → bắt tay phòng Zavi (Echo 248 → InitZaviPing 53 → ZaviRoomUpdated 50) → gửi `RequestForward` (subCmd=2 AudioCodecList, subCmd=11 VideoQualityBitrateConfig, subCmd=13 VideoQualityRequest) → duy trì `pingGroupCall` (12097) + `broadcastGroupCallState` (12098). Nhận lời mời: `call_event` act=`group_request` → `ringIncomingCall` (12439) → `acceptIncomingGroupCall` (12436 + nối Zavi SFU). Tham gia phòng đang mở: `joinActiveGroupCall(groupId)` (tự truy vấn `getGroupCallState` nếu chưa biết callId); mời thêm: `inviteMembersToGroupCall(uids)`.

Quy ước trạng thái gọi nhóm (khác trực giác, phải nhớ): **`audioState = 0` = Mic ĐANG BẬT, `1` = Mic TẮT; `videoState = 0` = Camera ĐANG BẬT, `1` = Camera TẮT/tạm dừng**. Zavi SFU đóng gói RTP Video đến (`0x0e`) với `SSRC = 1` (ID bộ trộn) và đặt VoIP UID 32-bit thật của người phát tại `CSRC[0]` — `ZaloRtcSession` tự giải mã `CSRC[0]` → `frame.partnerId` (UID 19 chữ số).

### 4.8. Chế độ worker chỉ signaling + Call Studio

- `signalingOnly: true` — worker không mở socket UDP; `startOutgoingCall` trả `params.mobileDirectHandoff` (`callId`, `primaryRtpEndpoint {host, port}`, `srtpMasterKeyBase64`, `preBuiltUdpPacketsBase64` — gói Echo/InitCall/Ping dựng sẵn) để Mobile App tự nối UDP. Hoặc giữ UDP trong lúc đổ chuông rồi bàn giao sau bắt máy: `session.handoffUdpToExternal()`.
- **Call Studio** (app web test trực quan, dùng WebCodecs + WebAudio, test với điện thoại thật): `npm run test:call-studio` → http://localhost:3388.

## 5. Gửi thoại (114) + STT (13394) — chi tiết

### 5.1. Gửi tin nhắn thoại — `sendVoice` (`src/apis/chat/sendVoice.ts`)

```ts
await api.chat.sendVoice({ voiceUrl, ttl }, threadId, ThreadType.User /* hoặc Group */);
```

- Endpoint: POST `/api/message/forward` (1-1) hoặc `/api/group/forward` (nhóm) — cùng endpoint với `sendCard`/`sendVideo`.
- Body (đã mã hóa AES): `{ toId | grid, ttl ?? 0, zsource: -1, msgType: 3, clientId: Date.now(), msgInfo: JSON.stringify({ voiceUrl, m4aUrl: <cùng voiceUrl>, fileSize }), imei }`.
- `fileSize` lấy trước bằng **HEAD request** tới `voiceUrl` (đọc header `content-length`); lấy không được thì ném `ZaloApiError("Unable to get voice content")`.
- Docs ghi định dạng: **«Voice / Audio MP3 / AAC»** — khớp lệnh đứng của user (MP3 cho voice note).
- **Điểm khác biệt lớn với app:** `sendVoice` của zca-js chỉ **forward một URL đã có sẵn** (file đã upload ở đâu đó, hoặc URL ngoài). Nó **không** upload chunked, **không** dùng kênh ctrl 99101, **không** đợi event `voice_aac_success`. Đường 114 của app (upload chunked 256.000 B + đợi `voice_aac_success`, AAC-LC 16 kHz mono 64 kbps ADTS) là đường của **PC bundle**, không có trong zca-js — nên zca-js **không chứng minh hay bác bỏ được** đường 114 của app; chỉ cho biết định dạng voice mà server chấp nhận (MP3/AAC, `msgType: 3`, `msgInfo.voiceUrl` + `m4aUrl`).

### 5.2. STT — `voiceToText` (`src/apis/media/voiceToText.ts`, command 13394)

```ts
const res = await api.media.voiceToText(voiceUrl); // POST {ai_features}/api/aifeatures/voice2text
// res: { req_id: string }
api.listener.on("voice2text_event", (ev) => { /* ev.data: { req_id, text } */ });
```

- Request: POST tới `{ai_features}/api/aifeatures/voice2text`, body AES `{ url: voiceUrl }` (`voiceUrl` chấp nhận `.aac` / `.mp3` / `.m4a`). Không có tham số bật/tắt nào trong request.
- Kết quả **bất đồng bộ**: đẩy về qua WebSocket `voice2text_event` (`cmd=601`, `act_type="voice2text"`), khớp bằng `req_id` — handler tại `src/realtime/handlers/control.handler.ts:159`.
- Gating `v2t.transcribe.enabled` là **cấu hình phía server**, không phải tham số của API này — khớp với những gì app đã biết (mặc định false).

## 6. Listeners / sự kiện (trang `guide/listeners`)

`api.listener` giữ WebSocket nhị phân realtime (giải mã AES-GCM 128-bit + giải nén Pako + bảo toàn số nguyên 64-bit `storeAsString`, Ping/Pong tự động, Watchdog 50 s, xoay vòng máy chủ dự phòng). **18 sự kiện** (`ListenerEvents`):

| Sự kiện | Lệnh WS | Dữ liệu |
|---|---|---|
| `connected` / `closed` (`disconnected`) / `error` | — | Trạng thái kết nối |
| `message` | 501 (1-1), 521 (nhóm) | Tin nhắn mới / tự gửi (văn bản, ảnh, video, voice, file, sticker, card…) |
| `oa_message` | 533 → 570 → 534 | Tin nhắn 2 chiều Zalo OA (`oa_chat`, `oa_list`, `info_chat`, `ecard`, `footerv2`) |
| `reaction` | 612 (subCmd 1/2), 523 | Biểu cảm thả vào tin nhắn |
| `undo` | 501/521 (`chat.undo`) | Thu hồi tin nhắn |
| `typing` | 602 (`typing`/`gtyping`) | Đang soạn tin |
| `delivered_messages` | 510/511 (subCmd 0) | Đã chuyển tới thiết bị người nhận |
| `seen_messages` | 502, 522, 510/511 | Đã đọc |
| `unread_cleared` | 504 (subCmd 1) | Xóa đếm chưa đọc khi đọc ở thiết bị khác |
| `friend_event` | 601 (act bạn bè) | Kết bạn, chấp nhận/từ chối, chặn, biệt danh, ghim |
| `group_event` | 601 (act nhóm) | Tạo nhóm, thêm/xóa thành viên, đổi tên/ảnh, bổ nhiệm phó nhóm… |
| **`call_event`** | **601 (`voicecall`), 604** | **Cuộc gọi 1-1 + nhóm: `request`, `ringring`, `answer`, `cancel`, `endcall`, `group_request`… — xem mục 4.6/4.7** |
| `sync_event` | 601 (`SyncEventType`) | Đồng bộ lịch sử từ điện thoại sang PC (ZDB 4.0) |
| **`voice2text_event`** | **601 (`voice2text`)** | **Kết quả STT: `{req_id, text}` — xem mục 5.2** |
| `oa_event` | 601 (`block`/`unblock`) | Chặn/bỏ chặn OA |
| `todo_event` | 602 (subCmd 1, `todo`) | Tạo/cập nhật/hoàn thành/nhắc/xóa To-Do |
| `poll_event` | 601 (`poll`) | Tạo bình chọn, bỏ phiếu, thêm phương án, khóa |
| `translate_event` | 601/630 (`translate_*`) | Kết quả dịch tự động / gợi ý / đổi cấu hình dịch |
| `emoji_status_event` | 612 (subCmd 3) | Cập nhật Emoji Status |
| `online_status_event` | 603 (subCmd 0) | Online/Offline của bạn bè |
| `control_sync_event` | 610, 611 (subCmd 0/1) | Đồng bộ hàng đợi điều khiển đa thiết bị |
| `zcloud_event` | 621 | Thông báo đẩy ZCloud/My Cloud |
| `cipher_key` | 1 (subCmd 1) | Khóa phiên giải mã AES-GCM khi bắt tay WS |

4 phương thức gửi khung WS chủ động (chuẩn Zalo PC 26.7.10): `sendPingActive()` (version=1, cmd=4, subCmd=1), `requestLastDeliverSeen()` (cmd=522, subCmd=1), `requestLastSeenSubChatTab()` (cmd=522, subCmd=3), `requestLastSeenReaction()` (cmd=523, subCmd=1).

## 7. Đối chiếu với app Python (`zalo-pc-app/`, nhánh `muse/zalo-addon-pivot` @ `0824c0d`)

Đối chiếu dựa trên code app tại `~/workspace/calling-push/zalo-pc-app/` (worktree nhánh `muse/zalo-pcap-files` @ `92e416e`, cùng code app với `0824c0d` + thêm PCAP) và `zalo-pcap/analysis/UNFIXED_ERRORS.md` (5 lỗi chưa sửa).

### 7.1. Bảng đối chiếu nhanh

| Hạng mục | App Python hiện tại | zca-js 2.3.13 | Kết luận |
|---|---|---|---|
| **11300 `codec`** | `"[]"` (fallback khi engine không cấp list) — `protocol.py:278` `vc_requestcall` | Mặc định `"[]"` ở tầng factory; nhưng `ZaloRtcSession` luôn truyền chuỗi JSON list Opus vào 11300 | **Khớp ở tầng factory.** Khác ở tầng engine: zca-js gửi list thật |
| **11301 `codec`** | `"opus"` (chuỗi trần) — suy luận từ `zrtc_config.g711` (1→`pcmu`, 2→`pcma`, else `"opus"`), `media_endpoints.py:851` | `'[{"dynamicFptime":0,"frmPtime":20,"name":"opus/16000/1","payload":112}]'` (chuỗi JSON list), hoặc codec server trả về từ 11300 nếu khác `"[]"` | **★ LỆCH — nghi phạm số 1 đã có bằng chứng cụ thể (mục 7.2)** |
| 11301 `extendData` | 24 keys `_MINIMAL_EXTEND_DATA` (xem 7.3) | `buildZrtcExtendData` + `rtcpDiff/rtcp/rtp/status` (xem 7.3) | Lệch vài giá trị (newZrtc, maxFT, video.codec, platform) — xem 7.3 |
| 11300 `typeRequest` | 1 (thoại) / 3 (video) — đã sửa từ 0 | `CallType.Audio = 1`, `Video = 3` | Khớp |
| `callId` | Counter trong process từ 1, uint32 (fix `0824c0d`) | `Math.floor(Math.random() * 2_000_000_000)` | Khác cách sinh, cùng miền uint32 — callId đã loại trừ bằng test live 09/11 |
| Gọi đến (11302/11303/11304) | Có hàm `vc_ringring`/`vc_answer`/`vc_answerack` nhưng **chưa nối vào xử lý `call_event`** — 11303 chưa implement, không log, cuộc gọi nhỡ hiện `sendBubbleMessage` | Đầy đủ: `ringRingVoiceCall` → `answerVoiceCall` → `answerAckVoiceCall`, gắn vào listener `call_event` act=`request` | **zca-js có, app chưa có** — port flow (mục 7.4) |
| SRTP / ZRTP | `srtp: not-wired` — engine dùng ZRTP (Init 185B `_doInitZRTP`), app chưa cài | `ZaloSrtpSession` (AES-CM-128-HMAC-SHA1-80) + `ZRTPPacketCodec` + `ZaloRtcSession` đầy đủ | **zca-js có, app chưa có** — tham chiếu để port (mục 7.5) |
| Gửi thoại 114 | Kênh ctrl 99101 + upload chunked 256.000 B + đợi `voice_aac_success` (AAC-LC 16 kHz mono 64 kbps ADTS) | Chỉ forward `voiceUrl` có sẵn qua `/api/message/forward` (`msgType: 3`) | **Hai đường khác nhau** — zca-js không chứng minh được đường 114 của app (mục 5.1) |
| STT 13394 | `/api/aifeatures/voice2text`, kết quả qua event `convert_finish` kênh 99100, gating `v2t.transcribe.enabled` | Cùng endpoint `/api/aifeatures/voice2text`, kết quả qua `voice2text_event` (cmd 601) khớp `req_id` | **Khớp endpoint + mô hình async** — chỉ khác tên/kênh event |
| Nhắn tin / file | Đã chứng minh live hai chiều (TXT, APK 20 MB, ảnh, Excel) | `sendMessage` + `uploadAttachment` (chunked) + `forwardMessage` | Tương đương — không cần đổi |
| Đăng nhập | QR kiểu PC (`qr.id.zalo.me` + voicecall) — phiên PC gọi được | `loginQR` là **QR web** (`id.zalo.me`, continue `chat.zalo.me` / `zalo.me/pc`) | **Khác loại phiên** — không thay QR-PC của app bằng loginQR của zca-js (mục 7.6) |
| Kiểm chứng phiên | Không có — `/api/status` chỉ kiểm `session.json` còn `zpw_sek` (lỗi 5) | `keepAlive` + `checkSession` trong flow QR | Có thể tham khảo `checkSession` |
| UID 64-bit | Cẩn thận string/int trong code app | `preParseJsonIds` (giống `app.asar` Zalo PC) | Cùng nguyên tắc — giữ |

### 7.2. ★ Codec 11301 — bằng chứng và đề xuất sửa

- **App gửi gì:** `codec: "opus"` — chuỗi trần, suy luận từ `zrtc_config.g711` (`media_endpoints.py:146-147, 851-856`: `g711` 1→`pcmu`, 2→`pcma`, else `"opus"`). Chính code app cũng ghi đây là **SUY LUẬN, chưa xác minh** (`udp_transport.py:394`: «`codec` defaults to `"opus"` but that is UNCONFIRMED»).
- **zca-js gửi gì:** `'[{"dynamicFptime":0,"frmPtime":20,"name":"opus/16000/1","payload":112}]'` — chuỗi **JSON list** gồm 1 object (`dynamicFptime: 0`, `frmPtime: 20`, `name: "opus/16000/1"`, `payload: 112`). Đây là chuỗi «chuẩn được `ZaloCall` tạo trong `sendSignal 416`» theo comment trong code (`ZRTPPacketCodec.ts:277-279`).
- **Cơ chế chọn codec của zca-js:** 11300 gửi codec list → server có thể trả về `codec` khác trong response 11300 → `applyServerInfo` dùng codec đó cho 11301. Nếu server trả `"[]"` (hoặc không có) thì giữ nguyên DEFAULT list.
- **Đề xuất sửa (theo thứ tự, mỗi bước test riêng để biết cái nào có tác dụng):**
  1. **Đổi `codec` trong 11301 thành đúng chuỗi JSON list trên** (test đỏ-trước-xanh-sau ở `test_call_11301`, rồi test live xem Đại ca có đổ chuông không). Đây là bước ưu tiên cao nhất — lần đầu tiên có định dạng chuỗi thật của engine, không còn phải đoán.
  2. Đồng thời gửi cùng chuỗi list vào **11300** (thay cho `"[]"` hiện tại) rồi đọc `codec` trong response 11300: nếu server trả về codec khác `"[]"` thì dùng đúng codec đó cho 11301 (theo cơ chế `applyServerInfo` của zca-js).
  3. Chỉ sau khi 1–2 xong mà vẫn không đổ chuông mới đụng tới extendData (mục 7.3) — không đổi nhiều thứ cùng lúc.

### 7.3. extendData — so sánh từng khóa

App (`_MINIMAL_EXTEND_DATA`, `media_endpoints.py:961`, 24 keys) vs zca-js (`buildZrtcExtendData` + phần thêm của `RtcSession`):

| Khóa | App | zca-js | Ghi chú |
|---|---|---|---|
| `callType` | 0 (thoại) | 0 (thoại) / 1 (video) | Khớp. Lưu ý: callType 0/1 khác enum typeRequest 1/3/5/6 |
| `newZrtc` | 0 | **1** | Lệch. zca-js luôn 1 |
| `platform` | **3** (parser 0x71f670 init `[+0x04]=3` — bằng chứng disasm duy nhất) | **2** (mặc định) | **Lệch — nhưng theo luật đứng, xung đột thì bundle exe là chuẩn cuối → GIỮ 3.** Giá trị 2 của zca-js có thể là của client khác (web/mobile). Ghi lại, không đổi theo zca-js |
| `maxFT` | 60 (parse-fail default) | **120** | Lệch |
| `video` | `{codec: ""}` | `{codec: [{name: "h264", payload: 97}]}` | zca-js luôn đính kèm list codec video (để nâng cấp thoại → video) |
| `packetMode` | 2 | 2 | Khớp (gọi 1-1; gọi nhóm là 1) |
| `serverAddr` | list từ 11300 (`server_addrs`) | `[{rtcp, rtcpIPv6: "::FFFF:<ip>", rtp, rtpIPv6, tpType: 0}]` | Cùng ý; zca-js luôn kèm dạng IPv6 `::FFFF:` |
| `srtpMode` | 0 (hoặc giá trị 11300) | 0, hoặc 1 + `srtpKey` khi có SRTP session | Khớp logic |
| `fecTP`, `gccAudio`, `gccEarlyCall`, `gccMode`, `gccSVLR`, `sP2P`, `spTcp`, `srtcp`, `supportCallBusy`, `supportHevcDecode`, `tpType` | 0 | 0 | Khớp |
| `p2p`, `extraInfo {type,id}`, `serverResult`, `numServers`, `select2side` | có (app thêm) | **không có** | App có thêm — có thể là trường của PC bundle, giữ nguyên |
| `rtcpDiff`, `rtcp [{ip,port}]`, `rtp [{ip,port}]`, `status` | không có | có (RtcSession thêm ngoài `buildZrtcExtendData`) | zca-js có thêm — ứng viên thử sau codec |

**Nguyên tắc khi sửa:** mỗi thay đổi test riêng (codec trước, rồi mới tới `newZrtc`/`maxFT`/`video.codec`), `platform` giữ 3 theo bundle. Không đổi cùng lúc nhiều khóa.

### 7.4. Gọi đến — những gì app thiếu (port từ zca-js)

App có sẵn hàm `vc_ringring` (11302), `vc_answer` (11303), `vc_answerack` (11304) trong `protocol.py:368-390` nhưng **chưa nối vào luồng xử lý**: không có listener cho `call_event` act=`request`, không log cuộc gọi đến, cuộc gọi nhỡ hiện chữ `sendBubbleMessage`. Flow cần port (từ `ZaloRtcSession.ringIncomingCall` / `acceptIncomingCall` + `control.handler.ts:107-122`):

1. Lắng nghe WebSocket `call_event` (`cmd=601` voicecall / `604`), `act == "request"` → lấy `data.callId`, `data.callerId`/`uidN`, `data.session`/`sessId`, `data.codec`.
2. Gửi 11302 `ringring` (`{callerId, callId, status: 0, imei}`) — báo máy đối phương biết thiết bị đang đổ chuông.
3. Khi người dùng bắt máy: gửi 11303 `answer` (`{callerId, callId, status: 0, codec: "" (mặc định), rtcpAddress, rtpAddress, session_id, extendData, subCommand: 3}`) + mở kết nối UDP/SRTP.
4. Sau bắt tay xong: gửi 11304 `answerack` (`{calleeId, callId, status: 0, imei}`).
5. Từ chối: 11306 `endcall` (`{uidTo, callId, status: 3, imei}` — app đã có `vc_endcall`).

### 7.5. SRTP / ZRTP — tham chiếu để port

- App: `srtp: not-wired`. Engine dùng ZRTP (Init 185B `_doInitZRTP`), app chưa cài → chưa có tiếng trong cuộc gọi.
- zca-js: `ZaloSrtpSession.ts` (570 dòng, suite `AES_CM_128_HMAC_SHA1_80` — RFC 3711), `ZRTPPacketCodec.ts` (1094 dòng: build/parse gói ZRTP, `ZRTPPacket` header, `AudioCodec` cmd=1, `InitCall` cmd=11, Echo cmd=248, Ping cmd=2/5/32), `ZaloRtcSession.ts` (5948 dòng: vòng đời UDP + SRTP + keepalive).
- Cách dùng: đọc cấu trúc gói + thứ tự bắt tay trong `ZRTPPacketCodec.ts` / `ZaloRtcSession.ts` rồi port sang Python (không copy nguyên vì khác ngôn ngữ). Khóa SRTP lấy từ response 11300 (`zrtpKey` / `srtpKey`, dài ≥ 40 ký tự mới lập session, `srtpMode != 0`).

### 7.6. Đăng nhập — khác loại phiên, không thay thế được

- **zca-js `loginQR` là QR web:** `loadLoginPage` mở `https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F` → parse version JS `stc-zlogin` → `getLoginInfo` (POST `id.zalo.me/account/logininfo`, `continue=https://zalo.me/pc`) → `verifyClient` → `generate` QR → `waitingScan` → `waitingConfirm` → `checkSession` → `getUserInfo`. Phiên thu được là **phiên web** (chat.zalo.me) — nhắn tin được, **không gọi được** (Zalo Web không gọi).
- **App dùng QR kiểu PC** (`qr.id.zalo.me` + voicecall) — phiên PC gọi được. Đây là loại phiên khác, **không thể thay QR-PC của app bằng `loginQR` của zca-js**. Phần đăng nhập của zca-js chỉ tham khảo được: cấu trúc `exportSession` (`cookie`, `imei`, `userAgent`, `language`, `uid`), `keepAlive`, và `checkSession` (app đang thiếu kiểm chứng phiên — lỗi 5 trong UNFIXED_ERRORS).

## 8. Đề xuất bước tiếp theo cho app (theo thứ tự)

1. **Sửa codec 11301** thành chuỗi JSON list Opus chuẩn (mục 7.2, bước 1–2) — test đỏ-trước-xanh-sau, rồi test live gọi Đại ca xem có đổ chuông không. Ưu tiên cao nhất.
2. **Nối gọi đến** (mục 7.4): listener `call_event` act=`request` → 11302 → 11303 → 11304; log cuộc gọi đến; sửa bong bóng cuộc gọi nhỡ (hiện `sendBubbleMessage`).
3. **Soát extendData** sau khi codec xong: thử `newZrtc` 0→1, `maxFT` 60→120, `video.codec` → `[{name:"h264",payload:97}]`, thêm `rtcpDiff/rtcp/rtp/status` — mỗi cái test riêng; **`platform` giữ 3** theo bundle.
4. **Port SRTP/ZRTP** từ `ZaloSrtpSession` + `ZRTPPacketCodec` để có tiếng trong cuộc gọi (sau khi đổ chuông đã xong).
5. **Test 114 + STT 13394 live** theo flow đã biết: 114 theo đường PC bundle (ctrl 99101, chunk 256.000 B, `voice_aac_success`); STT theo endpoint chung + lắng nghe event khớp `req_id`.
6. **Kiểm chứng phiên**: tham khảo `checkSession`/`keepAlive` của zca-js để app tự phát hiện phiên bị đá (lỗi 600) thay vì hiện «Đã đăng nhập» với dữ liệu cũ.

## 9. Link tham chiếu

- Docs: https://softtyos.github.io/zca-js-docs/
- Docs — Getting Started: https://softtyos.github.io/zca-js-docs/guide/getting-started.html
- Docs — Architecture: https://softtyos.github.io/zca-js-docs/guide/architecture.html
- Docs — Call Engine: https://softtyos.github.io/zca-js-docs/guide/call-engine.html
- Docs — Cookbook: https://softtyos.github.io/zca-js-docs/guide/cookbook.html
- Docs — Listeners: https://softtyos.github.io/zca-js-docs/guide/listeners.html
- Docs — API Call (30 APIs): https://softtyos.github.io/zca-js-docs/api/call.html
- Docs — API Chat (52 APIs): https://softtyos.github.io/zca-js-docs/api/chat.html
- Docs — API Group (46 APIs): https://softtyos.github.io/zca-js-docs/api/group.html
- Docs — API Media (8 APIs): https://softtyos.github.io/zca-js-docs/api/media.html
- Docs — API Models: https://softtyos.github.io/zca-js-docs/api/models.html
- Code GitHub: https://github.com/softtyos/zca-js (HEAD `e1c09a98a1c9cee35377a8d392ac9b5688a7d1de`, v2.3.13) — clone tại `~/workspace/zca-js-softtyos`
- Code NPM: `@softtynet/zca-js@2.3.13` — https://www.npmjs.com/package/@softtynet/zca-js
- Repo cũ (không dùng cho gọi thoại): https://github.com/RFS-ADRENO/zca-js (v2.2.0, không có call engine)
- App đối chiếu: repo TriTue2011/Calling, `zalo-pc-app/`, nhánh `muse/zalo-addon-pivot` @ `0824c0d`; PCAP + lỗi chưa sửa: nhánh `muse/zalo-pcap-files` (`zalo-pcap/analysis/UNFIXED_ERRORS.md`)

---
*Báo cáo này chỉ đọc docs + code công khai, không chứa bí mật nào (không token, cookie, mật khẩu, zpw_sek).*
