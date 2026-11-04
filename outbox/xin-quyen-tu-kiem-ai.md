# Xin quyền để Muse tự kiểm lỗi đăng nhập AI và màn hình noVNC

Người gửi: Muse (trợ lý của chủ máy) — ngày 04/11/2026.
Kênh: outbox, nhánh `muse/xin-quyen-tu-kiem-ai`, nền Giao main `82d9ff46`.
Mục đích: xin các quyền và dữ liệu tối thiểu để Muse **tự kiểm được** lỗi đăng
nhập AI và màn hình đăng nhập (noVNC) mà **không cần chủ máy mở tay từng lần**,
từ đó tự sửa code phần AI rồi nộp lại bằng nhánh `muse/*` như mọi lần.

## 0. Tóm tắt yêu cầu

Muse xin 5 quyền (chi tiết ở mục 2):

- **Q-A — Nhìn thấy chế độ đăng nhập qua MCP:** tool `tai_khoan` trả thêm
  `dang_nhap_bang` / `cach_dang_nhap`, và nhật ký lần đăng nhập gần nhất gồm
  bước tới được + tín hiệu gặp + mã lỗi.
- **Q-B — Xem màn hình đăng nhập ở chế độ chỉ-đọc:** khóa xem ảnh màn hình
  (`/v1/man-hinh`) hoặc vé xem noVNC chỉ-đọc, giới hạn ở dịch vụ đăng nhập,
  có hạn + ghi log. **Không xin mật khẩu VNC, không xin quyền bấm/gõ.**
- **Q-C — Được phép đăng nhập qua MCP cho các tài khoản provider AI:**
  phê duyệt luôn phần allowlist của trio (Claude, Gemini, Grok) sau khi các tài
  khoản được lưu ở chế độ «dùng hồ sơ Google đã đăng nhập».
- **Q-D — Đọc log chẩn đoán của dịch vụ đăng nhập:** chỉ-đọc, không chứa bí mật
  (bước đã chạy, selector đã thử, tín hiệu gặp, URL, mã lỗi).
- **Q-E (tùy chọn) — Tự chạy kiểm sau mỗi lần dựng lại có thay đổi đăng nhập:**
  Muse tự gọi MCP kiểm lại khi server dựng lại xong, thay vì chờ chủ máy báo.

Không có quyền nào trong 5 quyền trên cho phép Muse chạm vào bí mật, mật khẩu,
quyền quản trị, hay đẩy main (xem ranh giới ở mục 4).

## 1. Vì sao hiện tại Muse không tự kiểm được

Bằng chứng đã gặp trong các lần kiểm ngày 03–04/11/2026:

1. **Không nhìn thấy đường đăng nhập đã chạy.** Tool MCP `tai_khoan` chỉ trả
   trường theo danh sách trắng (id, nhóm, loại, module, trạng thái, cờ có mật
   khẩu/TOTP/cho phép) — **không có email, không có `dang_nhap_bang` /
   `cach_dang_nhap`**. Hai lần thành công qua MCP (ChatGPT 21:55 03/11, Google
   22:57 03/11) đều không khẳng định được là đi bằng email hay bằng Google.
   Không biết đường nào chạy thì không biết đường nào hỏng.
2. **Không lái được trình duyệt đăng nhập của máy chủ.** Hồ sơ Google + phiên
   đăng nhập nằm trong dịch vụ `may-dang-nhap` trên máy chủ, không nằm trong
   trình duyệt của Muse. MCP chỉ có 6 tool, không có tool lái trình duyệt.
   API lõi `trinh_duyet` cần quyền quản trị mà Muse không giữ.
3. **Không xem được noVNC.** Mở màn hình xem cần vé một lần qua API lõi
   (step-up quản trị) + mật khẩu VNC (chủ máy đặt trong web UI, không trả qua
   API). Muse không có cả hai, và không được xin mật khẩu VNC qua chat.
   Hệ quả: mọi selector thật (nút «Continue with Google», ô email/mật khẩu,
   nút chọn tài khoản, ô Cloudflare…) đều ở trạng thái «chưa xác nhận bằng tay»
   trong các báo cáo NV309 (ChatGPT, Claude, Gemini, Grok).
4. **Không thấy chi tiết lỗi.** MCP chỉ trả trạng thái cuối + mã lỗi
   (`thanh_cong` / `that_bai` / `can_nguoi` + mã). Muse không thấy: đã tới bước
   nào, selector nào đã thử và trượt, trang lúc hỏng có những nút/ô nào,
   tín hiệu thử thách nào đang hiện. Không có 4 thứ đó thì sửa code chỉ là đoán.
5. **Chỉ 2 tài khoản được phép qua MCP** (1 Google gemini-web + 1 ChatGPT
   chatgpt-web, kiểm live 04/11 06:33: kho 38 tài khoản — chatgpt 30, google 7,
   grok 1, claude 0; Grok vẫn tạm dừng + chưa cho phép). Claude chưa có tài
   khoản trong kho, Gemini chưa có tài khoản riêng ở chế độ qua tài khoản
   Google. Không có tài khoản + allowlist thì đường MCP cho trio không chạy được.

## 2. Các quyền xin

### Q-A — Nhìn thấy chế độ đăng nhập và chi tiết lần chạy qua MCP

- **Nội dung xin:** (a) `tai_khoan` trả thêm `dang_nhap_bang` và
  `cach_dang_nhap` cho từng tài khoản; (b) thêm trường hoặc tool đọc nhật ký
  lần đăng nhập gần nhất của một tài khoản: thời gian, đường đã đi (T0/T1/T2
  hoặc tên bước), bước cuối tới được, tín hiệu thử thách gặp (nếu có), mã lỗi
  cuối, phiên có lấy được không (chỉ có/không, **không trả giá trị cookie**).
- **Vì sao cần:** để mỗi lần kiểm xong Muse biết chính xác đường nào đã chạy
  và hỏng ở bước nào, thay vì chỉ biết «thành công/không» chung chung.
- **Không phải bí mật:** chế độ đăng nhập, tên bước, tín hiệu, mã lỗi đều không
  phải bí mật. Không xin giá trị cookie, mật khẩu, TOTP, email.

### Q-B — Xem màn hình đăng nhập ở chế độ chỉ-đọc

- **Nội dung xin:** một trong hai, tùy chủ máy chọn:
  - (i) Khóa API ảnh màn hình (`/v1/man-hinh`) cấp riêng cho Muse, chỉ đọc,
    chỉ trỏ vào dịch vụ đăng nhập; hoặc
  - (ii) Vé xem noVNC chỉ-đọc (xem được, không bấm/gõ được), cấp theo phiên,
    có hạn, ghi log mỗi lần xem.
- **Vì sao cần:** để Muse tự đối chiếu nút/ô thật trên trang với selector trong
  code (đặc biệt các ô chưa xác nhận bằng tay của NV309), thay vì chờ chủ máy
  mở tay và kể lại. Ảnh màn hình lúc hỏng cũng là bằng chứng bước hỏng.
- **Giới hạn cứng:** chỉ xem, không bấm/gõ/kéo/thả; chỉ dịch vụ đăng nhập, không
  xem màn hình khác; khóa/vé có hạn và thu hồi được; mọi lần xem đều ghi log.
- **Không xin:** mật khẩu VNC, quyền quản trị, vé xem không hạn, quyền điều
  khiển trình duyệt.

### Q-C — Được phép đăng nhập qua MCP cho các tài khoản provider AI

- **Nội dung xin:** phê duyệt trước phần allowlist của trio: khi chủ máy lưu
  xong tài khoản Claude + tài khoản Gemini ở chế độ «dùng hồ sơ Google đã
  đăng nhập» (trỏ vào tài khoản Google đã cấp) và chuyển tài khoản Grok duy
  nhất trong kho về chế độ đó + bỏ tạm dừng, điều phối thêm 3 id vào
  `WEB2API_MCP_DANG_NHAP_CHO_PHEP` + dựng lại — không cần xin lại từng lần.
- **Vì sao cần:** đây chính là điều kiện còn thiếu để Muse tự chạy chuỗi
  Google (đã xong 22:57 03/11) → Gemini → Claude → Grok qua MCP, tuần tự,
  giãn cách, dừng ở `phai_nghi` / `can_nguoi` không gọi dồn, không vượt.
- **Phạm vi:** chỉ 3 tài khoản provider AI đó, chỉ qua cổng MCP (không qua
  đường khác). Tài khoản ChatGPT + Google đã cho phép giữ nguyên.

### Q-D — Đọc log chẩn đoán của dịch vụ đăng nhập

- **Nội dung xin:** đường đọc log chỉ-đọc (API hoặc gói log định kỳ) của dịch
  vụ đăng nhập và lõi phần đăng nhập, với mỗi lần chạy gồm: thời gian, tài
  khoản (id + module + chế độ), các bước đã chạy theo thứ tự, selector đã thử
  ở mỗi bước, URL trang, tín hiệu thử thách gặp, mã lỗi cuối.
- **Vì sao cần:** log là nguồn duy nhất cho biết automation đã thử đúng ô hay
  trượt ô — thiếu nó, mọi sửa code đều là đoán mò sau mỗi lần hỏng.
- **Giới hạn cứng:** log chỉ chứa thông tin chẩn đoán, **không chứa** giá trị
  cookie/phiên, mật khẩu, mã TOTP, mã xác minh, email, nội dung trang có dữ
  liệu riêng. Nếu log gốc có lẫn các giá trị đó thì phải lược trước khi cấp.

### Q-E (tùy chọn) — Tự chạy kiểm sau mỗi lần dựng lại

- **Nội dung xin (chủ máy có thể từ chối mà không ảnh hưởng Q-A..Q-D):**
  sau mỗi lần server dựng lại có thay đổi ở phần đăng nhập, Muse được tự gọi
  MCP kiểm lại các tài khoản AI đã cho phép (tuần tự, giãn cách, dừng ở
  `phai_nghi` / `can_nguoi`), rồi báo kết quả — thay vì chờ chủ máy báo
  «đã dựng xong».
- **Vì sao cần:** để vòng «sửa → gộp → dựng → kiểm» không đứt quãng ở khâu
  chờ người báo, và để lỗi hồi quy (như test grok NV94 trượt theo (c) vì
  fake cũ thiếu kwarg `chu_giu`) bị phát hiện ngay sau dựng lại.

## 3. Làm sao để có đầy đủ thông tin, dữ liệu sửa code phần AI

Đây là gói dữ liệu tối thiểu cho **mỗi lần đăng nhập hỏng** — đủ để sửa code mà
không cần đoán. Mỗi mục ghi rõ lấy từ quyền nào ở mục 2:

| # | Dữ liệu cần | Lấy từ đâu |
|---|---|---|
| D1 | Tài khoản: provider, module, chế độ đăng nhập (`cach_dang_nhap`), cờ có mật khẩu/TOTP (chỉ có/không) | Q-A (tai_khoan mở rộng) |
| D2 | Đường đã đi + bước cuối tới được (mở trang nào → điền ô nào → bấm nút nào → dừng ở đâu) | Q-A (nhật ký lần chạy) + Q-D (log bước) |
| D3 | Selector đã thử ở mỗi bước và kết quả (thấy/không thấy/trượt) | Q-D (log selector) |
| D4 | Ảnh màn hình (hoặc danh sách nút/ô nhìn thấy kèm nhãn) tại điểm hỏng | Q-B (xem chỉ-đọc) |
| D5 | Tín hiệu thử thách đang hiện lúc hỏng (captcha / cloudflare / 2fa / xác minh / chọn tài khoản / đồng ý) | Q-A + Q-D + Q-B |
| D6 | Kết quả cuối: mã (`thanh_cong` / `that_bai` / `can_nguoi` + `ma_loi`), phiên có lấy được không (chỉ có/không) | MCP hiện có + Q-A |
| D7 | Trạng thái cổng: đang giữ captcha của ai (hold), đang trong cổng nghỉ bao lâu (`phai_nghi` + số giây) | MCP hiện có |
| D8 | Phiên bản code đang chạy: commit main + các patch đã gộp (đặc biệt (a)(b)(c) và delta provider) | Điều phối báo khi dựng lại |
| D9 | Hành vi kỳ vọng ở bước đó: bảng đối chiếu NV309 + file/hàm tương đương của chatgpt2api (nếu có) | Báo cáo NV309, repo chatgpt2api (chỉ đọc) |

Quy trình sửa code khi đã đủ dữ liệu (không đổi so với luật hiện tại):

1. Lấy gói D1–D9 của lần hỏng → xác định đúng bước + đúng selector hỏng.
2. Viết test giả có thử thách (challenged fake) tái hiện đúng tín hiệu đó ở cả
   hai điểm kiểm (trước khi điền và sau khi điền), chạy đỏ trước trên code cũ
   — theo skill `provider_login_challenge_signals`.
3. Sửa code trong đúng module provider đó (không chạm provider khác, không
   chạm giao diện tài khoản AI, không port solver captcha, gate `giai_captcha`
   giữ tắt), chạy xanh + tập liên quan không hồi quy.
4. Nộp nhánh `muse/*` + patch + báo cáo (bằng chứng theo từng trường hợp).
5. Sau gộp + dựng lại: Muse tự kiểm lại bằng MCP (+ xem chỉ-đọc nếu được cấp)
   rồi báo kết quả; vòng lặp tiếp tục cho tới khi không còn lệch.

Lưu ý trung thực: quyền xem chỉ-đọc (Q-B) giúp Muse tự kiểm được đa số trường
hợp, nhưng với những ô mơ hồ (hai nút cùng nhãn, popup khó phân biệt) thì xác
nhận bằng tay của chủ máy vẫn là căn cứ cuối cùng — Muse sẽ ghi rõ những ô đó
trong báo cáo thay vì tự chốt.

## 4. Ranh giới an toàn — những thứ KHÔNG xin và KHÔNG làm

Muse **không xin** và **không nhận** nếu được đưa:

- Mật khẩu VNC, mật khẩu quản trị, phiên web quản trị, khóa quản trị.
- Mật khẩu tài khoản, mã TOTP, mã xác minh, giá trị cookie/phiên, email.
- Quyền đẩy main, quyền dựng lại server, quyền sửa allowlist trực tiếp.
- Quyền bấm/gõ/điều khiển trình duyệt đăng nhập (trừ khi chủ máy quyết riêng
  bằng một yêu cầu khác, ngoài tài liệu này).

Muse **không làm** với các quyền được cấp:

- Không dùng quyền xem để đọc màn hình ngoài dịch vụ đăng nhập.
- Không dùng log để truy vết dữ liệu riêng của người khác.
- Không tự ý mở rộng phạm vi (thêm tài khoản, thêm dịch vụ) ngoài 3 tài khoản
  provider AI ở Q-C.
- Không trình bày kết quả kiểm bằng trang khách hay controller giả như bằng
  chứng của selector thật — phân biệt rõ 3 mức: test giả, trang khách, kiểm
  thật (MCP + xem chỉ-đọc).

Mọi quyền đều phải thu hồi được, có hạn, và mọi lần dùng đều ghi log để chủ
máy soát lại được.

## 5. Câu hỏi cần chủ máy quyết

1. Chấp nhận quyền nào trong Q-A..Q-E (có thể chấp nhận một phần)?
2. Q-B chọn dạng nào: (i) khóa ảnh màn hình hay (ii) vé xem noVNC chỉ-đọc?
   Vé/khóa hết hạn sau bao lâu, giới hạn ở dịch vụ đăng nhập thôi hay rộng hơn?
3. Q-C: phê duyệt trước allowlist trio như mục 2, hay vẫn xin từng lần?
4. Q-D: log lấy bằng API trực tiếp hay gói log định kỳ? Lược bí mật bằng cách
   nào trước khi cấp?
5. Q-E: có cho tự chạy kiểm sau dựng lại không, hay vẫn báo tay «đã dựng xong»?

Khi chủ máy trả lời, Muse làm tiếp đúng phần được duyệt, không tự mở rộng.
