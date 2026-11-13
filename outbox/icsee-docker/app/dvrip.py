"""DVRIP client for XiongMai (XM) cameras, self-contained (no python-dvr dep).

Protocol reference (both read directly, they agree on the framing):
* go2rtc ``pkg/dvrip/client.go`` + ``backchannel.go`` + ``producer.go``
  (AlexxIT/go2rtc) -- opcodes, 20-byte header, talkback packet format,
  monitor media packet layout.
* OpenIPC python-dvr (module ``dvrip``) -- same framing, plus the
  ``reassemble_bin_payload`` media-packet parser and the ``QCODES`` table
  (config opcodes 1040/1042/1360, KeepAlive 1006).

Wire format (all multi-byte integers little-endian unless noted):
* Command chunk: 20-byte header + JSON payload + ``\\n\\x00``.
  Header: [0]=0xFF, [1]=0x00, [2:4]=pad, [4:8]=session LE u32,
  [8:12]=sequence LE u32, [12:14]=pad, [14:16]=opcode LE u16,
  [16:20]=payload length LE u32 (payload bytes + 2 for the trailing
  ``\\n\\x00``).
* Login (opcode 1000): ``{"EncryptType":"MD5","LoginType":"DVRIP-Web",
  "PassWord":"<SofiaHash>","UserName":"<user>"}``. SofiaHash = MD5 of the
  password mapped to 8 chars of
  ``0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz``.
  Reply ``Ret`` must be 100 (or 515); ``SessionID`` is a hex string.
* KeepAlive (opcode 1006): ``{"Name":"KeepAlive","SessionID":"0x%08X"}``.
* Config get (opcode 1042, or 1360 for EncodeCapability/SystemFunction):
  ``{"Name":"<name>","SessionID":"0x%08X"}``.
* Monitor (OPMonitor): Claim opcode 1413, then Start opcode 1410, both with
  ``{"Name":"OPMonitor","SessionID":"0x%08X","OPMonitor":{"Action":
  "Claim"|"Start","Parameter":{"Channel":0,"CombinMode":"NONE",
  "StreamType":"Main"|"Extra1","TransMode":"TCP"}}}``. After Start the
  camera streams media chunks (no JSON reply is read for Start).
* Talk (OPTalk): Claim opcode 1434, then Start opcode 1430, both with
  ``{"Name":"OPTalk","SessionID":"0x%08X","OPTalk":{"Action":
  "Claim"|"Start","AudioFormat":{"EncodeType":"G711_ALAW"}}}``.
  Audio data: opcode 1432 (OPTalkData), payload = 8-byte header + 320 bytes
  G.711: header = BE u32 0x1FA, byte[4]=14 (PCMA) / 10 (PCMU),
  byte[5]=2 (8000 Hz), LE u16 length at [6:8].

Media packets inside monitor chunks (go2rtc ``ReadPacket``):
* Each media packet starts with bytes ``00 00 01`` + type byte:
  0xFC/0xFE = video I-frame, 0xFD = video P-frame, 0xFA = audio,
  0xF9 = unknown/info.
* I-frame: total size = LE u32 at [12:] + 16; header bytes:
  [4]=video codec (0x02/0x12=H.264, 0x03/0x13/0x43/0x53=H.265),
  [5]=fps, [6]=width/8, [7]=height/8, [8:12]=timestamp LE u32;
  payload = packet[16:].
* P-frame: total size = LE u32 at [4:] + 8; payload = packet[8:].
* Audio: total size = LE u16 at [6:] + 8; [4]=audio codec
  (10=G.711 mu-law, 14=G.711 A-law), [5]=sample-rate index
  (1=4000, 2=8000, 3=11025, ...); payload = packet[8:] (G.711 bytes).

A media packet may be split across several DVRIP chunks, and one chunk may
contain several packets -- hence the internal reassembly buffer.
"""

import hashlib
import json
import socket
import struct
import threading
import time

# DVRIP opcodes (go2rtc pkg/dvrip/client.go; python-dvr QCODES).
OP_LOGIN = 1000
OP_KEEPALIVE = 1006
OP_CONFIG_GET = 1042
OP_CONFIG_SET = 1040
OP_SYSTEM_INFO = 1020
OP_ENCODE_CAPABILITY = 1360  # also 'SystemFunction'; cmdId 0x550 in FunSDK
OP_MONITOR_CLAIM = 1413
OP_MONITOR_START = 1410
OP_TALK_CLAIM = 1434
OP_TALK_START = 1430
OP_TALK_DATA = 1432

OK_RET = (100, 515)

_SAMPLE_RATES = (4000, 8000, 11025, 16000, 20000, 22050, 32000, 44100, 48000)

_TALK_PACKET_SIZE = 320  # bytes of G.711 per OPTalkData packet


class DVRIPError(Exception):
    """Any DVRIP protocol / transport error."""


def sofia_hash(password: str) -> str:
    """Sofia MD5 password hash (go2rtc SofiaHash / python-dvr sofia_hash)."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    digest = hashlib.md5(password.encode("utf-8")).digest()
    out = []
    for i in range(0, 16, 2):
        out.append(chars[(digest[i] + digest[i + 1]) % 62])
    return "".join(out)


class DVRIPClient:
    """One TCP connection to a camera (DVRIP, default port 34567).

    One connection is used per session type (monitor / talk / config),
    mirroring go2rtc which dials a separate connection for the backchannel.
    All writes are serialised by a lock so a keepalive thread and a
    data-sending thread can share one connection safely.
    """

    def __init__(self, host: str, port: int = 34567,
                 connect_timeout: float = 5.0, read_timeout: float = 10.0):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.sock: socket.socket | None = None
        self.session: int = 0
        self.seq: int = 0
        self.alive_interval: float = 20.0
        self._write_lock = threading.Lock()
        self._buf = bytearray()  # reassembly buffer for media packets
        self._keepalive_thread: threading.Thread | None = None
        self._keepalive_stop = threading.Event()

    # -- transport -----------------------------------------------------
    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.host, self.port), timeout=self.connect_timeout)
        self.sock.settimeout(self.read_timeout)
        self.session = 0
        self.seq = 0
        self._buf = bytearray()

    def close(self) -> None:
        self._keepalive_stop.set()
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _read_exact(self, n: int) -> bytes:
        assert self.sock is not None
        data = bytearray()
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise DVRIPError("connection closed by camera")
            data.extend(chunk)
        return bytes(data)

    def write_cmd(self, opcode: int, payload: bytes) -> None:
        """Send one command chunk: 20-byte header + payload."""
        assert self.sock is not None
        header = struct.pack("<BB2xII2xHI",
                             0xFF, 0x00, self.session, self.seq,
                             opcode, len(payload))
        with self._write_lock:
            self.sock.sendall(header + payload)
        self.seq += 1

    def _write_json_cmd(self, opcode: int, obj: dict) -> None:
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n\x00"
        self.write_cmd(opcode, payload)

    def read_chunk(self) -> tuple[int, bytes]:
        """Read one chunk: 20-byte header + payload. Returns (opcode, payload)."""
        header = self._read_exact(20)
        if header[0] != 0xFF:
            raise DVRIPError(f"bad chunk header: {header[:4]!r}")
        # header layout: [4:8]=session LE u32, [8:12]=seq, [14:16]=opcode
        # LE u16, [16:20]=payload length LE u32.
        session = struct.unpack_from("<I", header, 4)[0]
        opcode = struct.unpack_from("<H", header, 14)[0]
        length = struct.unpack_from("<I", header, 16)[0]
        self.session = session
        payload = self._read_exact(length) if length else b""
        return opcode, payload

    def read_json(self) -> dict:
        """Read one chunk and parse it as JSON (trailing \\n\\x00 stripped)."""
        _, payload = self.read_chunk()
        if len(payload) >= 2 and payload[-2:] == b"\n\x00":
            payload = payload[:-2]
        try:
            reply = json.loads(payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise DVRIPError(f"invalid JSON reply: {payload[:200]!r}") from exc
        if not isinstance(reply, dict):
            raise DVRIPError(f"unexpected JSON reply: {reply!r}")
        ret = reply.get("Ret")
        if ret is not None and ret not in OK_RET:
            raise DVRIPError(f"camera returned Ret={ret}: {reply}")
        return reply

    # -- session -------------------------------------------------------
    def login(self, user: str, password: str) -> dict:
        """Login (opcode 1000). Returns the login reply dict."""
        self._write_json_cmd(OP_LOGIN, {
            "EncryptType": "MD5",
            "LoginType": "DVRIP-Web",
            "PassWord": sofia_hash(password),
            "UserName": user,
        })
        reply = self.read_json()
        session_id = reply.get("SessionID")
        if isinstance(session_id, str):
            try:
                self.session = int(session_id, 16)
            except ValueError:
                pass
        if isinstance(reply.get("AliveInterval"), (int, float)):
            self.alive_interval = float(reply["AliveInterval"])
        return reply

    def start_keepalive(self) -> None:
        """Background KeepAlive (opcode 1006) every AliveInterval seconds."""
        if self._keepalive_thread is not None:
            return
        self._keepalive_stop.clear()

        def _loop() -> None:
            while not self._keepalive_stop.wait(self.alive_interval):
                try:
                    self._write_json_cmd(OP_KEEPALIVE, {
                        "Name": "KeepAlive",
                        "SessionID": "0x%08X" % self.session,
                    })
                except (OSError, DVRIPError):
                    return

        t = threading.Thread(target=_loop, daemon=True,
                             name="dvrip-keepalive")
        t.start()
        self._keepalive_thread = t

    # -- config --------------------------------------------------------
    def get_config(self, name: str, opcode: int = OP_CONFIG_GET) -> dict:
        """Generic config get: {"Name": name, "SessionID": ...}."""
        self._write_json_cmd(opcode, {
            "Name": name,
            "SessionID": "0x%08X" % self.session,
        })
        return self.read_json()

    def query_decoder_pram(self) -> dict | None:
        """Best-effort DecoderPram negotiation (AV-TALK-VIDEO-SEND.md SS2).

        The iCSee app asks the device for ``DecoderPram`` with FunSDK
        DevConfigInfo cmdId 0x550 (1360). In DVRIP terms opcode 1360 is
        'EncodeCapability'/'SystemFunction' (python-dvr QCODES). We try the
        name "DecoderPram" first, then "EncodeCapability". Returns the
        decoded dict, or None if the camera does not answer either.
        UNVERIFIED on the DOSEN RPO V1 -- the exact DVRIP encoding of the
        FunSDK DevConfigInfo call has not been proven by packet capture.
        Callers must fall back to defaults (864x480, fps 10, H264).
        """
        for name in ("DecoderPram", "EncodeCapability"):
            try:
                reply = self.get_config(name, opcode=OP_ENCODE_CAPABILITY)
            except (OSError, DVRIPError):
                continue
            for key in ("DecoderPram", "EncodeCapability"):
                if isinstance(reply.get(key), dict):
                    return reply[key]
            if reply.get("Ret") in OK_RET:
                return reply
        return None

    # -- monitor (mic + video downlink) --------------------------------
    def monitor_claim_start(self, channel: int = 0,
                            stream: str = "Main") -> None:
        """OPMonitor Claim (1413, waits for JSON reply) + Start (1410).

        After Start the camera streams media chunks; no JSON reply is
        read for Start (same as go2rtc Play() / python-dvr start_monitor).
        """
        params = {"Channel": channel, "CombinMode": "NONE",
                  "StreamType": stream, "TransMode": "TCP"}
        self._write_json_cmd(OP_MONITOR_CLAIM, {
            "Name": "OPMonitor",
            "SessionID": "0x%08X" % self.session,
            "OPMonitor": {"Action": "Claim", "Parameter": params},
        })
        self.read_json()
        self._write_json_cmd(OP_MONITOR_START, {
            "Name": "OPMonitor",
            "SessionID": "0x%08X" % self.session,
            "OPMonitor": {"Action": "Start", "Parameter": params},
        })

    def _skip_json_replies(self) -> None:
        """Discard leading JSON reply chunks from the media buffer.

        The monitor connection carries both JSON replies (e.g. the
        KeepAlive response, or a reply to OPMonitorStart) and binary
        media packets. A JSON reply starts with '{' and ends with
        b"\\n\\x00"; a media packet starts with 00 00 01. Without this,
        a KeepAlive reply landing mid-stream breaks the media parser
        ("bad media packet prefix"). A reply split across chunks is
        handled by reading more chunks until the terminator appears.
        """
        while True:
            if not self._buf:
                _, chunk = self.read_chunk()
                self._buf.extend(chunk)
                continue
            if self._buf[0:1] != b"{":
                return
            end = self._buf.find(b"\n\x00")
            if end == -1:
                if len(self._buf) > 65536:
                    raise DVRIPError(
                        "oversized JSON reply in media stream")
                _, chunk = self.read_chunk()
                self._buf.extend(chunk)
                continue
            del self._buf[:end + 2]

    def read_media_packet(self) -> tuple[int, bytes, dict]:
        """Read one media packet from the monitor stream.

        Returns (ptype, payload, meta) where ptype is 0xFC/0xFE (video
        I-frame), 0xFD (video P-frame), 0xFA (audio) or 0xF9 (info).
        Payload is the media data only (headers stripped). Meta holds
        codec/fps/width/height for video, codec/sample_rate for audio.
        Mirrors go2rtc ReadPacket + producer.go payload slicing.
        """
        self._skip_json_replies()
        while len(self._buf) < 16:
            _, chunk = self.read_chunk()
            self._buf.extend(chunk)
            self._skip_json_replies()
        if bytes(self._buf[:3]) != b"\x00\x00\x01":
            raise DVRIPError(
                f"bad media packet prefix: {bytes(self._buf[:16])!r}")
        ptype = self._buf[3]
        if ptype in (0xFC, 0xFE):
            size = struct.unpack_from("<I", self._buf, 12)[0] + 16
        elif ptype == 0xFD:
            size = struct.unpack_from("<I", self._buf, 4)[0] + 8
        elif ptype in (0xFA, 0xF9):
            size = struct.unpack_from("<H", self._buf, 6)[0] + 8
        else:
            raise DVRIPError(f"unknown media packet type: 0x{ptype:02X}")
        while len(self._buf) < size:
            _, chunk = self.read_chunk()
            self._buf.extend(chunk)
        packet = bytes(self._buf[:size])
        del self._buf[:size]

        meta: dict = {}
        if ptype in (0xFC, 0xFE):
            codec_byte, fps = packet[4], packet[5]
            meta.update({
                "frame": "I",
                "codec": "h264" if codec_byte in (0x02, 0x12)
                         else "h265" if codec_byte in (0x03, 0x13, 0x43, 0x53)
                         else f"unknown-0x{codec_byte:02x}",
                "fps": fps,
                "width": packet[6] * 8,
                "height": packet[7] * 8,
            })
            payload = packet[16:]
        elif ptype == 0xFD:
            meta.update({"frame": "P"})
            payload = packet[8:]
        else:  # 0xFA audio / 0xF9 info
            codec_byte, rate_idx = packet[4], packet[5]
            meta.update({
                "codec": "g711a" if codec_byte == 14
                         else "g711u" if codec_byte == 10
                         else f"unknown-0x{codec_byte:02x}",
                "sample_rate": _SAMPLE_RATES[rate_idx - 1]
                               if 1 <= rate_idx <= len(_SAMPLE_RATES) else 0,
            })
            payload = packet[8:]
        return ptype, payload, meta

    # -- talk (speaker) --------------------------------------------------
    def talk_claim_start(self) -> None:
        """OPTalk Claim (1434, waits for JSON reply) + Start (1430).

        Same as go2rtc Client.Talk(). After Start, audio is pushed with
        talk_send(). The camera may send data back on this connection;
        callers should drain it (see audio.TalkSession).
        """
        for action, opcode, wait in (("Claim", OP_TALK_CLAIM, True),
                                     ("Start", OP_TALK_START, False)):
            self._write_json_cmd(opcode, {
                "Name": "OPTalk",
                "SessionID": "0x%08X" % self.session,
                "OPTalk": {"Action": action,
                           "AudioFormat": {"EncodeType": "G711_ALAW"}},
            })
            if wait:
                self.read_json()

    def talk_send(self, g711_data: bytes) -> int:
        """Send G.711 audio to the camera speaker (opcode 1432, OPTalkData).

        Data is split into 320-byte packets; each packet is an 8-byte
        header (BE u32 0x1FA, codec byte 14=PCMA, rate byte 2=8000 Hz,
        LE u16 length) + 320 bytes of G.711. A short tail (< 320 bytes)
        is padded with silence (A-law silence = 0xD5). Returns the
        number of packets sent. Mirrors go2rtc backchannel.go.
        """
        if not g711_data:
            return 0
        packets = 0
        offset = 0
        while offset < len(g711_data):
            chunk = g711_data[offset:offset + _TALK_PACKET_SIZE]
            if len(chunk) < _TALK_PACKET_SIZE:
                chunk = chunk + b"\xD5" * (_TALK_PACKET_SIZE - len(chunk))
            # 8-byte header (go2rtc backchannel.go): BE u32 0x1FA, codec
            # byte 14 (PCMA), rate byte 2 (8000 Hz), LE u16 length.
            header = struct.pack(">IBB", 0x1FA, 14, 2) + struct.pack(
                "<H", _TALK_PACKET_SIZE)
            self.write_cmd(OP_TALK_DATA, header + chunk)
            packets += 1
            offset += _TALK_PACKET_SIZE
        return packets

    def drain_forever(self, stop_event: threading.Event) -> None:
        """Read-and-discard loop for the talk connection (go2rtc
        Backchannel.Start does the same). Ends on error or stop_event."""
        assert self.sock is not None
        self.sock.settimeout(1.0)
        while not stop_event.is_set():
            try:
                self.read_chunk()
            except socket.timeout:
                continue
            except (OSError, DVRIPError):
                return
