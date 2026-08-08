#!/usr/bin/env python3
"""Protocol-level join test for the Eturlia core.

Reproduces what a NeoForge client does up to the configuration phase and asserts that the two
failures reported from the field are gone:

  1. "You are trying to connect to a server that is not using NeoForge, but you have mods that
     require it" — the client raises this when the server never announces the modded network, so
     the test asserts the server sends NeoForge's negotiation payloads during configuration.
  2. "Internal Exception: java.lang.UnsupportedOperationException" — asserts the connection is
     never closed with an exception disconnect during login/configuration.

No Minecraft libraries involved: this speaks the wire protocol directly (1.21.1, protocol 767).

Usage: join_test.py [host] [port] [player-name]
Exit code 0 = both checks passed.
"""
import json
import socket
import struct
import sys
import time
import uuid

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2] if len(sys.argv) > 2 else 25565)
NAME = sys.argv[3] if len(sys.argv) > 3 else "EturliaProbe"
PROTOCOL = 767  # 1.21.1

# NeoForge channels the server must announce for a modded client to accept the connection.
NEOFORGE_MARKERS = ("neoforge:", "fml:", "minecraft:register", "minecraft:unregister")

# When true the probe answers the server's modded query, i.e. behaves like a NeoForge client.
NEOFORGE_MODE = "--vanilla" not in sys.argv


# ----------------------------------------------------------------- varint / packet plumbing

def varint(value):
    out = b""
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out += bytes((b | 0x80,))
        else:
            out += bytes((b,))
            return out


def read_varint(sock):
    num = 0
    for i in range(5):
        b = recv_exact(sock, 1)[0]
        num |= (b & 0x7F) << (7 * i)
        if not b & 0x80:
            return num
    raise IOError("varint too long")


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise IOError("connection closed by server")
        buf += chunk
    return buf


def pstring(s):
    data = s.encode("utf-8")
    return varint(len(data)) + data


# Set by the Set Compression packet; -1 means "no compression yet".
COMPRESSION = {"threshold": -1}


def send_packet(sock, packet_id, payload=b""):
    body = varint(packet_id) + payload
    if COMPRESSION["threshold"] >= 0:
        # Compressed framing: length, then uncompressed-size (0 = stored), then data.
        if len(body) >= COMPRESSION["threshold"]:
            import zlib
            comp = zlib.compress(body)
            frame = varint(len(body)) + comp
        else:
            frame = varint(0) + body
        sock.sendall(varint(len(frame)) + frame)
        return
    sock.sendall(varint(len(body)) + body)


def read_packet(sock, timeout=10.0):
    sock.settimeout(timeout)
    length = read_varint(sock)
    data = recv_exact(sock, length)
    if COMPRESSION["threshold"] >= 0:
        # Strip the uncompressed-size prefix and inflate when it is non-zero.
        size = 0
        off = 0
        for i in range(5):
            b = data[off]
            size |= (b & 0x7F) << (7 * i)
            off += 1
            if not b & 0x80:
                break
        data = data[off:]
        if size:
            import zlib
            data = zlib.decompress(data)
    # packet id is a varint at the head of data
    idx = 0
    pid = 0
    for i in range(5):
        b = data[idx]
        pid |= (b & 0x7F) << (7 * i)
        idx += 1
        if not b & 0x80:
            break
    return pid, data[idx:]


def read_pstring(data, off=0):
    n = 0
    for i in range(5):
        b = data[off]
        n |= (b & 0x7F) << (7 * i)
        off += 1
        if not b & 0x80:
            break
    return data[off:off + n].decode("utf-8", "replace"), off + n


# ----------------------------------------------------------------- phases

def handshake(sock, next_state):
    payload = varint(PROTOCOL) + pstring(HOST) + struct.pack(">H", PORT) + varint(next_state)
    send_packet(sock, 0x00, payload)


def do_status():
    """Server list ping — also reports the brand the server advertises."""
    s = socket.create_connection((HOST, PORT), timeout=10)
    try:
        handshake(s, 1)
        send_packet(s, 0x00)
        pid, data = read_packet(s)
        text, _ = read_pstring(data)
        return json.loads(text)
    finally:
        s.close()


def do_login():
    """Login + configuration phase. Returns (payload_channels, disconnect_reason)."""
    s = socket.create_connection((HOST, PORT), timeout=15)
    channels = []
    disconnect = None
    try:
        handshake(s, 2)
        # Login Start: name + uuid
        send_packet(s, 0x00, pstring(NAME) + uuid.uuid5(uuid.NAMESPACE_OID, NAME).bytes)

        deadline = time.time() + 25
        state = "login"
        while time.time() < deadline:
            try:
                pid, data = read_packet(s, timeout=8)
            except (IOError, socket.timeout) as e:
                disconnect = disconnect or "connection ended: %s" % e
                break

            if state == "login":
                if pid == 0x00:  # login disconnect
                    disconnect, _ = read_pstring(data)
                    break
                if pid == 0x01:  # encryption request -> online mode, cannot continue
                    disconnect = "ENCRYPTION_REQUEST (server is in online-mode)"
                    break
                if pid == 0x02:  # login success
                    send_packet(s, 0x03)  # login acknowledged -> configuration
                    state = "config"
                    # Deliberately no Client Information: the modded negotiation happens before it,
                    # and an over-specified packet here only risks desyncing the probe.
                    continue
                if pid == 0x03:  # set compression
                    threshold = 0
                    off = 0
                    for i in range(5):
                        b = data[off]
                        threshold |= (b & 0x7F) << (7 * i)
                        off += 1
                        if not b & 0x80:
                            break
                    COMPRESSION["threshold"] = threshold
                    print("compression enabled at threshold %d" % threshold)
                    continue
                if pid == 0x04:  # login plugin request
                    # answer "unknown" so the server keeps going
                    msg_id = 0
                    off = 0
                    for i in range(5):
                        b = data[off]
                        msg_id |= (b & 0x7F) << (7 * i)
                        off += 1
                        if not b & 0x80:
                            break
                    send_packet(s, 0x02, varint(msg_id) + b"\x00")
                    continue
            else:  # configuration phase
                if pid == 0x02:  # disconnect
                    disconnect, _ = read_pstring(data)
                    break
                if pid == 0x01:  # clientbound custom payload
                    channel, _ = read_pstring(data)
                    channels.append(channel)
                    if channel == "neoforge:register" and NEOFORGE_MODE:
                        # A NeoForge client answers the query on the same channel. An empty map
                        # (varint 0) means "no extra channels", which is what a client with only
                        # server-side mods sends. This is what flips the server from
                        # initializeOtherConnection() to initializeNeoForgeConnection().
                        send_packet(s, 0x02, pstring("neoforge:register") + varint(0))
                        print("  -> answered as a NeoForge client")
                    continue
                if pid == 0x03:  # finish configuration
                    send_packet(s, 0x03)  # acknowledge -> play
                    break
                if pid == 0x05:  # clientbound ping -> serverbound pong is 0x05 in configuration
                    send_packet(s, 0x05, data[:4])
                    continue
                if pid == 0x04:  # keep alive
                    send_packet(s, 0x04, data[:8])
                    continue
                if pid == 0x07:  # registry data — the handshake already happened by now
                    continue
                continue
    finally:
        s.close()
    return channels, disconnect


def main():
    print("=== Eturlia join probe -> %s:%d as %s ===" % (HOST, PORT, NAME))
    failures = []

    try:
        status = do_status()
        version = status.get("version", {})
        print("status: %s (protocol %s)" % (version.get("name"), version.get("protocol")))
        players = status.get("players", {})
        print("players: %s/%s" % (players.get("online"), players.get("max")))
        if version.get("protocol") != PROTOCOL:
            print("  note: protocol differs from %d" % PROTOCOL)
    except Exception as e:
        failures.append("status ping failed: %s" % e)
        print("status ping FAILED: %s" % e)

    try:
        channels, disconnect = do_login()
    except Exception as e:
        print("login FAILED: %s" % e)
        failures.append("login threw: %s" % e)
        channels, disconnect = [], str(e)

    print("\nconfiguration payloads received: %d" % len(channels))
    for c in channels:
        print("  %s" % c)

    modded = [c for c in channels if any(m in c for m in NEOFORGE_MARKERS)]

    print("\n--- checks ---")
    if disconnect:
        print("disconnect reason: %s" % disconnect)

    # check 1: NeoForge announcement
    if modded:
        print("PASS  server announces the modded network (%d payload(s): %s)"
              % (len(modded), ", ".join(sorted(set(modded))[:4])))
    else:
        print("FAIL  no NeoForge/register payloads — a modded client would refuse with"
              " \"server is not using NeoForge\"")
        failures.append("no modded network announcement")

    # check 1b: a NeoForge client must not be rejected for missing NeoForge
    if NEOFORGE_MODE:
        if disconnect and "not" in disconnect.lower() and "neoforge" in disconnect.lower():
            print("FAIL  server rejected a NeoForge-speaking client: %s" % disconnect)
            failures.append("modded client rejected")
        else:
            print("PASS  NeoForge-speaking client was not rejected for missing NeoForge")

    # check 2: no UnsupportedOperationException / internal error
    if disconnect and ("UnsupportedOperationException" in disconnect
                       or "Internal Exception" in disconnect):
        print("FAIL  connection died with an internal exception: %s" % disconnect)
        failures.append("internal exception on connect")
    else:
        print("PASS  no UnsupportedOperationException during login/configuration")

    print("\n%s" % ("ALL CHECKS PASSED" if not failures else "FAILED: " + "; ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
