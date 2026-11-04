# telegram_user — integration mỏng cho Home Assistant (khung P0)

Cầu nối MỎNG giữa HA và module `telegram-user` trên web2api. Integration này
KHÔNG chứa MTProto, TDLib, NTgCalls, session, OTP/2FA, state machine cuộc gọi
hay hàng đợi — mọi logic đó nằm trong module web2api. Integration chỉ:

- config flow: nhập gốc web2api + khoá khách → kiểm `GET /m/telegram-user/api/health`
- service `telegram_user.send_message` → `POST /m/telegram-user/api/send_message`
- sensor: số tài khoản / số tài khoản online từ `health`
- event: HA nhận event module qua webhook có sẵn của HA (automation dùng
  webhook trigger) hoặc poll `GET /m/telegram-user/api/events?since=`

Đây là KHUNG P0, chưa kiểm thử trên HA thật (cần máy chủ w2a thật đã cài
module + tài khoản phụ). Đặt thành component HACS riêng khi xuất bản, không
nằm trong repo web2api.
