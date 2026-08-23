"""HTTP requests executed inside an asynchronous Playwright page session."""

from __future__ import annotations

import json as jsonlib
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..base.model import FetchResult
from ..exceptions import HTTP_Fetch_error

if TYPE_CHECKING:
    from .page import Ljp_Page

__all__ = ["FetchError", "FetchRequest"]

_FETCH_SCRIPT = """
async ({url, options, timeout}) => {
    const controller = new AbortController();
    let timer = null;
    if (timeout !== null) {
        timer = setTimeout(() => controller.abort(), timeout);
    }
    try {
        const requestOptions = {
            ...options,
            credentials: options.credentials ?? 'include',
            signal: controller.signal
        };
        if (requestOptions.bodyBytes) {
            requestOptions.body = new Uint8Array(requestOptions.bodyBytes);
            delete requestOptions.bodyBytes;
        }
        const response = await fetch(url, requestOptions);
        const headers = {};
        response.headers.forEach((value, key) => { headers[key] = value; });
        const content = Array.from(new Uint8Array(await response.arrayBuffer()));
        let cookies = '';
        try { cookies = document.cookie; } catch (_) {}
        return {url: response.url, status: response.status, headers, content, cookies};
    } catch (error) {
        return {error: String(error), url, status: 0, headers: {}, content: []};
    } finally {
        if (timer !== null) clearTimeout(timer);
    }
}
"""


class FetchError(HTTP_Fetch_error):
    """A browser-context fetch failed before an HTTP response was received."""


class FetchRequest:
    """Requests that inherit the page's cookie jar and authenticated browser state."""

    def __init__(self, page: "Ljp_Page") -> None:
        self.page = page
        self.verify_gate: Any = None

    def set_verify_gate(self, gate: Any) -> None:
        self.verify_gate = gate

    async def get(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> FetchResult:
        return await self.request("OPTIONS", url, **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        data: Mapping[str, Any] | Sequence[tuple[str, Any]] | str | bytes | None = None,
        json: Any = None,
        headers: Mapping[str, str] | Sequence[Mapping[str, str]] | None = None,
        timeout: float | None = None,
        check_fp: bool = True,
        verify_response: bool | None = None,
        verify_max_retries: int | None = None,
        **options: Any,
    ) -> FetchResult:
        """Execute a Fetch API request in the current page's JavaScript world."""
        if data is not None and json is not None:
            raise ValueError("data and json cannot be used together")
        final_url = _with_params(url, params)
        allow_redirects = options.pop("allow_redirects", None)
        if allow_redirects is not None:
            options["redirect"] = "follow" if allow_redirects else "manual"
        request_options = _build_options(
            method, data=data, json_data=json, headers=headers, **options
        )
        timeout_ms = None if timeout is None else max(0, int(timeout * 1000))

        async def send() -> FetchResult:
            result = await self.page.evaluate(
                _FETCH_SCRIPT,
                {"url": final_url, "options": request_options, "timeout": timeout_ms},
            )
            return _as_fetch_result(result)

        if self.verify_gate is None:
            return await send()
        return await self.verify_gate.run(
            send,
            context={
                "page": self.page,
                "request": self,
                "method": method.upper(),
                "url": final_url,
            },
            verify_response=check_fp if verify_response is None else verify_response,
            max_retries=verify_max_retries,
        )


def _with_params(url: str, params: Mapping[str, str] | None) -> str:
    if not params:
        return url
    parsed = urlsplit(url)
    query = list(parse_qsl(parsed.query, keep_blank_values=True))
    query.extend((str(key), str(value)) for key, value in params.items())
    return urlunsplit(parsed._replace(query=urlencode(query)))


def _build_options(
    method: str,
    *,
    data: Mapping[str, Any] | Sequence[tuple[str, Any]] | str | bytes | None,
    json_data: Any,
    headers: Mapping[str, str] | Sequence[Mapping[str, str]] | None,
    **options: Any,
) -> dict[str, Any]:
    result = {"method": method.upper(), **options}
    result["headers"] = _headers_to_dict(headers)
    if json_data is not None:
        result["body"] = jsonlib.dumps(json_data, ensure_ascii=False)
        result["headers"].setdefault("content-type", "application/json")
    elif isinstance(data, bytes):
        result["bodyBytes"] = list(data)
    elif isinstance(data, Mapping) or _is_tuple_sequence(data):
        result["body"] = urlencode(data, doseq=True)
        result["headers"].setdefault("content-type", "application/x-www-form-urlencoded")
    elif data is not None:
        result["body"] = data
    return result


def _headers_to_dict(
    headers: Mapping[str, str] | Sequence[Mapping[str, str]] | None,
) -> dict[str, str]:
    if headers is None:
        return {}
    if isinstance(headers, Mapping):
        return {str(key): str(value) for key, value in headers.items()}
    return {str(item["name"]): str(item["value"]) for item in headers}


def _is_tuple_sequence(data: Any) -> bool:
    return isinstance(data, Sequence) and not isinstance(data, str) and all(
        isinstance(item, tuple) and len(item) == 2 for item in data
    )


def _as_fetch_result(value: Any) -> FetchResult:
    if not isinstance(value, Mapping) or value.get("error"):
        message = value.get("error") if isinstance(value, Mapping) else repr(value)
        raise FetchError(f"Browser fetch failed: {message}")
    try:
        content = bytes(value.get("content", ()))
        return FetchResult(
            url=str(value["url"]),
            status=int(value["status"]),
            headers={str(key): str(item) for key, item in dict(value.get("headers", {})).items()},
            content=content,
            cookies=str(value.get("cookies", "")),
            source=value,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise FetchError("Browser fetch returned an invalid response") from error
