# tcp-ws-tunnel

A small, hacky **TCP-over-WebSocket tunnel** written in Python.  
It lets you forward arbitrary TCP connections (games, custom protocols, data streams, etc.) through a WebSocket relay on the internet.

Originally this was built to expose a **local Minecraft server** to friends without router port forwarding.  
But the tunnel is completely **protocol-agnostic** – it doesn’t know or care what’s inside the TCP stream.  
So you can also use it for things like:

- custom TCP backends
- home-grown game servers
- simple chat / telnet-like protocols
- internal services you want to tunnel out of your LAN

---

## Architecture

```text
[Client App] ─TCP─> [Client Adapter] ─WebSocket─> [Relay Server] ─WebSocket─> [Server Adapter] ─TCP─> [Server App]
```

- **Client App**: Any application that talks TCP to `localhost:PORT`
  (e.g. Minecraft, your own program, …)
- **Client Adapter**: Python script running on the client machine
- **Relay Server**: Runs on the internet (e.g. Render, Koyeb, Fly.io, …) and logically links host & client
- **Server Adapter**: Python script running on the machine where your actual server app lives
- **Server App**: Your real TCP server (Minecraft, custom TCP service, whatever)

The tunnel is “dumb”: it just forwards raw bytes in both directions and never interprets the protocol.

---

## Components

The project consists of three main parts:

### 1. Relay Server (on the internet)

- WebSocket server with two endpoints:
  - `/host`   – connection from the server adapter
  - `/client` – connection from the client adapter
- As soon as **host** and **client** are both connected, the relay starts piping data 1:1 between them.

> Typically implemented with FastAPI + `asyncio`, using a `pipe(ws_a, ws_b)` function that runs both directions in parallel.

### 2. Server Adapter (`server_adapter.py`)

Runs on the machine that hosts your **server app**.

- opens a **TCP connection** to your local server  
  (e.g. `127.0.0.1:25565` for Minecraft)
- opens a **WebSocket connection** to the relay (`wss://…/host`)
- forwards all bytes between TCP and WebSocket

Important constants in the script:

```python
MC_SERVER_HOST = "127.0.0.1"
MC_SERVER_PORT = 25565              # Port of your local server app

WS_URL = "wss://YOUR-RELAY-URL/host"    # WebSocket URL of the relay (host endpoint)
```

### 3. Client Adapter (`client_adapter.py`)

Runs on the client’s machine.

- starts a **local TCP server**, e.g. `127.0.0.1:25565`
- opens a **WebSocket connection** to the relay (`wss://…/client`)
- forwards all bytes between the local client app and the relay

Important constants in the script:

```python
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 25565                      # Port the client app connects to

WS_URL = "wss://YOUR-RELAY-URL/client"  # WebSocket URL of the relay (client endpoint)
```

For the client app this just looks like a normal TCP server on `localhost:LOCAL_PORT`.

---

## Requirements

- **Python 3.10+** (recommended)
- Python packages:
  ```bash
  pip install websockets fastapi uvicorn
  ```
- A hosting provider that supports **WebSockets**, e.g.:
  - **Render**
  - **Koyeb**
  - Fly.io
  - Northflank  
  (or any other PaaS / VM where you can run `uvicorn`)

---

## Installation

1. Clone the repo:

   ```bash
   git clone <your-repo-url>
   cd tcp-ws-tunnel
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
   or manually:

   ```bash
   pip install websockets fastapi uvicorn
   ```

3. Adjust config values:
   - `server_adapter.py` → `MC_SERVER_HOST`, `MC_SERVER_PORT`, `WS_URL`
   - `client_adapter.py` → `LOCAL_HOST`, `LOCAL_PORT`, `WS_URL`
   - Relay server (`main.py` or similar) → WebSocket endpoints `/host` and `/client`

---

## Deploying the Relay Server (Render, Koyeb, etc.)

You can deploy the relay on any service that runs a long-lived Python web process and supports WebSockets.  
For example:

### Render

1. Push your relay server code to GitHub (including `requirements.txt` and `main.py`).
2. On Render: **New → Web Service → From Git Repository**.
3. Select your repo.
4. Set:

   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

5. Choose a region (ideally in Europe if you’re in the EU).
6. After deploy, your app will have a URL like:

   ```text
   https://your-relay.onrender.com
   ```

   WebSocket URLs:

   ```text
   wss://your-relay.onrender.com/host
   wss://your-relay.onrender.com/client
   ```

### Koyeb

You can do basically the same thing on Koyeb:

1. Create a new **App → Service from GitHub repo**.
2. Koyeb auto-detects Python using `requirements.txt`.
3. Set:

   - **Build command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

4. Service type: **HTTP** (not raw TCP). WebSockets work as HTTP upgrade on top of this.
5. After deploy, you’ll get a URL like:

   ```text
   https://your-relay.koyeb.app
   ```

   WebSocket URLs:

   ```text
   wss://your-relay.koyeb.app/host
   wss://your-relay.koyeb.app/client
   ```

The same `uvicorn main:app --host 0.0.0.0 --port $PORT` pattern also works on other platforms (Fly.io, Northflank, etc.) as long as they pass a `$PORT` env variable.

---

## Usage

### 1. Start the Relay Server (online)

- Deploy the relay to Render, Koyeb, etc. as described above.
- Note your final relay URL and update:
  - `WS_URL` in `server_adapter.py` to `…/host`
  - `WS_URL` in `client_adapter.py` to `…/client`

### 2. Start the Server Adapter (on the server side)

On the machine where your server app runs:

1. Start your **server app** (e.g. Minecraft server, custom TCP server), listening on:

   ```text
   MC_SERVER_HOST : MC_SERVER_PORT
   ```

2. Set `WS_URL` in `server_adapter.py`, e.g.:

   ```python
   WS_URL = "wss://your-relay.koyeb.app/host"
   ```

3. Run the adapter:

   ```bash
   python server_adapter.py
   ```

The adapter connects:

- via TCP to your local server app
- via WebSocket to the relay `/host`

### 3. Start the Client Adapter (on the client side)

On the client’s machine:

1. Set `WS_URL` in `client_adapter.py`, e.g.:

   ```python
   WS_URL = "wss://your-relay.koyeb.app/client"
   ```

2. Run the adapter:

   ```bash
   python client_adapter.py
   ```

3. Configure the client app to connect to the **local** TCP server exposed by the adapter, e.g.:

   ```text
   Address: 127.0.0.1
   Port:    25565
   ```

From the client app’s perspective, it’s just talking to `localhost`. Under the hood, all traffic flows through the WebSocket relay.

---

## Example: Minecraft (just one use case)

Just as a concrete example (but remember: this works for any TCP app):

- **Server side:**
  - Minecraft server listening on `127.0.0.1:25565`
  - `server_adapter.py` with:
    ```python
    MC_SERVER_HOST = "127.0.0.1"
    MC_SERVER_PORT = 25565
    WS_URL = "wss://mc-tunnel-relay.koyeb.app/host"
    ```

- **Client side:**
  - `client_adapter.py` with:
    ```python
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 25565
    WS_URL = "wss://mc-tunnel-relay.koyeb.app/client"
    ```
  - In Minecraft, simply add a server:
    ```text
    Address: 127.0.0.1
    Port:    25565
    ```

**Important:**  
Latency and jitter will depend on:

- the quality of your hosting provider
- the physical distance between client ↔ relay ↔ server
- how busy the free tier is (if you use free plans)

---

## Notes & Limitations

- **Security**
  - The tunnel itself has no auth, ACLs, or TLS handling (apart from what your hoster offers).
  - Don’t use this as-is for sensitive production traffic. Add authentication, tokens, IP filtering, etc.

- **Latency**
  - Every extra hop (client ↔ relay ↔ server) and the WebSocket framing adds latency.
  - For chat, status, casual gaming, and debugging it’s often fine.
  - It’s not a replacement for a direct TCP connection if you need ultra-low, stable latency.

- **Reliability**
  - This is more of a learning / toy project than a battle-tested tunneling solution.
  - No per-connection reconnection logic.
  - No multi-client multiplexing – it’s designed for a single 1:1 tunnel at a time.

---

## License

Pick any license that fits your use case (MIT, Apache-2.0, etc.).  
Until then: use at your own risk 😄
