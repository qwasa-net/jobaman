import json
import socket
from concurrent.futures import ThreadPoolExecutor

from jobaman.logger import get_logger

from .handlers import handle
from .query import Query, parse_http_request

log = get_logger(__name__)

MAX_REQUEST_BODY_SIZE = 16 * 1024  # 16 KB
RESPONSE_400 = b"HTTP/1.1 400\r\nConnection: close\r\n\r\n"
RESPONSE_500 = b"HTTP/1.1 500\r\nConnection: close\r\n\r\n"
RESPONSE_200 = (
    "HTTP/1.1 {}\r\n"
    "Connection: close\r\n"
    "Content-Length: {}\r\n"
    "Content-Type: application/json\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "\r\n"
)


def try_handle_client(conn, addr, config):
    try:
        handle_client(conn, addr, config)
    except Exception as e:
        log.error("failed to handle request from [%s:%s]: %s", *addr, e)
        conn.sendall(RESPONSE_500)
    finally:
        conn.close()


def handle_client(conn, addr, config):

    request = conn.recv(MAX_REQUEST_BODY_SIZE).decode("utf-8", errors="ignore")
    query: Query = parse_http_request(request, addr)

    rsp_code, rsp_data = handle(query, config)
    rsp_json = json.dumps(rsp_data, indent=1, ensure_ascii=False).encode("utf-8")
    rsp_json_len = len(rsp_json)

    conn.sendall(RESPONSE_200.format(rsp_code, rsp_json_len).encode())
    conn.sendall(rsp_json)

    log.info("[%s:%s] %s %s - %s", *addr, query.method, query.path, rsp_code)


def run_server(config):

    max_workers = int(config.get("server.max_workers", 4))
    host = config.get("server.host", "127.0.0.1")
    port = int(config.get("server.port", 1954))
    listen_to = (host, port)
    config.http_server_address = f"http://{host}:{port}"

    with (
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server,
        ThreadPoolExecutor(max_workers=max_workers) as executor,
    ):

        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(listen_to)
        server.listen()
        log.info("server started on %s:%d", host, port)

        while True:
            conn, addr = server.accept()
            executor.submit(try_handle_client, conn, addr, config)
