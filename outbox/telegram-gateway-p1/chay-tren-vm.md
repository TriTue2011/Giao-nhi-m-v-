# Chạy gateway Telegram bằng Docker trên VM này — KẾT LUẬN: KHÔNG CHẠY ĐƯỢC CONTAINER

Ngày: 2026-11-04. Mục tiêu: cài lại Docker trên VM, build + chạy gateway
Telegram (`~/workspace/telegram-docker/`) bằng Docker để smoke test mức
mock trực tiếp trên máy này, thay vì chờ server của người dùng.

## Kết luận ngắn

- **Daemon Docker CHẠY ĐƯỢC** (bằng `dockerd` trực tiếp).
- **KHÔNG container nào khởi động được trên VM này** — sandbox chặn
  `setns` vào mount namespace, không cứu được bằng `--privileged` hay
  `seccomp=unconfined`.
- **Không pull được image `python:3.12-slim`** (EOF liên tục từ
  registry-1.docker.io) nên build cũng không tới được bước RUN.
- Do đó các bước build image, chạy compose và smoke test
  (`GET /health`, `POST /api/call` → 503, `docker logs`) **KHÔNG làm
  được trên VM này**. Dừng ở điểm chặn này, không lách bằng cách chạy
  gateway ngoài Docker (đó sẽ là test giả, không phải test Docker).
- Bằng chứng thay thế (trung thực, không phải test Docker): gói đã qua
  pytest 15/15 + smoke test boot thật ngoài Docker (`/health` 200,
  `/call` chưa có tài khoản → 503) trong báo cáo `bao-cao.md` của gói.
  Phần chạy container thật phải làm trên server của người dùng (Docker
  thật) hoặc một máy không bị sandbox chặn namespace.

## 1. Đã cài được gì

- **Không cần cài lại.** Ngược với giả định ban đầu (binary mất sau VM
  replacement), máy này vẫn còn nguyên `docker.io` + `docker-compose-v2`
  đúng version cũ: **Docker 29.1.3, Compose 2.40.3**. Không chạy
  `apt-get install` (không cần; apt mirror từng chậm ~61 kB/s nên tránh
  việc không cần thiết). Không thử lại `systemctl start docker`
  (policy-rc.d từng chặn; hướng dockerd trực tiếp đã thành công nên
  không cần đường đó).

## 2. Daemon chạy bằng cách nào

Lệnh chạy được (sau khi thử và loại dần):

```bash
dockerd --bridge=none --iptables=false --ip-masq=false --storage-driver=vfs
```

Từng bước loại trừ (log đầy đủ trong cùng thư mục):

1. `dockerd` mặc định → **thất bại**: không tạo được chain NAT DOCKER
   (`iptables … Permission denied (you must be root)` dù uid=0) —
   sandbox thiếu `CAP_NET_ADMIN` (kiểm `CapEff`: có `CAP_SYS_ADMIN`
   nhưng **không** có `CAP_NET_ADMIN`).
2. `dockerd --iptables=false --ip-masq=false` → **thất bại**: không tạo
   được bridge `docker0` qua netlink (`operation not permitted`).
3. `dockerd --bridge=none --iptables=false --ip-masq=false` →
   **daemon lên, API nghe trên `/var/run/docker.sock`, `docker info`
   báo Server 29.1.3, storage overlayfs**. `docker run --rm hello-world`
   pull được image nhưng phần chạy đã lỗi (xem §3) — lúc đó output bị
   cắt nên chưa thấy lỗi ngay.
4. Storage driver mặc định overlayfs → **build lỗi giải nén layer**
   (`failed to mount … overlay … invalid argument`, do overlay-trong-
   overlay trên filesystem của sandbox). Chuyển sang `--storage-driver=vfs`
   thì daemon vẫn lên bình thường (`docker info` báo `Storage Driver:
   vfs`).

Daemon đã **dừng** sau khi kết luận (giải phóng RAM cho việc khác; RAM
khả dụng lúc làm việc chỉ ~360–420 MB). Khởi động lại bằng lệnh ở trên
khi cần.

## 3. Vì sao không container nào chạy được (điểm chặn quyết định)

Mọi cách chạy đều gãy ở cùng một chỗ (runc create):

```
failed to create task for container: failed to create shim task:
OCI runtime create failed: runc create failed:
unable to start container process: error spawning mount remapping thread:
mount source thread: join container mntns: setns: operation not permitted
```

Đã thử, đều cùng lỗi: `docker run` thường, `--network=host`,
`--network=none`, `--privileged`, `--security-opt seccomp=unconfined`.
Chuỗi `Operating System: … (containerized)`, kernel `7.0.0-39-generic`
cho thấy VM này bản thân nó đã là một container bị hạn chế — lệnh cấm
`setns` nằm ở sandbox ngoài, không flag Docker nào vượt được.

Hệ quả: **cả build cũng không xong** — các bước `RUN` trong Dockerfile
chạy qua đúng đường runc create này nên sẽ gãy y hệt, dù có pull được
base image đi chăng nữa.

## 4. Không pull được base image (điểm chặn thứ hai)

`python:3.12-slim` pull thất bại 4 lần liên tiếp (2 lần qua build, 2 lần
`docker pull` trực tiếp, có nghỉ giữa các lần):

```
Head "https://registry-1.docker.io/v2/library/python/manifests/3.12-slim":
unable to decode token response: unexpected EOF
Get "https://registry-1.docker.io/v2/library/python/manifests/sha256:b18b…":
unexpected EOF
```

Trong khi `auth.docker.io` trả HTTP 200 qua curl và `hello-world` từng
pull được một lần — tức egress tới registry chập chờn/không ổn định
trong sandbox này, không phải do auth. Dù điểm này có tự khỏi thì điểm
chặn §3 vẫn đứng đó.

## 5. Những gì đã chuẩn bị xong (dùng lại được trên máy chạy được)

- `docker-compose.vm.yml` (VM-ONLY, **không dùng cho server thật**):
  override cho compose gốc — `network_mode: host` + `ports: !reset []`
  + `GATEWAY_HOST=127.0.0.1` (app có sẵn biến `GATEWAY_HOST`, mặc định
  `0.0.0.0`, nên đặt biến này vẫn giữ đúng ý định chỉ-bind-loopback
  của compose gốc mà không cần Docker port mapping). Trên server thật:
  dùng thẳng `docker-compose.yml`, **không** dùng file override này.
- Thư mục `data/` đã tạo (volume `./data:/data` của compose).
- File `.env` test đã tạo rồi **xóa** sau khi kết luận (tránh token test
  nằm lại trong thư mục gói; README dặn không copy `.env` từ máy khác).
  Tạo lại khi cần bằng: copy `.env.example` → `.env`, thay
  `GATEWAY_TOKEN` bằng giá trị mới từ `openssl rand -hex 32`,
  `chmod 0600 .env`.
- Image **không** build xong, **không** đẩy đi đâu (`telegram-gateway:local`
  chưa từng tồn tại). Container **không** chạy lần nào nên chưa có
  `docker logs` nào để đọc — và theo đúng thiết kế, log cuộc gọi đến
  cũng chỉ xuất hiện khi đã có client + tài khoản phụ đăng nhập + cuộc
  gọi đến thật, nên smoke test mock cũng không tạo ra log nhận.

## 6. Còn vướng gì / bước tiếp theo

1. **Muốn smoke test Docker thật: làm trên server của người dùng**
   (Docker thật, không sandbox chặn namespace) hoặc một máy Linux
   không bị hạn chế — dùng đúng `docker-compose.yml` của gói, không
   dùng override VM.
2. Trên VM này, mọi việc Docker dừng ở đây. Daemon có thể khởi động
   lại bằng lệnh §2 nhưng container vẫn sẽ gãy ở §3.
3. Gói gateway không có vấn đề gì mới phát hiện trong đợt này — điểm
   chặn nằm ở sandbox của VM, không phải ở Dockerfile/compose/code
   (code đã xanh ở pytest + boot smoke ngoài Docker).
