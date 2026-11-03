# Spec Kit — scaffold init cho web2api (chưa pilot, chưa constitution thật)

## KẾT QUẢ

Scaffold Spec Kit đã init xong vào web2api, chỉ thêm file mới, không sửa code cũ.
Nộp nhánh Giao `muse/spec-kit-web2api` với `outbox/spec-kit-web2api.patch`
(30 file mới, 5206 dòng thêm, 0 dòng bớt) + báo cáo này.
Base web2api main `8ef3ca9` (NV277+NV289). Chưa chạy tính năng pilot nào,
constitution vẫn là dạng scaffold mà init tạo ra — viết constitution thật
và chạy pilot là bước sau, cần chủ máy duyệt nguyên tắc trước.

## Lệnh init đã dùng

```
specify init . --here --force --non-interactive --integration muse --ignore-agent-tools
```

- Tool: uv 0.13.7, specify-cli 1.2.6, Python 3.12.3 (đủ yêu cầu 3.11+).
- Cờ `--ignore-agent-tools` là BẮT BUỘC trên máy này vì không có binary `muse`
  trên PATH (init thuần `--integration muse` sẽ lỗi «muse not found»).
  Trên máy nào đã cài Muse Code CLI thì init thuần chạy được; phần workflow
  dispatch dùng `muse exec` chưa thử được trên máy này.
- Cờ `--here --force` là cờ đúng cho repo đã có sẵn (theo `specify init --help`);
  init không tự `git init` thêm gì và không sửa file có sẵn.

## Patch chứa gì (chỉ file scaffold mới)

- `.agents/skills/` — đủ 10 skill: speckit-constitution, speckit-specify,
  speckit-plan, speckit-tasks, speckit-implement, speckit-converge,
  speckit-clarify, speckit-analyze, speckit-checklist, speckit-taskstoissues.
- `.specify/` — scripts/bash (check-prerequisites, common, create-new-feature,
  resolve-template, setup-plan, setup-tasks), templates (constitution, spec,
  plan, tasks, checklist), memory/constitution.md (dạng scaffold),
  init-options.json (ghi `integration: muse`, `speckit_version: 1.2.6`,
  `feature_numbering: sequential`), integration.json, integrations
  (muse.manifest.json, speckit.manifest.json), workflows/speckit/workflow.yml,
  workflow-registry.json, .gitignore. 0 symlink.

## Kiểm chứng

- `git status` sau init chỉ có `?? .agents/` và `?? .specify/` — không có
  file cũ nào bị sửa (không README, manifest, test hay cấu hình nào đổi).
- Đối chiếu danh sách file với project test `~/workspace/spec-kit-thu/`:
  chỉ khác đúng 1 file — project test có thêm `.specify/feature.json`
  (sinh ra khi chạy tính năng demo), scaffold web2api KHÔNG có file đó
  là đúng vì chưa chạy tính năng nào.
- Constitution để nguyên dạng scaffold của init (tiêu đề `[PROJECT_NAME]`,
  các nguyên tắc còn là placeholder) — KHÔNG tự bịa nguyên tắc cho repo.
- Không có khoá/mật khẩu/token/cookie/email thật/IP thật trong patch
  hay báo cáo này.

## Chưa làm / bước tiếp theo cần chủ máy

1. Soát và gộp patch scaffold này (thứ tự gộp do điều phối quyết; patch
   độc lập, không phụ thuộc NV300 bổ sung hay NV292 đang chạy).
2. Viết constitution thật cho web2api — cần chủ máy duyệt nguyên tắc trước,
   vì mọi spec/plan sau đều bị constitution chi phối.
3. Chọn 1 tính năng mới nhỏ, tự chứa để pilot (không retrofit toàn bộ
   repo cũ ngay), rồi chạy constitution → specify → plan → tasks →
   implement → converge trên clone của repo.
4. Chốt cách chạy cho hợp nếp hiện tại: Spec Kit muốn review từng phase,
   trong khi nếp hiện tại là chỉ báo kết quả và việc dài chạy ở subagent —
   điểm dừng nhẹ nhất là review spec.md trước khi implement, hoặc chấp
   nhận chạy một mạch và chỉ báo cáo cuối.
5. Lưu ý kỹ thuật: không cài chung integration của agent khác trong cùng
   project (integration `muse` không được khai là an toàn multi-install);
   luồng inbox NV giữ nguyên, artifacts Spec Kit chỉ bổ sung, không thay
   brief NV.
