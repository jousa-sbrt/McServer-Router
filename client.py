import asyncio
import time

import websockets


SERVER_URL = "wss://mcserver-router.onrender.com/ws"

async def ping_test():
    async with websockets.connect(SERVER_URL) as ws:
        print("Verbunden")
        while True:
            t0 = time.time()
            await ws.send("ping")
            msg = await ws.recv()
            t1 = time.time()
            rtt_ms = (t1 - t0) * 1000
            print(f"RTT: {rtt_ms:.1f} ms")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(ping_test())
