# Audit toàn bộ code app Zalo PC — 96 service + service mới + lỗi ngoài 96

- **Ngày audit:** 2026-11-09. **Chỉ đọc, không sửa code.** User lệnh: «kiểm tra kỹ tất cả code, không chỉ mỗi gọi không, xem cả 96 service cũ có cần bổ sung sửa gì không, có thêm được service nào nữa không».
- **App đối chiếu:** repo TriTue2011/Calling, `zalo-pc-app/`, nhánh `muse/zalo-addon-pivot` @ `0824c0d` (phần B đọc tại HEAD `2efce18` = 0824c0d + 1 commit codec của agent gọi đang chạy song song). ~16.000 dòng Python + 41 file test.
- **Phương pháp:** 3 agent chạy song song — (A) bảng 96 service, (B) audit code ngoài 96 + ngoài gọi, (C) service mới. Mỗi phần có file riêng kèm dưới; báo cáo này là bản tổng hợp + xếp ưu tiên.
- **Bằng chứng:** toàn bộ là đọc code + đếm bằng script (import thật + dump CATALOG, YAML parse services.yaml); test là mock (MockZalo). Chỉ #34/#40 có bằng chứng live ghi trong code; các op còn lại chưa có bằng chứng gọi thật thành công lên Zalo trong đợt này. 3 phát hiện mức Cao của phần B đã kiểm chứng live bằng server tạm loopback + DATA_DIR tạm (không đụng data thật).

## 0. Tóm tắt 3 con số

| Mảng | Kết quả |
|---|---|
| **96 service addon** | **73 gọi được** (52 đầy đủ + 21 body_unverified), **0 chưa hỗ trợ 409**, 10 chỉ thuộc zalobot, 11 thuộc khung chat, 2 view (#34/#40), 0 thiếu khỏi catalog. Con số cũ «25 chưa hỗ trợ» đã chứng minh là **sai** — cả 25 đều đã có endpoint PC trong OPS. |
| **Lỗi ngoài 96 service** | **43 phát hiện**: 5 Cao (trong đó 2 là lỗi bảo mật cổng ngoài), 18 trung bình, 20 thấp. |
| **Service mới (ngoài 96)** | **56 ứng viên** từ zca-js + 135 route zalobot + bundle exe PC. |

## 1. Service 96 cần sửa/bổ sung — xếp ưu tiên (chi tiết đầy đủ ở Phần A §3–§7)

**P0 — không có đường chạy ở đâu cả:**
1. **#71 `send_card`** — status `chat` nhưng chat.py cũng chưa implement; đường card user thường chưa lần riêng (chỉ có biến thể OA `forwardContactOA` 11774/11827). Service duy nhất trong nhóm chat mà cả hai tầng đều chưa có code. Cần: lần đường card user trong bundle → implement ở chat.py.
2. **#75 `send_video`** — status `chat`, chat.py chưa implement; chỉ lần được bước upload (12058/12061 + thumb), bước send sau upload chưa trích được. Cần: lần bước send trong bundle (zca-js làm `uploadAttachment` rồi `sendVideo({videoUrl, thumbnailUrl, duration})` — đối chiếu, không copy mù).

**P1 — chạy được một nửa / bị 409 theo trường hợp:**
3. **#67 `add_reaction`** — chỉ icon `like` có map đã xác minh; icon khác phải truyền tay `r_icon`/`r_type`; domain REACTION phụ thuộc services map lúc login (thiếu → 409). Cần: lần bảng icon `reactionMsgInfo` trong config server/bundle.
4. **#41 `get_group_chat_history`** — nhánh nhóm chạy (GET 11240), nhánh 1-1 trả 409 vì bundle không có endpoint HTTPS cho lịch sử 1-1 (chỉ DB local + `pull_mobile_msg` 12000 / `get_backupmsginfo` 12096 / `get_crossdb` 12412). Cần: đường sync/control hoặc đọc DB local cho 1-1.
5. **#34/#40 `get_all_friends` / `get_all_groups`** — dữ liệu đã live đúng trên UI danh bạ nhưng `POST /api/svc/*` trả 409 status `view`. Cần quyết định sản phẩm: thêm op chỉ-đọc vào `OPS` trỏ về contacts, hoặc giữ 409 + UI dùng tab danh bạ.

**P2 — 21 service body_unverified (gọi được, body chưa lan hết; UI đã cảnh báo):**
Thứ tự lan tiếp gợi ý: (1) #67 bảng icon reaction; (2) #69 transform forward theo loại tin (lần `transformForwardMessage`); (3) #7 body `getprofiles/v2` + #50 fields `profile/update` (lần caller UI); (4) #86/#89 `media`/`type` quick message; (5) #51 key thật `setting/update`; còn lại là trường lẻ (`src`, `suggestionId`, `avatarSize`, `conv_type`, `convs*Data`, `conver`). Danh sách đầy đủ 21 service + từng trường chưa biết ở Phần A §4.

**P3 — 409 có điều kiện (không phải thiếu endpoint):**
- #86–#89 quick message: domain QUICK_MESSAGE thiếu trong services map lúc login → 409 (chỉ #87/#88 body đã đủ, chỉ kẹt domain). Hướng: log host thực tế ở lần gọi đầu rồi pin lại, không hard-code.
- #67 (đã nêu ở P1): domain REACTION tương tự.

**Không cần làm:** 10 service zalobot (#4, #5, #17–#23, #96) là khác biệt kiến trúc theo thiết kế (đa tài khoản / webhook / proxy thuộc máy chủ zalobot; #96 QR web đã có tương đương native là QR PC). 5 op ngoài 96 trong CATALOG (`quote_message`, `mark_seen`, `fetch_important`, `get_group_link`, `update_label`) đã có sẵn, không tính vào 96.

## 2. Service mới đáng thêm nhất (56 ứng viên — bảng đầy đủ ở Phần C)

**Làm ngay, dễ, giá trị cao:**
1. **F1 Bỏ phiếu poll** (`board/votePoll`) — Cao/Dễ. 96 có tạo/xem/khoá poll mà không bỏ phiếu được; 1 endpoint, không phụ thuộc gì — quick win rõ nhất.
2. **I1 Kiểm chứng phiên đang sống** (`auth/keepAlive`) — Cao/Dễ. Sửa lỗi 5 đã biết (phiên bị đá vẫn hiện «Đã đăng nhập»); gọi được ngay, nên làm sớm; hết phiên thì xoá session + hiện lại QR.
3. **D1 Từ chối lời mời kết bạn** (`friend/rejectFriendRequest`) — Trung bình/Dễ. 96 chỉ có chấp nhận mà không có từ chối.
4. **C7 Thu hồi nhiều tin nhắn** (`chat/undoMultiMessage`) — Trung bình/Dễ. 96 chỉ có thu hồi 1 tin.
5. **G1 Kho lưu trữ hội thoại** (mediastore 11841–11843) — Cao/Trung bình. Xem lại ảnh/file/link của 1 hội thoại mà không cần cuộn lịch sử.

**Làm sau codec gọi đi:** A1 nhận cuộc gọi đến 1-1 (Cao/Khó — lỗ hổng lớn nhất: app có sẵn `vc_ringring/vc_answer/vc_answerack` nhưng chưa nối listener; cuộc gọi nhỡ hiện sai chữ `sendBubbleMessage`), B1 STT 13394 (Cao/Trung bình — gating server `v2t.transcribe.enabled`, cần test live).

**Làm sau SRTP:** A2 gọi video 1-1, A3 gọi nhóm đầy đủ (join/answer/add-user/state/notify/ping/broadcast — app mới chỉ có 12433/12434/12438), A7 mic/cam.

**Để sau cùng / khi có nhu cầu rõ:** C4/C5 sync mobile + backup ZDB (khó, cần hiểu ZDB 4.0), G3 ZCloud (khó, mã hoá riêng), J4 họp video ZaviMeet, E7 nâng nhóm lên cộng đồng (không đảo ngược được), J3 OA.

**Đã loại (ghi rõ lý do ở Phần C):** route chỉ thuộc máy chủ zalobot (đa tài khoản, webhook admin, proxy), business/OA nặng, pipe `call-v2` Windows-only; bundle exe PC không cho thêm service mới ngoài lệnh zca-js đã liệt kê — giá trị của nó là xác nhận platform/codec/extendData.

## 3. Lỗi ngoài 96 service — 5 lỗi Cao (chi tiết đầy đủ ở Phần B)

1. 🔴 **Path traversal qua `/fonts/` (public, không cần đăng nhập)** — `server.py:2066-2068` + `3290-3293`. Đã chứng minh live: `GET /fonts/../../../../tmp/...` trả nội dung file. Trong container 4 lần `../` là tới `/data/session.json` (lộ `zpw_sek`), `app_auth.json`, `webhooks.json`, `messages.db`. Sửa: allowlist `fonts/*.woff2` hoặc kiểm `realpath` trong `STATIC_DIR`.
2. 🔴 **`POST /api/thread/*` bypass đăng nhập app** — `server.py:2575-2576` (rẽ nhánh trước cổng app-login ở 2609-2612); chỉ kiểm phiên Zalo. Ai tới được cổng HTTP là gửi tin/file/ghi âm thay tài khoản Zalo mà không cần mật khẩu app. Sửa: kiểm `_require_app_login()` ngay đầu `_handle_thread_post`.
3. 🔴 **Không chống brute-force ở `/api/app/login`** — `server.py:2584-2599` + `app_auth.py:179-201` (không đếm lần sai, không khóa, không log). Một tài khoản dùng chung. Sửa: đếm lần sai theo IP, khóa tạm/delay tăng dần sau 5 lần sai, log lần sai.
4. 🔴 **`session.json` hỏng → server không khởi động được** — `session.py:50-53` + `server.py:709`. File JSON hỏng → `JSONDecodeError`, tiến trình chết trước cả `main()`. Sửa: `load()` trả `None` khi JSON hỏng (đổi tên file hỏng thành `session.json.corrupt`), khởi động với phiên trống + log rõ.
5. 🔴 **Không kiểm chứng phiên Zalo; lỗi 600 không được xử lý** — `server.py:834-867` (`public_status` chỉ kiểm `zpw_sek` còn trong file); grep toàn repo chỉ thấy `600` trong chuỗi gợi ý ở `chat.py:868-879`. Phiên bị đá → app vẫn báo `login: true`, không tự hiện lại QR. Sửa: validate phiên nhẹ lúc khởi động + định kỳ; gặp 600/401/403 kéo dài thì xoá session + hiện lại QR. (Service mới I1 keep-alive là cách sửa gọn nhất.)

**Thứ tự sửa đề xuất (Phần B):** H1 → H2 → H4 → H5 → H3. H1+H2 là lỗi cổng ngoài, sửa bằng vài dòng nhưng ảnh hưởng toàn bộ bảo mật app.

**Trung bình nổi bật (18):** friends không phân trang (`count=20000` cứng, `protocol.py:411-417`); nhóm đông thiếu `topMember` không có cờ báo (`contacts.py:170-196`); `ChatStore` RAM vô hạn (`chat.py:762-786`); webhook mất sự kiện im lặng, không retry/hàng đợi (`webhooks.py:390-430`); webhook message thiếu `kind`/`file_url` (`webhooks.py:262-295`); 2 kênh dùng con trỏ riêng lệch bundle chưa live-check (`ctrl_poll.py:30-35`); mã kick-out chưa biết nên retry mù (`sync_poll.py`); `session.json` hỏng (đã nêu); gửi file/voice giữ request HTTP tới 120s chờ event ctrl (`chat.py:191-206`).

**Đã kiểm chứng ĐÚNG (không phải lỗi):** contacts v4 + getmg-v2 (không còn v3), `avatar_size=160`, đếm thành viên nhóm bằng `totalMember`, cache TTL 120s + backoff 429 + stale-while-revalidate, lịch sử 1-1 đã có SQLite bền qua restart, webhook cả 4 họ đã nối nguồn thật qua 99100/99101, voice AAC 16 kHz mono 64 kbps khớp Node.js. 20 phát hiện thấp (docstring v3 cũ, QR cũ còn hiện sau lỗi, `ttl` âm, đường MP3 chết còn trong code, entrypoint chỉ chown không đệ quy, probe chưa commit, `run_tests.py` không timeout...) — xem Phần B §1–§12.

## 4. Nguồn tham chiếu

- 96 service chuẩn: `~/workspace/zalo-addon-doc/bao-cao-addon-96-services.md` (bảng 96, repo TriTue2011/zalo_bot HEAD 3ff124c); kiểm chứng: `~/workspace/zalo_bot/custom_components/zalo_bot/services.yaml` (96 key, YAML parse) + `__init__.py` (96 async_register).
- Đường PC: `~/workspace/zalo-addon-native-96/SERVICE-MAP.md` (audit bundle Zalo PC 26.11.10, 416 mã lệnh).
- zca-js: repo `~/workspace/zca-js-softtyos` (softtyos v2.3.13, `@softtynet/zca-js`) + báo cáo `outbox/zca-js-tong-hop.md` (cùng nhánh này).
- Máy chủ zalobot: `/tmp/zalobot-ref/zalo-pc-app/zalobot-embedded/routes/api.js` (135 route) + `api/zalo/zalo.js` (2922 dòng).
- Bundle exe PC: `~/workspace/zalo-pc-reverse/` (disassembly + so-sanh-416-11300-11301.md).
- Báo cáo cũ đối chiếu: `~/workspace/calling-push/zalo-pc-app/bao-cao-429.md`, `bao-cao-webhook.md`, `BAO-CAO-CHAT.md`, `bao-cao.md`, `bao-cao-doi-chieu-addon.md`.

---

---

# Phần A — Bảng trạng thái 96 service addon trong app Zalo PC


- **Ngày audit:** 2026-11-09 (chỉ đọc, không sửa code).
- **Nguồn chuẩn 96 service:** `~/workspace/zalo-addon-doc/bao-cao-addon-96-services.md` mục 2 (bảng 96 dòng, thứ tự #1–#96 giữ nguyên); kiểm chứng độc lập: `~/workspace/zalo_bot/custom_components/zalo_bot/services.yaml` (96 key, đếm bằng YAML parse — đã chạy lại trong đợt này, đúng 96, thứ tự khớp) và `__init__.py` cùng thư mục (96 lần `async_register` theo báo cáo chuẩn).
- **App đối chiếu:** `~/workspace/calling-push/zalo-pc-app`, nhánh `muse/zalo-addon-pivot` @ `0824c0d`. File chính `zalo_pc_app/services.py` (2154 dòng, `CATALOG = build_catalog()` dòng 1869, `dispatch()` dòng 2070, `handle_svc()` dòng 2130). Route server: `GET /api/svc/catalog` (`server.py:2089`), `POST /api/svc/<action>` (`server.py:2629`, qua `handle_svc`, yêu cầu phiên Zalo `_require_login`, chưa đăng nhập → 401).
- **Tham chiếu đường PC:** `~/workspace/zalo-addon-native-96/SERVICE-MAP.md` (audit bundle Zalo PC 26.11.10, 416 mã lệnh).
- **Kiểm chứng bằng code, không chỉ đọc:** đã import `services.py` và dump `CATALOG` bằng script (không sửa file), đếm lại toàn bộ; đã chạy `pytest tests/test_services.py` → **13 passed** (mock, không login thật).
- **Ghi chú về file đang sửa dở:** `git status` lúc audit thấy agent khác đang sửa trên cùng nhánh: `M tests/mock_server.py, tests/run_tests.py, tests/test_call_diag_11301.py, tests/test_media_provider.py, zalo_pc_app/media_endpoints.py, zalo_pc_app/protocol.py, zalo_pc_app/server.py` và file mới `probe_reqqr.py`, `tests/test_codec_zca_js.py`. Riêng `zalo_pc_app/services.py` và `tests/test_services.py` **sạch, không có thay đổi chưa commit** — bảng này đối chiếu đúng commit `0824c0d` + các file services. Riêng `server.py` có thay đổi chưa commit (7 dòng: +6/−1, theo `git diff --stat`); 2 route `/api/svc/*` vẫn ở đúng vị trí đã dẫn ở trên, nội dung móc `handle_svc` không đổi.

## 1. Đếm tổng (96 service)

| Nhóm | Ý nghĩa | Số |
|---|---|---|
| (a) CÓ ĐẦY ĐỦ | Trong `OPS`, `body_unverified=False` — body đã lan hết từ bundle | **52** |
| (b) CÓ NHƯNG body_unverified | Trong `OPS`, `body_unverified=True` — gọi được qua dispatch nhưng body chưa lan hết, UI cảnh báo | **21** |
| (c) CHƯA HỖ TRỢ 409 (chưa có đường PC) | Không có trong `OPS` lẫn `_NOT_SUPPORTED` với lý do "không có đường PC" | **0** |
| (d) CHỈ THUỘC ZALOBOT | Status `zalobot` — 409, phiên web của máy chủ zalobot | **10** |
| (e) THUỘC KHUNG CHAT | Status `chat` — 409 ở services.py, chat.py làm | **11** |
| (f) KHÔNG CÓ TRONG CATALOG | Thiếu hẳn khỏi `CATALOG` | **0** |
| (x) VIEW — ngoài 6 nhóm trên | Status `view` — dữ liệu đã xem được ở UI danh bạ (contacts.py), không phải op dispatch được; POST `/api/svc/<tên>` → 409 status `view` | **2** |
| **Tổng** | | **96** |

Ghi chú: `CATALOG` còn có thêm **5 op ngoài 96** (đều `supported`, `addon_no=None`): `quote_message`, `mark_seen`, `fetch_important`, `get_group_link`, `update_label` — không tính vào 96. Tổng entry catalog = 101, tổng `OPS` = 78 (73 trong 96 + 5 ngoài 96). `CATALOG["counts"]` do code tự tính: `supported 78, chat 11, zalobot 10, view 2, total_96 96`.

## 2. Đối chiếu với con số cũ trong bộ nhớ (50 / 25 / 10 / 11)

Con số cũ: **50/96 thao tác được, 25 chưa hỗ trợ 409, 10 zalobot, 11 chat** (tổng 96).

| Hạng mục cũ | Cũ | Nay | Khác ở đâu |
|---|---|---|---|
| Thao tác được | 50 | **73 gọi được qua dispatch** (52 đầy đủ + 21 body_unverified) | **+23**. Toàn bộ +23 đến từ nhóm "25 chưa hỗ trợ" cũ (xem dòng dưới). |
| Chưa hỗ trợ 409 | 25 | **0** (ở cấp service) | **−25, khớp hoàn toàn với kết luận của SERVICE-MAP.md §2**: cả 25 service đó (kết bạn/chặn/biệt danh ×10: #8, 24, 25, 26, 35, 36, 37, 38, 39, 91; ghim/ẩn/lưu trữ ×7: #53, 58, 61, 62, 63, 64, 66; reaction ×1: #67; poll ×3: #79, 80, 81; tin nhắn nhanh ×4: #86, 87, 88, 89) đều đã có trong `OPS` với endpoint PC trích từ bundle. Trong 25 này, 21 đã đầy đủ, 4 còn body_unverified (#67, #79, #86, #89). Claim cũ "25 service không có đường PC" đã được chứng minh là **sai** — test `test_catalog_covers_all_96` (tests/test_services.py:125) pin đúng điều này và `test_dispatch_refusals_and_validation` (dòng 874) spot-check 5/25 đều dispatch được, không 409. |
| Zalobot | 10 | **10** (#4, 5, 17, 18, 19, 20, 21, 22, 23, 96) | Khớp, không đổi. |
| Chat | 11 | **11** (#1, 2, 3, 13, 14, 15, 16, 33, 71, 72, 75) | Khớp, không đổi. |
| (không có trong con số cũ) | — | **2 view** (#34 get_all_friends, #40 get_all_groups) | Con số cũ không có nhóm này. 2 service này có dữ liệu live qua contacts.py (60 bạn / 6 nhóm) nhưng không dispatch được qua `/api/svc/*`. |
| (chênh lệch chưa giải thích được) | 50 thao tác được | 52 đầy đủ | **+2 chưa đối chiếu được từng service**: con số cũ 50 không kèm danh sách 50 service nào, nên không xác định được 2 service nào là "mới đầy đủ" so với lúc đếm cũ. Khả năng cao là 2 op được hoàn thiện body sau lần đếm cũ (ví dụ nhánh nhóm của create_reminder, body đầy đủ của set_mute/delete_chat). Ghi nhận là chênh lệch mở, không đoán. |

**Kết luận đối chiếu:** con số cũ đã lỗi thời ở đúng 1 điểm lớn — nhóm "25 chưa hỗ trợ 409" nay bằng **0**; bù lại, thao tác được tăng từ 50 lên **73** (52 đầy đủ + 21 còn cờ unverified). Zalobot (10) và chat (11) giữ nguyên.

**Lưu ý về HTTP 409 (dễ nhầm với nhóm (c)):** ở cấp HTTP, `POST /api/svc/<action>` trả 409 cho **23/96** service — nhưng đó là 409 *theo thiết kế* (11 chat + 10 zalobot + 2 view, `handle_svc` services.py:2130 trả 409 cho mọi `UnsupportedService`), không phải "chưa có đường PC". Ngoài ra còn có 409 *có điều kiện* trong lúc dispatch (xem mục 5).

## 3. Bảng 96 dòng (thứ tự #1–#96 của báo cáo chuẩn)

Cột "bằng chứng": dòng `OPS` trong services.py (entry `_op(...)`) + dòng builder `_b_*` (nếu có); với nhóm chat/zalobot/view là dòng trong `_NOT_SUPPORTED` (services.py:1735). Cột "ghi chú": endpoint PC từ `CATALOG["pc"]` (path + mã lệnh trong bundle) + điểm chưa rõ.

| # | service | trạng thái | bằng chứng | ghi chú |
|---|---|---|---|---|
| 1 | `send_message` | (e) CHAT | _NOT_SUPPORTED services.py:1737 (không có action trong OPS) |  |
| 2 | `send_file` | (e) CHAT | _NOT_SUPPORTED services.py:1741 (không có action trong OPS) | Đường `sharefile_full` 11146/11191 là đường chết (Zalo trả 405); đường thật là 2 bước asyncfile (upload 11776/13000 + msg 11777/13001) — chat.py làm. |
| 3 | `send_image` | (e) CHAT | _NOT_SUPPORTED services.py:1745 (không có action trong OPS) |  |
| 4 | `get_logged_accounts` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1770 (không có action trong OPS) | Genuine gap (SERVICE-MAP §5): app PC đơn tài khoản, 1 session — xem tài khoản hiện tại ở /api/status. |
| 5 | `get_account_details` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1773 (không có action trong OPS) | Genuine gap: không có endpoint lấy chi tiết theo ownId; gần nhất là `profile/me-v2` 11139 (body chưa lần). |
| 6 | `find_user` | (a) ĐẦY ĐỦ | OPS `find_user` services.py:1431; builder services.py:692 | PC: /api/friend/profile/get (11420) |
| 7 | `get_user_info` | (b) body_unverified | OPS `get_user_info` services.py:1438; builder services.py:685 | PC: /api/social/friend/getprofiles/v2 (11140). Chưa biết toàn bộ body: `{userId, imei}` giữ từ audit cũ, chưa trích được caller của GET 11140. |
| 8 | `send_friend_request` | (a) ĐẦY ĐỦ | OPS `send_friend_request` services.py:1092; builder services.py:366 | PC: /api/friend/sendreq (11424) |
| 9 | `create_group` | (b) body_unverified | OPS `create_group` services.py:1164; builder services.py:417 | PC: /api/group/create (11185). `suggestionId` chưa biết giá trị — không gửi; v2 (`create/v2` 12443) còn `memberTypes`/`groupType` chưa rõ. |
| 10 | `get_group_info` | (a) ĐẦY ĐỦ | OPS `get_group_info` services.py:1173; builder services.py:426 | PC: /api/group/getmg (12604) |
| 11 | `add_user_to_group` | (a) ĐẦY ĐỦ | OPS `add_user_to_group` services.py:1180; builder services.py:434 | PC: /api/group/invite (11186) |
| 12 | `remove_user_from_group` | (a) ĐẦY ĐỦ | OPS `remove_user_from_group` services.py:1188; builder services.py:440 | PC: /api/group/kickout (11187) |
| 13 | `send_image_to_user` | (e) CHAT | _NOT_SUPPORTED services.py:1748 (không có action trong OPS) |  |
| 14 | `send_images_to_user` | (e) CHAT | _NOT_SUPPORTED services.py:1750 (không có action trong OPS) |  |
| 15 | `send_image_to_group` | (e) CHAT | _NOT_SUPPORTED services.py:1752 (không có action trong OPS) |  |
| 16 | `send_images_to_group` | (e) CHAT | _NOT_SUPPORTED services.py:1754 (không có action trong OPS) |  |
| 17 | `get_account_webhooks` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1777 (không có action trong OPS) | Genuine gap: grep `webhook` trong bundle = 0 endpoint; webhook là khái niệm máy chủ zalobot. |
| 18 | `get_account_webhook` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1780 (không có action trong OPS) |  |
| 19 | `set_account_webhook` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1782 (không có action trong OPS) |  |
| 20 | `delete_account_webhook` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1784 (không có action trong OPS) |  |
| 21 | `get_proxies` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1786 (không có action trong OPS) | Genuine gap: không có proxy trong bundle/app PC; proxy chỉ có ở docker zalobot. |
| 22 | `add_proxy` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1789 (không có action trong OPS) |  |
| 23 | `remove_proxy` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1791 (không có action trong OPS) |  |
| 24 | `accept_friend_request` | (a) ĐẦY ĐỦ | OPS `accept_friend_request` services.py:1100; builder services.py:372 | PC: /api/friend/accept (11427) |
| 25 | `block_user` | (a) ĐẦY ĐỦ | OPS `block_user` services.py:1107; builder services.py:377 | PC: /api/friend/block (11422) |
| 26 | `unblock_user` | (a) ĐẦY ĐỦ | OPS `unblock_user` services.py:1113; builder services.py:382 | PC: /api/friend/unblock (11433) |
| 27 | `send_sticker` | (a) ĐẦY ĐỦ | OPS `send_sticker` services.py:1494; builder services.py:355 | PC: 1-1 /api/message/sticker (11154); nhóm /api/group/sticker (11165) |
| 28 | `undo_message` | (a) ĐẦY ĐỦ | OPS `undo_message` services.py:993; builder services.py:240 | PC: 1-1 /api/message/undo (11281); nhóm /api/group/undomsg (11192) |
| 29 | `create_reminder` | (b) body_unverified | OPS `create_reminder` services.py:1521; builder services.py:804 | PC: 1-1 /api/board/oneone/create (12429); nhóm /api/board/topic/create (12141). `src` chưa biết — không gửi. Nhánh nhóm qua `/api/board/topic/create` 12141 (đã lần); nhánh 1-1 `objectData` JSON-str. |
| 30 | `remove_reminder` | (a) ĐẦY ĐỦ | OPS `remove_reminder` services.py:1534; builder services.py:826 | PC: 1-1 /api/board/oneone/remove (12431); nhóm /api/board/topic/remove (12143) |
| 31 | `change_group_name` | (a) ĐẦY ĐỦ | OPS `change_group_name` services.py:1195; builder services.py:446 | PC: /api/group/updateinfo (11188) |
| 32 | `change_group_avatar` | (b) body_unverified | OPS `change_group_avatar` services.py:1201; builder services.py:451 | PC: /api/group/upavatar (11195). `avatarSize` chưa biết giá trị — không gửi. Upload file thật (multipart `fileContent`), không phải URL. |
| 33 | `send_voice` | (e) CHAT | _NOT_SUPPORTED services.py:1756 (không có action trong OPS) |  |
| 34 | `get_all_friends` | (x) VIEW — xem được ở danh bạ | _NOT_SUPPORTED services.py:1797 (không có action trong OPS) | Dữ liệu đã live trên UI danh bạ (60 bạn) qua contacts.py; POST /api/svc/get_all_friends → 409 status `view` (không phải op dispatch được). |
| 35 | `get_sent_friend_requests` | (a) ĐẦY ĐỦ | OPS `get_sent_friend_requests` services.py:1119; builder services.py:387 | PC: /api/friend/requested/list (12203) |
| 36 | `undo_friend_request` | (a) ĐẦY ĐỦ | OPS `undo_friend_request` services.py:1125; builder services.py:391 | PC: /api/friend/undo (11441) |
| 37 | `remove_friend` | (a) ĐẦY ĐỦ | OPS `remove_friend` services.py:1132; builder services.py:395 | PC: /api/friend/remove (11423) |
| 38 | `change_friend_alias` | (a) ĐẦY ĐỦ | OPS `change_friend_alias` services.py:1138; builder services.py:400 | PC: /api/alias/update (12201) |
| 39 | `remove_friend_alias` | (a) ĐẦY ĐỦ | OPS `remove_friend_alias` services.py:1147; builder services.py:406 | PC: /api/alias/remove (12202) |
| 40 | `get_all_groups` | (x) VIEW — xem được ở danh bạ | _NOT_SUPPORTED services.py:1799 (không có action trong OPS) | Dữ liệu đã live trên UI danh bạ (6 nhóm) qua contacts.py (v4 + getmg-v2); POST /api/svc/get_all_groups → 409 status `view`. |
| 41 | `get_group_chat_history` | (a) ĐẦY ĐỦ | OPS `get_group_chat_history` services.py:1067; builder services.py:333 | PC: /api/group/history (11240). CHỈ nhóm mới gọi được: thread 1-1 → dispatch raise UnsupportedService → HTTP 409 (services.py `_b_history_group` dòng 333). Lịch sử 1-1 không có endpoint HTTPS trong bundle. |
| 42 | `add_group_deputy` | (a) ĐẦY ĐỦ | OPS `add_group_deputy` services.py:1214; builder services.py:469 | PC: /api/group/admins/add (11814) |
| 43 | `remove_group_deputy` | (a) ĐẦY ĐỦ | OPS `remove_group_deputy` services.py:1222; builder services.py:469 | PC: /api/group/admins/remove (11815) |
| 44 | `change_group_owner` | (a) ĐẦY ĐỦ | OPS `change_group_owner` services.py:1230; builder services.py:476 | PC: /api/group/change-owner (10063) |
| 45 | `disperse_group` | (a) ĐẦY ĐỦ | OPS `disperse_group` services.py:1238; builder services.py:483 | PC: /api/group/disperse (11832) |
| 46 | `enable_group_link` | (a) ĐẦY ĐỦ | OPS `enable_group_link` services.py:1245; builder services.py:483 | PC: /api/group/link/new (11822) |
| 47 | `disable_group_link` | (a) ĐẦY ĐỦ | OPS `disable_group_link` services.py:1252; builder services.py:483 | PC: /api/group/link/disable (11823) |
| 48 | `join_group` | (a) ĐẦY ĐỦ | OPS `join_group` services.py:1265; builder services.py:490 | PC: /api/group/link/join (11825) |
| 49 | `leave_group` | (a) ĐẦY ĐỦ | OPS `leave_group` services.py:1271; builder services.py:496 | PC: /api/group/leave (11189) |
| 50 | `update_profile` | (b) body_unverified | OPS `update_profile` services.py:1454; builder services.py:706 | PC: /api/social/profile/update (12075). Fields cụ thể của POST 12075 chưa lần — body `{name?, dob?, gender?}` giữ từ audit cũ. |
| 51 | `update_settings` | (b) body_unverified | OPS `update_settings` services.py:1464; builder services.py:722 | PC: /api/setting/update (12033). Key thật của GET 12033 chưa lần — body `{settingType, status}` giữ từ audit cũ (object truyền thẳng). |
| 52 | `set_mute` | (a) ĐẦY ĐỦ | OPS `set_mute` services.py:1420; builder services.py:668 | PC: /api/social/profile/setmute (11288) |
| 53 | `set_pinned_conversation` | (a) ĐẦY ĐỦ | OPS `set_pinned_conversation` services.py:1305; builder services.py:981 | PC: /api/pinconvers/update (12121) |
| 54 | `get_unread_mark` | (a) ĐẦY ĐỦ | OPS `get_unread_mark` services.py:1364 | PC: /api/conv/getUnreadMark (12011) |
| 55 | `add_unread_mark` | (a) ĐẦY ĐỦ | OPS `add_unread_mark` services.py:1370; builder services.py:626 | PC: /api/conv/addUnreadMark (12013) |
| 56 | `remove_unread_mark` | (b) body_unverified | OPS `remove_unread_mark` services.py:1377; builder services.py:636 | PC: /api/conv/removeUnreadMark (12014). `convsGroupData`/`convsUserData` chưa biết — không gửi. |
| 57 | `delete_chat` | (b) body_unverified | OPS `delete_chat` services.py:1385; builder services.py:646 | PC: 1-1 /api/message/deleteconver (11778); nhóm /api/group/deleteconver (11835). `cliMsgId`/`conver` lấy từ tin cuối hội thoại — chỉ gửi khi caller biết; giá trị `conver` chưa lần. |
| 58 | `get_archived_chat_list` | (a) ĐẦY ĐỦ | OPS `get_archived_chat_list` services.py:1323; builder services.py:509 | PC: /api/archivedchat/list (12076) |
| 59 | `get_auto_delete_chat` | (a) ĐẦY ĐỦ | OPS `get_auto_delete_chat` services.py:1395 | PC: /api/conv/autodelete/getConvers (12022) |
| 60 | `update_auto_delete_chat` | (a) ĐẦY ĐỦ | OPS `update_auto_delete_chat` services.py:1402; builder services.py:659 | PC: /api/conv/autodelete/updateConvers (12023) |
| 61 | `get_hidden_conversations` | (a) ĐẦY ĐỦ | OPS `get_hidden_conversations` services.py:1330; builder services.py:516 | PC: /api/hiddenconvers/get-all (10048) |
| 62 | `set_hidden_conversations` | (a) ĐẦY ĐỦ | OPS `set_hidden_conversations` services.py:1337; builder services.py:520 | PC: /api/hiddenconvers/add-remove (10049) |
| 63 | `update_hidden_convers_pin` | (a) ĐẦY ĐỦ | OPS `update_hidden_convers_pin` services.py:1347; builder services.py:529 | PC: /api/hiddenconvers/update-pin (10050) |
| 64 | `reset_hidden_convers_pin` | (a) ĐẦY ĐỦ | OPS `reset_hidden_convers_pin` services.py:1356 | PC: /api/hiddenconvers/reset (10051) |
| 65 | `get_mute` | (a) ĐẦY ĐỦ | OPS `get_mute` services.py:1413 | PC: /api/social/profile/getmute (11280) |
| 66 | `get_pin_conversations` | (a) ĐẦY ĐỦ | OPS `get_pin_conversations` services.py:1316; builder services.py:505 | PC: /api/pinconvers/list (12120) |
| 67 | `add_reaction` | (b) body_unverified | OPS `add_reaction` services.py:1074; builder services.py:586 | PC: 1-1 /api/message/reaction (12410); nhóm /api/group/reaction (12411). Chỉ map được icon `like` (rType 3, rIcon `/-strong`); icon khác phải truyền `r_icon`/`r_type` tay. Domain REACTION chỉ resolve qua services map lúc login — map thiếu → 409. |
| 68 | `delete_message` | (a) ĐẦY ĐỦ | OPS `delete_message` services.py:1000; builder services.py:256 | PC: 1-1 /api/message/delete (11779); nhóm /api/group/deletemsg (11834) |
| 69 | `forward_message` | (b) body_unverified | OPS `forward_message` services.py:1008; builder services.py:267 | PC: 1-1 /api/message/forward (11199); nhóm /api/group/forward (11818). Chỉ gửi khung `{toId|grid, imei}`; transform theo loại tin (`msgType`, `msgs`/`totalIds`, file/photo) CHƯA lần. |
| 70 | `parse_link` | (a) ĐẦY ĐỦ | OPS `parse_link` services.py:1047; builder services.py:312 | PC: /api/message/parselink (11285) |
| 71 | `send_card` | (e) CHAT | _NOT_SUPPORTED services.py:1759 (không có action trong OPS) | Đường card user thường CHƯA lần riêng (chỉ có biến thể OA `forwardContactOA` 11774/11827) — chat.py cũng chưa implement. |
| 72 | `send_link` | (e) CHAT | _NOT_SUPPORTED services.py:1763 (không có action trong OPS) | chat.py `send_link` đã implement (1-1 link 11286, nhóm sendlink 11193). |
| 73 | `get_stickers` | (a) ĐẦY ĐỦ | OPS `get_stickers` services.py:1505; builder services.py:755 | PC: /api/message/sticker/category/list (11155) |
| 74 | `get_stickers_detail` | (a) ĐẦY ĐỦ | OPS `get_stickers_detail` services.py:1511; builder services.py:762 | PC: /api/message/sticker/category/detail (11156) |
| 75 | `send_video` | (e) CHAT | _NOT_SUPPORTED services.py:1766 (không có action trong OPS) | Chỉ có bước upload (12058/12061 + thumb); bước send sau upload CHƯA lần hết — chat.py cũng chưa implement. |
| 76 | `create_note_group` | (b) body_unverified | OPS `create_note_group` services.py:1278; builder services.py:895 | PC: /api/board/topic/create (12141). `src` chưa biết — không gửi; `createGroupTopicv2` chưa trích hết các nhánh. |
| 77 | `edit_note_group` | (b) body_unverified | OPS `edit_note_group` services.py:1288; builder services.py:911 | PC: /api/board/topic/update (12142). Như #76 + `topicId`; `needPin` chỉ gửi khi caller truyền `pin_act`. |
| 78 | `get_list_board` | (b) body_unverified | OPS `get_list_board` services.py:1298; builder services.py:929 | PC: /api/board/list (12140). `board_type`/`page`/`count`/`last_id`/`last_type` chưa biết giá trị — chỉ gửi khi caller truyền. |
| 79 | `create_poll` | (b) body_unverified | OPS `create_poll` services.py:1580; builder services.py:535 | PC: /api/poll/create (12080). `src` chưa biết — không gửi (các trường còn lại đã lần từ UI `_createPoll`). |
| 80 | `get_poll_detail` | (a) ĐẦY ĐỦ | OPS `get_poll_detail` services.py:1594; builder services.py:549 | PC: /api/poll/detail (12081) |
| 81 | `lock_poll` | (a) ĐẦY ĐỦ | OPS `lock_poll` services.py:1601; builder services.py:554 | PC: /api/poll/end (12089) |
| 82 | `edit_reminder` | (b) body_unverified | OPS `edit_reminder` services.py:1543; builder services.py:840 | PC: 1-1 /api/board/oneone/update (12430); nhóm /api/board/topic/updateEventResponse (12087). Nhánh nhóm `type` chưa biết — không gửi; nhánh 1-1 `src` chưa biết. |
| 83 | `get_reminder` | (a) ĐẦY ĐỦ | OPS `get_reminder` services.py:1555; builder services.py:854 | PC: /api/board/topic/getReminder (12088) |
| 84 | `get_list_reminder` | (b) body_unverified | OPS `get_list_reminder` services.py:1564; builder services.py:877 | PC: 1-1 /api/board/oneone/list (12432); nhóm /api/board/listReminder (12425). Thật là `objectData` JSON-str (`uid`/`group_id` + phân trang) — chỉ gửi key đã biết. |
| 85 | `get_reminder_responses` | (a) ĐẦY ĐỦ | OPS `get_reminder_responses` services.py:1570; builder services.py:888 | PC: /api/board/topic/listResponseEvent (12086) |
| 86 | `add_quick_message` | (b) body_unverified | OPS `add_quick_message` services.py:1609; builder services.py:560 | PC: /api/quickmessage/create (12029). `media`/`type` chưa biết kiểu/giá trị — không gửi. Domain QUICK_MESSAGE qua services map — map thiếu → 409. |
| 87 | `get_quick_message` | (a) ĐẦY ĐỦ | OPS `get_quick_message` services.py:1619; builder services.py:568 | PC: /api/quickmessage/list (12025) |
| 88 | `remove_quick_message` | (a) ĐẦY ĐỦ | OPS `remove_quick_message` services.py:1625; builder services.py:572 | PC: /api/quickmessage/delete (12032) |
| 89 | `update_quick_message` | (b) body_unverified | OPS `update_quick_message` services.py:1634; builder services.py:577 | PC: /api/quickmessage/update (12026). `media`/`type` chưa biết — không gửi; KHÔNG có `imei` (đúng bundle). |
| 90 | `get_labels` | (a) ĐẦY ĐỦ | OPS `get_labels` services.py:1646; builder services.py:944 | PC: /api/convlabel/get (12161) |
| 91 | `block_view_feed` | (a) ĐẦY ĐỦ | OPS `block_view_feed` services.py:1154; builder services.py:410 | PC: /api/friend/feed/block (12204) |
| 92 | `change_account_avatar` | (b) body_unverified | OPS `change_account_avatar` services.py:1475; builder services.py:731 | PC: /api/profile/upavatar (11819). `avatarSize`/`metaData` chưa biết — không gửi. Upload file thật (POST 11819), không phải URL. |
| 93 | `get_avatar_list` | (b) body_unverified | OPS `get_avatar_list` services.py:1485; builder services.py:741 | PC: /api/social/avatar-list (12451). Body `{count, page, imei}` chưa lần hết (endpoint GET 12451 đã rõ). |
| 94 | `last_online` | (b) body_unverified | OPS `last_online` services.py:1446; builder services.py:699 | PC: /api/social/profile/lastOnline (12090). `conv_type` chưa biết giá trị — không gửi; body thật là `{uid, imei}`. |
| 95 | `send_typing_event` | (a) ĐẦY ĐỦ | OPS `send_typing_event` services.py:1061; builder services.py:348 | PC: 1-1 /api/message/typing (11144); nhóm /api/group/typing (11196) |
| 96 | `get_login_qr` | (d) ZALOBOT | _NOT_SUPPORTED services.py:1793 (không có action trong OPS) | Không phải gap chức năng: QR PC đã native trong app (`reqqr` 11133 → `getLoginInfo` 11134, qr_login.py). |
## 4. Nhóm (b) body_unverified — 21 service, trường body nào chưa biết

Danh sách này khớp 1–1 với tập `unverified` trong `test_catalog_body_unverified_flagged` (tests/test_services.py:171) trừ 3 op ngoài 96 (`mark_seen`, `get_group_link`, `update_label`). Nguồn chi tiết: comment ngay trên từng builder trong services.py + SERVICE-MAP.md §4.

| # | service | Trường body chưa biết / chưa lần hết (code ghi rõ — trường nào chưa biết thì KHÔNG gửi) |
|---|---|---|
| 7 | get_user_info | Toàn bộ body chưa trích được caller của GET `/api/social/friend/getprofiles/v2` 11140 — body `{userId, imei}` chỉ là giữ từ audit cũ. |
| 9 | create_group | `suggestionId` chưa biết giá trị (v1 GET 11185); v2 `create/v2` 12443 còn `memberTypes`, `groupType` chưa rõ. |
| 29 | create_reminder | `src` chưa biết (cả 2 nhánh); nhánh nhóm qua `/api/board/topic/create` 12141 đã lần, nhánh 1-1 `objectData` JSON-str đã lần khung. |
| 32 | change_group_avatar | `avatarSize` chưa biết giá trị. (Upload file đã đúng — multipart `fileContent`, POST 11195.) |
| 50 | update_profile | Fields cụ thể của POST `/api/social/profile/update` 12075 chưa lần — body `{name?, dob?, gender?}` giữ từ audit cũ. |
| 51 | update_settings | Key thật của GET `/api/setting/update` 12033 chưa lần (object truyền thẳng) — body `{settingType, status}` giữ từ audit cũ. |
| 56 | remove_unread_mark | `convsGroupData` / `convsUserData` trong `param` JSON-str chưa biết. |
| 57 | delete_chat | `cliMsgId` / `conver` lấy từ tin cuối hội thoại — chỉ gửi khi caller biết; giá trị `conver` chưa lần. |
| 67 | add_reaction | Chỉ map được icon `like` (rType 3, rIcon `/-strong`); các icon khác (heart/haha/wow/cry/angry…) chưa có cặp `(rIcon, rType)` — bảng icon nằm trong config server `reactionMsgInfo`, chưa lần được; caller phải truyền `r_icon`/`r_type` trực tiếp. |
| 69 | forward_message | Transform theo loại tin (`msgType`, `msgs`/`totalIds`, field file/photo) chưa lần — hiện chỉ gửi khung `{toId|grid, imei}` cho từng đích. |
| 76 | create_note_group | `src` chưa biết; hàm `createGroupTopicv2` (POST 12141) chưa trích hết các nhánh. |
| 77 | edit_note_group | Như #76 + `topicId`; `needPin` chỉ gửi khi caller truyền `pin_act` (không đoán trạng thái ghim cũ). |
| 78 | get_list_board | `board_type` / `page` / `count` / `last_id` / `last_type` chưa biết giá trị — chỉ gửi khi caller truyền. |
| 79 | create_poll | `src` chưa biết (các trường còn lại đã lần từ UI `_createPoll`). |
| 82 | edit_reminder | Nhánh nhóm (`updateEventResponse` 12087): `type` chưa biết; nhánh 1-1: `src` chưa biết. |
| 84 | get_list_reminder | Body thật là `objectData` JSON-str (`uid`/`group_id` + phân trang) — các key `board_type`/`page`/`count`/`last_id`/`last_type` chỉ gửi khi biết. |
| 86 | add_quick_message | `media` / `type` chưa biết kiểu/giá trị (GET 12029). |
| 89 | update_quick_message | `media` / `type` chưa biết (GET 12026, KHÔNG có `imei`). |
| 92 | change_account_avatar | `avatarSize` / `metaData` chưa biết giá trị (POST 11819, upload file). |
| 93 | get_avatar_list | Body `{count, page, imei}` chưa lần hết (GET 12451, endpoint + mã đã rõ). |
| 94 | last_online | `conv_type` chưa biết giá trị (GET 12090); body thật là `{uid, imei}`. |

Để đợt sau lan tiếp, theo thứ tự ưu tiên gợi ý: (1) #67 bảng icon reaction (cần lần `reactionMsgInfo` trong config server/bundle — ảnh hưởng mọi reaction ngoài "like"); (2) #69 transform forward theo loại tin (cần lần `transformForwardMessage` trong bundle); (3) #7 body `getprofiles/v2` và #50 fields `profile/update` (lần caller UI); (4) #86/#89 `media`/`type` của quick message (lần UI tin nhắn nhanh); (5) #51 key thật của `setting/update` (lần caller UI cài đặt); còn lại là các trường lẻ (`src`, `suggestionId`, `avatarSize`, `conv_type`, `convs*Data`, `conver`) — lần caller tương ứng trong bundle.

## 5. Nhóm (c)/(f) — chưa hỗ trợ / thiếu khỏi catalog: KHÔNG CÓ service nào

- **(c) = 0, (f) = 0.** Mọi service trong 96 đều có mặt trong `CATALOG` (test `test_catalog_covers_all_96` assert `sorted(by_no) == list(range(1, 97))` và `counts["unsupported"] == 0`), và không service nào mang status `unsupported` ở cấp catalog. Vì vậy mục này không có "lý do 409 trong code" nào để ghi theo nghĩa nhóm (c), và không có gợi ý đường PC nào cần viết cho service thiếu.
- **Thay vào đó, 3 trường hợp 409 CÓ ĐIỀU KIỆN (service có trong catalog nhưng một số đường gọi vẫn trả 409)** — ghi lại để đợt sau không nhầm với nhóm (c):

| # | service | Khi nào trả 409 | Gợi ý đường PC khả thi (chỉ gợi ý, không sửa code) |
|---|---|---|---|
| 41 | get_group_chat_history | `type=user` (1-1): `_b_history_group` (services.py:333) raise `UnsupportedService` → `handle_svc` trả 409. | SERVICE-MAP.md §1 + §6: **không có endpoint HTTPS cho lịch sử 1-1** trong bundle — chỉ có DB local + `pull_mobile_msg` 12000 / `get_backupmsginfo` 12096 / `get_crossdb` 12412. Đường khả thi duy nhất là kênh sync/control (như `sync_poll.py`/`ctrl_poll.py` đang làm) hoặc đọc DB local, không phải một endpoint gửi tin mới. |
| 67 | add_reaction | Services map lúc login thiếu key `reaction` → `_domain_for` (services.py, `_SERVICES_MAP_DOMAINS`) raise `UnsupportedService` → 409 "Domain reaction chưa có trong services map… cần đăng nhập lại". | Không phải thiếu endpoint: domain REACTION chỉ có trong services map server trả về lúc login (`zpw_service_map_new`). Hướng lan: ghi log domain resolve được ở lần gọi đầu (code đã log host) rồi pin lại; đồng thời lần bảng icon `reactionMsgInfo` (xem mục 4, #67). |
| 86–89 | add/get/remove/update_quick_message | Như #67, với key `quick_message` trong services map → thiếu map thì 409. Riêng #87/#88 body đã đầy đủ, chỉ kẹt ở domain. | Như #67: domain QUICK_MESSAGE chỉ có trong services map; lần gọi đầu log host thực tế rồi pin lại, không hard-code (path `/api/quickmessage/*` gợi ý chat-wpa nhưng SERVICE-MAP.md §1 nói rõ chưa xác minh). |
| 34, 40 | get_all_friends / get_all_groups | Mọi `POST /api/svc/<tên>` → 409 status `view` (dispatch không thấy action trong `OPS`, tra catalog rồi raise theo status). | Không cần đường PC mới: dữ liệu đã live qua `contacts.py` (bạn: GET 11137; nhóm: v4 12027 + getmg-v2 12028). Nếu muốn gọi qua `/api/svc/*`, cần quyết định sản phẩm: hoặc thêm op chỉ-đọc vào `OPS` trỏ về contacts, hoặc giữ nguyên 409 + UI dùng tab danh bạ. |
| 71, 75 | send_card / send_video | Không trả 409 từ services.py mà là status `chat` (409) — và **chat.py cũng chưa implement** (xem mục 6). | #71: lần riêng đường card user thường trong bundle (hiện chỉ có biến thể OA `forwardContactOA` 11774/11827, SERVICE-MAP §3.2); #75: lần bước send sau upload (upload 12058/12059 + nhóm 12061/12062 đã rõ; bước send chưa trích được — zca-js làm `uploadAttachment` rồi `sendVideo({videoUrl, thumbnailUrl, duration})`, có thể dùng làm gợi ý đối chiếu, không copy mù). |

- **Nhóm (d) zalobot (10 service) — có cần đường PC không?** Không, theo thiết kế: 9 genuine gap trong SERVICE-MAP.md §5 (#4, #5, #17–#23) là khác biệt kiến trúc (đa tài khoản / webhook / proxy thuộc về máy chủ zalobot, không thuộc client PC); #96 là QR kiểu web, đã có tương đương native là QR kiểu PC (`reqqr` 11133 → `getLoginInfo` 11134). Không gợi ý đường PC cho nhóm này.

## 6. Test phủ (tests/test_services.py, 1101 dòng, 13 test — đã chạy: 13 passed)

- `test_catalog_covers_all_96` (dòng 125): pin catalog đủ 96, đúng 73 supported + 2 view + 11 chat + 10 zalobot + 0 unsupported; 5 op ngoài 96 không làm phồng số đếm.
- `test_catalog_body_unverified_flagged` (dòng 171): pin đúng tập 24 action body_unverified trong `OPS` (21 trong 96 + 3 ngoài 96).
- Dispatch mock (không login thật, MockZalo + envelope 2 lớp): message ops 2 thread (dòng 196), friends (310), group ops (363), pin/hidden/archived (488), reaction (547), poll (601), quick message (629), conversation/profile/sticker (666), reminders user-vs-group (793, ghi rõ "create nhóm: qua topic/create — không còn 409").
- `test_dispatch_refusals_and_validation` (dòng 874): 13 case từ chối đúng status (9 zalobot + 4 chat), 5 spot-check nhóm 25 cũ đều dispatch được, action lạ → `UnknownAction`, thiếu param → 400 (không gọi Zalo).
- `test_svc_http_api` (dòng 989): catalog HTTP 200, zalobot-only → 409 đúng status, chat → 409; login QR qua mock.
- **Không có test nào ghi service là "chưa hỗ trợ" hay "không có" trong 96** — test chỉ còn pin các từ chối *có chủ đích* (zalobot/chat/view). Test là mock (MockZalo), không phải bằng chứng live: chỉ #34/#40 có bằng chứng live ghi trong code (60 bạn / 6 nhóm đúng thật, contacts.py); các op còn lại chưa có bằng chứng gọi thật thành công lên Zalo trong đợt này.

## 7. Năm service thiếu/hỏng đáng chú ý nhất

1. **#71 send_card — không có đường chạy ở đâu cả.** Status `chat` nhưng chat.py chưa implement; đường card user thường chưa lần riêng (chỉ có biến thể OA `forwardContactOA`). Đây là service duy nhất trong nhóm chat mà cả hai tầng đều chưa có code.
2. **#75 send_video — dở dang ở bước cuối.** Status `chat`, chat.py chưa implement; chỉ lần được bước upload (12058/12061 + thumb), bước send sau upload chưa trích được từ bundle. Không bịa endpoint là đúng, nhưng service này hiện không gửi được video.
3. **#67 add_reaction — chạy được một nửa.** Chỉ icon `like` có map đã xác minh; mọi icon còn lại (heart/haha/wow/cry/angry…) bắt caller truyền tay `r_icon`/`r_type`, và domain REACTION phụ thuộc services map lúc login (thiếu map → 409).
4. **#41 get_group_chat_history — một nửa bị 409 theo thread.** Nhánh nhóm chạy (GET 11240), nhánh 1-1 raise 409 vì bundle không có endpoint HTTPS cho lịch sử 1-1 (chỉ DB local + sync). Đây là service duy nhất trong 73 "supported" mà một thread hợp lệ vẫn bị từ chối.
5. **#34/#40 get_all_friends / get_all_groups — dữ liệu có, op không.** Dữ liệu đã live đúng thật trên UI danh bạ, nhưng `POST /api/svc/*` trả 409 status `view`; con số cũ (50/25/10/11) không có chỗ cho 2 service này, và bảng này phải thêm nhóm (x) ngoài 6 nhóm của đề bài để đếm đủ 96.

## 8. Phương pháp & giới hạn

- Đọc kỹ `services.py` toàn bộ (docstring, 60+ builder `_b_*`, `OPS` dòng 991, `_SPLIT` dòng 1664, `_NOT_SUPPORTED` dòng 1735, `build_catalog()` dòng 1804, `dispatch()` + `handle_svc()` dòng 2130), `tests/test_services.py` toàn bộ, `server.py` phần `/api/svc/*` (dòng 2089, 2577–2660), SERVICE-MAP.md §0–§5.
- Số đếm không đếm tay: import module thật và dump `CATALOG`, đối chiếu từng `addon_no` 1–96 với services.yaml (YAML parse, đúng 96 key, thứ tự khớp) — mọi dòng bảng đều sinh từ dump đó + số dòng grep được từ file.
- "ĐẦY ĐỦ" ở đây nghĩa là **body đã lan hết từ bundle theo audit**, không phải đã gọi thật thành công lên Zalo: toàn bộ test là mock (MockZalo); chỉ #34/#40 có bằng chứng live ghi trong code. Đợt lan tiếp cần gọi thật từng op (đặc biệt 21 op body_unverified) mới xác nhận được body đúng.
- Không sửa code, không ghi bí mật nào. File này chỉ chứa tên service, endpoint/mã lệnh công khai từ bundle audit, và số dòng code.

---

# Phần B — Audit code app (ngoài 96 service + ngoài gọi)


- **Phạm vi:** `~/workspace/calling-push/zalo-pc-app/`, chỉ đọc, không sửa code.
- **Cây audit:** HEAD `2efce18` ("Codec 11300/11301 theo dinh dang that cua engine (zca-js)") — tức `0824c0d` + 1 commit codec của agent gọi chạy song song. Số dòng trong báo cáo này theo cây đó.
- **Ngoài phạm vi (không đếm ở đây):** 96 service (`services.py` — agent khác), phần gọi (`signaling.py`, `media_endpoints.py`, `udp_transport.py`, `call_log.py` — agent khác; chỉ ghi chú ngắn khi chạm tới). Quote/forward/undo/delete tin nhắn nằm ở `services.py`, không nằm ở `chat.py` — không đếm trùng sang agent service.
- **Phương pháp:** đọc code thật từng module, đối chiếu với `bao-cao-429.md`, `bao-cao-webhook.md`, `BAO-CAO-CHAT.md`, `bao-cao.md`. 3 phát hiện mức Cao đã **kiểm chứng live** bằng server tạm trên cổng loopback với `DATA_DIR` tạm trong `/tmp` (không đụng data thật): traversal `/fonts/`, bypass app-login ở `POST /api/thread/*`, crash khởi động khi `session.json` hỏng.
- **Không có bí mật nào trong file này** (không chép giá trị token/cookie/mật khẩu).

## Tổng số phát hiện: 43

| Mức độ | Số lượng |
|---|---|
| 🔴 Cao | 5 |
| 🟠 Trung bình | 18 |
| 🟡 Thấp | 20 |

## Top 5 nghiêm trọng nhất

1. 🔴 **Path traversal qua `/fonts/` (public, không cần đăng nhập) đọc được mọi file** — `zalo_pc_app/server.py:2066-2068` + `3290-3293`. Đã chứng minh live: `GET /fonts/../../../../../../../../tmp/.../marker.txt` trả về nội dung file. Trong container, 4 lần `../` là tới `/data/session.json` (chứa `zpw_sek`), `app_auth.json`, `webhooks.json`, `messages.db`.
2. 🔴 **`POST /api/thread/*` bypass đăng nhập app** — `zalo_pc_app/server.py:2575-2576` (trả về `_handle_thread_post` trước cổng app-login ở `2609-2612`); `_handle_thread_post` (`server.py:2359-...`) chỉ kiểm phiên Zalo. Đã chứng minh live: POST không cookie trả `{"error":"chua_dang_nhap"}` (cổng Zalo) thay vì `{"error":"chua_dang_nhap_app"}` như mọi `/api/*` khác.
3. 🔴 **Không chống brute-force ở `/api/app/login`** — `zalo_pc_app/server.py:2584-2599` + `zalo_pc_app/app_auth.py:179-201` (không đếm lần sai, không khóa, không delay, không log). Chỉ có 1 tài khoản dùng chung.
4. 🔴 **`session.json` hỏng → server không khởi động được** — `zalo_pc_app/session.py:50-53` (`load()` không try) + `zalo_pc_app/server.py:709` (load trực tiếp trong `AppState.__init__`, `STATE` dựng ở `server.py:1949` lúc import). Đã chứng minh live: file JSON hỏng → `JSONDecodeError`, tiến trình chết trước cả `main()`.
5. 🔴 **App không bao giờ kiểm chứng phiên Zalo; lỗi 600 không được xử lý** — `zalo_pc_app/server.py:834-867` (`public_status` chỉ kiểm `zpw_sek` còn trong file); grep toàn repo: chuỗi `600` chỉ xuất hiện trong câu gợi ý ở `zalo_pc_app/chat.py:868-879`, không có code nhánh nào xử lý. Phiên bị đá ở nơi khác → app vẫn báo `login: true`, user không được báo "quét lại QR", không tự hiện lại QR.

---

## 1. `server.py` — routing, static, auth cổng ngoài (phần auth xem thêm §7)

### H1. 🔴 Path traversal qua route `/fonts/` public — `server.py:2066-2068` + `3290-3293`
Route `/fonts/` không kiểm tra đăng nhập và truyền thẳng phần path vào `_serve_static(path.lstrip("/"), ...)`. `_serve_static` chỉ làm `open(os.path.join(STATIC_DIR, name), "rb")`, không `realpath`, không chặn `..`, không allowlist tên file. **Đã chứng minh live:** `GET /fonts/../../../../../../../../tmp/audit-h1/data/marker.txt` (không cookie) trả về đúng nội dung file. Trong container (`STATIC_DIR=/app/zalo_pc_app/static`), chỉ cần 4 lần `../` là tới `/data/session.json` → lộ `zpw_sek`/`zpw_enk`/`zpw_kt`, `app_auth.json` (hash mật khẩu app), `webhooks.json` (URL webhook có thể chứa token), `messages.db` (toàn bộ tin nhắn). Các route static khác dùng tên cố định nên an toàn; chỉ `/fonts/` nhận tên từ URL.
**Gợi ý:** chỉ serve tên file nằm trong allowlist `fonts/*.woff2` (hoặc kiểm `realpath` phải nằm trong `STATIC_DIR`), và/hoặc bắt đăng nhập app trước khi serve font.

### H2. 🔴 `POST /api/thread/*` bypass đăng nhập app — `server.py:2575-2576`, `2359-2440`
`do_POST` rẽ nhánh `/api/thread/` về `_handle_thread_post` **trước** cổng `_require_app_login()` (dòng `2609-2612`). `_handle_thread_post` chỉ gọi `_require_login()` (phiên Zalo), không kiểm tra cookie app. Hậu quả: ai tới được cổng HTTP là gửi tin nhắn/file/ghi âm, typing, seen, link thay tài khoản Zalo mà không cần mật khẩu app. **Đã chứng minh live:** POST `/api/thread/123/send` không cookie trả `{"error":"chua_dang_nhap"}` (cổng Zalo), trong khi `GET /api/status` không cookie trả `{"error":"chua_dang_nhap_app"}`. Giảm nhẹ: `HOST` mặc định `127.0.0.1` (`server.py:107`); rủi ro bùng lên khi bind LAN / sau reverse proxy. Docstring của `_handle_thread_post` (`server.py:2361-2366`) còn ghi "đăng nhập app chưa có trong bản copy" — đã lỗi thời so với phần còn lại của server.
**Gợi ý:** kiểm tra `_require_app_login()` ngay đầu `_handle_thread_post` (hoặc dời nhánh `/api/thread/` xuống sau cổng app-login trong `do_POST`), sửa docstring.

### M15. 🟠 Đọc body không giới hạn trước khi kiểm tra kích thước — `server.py:2031-2045`, `2355-2358`, `2470-2472`
`_read_json()` / `_read_raw()` đọc toàn bộ `Content-Length` vào RAM, không có giới hạn. Giới hạn file 100 MB ở `sendfile` (`server.py:2470`) chỉ kiểm tra **sau khi đã đọc xong** toàn bộ body → upload vài GB gây OOM trước khi bị từ chối 400. Tương tự `_read_json` cho mọi POST JSON khác.
**Gợi ý:** từ chối ngay theo `Content-Length` trước khi đọc (ví dụ >100 MB cho multipart, >1 MB cho JSON), và giới hạn trong `_read_json`/`_read_raw`.

### M11. 🟠 QR cũ vẫn hiện sau khi lỗi/hết hạn/từ chối — `server.py:1239-1253`, `1334-1345`
Các nhánh `except` của `_qr_worker` (RateLimited / UserRejected / QRExpired / TrustFlowRequired / Exception) chỉ đổi `qr_state`, **không xóa `self.qr`** (chỉ nhánh thành công `done` mới xóa ở `server.py:1226-1229`). `qr_status()` vẫn trả `qr_image` cũ khi state là `rejected`/`expired`/`error`/`rate_limited` → UI có thể hiển thị QR đã hết hạn, user quét mã chết.
**Gợi ý:** đặt `self.qr = None` trong mọi nhánh lỗi/hết hạn/từ chối (giữ lại `qr_wait` cho rate-limit).

---

## 2. `contacts.py` (310 dòng) — bạn bè / nhóm

Đã kiểm chứng đúng: dùng **v4 + getmg-v2** (`contacts.py:262-310`, `protocol.py:435-477`), không còn fallback v3; `avatar_size=160` (`protocol.py:419-424`); đếm thành viên nhóm đã sửa đúng bằng `totalMember` → `memberIds` → `currentMems` (`contacts.py:133-158`); cache TTL 120s + backoff 429 (60s, gấp đôi, tối đa 300s) + stale-while-revalidate nằm ở `server.py:126-128`, `908-1167` và khớp `bao-cao-429.md`.

### M1. 🟠 Bạn bè không phân trang, `count=20000` cứng — `protocol.py:411-417`, `contacts.py:243-258`
`friends_params` gửi `page: 1, count: 20000` duy nhất, không lặp trang. Tài khoản có >20.000 bạn bị cắt im lặng; `friends()` cũng không đọc `hasMore`/`total` nên UI không biết là thiếu.
**Gợi ý:** lặp `page` tới khi hết (hoặc khi `hasMore` false), hoặc ít nhất báo `truncated` khi trả đủ 20.000.

### M2. 🟠 Nhóm đông: `topMember` thiếu nhưng row không mang cờ — `contacts.py:170-196`
`_group_row` chỉ lấy `members` từ `topMember` (danh sách hiển thị, có thể thiếu khi `hasMoreMember` đặt). Row trả về không có trường `hasMoreMember`/`has_more_members` nên tầng gọi nhóm không biết là thiếu người — gọi nhóm đông sẽ thiếu thành viên. Docstring đã tự nhận "follow-up getgi/v2" nhưng chưa có code nào làm.
**Gợi ý:** thêm cờ `has_more_members` vào row; khi gọi nhóm đông thì gọi `getgi/v2` lấy đủ danh sách trước khi ring.

### L1. 🟡 Docstring ví dụ còn shape v3 cũ — `contacts.py:183-200`
Ví dụ trong docstring `describe_shape` vẫn minh họa dict `{groups, hasMore, total}` của v3, trong khi code đã dùng v4 (`gridVerMap`/`gridInfoMap`). Không ảnh hưởng chạy, nhưng gây nhầm cho người đọc/sửa sau.
**Gợi ý:** sửa ví dụ thành shape v4.

### L2. 🟡 Cờ `init=1` bị xóa cả khi nhóm lỗi — `server.py:1089-1090`
`_contacts_apply_fetch_result_locked`: friends thành công nhưng groups lỗi thì vẫn đặt `_contacts_init_pending = False`. Lần tải sau không còn gửi `init=1` cho friends dù lần đầu chưa hoàn tất trọn vẹn.
**Gợi ý:** chỉ xóa cờ khi cả friends lẫn groups đều thành công.

### L16. 🟡 Payload `/api/contacts` kèm toàn bộ `raw` — `server.py:889-908`, `contacts.py:243-310`
`_contacts_payload` trả nguyên `friends`/`groups` gồm cả trường `raw` (toàn bộ `gridInfoMap`, dữ liệu bạn bè thô) → response nặng hơn mức UI cần (60 bạn + 6 nhóm kèm raw), và lộ nhiều dữ liệu thô hơn cần thiết qua API nội bộ.
**Gợi ý:** chỉ trả `rows` + một số trường chẩn đoán gọn (số lượng, shape), không trả `raw` mặc định (thêm `?debug=1` khi cần).

### L19. 🟡 Thứ tự nhóm không ổn định — `contacts.py:296-310`
`groups()` trả rows theo thứ tự key của `gridVerMap` (thứ tự server trả), không sắp xếp theo tên → danh sách nhóm có thể nhảy thứ tự giữa các lần tải.
**Gợi ý:** sắp xếp rows theo `name` (không dấu, không phân biệt hoa thường) trước khi trả.

---

## 3. `chat.py` (1577 dòng) — gửi tin / file / ảnh / voice, lịch sử, typing/seen

Đã kiểm chứng đúng: lịch sử 1-1 **không có endpoint HTTPS** (giờ đọc từ `message_store` SQLite + Inbox + tin đã gửi, có notice trung thực — xem `server.py:2165-2205`); lịch sử nhóm qua 11240 (`chat.py:982-1005`); đường gửi file/voice hai bước + chờ event ctrl (`chat.py:1072-1255`, `1330-1549`); ghi âm webm/opus được đổi sang AAC trước khi gửi (xem §11). Quote/forward/undo/delete **không nằm ở đây** mà ở `services.py` (phần agent khác).

### M4. 🟠 `ChatStore` (tin đã gửi) tăng RAM vô hạn — `chat.py:762-786`
`record_sent` chỉ `append`, không cắt, không giới hạn — khác với `Inbox` (cắt 1000/thread, `sync_poll.py:308-340`) và `MessageStore` (cắt 5000/thread). Phiên dài, gửi nhiều → RAM tăng mãi; restart mới hết.
**Gợi ý:** cắt như Inbox (giữ N tin mới nhất/thread, ví dụ 1000).

### M7. 🟠 Lịch sử 1-1 chỉ có từ khi app bắt đầu lưu; `need_sync_msg` bị bỏ — `chat.py:1006-1011`, `qr_login.py:246-257`, `server.py:1189-1253`
`history_user_unavailable()` + notice `HISTORY_USER_DB_PARTIAL` đã nói trung thực, nhưng tin 1-1 cũ hơn thời điểm app bắt đầu lưu thì **không có cách nào lấy**: `pull_mobile_msg` (12000) / `get_backupmsginfo` (12096) / `get_crossdb` (12412) chưa implement. `parse_confirm` có lấy `need_sync_msg` (`needSyncMsg`) nhưng không chỗ nào trong `server.py` đọc nó — `_qr_worker` không kích hoạt đồng bộ từ điện thoại sau khi login.
**Gợi ý:** implement `pull_mobile_msg` sau login khi `need_sync_msg=true` (ưu tiên), hoặc ít nhất ghi rõ giới hạn này ở UI lịch sử 1-1.

### M10. 🟠 Gửi text không giới hạn độ dài, không retry 112 — `chat.py:1013-1037`
`send_text` chỉ kiểm rỗng; không giới hạn độ dài tin. Tin gửi bằng GET với `params=<AES JSON>` trong URL — tin rất dài có thể vượt giới hạn URL phía server (414) hoặc bị cắt. Không retry khi gặp 112 (lỗi tạm theo bundle) như `send_file`/`send_voice` đã làm (`_post_multipart_retry`, `_post_form_retry`).
**Gợi ý:** giới hạn độ dài tin (ví dụ 20.000 ký tự, báo rõ khi vượt) + retry 112 giới hạn như hai đường kia.

### L3. 🟡 Tin text có trường `title` ở top-level bị xếp thành file — `chat.py:677-708`
`normalize_message` lấy `file_name` từ `item.get("title")` rồi xếp `kind="file"` khi `file_name` có giá trị, và ghi đè `text` bằng tên file (`chat.py:706-708`). Một tin text có trường `title` sẽ hiển thị sai loại và mất nội dung gốc.
**Gợi ý:** chỉ coi là file khi `msgType` thuộc nhóm đính kèm (`_MSG_TYPE_KIND`) hoặc có `content.href`/`params.fileSize`, không dựa vào `title` top-level.

### L4. 🟡 `send_photo` không retry 112 — `chat.py:1255-1328`
`send_photo` dùng `_post_multipart` thẳng, không dùng `_post_multipart_retry` như `send_file`/`send_voice` → ảnh gặp lỗi tạm 112 là lỗi ngay, không nhất quán.
**Gợi ý:** dùng `_post_multipart_retry` như hai hàm kia.

### L5. 🟡 `ttl` âm không được kiểm — `chat.py:1013-1037`, `1039-1070`, `server.py:2440-2443`
`send_text`/`send_link` nhận `ttl` rồi `int(ttl)` gửi thẳng; server cũng chỉ `int()` không kiểm `>= 0` → `ttl` âm được gửi lên Zalo (hành vi không xác định).
**Gợi ý:** chặn `ttl < 0` thành 400 / ép về 0.

---

## 4. `file_inbox.py` (457 dòng) — nhận file/ảnh đến

Đã kiểm chứng đúng: giữ nguyên tên gốc, trùng tên thêm ` (1)` không ghi đè (`file_inbox.py:99-116`); sanitize chặn path traversal + kiểm `realpath` trong thư mục thread (`file_inbox.py:66-96`, `243-256`); kiểm size + md5 checksum trước khi lưu (`file_inbox.py:322-355`); registry JSON 0600 ghi atomic; `_send_bytes` đã sanitize tên file cho header (`server.py:1971-1985`).

### M8. 🟠 Tin voice/video đến không được tự tải — `file_inbox.py:60-62`, `server.py:1400-1412`
`AUTO_DOWNLOAD_KINDS = ("file", "photo")` — kind `"voice"` và `"video"` không tự tải về đĩa. Tin thoại đến do đó không có file local, nút Tải xuống/Chuyển tiếp phụ thuộc registry (chỉ có bản ghi khi đã tải tay).
**Gợi ý:** thêm `"voice"` (và `"video"` khi normalize đã phân loại được) vào `AUTO_DOWNLOAD_KINDS`, hoặc cho UI tải tay qua cùng một đường `download()`.

### M9. 🟠 Registry + thư mục downloads tăng vô hạn, không quota/dọn — `file_inbox.py:134-215`, `280-360`
`FileRegistry` không cắt mục cũ, không xóa bản ghi của file đã mất khỏi đĩa (chỉ lọc khi đọc); thư mục `downloads/<thread>/` chỉ thêm không bớt; không có giới hạn tổng dung lượng. Mỗi file tới 150 MB → đĩa đầy dần theo thời gian.
**Gợi ý:** quota tổng (ví dụ 2 GB) + dọn file/bản ghi cũ nhất, hoặc TTL cho file đã tải.

### L7. 🟡 `FileRegistry._save_locked` không chmod file tạm trước khi replace — `file_inbox.py:158-180`
File tạm được tạo với mode mặc định của umask (thường 0644) rồi mới `os.replace`, sau đó mới `chmod 0600` — có cửa sổ ngắn `registry.json` ở mode 0644 thay vì 0600 (khác với `SessionStore`/`WebhookStore` chmod tmp trước).
**Gợi ý:** `os.chmod(tmp, 0o600)` trước `os.replace` như các store khác.

---

## 5. `webhooks.py` (499 dòng) + `ctrl_poll.py` (754 dòng) + `sync_poll.py` (674 dòng) — webhook, kênh O3/tin đến/cuộc gọi đến, đồng bộ

Đã kiểm chứng: **cả 4 họ webhook đều đã có nguồn sự kiện thật** — `message` qua sync 99100 (`server.py:1380-1424` → `dispatch_message`), `group_event`/`reaction` qua ctrl 99101 (`ctrl_poll.py:190-365` `extract_group_events`/`extract_reactions` → `server.py:1435-1457` → `dispatch_*`). Giới hạn cũ trong `bao-cao-webhook.md` §6 ("chưa có nguồn sự kiện, chờ O3") **đã hết ở mức nối dây**; còn lại là shape live của group_event/reaction chưa được kiểm chứng bằng tin thật (chính `webhooks.py:30-50` cũng ghi rõ). **Kênh O3/WebSocket: chưa có** — `ws_endpoint` chỉ được lưu từ getLoginInfo (`session.py:14`, `server.py:1217`) chứ không chỗ nào mở WebSocket; UI lấy tin mới bằng polling `/api/thread/<id>/updates` (`sync_poll.py:60-61`). Theo thiết kế hiện tại (long-poll 99100/99101 là kênh đầy đủ) thì WS không bắt buộc, nhưng mọi sự kiện chỉ tới khi poller chạy.

### M5. 🟠 Webhook mất sự kiện im lặng: không retry, không hàng đợi — `webhooks.py:390-430`, `440-470`
`dispatch()` fire-and-forget trên thread daemon; lỗi chỉ ghi vào `_last` (20 mục, trong RAM, mất khi restart). HA/n8n chết đúng lúc có tin/cuộc gọi → sự kiện mất vĩnh viễn, không có API xem lại ngoài 20 mục gần nhất.
**Gợi ý:** hàng đợi bền (SQLite như `message_store`) + retry backoff + API xem lại/trạng thái gửi.

### M6. 🟠 Webhook `message` thiếu loại tin và file đính kèm — `webhooks.py:262-295`, `server.py:1414-1424`
`_on_sync_message` chỉ truyền `threadId/type/senderId/msgId/content/isSelf`; `build_message_event` không có `kind`/`file_url`/`file_name`. HA nhận webhook không phân biệt được tin text, tin file, ảnh hay voice note, cũng không có URL để tải.
**Gợi ý:** thêm `kind`, `file_url`, `file_name`, `file_size` (khi có) vào payload message.

### M3. 🟠 Hai kênh dùng con trỏ riêng, lệch bundle (chưa chứng minh bằng live) — `ctrl_poll.py:30-35`, `sync_poll.py:145-233`
Bundle dùng **chung một `idPoll`** cho cả hai poller; app tách `PollCursor` riêng mỗi kênh để tránh race. Chính `ctrl_poll.py:30-35` ghi "cần live kiểm chứng". Hậu quả nếu server kỳ vọng con trỏ chung: event ctrl có thể bị bỏ lỡ hoặc trùng khi hai kênh tiến con trỏ khác nhau.
**Gợi ý:** kiểm chứng live (so sánh tin/event nhận được khi dùng chung vs tách), rồi quyết định gộp hay giữ — ghi kết quả vào docstring.

### M16. 🟠 Mã kick-out chưa biết nên mọi `error_code != 0` đều retry mù — `sync_poll.py:1-100` (`KICK_OUT_NOTE`), `560-600`
`ERR_KICK_OUT` (biến `Fi` trong bundle) chưa lần ra giá trị số; `_poll_once` coi mọi mã khác 0 (trừ -69) là lỗi tạm → retry/backoff tới 5 lần rồi dừng với `stopped` thay vì báo "bị đá, quét lại QR". Phiên bị ép đăng xuất có thể mất nhiều phút mới lộ rõ.
**Gợi ý:** lần giá trị `Fi` trong bundle; khi gặp mã kick-out thì dừng poller và đặt trạng thái `kicked_out` rõ ràng như -69.

### M17. 🟠 `SyncCursorStore.save()` race làm mất con trỏ một kênh — `cursor_store.py:100-142`
`save()` dựng `new_data` dưới lock, **ghi file ngoài lock**, rồi mới gán `self._data = new_data` dưới lock. Hai poller (msg + ctrl) lưu cùng lúc có thể xen nhau: bản ghi sau ghi đè file và bộ nhớ bằng snapshot cũ, mất con trỏ mới của kênh kia → poll lại từ con trỏ cũ (trùng tin; dedup ở Inbox/`message_store` đỡ được phần trùng, nhưng vẫn là mất cập nhật).
**Gợi ý:** giữ lock xuyên suốt dựng + ghi file + gán (ghi file dưới lock), hoặc khóa riêng cho thao tác save.

### M18. 🟠 Gửi file/voice giữ request HTTP tới 120s chờ event ctrl — `chat.py:191-206`, `ctrl_poll.py:366-505`
`VOICE_ASYNC_WAIT_SECONDS` / `FILE_ASYNC_WAIT_SECONDS` = 120s; `wait()` chặn luồng handler. Dù đã kiểm `feeder_running` trước, kênh ctrl có thể chết **giữa chừng** → UI treo tới 2 phút. Cũng chưa replay chunk cuối khi hết giờ như bundle (chính `chat.py` docstring `send_voice` tự nhận).
**Gợi ý:** timeout chờ ngắn hơn theo từng bước + replay chunk cuối sau ~30s như bundle khi hết giờ (thay vì lỗi ngay).

### L17. 🟡 Vòng poll có sàn 1 giây → tin đến chậm thêm tới 1s — `sync_poll.py:602-650`, `ctrl_poll.py:686-724`
`run()` chờ đủ 1s mỗi vòng dù poll đã xong ngay. Chấp nhận được cho chat, nhưng là độ trễ cộng thêm có chủ đích.
**Gợi ý:** bỏ sàn 1s khi vừa nhận được tin (chỉ giữ khi poll trả rỗng liên tiếp), hoặc giảm xuống 200ms.

### L18. 🟡 Tin không có `time` luôn bị coi là mới — `sync_poll.py:347-360`
`Inbox.since()` lấy cả tin `time=None` (`when is None → lấy`). `/api/thread/<id>/updates` có thể trả lại tin cũ không có timestamp mỗi lần UI poll.
**Gợi ý:** tin không có time thì gán thời điểm nhận vào lúc `record`, hoặc loại khỏi `since` khi đã trả một lần.

---

## 6. `app_auth.py` (240 dòng) + cổng auth ở `server.py`

Đã kiểm chứng đúng: PBKDF2-HMAC-SHA256 210.000 vòng, salt 16 byte, hash 32 byte (`app_auth.py:28-30`); không có mật khẩu mặc định, thiếu ENV thì `main()` từ chối khởi động (`app_auth.py:130-175`, `server.py:3303-3315`); phiên cookie 8h, HttpOnly, SameSite=Lax (`app_auth.py:179-201`, `218-228`); mọi `/api/*` trả 401 khi chưa đăng nhập app — **trừ 2 ngoại lệ ở §1 (H1, H2)**; một tài khoản dùng chung (theo thiết kế).

### H3. 🔴 Không chống brute-force ở `/api/app/login` — `server.py:2584-2599`, `app_auth.py:179-201`
Không đếm lần sai, không khóa tài khoản/IP, không delay tăng dần, không ghi log lần sai. PBKDF2 210k vòng làm mỗi lần thử tốn ~0,1–0,2s (hạn chế phần nào) nhưng không ngăn được dò mật khẩu yếu/mật khẩu mặc định qua thời gian dài. Lỗi trả về chung một mã (`sai_tai_khoan`) là điểm tốt duy nhất.
**Gợi ý:** đếm lần sai theo IP (+ theo tài khoản), khóa tạm/delay tăng dần sau 5 lần sai, log lần sai (không log mật khẩu), cân nhắc thêm CAPTCHA khi mở ra ngoài loopback.

### M12. 🟠 Cookie `Secure` mặc định tắt; phiên token hết hạn không được dọn — `app_auth.py:184-201`, `218-238`
`Secure` chỉ bật khi `ZALO_PC_APP_COOKIE_SECURE=1`; mặc định cookie đi qua HTTP (đỡ bởi HOST loopback mặc định, nhưng hở khi chạy sau reverse proxy HTTP trên LAN). Token hết hạn chỉ bị xóa khi đúng token đó được `validate_token` gọi — token chết không bao giờ trình lại sẽ nằm mãi trong `_sessions`; không có "đăng xuất tất cả" / đổi mật khẩu qua UI.
**Gợi ý:** dọn token hết hạn định kỳ (khi login hoặc theo timer); bật `Secure` khi biết chạy sau HTTPS; thêm đổi mật khẩu + thu hồi toàn bộ phiên.

---

## 7. `session.py` (97 dòng) + `qr_login.py` (224 dòng) — phiên Zalo, QR

### H4. 🔴 `session.json` hỏng → sập toàn bộ server lúc khởi động — `session.py:48-53`, `server.py:709`, `1949`
`SessionStore.load()` không có try/except; `AppState.__init__` gọi `self.store.load()` trực tiếp; `STATE = AppState(DATA_DIR)` chạy lúc import. **Đã chứng minh live:** `session.json` chứa `{corrupt json!!!` → `JSONDecodeError` (traceback qua `json/decoder.py`), tiến trình chết trước cả `main()`. Người dùng phải tự xóa/sửa file trong volume mới chạy lại được; không có cơ chế tự phục hồi.
**Gợi ý:** `load()` trả `None` khi JSON hỏng (đổi tên file hỏng thành `session.json.corrupt` để còn cứu), `AppState` khởi động với phiên trống + log rõ.

### H5. 🔴 Không kiểm chứng phiên Zalo; lỗi 600 không được xử lý — `server.py:834-867`, `1540-1700`
`public_status` tính `logged = bool(sess and sess.get("zpw_sek"))` — chỉ kiểm file còn khóa, **không gọi Zalo lần nào** để xác thực phiên. Không có hàm validate phiên, không xử lý lỗi 600 ở bất cứ đâu (grep toàn repo chỉ thấy `600` trong chuỗi gợi ý ở `chat.py:868-879`). Khi Zalo đá phiên (đăng nhập PC khác, đổi mật khẩu…): app vẫn báo `login: true`; danh bạ/poll cứ lỗi 401/403 → `auth_failed`, nhưng session không bị xóa và UI không được đẩy về màn QR. Vòng retry nền (`server.py:1797-1827`) đã đúng khi **không** retry `auth_failed`/`kicked_out`, nhưng trạng thái kẹt ở đó cho tới khi user tự phát hiện.
**Gợi ý:** validate phiên nhẹ lúc khởi động và định kỳ (1 call rẻ qua `getLoginInfo` hoặc friends); khi gặp 600/401/403 kéo dài thì xóa `session.json` (hoặc đánh dấu `STATUS_QR_EXPIRED`), đặt `qr_state` về chờ quét và hiện banner "phiên đã hết, quét lại QR".

### L8. 🟡 `load()` không kiểm kiểu dữ liệu — `session.py:48-53`
`load()` trả nguyên JSON đã parse; nếu file chứa list/số (không phải dict) thì `sess.get(...)` ở khắp `server.py` ném `AttributeError` trong handler.
**Gợi ý:** `load()` trả `None` khi dữ liệu không phải dict (gộp với sửa H4).

### L9. 🟡 Làm tròn thời gian chờ rate-limit cộng thừa 5s — `qr_login.py:132-140`
`wait = wait + (5 - wait % 5)` cộng thêm 5 giây cả khi `wait` đã tròn bội của 5 (ví dụ 60 → 65).
**Gợi ý:** `wait += (-wait) % 5` (chỉ làm tròn lên khi chưa tròn).

### L10. 🟡 QR2 renew (-20) được coi như "đã quét" với event rỗng — `qr_login.py:176-183`
Nhánh `ERR_QR2_RENEW` trả event `{avatar: "", display_name: "", ...}` im lặng, `_qr_worker` sau đó đặt `qr_state = "scanned"` dù chưa có thông tin người quét.
**Gợi ý:** đặt trạng thái riêng (ví dụ `qr2_renew`) hoặc chờ confirm mới báo scanned; ghi log rõ nhánh này.

---

## 8. `message_store.py` (240 dòng) + `cursor_store.py` (148 dòng) — kho tin, con trỏ đồng bộ

Đã kiểm chứng đúng: tin đến + tin gửi được ghi SQLite bền qua restart (`message_store.py:100-180`, dedup cùng khóa với Inbox, cắt 5000/thread); `set_account` xóa tin khi đổi tài khoản (`message_store.py:100-125`); con trỏ lưu đĩa theo uid, file hỏng trả mặc định (`cursor_store.py:29-96`).

### L20. 🟡 Lỗi base64 khóa phiên thành 502 chung — `crypto.py:150-162`, `contacts.py:70-90`
`session_aes_encrypt` gọi `base64.b64decode(zpw_enk)` không try; khóa phiên hỏng (file session bị sửa tay) ném `binascii.Error` ra ngoài thành 502 chung thay vì thông báo "phiên hỏng, quét lại QR".
**Gợi ý:** bắt lỗi giải mã khóa ở tầng gọi Zalo, chuyển thành lỗi phiên rõ ràng.

---

## 9. `protocol.py` (471 dòng) + `crypto.py` (184 dòng) + `aes_pure.py` (206 dòng) — hằng số, mã hóa

Đã kiểm chứng: `aes_pure.py` kiểm tra độ dài key/block (`aes_pure.py:150-165`), kiểm tra PKCS#7 padding (`aes_pure.py:172-180`), S-box sinh từ định nghĩa GF(2^8); `decode_postlogin_data` mở envelope 2 lớp đúng (`crypto.py:165-183`); `signkey`/`ParamCipher` theo đúng mô tả bundle. Không thấy lệch rõ ràng nào so với bundle 26.11.10 trong phạm vi đã đọc — chỉ còn các điểm nghi ngờ dưới đây (không sửa, cần live/bundle đối chiếu thêm).

### M13. 🟠 `apiVersion`/`apiType` cứng, không nhận giá trị server trả — `protocol.py:36-60`, `probe_serverinfo.py:1-50`
`API_VERSION = 695`, `API_TYPE = 30` là hằng hard-code theo bundle 26.11.10. Chính `probe_serverinfo.py` ghi: client thật cập nhật `apiType`/`apiVersion` từ `getServerInfo`, nhưng app **không bao giờ gọi getServerInfo lúc chạy** — probe chỉ chạy tay. Nếu Zalo tăng version, mọi post-login call lỗi 602 cho tới khi sửa code + rebuild + deploy.
**Gợi ý:** gọi `getServerInfo` lúc khởi động (và khi gặp 602), nhận `type`/`client_version` server trả khi có, fallback về hằng hiện tại.

### L11. 🟡 `decode_postlogin_data` coi `error_code` chuỗi `"0"` là lỗi — `crypto.py:165-183`
Kiểm tra `inner.get("error_code") not in (0, None)` — nếu server trả `"0"` dạng chuỗi thì bị coi là lỗi dù thành công.
**Gợi ý:** chuẩn hóa về int trước khi so sánh (chấp nhận cả `"0"`).

---

## 10. `voice_transcode.py` (369 dòng) + `pc_media.py` (349 dòng) — định dạng voice, chuyển mã

Đã kiểm chứng đúng: đường hai bước hiện tại dùng **AAC-LC ADTS, mono 16 kHz, 64 kbps** (`voice_transcode.py:79-84`, `290-369`), khớp Node.js `voiceAac.js`; file đã là AAC ADTS thì gửi thẳng (nhận diện bằng ADTS syncword, `voice_transcode.py:310-330`); MP3 chỉ còn là đường cũ đã bỏ (voicemp3 trả 133, 0 caller trong bundle). `pc_media.py`: Opus 16 kHz, frame 20ms/640 byte PCM, SRTP hooks lazy-import.

### L6. 🟡 Đường MP3 cũ chết vẫn nằm trong code, docstring gây nhầm — `voice_transcode.py:108-130`, `180-290`
`ffmpeg_args()`, `to_zalo_voice_mp3()`, `ensure_voice_mp3()`, `needs_transcode()` **không còn caller nào** ngoài test (`server.py`/`chat.py` chỉ gọi `ensure_voice_aac`). Docstring `ffmpeg_args()` nhắc pin AAC của Node.js rồi mới nói "ở đây … libmp3lame" — đọc nhanh dễ tưởng hàm trả tham số AAC.
**Gợi ý:** chuyển toàn bộ hàm MP3 sang file riêng `_legacy_mp3.py` (hoặc xóa nếu test không cần), sửa docstring ghi rõ "chỉ dùng cho test/lưu trữ, đường chạy đã bỏ".

### L13. 🟡 `PcMediaEngine` drop frame im lặng; lỗi encode ném sai loại exception — `pc_media.py:130-145`, `320-349`
Hàng đợi PCM 50 frame (~1 giây) đầy thì `_on_pcm` chỉ tăng `_dropped` — không log, không báo lên UI. `encode()`/`decode()` lỗi ném `OpusUnavailable` dù lỗi không phải "không có libopus" (ví dụ `opus_encode` trả mã lỗi âm).
**Gợi ý:** log khi drop vượt ngưỡng; ném `ValueError`/`RuntimeError` riêng cho lỗi encode/decode, giữ `OpusUnavailable` cho trường hợp không load được lib.

### Ghi chú (không đếm): SRTP chưa bao giờ wired được trong image hiện tại
`pc_media.py:30-60` tự ghi: `zrtc_config` của 11300 live **không có `srtpKey`**, và image app là stdlib-only (không có libsrtp2/libopus, `make_srtp_hooks` lazy-import sẽ lỗi rõ ràng). Đây là thiếu đã biết thuộc phần gọi/media (agent khác), chỉ ghi nhận: mọi cuộc gọi hiện tại đều ở trạng thái signaling-only cho tới khi có nguồn key + bundle lib.

---

## 11. `engine_seam.py` (97 dòng) — seam media-engine (chỉ ghi trạng thái)

- Trạng thái: seam là placeholder đúng nghĩa — `SEAM.engine = None` mặc định, `/api/engine/status` báo trung thực "chưa có engine tiếng, gọi đi vẫn signaling được, chưa có tiếng" (`engine_seam.py:30-50`).
- `attach_pc_media` đã nối `PcMediaEngine` khi có transport (`engine_seam.py:66-89`).
- Xem L12 dưới đây (thấp, không đào sâu theo brief).

### L12. 🟡 `attach_pc_media` nuốt mọi lỗi im lặng — `engine_seam.py:66-89`
`except Exception: return False` không log gì — media không dây mà không biết vì sao (thiếu lib? transport lỗi?).
**Gợi ý:** log loại lỗi (không log nội dung) trước khi trả `False`.

---

## 12. `docker-entrypoint.py`, `probe_*.py`, `tests/run_tests.py`

### M14. 🟠 Entrypoint chỉ chown thư mục data, không đệ quy; thiếu user thì chạy luôn bằng root — `docker-entrypoint.py:33-66`
`_fix_data_dir` chỉ `os.chown` chính thư mục data khi khác owner, **không đệ quy**. File/thư mục con do lần chạy root trước tạo ra (ví dụ `downloads/`, `session.json` cũ) vẫn thuộc root → server chạy user `app` không ghi được → lỗi khó hiểu lúc chạy. Nếu user `app` thiếu, entrypoint chỉ cảnh báo rồi **chạy server bằng root luôn**.
**Gợi ý:** chown đệ quy (có giới hạn độ sâu/số file, hoặc chỉ chown các file app tự tạo) khi cần; nếu không drop được quyền thì fail rõ thay vì chạy root im lặng.

### L14. 🟡 `probe_reqqr.py` chưa commit; các probe không chạy trong CI — `probe_reqqr.py`, `probe_serverinfo.py`, `probe_relay.py`
`probe_reqqr.py` còn untracked (`??` trong `git status`); cả 3 probe chỉ chạy tay, không có trong `run_tests.py`, không có kiểm tra định kỳ. Probe `getServerInfo` (M13) vì thế không bao giờ chạy tự động.
**Gợi ý:** commit `probe_reqqr.py`; thêm chế độ `--selftest` (offline) của các probe vào `run_tests.py`.

### L15. 🟡 `run_tests.py` không có timeout từng suite — `tests/run_tests.py:1-74`
41/41 file test trên đĩa đều có trong danh sách (đã kiểm bằng script so sánh) — tốt. Nhưng `subprocess.run` không đặt `timeout`: một suite treo (ví dụ poller không dừng) thì cả bộ treo theo.
**Gợi ý:** thêm `timeout` (ví dụ 120s/suite) và báo suite nào timeout.

---

## Đối chiếu bối cảnh đã biết (đã kiểm chứng lại bằng code, không chép lại)

| Nội dung cũ | Kết quả kiểm chứng |
|---|---|
| Contacts v3 kỳ vọng `{groups, hasMore, total}` | **Đã đổi hẳn sang v4** (`gridVerMap` + `getmg-v2`, `contacts.py:262-310`); không còn code v3. |
| Cache TTL 120s, backoff 429 60s gấp đôi tối đa 300s, stale-while-revalidate | **Đúng**, ở `server.py:126-128`, `908-1167` (trả `source: fresh/cache/stale/cache-after-429`, `retry_after_seconds`). |
| Số thành viên nhóm hiện 0 | **Đã sửa** (`contacts.py:133-158`, ưu tiên `totalMember`). |
| Lịch sử 1-1 không có endpoint HTTPS, chỉ hiện tin gửi trong phiên, kho RAM mất khi restart | **Đã cải thiện một phần**: tin đến + tin gửi đã ghi SQLite bền qua restart (`message_store.py`); nhưng tin cũ hơn thời điểm bắt đầu lưu vẫn không lấy được (M7). |
| Tin đến chưa tự cập nhật | **Đã có**: sync 99100 đẩy tin vào Inbox + UI poll `/api/thread/<id>/updates` mỗi 5s; webhook message đã nối nguồn. |
| Ghi âm webm/opus, Zalo có thể từ chối vì không phải mp3 | **Đã xử lý**: đổi sang AAC ADTS trước khi gửi (`voice_transcode.py`); đường MP3 cũ đã bỏ vì bundle không gọi `sendVoice`. |
| Webhook tin/nhóm/reaction mới chỉ dispatch call | **Đã cũ**: cả 4 họ đều đã nối nguồn thật (99100/99101); chỉ còn shape live group_event/reaction chưa chứng minh. |
| Kênh O3 (tin đến/cuộc gọi đến) | **Chưa có WebSocket**; long-poll 99100/99101 là kênh duy nhất đang chạy, `ws_endpoint` chỉ được lưu chứ không dùng. |
| App login PBKDF2 210k, cookie 8h, mọi `/api/*` 401 | **Đúng, trừ H1 (fonts) và H2 (thread POST)**. Thiếu ENV thì từ chối khởi động — đúng. |
| Một tài khoản dùng chung, phiên mất khi restart | **Đúng**: phiên app chỉ trong RAM (`app_auth.py:179-201`); phiên Zalo thì bền qua `session.json`. |
| App không kiểm chứng phiên Zalo; lỗi 600 thì sao | **Xác nhận là lỗi thật (H5)**: không có code validate phiên hay xử lý 600; không tự hiện lại QR. |
| `protocol.py` lệch bundle 26.11.10? | Không thấy lệch rõ trong phạm vi đọc; chỉ còn M13 (version cứng, không nhận từ `getServerInfo`) là điểm cần live-check. |

---

## Ghi chú cho điều phối viên

- **Sửa trước (theo thứ tự):** H1 → H2 → H4 → H5 → H3. H1+H2 đều là lỗi cổng ngoài, sửa bằng vài dòng (allowlist fonts / cổng app-login cho thread POST) nhưng ảnh hưởng toàn bộ bảo mật app.
- **Không sửa trong đợt audit này** theo brief (chỉ đọc). Các file kết quả kiểm chứng live (`/tmp/audit-h1/`, `/tmp/audit-h4/`) là thư mục tạm, sẽ mất khi VM restart; bằng chứng đã ghi đủ trong báo cáo.
- **Tránh đếm trùng:** quote/forward/undo/delete nằm ở `services.py` (agent service); signaling/media/cuộc gọi thuộc agent gọi (commit `2efce18` vừa vào trong lúc audit — số dòng của `server.py`/`protocol.py`/`media_endpoints.py` có thể lệch nhẹ so với `0824c0d` gốc nếu agent gọi sửa tiếp).

---

# Phần C — Service mới có thể thêm (ngoài 96)


- Ngày: 2026-11-09. Chỉ đọc + nghiên cứu, không sửa code.
- Baseline «đã có» = bảng 96 service addon (`~/workspace/zalo-addon-doc/bao-cao-addon-96-services.md` mục 2)
  **cộng** những gì app PC đã có thêm: `/api/svc/` hỗ trợ 78 action (services.py),
  khung chat (`chat.py`: gửi text/ảnh/file/voice/video, lịch sử 1-1 + nhóm, quote, seen…),
  gọi đi 1-1 + nhóm (`/api/call/request`, 11300/11301, 12433/12434), board 1-1
  (`/api/board/oneone/*`), poll/quickmessage/reaction, file inbox, webhook.
  Chỉ những gì **không có trong cả hai** mới vào bảng ứng viên dưới đây.
- Nguồn đối chiếu:
  - zca-js v2.3.13 (`~/workspace/zca-js-softtyos/src/apis/`, 333 API / 12 domain) +
    `~/workspace/nv270/giao-nhi-m-v-/outbox/zca-js-tong-hop.md`.
  - Máy chủ zalobot: `/tmp/zalobot-ref/zalo-pc-app/zalobot-embedded/routes/api.js`
    (135 route) + `api/zalo/zalo.js` (100 hàm `*ByAccount`).
  - Bundle exe PC: `~/workspace/zalo-pc-reverse/` (Zalo 26.11.10, `so-sanh-416-11300-11301.md`,
    `bao-cao.md`, `SERVICE-MAP.md` tại `~/workspace/zalo-addon-native-96/`).
- Quy ước: **Ưu tiên** theo giá trị cho user (gọi đến/gọi video/STT/lịch sử cao nhất).
  **Độ khó**: dễ = 1 endpoint Zalo đã biết rõ body + không cần kênh mới; trung bình = cần
  kênh sync/event mới hoặc body chưa lần hết trên PC; khó = cần engine native (SRTP/ZRTP,
  Opus/H.264, Zavi SFU) hoặc mã hoá riêng (ZDB/ZCloud).

## Bảng ứng viên (56 service)

| # | Tên gợi ý | Mô tả ngắn | Nguồn | Ưu tiên | Độ khó | Phụ thuộc |
|---|---|---|---|---|---|---|
| A1 | Nhận cuộc gọi đến 1-1 | Nghe `call_event` act=`request` → đổ chuông (11302 ringring) → bắt máy (11303 answer) → xác nhận (11304 answerack); từ chối = 11306 endcall; log cuộc gọi nhỡ thay cho chữ `sendBubbleMessage` hiện tại | zca-js `call/ringRingVoiceCall`, `answerVoiceCall`, `answerAckVoiceCall`; `call-engine/ZaloRtcSession.ringIncomingCall/acceptIncomingCall` | Cao | Khó | Codec 11301 xong (đang sửa); SRTP/ZRTP để có tiếng sau khi bắt máy; kênh sync WS `call_event` (601/604) |
| A2 | Gọi video 1-1 | Gọi có hình: `typeRequest=3` (CallType.Video), codec video H.264 trong extendData, nhận/khử khung `video_annexb_frame` | zca-js `call/requestVoiceCall` (typeRequest 3), `createRtcSession` (H.264 Annex-B FU-A, PT 97/98); bundle: video codec `h264/payload 97` trong extendData | Cao | Khó | SRTP xong; codec 11301 xong; camera/capture phía app (chưa có); Opus audio trước, video sau |
| A3 | Gọi nhóm đầy đủ | Tham gia/phản hồi gọi nhóm đang diễn ra: xem trạng thái phòng (12445), tham gia từ banner (12043 join), bắt máy lời mời nhóm (12436), báo đổ chuông nhóm (12439), mời thêm người (12435), huỷ (12437) / rời (12438) / kết thúc toàn phòng (12446), thông báo vào chat nhóm (12447), ping (12097) + broadcast mic/cam (12098). App hiện chỉ có xin phòng (12433) + mời (12434) + rời (12438) | zca-js `call/getGroupCallState`, `joinGroupCall`, `answerGroupCall`, `ringRingGroupCall`, `addUserGroupCall`, `cancelGroupCall`, `finishGroupCall`, `notifyGroupCall`, `pingGroupCall`, `broadcastGroupCallState` | Cao | Khó | Zavi SFU handshake (Echo 248 → InitZaviPing 53 → RoomUpdated 50); SRTP; `partners` = member list qua `getGroupInfo` (app hiện gửi `[]`) |
| A4 | Nâng cấp thoại → video trong cuộc gọi | Đang gọi thoại thì bật camera, nâng cấp lên video (và ngược lại) | zca-js `call/requestAudioToVideoCall` (12056) | Trung bình | Khó | A2 xong (video engine) |
| A5 | Chia sẻ màn hình trong cuộc gọi | Bắt đầu/dừng share màn hình, 1-1 (12064) và nhóm (12044) | zca-js `call/requestShareScreenCall` (12064), `shareScreenGroupCall` (12044); bundle có `ZaloCap.exe` (capture) riêng | Thấp | Khó | A2/A3 xong; capture màn hình trên Linux (chưa có) |
| A6 | Tạm giữ / khôi phục cuộc gọi | Hold/unhold trong cuộc gọi (11307/11308, 11309/11310) | zca-js `call/holdVoiceCall`, `unholdVoiceCall`; app đã có `signaling.hold_request/hold_response/unhold_*` nhưng chưa có endpoint/UI | Thấp | Trung bình | Cuộc gọi 1-1 có tiếng (SRTP) xong; chỉ cần nối endpoint |
| A7 | Đồng bộ trạng thái mic/camera trong cuộc gọi | Báo mic tắt/mở, cam bật/tắt cho đối phương (conf 12006); dùng cho nút mute/camera trên UI gọi | zca-js `call/updateCallMediaState` (12006) | Trung bình | Trung bình | A1/A2 (đang trong cuộc gọi mới có ý nghĩa); mic/camera phía app |
| A8 | Thống kê chất lượng sau cuộc gọi | Gửi log QoS/billing sau khi kết thúc (11311 logendcall) | zca-js `call/logEndVoiceCall` (11311); app đã có `call_log.py` | Thấp | Dễ | Cuộc gọi kết thúc được (11306) — chỉ thêm 1 GET sau endcall |
| B1 | Chuyển giọng nói thành văn bản (STT) | Gửi URL voice → Zalo AI trả text, bất đồng bộ khớp bằng `req_id` | zca-js `media/voiceToText` (POST `/api/aifeatures/voice2text`, lệnh 13394), event `voice2text_event`; app chưa có (grep không thấy) | Cao | Trung bình | Kênh lắng nghe event async (ctrl_poll đã có `VoiceAsyncRegistry`, cần nối event `convert_finish`/99100 khớp `req_id`); gating phía server `v2t.transcribe.enabled` (mặc định false, không điều khiển được từ client) |
| B2 | Dịch tin nhắn bằng AI | Dịch thủ công (13397) / tự động (13398) / gợi ý (13399) + đọc/cập nhật cấu hình dịch (13395/13396); kết quả về qua `translate_event` | zca-js `chat/translateMessage*`, `getTranslateSetting`, `updateTranslateSetting` | Trung bình | Trung bình | Kênh event `translate_event`; UI hiển thị bản dịch |
| C1 | Tìm kiếm tin nhắn + lịch sử tìm kiếm | Tìm tin nhắn trong hội thoại; xem/xoá lịch sử tìm kiếm gần đây (12125) | zca-js `chat/getRecentSearchList` (12125), `updateRecentSearch`; app chưa có endpoint tìm kiếm | Trung bình | Dễ | Kho tin nhắn local (`message_store.py`) hoặc endpoint Zalo; không cần engine |
| C2 | Nhảy tới một tin nhắn cụ thể | Nhảy tới vị trí tin nhắn trong lịch sử cloud của nhóm + lấy nhiều tin cloud cùng lúc | zca-js `group/getGroupCloudMessageJump`, `getGroupCloudMessagePath`, `getMultiGroupCloudMessages` | Trung bình | Trung bình | Lịch sử nhóm cloud (12506/12507) đã có; cần hiểu tham số jump |
| C3 | Trạng thái từng tin nhắn (đã nhận/đã xem) | Truy vấn trạng thái deliver/seen của 1 tin (1-1: 12016, nhóm: 12017) và trạng thái đã xem cuối (12009) | zca-js `chat/getDirectMessageStatus` (12016), `group/getGroupMessageStatus` (12017), `chat/getLastSeen` (12009); app mới chỉ có *gửi* seen, chưa có *hỏi* trạng thái | Trung bình | Dễ | Không — endpoint độc lập |
| C4 | Tin nhắn offline + đồng bộ từ điện thoại | Lấy hội thoại có tin offline mới (12300); yêu cầu mobile đóng gói + tải lên bản sao lưu tin nhắn (ZDB 4.0) | zca-js `chat/getConvOfflineMessages` (12300), `sync/pullMobile`, `getSyncData`, `requestSyncFromPhone`; app có `sync_poll.py` (kênh PC) nhưng chưa có pull từ mobile | Trung bình | Khó | Hiểu ZDB 4.0 (RSA-2048 + AES-256-CBC multi-chunk); cần điện thoại phối hợp |
| C5 | Sao lưu / khôi phục tin nhắn | Xem thông tin bản sao lưu hiện có (12096), tải lên chunk backup, tải về bản sao lưu | zca-js `sync/getBackupMsgInfo` (12096), `uploadBackupChunk`, `downloadTransferSync` | Thấp | Khó | C4 (hiểu ZDB/backup); dung lượng lưu trữ |
| C6 | Hội thoại gợi ý | Danh sách hội thoại được gợi ý (11233) | zca-js `chat/getSuggestedConversations` (11233) | Thấp | Dễ | Không |
| C7 | Thu hồi nhiều tin nhắn cùng lúc | Thu hồi 1 loạt tin (96 chỉ có thu hồi 1 tin) | zca-js `chat/undoMultiMessage` | Trung bình | Dễ | Không — cùng họ endpoint undo đã có |
| D1 | Từ chối lời mời kết bạn | 96 chỉ có *chấp nhận* lời mời, không có *từ chối* — thiếu nửa chức năng | zca-js `friend/rejectFriendRequest`; zalobot cũng không có route này | Trung bình | Dễ | Không |
| D2 | Gợi ý kết bạn | Danh sách gợi ý kết bạn / lời mời đã nhận | zca-js `friend/getFriendRecommendations`; zalobot đã có route `getFriendRecommendationsByAccount` (96 không có) | Trung bình | Dễ | Không |
| D3 | Tìm user bằng username | Tìm người bằng username, không chỉ số điện thoại như `find_user` (#6) | zca-js `friend/findUserByUsername` | Trung bình | Dễ | Không |
| D4 | Danh bạ điện thoại V2 | Danh bạ bạn bè đồng bộ từ số điện thoại (12428) — tìm bạn từ danh bạ máy | zca-js `friend/getPhonebookV2` (12428) | Trung bình | Trung bình | Nguồn danh bạ (người dùng cấp); map số → userId |
| D5 | Bạn bè đang online (PC/Web) | Ai đang online, ai đang dùng PC/Web | zca-js `friend/getFriendOnlines`, `getFriendsActivePCWeb`; event `online_status_event` (603) | Trung bình | Dễ | Kênh event online (603) để cập nhật live; bản thân API là 1 GET |
| D6 | Danh sách biệt danh | Liệt kê tất cả biệt danh đã đặt cho bạn bè | zca-js `friend/getAliasList`, `getAliasListV2`; zalobot đã có route `getAliasListByAccount` (96 không có) | Thấp | Dễ | Không |
| D7 | Bạn thân (close friends) | Xem/cập nhật danh sách bạn thân | zca-js `friend/getCloseFriends`, `updateCloseFriend` | Thấp | Dễ | Không |
| E1 | Duyệt thành viên chờ vào nhóm | Xem danh sách chờ + duyệt/từ chối từng người | zca-js `group/getPendingGroupMembers`, `reviewPendingMemberRequest` | Trung bình | Dễ | Nhóm bật phê duyệt thành viên |
| E2 | Mời 1 user vào nhiều nhóm cùng lúc | Mời cùng 1 người vào nhiều nhóm trong 1 lần gọi | zca-js `group/inviteUserToGroups`; zalobot đã có route `inviteUserToGroupsByAccount` (96 không có) | Thấp | Dễ | Không |
| E3 | Cài đặt nhóm | Cập nhật cài đặt nhóm (quyền gửi tin, phê duyệt,…) | zca-js `group/updateGroupSettings`; zalobot đã có route `updateGroupSettingsByAccount` (96 không có) | Trung bình | Dễ | Body cài đặt trên PC chưa lần hết — đối chiếu zalobot/zca-js trước khi làm |
| E4 | Thành viên bị chặn trong nhóm | Xem/thêm/xoá thành viên bị chặn khỏi nhóm | zca-js `group/getGroupBlockedMember`, `addGroupBlockedMember`, `removeGroupBlockedMember` | Thấp | Dễ | Không |
| E5 | Chi tiết link tham gia nhóm | Xem thông tin link mời (96 chỉ có bật/tắt link, không có xem chi tiết) | zca-js `group/getGroupLinkDetail`, `getGroupLinkInfo`; zalobot đã có route `getGroupLinkInfoByAccount` (96 không có) | Thấp | Dễ | Không |
| E6 | Thống kê nhóm | Dữ liệu phân tích/thống kê nhóm (12407) | zca-js `group/analyseGroup` (12407) | Thấp | Dễ | Không |
| E7 | Nâng nhóm lên cộng đồng (Community) | Chuyển nhóm thường thành cộng đồng | zca-js `group/upgradeGroupToCommunity`, `checkQuotaCommunityMember`, `getQuotaCommunity` | Thấp | Trung bình | Hành động lớn, khó đảo ngược — cần xác nhận UI rõ ràng |
| E8 | Hộp thư mời vào nhóm | Xem danh sách hộp thư mời nhóm + tham gia từ hộp thư | zca-js `group/getGroupInviteBoxList`, `getGroupInviteBoxInfo`, `joinGroupInviteBox`, `deleteGroupInviteBox` | Thấp | Trung bình | Không |
| F1 | Bỏ phiếu poll | 96 có tạo/xem/khoá poll nhưng **không có bỏ phiếu** — thiếu nửa chức năng | zca-js `board/votePoll` | Cao | Dễ | Không — endpoint độc lập, UI poll đã có |
| F2 | Thêm phương án / chia sẻ poll | Thêm lựa chọn vào poll đang mở; chia sẻ poll sang hội thoại khác | zca-js `board/addPollOptions`, `sharePoll` | Trung bình | Dễ | Poll đã tạo (F1) |
| F3 | Ghim tin nhắn trong chat 1-1 | Ghim/bỏ ghim tin nhắn (khác với ghim *hội thoại* đã có) (12067) | zca-js `board/pinFriendMessage`, `unpinFriendMessages` (12067) | Trung bình | Dễ | Không |
| F4 | Ghim chủ đề trên bảng tin nhóm | Liệt kê/sắp xếp/ghim/bỏ ghim chủ đề bảng tin (12001) | zca-js `board/getListPinTopics`, `pinBoardTopic`, `unpinBoardTopic`, `multiUnpinBoardTopics`, `reorderPinTopics` | Trung bình | Dễ | Board nhóm đã có (`get_list_board`, note) |
| F5 | Zalo To-Do | Tạo/xem/cập nhật/xoá/hoàn thành công việc, nhắc việc (12413) | zca-js `board/createTodo`, `getTodoList`, `getTodoDetail`, `updateTodo`, `deleteTodo`, `verifyTodo`, `dingTodo`, `ackDingTodo`, `updateTodoStatus`; event `todo_event` | Trung bình | Trung bình | Kênh event `todo_event`; UI danh sách việc riêng |
| F6 | Phản hồi nhắc hẹn | Trả lời một nhắc hẹn (96 chỉ có xem danh sách phản hồi, không có gửi phản hồi) | zca-js `board/respondReminder` | Thấp | Dễ | Nhắc hẹn đã có |
| G1 | Kho lưu trữ hội thoại (ảnh/file/link) | Xem kho ảnh/video/file/link của 1 hội thoại, xem trước nhanh, xoá mục khỏi kho (11841–11843) | zca-js `media/getConversationMedia` (11841), `getMediaStorePreview` (11843), `removeConversationMedia` (11842) | Cao | Trung bình | Không cần engine; cần UI kho riêng (khác `/api/file/list` là inbox file local của app) |
| G2 | Kho cá nhân Send2Me / My Cloud | Kho ảnh/file/link của chính mình (12220–12222) | zca-js `media/getPersonalMedia` (12220), `getPersonalMediaPreview` (12221), `removePersonalMedia` (12222) | Trung bình | Trung bình | Không |
| G3 | ZCloud / lưu trữ đám mây | Thông tin + dung lượng + link tải/lên ZCloud (mã hoá 98yS) | zca-js `zcloud/getCloudInfo`, `getUsageMyCloud`, `getCloudDownloadUrls`, `getCloudUploadUrl`, `getCloudViewerKey` | Trung bình | Khó | Hiểu ZCloud crypto (AES-256-CBC, ViewerKey 98yS); G2 trước |
| H1 | Gửi GIF (Giphy/Guggy/Tenor) | Tìm + gửi GIF động từ Giphy/Guggy/Tenor | zca-js `sticker/searchGuggyGifs`, `searchGifs`, `getTrendingGifs`, `getGifCategories`, `getDefaultGuggyGifs`, `getTenorStickerMapping` | Trung bình | Dễ | Không — gửi như sticker/ảnh động |
| H2 | Gợi ý sticker theo ngữ cảnh | Gợi ý sticker theo nội dung đang gõ | zca-js `sticker/getStickerSuggestion`, `searchSticker`, `getStickerSuggestKeywords`, `getRecommendedStickers` | Thấp | Dễ | Khung chat (gợi ý lúc soạn tin) |
| H3 | Hiệu ứng tin nhắn | Xem hiệu ứng tin nhắn theo ID (11742) | zca-js `sticker/getMessageEffects`, `getMessageEffectById` | Thấp | Dễ | Không |
| I1 | Kiểm chứng phiên đang sống (keep-alive) | Chủ động hỏi Zalo xem phiên còn sống không, thay vì `/api/status` chỉ kiểm `session.json` còn `zpw_sek` (lỗi 5 đã biết: phiên bị đá vẫn hiện «Đã đăng nhập») | zca-js `auth/keepAlive` (tín hiệu duy trì phiên tới máy chủ Chat); xem thêm `zca-js-tong-hop.md` §7.6/§8.6 | Cao | Dễ | Không — gọi được ngay, nên làm sớm; khi hết phiên thì xoá session + hiện lại QR |
| I2 | Danh sách thiết bị đã đăng nhập | Xem các thiết bị/phiên đang đăng nhập tài khoản | zca-js `auth/getListDevice` | Trung bình | Dễ | Không |
| I3 | Đọc cài đặt riêng tư | Đọc cài đặt hiện tại (96 chỉ có *cập nhật* cài đặt, không có *đọc*) | zca-js `profile/getSettings` | Thấp | Dễ | Không |
| I4 | Tiểu sử + chế độ hồ sơ | Cập nhật bio, chế độ hồ sơ | zca-js `profile/updateProfileBio`, `updateProfileMode`, `getProfileExtra` | Thấp | Dễ | Không |
| I5 | Xoá / dùng lại avatar cũ | Xoá ảnh đại diện cũ, dùng lại avatar đã dùng | zca-js `profile/deleteAvatar`, `reuseAvatar`; zalobot đã có route `deleteAvatarListByAccount`, `reuseAvatarByAccount` (96 chỉ có xem list + đổi avatar) | Thấp | Dễ | Không |
| I6 | QR của chính mình / của nhiều user | Lấy mã QR cá nhân (để người khác quét kết bạn) | zca-js `auth/getQR`, `friend/getMultiUserQRCodes` | Thấp | Dễ | Không |
| I7 | Trạng thái hoạt động (online) | Cập nhật trạng thái đang hoạt động / mất tập trung | zca-js `auth/updateActiveStatus`, `lostFocus` | Thấp | Dễ | Không |
| I8 | Đổi ngôn ngữ tài khoản | Đổi ngôn ngữ giao diện/tài khoản | zca-js `auth/updateLang`; zalobot đã có route `updateLangByAccount` (96 không có) | Thấp | Dễ | Không |
| J1 | Báo cáo tin nhắn / người dùng | Báo cáo nội dung vi phạm | zca-js `chat/sendReport`; zalobot đã có route `sendReportByAccount` (96 không có) | Thấp | Dễ | Không |
| J2 | Gửi sự kiện «đã nhận» (delivered) | Báo đã nhận tin (app mới chỉ có *gửi* seen, chưa có delivered) | zca-js `chat/sendDeliveredEvent`; zalobot đã có route `sendDeliveredEventByAccount` (96 không có) | Thấp | Dễ | Không |
| J3 | Zalo OA — chặn/bỏ chặn, hồ sơ OA | Chặn/bỏ chặn Official Account, xem hồ sơ OA | zca-js `business/blockOA`, `unblockOA`, `getOAProfile`, `convertOAIds` | Thấp | Trung bình | Chỉ có ý nghĩa nếu user dùng OA; app cá nhân ít cần |
| J4 | Họp video nhóm Zavi | Họp video nhiều người qua Zavi SFU (client PC có `ZaviMeet.exe` riêng) | Bundle exe PC: `plugins/.../ZaviMeet.exe` (bao-cao.md §2); zca-js `call-engine` (Zavi SFU, CSRC[0] → partnerId) | Thấp | Khó | A3 (gọi nhóm) xong; video engine (A2) xong; SFU |

## Ghi chú theo nhóm

### Nhóm A — Gọi (A1–A8): giá trị cao nhất, khó nhất
- Toàn bộ `api.call` của zca-js (30 API) đều nằm ngoài 96. App hiện chỉ có: gọi đi 1-1
  (11300/11301, đang sửa codec), gọi đi nhóm (12433/12434), kết thúc (11306/12438),
  hàm hold trong `signaling.py` chưa nối endpoint, `vc_ringring/vc_answer/vc_answerack`
  trong `protocol.py` chưa nối listener. **A1 (gọi đến) là lỗ hổng lớn nhất**: user nhận
  được cuộc gọi mà app không đổ chuông, không bắt máy được, cuộc gọi nhỡ hiện sai chữ.
- Thứ tự làm nên là: codec 11301 → A1 (signaling gọi đến, chưa cần tiếng) → SRTP →
  A2/A3 (media) → A4–A7. A8 làm bất cứ lúc nào.
- Bundle exe không cho thêm lệnh gọi nào ngoài các lệnh zca-js đã liệt kê
  (11300–11311, 12006, 12043–12044, 12056, 12064, 12433–12447, 12097–12098);
  giá trị của bundle ở đây là xác nhận `platform=3`, codec, extendData — không phải
  service mới. `call-v2` named pipe (`PipeZCallRecv/Send`, AES khóa cố định) là
  IPC Windows-only, **không** áp dụng cho app Linux — loại trừ.

### Nhóm B — STT + dịch (B1–B2)
- B1 là service AI duy nhất của Zalo mà app chưa có; endpoint giống hệt đường PC đã
  biết (`/api/aifeatures/voice2text`, 13394), chỉ khác kênh nhận kết quả. Lưu ý
  gating phía server: nếu tài khoản chưa được bật `v2t.transcribe.enabled` thì API
  vẫn nhận request nhưng không trả text — cần test live mới kết luận.
- B1 không cần SRTP/engine, làm được song song với việc sửa codec gọi đi.

### Nhóm C — Lịch sử / tìm kiếm / đồng bộ (C1–C7)
- **Lịch sử 1-1 đã có trong app** (`/api/message/history`, `chat.py`) nên không vào bảng,
  dù 96 thiếu nó. C2/C3 là phần mở rộng tự nhiên của lịch sử đã có.
- C4/C5 (sync mobile, backup ZDB) là nhóm khó và ít giá trị trực tiếp cho dùng hàng ngày;
  chỉ nên làm khi user cần chuyển máy/khôi phục tin nhắn.

### Nhóm D — Bạn bè (D1–D7)
- D1 là thiếu sót rõ ràng nhất của 96 (có accept mà không có reject). D2/D6 có sẵn
  route ở zalobot nhưng 96 không expose — thêm vào app là việc nhỏ, chỉ cần map route
  zalobot → endpoint PC tương đương (hoặc gọi thẳng zca-js nếu body PC chưa lần).
- D4/D5 cần dữ liệu ngoài (danh bạ máy / event online) nên khó hơn vẻ ngoài.

### Nhóm E — Nhóm (E1–E8)
- E1 (duyệt thành viên chờ) là cái duy nhất có giá trị quản trị thực sự; còn lại là
  tiện ích nhỏ. E3/E5 có sẵn route zalobot — giống nhóm D, thêm nhanh.
- E7 không đảo ngược được, phải có xác nhận riêng trên UI.

### Nhóm F — Board / To-Do / Poll (F1–F6)
- F1 (bỏ phiếu) là «quick win» rõ ràng nhất: 96 có tạo/xem/khoá poll mà không bỏ
  phiếu được; 1 endpoint, không phụ thuộc gì.
- F5 (To-Do) là cụm tính năng riêng (cần UI + event `todo_event`); không nên làm
  lẻ 1 API mà làm cả cụm hoặc không làm.

### Nhóm G — Kho lưu trữ (G1–G3)
- G1 có giá trị thực tế cao: xem lại ảnh/file/link đã gửi trong 1 hội thoại mà không
  cần cuộn lịch sử. Khác với `/api/file/list` của app (inbox file local).
- G3 (ZCloud) khó vì mã hoá riêng; làm G2 trước để thăm dò.

### Nhóm H — Sticker / GIF (H1–H3)
- 96 đã có sticker cơ bản (gửi/tìm/chi tiết bộ). H1 (GIF) là bổ sung đáng kể nhất;
  H2/H3 là tiện ích nhỏ.

### Nhóm I — Tài khoản / phiên (I1–I8)
- **I1 nên làm ngay, không đợi gọi xong**: app đang báo sai trạng thái đăng nhập khi
  phiên bị đá (lỗi 5 trong UNFIXED_ERRORS); 1 API keep-alive là sửa được, độ khó dễ.
- I2–I8 đều là 1 endpoint độc lập, làm lẻ từng cái được.

### Nhóm J — Khác (J1–J4)
- J1/J2 có sẵn route zalobot, thêm nhanh. J3 (OA) chỉ phù hợp nếu user dùng OA —
  hiện chưa có nhu cầu. J4 (ZaviMeet) là hướng dài hạn, sau A2+A3.

## Những thứ đã kiểm tra và LOẠI (không phải service mới cho app)
- **Đã có trong app, dù 96 thiếu**: lịch sử chat 1-1 (`/api/message/history`); gửi
  voice 114 (đường PC, khác đường forward URL của zca-js `sendVoice`); board 1-1
  (`/api/board/oneone/*` ≈ `getFriendBoardList`); `getGroupMembersInfo` ≈
  `/api/group/getmg` (member list đã có); `updateLabels` ≈ `/api/convlabel/*`.
- **Chỉ thuộc máy chủ zalobot, không thuộc app PC** (theo SERVICE-MAP.md §5):
  đa tài khoản (`get_logged_accounts`, `get_account_details`), webhook admin
  (17–20), proxy (21–23), quản trị user/admin của server (`/users`, `/login`,
  `/change-password`, `/reset-admin-password`, `/health`, `/session-test`…),
  QR kiểu web (#96 — app đã có QR kiểu PC).
- **Business/OA nặng** (`createCatalog`, `createProductCatalog`, `createAutoReply`,
  `getBizAccount`, `registerCatalog`…): chỉ cho OA/shop, không phù hợp app cá nhân —
  không liệt kê ngoài J3.
- **Zalo To-Do / reminder đã có trong 96** (`create_reminder`, `get_list_reminder`…):
  chỉ F5/F6 là phần thiếu thật.
- **Đồng bộ ZDB/sync mobile, backup**: đã liệt kê ở C4/C5, không nhân thêm thành
  nhiều service lẻ (mỗi hàm `sync/*` là 1 bước của cùng 1 luồng).

## Đề xuất thứ tự (nếu chỉ chọn 1 đợt)
1. **Làm ngay, dễ, giá trị cao**: F1 (bỏ phiếu poll), I1 (kiểm chứng phiên), D1
   (từ chối kết bạn), C7 (thu hồi nhiều tin), G1 (kho lưu trữ hội thoại).
2. **Làm sau codec gọi đi**: A1 (gọi đến), B1 (STT).
3. **Làm sau SRTP**: A2 (gọi video 1-1), A3 (gọi nhóm đầy đủ), A7 (mic/cam).
4. **Để sau cùng / khi có nhu cầu rõ**: C4/C5 (sync/backup), G3 (ZCloud), J4 (ZaviMeet),
   E7 (lên cộng đồng), J3 (OA).

---
*Nguồn đã đọc: `bao-cao-addon-96-services.md` (bảng 96), `zca-js-tong-hop.md`,
`zca-js-softtyos/src/apis/*` (333 file), `routes/api.js` (135 route) +
`api/zalo/zalo.js`, `zalo-pc-reverse/` (bao-cao.md, so-sanh-416-11300-11301.md,
disasm-*.md), `zalo-pc-app/zalo_pc_app/` (services.py 78 action, server.py,
signaling.py, protocol.py, chat.py, media_endpoints.py). Không chứa bí mật nào.*
