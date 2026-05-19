# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._core._exceptions import ALL_EXCEPTIONS as ALL_EXCEPTIONS
    from ljp_page._core._exceptions import CaptchaException as CaptchaException
    from ljp_page._core._exceptions import ConfigError as ConfigError
    from ljp_page._core._exceptions import EncodingException as EncodingException
    from ljp_page._core._exceptions import HTTPStatusException as HTTPStatusException
    from ljp_page._core._exceptions import LjpBaseException as LjpBaseException
    from ljp_page._core._exceptions import LjpRequestException as LjpRequestException
    from ljp_page._core._exceptions import MaxRetriesException as MaxRetriesException
    from ljp_page._core._exceptions import MeetCheckError as MeetCheckError
    from ljp_page._core._exceptions import NetworkError as NetworkError
    from ljp_page._core._exceptions import NetworkException as NetworkException
    from ljp_page._core._exceptions import No as No
    from ljp_page._core._exceptions import Notfound as Notfound
    from ljp_page._core._exceptions import ParseError as ParseError
    from ljp_page._core._exceptions import ProxyException as ProxyException
    from ljp_page._core._exceptions import ResponseParseException as ResponseParseException
    from ljp_page._core._exceptions import SSLException as SSLException
    from ljp_page._core._exceptions import TimeoutException as TimeoutException
    from ljp_page._core._exceptions import Yes as Yes

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._core._exceptions",
    [
        "ALL_EXCEPTIONS",
        "CaptchaException",
        "ConfigError",
        "LjpBaseException",
        "LjpRequestException",
        "MaxRetriesException",
        "MeetCheckError",
        "NetworkError",
        "NetworkException",
        "No",
        "Notfound",
        "ParseError",
        "ProxyException",
        "ResponseParseException",
        "SSLException",
        "TimeoutException",
        "Yes",
        "EncodingException",
        "HTTPStatusException",
    ],
)
