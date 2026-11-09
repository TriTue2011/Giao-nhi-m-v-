# Phicomm R1 — Acoustic Echo Cancellation (AEC) Research

**Date researched:** 2026-11-09. **Device:** Phicomm R1 (斐讯R1), released 2018-03, Rockchip RK3229, 512 MB RAM, 8 GB eMMC, Android 5.1.1 / API 22, ARMv7, 4-mic array, mono speaker path (1.25″ tweeter + 2.75″ woofer, 15 W). Consensus community firmware: **3448**.

## Summary

- **Stock AEC exists, but it is locked inside the stock Unisound (云知声) voice pipeline — it is not exposed to third-party apps.** The hardware can do it (RK3229 + Unisound 4-mic array + AKM AK7755 DSP + a factory `/system/lib/libaec.so`), and the stock assistant can wake / take no-wake commands while music plays, which implies in-pipeline echo handling. No public API, no `AcousticEchoCanceler` evidence, and an ordinary app is SELinux-blocked from the raw audio devices.
- **The only project that has actually tapped the factory AEC is `sewellzhong/phicomm-r1-satellite` (Sept 2026, one device).** It got the factory AEC to produce non-empty output and, in controlled tests, to let a spoken “Alexa” during TTS playback cancel the reply (1–2 events). It has **not** proven echo *elimination* (no ERLE/dB figure), and it has **not** demonstrated echo-free two-way calls.
- **No proven, working solution for echo-free two-way calls on an R1 exists in any source found.** Every other R1 project either avoids the problem (half-duplex: mute the mic while playing) or never attempts AEC. No VoIP APK is known to work on the R1 for this.
- **Recommended path (in order):** (1) a 10-minute on-device probe of `AcousticEchoCanceler.isAvailable()` + `VOICE_COMMUNICATION` — cheap, probably negative; (2) software WebRTC AECM/AEC3 inside your own calling APK, feeding it the exact far-end PCM you play as reference (most promising for *calls*, independent of the factory stack); (3) only if (2) is insufficient, the factory route — privileged proxy calling `libUniMicArray.so` / `libaec.so` via a patched boot, following sewellzhong — the only route that reuses the tuned 4-mic/AEC/DSP chain, but heavy, single-device, and still unproven for calls. In parallel, ship the half-duplex fallback (mute mic while the remote party speaks).

## Findings

### 1. Stock firmware AEC / hardware DSP — can third-party apps use it?

**Hardware — yes, the pieces are there.**
- Teardown: RK3229 + 512 MB RAM, 3× ES7243 ADCs, **AKM AK7755EN DSP** (integrated mono ADC, stereo DAC, mic amp, digital audio interface), TI TPA3118 amp, top 4-mic array, ~10 m far-field pickup claimed. Source: https://www.52audio.com/archives/534.html (verified live, 2026-11-09).
- RK3229 “supports 4–8 mic; in voice algorithms supports source localisation, source enhancement, **echo cancellation**, noise suppression” and 8-channel digital I²S mic input; R1 uses 4 mics. Source: https://post.smzdm.com/p/645292/ (index).
- Voice front-end is **Unisound (云知声) 4-mic array technology**. Source: http://m.ikanchai.com/pcarticle/205603 (index). AK7755EN in general is a programmable DSP codec whose DSP code includes echo cancellation, but no R1-specific AK7755 programming interface was found. Sources: https://fr.ovaga.com/products/detail/ak7755en, https://www.microchip.com/en-us/development-tool/ac327755 (index).

**Stock software — AEC lives inside the proprietary Unisound chain, not in the Android audio framework.**
- The stock voice service is `com.phicomm.speaker.device` (Unisound) + `com.phicomm.speaker.player` (EchoService). Community apps must `pm hide` both to take over the mic. Source: https://github.com/sagan/r1-helper (verified live).
- The most thorough audit, `sewellzhong/phicomm-r1-satellite` (firmware 3448, Sept 2026), extracted the factory system image and confirmed: Audio HAL, `libuni4michal.so`, `libuni4michalchance.so`, **AK7755 data2 firmware**, and DTB nodes for RK3229 I²S0/1/2, ES7243, ES8323, AK7755. It fixed the factory ABI: `Unisound_MicArray_Process(handle, in, in_len, echo_ref, is_waked, out_asr, out_vad, out_len)` — 256 samples/channel, **4-mic interleaved input + 2 interleaved echo-reference channels**, max 256 mono output samples — and a separate **`/system/lib/libaec.so`** with a 300-sample ABI. Factory logs report “MicArray v2.3.0, 4 mic, 2 echo refs, AEC on”. Source: https://github.com/sewellzhong/phicomm-r1-satellite and https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-08-r1-factory-audio-root-plan.md and https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-11-r1-factory-audio-micarray-tap-host.md (verified live).
- **Third-party apps cannot use it as-is.** The same project documents: an ordinary APK can load `Uni4micHalJNI` but its `untrusted_app` SELinux domain is denied search on `/dev/snd` (`audio_device`), `openAudioIn(2)` returns 0; `RECORD_AUDIO` only permits recording via AudioRecord/AudioFlinger, with no direct tinyalsa/mixer/I²C/DSP access. Reuse requires a privileged proxy/daemon, patched boot, and a dedicated SELinux domain. Source: factory-audio-root-plan doc above.
- **No evidence was found that Android's `AcousticEchoCanceler` works on the R1.** Android's API only works if the vendor HAL implements it (gated by `audio_effects.conf`); `isAvailable()` must be probed on-device. Sources: https://developer.android.com/reference/android/media/audiofx/AcousticEchoCanceler, http://gopinaths.gitlab.io/post/acoustic_echo_cancellation_in_android_using_webrtc/ (index). Nobody in the community reports having probed it on the R1.

### 2. Community work: rooting, custom firmware, ROMs, GitHub, forums

**No AOSP/custom ROM exists; all work is modified stock firmware or APKs on stock firmware.** The main hub is Enshan Wireless Forum (恩山无线论坛, right.com.cn); no XDA thread was found.

| Project / thread | What it does | AEC relevance |
|---|---|---|
| Root/Xiaoai flashing tutorial — https://www.cnblogs.com/yanglang/articles/12580726.html | Solder USB to reserved Micro-USB pads on mainboard back, Rockchip loader flash, rooted firmware, Xiaoai; also “no-solder Xiaoxun APK” route | Root method that makes factory-AEC tapping possible; no AEC work itself |
| Enshan Mod firmware 2026-09/10 — https://www.right.com.cn/forum/thread-8491286-1-1.html | 3448-based mod: 3 music sources, Navidrome, Home Assistant, LLM, custom wake word | Uses stock voice pipeline; no AEC work |
| Xiaoai 2.10.24 + original 4 mics — https://www.right.com.cn/forum/thread-7914296-1-1.html (from search) | “Original four microphones awakened” with Xiaoai firmware | Implies stock mic array works under Xiaoai mod; no echo measurement |
| `sagan/r1-helper` (2020, 17★) — https://github.com/sagan/r1-helper | Alexa app (AlexaAndroid + Snowboy), runs on stock firmware; LED needs root | Disables Unisound+player; **no AEC** |
| `Enter-tainer/phicomm-r1-voice-assistant` (2026-07, 5★) — https://github.com/Enter-tainer/phicomm-r1-voice-assistant | R1 as dumb terminal: streams 16 kHz mic to server, plays 48 kHz TTS back; ADB over Wi-Fi :5555, no root/disassembly | **No AEC — documents the echo problem**: VAD false-triggered by beep echo; workaround is mute mic while SPEAKING + wait beep+150 ms before VAD. Also: `STREAM_MUSIC` does not reach the speaker (must use `STREAM_SYSTEM`); AudioFlinger deadlocks if AudioRecord is recreated quickly or the stock service competes for the mic |
| `sewellzhong/phicomm-r1-satellite` (2026-09, 0★, 236 commits) — https://github.com/sewellzhong/phicomm-r1-satellite | Home Assistant ESPHome voice satellite, Chinese | **Only project doing AEC work** — see §1 and §5 |
| `yangyedan/r1-webui` (2026-10, 6★) — https://github.com/yangyedan/r1-webui | Self-hosted AI backend reusing modified stock Xiaoxun APK (3448) + DLNA | Reuses stock pipeline; no AEC work |
| `knoop7/Ava-Pro` + R1 mod v1.3.0 — https://github.com/knoop7/Ava-Pro/blob/HEAD/README.md, https://github.com/knoop7/Ava-Pro/blob/HEAD/wiki/Mod-Store-Catalog.md | HA Android companion, Android 5.0–16; R1 mod needs root + stock `libUni4micHalJNI` for 4-mic DOA LEDs | Claims generically “Acoustic echo cancellation (wake works while music plays)”; **no R1-specific AEC test/measurement published** — treat as unproven marketing claim |
| `kuteo-git/robot-esp32` — https://github.com/kuteo-git/robot-esp32/blob/HEAD/README.md | xiaozhi server; R1 running self-built Android app as client | No AEC discussion found |
| Others: `sidealice/phicomm_r1` https://github.com/sidealice/phicomm_r1; `jojo729/R1_DEVICE` https://github.com/jojo729/R1_DEVICE (stock device app, hooks Unisound API); `IoTDevice/phicomm-r1-controler` via https://www.right.com.cn/forum/thread-4096582-1-1.html (ADB control, 2021); `ring1012/r1-py` / `r1-dummy` (cited by r1-webui as the no-solder APK source) | Research / control / protocol work | No AEC work |

### 3. Via APK: existing Android APKs providing echo cancellation

**No APK is known to work on the R1 (or has been tested on it) for echo-free calls.** Candidates, all untested on R1:

| APK / app | AEC mechanism | R1 fit |
|---|---|---|
| **Linphone** — https://wiki.linphone.org/xwiki/wiki/public/view/Lib/Features/Audio%20tuning/ | Hardware AEC first (sets `MODE_IN_COMMUNICATIONS`); if absent, software Speex AEC, WebRTC AECM (8/16 kHz, ARM NEON, poor double-talk) or WebRTC AEC/AEC3 (≤48 kHz, ≥v5.5). Never stack software on hardware AEC. | **Current builds cannot run on R1**: SDK 5.5 raised minimum to Android 6 / SDK 23 (https://github.com/belledonnecommunications/linphone-sdk/blob/HEAD/CHANGELOG.md). An old 4.5/5.4 APK might install on API 22 — untested, and its AECM is the weakest variant. |
| **Jitsi Meet (Android)** — https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-configuration/, https://deepwiki.com/jitsi/lib-jitsi-meet/3.2-screen-sharing | WebRTC AEC on by default (`disableAEC: false`); `JavaAudioDeviceModule` with `VOICE_COMMUNICATION`/`MIC` | Modern app requires Android ≫5.1; no R1 test. Web only (browser AEC3) is not an R1 APK. |
| **Zadarma** — https://play.google.com/store/apps/details?id=com.zadarma.sip | Play listing (Nov 2025): “Implemented a new echo cancellation algorithm (WebRTC AEC3)” | Modern Android VoIP app; no R1 test, almost certainly too new for API 22. |
| **Ava-Pro** — https://github.com/knoop7/Ava-Pro/blob/HEAD/README.md | Claims on-device AEC, “wake works while music plays”; supports Android 5.0–16, so it *can* install on the R1; R1 mod exists | Closest installable candidate, but the AEC claim is generic to the app, with no published R1 measurement. Worth a trial, not a proven solution. |
| Stock Xiaoai / Xiaoxun mod APKs (Enshan forum) | Presumably use the factory Unisound AEC for wake-word barge-in (they support no-wake playback commands while music plays) | Wake-word barge-in only — not full-duplex call echo cancellation, and no ERLE figure. |
| Any generic VoIP app using `VOICE_COMMUNICATION` | Triggers platform AEC *if* the HAL implements it | On the R1 the HAL is the proprietary Unisound one; whether `AcousticEchoCanceler.isAvailable()` is true is unknown — probe it (see §4). |

### 4. Via code: developer implementation paths

Ranked by promise for the stated goal (echo-free two-way calls on the R1):

**A. Software WebRTC AEC inside your own calling APK — most promising for calls, independent of the factory stack. (Speculative on R1, proven technology elsewhere.)**
- Architecture: your app owns both ends, so it has the exact far-end reference: feed the PCM you are about to play (`bufferFarend`) and the mic PCM (`process`) into the canceller, 10/20 ms frames. This is exactly what WebRTC AECM/AEC3 and Linphone's software AEC do. Sources: https://wiki.linphone.org/xwiki/wiki/public/view/Lib/Features/Audio%20tuning/, https://www.forasoft.com/learn/audio-for-video/articles-audio/aec-on-bluetooth-speakerphone-airpods (index).
- Ready-made building block that fits the R1: `xia-chu/webrtc_apm` — extracted WebRTC APM (AEC/NS/AGC/VAD), **min SDK 21, armeabi-v7a**, `libwebrtc_apm.so`, Java `WebRtcJni.WebRtcAecm(fs, cngMode, echoMode 0–4)`, `bufferFarend()` + `process()`; AECM is **8/16 kHz only, 10/20 ms frames**. Source: https://github.com/xia-chu/webrtc_apm (verified live). Modern alternative: `webrtc-audio-processing` library (standalone APM, AEC3) or Linphone's `mswebrtc` AEC3 — more CPU, better double-talk, up to 48 kHz; needs NDK cross-compile for ARMv7/API 22.
- **Known blockers on the R1:** (i) CPU: quad Cortex-A7 + 512 MB RAM — AEC3 is heavy; AECM is the lighter fit. (ii) Delay alignment is everything — AEC lives or dies on matching reference to echo within ms; R1 playback latency is unknown and `STREAM_MUSIC` doesn't even route to the speaker (use `STREAM_SYSTEM`, per Enter-tainer). (iii) Sample-rate mismatch: mic 16 kHz vs playback 48 kHz — resample the reference to the AEC rate. (iv) AudioFlinger/HAL fragility: recreating AudioRecord quickly deadlocks; the stock Unisound/player service competes for the mic — must `pm hide` it first. (v) Speaker non-linearity/clipping: sewellzhong measured mic input clipping at −32768 during playback and AEC-output saturation; keep playback volume low (1–5% stopped new clipping in their tests) and/or add a limiter. (vi) Only one canceller in the chain — disable any platform AEC if running software AEC, or they fight. (vii) No separate mic channels via standard `AudioRecord` — the 4-mic array is only exposed through the factory HAL (see B).

**B. Factory route — reuse `libUniMicArray.so` + `libaec.so` via a privileged proxy. (Most promising for wake-word barge-in; heaviest; unproven for calls.)**
- Follow sewellzhong's R2 plan: a minimal privileged daemon (patched boot, dedicated SELinux domain, Unix-socket IPC with `SO_PEERCRED`, fixed PCM S16LE 16 kHz mono 20 ms frames to the APK) that dynamically loads the factory libs from the device — do not redistribute the proprietary binaries. It must collect a reference from *every* playback source (TTS, media, Bluetooth, prompts); a source with no reference must be reported as unprotected, not silently claimed clean. Source: https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-08-r1-factory-audio-root-plan.md
- Concrete ABI details already reverse-engineered (saves months): `Unisound_MicArray_Process` 8-param ABI (4-mic + 2-ref, 256 samples/channel); `libaec.so` 300-sample ABI adapter; factory config “dual reference / AEC on”. But alignment is fragile — v158/v159 showed `invalid_or_discontinuous_pcm_frame` / per-block warm-up failures from 300-sample ABI vs continuous-reference mismatch, and the two factory outputs were sample-identical with DOA stuck at 5° in early tests.
- Blockers: needs root/patched boot (brick risk; full eMMC backup/restore R0 still pending even in that project); SELinux `Enforcing` work; R1 must stay on firmware 3448; the AEC's actual echo-reduction quantity is still unmeasured.

**C. Android `AcousticEchoCanceler` / `VOICE_COMMUNICATION` — try first, expect failure. (10-minute probe.)**
- `AcousticEchoCanceler.isAvailable()` + `create(audioSessionId)` + `VOICE_COMMUNICATION` AudioRecord. Source: https://developer.android.com/reference/android/media/audiofx/AcousticEchoCanceler. It only works if the vendor HAL + `audio_effects.conf` implement it (http://gopinaths.gitlab.io/post/acoustic_echo_cancellation_in_android_using_webrtc/). Given the R1's proprietary Unisound HAL bypasses the standard preprocessing path, the expected result is `false`/null — but no one has published the probe, so run it before ruling it out.

**D. PulseAudio `module-echo-cancel` / ALSA — not applicable on stock R1. (Dead end unless the OS is replaced.)**
- PulseAudio's `module-echo-cancel` (`aec_method=webrtc|speex|adrian`) is a sound-server module creating a virtual sink/source pair. Source: https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/. Stock Android 5.1 has no PulseAudio (AudioFlinger/TinyALSA). It only becomes relevant if the R1 is re-flashed to Linux — no community project has done that, and sewellzhong explicitly deprioritised generic Linux in favour of keeping the factory kernel/HAL/DSP. SpeexDSP as a *library* (not via PulseAudio) remains a valid lightweight fallback inside approach A — SEPIA's smart-speaker tests found Speex attenuates robustly where WebRTC AEC fails at low SNR. Source: https://github.com/orgs/SEPIA-Framework/discussions/152 (index).

**E. AK7755 DSP directly — speculative, no path found.**
- The AK7755EN is a programmable DSP codec that in principle can run AEC, but on the R1 it is driven by a proprietary factory `data2` firmware blob loaded through the factory stack; no public API, datasheet programming flow, or community access was found. Do not pursue unless reverse-engineering the factory driver.

**F. Server-side AEC — attractive complement, untested on R1.**
- If the call is relayed through your server, the server knows the exact far-end PCM before the R1 plays it and can run WebRTC APM AEC3 on the R1's uplink (the Enter-tainer architecture already streams raw mic PCM to a server — it just doesn't do AEC). Advantage: no R1 CPU load, exact digital reference. Risk: Wi-Fi/WebSocket jitter + unknown R1 playback latency make delay estimation hard; playback from other on-device sources (DLNA, Bluetooth) bypasses the server entirely.

**Fallback that is proven to work in practice (half-duplex):** mute/ignore the mic while the remote party/TTS is playing, delay VAD start until beep+150 ms after prompts, and keep volume low. This is what Enter-tainer ships; it prevents echo from being sent, at the cost of no simultaneous talking.

### 5. Proven working solution vs unsolved?

**Unsolved for the stated goal. No one has demonstrably achieved echo-free two-way calls on an R1.**

| Claim | Status | Evidence |
|---|---|---|
| Stock assistant wakes / takes commands while music plays (factory AEC in its own pipeline) | **Proven in normal use** (qualitative) | Product behaviour + Xiaoai/Xiaoxun mod communities; no ERLE/dB measurement |
| Factory AEC produces non-empty output during playback | **Proven (single device)** | sewellzhong v164: 553 non-zero AEC frames, RMS ~1358 during HA playback — but peak 32767 saturation; author: “cannot prove output is usable speech” |
| Factory AEC enables playback wake-word + reply cancel | **Partially proven (single device, controlled)** | v171: 2 AEC KWS detections + 2 actual reply cancels during a long TTS answer; v173 (threshold 229): 1 playback wake, 446 AEC KWS frames, max score 246/255, 1 AEC KWS detection, 1 reply cancel, 0 clipping. Source: https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-16-r1-playback-wake-threshold-229.md. Author's own boundary: “controlled single-device diagnosis, not the final acoustic gate; far distance, low volume, directions, continuous pure echo, long false-trigger not covered” |
| Factory AEC *elimination amount* (ERLE), DSP quality, 4-mic independent response, DOA accuracy | **Unproven** | Author states repeatedly: “AEC elimination and DSP quality still not verified”; early outputs sample-identical, DOA fixed 5°; playback clipping at −32768 |
| Any VoIP APK gives echo-free calls on R1 | **No evidence** | No test report found for Linphone/Jitsi/Zadarma/Ava-Pro on R1 |
| Software WebRTC AECM/AEC3 in a custom R1 APK gives echo-free calls | **Untested idea** | Technology is proven on phones; R1 fit (API 22/ARMv7 AECM library exists) is plausible but no R1 run exists |
| Half-duplex (mute mic while playing) avoids sending echo | **Proven workaround** | Enter-tainer project ships it; it is not AEC |

## Recommended path

1. **Probe (hours):** on-device `AcousticEchoCanceler.isAvailable()` + `VOICE_COMMUNICATION` recording while playing a known tone; measure residual echo. Expect negative; if positive, it is the cheapest win.
2. **Build the call APK with in-app WebRTC AECM first** (`xia-chu/webrtc_apm`, 16 kHz, 20 ms frames, echoMode 3–4), feeding it the exact far-end PCM, playing via `STREAM_SYSTEM`, stock Unisound/player hidden, mic muted as fallback during playback, volume capped low. Measure ERLE (echo power before/after) on-device; if AECM is insufficient, try AEC3 / SpeexDSP and/or server-side AEC.
3. **Only then consider the factory route** (sewellzhong's privileged-proxy + patched boot reusing `libaec.so`/`libUniMicArray.so`) — the only way to get the tuned 4-mic beamforming + factory AEC + DSP, and the only route with any playback-barge-in evidence — accepting root/boot risk, 3448 lock-in, and that call-quality AEC is still unproven there.
4. **Do not pursue:** PulseAudio/ALSA on stock Android, direct AK7755 programming, or any current Play-Store VoIP APK as a drop-in solution (API-22 incompatibility + no R1 evidence).

## Could not verify / open questions

- Whether `AcousticEchoCanceler.isAvailable()` returns true on a 3448 R1 (needs a 10-minute on-device probe; no source reports it).
- Any ERLE/dB echo-reduction figure for the factory AEC, or for any software AEC, on the R1 (no source measures it).
- Whether current Ava-Pro's AEC actually functions on the R1 (claim only, no test).
- Whether an old Linphone 4.x/5.4 APK installs and runs its software AEC on API 22 (version archaeology + test needed).
- Exact AudioRecord channel layout / sample rate the stock HAL exposes to third-party apps (mono processed only? — sewellzhong's baseline is mono; 4-channel access is factory-HAL-only).
- AK7755 `data2` firmware contents / whether the DSP does AEC vs only codec/EQ duties (proprietary blob, unaudited publicly).

## Sources

- https://github.com/sewellzhong/phicomm-r1-satellite (verified live 2026-11-09)
- https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-08-r1-factory-audio-root-plan.md (verified live)
- https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-16-r1-playback-wake-threshold-229.md (verified live)
- https://github.com/sewellzhong/phicomm-r1-satellite/blob/main/docs/2026-09-11-r1-factory-audio-micarray-tap-host.md (index)
- https://www.52audio.com/archives/534.html (verified live — teardown: RK3229, ES7243, AK7755EN, 4-mic)
- https://post.smzdm.com/p/645292/ (index — RK3229 AEC capability, 4-mic, 10 m)
- https://post.smzdm.com/p/a260m9pp/ (index — hardware summary, 3448 firmware)
- http://m.ikanchai.com/pcarticle/205603 (index — Unisound 4Mic)
- https://github.com/sagan/r1-helper (verified live)
- https://github.com/Enter-tainer/phicomm-r1-voice-assistant (verified live)
- https://github.com/yangyedan/r1-webui (verified live)
- https://github.com/knoop7/Ava-Pro/blob/HEAD/README.md (verified live)
- https://github.com/knoop7/Ava-Pro/blob/HEAD/wiki/Mod-Store-Catalog.md (index)
- https://github.com/kuteo-git/robot-esp32/blob/HEAD/README.md (index)
- https://www.cnblogs.com/yanglang/articles/12580726.html (index — solder/root/Xiaoai tutorial)
- https://www.right.com.cn/forum/thread-8491286-1-1.html (index — 2026 Mod firmware)
- https://www.right.com.cn/forum/thread-4096582-1-1.html (index — ADB control toolbox)
- https://developer.android.com/reference/android/media/audiofx/AcousticEchoCanceler (index)
- http://gopinaths.gitlab.io/post/acoustic_echo_cancellation_in_android_using_webrtc/ (index)
- https://wiki.linphone.org/xwiki/wiki/public/view/Lib/Features/Audio%20tuning/ (index)
- https://github.com/belledonnecommunications/linphone-sdk/blob/HEAD/CHANGELOG.md (index — min Android 6 in SDK 5.5)
- https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-configuration/ (index)
- https://play.google.com/store/apps/details?id=com.zadarma.sip (index — WebRTC AEC3)
- https://github.com/xia-chu/webrtc_apm (verified live — WebRTC APM, min SDK 21, ARMv7, AECM)
- https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/ (index — module-echo-cancel)
- https://github.com/baresip/baresip/wiki/Acoustic-Echo-Cancellation-(AEC) (index)
- https://github.com/orgs/SEPIA-Framework/discussions/152 (index — PulseAudio AEC on smart speaker, Speex vs WebRTC)
- https://www.forasoft.com/learn/audio-for-video/articles-audio/aec-on-bluetooth-speakerphone-airpods (index — AEC3 / platform AEC ownership)
