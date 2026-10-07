"""WebSocket fan-out. Each client has its own queue and sender task, so one slow browser can't
stall the 20 Hz tick or the MQTT loop."""

from __future__ import annotations

import asyncio
import json
import logging
from itertools import count
from typing import Any

from fastapi import WebSocket

log = logging.getLogger("twindock.hub")

QUEUE_MAX = 400  # ~20 s of 20 Hz updates; a client further behind than that is dropped


class Client:
    def __init__(self, cid: str, ws: WebSocket) -> None:
        self.id = cid
        self.ws = ws
        self.queue: asyncio.Queue[str | None] = asyncio.Queue(QUEUE_MAX)
        self.task = asyncio.create_task(self._sender())

    async def _sender(self) -> None:
        try:
            while (text := await self.queue.get()) is not None:
                await self.ws.send_text(text)
        except Exception as e:  # socket closed under us; the receive loop cleans up
            log.info("client %s send failed: %s", self.id, e)


class Hub:
    def __init__(self) -> None:
        self.clients: dict[str, Client] = {}
        self._ids = count(1)

    def add(self, ws: WebSocket) -> str:
        cid = f"client-{next(self._ids)}"
        self.clients[cid] = Client(cid, ws)
        return cid

    def remove(self, cid: str) -> None:
        c = self.clients.pop(cid, None)
        if c:
            c.task.cancel()

    def send(self, to: str | None, msg: dict[str, Any]) -> None:
        text = json.dumps(msg, separators=(",", ":"))
        targets = [self.clients[to]] if to in self.clients else ([] if to else list(self.clients.values()))
        for c in targets:
            try:
                c.queue.put_nowait(text)
            except asyncio.QueueFull:
                log.warning("client %s is too far behind, dropping it", c.id)
                self.remove(c.id)
                asyncio.create_task(c.ws.close(code=1013))
