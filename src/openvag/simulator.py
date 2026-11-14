"""Deterministic ELM327 simulator for tests and CLI demonstration only."""

import re
from typing import Dict, Iterable, List, Optional, Union

from .transport import LineTransport

Reply = Union[str, Iterable[str]]


class SimulatedElm327Transport(LineTransport):
    """A simulator, not evidence of compatibility with a vehicle or adapter."""

    def __init__(self, replies: Optional[Dict[str, Reply]] = None) -> None:
        self.replies = replies if replies is not None else {
            "ATZ": "ELM327 vSIM 1.0",
            "ATE0": "OK",
            "ATL0": "OK",
            "ATS0": "OK",
            "ATH0": "OK",
            "ATSP0": "OK",
            "ATI": "ELM327 vSIM 1.0",
            "AT@1": "OBDII to RS232 Interpreter",
            "ATDPN": "A6",
            "0100": "41 00 BE 3E B8 13",
            "010C": "41 0C 1A F8",
            "010D": "41 0D 28",
            "03": "43 00 00",
        }
        self.closed = False

    def request(self, command: str, timeout_seconds: float) -> List[str]:
        reply = self.replies.get(command, "NO DATA")
        if isinstance(reply, str):
            parts = re.split(r"[\r\n]+", reply)
        else:
            parts = list(reply)
        return [part.strip() for part in parts if part.strip()]

    def close(self) -> None:
        self.closed = True
