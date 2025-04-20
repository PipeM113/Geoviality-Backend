import websockets
import asyncio

async def test_websocket():
    uri = "ws://localhost:8080/data/events/test"  # Cambia por la URL de tu WebSocket
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"Received: {data}")

asyncio.run(test_websocket())