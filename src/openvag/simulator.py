"""Deterministic ELM327 simulator for tests and CLI demonstration only."""

from typing import Dict, Optional

from .transport import LineTransport


class SimulatedElm327Transport(LineTransport):
    """A simulator, not evidence of compatibility with a vehicle or adapter."""

    def __init__(self, replies: Optional[Dict[str, str]] = None) -> None:
        self.replies = replies or {
            "ATZ": "ELM327 vSIM 1.0", "ATE0": "OK", "ATL0": "OK", "ATS0": "OK", "ATH0": "OK", "ATSP0": "OK",
            "0100": "41 00 BE 3E B8 13", "010C": "41 0C 1A F8", "010D": "41 0D 28", "03": "43 00 00",
        }
        self.closed = False

    def request(self, command: str, timeout_seconds: float) -> str:
        return self.replies.get(command, "NO DATA")

    def close(self) -> None:
        self.closed = True
