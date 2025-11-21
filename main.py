from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_ping_pong(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()       # "ping" ignorieren
            await websocket.send_text("pong")   # direkt antworten
    except WebSocketDisconnect:
        pass
