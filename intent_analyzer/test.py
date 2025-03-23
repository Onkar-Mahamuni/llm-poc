import asyncio
import websockets

async def test_websocket():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        await ws.send("Hello Server")
        response = await ws.recv()
        print(response)

asyncio.run(test_websocket())
