"""aiomqtt connection to Mosquitto: feeds twin/gateway/* into the engine, publishes commands."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable

import aiomqtt

from .engine import Engine

log = logging.getLogger("twindock.mqtt")


class MqttBridge:
    def __init__(self, engine: Engine, flush: Callable[[], None], host: str, port: int) -> None:
        self.engine = engine
        self.flush = flush
        self.host = host
        self.port = port
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
                async with aiomqtt.Client(self.host, self.port, identifier="twindock-backend", keepalive=30) as client:
                    log.info("connected to MQTT %s:%s", self.host, self.port)
                    backoff = 1.0
                    while not self._queue.empty():  # commands queued while offline were already rejected
                        self._queue.get_nowait()
                    await client.subscribe("twin/gateway/#", qos=1)
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
                log.warning("MQTT %s:%s unavailable (%s), retrying in %.0f s", self.host, self.port, e, backoff)
            self.engine.set_mqtt_connected(False)
            self.flush()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 10.0)
