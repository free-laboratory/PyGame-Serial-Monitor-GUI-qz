import json
import socket
from typing import List

HOST = "127.0.0.1"
PORT = 5555

_sock = None


def _connect():
    global _sock
    if _sock is not None:
        return _sock

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    _sock = s
    return _sock


def send_joint_positions(joints: List[float]) -> None:
    s = _connect()
    msg = {
        "type": "joint",
        "positions": joints,
    }
    payload = (json.dumps(msg) + "\n").encode("utf-8")
    s.sendall(payload)