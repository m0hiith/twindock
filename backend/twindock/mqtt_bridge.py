"""aiomqtt connection to Mosquitto: feeds twin/gateway/* into the engine, publishes commands."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from dataclasses import dataclass
from typing import Callable
from urllib.parse import unquote, urlparse

import aiomqtt

from .engine import Engine

log = logging.getLogger("twindock.mqtt")


@dataclass(frozen=True)
class BrokerConfig:
    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
    tls: bool = False

    @classmethod
    def from_url(cls, url: str) -> "BrokerConfig":
        """MQTT_URL: mqtt://[user:pass@]host[:1883] or mqtts://[user:pass@]host[:8883] (TLS, e.g. HiveMQ Cloud)."""
        u = urlparse(url)
        if u.scheme not in ("mqtt", "mqtts", "tcp", "ssl") or not u.hostname:
            raise ValueError(f"MQTT_URL must look like mqtt://host:1883 or mqtts://user:pass@host:8883, not {url!r}")
        tls = u.scheme in ("mqtts", "ssl")
        return cls(u.hostname, u.port or (8883 if tls else 1883), unquote(u.username) if u.username else None,
                   unquote(u.password) if u.password else None, tls)

    def __str__(self) -> str:  # never logs the password
        return f"{'mqtts' if self.tls else 'mqtt'}://{self.host}:{self.port}"


class MqttBridge:
    def __init__(self, engine: Engine, flush: Callable[[], None], broker: BrokerConfig,
                 client_id: str = "twindock-backend") -> None:
        self.client_id = client_id  # must be unique on the broker, or two backends kick each other off
        self.engine = engine
        self.flush = flush
        self.broker = broker
        self._queue: asyncio.Queue[tuple[str, bytes]] = asyncio.Queue()

    def publish(self, topic: str, payload: dict[str, object]) -> None:
        self._queue.put_nowait((topic, json.dumps(payload, separators=(",", ":")).encode()))

    async def _publisher(self, client: aiomqtt.Client) -> None:
        while True:
            topic, data = await self._queue.get()
            # QoS 1: an LED command must reach the board at least once; it is idempotent (sets a state).
            await client.publish(topic, data, qos=1)

    async def run(self) -> None:
        backoff = 1.0
        while True:
            try:
                b = self.broker
                async with aiomqtt.Client(b.host, b.port, identifier=self.client_id, keepalive=30, username=b.username,
                                          password=b.password, tls_context=ssl.create_default_context() if b.tls else None) as client:
                    log.info("connected to MQTT %s", b)
                    backoff = 1.0
                    while not self._queue.empty():  # commands queued while offline were already rejected
                        self._queue.get_nowait()
                    # One subscription for the board (twin/gateway/#) and the simulated site devices
                    # (twin/<site>/<device>/<channel>); the engine routes by prefix.
                    await client.subscribe("twin/#", qos=1)
                    self.engine.set_mqtt_connected(True)
                    self.flush()
                    pub = asyncio.create_task(self._publisher(client))
                    try:
                        async for m in client.messages:
                            p = m.payload
                            raw = p if isinstance(p, (bytes, bytearray)) else str(p or "").encode()
                            self.engine.on_mqtt(str(m.topic), bytes(raw), bool(m.retain))
                            self.flush()
                    finally:
                        pub.cancel()
            except aiomqtt.MqttError as e:
                log.warning("MQTT %s unavailable (%s), retrying in %.0f s", self.broker, e, backoff)
            self.engine.set_mqtt_connected(False)
            self.flush()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 10.0)
