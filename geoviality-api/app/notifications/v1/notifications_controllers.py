import asyncio
from typing import List
from fastapi import WebSocket

# Colas de eventos (conserva nombres si tu código los usa)
event_queue1: asyncio.Queue = asyncio.Queue()
event_queue2: asyncio.Queue = asyncio.Queue()

active_connections: List[WebSocket] = []

async def event_generator1():
    while True:
        data = await event_queue1.get()
        yield f"data: {data}\n\n"

async def event_generator2():
    while True:
        data = await event_queue2.get()
        yield f"data: {data}\n\n"
