from ljp_page.config import RetryConfig,PoolConfig,ProxyConfig,TimeoutConfig,LogConfig,RequestConfig


_JSON_UNSET = object()

class LjpConfig:
    _request = _JSON_UNSET
    _timeout = _JSON_UNSET
    _retry = _JSON_UNSET
    _pool = _JSON_UNSET
    _log = _JSON_UNSET
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def request(self):
        if self._request is _JSON_UNSET:
            self._request = RequestConfig()
        return self._request

    @property
    def timeout(self):
        if self._timeout is _JSON_UNSET:
            pass

        return self._timeout

    @property
    def retry(self):
        if self._retry is _JSON_UNSET:
            self._retry = RetryConfig()
        return self._retry


    @property
    def pool(self):
        if self._pool is _JSON_UNSET:
            self._pool = PoolConfig()
        return self._pool

    @property
    def log(self):
        if self._log is _JSON_UNSET:
            self._log = LogConfig()
        return self._log









