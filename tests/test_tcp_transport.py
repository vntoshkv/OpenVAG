import socket
import socketserver
import threading
import unittest

from openvag.elm327 import Elm327Adapter
from openvag.errors import AdapterUnavailableError, TransportTimeoutError
from openvag.tcp_transport import TcpLineTransport


class _ElmHandler(socketserver.BaseRequestHandler):
    def handle(self):
        server = self.server
        if server.greeting:
            self.request.sendall(b">")
        buffer = b""
        while True:
            chunk = self.request.recv(1024)
            if not chunk:
                return
            buffer += chunk
            while b"\r" in buffer:
                raw, buffer = buffer.split(b"\r", 1)
                command = raw.decode("ascii", errors="replace").strip()
                if not command:
                    continue
                server.commands.append(command)
                if server.silent:
                    continue
                reply = server.replies.get(command, "NO DATA")
                body = "\r".join(reply) if isinstance(reply, (list, tuple)) else reply
                try:
                    self.request.sendall((body + "\r\r>").encode("ascii"))
                except OSError:
                    return


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _FakeElmServer:
    def __init__(self, replies, silent=False, greeting=False):
        self.server = _Server(("127.0.0.1", 0), _ElmHandler)
        self.server.replies = replies
        self.server.commands = []
        self.server.silent = silent
        self.server.greeting = greeting
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.02},
            daemon=True,
        )
        self.thread.start()

    @property
    def host(self):
        return self.server.server_address[0]

    @property
    def port(self):
        return self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class TcpTransportTests(unittest.TestCase):
    def start_server(self, replies, silent=False, greeting=False):
        server = _FakeElmServer(replies, silent=silent, greeting=greeting)
        self.addCleanup(server.close)
        return server

    def test_request_returns_lines_without_prompt(self):
        server = self.start_server({"ATZ": "ELM327 v1.5"})
        transport = TcpLineTransport(server.host, server.port, connect_timeout=1.0)
        self.addCleanup(transport.close)

        self.assertEqual(transport.request("ATZ", 1.0), ["ELM327 v1.5"])
        self.assertEqual(server.server.commands, ["ATZ"])

    def test_adapter_connects_and_reads_values_over_tcp(self):
        replies = {
            "ATZ": "ELM327 v1.5",
            "ATE0": "OK",
            "ATL0": "OK",
            "ATS0": "OK",
            "ATH0": "OK",
            "ATSP0": "OK",
            "ATI": "ELM327 v1.5",
            "AT@1": "OBDII to RS232 Interpreter",
            "ATDPN": "A6",
            "010C": ["41 0C 1A F8", "41 0C 0F A0"],
            "03": "43 00 00",
        }
        server = self.start_server(replies)
        adapter = Elm327Adapter(TcpLineTransport(server.host, server.port, connect_timeout=1.0))
        self.addCleanup(adapter.close)

        capabilities = adapter.connect()
        self.assertEqual(capabilities.version, "ELM327 V1.5")
        self.assertEqual(capabilities.protocol, "A6")
        responses = adapter.request_obd("010C")
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[1].values, (0x41, 0x0C, 0x0F, 0xA0))
        self.assertEqual(adapter.describe_protocol(), "A6")

    def test_initial_greeting_prompt_is_ignored(self):
        server = self.start_server({"ATZ": "ELM327 v1.5"}, greeting=True)
        transport = TcpLineTransport(server.host, server.port, connect_timeout=1.0)
        self.addCleanup(transport.close)

        self.assertEqual(transport.request("ATZ", 1.0), ["ELM327 v1.5"])

    def test_timeout_is_normalized(self):
        server = self.start_server({}, silent=True)
        transport = TcpLineTransport(server.host, server.port, connect_timeout=1.0)
        self.addCleanup(transport.close)

        with self.assertRaises(TransportTimeoutError):
            transport.request("ATZ", 0.2)

    def test_connection_refused_is_adapter_unavailable(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()

        transport = TcpLineTransport("127.0.0.1", port, connect_timeout=0.2)
        self.addCleanup(transport.close)
        with self.assertRaises(AdapterUnavailableError):
            transport.request("ATZ", 0.2)
