# Báo cáo train giọng gần giống giọng B — CHƯA CÓ MODEL, chỉ xong dữ liệu

Ngày: 2026-11-01. Ngôn ngữ báo cáo: tiếng Việt.
Kết luận ngắn nhất: **đã gom đủ dữ liệu giọng B (501 câu, 34 phút), đã chuẩn bị
xong dữ liệu train theo chuẩn Piper, nhưng CHƯA TRAIN ĐƯỢC MODEL trên máy này,
và không giao model ONNX hay mẫu sau train nào — vì giao model bịa hoặc model
train dở vài chục bước sẽ là nói dối về chất lượng.** Phần train cần máy có GPU
(xem script `train-gpu.sh` kèm theo, chưa chạy ở máy này).

## 1. Giọng gốc đã duyệt

- Giọng B: Muse voice Glad Kite, id `avocado_v2:vd3_vd2_r8_rep5k_3492_v068_28k_g5k`,
  tiếng Việt (`language vi`), tốc độ 90, giọng nữ cao, vui, ngọt.
- Mẫu B gốc đã có từ trước: `~/workspace/your_files/giong-nu-mien-nam-ngot-b.mp3`
  (khoảng 11 giây). Người dùng đã được nói rõ từ đầu: giọng B là giọng cloud
  của Muse, không có file model ONNX sẵn; train từ mẫu chỉ **gần giống, không
  y hệt**.
- Mục tiêu cập nhật của người dùng: tăng dữ liệu từ 150–200 câu lên khoảng
  500 câu, vẫn đa dạng, mỗi câu có audio + transcript đúng câu đó.

## 2. Môi trường đã kiểm (số thật, không bịa)

- CPU: 4 nhân, AMD EPYC 9D25. RAM: 7,7 GB tổng, lúc kiểm chỉ còn khoảng
  0,5 GB trống (máy đang dùng 7,2 GB), không có swap.
- GPU: không có (`nvidia-smi` không tồn tại, không có `/dev/nvidia*`).
- Python hệ thống: 3.12.3. Có sẵn: ffmpeg. Không có sẵn: torch, sherpa-onnx,
  piper, piper-train, espeak-ng.
- Ổ đĩa: còn trống 148 GB trên 150 GB — dung lượng không phải vấn đề, CPU/GPU/RAM
  mới là vấn đề.
- Tài liệu Piper nêu: train nên dùng GPU (khuyến nghị Dockerfile NVIDIA
  PyTorch), RAM tối thiểu 12 GB, và train trên CPU thì “mất nhiều ngày, thậm
  chí lâu hơn”. Một báo cáo train VITS/Piper khác: 10.000 bước trên 2 GPU
  A100 mất khoảng 3 giờ cho bộ dữ liệu 24 giờ. Máy này yếu hơn rất nhiều so
  với cả hai mốc đó, lại dưới mức RAM tối thiểu.

## 3. Dữ liệu đã gom — xong 100%

- File câu: `~/workspace/train-voice-b/sentences.txt` — 501 câu, kiểm tra
  không có câu trùng lặp.
- Audio gốc: `~/workspace/train-voice-b/dataset/mp3/b0001.mp3` … `b0501.mp3`,
  tạo bằng `/opt/hatch/bin/tts speak` với đúng voice B, language vi, speed 90.
  Kết quả chạy: ok = 501, lỗi = 0, bỏ qua = 0. Thời gian gom khoảng 13,5 phút.
- Nội dung câu đa dạng: chào hỏi miền Nam, thời tiết, tin tức ngắn, hướng
  dẫn nấu ăn/sinh hoạt, hội thoại hỏi đáp, số/ngày/tháng/tiền (viết bằng chữ,
  ví dụ “mười lăm”, “hai trăm năm mươi nghìn đồng” để transcript khớp với
  cách đọc), tên người/địa danh Việt Nam, câu dài phức tạp, câu cảm thán.
- Chuyển đổi: `~/workspace/train-voice-b/dataset/wav/` — wav 22050 Hz, mono,
  PCM 16-bit, chuyển bằng ffmpeg từ mp3.
- Tổng thời lượng đo bằng ffprobe: **2040,6 giây = 34,01 phút** cho 501 câu
  (trung bình khoảng 4,1 giây/câu).
- Định dạng train: `dataset/metadata.csv` (dạng `ten_file.wav|transcript`),
  `dataset/train.txt` 490 câu, `dataset/val.txt` 11 câu (chia ngẫu nhiên,
  seed 42), `dataset/summary.json`.
- Dung lượng toàn bộ thư mục dataset: 104 MB (mp3 + wav).
- Script gom và chuẩn bị (chạy lại được, gom tiếp được vì bỏ qua file đã có):
  `gen_dataset.py`, `prepare_dataset.py`, `train-gpu.sh` (script cho máy GPU,
  chưa chạy).

## 4. Train — DỪNG CÓ LÝ DO, không có model

- Đã không chạy train full trên máy này, vì:
  1. Không có GPU, chỉ 4 CPU; train VITS/Piper từ đầu trên CPU theo tài liệu
     là chuyện tính bằng ngày, không phải tính bằng giờ trong một phiên nền.
  2. RAM tổng 7,7 GB đã dưới mức tối thiểu 12 GB, lúc kiểm chỉ còn ~0,5 GB
     trống — train torch trên máy này rất dễ hết RAM giữa chừng.
  3. Chưa có torch/espeak-ng/piper-train; cài đặt xong cũng chỉ mới tới
     vạch xuất phát, chưa giải quyết được tốc độ train trên CPU.
  4. Dữ liệu 34 phút là mỏng cho train từ đầu: các bộ VITS tốt thường cần
     hàng giờ dữ liệu. Với 34 phút, hướng thực tế hơn là **fine-tune từ một
     checkpoint tiếng Việt có sẵn** (nếu tìm được checkpoint phù hợp) thay vì
     train từ đầu — việc này vẫn cần GPU và cần chủ máy quyết checkpoint nào.
- Vì vậy: **không có file model ONNX, không có file config model, không có
  mẫu sau train** trong đợt này. Thư mục `mau-sau-train/` để trống có chủ ý;
  không đưa mẫu giọng B gốc vào đó để giả làm mẫu sau train.
- Đây không phải lỗi dữ liệu: dữ liệu đã đủ để đưa sang máy GPU train ngay,
  chỉ thiếu máy train.

## 5. Độ gần giống — chưa đánh giá được, và giới hạn phải nói rõ

- Chưa có model nên chưa đo được độ gần giống với giọng B bằng tai hay bằng
  số. Không được nói model “gần giống B” khi chưa có model.
- Ngay cả khi train xong trên GPU: kết quả cũng chỉ gần giống, không y hệt,
  vì giọng B gốc là giọng cloud, còn model local là VITS/Piper học lại từ
  34 phút mẫu đó; âm sắc, ngữ điệu, cách nhấn miền Nam có thể lệch, nhất là
  với câu dài, tên riêng lạ, và số.
- Chưa kiểm gì trên web2api: **web2api hiện chưa có module TTS nào** (đã kiểm
  danh sách 42 module, không có module giọng nói). Kể cả khi có model ONNX,
  vẫn cần làm module TTS cho web2api trước thì model mới có chỗ chạy; việc đó
  chưa nằm trong đợt này.

## 6. Việc tiếp theo cần quyết (xem file câu hỏi)

1. Train ở đâu: máy chủ có GPU của chủ máy, Colab, hay thuê GPU?
2. Fine-tune từ checkpoint tiếng Việt nào, hay chấp nhận train từ đầu với
   34 phút và chất lượng hạn chế?
3. Có gom thêm dữ liệu giọng B (lên 1–2 giờ) trước khi train không?
4. Làm module TTS cho web2api trước hay sau khi có model?

## 7. File trong đợt này (cục bộ, chưa đẩy hết lên outbox)

- `~/workspace/train-voice-b/sentences.txt` (501 câu)
- `~/workspace/train-voice-b/dataset/mp3/` (501 file), `dataset/wav/` (501 file)
- `~/workspace/train-voice-b/dataset/metadata.csv`, `train.txt`, `val.txt`, `summary.json`
- `~/workspace/train-voice-b/gen_dataset.py`, `prepare_dataset.py`, `train-gpu.sh`
- `~/workspace/train-voice-b/train-voice-b-bao-cao.md` (file này)
- `~/workspace/train-voice-b/hoi-train-voice-b.md`
- Không push, không PR ở bước làm dữ liệu; bước đẩy outbox ở cuối đợt này chỉ
  đẩy báo cáo + câu hỏi (xem phần đẩy outbox trong báo cáo cuối cho chat chính),
  không đẩy dataset 104 MB và không đẩy model (vì không có model).
