# Báo cáo: client gọi Zalo (signaling) — outbox

Ngày: 2026-11-05. Nhánh: `muse/zalo-call-client` (từ main Giao
`82d9ff46fc5f61011e70cb37c7fd9a6834d451b1`).

## Code gồm những gì

Cây `outbox/zalo-call-client/` — package Python `zalo_call/`:

| Module | Nội dung |
|---|---|
| `errors.py` | Exception hierarchy (ChecksumError, FrameError, DecryptError, HandshakeError, OpusUnavailable, SrtpUnavailable) |
| `params.py` | Codec int LE / chuỗi tiền tố độ dài / blob; ParamsWriter/Reader |
| `req.py` | Message Req (23B) / Comm (36B) / Ret (27B), checksum `sum XOR 0x6ce7daa0` (Req xác nhận 2 chiều) |
| `xor_params.py` | XOR params 2 chặng (E2E srcId + độ dài message), miễn 0xa1/0xa3, NULL-key pass-through |
| `keyset.py` | KeySet: k1 verbatim, transport key = Base64Decode(k2), xoay khóa cũ, tên key-set auth = `host:port`, XOR key mặc định = k1 (giả thuyết chưa xác minh) |
| `transport.py` | Framing `[u32 L][u8 wire_type][payload]`, plaintext / AES-GCM-256 / ProvV21 ECDH+GCM / fallback CBCXor+MD5, retry khóa cũ |
| `signaling.py` | Opcode 401/402/405/407/408/409/411/413/416/417/425/427/432/440/441 + state machine IDLE → DIALING → RINGING → ACTIVE → ENDED |
| `client.py` | TCP client (+ HTTP CONNECT proxy), sender/reader thread, handshake 0xa1/0xa3, Prov handshake, `make_call(thread_id, tts_text)` |
| `audio.py` | Audio I/O trừu tượng (file/silent/null/TTS), Opus codec thật qua ctypes libopus, SRTP STUB, header gói media ZRTP relay |
| `__main__.py` | CLI `--help` / `--self-check` (offline only, không có chế độ gọi thật) |

Kèm theo: `tests/` (10 file), `Dockerfile` (python:3.12-slim +
ffmpeg + libopus0), `README.md`, `requirements.txt`
(chỉ `cryptography>=42`), `pyproject.toml`.

## Kiểm thử (chỉ offline, không tài khoản thật, không gọi thật)

- **40/40 test xanh** (`pytest -q`): framing, checksum (vector tính
  tay literal), XOR params (vector tính tay + involution), GCM
  round-trip + retry khóa cũ, dựng/parse Req/Comm/Ret, handshake
  plaintext + Prov layout, CBC fallback layout + thứ tự GCM-rồi-CBC,
  client qua socketpair (gửi 401, nhận 407 → 402 → 409, state
  machine + inbound queue), Opus round-trip qua libopus 1.4,
  header gói media (seq quay vòng, timestamp +960).
- `python -m zalo_call --self-check`: PASS (req, GCM, Opus).

## Trạng thái trung thực

Signaling đã đủ theo đặc tả disassembly. Codec Opus là thật.
SRTP là stub có chủ đích (raise `SrtpUnavailable`), không giả vờ
media đã chạy được.

## Còn thiếu cho việc CHẠY thật (chưa làm, không bịa)

1. Giá trị p/q (`CoreUtility.p` / `.q` từ JSON server).
2. Phiên socket mobile (U5) — client hiện nhận host/port từ tầng ngoài.
3. KDF từ shared secret Prov ra khóa GCM (hook inject được, mặc
   định raise `NotImplementedError`).
4. Danh tính 2 trường Prov A/B 32 byte (tham số tường minh).
5. Nội dung message Prov đầu tiên (U4, caller cấp).
6. Cách dựng CBCXor chính xác + byte header đưa vào MD5 (hook
   inject được, mặc định raise).
7. Engine media hoàn chỉnh (SRTP thật, portable x86).
8. Mapping field 401 (thread_id → str2 đầu tiên của 401 mode 1 là
   phỏng đoán có ghi log UNCONFIRMED) và ý nghĩa mode 1/2/3.
9. Kiểm thử thật bằng tài khoản phụ (tuyệt đối không tài khoản chính).

## Workflow image test

`.github/workflows/build-test.yml` đã soạn sẵn: build image
`ghcr.io/tritue2011/zalo-call:test` và `test-${{ github.sha }}`,
platforms linux/amd64,linux/arm64, trigger push main +
workflow_dispatch, context `outbox/zalo-call-client`.

**CHƯA PUSH ĐƯỢC FILE WORKFLOW (lý do kỹ thuật, không phải do
code):** token GitHub hiện có trên máy thiếu scope `workflow`
nên server từ chối tạo/cập nhật file `.github/workflows/*`
(`refusing to allow a Personal Access Token to create or update
workflow ... without workflow scope`). File workflow đã soạn xong
và giữ trong cây làm việc; để hoàn tất chỉ cần push file đó bằng
một token có scope `workflow`, hoặc thêm file qua giao diện web
GitHub với đúng nội dung đã soạn. Phần code + báo cáo đã push
thành công ở commit này.
