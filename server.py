import os
import socket
import threading

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

def handle_client(conn, addr):
    print(f"Verbunden mit {addr}")
    with conn:
        try:
            buffer = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    print(f"Verbindung mit {addr} geschlossen")
                    break

                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    message = line.decode("utf-8", errors="ignore").strip()

                    if message.lower() == "ping":
                        response = "pong\n"
                        conn.sendall(response.encode("utf-8"))
                    else:
                        response = f"echo:{message}\n"
                        conn.sendall(response.encode("utf-8"))
        except Exception as e:
            print(f"Fehler mit {addr}: {e}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen()
        print(f"TCP-Server läuft auf {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    main()
