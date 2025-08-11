import json
import urllib.parse as urlparse
from dataclasses import dataclass, field


@dataclass
class Query:

    addr: tuple | None = None
    method: str | None = None
    path: str | None = None
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    data: dict | None = None

    @classmethod
    def parse_http_request(cls, request: str, addr=None) -> "Query":

        header, _, body = request.partition("\r\n\r\n")
        lines = header.split("\r\n")
        command = lines[0] if lines else ""
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        method, path, params = cls.parse_http_command(command)

        data = json.loads(body) if body else None

        return cls(
            addr=addr,
            method=method,
            path=path,
            params=params,
            headers=headers,
            data=data,
        )

    @staticmethod
    def parse_http_command(command: str) -> tuple[str, str, dict]:
        parts = command.split()
        method = parts[0].upper()
        uri = parts[1]
        urlp = urlparse.urlparse(uri)
        path = urlp.path
        qs = urlparse.parse_qs(urlp.query, keep_blank_values=True, strict_parsing=True)
        return method, path, qs

    def params_to_args(self) -> list[str]:

        if not self.params:
            return []

        args = []
        for key in sorted(map(str, self.params.keys()), key=lambda k: (not k.startswith("_"), k)):
            if key.startswith("__"):
                continue
            values = self.params[key]
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

    def get_param(self, key: str, default=None):
        if not self.params or key not in self.params:
            return default
        values = self.params[key]
        return values[0] if isinstance(values, list) and values else default
