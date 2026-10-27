# Hỏi thêm — NV273: endpoint liệt kê model thật cho 4 module

## ĐÃ QUYẾT — đáp án của chủ máy, 2026-10-28 01:29 +07 (đã áp vào code)

1. **Không có endpoint liệt kê model thật → giữ danh sách tĩnh kèm kiểm
   phiên, ghi rõ «không tự lấy được».** Đã ghi rõ trong docstring
   `lam_moi_model()` của cả 4 module và trong báo cáo. Không bịa endpoint.
2. **Hai chỗ khai song song (manifest `model_tinh` và code) → giữ như
   hiện tại, dọn về một nguồn ở đợt sau.** Không refactor về một nguồn
   trong đợt này.
3. **openaicodex không làm mới token thật trong `lam_moi_model()`.**
   Đã bỏ `_lam_moi_tai_khoan(ep=True)` khỏi `lam_moi_model()`, thay bằng
   kiểm phiên GET `/backend-api/wham/usage` bằng access_token hiện tại;
   test `test_codex_lam_moi_khong_xoay_token` chứng minh token không đổi
   và OAuth không được gọi. Các câu hỏi dưới đây giữ lại làm hồ sơ gốc.

Nhánh: `muse/nv273` (web2api, từ `main` ffb7f3e) — xem `nv273-bao-cao.md`
đi kèm. Bản này đã làm xong phần khuôn: cả 4 module đều có
`lam_moi_model()` theo đúng hợp đồng lõi, test 21/21 xanh, và nguồn hiện
tại là danh sách tĩnh khai trong manifest (`model_tinh`).

## Câu hỏi

**1. Có endpoint liệt kê model nào dùng được với đúng loại xác thực web
của từng module không, hay giữ danh sách tĩnh?**

Đã kiểm trong repo (không bịa endpoint):

| Module | Đã kiểm | Kết quả |
|---|---|---|
| claude-web | `GET /api/organizations` (client đã có) | Chỉ trả tổ chức + capability `chat`, không trả model. `/v1/models` của Anthropic cần API key, không phải cookie web. |
| grok-web | WebSocket grok.com, `/api/auth/session` | «Model» thực chất là chế độ web app (fast/auto/expert/heavy). `/v1/models` của xAI cần API key, không phải cookie web. |
| openaicodex | `/backend-api/codex/responses`, `/backend-api/wham/usage` | Không có đường liệt kê model nào cho token Codex OAuth trong repo. `/v1/models` của OpenAI cần API key, không phải token Codex. |
| muse2api | Giao thức muse.ai (WebSocket + Noise) | Chỉ có đúng một model (`muse`); không có endpoint liệt kê trong repo. |

Nếu chủ máy biết endpoint thật nào (kèm loại xác thực nó chấp nhận),
cho tên endpoint + cách xác thực, Muse sẽ đổi nguồn của module đó từ tĩnh
sang lấy thật. Nếu không có, giữ nguyên danh sách tĩnh + kiểm phiên như
bản này, và bảng nghiệm thu ghi rõ «không tự lấy được» cho cả 4.

**2. Danh sách tĩnh có cần đồng bộ tay khi nhà cung cấp đổi model không?**

Hiện tại `model_tinh` trong manifest là bản sao của danh sách tĩnh đã có
trong code (converter / `DANH_SACH_MODEL` / `MODEL_ID`). Khi nhà cung cấp
thêm/bớt model, cần sửa cả hai chỗ (hoặc chỉ một chỗ nếu chủ máy muốn
đổi code để đọc thẳng từ manifest). Chủ máy muốn giữ hai chỗ song song
như hiện tại, hay dọn về một nguồn duy nhất?

**3. Có muốn `lam_moi_model()` của openaicodex làm mới token thật không?**

Hiện tại bước «lấy lại» của openaicodex là làm mới token OAuth thật của
tài khoản đang hoạt động (qua `_lam_moi_tai_khoan`, `ep=True`, bỏ qua
cache). Đây là tác dụng phụ có chủ ý: nó chứng minh tài khoản còn dùng
được, nhưng cũng xoay token. Nếu chủ máy chỉ muốn kiểm mà không xoay
token, nói rõ để đổi sang bước kiểm nhẹ hơn (khi có endpoint kiểm phù
hợp).
