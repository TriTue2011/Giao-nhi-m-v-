# Hỏi NV281 — các điểm chưa rõ (không chặn triển khai)

1. **Nhánh NV280 không có trên remote.** Tại thời điểm làm NV281, `git ls-remote`
   trên cả `TriTue2011/web2api` và `TriTue2011/Giao-nhi-m-v-` đều không trả về
   `refs/heads/agy/nv280-module-gon` (cũng chưa có `refs/heads/muse/nv281` trước
   khi nộp). Vì vậy không đối chiếu được diff NV280 thật, và không xác định
   được test NV280 gốc nào khác đã «buộc phải bỏ» ngoài test trình duyệt duy
   nhất bị ảnh hưởng trực tiếp bởi thay đổi `noiThemKhoa` (đã viết lại trong
   patch này). Hỏi chủ kho: test NV280 nào khác đã bị bỏ mà NV281 phải viết
   lại? Và neo `#khoa-module-<id>` trong patch này có khớp đúng với neo agy
   đang dùng trong bảng chi tiết không?

2. **Form cấu hình trong bảng chi tiết Module vẫn còn.** NV281 bỏ nút «Thêm
   khoá» và thay bằng liên kết, nhưng form cấu hình chung `K.cauHinh` trong
   bảng chi tiết vẫn hiện cho module đã liên kết (để sửa cấu hình thường và
   khoá đã lưu). Nếu chủ kho muốn «một nơi duy nhất» tuyệt đối — kể cả sửa
   khoá của module đã liên kết cũng chỉ ở Bảo mật — thì cần quyết riêng, vì
   form đó dùng chung cả ở trang AI → Tài khoản; tách nó khỏi bảng chi tiết
   sẽ chạm phần NV280 nên không làm trong NV281.

3. **Module từ xa.** Module `tu_xa` không vào danh sách «Khoá của module» và
   `DELETE /api/modules/{id}/khoa` trả 400 `module_tu_xa`, vì khoá của chúng
   không nằm trong kho bí mật cục bộ. Nếu chủ kho muốn quản lý khoá module từ
   xa ở đây nữa, cần chỉ rõ khoá đó lưu ở đâu.

4. **Mã trả khi khoá sai.** Brief nghiệm thu ghi «không khoá quản trị → 401»;
   đo thực tế: không khoá → 401, khoá sai hoàn toàn → 401 `invalid_api_key`,
   khoá khách hợp lệ nhưng không phải quản trị → 403. Patch giữ nguyên hành vi
   lõi này (không đổi mã chỉ để khớp chữ trong brief). Chủ kho xác nhận giữ
   nguyên là được.
