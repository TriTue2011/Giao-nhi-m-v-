# Hỏi kèm NV288 (không chặn gộp — mọi tính năng đều mặc định TẮT)

1. **Tự phục hồi khi ADB chưa từng nối:** hiện tại, nếu `AdbDevice.duong` chưa từng
   nối (None) thì tự phục hồi bỏ qua, dù cổng 5555 thực ra có thể nối được. Lựa chọn
   này là bảo thủ (tránh chạm vào ADB khi chưa rõ trạng thái). Chủ máy có muốn khi tự
   phục hồi thì HA **thử nối ADB theo yêu cầu** (dùng `con_nghe_mang()` — chỉ bắt tay
   TCP, không nói giao thức ADB) thay vì chỉ dựa vào `duong` đã nối sẵn không? Nếu có,
   lần nộp sau sẽ đổi cổng tự phục hồi thành: thử bắt tay 5555 trước, nối được mới reboot.
2. **Hoãn quá hạn thì bỏ lượt hôm nay:** hiện tại, tới giờ mà loa bận (phiên Assist /
   phát nhạc) thì hoãn tối đa 30 phút; quá hạn mà vẫn bận thì **bỏ lịch hôm đó** chứ
   không reboot vào giữa phiên. Chủ máy có đồng ý với lựa chọn «bỏ» này không, hay muốn
   reboot ngay khi loa vừa rảnh dù đã quá 30 phút?
3. **Ngưỡng:** các ngưỡng hiện tại đều là lựa chọn chưa đo (ghi rõ trong mã + báo cáo):
   get_info im quá 120 giây mới kết luận treo; treo quá 300 giây mới tự phục hồi; sau tự
   phục hồi nghỉ 4 giờ; hoãn tối đa 30 phút; giờ mặc định 03:00. Chủ máy có muốn đổi
   ngưỡng nào không (đặc biệt 120/300 giây và 4 giờ nghỉ)?
