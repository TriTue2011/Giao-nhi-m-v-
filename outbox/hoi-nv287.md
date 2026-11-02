# Hỏi NV287 — nhạc nhảy bài sau TTS + hạ nhạc nền khi loa nói

(Nộp kèm `outbox/nv287-bao-cao.md`. Không câu nào chặn việc gộp phần C — phần
sửa «hết bài» giả luôn bật và không cần đo loa thật. Các câu 1–2 quyết định hai
cờ mới có được bật mặc định hay không; câu 3 quyết định phần C có đủ hay không.)

## 1. Loa Android có trộn được DLNA + RAOP cùng lúc hay không? (CHƯA ĐO)

Chế độ tin song song (`tts_song_song_airplay`) dựa trên giả định loa phát được
đồng thời hai nguồn: nhạc qua renderer DLNA của firmware và tin qua bộ nhận
RAOP của APK. Nếu firmware chỉ cho một nguồn ra tiếng thì tin song song sẽ im
hoặc cướp tiếng nhạc — khi đó cờ này phải giữ TẮT và chỉ dùng đường tin thường
+ phần C. **Đo theo kịch bản 5 bước trong `docs/PHAT-RA-LOA.md` (mục NV287)
rồi báo lại: tin có nghe được trong lúc nhạc vẫn phát không?**

## 2. RAOP có dùng luồng âm lượng riêng với STREAM_MUSIC hay không? (CHƯA ĐO)

Ducking hạ âm lượng nhạc bằng `STREAM_MUSIC` (đường APK `setStreamVolume`,
thang 0–15, đã đo qua `number.r1_am_luong`/`bao_thuc.py`). Nếu bộ nhận RAOP
của loa cũng đi `STREAM_MUSIC` thì hạ nhạc cũng hạ luôn tin → ducking vô nghĩa
và phải tắt `ha_nhac_xuong` (giữ A nếu câu 1 đo được). **Đo: bật cả hai cờ,
nghe xem tin có bị nhỏ đi theo nhạc không.**

## 3. Bộ điều khiển danh sách phát của chủ máy có tôn trọng `idle_reason` không?

Phần C sửa «hết bài» giả trong repo này: trong lúc giữ nhạc, renderer về idle
được ghi `interrupted` thay vì `finished`. Nhưng nếu bộ điều khiển danh sách
phát (tích hợp nhạc/YouTube hoặc automation của chủ máy, ngoài repo này — trong
repo chỉ có nút bấm `media_next_track` ở `phim.py`, không có logic tự nhảy
bài) nhảy bài trên **mọi** idle bất kể lý do, hoặc nhảy bài chỉ vì URI đổi,
thì phần C không đủ và phải sửa bên bộ điều khiển đó. **Hỏi chủ máy: bộ điều
khiển đó đọc tín hiệu nào để quyết định «bài kế»?**

## 4. Sau khi đo xong, có bật mặc định hai cờ mới không, và `ha_nhac_nac` bao nhiêu là vừa?

Hiện tại cả hai cờ mặc định TẮT, `ha_nhac_nac` mặc định 5 nấc. Brief có ghi
«~10 dB/nấc» cho lệnh ADB `service call audio` — con số này cần đo lại vì
5 nấc × 10 dB là mức hạ rất lớn; thang APK 0–15 có thể không tuyến tính theo
dB như vậy. **Đề nghị chủ máy nghe thử với 5 nấc rồi chốt: giữ 5, hay giảm
xuống 3, hay tăng lên? Và sau khi đo câu 1–2 xong thì bật mặc định cờ nào?**

## 5. (Dành chỗ — điền sau khi chạy test)

Nếu lúc chạy test liên quan/cả bộ lộ thêm điểm chưa rõ, ghi thêm tại đây
trước khi nộp. Không bịa câu hỏi.
