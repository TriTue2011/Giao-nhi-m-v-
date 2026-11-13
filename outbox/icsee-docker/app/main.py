"""HTTP API for the ICSee DVRIP-native Docker service.

Features and their real status (see README.md for the full picture):
* Mic (GET /api/audio/mic) and speaker (POST /api/audio/talk/*) -- DVRIP
  native, implemented. NOT yet verified live on the DOSEN RPO V1 camera.
* Video to the camera screen (POST /api/video/*) -- transcode pipeline
  implemented (dry-run); the wire send is NOT implemented (see
  video_sender.WIRE_BLOCKER) and the API says so on every response.

No credential is ever logged or returned in a response.
"""

import asyncio
import base64
import binascii
import json
import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from . import video_sender
from .audio import MicSession, TalkSession
from .config import settings
from .dvrip import DVRIPClient, DVRIPError
from .video import VideoPipeline

SERVICE_VERSION = "0.1.0"

app = FastAPI(title="icsee-docker",
              description="DVRIP-native HTTP API for ICSee/XM cameras "
                          "(mic + speaker live, video-to-screen dry-run).",
              version=SERVICE_VERSION)

_mic = MicSession()
_talk = TalkSession()
_video = VideoPipeline()
_started_at = time.time()


def _camera_configured() -> bool:
    return bool(settings.cam_ip)


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": code, "message": message})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "icsee-docker",
            "version": SERVICE_VERSION,
            "uptime_seconds": round(time.time() - _started_at, 1)}


@app.get("/api/status")
def status() -> dict:
    return {
        "camera": {
            "configured": _camera_configured(),
            "ip": settings.cam_ip or None,
            "port": settings.cam_port,
            "user": settings.cam_user,
            "channel": settings.cam_channel,
            "stream": settings.cam_stream,
        },
        "mic": _mic.status(),
        "talk": _talk.status(),
        "video": _video.status(),
    }


# -- camera ------------------------------------------------------------

@app.post("/api/cam/connect")
def cam_connect() -> Response:
    """Test the DVRIP login against the configured camera (short-lived)."""
    if not _camera_configured():
        return _err(503, "camera_not_configured",
                    "ICSEE_CAM_IP is not set (see .env.example)")
    client = DVRIPClient(settings.cam_ip, settings.cam_port,
                         settings.dvrip_connect_timeout,
                         settings.dvrip_read_timeout)
    try:
        client.connect()
        reply = client.login(settings.cam_user, settings.cam_pass)
    except (OSError, DVRIPError) as exc:
        return _err(503, "camera_unreachable",
                    f"DVRIP login failed: {exc}")
    finally:
        client.close()
    return JSONResponse({"connected": True,
                         "session": reply.get("SessionID"),
                         "device": reply.get("DeviceType")})


@app.get("/api/cam/decoder-pram")
def cam_decoder_pram() -> Response:
    """Best-effort DecoderPram negotiation (opcode 1360).

    Tries Name "DecoderPram" then "EncodeCapability"; on failure returns
    the app fallback (864x480, fps 10, H264) with negotiated=false.
    UNVERIFIED on the DOSEN camera -- see dvrip.query_decoder_pram.
    """
    if not _camera_configured():
        return _err(503, "camera_not_configured",
                    "ICSEE_CAM_IP is not set (see .env.example)")
    client = DVRIPClient(settings.cam_ip, settings.cam_port,
                         settings.dvrip_connect_timeout,
                         settings.dvrip_read_timeout)
    try:
        client.connect()
        client.login(settings.cam_user, settings.cam_pass)
        pram = client.query_decoder_pram()
    except (OSError, DVRIPError) as exc:
        return _err(503, "camera_unreachable",
                    f"DecoderPram query failed: {exc}")
    finally:
        client.close()
    params = video_sender.apply_decoder_pram(pram)
    return JSONResponse({"raw": pram, "params": params})


# -- speaker (talk) ------------------------------------------------------

@app.post("/api/audio/talk/start")
def talk_start() -> Response:
    try:
        _talk.start()
    except (OSError, DVRIPError) as exc:
        return _err(503, "camera_unreachable",
                    f"talk start failed: {exc}")
    return JSONResponse(_talk.status())


@app.post("/api/audio/talk/send")
async def talk_send(request: Request) -> Response:
    """Send audio to the camera speaker.

    Accepts either:
    * application/octet-stream -- raw PCM16 8 kHz mono bytes, or raw
      G.711 A-law bytes when ?format=g711a is given;
    * application/json -- {"format": "pcm16"|"g711a", "data": "<base64>"}.
    Audio is chunked into 320-byte G.711 packets (OPTalkData, 1432).
    """
    if not _talk.running:
        return _err(409, "talk_not_started",
                    "call POST /api/audio/talk/start first")
    content_type = request.headers.get("content-type", "")
    fmt = request.query_params.get("format", "pcm16").lower()
    try:
        if content_type.startswith("application/json"):
            body = json.loads(await request.body())
            fmt = str(body.get("format", fmt)).lower()
            try:
                data = base64.b64decode(body.get("data", ""))
            except binascii.Error as exc:
                return _err(400, "bad_base64", f"invalid base64 data: {exc}")
        else:
            data = await request.body()
        if not data:
            return _err(400, "empty_body", "no audio data received")
        if fmt == "g711a":
            packets = _talk.send_g711a(data)
        elif fmt == "pcm16":
            packets = _talk.send_pcm16(data)
        else:
            return _err(400, "bad_format",
                        "format must be 'pcm16' or 'g711a'")
    except (OSError, DVRIPError) as exc:
        return _err(503, "camera_unreachable",
                    f"talk send failed: {exc}")
    except ValueError as exc:
        return _err(400, "bad_audio", str(exc))
    return JSONResponse({"packets_sent": packets,
                         "bytes_received": len(data),
                         "talk": _talk.status()})


@app.post("/api/audio/talk/stop")
def talk_stop() -> dict:
    _talk.stop()
    return _talk.status()


# -- microphone (listen) ---------------------------------------------------

@app.get("/api/audio/mic")
async def mic_stream(request: Request, format: str = "pcm16"):
    """Stream the camera microphone audio (chunked HTTP).

    format=pcm16 (default): raw little-endian PCM16 8 kHz mono,
    Content-Type audio/L16;rate=8000;channels=1.
    format=wav: same PCM with a 44-byte WAV header (data size
    0xFFFFFFFF, streaming-style).
    format=g711a: raw G.711 A-law bytes as received from the camera.
    The mic session starts on first request and stops automatically
    when the client disconnects (or via POST /api/audio/mic/stop).
    """
    fmt = format.lower()
    if fmt not in ("pcm16", "wav", "g711a"):
        return _err(400, "bad_format",
                    "format must be 'pcm16', 'wav' or 'g711a'")
    try:
        _mic.start()
    except (OSError, DVRIPError) as exc:
        return _err(503, "camera_unreachable",
                    f"mic start failed: {exc}")

    async def generate():
        # try/finally: uvicorn CANCELS this generator when the client
        # disconnects (it does not wait for is_disconnected() to be
        # polled), so the session stop must live in finally, not after
        # the loop.
        try:
            if fmt == "wav":
                yield _wav_header(8000, 1, 16)
            while _mic.running:
                if await request.is_disconnected():
                    break
                # Read in a thread so the event loop is not blocked.
                chunk = await asyncio.to_thread(_mic.read_chunk, 1.0)
                if chunk is None:
                    continue  # timeout: re-check disconnect, keep waiting
                if fmt == "g711a":
                    # The mic session only keeps PCM; transcode back to
                    # A-law for the raw G.711 stream.
                    from . import g711 as _g711
                    yield _g711.alaw_encode(chunk)
                else:
                    yield chunk
        finally:
            _mic.stop()

    media = {"pcm16": "audio/L16;rate=8000;channels=1",
             "wav": "audio/wav",
             "g711a": "audio/PCMA;rate=8000"}[fmt]
    return StreamingResponse(generate(), media_type=media)


def _wav_header(rate: int, channels: int, bits: int) -> bytes:
    """44-byte WAV header with unknown data size (streaming)."""
    import struct
    byte_rate = rate * channels * bits // 8
    block_align = channels * bits // 8
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 0xFFFFFFFF, b"WAVE", b"fmt ", 16, 1, channels,
        rate, byte_rate, block_align, bits, b"data", 0xFFFFFFFF)


@app.post("/api/audio/mic/stop")
def mic_stop() -> dict:
    _mic.stop()
    return _mic.status()


# -- video to the camera screen (dry-run) -----------------------------------

@app.post("/api/video/start")
async def video_start(request: Request) -> Response:
    """Start the video transcode pipeline (DRY-RUN).

    Body (JSON): {"source": "rtsp://<lan-ip>:554/...", "width": 1920,
    "height": 1080, "fps": 30, "codec": "H265"} -- width/height/fps/codec
    are optional; when all are omitted the service tries the DecoderPram
    negotiation, then falls back to 864x480 / fps 10 / H264.
    The pipeline decodes the source with FFmpeg to YUV420P at the
    negotiated resolution/fps and counts frames. It does NOT send anything
    to the camera screen yet: the DVRIP encapsulation of Dev_SendMsg
    11004/11006 is still unknown (see video_sender.WIRE_BLOCKER), so the
    response always reports video_send.implemented=false.
    """
    try:
        body = json.loads(await request.body()) if await request.body() else {}
    except ValueError:
        return _err(400, "bad_json", "request body is not valid JSON")
    source = body.get("source", "")
    if not isinstance(source, str) or not source:
        return _err(400, "bad_source",
                    "field 'source' is required, e.g. "
                    "rtsp://192.168.1.10:554/user=admin&password=xxxx"
                    "&channel=1&stream=0.sdp?real_stream")
    try:
        status = _video.start(source,
                              width=body.get("width"),
                              height=body.get("height"),
                              fps=body.get("fps"),
                              codec=body.get("codec"))
    except RuntimeError as exc:
        return _err(409, "video_already_running", str(exc))
    except ValueError as exc:
        return _err(400, "bad_params", str(exc))
    return JSONResponse(status)


@app.post("/api/video/stop")
def video_stop() -> dict:
    _video.stop()
    return _video.status()


@app.get("/api/video/status")
def video_status() -> dict:
    return _video.status()


@app.post("/api/video/control")
async def video_control(request: Request) -> Response:
    """AV-talk control (pause/continue/resolution/reset) -- 501.

    The control JSON builders are complete (video_sender), but sending
    requires the same unknown 11004 wire encapsulation as the video
    frames, so this endpoint honestly refuses until the capture is done.
    """
    try:
        body = json.loads(await request.body()) if await request.body() else {}
    except ValueError:
        return _err(400, "bad_json", "request body is not valid JSON")
    command = body.get("command", "")
    try:
        ctrl_json = video_sender.build_control_json(
            command, int(body.get("width", 0)), int(body.get("height", 0)))
    except ValueError as exc:
        return _err(400, "bad_command", str(exc))
    return _err(501, "video_send_not_implemented",
                f"control {command!r} would send {ctrl_json}, but the "
                f"AV-talk wire protocol is not implemented. "
                f"{video_sender.WIRE_BLOCKER}")
