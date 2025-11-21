import asyncio
import websockets

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 25565

WS_URL = "wss://DEIN-RELAY-URL_HIER/client"


async def handle_connection(reader: asyncio.StreamReader,
                                      writer: asyncio.StreamWriter):

    try:
        async with websockets.connect(
            WS_URL,
            ping_interval=None,
            max_size=None
        ) as ws:
            print("[WS] Connected to relay")

            async def tcp_to_ws():
                try:
                    while True:
                        data = await reader.read(4096)
                        await ws.send(data)
                except Exception as e:
                    print(f"[tcp_to_ws] Error: {e}")
                    await ws.close()

            async def ws_to_tcp():
                try:
                    async for message in ws:
                        data = message
                        writer.write(data)
                        await writer.drain()
                except Exception as e:
                    print(f"[ws_to_tcp] Error: {e}")
                finally:
                    writer.close()
                    await writer.wait_closed()
                    
            await asyncio.gather(tcp_to_ws(), ws_to_tcp())

    except Exception as e:
        print(f"[handle_minecraft_connection] Error: {e}")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_connection,
        LOCAL_HOST,
        LOCAL_PORT
    )
    print(f"[INFO] {LOCAL_HOST}:{LOCAL_PORT}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
