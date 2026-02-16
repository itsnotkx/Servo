from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import json
import urllib.error
import urllib.request

from .errors import ServoAPIError, ServoConnectionError


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


@dataclass
class HTTPClient:
    base_url: str
    api_key: str | None
    timeout_s: float

    def request_json(
        self,
        method: str,
        path: str,
        json_body: Mapping[str, Any] | None = None,
    ) -> Any:
        url = _join_url(self.base_url, path)
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body_bytes: bytes | None = None
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url=url, method=method.upper(), data=body_bytes, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                status = getattr(resp, "status", None) or resp.getcode()
                content_type = (resp.headers.get("content-type") or "").lower()
                raw = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read()
            content_type = (e.headers.get("content-type") or "").lower()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ServoConnectionError(message=f"Failed to connect to {url}", cause=e) from e

        data: Any | None = None
        text = raw.decode("utf-8", errors="replace")
        if "application/json" in content_type:
            try:
                data = json.loads(text) if text else None
            except ValueError:
                data = None

        if status < 200 or status >= 300:
            raise ServoAPIError(
                message=f"Servo API error ({status}) for {method} {path}",
                status_code=int(status),
                body=data if data is not None else text,
            )

        return data if data is not None else text

