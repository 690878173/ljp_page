from ljp_page._core.exceptions import NetworkException



class HTTP_Fetch_error(NetworkException):
    message: str = '发送fetch请求失败'
