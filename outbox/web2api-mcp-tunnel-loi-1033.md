# web2api — MCP không tới được (Cloudflare Tunnel lỗi 1033)

Ngày: 2026-11-09 ~17:03 +07 (10:03 UTC). Người kiểm: Muse.

## Kết quả kiểm

Gọi MCP `https://web2api.home-labs.io.vn/mcp` 2 lần (khóa MCP cũ, còn hiệu lực):

- Lần 1 (không User-Agent trình duyệt): HTTP 403, lỗi Cloudflare 1010 (chặn theo User-Agent).
- Lần 1 + lần 2 (User-Agent trình duyệt): **HTTP 530, lỗi Cloudflare Tunnel 1033** —
  «The host is configured as a Cloudflare Tunnel, but Cloudflare is
  currently unable to reach it.»

Cả 2 lần đều 530/1033, không phải lỗi thoáng qua.

## Kết luận

- Đường hầm Cloudflare về máy chủ web2api đang đứt: Cloudflare không tới
  được origin. Server hoặc dịch vụ `cloudflared` trên server đang tắt /
  không chạy.
- **Không phải lỗi khóa MCP** (khóa vẫn còn, request đã qua được lớp
  Cloudflare tới bước tunnel).
- **Không phải cắt điện** (lịch cắt là thứ Ba 10/11 08:00–17:00, hôm nay
  09/11 chưa tới).

## Ảnh hưởng

- Không kiểm thật đăng nhập AI qua MCP được lúc này (Claude qua Google,
  Grok qua Google / tài khoản riêng).
- Q-B hết hạn **2026-11-10 02:12 UTC** (09:12 +07 ngày 10/11) — nếu tunnel
  chưa lên lại trước đó thì cần gia hạn Q-B trước khi kiểm thật.

## Cần chủ máy

- Kiểm tra server có đang chạy không, `cloudflared` có đang chạy không.
- Báo Muse khi nào MCP thông lại để chạy kiểm thật ngay.
