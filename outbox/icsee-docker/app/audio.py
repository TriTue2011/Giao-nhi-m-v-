"""Microphone (listen) and speaker (talk) sessions over DVRIP.

Mic: a dedicated DVRIP connection, login, OPMonitor Claim+Start, then the
read loop parses media packets (dvrip.read_media_packet). Audio packets
(0xFA, G.711 A-law 8 kHz) are decoded to PCM16 8 kHz mono and pushed into
a bounded queue; the HTTP layer streams from that queue. Provenance:
go2rtc producer.go (audio payload = packet[8:], codec byte 14 = PCMA,
rate byte 2 = 8000 Hz).

Talk: a dedicated DVRIP connection, login, OPTalk Claim+Start, then
OPTalkData packets (go2rtc backchannel.go). A drain thread reads and
discards anything the camera sends back on the talk connection.
"""

import queue
import threading
import time

from . import g711
from .config import settings
from .dvrip import DVRIPClient, DVRIPError

_PCM_CHUNK = 320  # G.711 samples per packet -> 640 bytes PCM16


class MicSession:
    """Listen to the camera microphone via the DVRIP monitor stream."""

    def __init__(self):
        self.client: DVRIPClient | None = None
        self.running = False
        self.audio_codec = "unknown"
        self.sample_rate = 0
        self.packets_received = 0
        self.bytes_streamed = 0
        self.started_at: float | None = None
        self.last_error: str | None = None
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=200)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self.running:
            return
        if not settings.cam_ip:
            raise DVRIPError("ICSEE_CAM_IP is not set")
        client = DVRIPClient(settings.cam_ip, settings.cam_port,
                             settings.dvrip_connect_timeout,
                             settings.dvrip_read_timeout)
        try:
            client.connect()
            client.login(settings.cam_user, settings.cam_pass)
            client.monitor_claim_start(settings.cam_channel,
                                       settings.cam_stream)
            client.start_keepalive()
        except Exception:
            client.close()
            raise
        self.client = client
        self._stop.clear()
        self.running = True
        self.started_at = time.time()
        self.last_error = None
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="mic-session")
        self._thread.start()

    def _loop(self) -> None:
        assert self.client is not None
        try:
            while not self._stop.is_set():
                try:
                    ptype, payload, meta = self.client.read_media_packet()
                except DVRIPError as exc:
                    self.last_error = str(exc)
                    break
                if ptype != 0xFA:
                    continue  # video / info packets are ignored here
                self.audio_codec = meta.get("codec", "unknown")
                self.sample_rate = meta.get("sample_rate", 0)
                if self.audio_codec == "g711a":
                    pcm = g711.alaw_decode(payload)
                elif self.audio_codec == "g711u":
                    # mu-law not expected on this camera; keep raw bytes
                    # marked as-is rather than inventing a decode.
                    pcm = payload
                else:
                    continue
                self.packets_received += 1
                try:
                    self._queue.put_nowait(pcm)
                except queue.Full:
                    # Slow consumer: drop the oldest chunk, keep streaming.
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._queue.put_nowait(pcm)
        finally:
            self.running = False
            if self.client is not None:
                self.client.close()
                self.client = None

    def read_chunk(self, timeout: float = 5.0) -> bytes | None:
        """Next PCM16 chunk (640 bytes), or None on timeout/end."""
        try:
            chunk = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        self.bytes_streamed += len(chunk)
        return chunk

    def stop(self) -> None:
        self._stop.set()
        if self.client is not None:
            self.client.close()
        if self._thread is not None:
            self._thread.join(timeout=3)
        self.running = False

    def status(self) -> dict:
        return {
            "running": self.running,
            "codec": self.audio_codec,
            "sample_rate": self.sample_rate,
            "packets_received": self.packets_received,
            "bytes_streamed": self.bytes_streamed,
            "started_at": self.started_at,
            "last_error": self.last_error,
        }


class TalkSession:
    """Speak out of the camera speaker via DVRIP talkback (OPTalkData)."""

    def __init__(self):
        self.client: DVRIPClient | None = None
        self.running = False
        self.packets_sent = 0
        self.bytes_received = 0
        self.started_at: float | None = None
        self.last_error: str | None = None
        self._drain_stop = threading.Event()
        self._drain_thread: threading.Thread | None = None

    def start(self) -> None:
        if self.running:
            return
        if not settings.cam_ip:
            raise DVRIPError("ICSEE_CAM_IP is not set")
        client = DVRIPClient(settings.cam_ip, settings.cam_port,
                             settings.dvrip_connect_timeout,
                             settings.dvrip_read_timeout)
        try:
            client.connect()
            client.login(settings.cam_user, settings.cam_pass)
            client.talk_claim_start()
            client.start_keepalive()
        except Exception:
            client.close()
            raise
        self.client = client
        self._drain_stop.clear()
        self._drain_thread = threading.Thread(
            target=client.drain_forever, args=(self._drain_stop,),
            daemon=True, name="talk-drain")
        self._drain_thread.start()
        self.running = True
        self.started_at = time.time()
        self.last_error = None

    def send_pcm16(self, pcm: bytes) -> int:
        """Send PCM16 8 kHz mono bytes to the speaker. Returns packets sent."""
        if not self.running or self.client is None:
            raise DVRIPError("talk session is not running")
        if len(pcm) % 2:
            raise ValueError("PCM16 input must have an even number of bytes")
        self.bytes_received += len(pcm)
        packets = self.client.talk_send(g711.alaw_encode(pcm))
        self.packets_sent += packets
        return packets

    def send_g711a(self, data: bytes) -> int:
        """Send raw G.711 A-law bytes to the speaker. Returns packets sent."""
        if not self.running or self.client is None:
            raise DVRIPError("talk session is not running")
        self.bytes_received += len(data)
        packets = self.client.talk_send(data)
        self.packets_sent += packets
        return packets

    def stop(self) -> None:
        self._drain_stop.set()
        if self.client is not None:
            self.client.close()
            self.client = None
        if self._drain_thread is not None:
            self._drain_thread.join(timeout=3)
        self.running = False

    def status(self) -> dict:
        return {
            "running": self.running,
            "packets_sent": self.packets_sent,
            "bytes_received": self.bytes_received,
            "started_at": self.started_at,
            "last_error": self.last_error,
        }
