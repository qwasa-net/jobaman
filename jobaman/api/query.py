import json
import urllib.parse as urlparse
from collections import namedtuple

Query = namedtuple(
    "Query",
    ["addr", "method", "path", "params", "headers", "data"],
    defaults=[None, None, None, None, None, None],
)


def parse_http_request(request: str, addr=None) -> Query:

    header, _, body = request.partition("\r\n\r\n")
    lines = header.split("\r\n")
    command = lines[0] if lines else ""
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    method, path, qs_params = parse_http_command(command)

    data = json.loads(body) if body else None

    return Query(
        addr=addr,
        method=method,
        path=path,
        params=qs_params,
        headers=headers,
        data=data,
    )


def parse_http_command(command: str):
    parts = command.split()
    method = parts[0].upper()
    uri = parts[1]
    urlp = urlparse.urlparse(uri)
    path = urlp.path
    qs = urlparse.parse_qs(urlp.query, keep_blank_values=True, strict_parsing=True)
    return method, path, qs


def params_to_args(params):
    args = []
    for key in sorted(map(str, params.keys()), key=lambda k: (not k.startswith("_"), k)):
        if key.startswith("__"):
            continue
        values = params[key]
        if key.startswith("_") and key[1:].isdigit() and len(key) > 1:
            for v in values:
                args.append(v)
        else:
            for v in values:
                if v == "":
                    args.append(f"{key}")
                else:
                    args.append(f"{key}={v}")
    return args
