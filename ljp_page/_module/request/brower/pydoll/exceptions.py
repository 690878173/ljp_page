"""Pydoll 异常类

该模块包含整个 Pydoll 库中使用的所有异常类，
根据其功能和使用模式组织成逻辑类别。
每个类别都使用一个基类来为相关异常提供通用功能。"""


class PydollException(Exception):
    """所有 Pydoll 异常的基类。"""

    message = 'An error occurred in Pydoll'

    def __init__(self, message: str = ''):
        self.message = message or self.message

    def __str__(self):
        return self.message


class ConnectionException(PydollException):
    """与浏览器连接相关的异常的基类。"""

    message = 'A connection error occurred'


class ConnectionFailed(ConnectionException):
    """当无法建立与浏览器的连接时引发。"""

    message = 'Failed to connect to the browser'


class ReconnectionFailed(ConnectionException):
    """当尝试重新连接浏览器失败时引发。"""

    message = 'Failed to reconnect to the browser'


class WebSocketConnectionClosed(ConnectionException):
    """当与浏览器的 WebSocket 连接意外关闭时引发。"""

    message = 'The WebSocket connection is closed'


class NetworkError(ConnectionException):
    """当浏览器通信期间发生一般网络错误时引发。"""

    message = 'A network error occurred'


class BrowserException(PydollException):
    """与浏览器进程管理相关的异常的基类。"""

    message = 'A browser error occurred'


class BrowserNotRunning(BrowserException):
    """尝试与未运行的浏览器交互时引发。"""

    message = 'The browser is not running'


class FailedToStartBrowser(BrowserException):
    """当浏览器进程无法启动时引发。"""

    message = 'Failed to start the browser'


class UnsupportedOS(BrowserException):
    """尝试在不受支持的操作系统上运行时引发。"""

    message = 'Unsupported OS'


class NoValidTabFound(BrowserException):
    """当找不到或创建有效的浏览器选项卡时引发。"""

    message = 'No valid attached tab found'


class InvalidConnectionPort(BrowserException):
    """当提供无效（非正）连接端口时引发。"""

    message = 'Connection port must be a positive integer'


class InvalidWebSocketAddress(BrowserException):
    """当提供或需要但缺少无效的 WebSocket 地址时引发。"""

    message = 'Invalid WebSocket address'


class MissingTargetOrWebSocket(BrowserException):
    """当选项卡既没有目标 ID 也没有可用的 WebSocket 地址时引发。"""

    message = 'Tab has no target ID or WebSocket address'


class ProtocolException(PydollException):
    """与 CDP 协议通信相关的异常的基类。"""

    message = 'A protocol error occurred'


class TopLevelTargetRequired(ProtocolException):
    """当命令只能在顶级目标上执行时引发。"""

    message = 'Command can only be executed on top-level targets.'


class InvalidCommand(ProtocolException):
    """当向浏览器发送无效命令时引发。"""

    message = 'The command provided is invalid'


class InvalidResponse(ProtocolException):
    """当从浏览器收到无效响应时引发。"""

    message = 'The response received is invalid'


class ResendCommandFailed(ProtocolException):
    """当尝试重新发送失败的命令失败时引发。"""

    message = 'Failed to resend the command'


class CommandExecutionTimeout(ProtocolException):
    """命令执行超时时引发。"""

    message = 'The command execution timed out'


class InvalidCallback(ProtocolException):
    """当为事件提供无效回调时引发。"""

    message = 'The callback provided is invalid'


class EventNotSupported(ProtocolException):
    """当尝试订阅不受支持的事件时引发。"""

    message = 'The event is not supported'


class ElementException(PydollException):
    """与元素交互相关的异常的基类。"""

    message = 'An element interaction error occurred'


class ElementNotFound(ElementException):
    """当在 DOM 中找不到元素时引发。"""

    message = 'The specified element was not found'


class ElementNotVisible(ElementException):
    """尝试与不可见的元素交互时引发。"""

    message = 'The element is not visible'


class ElementNotInteractable(ElementException):
    """当尝试与无法接收交互的元素交互时引发。"""

    message = 'The element is not interactable'


class ClickIntercepted(ElementException):
    """当单击操作被另一个元素拦截时引发。"""

    message = 'The click was intercepted'


class ElementNotAFileInput(ElementException):
    """尝试在非文件输入元素上使用文件输入方法时引发。"""

    message = 'The element is not a file input'


class ShadowRootNotFound(ElementException):
    """当元素没有附加的影子根时引发。"""

    message = 'No shadow root attached to this element'


class TimeoutException(PydollException):
    """与超时相关的异常的基类。"""

    message = 'A timeout occurred'


class PageLoadTimeout(TimeoutException):
    """当页面加载操作超时时引发。"""

    message = 'Page load timed out'


class WaitElementTimeout(TimeoutException):
    """当等待元素超时时引发。"""

    message = 'Timed out waiting for element to appear'


class DownloadTimeout(TimeoutException):
    """等待文件下载完成超时时引发。"""

    message = 'Timed out waiting for download to complete'


class NavigationError(PydollException):
    """当页面导航失败（例如 DNS 解析失败）时引发。"""

    def __init__(self, url: str, error_text: str):
        self.url = url
        self.error_text = error_text
        super().__init__(
            message=f'Navigation to {url} failed: {error_text}',
        )


class ConfigurationException(PydollException):
    """与配置和选项相关的异常的基类。"""

    message = 'A configuration error occurred'


class InvalidOptionsObject(ConfigurationException):
    """当提供无效的选项对象时引发。"""

    message = 'The options object provided is invalid'


class InvalidBrowserPath(ConfigurationException):
    """当提供无效的浏览器可执行路径时引发。"""

    message = 'The browser path provided is invalid'


class ArgumentAlreadyExistsInOptions(ConfigurationException):
    """尝试向浏览器选项添加重复参数时引发。"""

    message = 'The argument already exists in the options'


class ArgumentNotFoundInOptions(ConfigurationException):
    """尝试删除浏览器选项中不存在的参数时引发。"""

    message = 'The argument does not exist in the options'


class InvalidFileExtension(ConfigurationException):
    """当提供不受支持的文件扩展名时引发。"""

    message = 'The file extension provided is not supported'


class InvalidTabInitialization(ConfigurationException):
    """创建没有 connection_port、target_id 或 ws_address 的选项卡时引发。"""

    message = 'Either connection_port, target_id, or ws_address must be provided'


class MissingScreenshotPath(ConfigurationException):
    """当在没有路径的情况下调用 take_screenshot 且不返回 base64 时引发。"""

    message = 'path is required when as_base64 is False'


class DialogException(PydollException):
    """与浏览器对话框相关的异常的基类。"""

    message = 'A dialog error occurred'


class NoDialogPresent(DialogException):
    """尝试与不存在的对话框交互时引发。"""

    message = 'No dialog present on the page'


class NotAnIFrame(PydollException):
    """当元素不是 iframe 时引发。"""

    message = 'The element is not an iframe'


class InvalidIFrame(PydollException):
    """当 iframe 无效时引发。"""

    message = 'The iframe is not valid'


class IFrameNotFound(PydollException):
    """未找到 iframe 时引发。"""

    message = 'The iframe was not found'


class NetworkEventsNotEnabled(PydollException):
    """未启用网络事件时引发。"""

    message = 'Network events not enabled'


class RequestException(PydollException):
    """与 HTTP 请求相关的异常的基类。"""

    message = 'An HTTP request error occurred'


class HTTPError(RequestException):
    """HTTP 错误响应（4xx 和 5xx 状态代码）引发异常。"""

    message = 'An HTTP error occurred'


class HarRecordingError(RequestException):
    """HAR 记录失败时引发。"""

    message = 'HAR recording error occurred'


class ScriptException(PydollException):
    """与 JavaScript 执行相关的异常的基类。"""

    message = 'A script execution error occurred'


class InvalidScriptWithElement(ScriptException):
    """当脚本包含“参数”但未提供元素时引发。"""

    message = 'Script contains "argument" but no element was provided'


class WrongPrefsDict(PydollException):
    """当提供的首选项字典包含“首选项”键时引发"""

    message = 'The dict can not contain "prefs" key, provide only the prefs options'


class ElementPreconditionError(ElementException):
    """当为元素操作提供无效或缺少前提条件时引发。"""

    message = 'Invalid element preconditions'
