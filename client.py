
import socket
import time

HOST = "DEIN-ENDPOINT-HOST"
PORT = 12345


def main():
    with socket.create_connection((HOST, PORT)) as s:
        print(f"Verbunden mit {HOST}:{PORT}")
        f = s.makefile("rwb", buffering=0)

        while True:
            t0 = time.time()
            # "ping\n" senden
            msg = b"ping\n"
            f.write(msg)

            # Antwortzeile lesen
            line = f.readline()
            if not line:
                print("Server hat die Verbindung geschlossen.")
                break

            t1 = time.time()
            rtt_ms = (t1 - t0) * 1000.0
            print(f"Antwort: {line.decode().strip()} | RTT: {rtt_ms:.1f} ms")

            time.sleep(1)


if __name__ == "__main__":
    main()
