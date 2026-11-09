# Zalo — Tổng hợp tất cả trường hợp cuộc gọi có thể xảy ra

Ngày: 2026-11-09. Nguồn: các trường hợp Việt liệt kê và làm rõ trong chat 09/11.
Mục đích: đặc tả đầy đủ để Claude triển khai tiếp (code so sánh + thêm mới).

## Nguyên tắc chung

- Tất cả các trường hợp chạy trên **tài khoản phụ** và qua **client PC** (app 8080).
- **Voice trước, video sau** (video dùng cờ `is_video`, chưa làm).
- Âm thanh chính qua **HA mic/loa**; UI app và thiết bị bất kỳ là các kênh khác.
- Từ chối / kết thúc cuộc gọi chỉ là **báo hiệu thuần túy**, không dính gì đến âm
  thanh; âm thanh chỉ có khi nhấc máy (gọi đi) hoặc khi có người nhấc máy (gọi đến).
- Gọi nhóm và video là **tương lai**, chưa làm.

## A. Gọi đi — từ app Zalo PC

1. Việt ra lệnh (bấm UI / nói với HA / nhắn chat) → gọi 1 contact → Việt đàm
   thoại qua HA mic/loa. (người–người)
2. Việt ra lệnh → gọi 1 contact → Việt đàm thoại qua trình duyệt (UI 8080).
   (người–người)
3. Việt ra lệnh → gọi 1 contact → Việt đàm thoại qua thiết bị bất kỳ do Việt
   chỉ định (điện thoại, máy tính, loa). (người–người)
4. Việt ra lệnh → gọi 1 contact → AI đàm thoại thay Việt. (AI–người)
5. AI tự gọi đi (cảnh báo, nhắc việc, báo cáo) → gọi 1 contact → AI nói thông
   báo. (AI–người, cảnh báo)
6. AI tự gọi đi → gọi cho chính Việt → AI nói. (AI–người, cảnh báo/nhắc)
7. AI cảnh báo sự kiện (người ngã / trộm) bằng TTS → gọi cho Việt → Việt yêu
   cầu nối tới thiết bị phát hiện → nối thẳng tới thiết bị đó (camera /
   cảm biến đã phát hiện sự kiện). Thiết bị cần nối hệ thống tự biết, Việt
   chỉ cần nói «nối tới đó», không cần nêu tên thiết bị. (AI–người, cảnh báo,
   nối thiết bị phát hiện)
8. Gọi nhóm nhiều người cùng lúc — voice. (người–người, tương lai)
9. Gọi đi video. (tương lai)

## B. Gọi đến — tới app Zalo PC

10. Contact gọi đến → chỉ đổ chuông báo, không nhấc máy, không tiếng.
    (cảnh báo thuần túy)
11. Contact gọi đến → Việt nhấc qua HA mic/loa → đàm thoại. (người–người)
12. Contact gọi đến → Việt nhấc qua UI trình duyệt → đàm thoại. (người–người)
13. Contact gọi đến → Việt nhấc qua thiết bị bất kỳ → đàm thoại.
    (người–người)
14. Contact gọi đến → Việt yêu cầu nối thiết bị khi đang đổ chuông (nhắn chat
    / ra lệnh giọng nói / bấm UI) → app nhấc máy + nối âm thanh tới đúng
    thiết bị đó. (người–người, nối thiết bị)
15. Contact gọi đến → AI nhấc máy, đàm thoại với người gọi. (người–AI)
16. Contact gọi đến → AI nhấc máy, ghi nhận / ghi âm, chuyển lại cho Việt.
    (người–AI)
17. Contact gọi đến → quá X giây không nhấc → giao AI nhận thông tin + phản
    hồi người gọi. (người–AI, timeout)
18. Contact gọi đến → quá X giây không nhấc → AI nhận nhưng không trả lời
    được → AI báo người gọi nhắn tin hoặc ghi âm lại (tin nhắn chữ hoặc ghi
    âm giọng nói 114); app nhận tin đó rồi báo cho Việt. (người–AI, timeout,
    fallback)
19. Contact gọi đến → không ai nhấc, không giao AI → cuộc gọi nhỡ, ghi log +
    báo Việt. (cảnh báo)
20. Gọi đến video. (tương lai)
21. Gọi nhóm đến. (tương lai)

## C. Thiết bị / kênh đàm thoại (dùng chung cho cả gọi đi và gọi đến)

- HA mic/loa — đường chính.
- Trình duyệt / UI app 8080.
- Điện thoại, máy tính, loa — thiết bị bất kỳ do Việt chỉ định lúc ra lệnh.
- Thiết bị phát hiện sự kiện (camera / cảm biến) — hệ thống tự xác định từ
  sự kiện, không cần Việt chọn tay (chỉ dùng trong trường hợp 7).

## D. Hành động trong / sau cuộc gọi

- Từ chối cuộc gọi đến: chỉ là báo hiệu, không âm thanh.
- Kết thúc cuộc gọi (từ hai phía): chỉ là báo hiệu, không âm thanh.
- Ghi âm / ghi nhận nội dung khi AI nhận máy (trường hợp 16).
- Người gọi để lại tin nhắn chữ hoặc ghi âm (trường hợp 18).

## E. Tóm tắt theo bản chất

- Người–người: 1, 2, 3, 8, 11, 12, 13, 14.
- Người–AI: 15, 16, 17, 18.
- AI–người: 4, 5, 6, 7.
- Cảnh báo: 5, 6, 7, 10, 19 (chỉ báo hiệu, không âm thanh khi chưa nhấc máy).

## F. Tham số cần chốt

- **X giây** (trường hợp 17, 18): thời gian chờ trước khi giao AI khi Việt
  không nhấc máy. Chưa chốt — đề xuất 20–30 giây.
- **Thiết bị mặc định** khi Việt không chỉ định: HA mic/loa.
- **AI nhấc máy tự động sau timeout** (trường hợp 17, 18): luật đứng, đặt một
  lần, không duyệt từng lần.

## G. Hiện trạng (đối chiếu code app, nhánh muse/zalo-addon-pivot @ c780ae5)

Đã có:
- Gọi đi: signaling 11300/11301 với codec JSON list (commit 2efce18).
- Gọi đến: phát hiện tín hiệu (11302), đổ chuông, webhook `call.incoming` /
  `call.ended`, ghi log cuộc gọi nhỡ, nhấc máy (POST /api/call/answer) và
  từ chối (POST /api/call/reject) ở mức signaling (commit b9fa55d).

Chưa có (cần làm để các trường hợp trên chạy được):
- Media SRTP/ZRTP — chưa nối dây, nên mọi cuộc gọi hiện chỉ có tín hiệu,
  chưa có tiếng. Đây là việc chặn tất cả các trường hợp đàm thoại (1–7,
  11–18).
- Lệnh chọn thiết bị + nối âm thanh tới thiết bị đã chọn (trường hợp 3, 13,
  14) và tới thiết bị phát hiện (trường hợp 7).
- AI nhấc máy có tiếng (TTS giọng B) + logic timeout / chuyển giao
  (trường hợp 15–18).
- Video (trường hợp 9, 20) và gọi nhóm (trường hợp 8, 21).
- Ghi âm giọng nói 114 và STT 13394: chưa test live.
- Bong bóng `sendBubbleMessage` cho cuộc gọi nhỡ: chưa sửa (cần payload sync
  cuộc gọi nhỡ thật).
