import logging
import pickle
import signal
import socket
import socketserver
import struct
import subprocess
import threading

from qureed.gui.report import GuiLogHandler


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        gui_handler = GuiLogHandler()
        while True:
            try:
                # Read the length prefix
                length_prefix = self.rfile.read(4)
                if not length_prefix:
                    break

                # Unpack the length prefix to get the data length
                data_length = struct.unpack(">L", length_prefix)[0]

                # Read the actual data of specified length
                data = self.rfile.read(data_length)
                if not data:
                    break

                try:
                    record_dict = pickle.loads(data)
                except (pickle.UnpicklingError, EOFError) as e:
                    print(f"Decoding error: {e}")
                    continue

                try:
                    record = logging.makeLogRecord(record_dict)
                except Exception as e:
                    print(f"Error creating LogRecord: {e}")
                    continue

                logger = logging.getLogger(record.name)
                logger.addHandler(gui_handler)
                logger.handle(record)
            except Exception as e:
                print(f"Error handling log record: {e}")
                break


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, HandlerClass):
        super().__init__(server_address, HandlerClass)
        self.shutdown_requested = False

    def shutdown_server(self):
        print("shutdown requested")
        self.shutdown()  # This will stop serve_forever
        self.server_close()  # This will close the server socket


def start_tcp_server(port):
    server = LogRecordSocketReceiver(("localhost", port), LogRecordStreamHandler)
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
