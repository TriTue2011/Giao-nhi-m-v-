# NV287 — R1: nhạc không nhảy bài sau TTS, hạ nhạc nền khi loa nói

**Nền:** TriTue2011/assist-phicom-R1 main 4e2d6be (xác minh bằng `git ls-remote`;
bản làm việc dựng từ tarball main vì `git clone` treo — xem «Cách dựng» cuối báo cáo).
**Nộp:** nhánh `muse/nv287` trên TriTue2011/Giao-nhi-m-v- (xem commit ở cuối báo cáo).
**Chưa thử trên loa.** Mọi kịch bản dưới đây chạy với renderer DLNA giả + RAOP giả;
nghiệm thu trên loa thật là việc của chủ máy (kịch bản đo 5 bước trong
`docs/PHAT-RA-LOA.md`, mục NV287).

## Kết quả tóm tắt

- **Phần C (luôn bật):** trong lúc có lượt giữ nhạc đang mở, renderer về idle được
  ghi `idle_reason=interrupted`, không bao giờ thành `finished` — bộ điều khiển
  danh sách phát đọc `finished` là nhảy bài kế, đúng triệu chứng.
- **Phần A + B (tự chọn, mặc định TẮT):** tin đi AirPlay song song trong khi nhạc
  vẫn ở DLNA + ducking hạ nhạc nền rồi trả đúng mức cũ. Hai cờ mặc định tắt vì
  hai điều chưa đo được trên loa thật (xem `hoi-nv287.md` câu 1–2).
- **Ví dụ báo thức buổi sáng 30 phút** đã thêm vào `docs/PHAT-RA-LOA.md` dưới dạng
  tự động hoá HA (không thêm mã tích hợp mới cho báo thức — `bao_thuc.py` không
  có sẵn kịch bản này, xem dưới).
- **Test mới 8/8 xanh; test liên quan 126 xanh; 7 đỏ còn lại đều có sẵn trên mã
  cũ trong môi trường này** (chặn UDP — xem «Điểm chưa kiểm / giới hạn môi trường»).

## Vì sao nhạc nhảy bài (đo trên mã, không đoán)

Tin báo đi qua `media_player.play_media` với `announce`: `MusicKeeper` tạm dừng
nhạc, tin **thay URI của renderer DLNA**, xong tin thì khôi phục bằng cách đặt
lại URI nhạc cũ + tua về vị trí đã chụp. Nhảy bài xảy ra ở hai chỗ nối nhau:

1. Khi tin kết thúc, renderer về idle. Mã cũ xóa `idle_reason` mỗi lần hỏi lại
   thấy renderer đang phát, nên lúc tin hết nó lại thành `finished` («hết bài»)
   thay vì `interrupted` («bị chen ngang»).
2. Bộ điều khiển danh sách phát (tích hợp nhạc/YouTube của chủ máy, **ngoài repo
   này** — trong repo chỉ có nút bấm `media_next_track` ở `phim.py:156`, không
   có logic tự nhảy bài) đọc `finished`/idle là gọi bài kế. Lúc khôi phục, nếu
   bộ điều khiển đã kịp bật bài kế thì renderer đang `playing` bài khác, và
   `MusicKeeper._restore` thấy «đã có gì đó phát» thì không đụng tới nữa — nhạc
   ở lại bài kế, đúng triệu chứng.
3. Đường AirPlay còn rõ hơn: `_chay_ap` khi phiên kết thúc tự đặt
   `_ly_do = "finished"` kể cả khi phiên đó chỉ là tin báo.

## Đánh giá A / B / C (chọn bằng mã + test, không đoán)

| Phương án | Kết luận |
|---|---|
| **A — TTS qua AirPlay, nhạc ở DLNA** | **Không dùng được với `_phat` hiện tại** (nó gọi `_don_duong("dlna")` trước, `_THU_TU` chỉ thử lần lượt) — nên đã làm **đường tin AirPlay song song riêng**: không dừng DLNA, không đổi `_duong`/`_uri`/`_ly_do`/trạng thái thực thể, watcher chờ chính tác vụ phiên (không đọc trạng thái renderer vì renderer vẫn phát nhạc). Chỉ dùng khi nhạc đang ở DLNA; nhạc ở AirPlay hoặc không có nhạc thì về đường thường. Mở không được thì về đường thường (nhả lượt giữ duck rồi giữ lại kiểu tạm dừng — bắt buộc, vì giữ nguyên lượt duck thì lúc nhả chỉ trả mức mà không phát lại nhạc sau khi tin đã thay URI). |
| **B — ducking bằng âm lượng** | Đường âm lượng đã có sẵn và đã đo: loa dùng APK `AudioManager.setStreamVolume(STREAM_MUSIC)`, thang 0–15 (`const.py` `VOL_MIN/VOL_MAX`); thực thể đọc `volume_level` từ `coordinator.mic_server.am_luong`, `volume_set` dùng đúng đường này; `bao_thuc.py` đã có mẫu lưu/trả mức cũ. Ducking = hạ N nấc trong lúc tin rồi trả đúng mức cũ, kể cả khi tin lỗi (nhả trong `finally`). **B đứng một mình không sửa được nhảy bài** (tin đường thường vẫn thay URI; hạ âm lượng lúc nhạc đã tạm dừng là vô nghĩa) — nên B chỉ chạy khi A bật. |
| **C — sửa gốc, luôn bật** | Trong lúc giữ nhạc, idle = `interrupted` (cả DLNA lẫn AirPlay). Bộ điều khiển tôn trọng `idle_reason` sẽ không nhảy bài; bộ điều khiển nhảy bài trên mọi idle thì vẫn nhảy — đó là việc của bộ điều khiển, ghi ở `hoi-nv287.md` câu 3. C cũng là đường dự phòng cho A. |

**Chế độ song song không bao giờ tạm dừng nhạc:** tắt ducking nghĩa là nhạc phát
tiếp ở mức đầy đủ (`nac=0`), bật ducking thì nhạc nhỏ đi rồi trả mức cũ; chỉ
khi không đọc được mức cũ mới về tạm dừng (an toàn hơn hạ mù rồi không trả
được). Người dùng tự đổi mức giữa chừng thì lúc nhả sẽ ghi đè mức người dùng
chọn — hành vi giống `bao_thuc.py`, ghi chú ở đây để khỏi bất ngờ.

**Cảnh báo chưa đo (ghi trong code, docs và hỏi):** âm lượng `STREAM_MUSIC` là
toàn cục trên loa; nếu bộ nhận RAOP cũng dùng `STREAM_MUSIC` thì hạ nhạc cũng
hạ luôn tin → ducking vô nghĩa. Và Android trên loa có trộn được DLNA + RAOP
cùng lúc hay không là chưa đo — cả hai đều là phép đo của chủ máy.

## Thay đổi theo file

- `custom_components/r1_speaker/giu_nhac.py` — `MusicKeeper.hold(duck=, nac=)`:
  chế độ duck (chụp nhưng không tạm dừng, hạ N nấc thang 0–15, không đọc/đặt
  được mức thì về tạm dừng cũ); `_release` ở chế độ duck chỉ trả mức, không phát
  lại nhạc; `_chup()` tách từ `_snapshot_and_pause` cũ (hành vi tạm dừng giữ nguyên).
- `custom_components/r1_speaker/media_player.py` — `_ap_dung` (idle trong lúc giữ
  nhạc → `interrupted`), `_chay_ap` (phiên AirPlay là tin trong lúc giữ nhạc →
  `interrupted`), nhánh announce trong `async_play_media` (song song → watcher
  riêng; mở hỏng → về đường thường), `_tin_co_the_song_song`,
  `_bat_dau_tin_song_song`, `_mo_tin_airplay`, `_theo_doi_tin_song_song`,
  `_dung_tin_song_song` (nối vào `_dung_airplay`, `_huy_airplay`,
  `async_media_stop` — Stop/đổi đường/gỡ thực thể đều dừng cả phiên tin song
  song, không để hai phiên RAOP cùng nói với loa).
- `custom_components/r1_speaker/const.py` + `settings.py` — 3 tuỳ chọn mới:
  `tts_song_song_airplay` (bool, mặc định False), `ha_nhac_xuong` (bool, mặc
  định False), `ha_nhac_nac` (int 1–14, mặc định 5, giá trị lạ về mặc định).
- `custom_components/r1_speaker/config_flow.py` — 3 trường vào form chính, ghi
  vào `_co_ban` và `_GOC` để không bị rớt khi lưu (lỗi này đã kiểm bằng test
  tuỳ chọn).
- `custom_components/r1_speaker/strings.json`,
  `translations/vi.json`, `translations/en.json` — mô tả 3 khoá mới, nêu rõ
  mặc định tắt + chưa đo trộn luồng.
- `docs/PHAT-RA-LOA.md` — mục NV287: nguyên nhân, bảng A/B/C, kịch bản đo 5 bước,
  ví dụ automation báo thức buổi sáng 30 phút (nhạc 30 phút, mỗi 10 phút đọc
  thời gian còn lại, hết 30 phút dừng nhạc).
- `tests/test_nv287_giu_nhac.py` (mới) — 8 test, hai tầng (xem dưới).
- `tests/test_tuy_chon.py` — **1 test cũ viết lại theo luật mới** (không nới
  kiểm): `test_form_co_du_truong` nay ghim thêm 3 trường mới và mặc định của
  chúng (False/False/5). Không sửa test nào khác.
- **Không sửa `assist_satellite.py`** (chỉ đọc), không đụng APK, không thêm danh
  sách, không đổi `bao_thuc.py` (ví dụ báo thức là automation, không phải mã mới).

## `bao_thuc.py` có làm được kịch bản báo thức không? — Không

Báo thức kiểu `tts` của nó lặp lại **một lời nhắn cố định** mỗi `lap_s` giây
(mặc định 30) cho tới khi bị tắt/hết `toi_da_s` (mặc định 300); `hen_gio_tat_nhac`
thì nhỏ dần rồi **dừng** nhạc và trả mức cũ. Không có «nhạc nền 30 phút xen
thông báo thời gian còn lại rồi phát tiếp». Vì vậy ví dụ trong docs là automation
HA dùng dịch vụ sẵn có — đúng ranh giới brief (không thêm mã tích hợp mới cho
báo thức).

## Test

Môi trường chạy: Python 3.13.5 độc lập (astral build-standalone), venv
`~/workspace/nv287/venv13/`, Home Assistant 2026.2.3 + `requirements-test.txt`
(đã phải cài HA `--no-deps` rồi cài từng dependency từ METADATA vì pip
backtrack vô tận qua nhánh bluetooth; xem «Cách dựng»).

- **Test mới** `tests/test_nv287_giu_nhac.py`: **8/8 xanh**.
  - Tầng giữ nhạc (FakeDmrPlayer + âm lượng giả): duck không tạm dừng và trả
    đúng mức cũ; duck lồng nhau chỉ hạ một lần, chỉ trả khi bên cuối nhả; lỗi
    giữa chừng vẫn trả mức; không đọc được mức thì về tạm dừng như cũ; không
    duck thì giữ nguyên hành vi cũ.
  - Tầng thực thể (DLNA giả + RAOP giả): tin báo không phát sinh `finished`,
    nhạc về đúng URI + có Seek; tin song song: bắt tay RAOP (RECORD) xong, URI
    DLNA không đổi suốt lúc tin, watcher báo xong, cuối cùng nhạc vẫn phát đúng
    bài; nhạc ở AirPlay thì về đường thường (`[MUSIC, TTS, MUSIC]`).
  - **Đỏ-trước-xanh:** chạy cùng file test trên mã cũ (worktree ở commit base):
    **7/8 đỏ**; 1 test còn lại (`...khi_nhac_o_airplay_thi_ve_duong_thuong`) là
    guard hành vi cũ nên xanh cả trước lẫn sau — đúng kỳ vọng, không phải test
    hỏng.
- **Test liên quan:** `test_dam_thoai`, `test_airplay_song_song`, `test_dlna`,
  `test_dmr`, `test_am_luong`, `test_bao_thuc`, `test_tuy_chon`,
  `test_nv287_giu_nhac`: **126 xanh, 7 đỏ — cả 7 đỏ đều có sẵn trên mã cũ**
  (đã chạy đối chứng trên worktree base: 7 đỏ y hệt, `test_form_co_du_truong`
  xanh trên mã cũ). 7 đỏ đó gồm 6 test AirPlay assert `raop.audio` và 1 test
  SSDP (`test_tim_mo_ta...`) — xem «Điểm chưa kiểm».
- **Cả bộ** `python -m pytest tests -q -p no:sugar`: **715 xanh, 15 đỏ,
  11 skipped (287 giây)** — cả 15 đỏ đều có sẵn trên mã cũ, đã đối chứng trên
  worktree base: 14 đỏ do UDP bị chặn (7 test AirPlay trực tiếp + 6 test
  AirPlay song song + 1 test SSDP) và 1 đỏ test script đèn
  (`test_r1den_chay_that::test_so_choi_ngoai_khoang_bi_kep[9-15]`, lỗi
  subprocess/timeout trong môi trường này, module đèn không nằm trong patch).
  **Không có đỏ mới do patch.**
- **Bandit** `bandit -r custom_components/r1_speaker -lll`: exit 0; danh sách
  vị trí issue không chứa file nào NV287 sửa (giu_nhac, media_player, const,
  settings, config_flow hunk mới, translations, docs) — các issue còn lại là
  code cũ của component, không đụng tới.
- `git diff --check` sạch; quét bí mật trong diff sạch (chỉ có miền ví dụ
  `*.example` và 127.0.0.1, không token/mật khẩu/cookie/email/IP thật).

## Điểm chưa kiểm / giới hạn môi trường (nói thẳng)

1. **Chưa thử trên loa.** Trộn DLNA+RAOP và luồng âm lượng RAOP chưa đo (câu
   1–2 trong `hoi-nv287.md`).
2. **Sandbox này chặn UDP send** (`PermissionError: Operation not permitted` khi
   `sendto`, đã kiểm trực tiếp bằng script UDP loopback — cùng chữ ký với chặn
   ghi file Python từng gặp): gói RTP từ bộ gửi không bao giờ tới được loa giả
   nên mọi assert `raop.audio` đều đỏ ở đây, kể cả trên mã cũ. Test song song
   của NV287 vì vậy chứng minh bằng bắt tay RTSP + URI DLNA không đổi + watcher
   hoàn tất, không dựa vào gói UDP. Trên máy không bị chặn, các test cũ đó phải
   chạy lại — chủ máy chạy cả bộ trên máy thật sẽ thấy rõ.
3. **SSDP cũng dùng UDP** nên `test_tim_mo_ta_tra_dung_dia_chi_cua_chinh_loa`
   đỏ ở đây vì cùng lý do, cũng có sẵn trên mã cũ.
4. Trong môi trường test này `mic_server` không nối nên `volume_level` là None:
   chế độ song song ở tầng thực thể rơi về tạm dừng (đúng fallback thiết kế);
   trên loa thật mic_server nối nên volume đọc được và nhạc không tạm dừng.
   Tầng giữ nhạc (âm lượng giả) đã kiểm đủ cơ chế duck.
5. Chưa chụp ảnh 390 px / máy tính (brief NV287 không yêu cầu ảnh như NV280/
   NV282; không bịa ảnh).

## Cách dựng (để tiếp tục / kiểm lại)

- `git clone` R1 treo (repo lớn) → tải tarball
  `https://codeload.github.com/TriTue2011/assist-phicom-R1/tar.gz/refs/heads/main`
  (36.110.868 byte) về `~/workspace/nv287/r1.tar.gz`, giải nén thành
  `~/workspace/nv287/repo/`, `git init -b nv287-lam-viec`, commit base
  `a7234f1` («base: assist-phicom-R1 main (brief 4e2d6be)» — commit git-init cục
  bộ, upstream thật là 4e2d6be đã xác minh bằng ls-remote). Patch cuối diff từ
  commit base này.
- Python 3.13.5 từ astral-sh/python-build-standalone tag 20250723
  (`~/workspace/nv287/python/`), venv `~/workspace/nv287/venv13/`. Venv cũ bằng
  Python 3.12 (`~/workspace/nv287/venv/`) cài lỗi, bỏ qua.
- HA 2026.2.3: wheel tải bằng curl có resume (pip tải trực tiếp đứt giữa chừng),
  cài `--no-deps`, rồi cài từng dependency từ METADATA của wheel (bỏ
  `home-assistant-bluetooth` — nhánh bluetooth làm pip backtrack tới bản sdist
  không build được); `CC=gcc CXX=g++` vì Python standalone mặc định tìm clang;
  `pytest-homeassistant-custom-component==0.13.316` cài `--no-deps` +
  `pytest-asyncio==1.3.0`, `syrupy==4.8.1`, `freezegun`, `pytest-socket`,
  `numpy` bổ sung tay (không nằm trong requirements-test.txt nhưng test cần).
