"""Video-send to the camera screen (AV talk) -- pipeline + wire sender.

This module implements everything about the AV-talk video path that has
actually been proven, and it marks the one missing piece explicitly instead
of pretending the feature works.

PROVEN (AV-TALK-VIDEO-SEND.md + AV-TALK-NATIVE.md, iCSee 7.9.6_G):
* Session: DevStartAVTalk (XMSG 5556) with an EncodeCameraBean JSON, then
  frames via DevSendAVTalkData (XMSG 5557), control via DevControlAVTalk
  (XMSG 5559), stop via DevStopAVTalkData (XMSG 5558). Login first is
  mandatory (native log "Start AVTalk,NotLogin").
* Negotiation: the app asks the device for DecoderPram (FunSDK DevConfigInfo
  cmdId 0x550 = 1360) and builds EncodeCameraBean from it; on failure it
  falls back to 864x480, fps 10, H264.
* EncodeCameraBean JSON (Gson, null fields omitted):
  {"audioinfo": {"encodetype": "g711a", "channels": 1, "bit": 16,
                 "sampleRate": 8000},
   "mediatype": 0,   # 0=ALL, 1=AUDIO, 2=VIDEO
   "videoinfo": {"dstheight": H, "dstwidth": W, "srcheight": H,
                 "srcwidth": W, "encodetype": "H264"|"H265",
                 "fps": 10, "gopsize": 4, "qp": 50, "preset": 2},
   "protocoltype": 0, "channel": 0, "version": 0, "timeout": 5000}
  (qp is forced to 50 and gopsize to 4 by VideoEncodeManager.D();
  preset = 1 when encodetype is H265, else 2.)
* Frame data: video = raw YUV420P planar, exactly W*H*3/2 bytes per frame,
  rotated per SENSOR_ORIENTATION; audio = raw PCM16 8 kHz mono, 640-byte
  (40 ms) frames. Frame-info JSON per frame:
  {"timestamp": "<millis>", "type": 1} for video, {"timestamp": ..., "type": 2}
  for audio. NO pre-encoded NAL is accepted -- transcode is mandatory.
* Native (proven by disassembly): encodetype "H265" -> ToEncodeTypeInt=3 ->
  ToFFMpegCodecID=173 -> ff_libx265_encoder, preset 1 -> "ultrafast",
  tune "zero-latency", x265-params (qp/crf/fps/keyint=fps*gop); software
  encoder only (CFFMpegEncoder, bSoft=1). Frame-info JSON parses exactly
  two fields (timestamp, type).
* Control JSON: {"command": "video_pause"|"video_continue"|
  "switching_resolution"|"reset_encoder_info"[, "info": {w/h}]};
  command enum: video_pause=3, video_continue=4, switching_resolution=12,
  reset_encoder_info=13.
* Wire (proven to the send call): frames flow
  YUV/PCM -> XMSG 5557 -> 4009 -> CEncoderMgr -> CFFMpegEncoder::Encode ->
  XMSG 4181 -> CDeviceV2::SendNextData -> Dev_SendMsg(..., 11006, ...);
  open/close AV talk is Dev_SendMsg(..., 11004, ...) with a
  SNetMediaControlParam struct (+0x10=10, +0x14=1 start / 0 stop,
  +0x18=msgID, +0x618=EncodeCameraBean JSON string).
* NO command to turn the screen on or select a display source exists
  anywhere in the app or the native library; the LCD is driven by the
  camera firmware when it receives media 11006 (unproven until a live
  video call is observed).

NOT IMPLEMENTED -- the missing piece (AV-TALK-NATIVE.md SS6):
* The DVRIP encapsulation below Dev_SendMsg is UNKNOWN: how
  SNetMediaControlParam is serialised on the wire for 11004, which fields
  of FRAME_INFO travel with the NAL payload of 11006 (timestamp, keyframe
  flag, fps, W/H -- and in which byte order), and which device-side
  message triggers SendNextData (hypothesis: the device sends 11006
  asking for the next frame -- flow control via bWaitSendData).
  Until a live packet capture (tcpdump + logcat) during a real video call
  from the iCSee app reveals these bytes, the wire sender CANNOT be
  completed. AVTalkWireSender below therefore raises
  WireProtocolNotImplemented on every method that would touch the wire.
"""

import json
import time

# Control command -> enum value (ParseAVTalkControl, AV-TALK-NATIVE.md SS2).
CONTROL_COMMANDS = {
    "video_pause": 3,
    "video_continue": 4,
    "switching_resolution": 12,
    "reset_encoder_info": 13,
}

# FunSDK internal message IDs (EUIMSG) / wire message IDs (Dev_SendMsg).
MSG_START_AV_TALK = 5556
MSG_SEND_AV_TALK_DATA = 5557
MSG_STOP_AV_TALK = 5558
MSG_CONTROL_AV_TALK = 5559
WIRE_OPEN_AV_TALK = 11004   # 0x2afc, media control
WIRE_MEDIA_DATA = 11006     # 0x2afe, encoded media frame

WIRE_BLOCKER = (
    "AV-talk wire protocol not implemented: the DVRIP encapsulation below "
    "Dev_SendMsg for messages 11004 (open/close) and 11006 (media data) "
    "is unknown -- SNetMediaControlParam serialisation, FRAME_INFO fields "
    "sent with each NAL, and the device-side message that triggers "
    "SendNextData (flow control) have not been captured yet. A live packet "
    "capture (tcpdump + logcat) during a real video call from the iCSee "
    "app is required. See AV-TALK-NATIVE.md SS6."
)


class WireProtocolNotImplemented(NotImplementedError):
    """Raised by any AV-talk wire operation until the capture is done."""


def build_encode_camera_bean(width: int, height: int, fps: int,
                             codec: str = "H264",
                             mediatype: int = 0) -> dict:
    """Build the EncodeCameraBean JSON (AV-TALK-VIDEO-SEND.md SS2).

    qp is forced to 50 and gopsize to 4 exactly as VideoEncodeManager.D()
    does; preset is 1 for H265, 2 otherwise.
    """
    codec = codec.upper()
    if codec not in ("H264", "H265"):
        raise ValueError(f"unsupported codec for AV talk: {codec!r}")
    return {
        "audioinfo": {"encodetype": "g711a", "channels": 1, "bit": 16,
                      "sampleRate": 8000},
        "mediatype": mediatype,
        "videoinfo": {
            "dstheight": height, "dstwidth": width,
            "srcheight": height, "srcwidth": width,
            "encodetype": codec,
            "fps": fps, "gopsize": 4, "qp": 50,
            "preset": 1 if codec == "H265" else 2,
        },
        "protocoltype": 0, "channel": 0, "version": 0, "timeout": 5000,
    }


def build_frame_info(timestamp_ms: int | None = None, media_type: int = 1) -> str:
    """Frame-info JSON: {"timestamp": "<millis>", "type": 1|2}.

    type 1 = video (SEND_DATA_VIDEO), type 2 = audio (SEND_DATA_AUDIO).
    Only these two fields are parsed (ParseAVTalkFrameInfoJson).
    """
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    return json.dumps({"timestamp": str(timestamp_ms), "type": media_type})


def build_control_json(command: str, width: int = 0, height: int = 0) -> str:
    """Control JSON for DevControlAVTalk (5559)."""
    if command not in CONTROL_COMMANDS:
        raise ValueError(f"unknown AV-talk control command: {command!r}")
    obj: dict = {"command": command}
    if command == "switching_resolution" and width > 0 and height > 0:
        obj["info"] = {"srcwidth": width, "srcheight": height,
                       "dstwidth": width, "dstheight": height}
    return json.dumps(obj)


def apply_decoder_pram(pram: dict | None) -> dict:
    """Negotiate video params from a DecoderPram reply (best effort).

    pram is the decoded DecoderPram dict (Video[0].Enc, Video[0].Res[0]
    .W/H/FPS, Audio[0].SR[]) or None. Returns
    {"codec", "width", "height", "fps", "negotiated": bool}.
    On any failure the iCSee app falls back to 864x480, fps 10, H264 --
    we do exactly the same.
    """
    fallback = {"codec": "H264", "width": 864, "height": 480,
                "fps": 10, "negotiated": False}
    if not isinstance(pram, dict):
        return fallback
    try:
        video = (pram.get("Video") or [{}])[0]
        enc = str(video.get("Enc") or "H264").upper()
        if enc not in ("H264", "H265"):
            enc = "H264"
        res = (video.get("Res") or [{}])[0]
        width = int(res.get("W") or 864)
        height = int(res.get("H") or 480)
        fps = int(res.get("FPS") or 10)
        if width <= 0 or height <= 0 or fps <= 0:
            return fallback
        return {"codec": enc, "width": width, "height": height,
                "fps": fps, "negotiated": True}
    except (TypeError, ValueError, IndexError, KeyError):
        return fallback


class AVTalkWireSender:
    """Wire sender for AV talk (messages 11004 / 11006).

    STUB -- every method raises WireProtocolNotImplemented. The JSON
    builders above are complete and proven; only the DVRIP encapsulation
    below Dev_SendMsg is missing (see WIRE_BLOCKER). This class exists so
    the video pipeline, the API and the future capture work all have one
    place to plug the real implementation into once the bytes are known.
    """

    implemented = False

    def __init__(self, host: str, port: int = 34567):
        self.host = host
        self.port = port

    def open(self, bean: dict) -> None:
        """Would send Dev_SendMsg(..., 11004, ...) with SNetMediaControlParam.

        Known: struct is 0x678 bytes, +0x10=10, +0x14=1 (start),
        +0x18=msgID, +0x618=EncodeCameraBean JSON string.
        Unknown: how the struct is serialised on the wire.
        """
        raise WireProtocolNotImplemented(
            f"open AV talk (11004) not implemented. Bean was: "
            f"{json.dumps(bean)}. {WIRE_BLOCKER}")

    def send_frame(self, yuv_or_pcm: bytes, timestamp_ms: int,
                   media_type: int) -> None:
        """Would encode the frame and send Dev_SendMsg(..., 11006, ...).

        Known: video frames must be exactly srcW*srcH*3/2 bytes of YUV420P
        (wrong size is dropped by CEncoderMgr::OnMsg); audio frames are
        640-byte PCM16; frame-info is {"timestamp","type"}; flow control
        runs via a bWaitSendData flag set by a device-side 11006 message.
        Unknown: DVRIP framing of the 11006 payload and of FRAME_INFO.
        """
        raise WireProtocolNotImplemented(
            f"send AV-talk frame (11006, type={media_type}, "
            f"len={len(yuv_or_pcm)}) not implemented. {WIRE_BLOCKER}")

    def send_control(self, command: str, width: int = 0,
                     height: int = 0) -> None:
        """Would send DevControlAVTalk (5559) / wire 11004 control."""
        raise WireProtocolNotImplemented(
            f"send AV-talk control {command!r} not implemented. "
            f"{WIRE_BLOCKER}")

    def close(self) -> None:
        """Would send Dev_SendMsg(..., 11004, ...) with +0x14=0 (stop)."""
        raise WireProtocolNotImplemented(
            f"close AV talk (11004 stop) not implemented. {WIRE_BLOCKER}")
