"""Video pipeline: any LAN source -> FFmpeg decode -> YUV420P frames.

The transcode half of the "video to the camera screen" feature is fully
implemented and testable: any FFmpeg-readable source (RTSP H.265/H.264
from a LAN IP, HTTP, local file, lavfi test source) is decoded and
scaled to the negotiated resolution/fps as raw YUV420P frames -- exactly
the input DevSendAVTalkData expects (AV-TALK-VIDEO-SEND.md SS3: raw
YUV420P, W*H*3/2 bytes per frame; transcode is mandatory, no NAL
passthrough).

The wire half is NOT implemented: frames are produced, counted and
discarded (dry-run mode) because the DVRIP encapsulation of Dev_SendMsg
11004/11006 is still unknown (see video_sender.WIRE_BLOCKER). The
pipeline therefore proves the transcode works while the API honestly
reports video_send as not implemented. Once a live capture reveals the
11004/11006 bytes, the only change needed is in AVTalkWireSender --
the pipeline already produces the exact frames it needs.
"""

import subprocess
import threading
import time

from . import video_sender
from .config import settings
from .dvrip import DVRIPClient, DVRIPError


def _even(n: int) -> int:
    """YUV420P needs even dimensions; round down."""
    return n - (n % 2)


class VideoPipeline:
    """FFmpeg decode -> YUV420P producer (dry-run: frames are not sent)."""

    def __init__(self):
        self.running = False
        self.source = ""
        self.width = 0
        self.height = 0
        self.fps = 0
        self.codec = ""
        self.negotiated = False
        self.frames_produced = 0
        self.frames_dropped = 0  # produced but not sent (no wire sender)
        self.started_at: float | None = None
        self.last_error: str | None = None
        self.last_frame_at: float | None = None
        self.actual_fps: float = 0.0
        self.bean: dict | None = None
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._sender = video_sender.AVTalkWireSender(
            settings.cam_ip, settings.cam_port)

    # -- negotiation ---------------------------------------------------
    def negotiate(self, width: int | None, height: int | None,
                  fps: int | None, codec: str | None) -> dict:
        """Resolve video params: explicit args > DecoderPram > env/defaults.

        The DecoderPram query is best-effort (DVRIP opcode 1360, see
        dvrip.query_decoder_pram) and unverified on the DOSEN camera; any
        failure falls back exactly like the iCSee app does.
        """
        params = {"codec": (codec or settings.video_codec).upper(),
                  "width": width or settings.video_width,
                  "height": height or settings.video_height,
                  "fps": fps or settings.video_fps,
                  "negotiated": False}
        if width is None and height is None and fps is None and codec is None:
            pram = self._query_decoder_pram()
            if pram is not None:
                params.update(
                    video_sender.apply_decoder_pram(pram))
        params["width"] = _even(int(params["width"]))
        params["height"] = _even(int(params["height"]))
        params["fps"] = max(1, int(params["fps"]))
        if params["codec"] not in ("H264", "H265"):
            params["codec"] = "H264"
        return params

    def _query_decoder_pram(self) -> dict | None:
        if not settings.cam_ip:
            return None
        client = DVRIPClient(settings.cam_ip, settings.cam_port,
                             settings.dvrip_connect_timeout,
                             settings.dvrip_read_timeout)
        try:
            client.connect()
            client.login(settings.cam_user, settings.cam_pass)
            return client.query_decoder_pram()
        except (OSError, DVRIPError):
            return None
        finally:
            client.close()

    # -- pipeline ------------------------------------------------------
    def start(self, source: str, width: int | None = None,
              height: int | None = None, fps: int | None = None,
              codec: str | None = None) -> dict:
        if self.running:
            raise RuntimeError("video pipeline is already running")
        params = self.negotiate(width, height, fps, codec)
        self.width, self.height = params["width"], params["height"]
        self.fps = params["fps"]
        self.codec = params["codec"]
        self.negotiated = params["negotiated"]
        self.bean = video_sender.build_encode_camera_bean(
            self.width, self.height, self.fps, self.codec)
        self.source = source
        self.frames_produced = 0
        self.frames_dropped = 0
        self.last_error = None
        self.actual_fps = 0.0

        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
        if source.startswith("rtsp://"):
            # FFmpeg >= 6: the RTSP demuxer socket-timeout option is
            # "-timeout" (microseconds); "-stimeout" was removed.
            cmd += ["-rtsp_transport", "tcp", "-timeout", "5000000"]
        cmd += ["-i", source,
                "-f", "rawvideo", "-pix_fmt", "yuv420p",
                "-vf", f"scale={self.width}:{self.height},fps={self.fps}",
                "-an", "-vcodec", "rawvideo", "-"]
        try:
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as exc:
            raise RuntimeError(f"failed to start ffmpeg: {exc}") from exc
        self._stop.clear()
        self.running = True
        self.started_at = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="video-pipeline")
        self._thread.start()
        return self.status()

    def _loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        frame_size = self.width * self.height * 3 // 2
        window_start = time.time()
        window_frames = 0
        try:
            while not self._stop.is_set():
                frame = self._proc.stdout.read(frame_size)
                if len(frame) < frame_size:
                    # EOF or short read: ffmpeg ended or the source died.
                    err = b""
                    if self._proc.stderr is not None:
                        try:
                            err = self._proc.stderr.read() or b""
                        except OSError:
                            err = b""
                    self.last_error = (
                        "ffmpeg ended: "
                        + (err.decode("utf-8", "replace").strip()
                           or "short read / source closed"))
                    break
                now = time.time()
                self.frames_produced += 1
                self.last_frame_at = now
                window_frames += 1
                if now - window_start >= 2.0:
                    self.actual_fps = window_frames / (now - window_start)
                    window_start, window_frames = now, 0
                # Dry-run: the wire sender is not implemented, so frames
                # are counted and discarded. This is deliberate -- see
                # video_sender.WIRE_BLOCKER.
                self.frames_dropped += 1
        finally:
            # Final fps estimate from the whole run (the 2 s window above
            # may never elapse for a short file).
            elapsed = time.time() - (self.started_at or time.time())
            if elapsed > 0 and self.frames_produced:
                self.actual_fps = round(
                    self.frames_produced / elapsed, 2)
            self.running = False
            if self._proc is not None:
                try:
                    self._proc.terminate()
                except OSError:
                    pass
                self._proc = None

    def stop(self) -> None:
        self._stop.set()
        if self._proc is not None:
            try:
                self._proc.terminate()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.running = False

    def status(self) -> dict:
        return {
            "running": self.running,
            "source": self.source,
            "negotiated": self.negotiated,
            "params": {"codec": self.codec, "width": self.width,
                       "height": self.height, "fps": self.fps},
            "encode_camera_bean": self.bean,
            "frames_produced": self.frames_produced,
            "frames_dropped_not_sent": self.frames_dropped,
            "actual_fps": round(self.actual_fps, 2),
            "started_at": self.started_at,
            "last_frame_at": self.last_frame_at,
            "last_error": self.last_error,
            # Honest capability flag -- the screen does NOT show anything yet.
            "video_send": {
                "implemented": False,
                "state": "dry_run_transcode_only",
                "reason": video_sender.WIRE_BLOCKER,
            },
        }
