# KẾT QUẢ — Scaffold Spec Kit cho repo loa R1 (chỉ init, chưa pilot)

## Kết quả

- **Nộp:** nhánh Giao `muse/spec-kit-r1` (kiểm bằng `ls-remote` sau khi đẩy — xem cuối báo cáo), gồm `outbox/spec-kit-r1.patch` + `outbox/spec-kit-r1-bao-cao.md`.
- **Patch:** 30 file mới, 5206 dòng thêm, 0 dòng bớt. Chỉ chứa file scaffold mới (`.specify/` và `.agents/skills/speckit-*/`), **không sửa bất kỳ file nguồn có sẵn nào** (không README, manifest, test hay cấu hình).
- **Nền:** repo loa TriTue2011/assist-phicom-R1, main `2e0c913` (v0.12.0), clone mới tại `~/workspace/spec-kit-r1/repo`.
- **Không đẩy trực tiếp lên repo loa, không đụng main Giao, không force-push.** Đây là bản nộp qua outbox để điều phối soát/gộp.

## Lệnh init đã dùng

Đọc `specify init --help` trước, rồi chạy trong thư mục repo (luồng project hiện hữu):

```
specify init . --here --force --non-interactive --integration muse --ignore-agent-tools
```

- Tool đã kiểm: uv 0.13.7, specify-cli 1.2.6, Python 3.12.3 (đủ yêu cầu 3.11+).
- `--ignore-agent-tools` là **bắt buộc trên máy này** vì không có binary `muse` trên PATH (đã kiểm `which muse`, không có) — init thuần `--integration muse` sẽ lỗi «muse not found» và đòi cài Muse Code từ dev.meta.ai, đúng như đã gặp ở project test. Trên máy nào đã cài Muse Code CLI thì init thuần chạy được; workflow dispatch dùng `muse exec` chưa thử được ở đây.
- `--here --force` vì thư mục repo không rỗng; `--non-interactive` để khỏi treo prompt.

## Kiểm chứng scaffold

- `git status` sau init chỉ hiện đúng hai dòng: `?? .agents/` và `?? .specify/` — không file cũ nào bị sửa.
- Đủ 10 skill tại `.agents/skills/`: speckit-constitution, speckit-specify, speckit-plan, speckit-tasks, speckit-implement, speckit-converge, speckit-clarify, speckit-analyze, speckit-checklist, speckit-taskstoissues.
- `.specify/` đủ 20 file: `init-options.json` ghi đúng `integration: muse`, `speckit_version: 1.2.6`, `feature_numbering: sequential`; scripts bash 6 file; templates 5 file; `memory/constitution.md`; `workflows/speckit/workflow.yml`; 0 symlink.
- Đối chiếu với project test `~/workspace/spec-kit-thu/`: scaffold R1 chỉ khác ở (1) project test có thêm `.specify/feature.json` (sinh ra khi chạy tính năng demo — R1 chưa chạy tính năng nào nên đúng là chưa có), (2) `init-options.json` khác đúng một dòng `here: false → true`, (3) timestamp `installed_at` trong manifest, (4) constitution của project test đã được viết thật trong lượt demo còn constitution R1 vẫn là scaffold (xem dưới).
- Quét patch: không có khoá/mật khẩu/token/cookie/email thật/IP thật (các lần xuất hiện chữ «token»/«secret» trong patch chỉ là chữ trong văn bản mẫu của skill, ví dụ «token-efficient», không phải giá trị thật).

## Constitution vẫn là scaffold — cố tình

`.specify/memory/constitution.md` giữ nguyên dạng init tạo ra, đầu file vẫn là `# [PROJECT_NAME] Constitution` với các placeholder `[PRINCIPLE_N_NAME]`. **Không tự bịa nguyên tắc thật trong lượt này** vì nguyên tắc của repo cần chủ máy duyệt trước — đó là bước sau.

## Chưa làm (trong phạm vi lượt này)

- Không chạy tính năng pilot nào (không có `specs/`, không có `feature.json`).
- Không viết constitution thật.
- Không sửa code, không chạy test của repo (patch không đụng code nên không cần chạy lại suite R1).
- Không thử trên loa/HA thật (không liên quan — lượt này chỉ thêm scaffold).

## Việc tiếp theo thuộc về điều phối / chủ máy

1. Soát và gộp patch scaffold này vào main repo loa.
2. Duyệt nguyên tắc rồi viết constitution thật cho repo loa (bước `/speckit-constitution`).
3. Chọn 1 tính năng mới nhỏ, tự chứa để pilot (đừng retrofit toàn bộ repo cũ ngay).
4. Chốt nếp chạy: review `spec.md` trước khi implement (điểm dừng nhẹ nhất) hay chạy một mạch qua subagent rồi chỉ báo cáo cuối — vì Spec Kit muốn review từng phase trong khi nếp hiện tại là chỉ báo kết quả.
5. Luồng inbox NV giữ nguyên — artifacts Spec Kit chỉ bổ sung, không thay brief NV.
6. Lưu ý kỹ thuật: máy nào chạy `specify init` tiếp theo phải có CLI `muse`, nếu không thì luôn kèm `--ignore-agent-tools`; không cài chung integration của agent khác trong cùng project (integration `muse` không được khai là an toàn multi-install).
7. Patch này độc lập với NV292 đang chạy song song (clone riêng, không chạm file của NV292) và với scaffold web2api (nhánh `muse/spec-kit-web2api` riêng).

## Xác minh nộp

- Nhánh Giao `muse/spec-kit-r1` = `77db5e323919652b958e22627abb4f788504e16e` (kiểm bằng `ls-remote`).
- Con trực tiếp của Giao main `8b00fcecb671c62da1fbea7545eba51fc5d1d99e` (main không bị đẩy, không bị đổi).
