# NV273 — Báo cáo: provider tự lấy danh sách model cho 4 module còn thiếu

- Nguồn nhiệm vụ: `inbox/NV273.md`, repo `TriTue2011/Giao-nhi-m-v-`,
  commit `07a1ba2`.
- Nền: `TriTue2011/web2api`, nhánh `muse/nv273`, từ `main` `ffb7f3e`.
- Đo trước khi làm (đúng lệnh trong file nhiệm vụ):
  - `grep -rln "lam_moi_model" modules/*/module.py` → **5 file**
    (antigravity, chatgpt-web, gemini-api, gemini-web, grok-api).
  - `ls modules/*/manifest.json` → **43 manifest**.
  - Khớp bằng chứng trong file NV273: 5/9 module AI có, 4/9 thiếu.
- Không chạm nhánh/file của NV272. Không sửa `app/` hay `web/` (lõi không
  nhắc tên nhà cung cấp, không có logic chung mới). Không đăng nhập thật,
  không gọi dịch vụ ngoài thật, không dùng key MCP, không vượt chống bot.
- Ba câu cho commit (theo NV273 §2d):
  1. Lớp lỗi: 4 module AI chưa có `lam_moi_model()` trong khi lõi và giao
     diện đã gọi phương thức này theo hợp đồng chung.
  2. Đã grep chỗ cùng lớp: `grep -rln "lam_moi_model" modules/*/module.py`
     → trước 5, sau **9**; `ls modules/*/manifest.json` → 43.
  3. Theo nguyên tắc, không theo danh sách: lõi chỉ gọi `lam_moi_model()`
     nếu callable, không nhắc tên nhà cung cấp; mỗi module tự chứa đủ
     logic của nó, không import chéo module khác.

## Đã đổi gì — theo từng module (mỗi module độc lập)

### claude-web
- `modules/claude-web/module.py`: thêm `lam_moi_model()` sau `models()`.
  Kiểm phiên thật qua `GET /api/organizations` đã có (`lay_org_id()`).
- `modules/claude-web/manifest.json`: thêm `model_tinh` (14 id `clw/...`).
- Nguồn: xem mục «Trung thực về nguồn» dưới đây.

### grok-web
- `modules/grok-web/module.py`: thêm `lam_moi_model()` sau `models()`.
  Kiểm phiên thật qua `/api/auth/session` đã có (`lay_uid_tu_phien()`).
  Thử thách truy cập (Cloudflare) không vượt, báo mã `mang` và dừng.
- `modules/grok-web/manifest.json`: thêm `model_tinh`
  (`grok/fast`, `grok/auto`, `grok/expert`, `grok/heavy`).

### openaicodex
- `modules/openaicodex/module.py`: thêm `lam_moi_model()` sau `models()`.
  Làm mới token OAuth thật của tài khoản đang hoạt động qua
  `_lam_moi_tai_khoan(ep=True)` đã có; không đánh dấu tài khoản hỏng
  (việc đó thuộc `lam_moi_phien`/chat).
- `modules/openaicodex/manifest.json`: thêm `model_tinh`
  (`openaicodex/gpt-5.5`, `openaicodex/gpt-5`).

### muse2api
- `modules/muse2api/module.py`: thêm `lam_moi_model()` sau `models()`.
  Kiểm cookie thật qua `_kiem_cookie()` đã có (auth/check + session,
  chạy trong luồng riêng như `suc_khoe()`).
- `modules/muse2api/manifest.json`: thêm `model_tinh` (`muse2api/muse`).

### Test mới
- `test/test_web2api_nv273_lam_moi_model.py`: 21 test — 5 test/module
  (thành công, xác thực, mạng hỏng, sai khuôn, không tài khoản) + 1 test
  bảng 9 module. Tất cả qua dịch vụ giả cục bộ (máy chủ giả loopback,
  `httpx.MockTransport`, hoặc chích `_kiem_cookie` giả cho muse2api).

## Hành vi chung của `lam_moi_model()` mới (cả 4 module)
- Có ít nhất một phiên/tài khoản còn dùng được → giữ danh sách, trả về.
- Mọi phiên đều hỏng → ném `RuntimeError` mang mã rõ: `xac_thuc`,
  `mang`, hoặc `sai_khuon`; **không xoá, không thay danh sách đang có**.
  Lõi (`app/lam_moi_model.py:lam_moi_mot`) gặp ngoại lệ này thì trả
  `loi` và không cập nhật sổ — danh sách cũ được giữ nguyên.
- `model_tinh` trong manifest sai khuôn hoặc danh sách hiện tại thiếu
  model đã khai → ném `sai_khuon`, giữ danh sách cũ.
- Chưa có tài khoản nào → trả về im lặng (như chatgpt-web); `models()`
  vẫn trả danh sách tĩnh (riêng openaicodex trả `[]` khi không có tài
  khoản đang hoạt động, giữ đúng hành vi cũ).

## Trung thực về nguồn — «không tự lấy được» cho cả 4
Đã kiểm trong repo, không bịa endpoint:
- claude-web: `GET /api/organizations` chỉ trả tổ chức + capability
  `chat`, không trả model. `/v1/models` của Anthropic cần API key, không
  phải cookie web của module → không dùng.
- grok-web: «model» là chế độ web app, khai tĩnh trong converter; không
  có endpoint HTTP liệt kê trong repo. `/v1/models` của xAI cần API key,
  không phải cookie web → không dùng.
- openaicodex: các đường đã dùng là `/backend-api/codex/responses` và
  `/backend-api/wham/usage`; không có đường liệt kê model nào cho token
  Codex OAuth trong repo. Không bịa `/backend-api/codex/models`.
  `/v1/models` của OpenAI cần API key, không phải token Codex → không dùng.
- muse2api: giao thức hiện tại chỉ có đúng một model (`muse`); không có
  endpoint liệt kê trong repo.

Vì vậy nguồn hiện tại là **danh sách tĩnh khai trong manifest**
(`model_tinh`), còn bước «lấy lại» là kiểm phiên thật như trên. File hỏi
lại đi kèm: `hoi-nv273-endpoint-liet-ke.md` (3 câu hỏi, trong đó câu 1
hỏi endpoint thật nếu chủ máy biết).

## Bảng nghiệm thu — module → có lam_moi_model → nguồn model → đã test

| Module | Có `lam_moi_model` | Nguồn model | Đã test |
|---|---|---|---|
| antigravity | Có (đã có) | `POST /v1/models/lam-moi` của cầu nối + đệm | Không đổi, test cũ xanh |
| chatgpt-web | Có (đã có) | `GET /backend-api/models` theo tài khoản | Không đổi, test cũ xanh |
| gemini-api | Có (đã có) | `GET {goc_api}/models` có phân trang | Không đổi, test cũ xanh |
| grok-api | Có (đã có) | `GET /models` của xAI qua bộ chuyển tiếp | Không đổi, test cũ xanh |
| gemini-web | Có (đã có) | Trang chủ gemini.google.com theo tài khoản | Không đổi, test cũ xanh |
| claude-web | **Có (mới, NV273)** | **Tĩnh trong manifest — không tự lấy được** | 5 test mới xanh |
| grok-web | **Có (mới, NV273)** | **Tĩnh trong manifest — không tự lấy được** | 5 test mới xanh |
| openaicodex | **Có (mới, NV273)** | **Tĩnh trong manifest — không tự lấy được** | 5 test mới xanh |
| muse2api | **Có (mới, NV273)** | **Tĩnh trong manifest — không tự lấy được** | 5 test mới xanh |

Sau NV273: `grep -rln "lam_moi_model" modules/*/module.py` → **9 file**.

## Kết quả kiểm chứng (số thật)

- Test mới NV273: **21 passed, 0 failed**.
- Nhóm test của 4 module + lõi làm mới model (17 file, gồm claude-web,
  grok-web, muse2api, nv173 codex, nv102 lam_moi_model/module_api,
  nv89, nv90, nv93, nv80, nv102 web grok claude, nv103, nv224, nv230,
  nv271 codex/claude): **293 passed, 0 failed** (một lỗi ban đầu do venv
  thiếu `paho-mqtt`, không phải do patch; sau khi cài đủ thì qua).
- Toàn bộ `test/` (chạy 2 shard do quirk import của môi trường, xem ghi
  chú dưới): shard A (mặc định, trừ file `dang_nhap_tu_dong`) **6061
  passed, 8 failed, 10 errors, 237 skipped, 31 xfailed** trong 17:40;
  shard B (mode importlib, chỉ file `dang_nhap_tu_dong`) **38 passed**.
  Tổng **6099 passed, 0 đỏ mới**: 8 failed gồm youtube_phat,
  bien_env_tai_lieu, nv159 c5, nv187, nv85 ×2 (cả 6 đã kiểm lại trên main
  sạch `ffb7f3e` — đỏ y hệt), nv261 lấy mẫu CPU và nv266 đo tài nguyên
  (chập chờn do tải: nv266 qua khi chạy riêng trên nhánh mới, lỗi ở
  full-suite là 429 «Đo quá dày: 1 lần/giây»); 10 errors gồm nv259 ×2 và
  nv268 giao diện ×8 (đã kiểm lại trên main sạch — lỗi y hệt).
  Ghi chú quirk: chạy mặc định thì file `test_web2api_dang_nhap_tu_dong.py`
  lỗi collection ở `from test.gia import` (stdlib `test` che mất), còn
  chạy mode importlib thì 93 file dùng `from gia import` lỗi collection;
  cả hai đều là quirk có sẵn trên main sạch, không phải do patch — vì vậy
  suite được chạy thành 2 shard bao phủ toàn bộ test/.
- `bandit -r app modules -lll`: thoát **0**.
- `git diff --check`: đạt. Quét bí mật/IP trên diff: sạch (không token,
  key, mật khẩu, cookie, email, IP thật; chỉ có cookie giả trong test và
  `127.0.0.1` trong test).

## Chưa kiểm (nói thật)
- Không đăng nhập thật, không gọi claude.ai / grok.com / chatgpt.com /
  muse.ai thật; không đo model theo gói Free/Pro thật.
- Chưa merge, chưa chạy trên server web2api đang chạy: nút «Làm mới danh
  sách» chỉ có tác dụng với 4 module này sau khi merge + dựng lại server.
- Câu hỏi trong `hoi-nv273-endpoint-liet-ke.md` chưa được trả lời.
