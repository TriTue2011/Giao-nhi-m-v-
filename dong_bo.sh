#!/usr/bin/env bash
# Đồng bộ thư mục này với nhánh `main` của repo GitHub riêng TriTue2011/Giao-nhi-m-v- — chạy bằng cron mỗi 5 phút.
#
# VÌ SAO: Muse không còn vào máy chủ. GitHub là kênh trung gian: việc giao ở inbox/, kết quả của Muse về ở outbox/ (qua Pull Request, xem README).
# Mỗi lượt: (1) kéo nhánh về (rebase, giữ tệp đang sửa dở); (2) nếu có tệp mới/đổi → KIỂM rồi commit và đẩy.
#
# CHỐT AN TOÀN vì kho CÔNG KHAI và việc đẩy là TỰ ĐỘNG:
#   • chỉ đẩy các đuôi tệp trong DANH SÁCH CHO PHÉP (văn bản, ảnh, patch, mã tham chiếu); tệp khác bị bỏ lại, ghi vào nhật ký;
#   • mỗi tệp ≤ 20 MB, tổng lượt ≤ 60 MB;
#   • gitleaks quét phần sắp commit: có rò rỉ thì KHÔNG commit, KHÔNG đẩy, ghi nhật ký (gỡ tệp đó ra rồi chạy lại);
#   • chỉ đẩy lên nhánh main CỦA REPO GIAO VIỆC NÀY (repo riêng, không phải kho mã sản phẩm); không --force, không xoá nhánh;
#   • khoá chống chạy chồng; bất cứ bước nào hỏng thì dừng (không đoán).
set -uo pipefail
export PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
cd "$(dirname "$(readlink -f "$0")")" || exit 1
NHAT_KY="$PWD/dong_bo.log"
GITLEAKS=/opt/claude-c2a/web2api-trien-khai/gitleaks/moi/gitleaks
NHANH=giao-viec     # tên nhánh CỤC BỘ (bản clone này còn một nhánh main cũ nên không đặt trùng)
TU_XA=main          # nhánh trên repo giao việc
ghi() { echo "$(date '+%d/%m %H:%M:%S') $*" >>"$NHAT_KY"; }

exec 9>"$PWD/.khoa-dong-bo"
flock -n 9 || exit 0

[ "$(git symbolic-ref --short HEAD 2>/dev/null)" = "$NHANH" ] || { ghi "KHÔNG ở nhánh $NHANH — dừng"; exit 1; }

# 1) kéo về (nhánh có thể chưa có trên GitHub ở lượt đầu)
if timeout 120 git ls-remote --exit-code --heads origin "$TU_XA" >/dev/null 2>&1; then
    timeout 120 git pull --rebase --autostash --quiet origin "$TU_XA" 2>>"$NHAT_KY" || { ghi "pull --rebase hỏng — dừng (kiểm tay)"; exit 1; }
fi

# 2) tệp mới/đổi (chưa theo dõi + đã đổi), trừ tệp nội bộ của chính script
CHO_PHEP='\.(md|txt|json|patch|diff|png|webp|jpg|jpeg|html|py|sh|yml|yaml)$'
BO_QUA='^(dong_bo\.log|\.khoa-dong-bo|\.gitignore)$'
mapfile -t TEP < <(git status --porcelain --untracked-files=all | sed -E 's/^.. //; s/^"(.*)"$/\1/' | grep -vE "$BO_QUA")
[ "${#TEP[@]}" -gt 0 ] || exit 0

HOP_LE=(); TONG=0
for f in "${TEP[@]}"; do
    [ -e "$f" ] || { HOP_LE+=("$f"); continue; }                  # tệp bị xoá: cứ ghi nhận việc xoá
    if ! printf '%s' "$f" | grep -qiE "$CHO_PHEP"; then ghi "BỎ QUA (đuôi tệp không cho phép): $f"; continue; fi
    kich=$(stat -c %s "$f"); if [ "$kich" -gt $((20*1024*1024)) ]; then ghi "BỎ QUA (> 20 MB): $f"; continue; fi
    TONG=$((TONG+kich)); HOP_LE+=("$f")
done
[ "$TONG" -le $((60*1024*1024)) ] || { ghi "tổng lượt > 60 MB — dừng, chia nhỏ"; exit 1; }
[ "${#HOP_LE[@]}" -gt 0 ] || exit 0

git add -A -- "${HOP_LE[@]}" || { ghi "git add hỏng"; exit 1; }
if ! "$GITLEAKS" protect --staged --no-banner --redact >>"$NHAT_KY" 2>&1; then
    git reset -q; ghi "gitleaks báo rò rỉ — KHÔNG commit. Gỡ tệp chứa bí mật rồi chạy lại."; exit 1
fi
git diff --cached --quiet && exit 0
git -c user.name=TriTue2011 -c user.email=TriTue2011@users.noreply.github.com commit -q -m "giao-viec: đồng bộ tự động $(date '+%d/%m/%Y %H:%M') (${#HOP_LE[@]} tệp)" || { ghi "commit hỏng"; exit 1; }
timeout 180 git push -q origin "HEAD:$TU_XA" 2>>"$NHAT_KY" && ghi "đã đẩy ${#HOP_LE[@]} tệp" || { ghi "push hỏng (không --force)"; exit 1; }
