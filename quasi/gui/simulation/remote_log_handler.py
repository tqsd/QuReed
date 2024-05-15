import threading
import socketserver
import logging
import subprocess
import signal
import socket

from quasi.gui.report import GuiLogHandler

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.rfile.readline()
                if not data:
                    break
                data = data.strip()
                record = logging.makeLogRecord(eval(data))
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except Exception:
                break

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, HandlerClass):
        super().__init__(server_address, HandlerClass)
        self.shutdown_requested = False

    def serve_forever(self, poll_interval=0.5):
        while not self.shutdown_requested:
            self.handle_request()

    def shutdown_server(self):
        self.shutdown_requested = True
        self.server_close()

def start_tcp_server(port):
    server = LogRecordSocketReceiver(('localhost', port), LogRecordStreamHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server, server_thread


def find_free_port(start=49152, end=65535):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise IOError("No free ports available in range.")
