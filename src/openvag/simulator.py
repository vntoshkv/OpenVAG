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
            "ATRV": "12.6V",
            "0100": "41 00 BE 3E B8 13",
            "0101": "41 01 00 07 65 00",
            "0104": "41 04 80",
            "0105": "41 05 5A",
            "0106": "41 06 80",
            "0107": "41 07 80",
            "010B": "41 0B 64",
            "010C": "41 0C 1A F8",
            "010D": "41 0D 28",
            "010E": "41 0E 80",
            "010F": "41 0F 50",
            "0110": "41 10 0C 80",
            "0111": "41 11 40",
            "011F": "41 1F 01 2C",
            "0120": "41 20 80 02 A0 01",
            "0121": "41 21 00 0A",
            "012F": "41 2F 80",
            "0131": "41 31 00 64",
            "0133": "41 33 65",
            "0140": "41 40 44 00 00 14",
            "0142": "41 42 30 39",
            "0146": "41 46 50",
            "015C": "41 5C 5A",
            "015E": "41 5E 03 E8",
            "03": "43 00 00",
            "07": "47 00 00",
            "0A": "4A 00 00",
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
