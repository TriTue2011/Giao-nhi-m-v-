# Câu hỏi cho chủ máy — train giọng gần giống giọng B

Dữ liệu đã xong (501 câu giọng B, 34 phút, xem train-voice-b-bao-cao.md).
Model chưa train được trên máy này. Cần chủ máy quyết 4 việc sau trước khi
train tiếp:

1. **Train ở đâu?** Máy này không có GPU, 4 CPU, RAM 7,7 GB (dưới mức tối
   thiểu 12 GB của Piper), train CPU tính bằng ngày. Chủ máy có máy GPU nào
   (máy chủ nhà, Colab, thuê GPU) để chạy `train-gpu.sh` không, hay muốn dừng
   ở mức dữ liệu?
2. **Fine-tune hay train từ đầu?** Với chỉ 34 phút dữ liệu, fine-tune từ một
   checkpoint tiếng Việt có sẵn thực tế hơn train từ đầu. Chủ máy có checkpoint
   nào muốn dùng không, hay để người làm tự chọn checkpoint tiếng Việt công
   khai phù hợp?
3. **Có gom thêm dữ liệu không?** 34 phút là mỏng cho VITS từ đầu. Có muốn gom
   thêm giọng B lên khoảng 1–2 giờ trước khi train để chất lượng khá hơn không?
4. **Module TTS cho web2api làm trước hay sau?** web2api hiện chưa có module
   TTS nào, nên kể cả khi có model ONNX cũng chưa có chỗ chạy trong web2api.
   Chủ máy muốn làm module TTS trước, train model trước, hay làm song song?

Chưa có model ONNX, chưa có mẫu sau train, chưa kiểm gì trên web2api — các
mục trên cần trả lời trước khi nói tới chuyện gắn giọng vào web2api.
