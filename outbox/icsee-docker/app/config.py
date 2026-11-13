"""Configuration for the icsee-docker service.

All settings come from environment variables. No real credential values are
stored here or anywhere in this repository -- see .env.example.
"""

import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class Settings:
    # Camera (DVRIP) connection -- all from env, no defaults with real values.
    cam_ip: str = os.environ.get("ICSEE_CAM_IP", "")
    cam_port: int = _int("ICSEE_CAM_PORT", 34567)
    cam_user: str = os.environ.get("ICSEE_CAM_USER", "admin")
    cam_pass: str = os.environ.get("ICSEE_CAM_PASS", "")
    cam_channel: int = _int("ICSEE_CAM_CHANNEL", 0)
    # Monitor stream type: "Main" (1080P) or "Extra1" (D1 sub stream).
    cam_stream: str = os.environ.get("ICSEE_CAM_STREAM", "Main")
    # Device serial, only needed by the (not yet implemented) FunSDK/AV-talk
    # path. Kept for future use; DVRIP-native mic/talk do not need it.
    cam_sn: str = os.environ.get("ICSEE_CAM_SN", "")

    # Video pipeline defaults. These are the fallbacks used when the camera
    # does not answer the DecoderPram negotiation -- they mirror the iCSee
    # app behaviour (AV-TALK-VIDEO-SEND.md SS2): 864x480, fps 10, H264.
    # The user's DOSEN RPO V1 reports H.265 / 1080P / 30fps in its own
    # settings; set these env vars to match, or let the DecoderPram query
    # override them at /api/video/start time.
    video_width: int = _int("VIDEO_WIDTH", 864)
    video_height: int = _int("VIDEO_HEIGHT", 480)
    video_fps: int = _int("VIDEO_FPS", 10)
    video_codec: str = os.environ.get("VIDEO_CODEC", "H264").upper()
    # Optional directory to dump raw YUV debug frames (off by default).
    video_debug_dump_dir: str = os.environ.get("VIDEO_DEBUG_DUMP_DIR", "")

    # HTTP API.
    api_host: str = os.environ.get("API_HOST", "0.0.0.0")
    api_port: int = _int("API_PORT", 8080)

    # DVRIP socket timeouts (seconds).
    dvrip_connect_timeout: float = float(os.environ.get("DVRIP_CONNECT_TIMEOUT", "5"))
    dvrip_read_timeout: float = float(os.environ.get("DVRIP_READ_TIMEOUT", "10"))


settings = Settings()
