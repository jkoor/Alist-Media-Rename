import pyotp
import requests
from functools import wraps
from .models import ApiResponseModel
from .utils import Message


# 封装接口返回信息
class ApiResponse:
    """
    封装接口返回信息
    """

    @staticmethod
    def alist_api_response(func):
        """
        封装Alist api返回信息.
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            rawdata = func(*args, **kwargs)

            if rawdata["message"] == "success":
                return ApiResponseModel(
                    success=True,
                    status_code=rawdata["code"],
                    error="",
                    data=rawdata["data"],
                )
            else:
                return ApiResponseModel(
                    success=False,
                    status_code=rawdata["code"],
                    error=rawdata["message"],
                    data=rawdata["data"],
                )

        return wrapper

    @staticmethod
    def tmdb_api_response(func):
        """
        封装TMDB api返回信息装饰器.
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            rawdata, status_code = func(*args, **kwargs)

            if status_code == 200:
                return ApiResponseModel(
                    success=True, status_code=status_code, error="", data=rawdata
                )
            else:
                return ApiResponseModel(
                    success=False,
                    status_code=status_code,
                    error=rawdata.get("status_message", ""),
                    data=rawdata,
                )

        return wrapper


class AlistApi:
    """
    Alist请求函数, 包含: 登录/获取文件列表/重命名文件/删除文件/新建文件夹/上传文件/获取下载链接/获取存储驱动信息
    Alist api非官方说明文档(来自网友分享): https://zhuanlan.zhihu.com/p/587004798
    """

    def __init__(
        self, url: str, user: str = "", password: str = "", totp_code: str = ""
    ):
        """
        初始化参数.

        :param url: Alist 主页链接
        :param user: Alist 登录账号
        :param password: Alist 登录密码
        :param totp_code: Alist 2FA 验证码
        """

        self.url = url.rstrip("/")
        self.user = user
        self.password = password
        # 使用self.totp_code.now() 生成实时 TOTP 验证码
        self.totp_code = pyotp.TOTP(totp_code)
        self.login_success = False
        self.token = ""
        self.timeout = 10
        self.silence = False

    @Message.output_alist_login
    @ApiResponse.alist_api_response
    def login(self) -> dict:
        """
        获取登录Token

        :param silent: 是否不显示登录状态信息
        :return: 获取Token请求结果
        """

        # 发送请求
        post_url = self.url + "/api/auth/login"
        post_datas = {
            "Username": self.user,
            "Password": self.password,
            "OtpCode": self.totp_code.now(),
        }
        r = requests.post(url=post_url, data=post_datas, timeout=self.timeout)

        return_data = r.json()

        if return_data["message"] == "success":
            self.token = return_data["data"]["token"]
            self.login_success = True

        # 返回请求结果
        return return_data

    @Message.output_alist_file_list
    @ApiResponse.alist_api_response
    def file_list(
        self,
        path: str = "/",
        password=None,
        refresh: bool = True,
        per_page: int = 0,
        page: int = 1,
    ) -> dict:
        """
        获取文件列表,并格式化输出所有文件名称.

        :param path: 路径, 默认为首页/
        :param password: 路径访问密码, 默认为空
        :param refresh: 是否强制刷新文件夹, 默认为否
        :param per_page: 每页显示文件数量, 默认为0, 获取全部
        :param page: 当前页数, 默认为1;
        :return: 获取文件列表请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/list"
        post_headers = {"Authorization": self.token}
        post_params = {
            "path": path,
            "password": password,
            "refresh": refresh,
            "per_page": per_page,
            "page": page,
        }
        r = requests.post(
            url=post_url, headers=post_headers, params=post_params, timeout=self.timeout
        )

        # 获取请求结果
        return r.json()

    # @Message.output_alist_rename
    @ApiResponse.alist_api_response
    def rename(self, name: str, path: str) -> dict:
        """
        重命名文件/文件夹.

        :param name: 重命名名称
        :param path: 源文件/文件夹路径
        :return: 重命名文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/rename"
        post_headers = {"Authorization": self.token}
        post_json = {"name": name, "path": path}
        r = requests.post(
            url=post_url, headers=post_headers, json=post_json, timeout=self.timeout
        )

        # 获取请求结果
        return r.json()

    @Message.output_alist_move
    @ApiResponse.alist_api_response
    def move(self, names: list, src_dir: str, dst_dir: str) -> dict:
        """
        移动文件/文件夹.
        :param names: 需要移动的文件名称列表
        :param src_dir: 需要移动的源文件所在文件夹
        :param dst_dir: 需要移动的目标文件夹
        :return: 移动文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/move"
        post_headers = {"Authorization": self.token}
        post_json = {"src_dir": src_dir, "dst_dir": dst_dir, "names": names}
        r = requests.post(
            url=post_url, headers=post_headers, json=post_json, timeout=self.timeout
        )
        # 获取请求结果
        return r.json()

    @Message.output_alist_mkdir
    @ApiResponse.alist_api_response
    def mkdir(self, path: str) -> dict:
        """
        新建文件夹.

        :param path: 新建文件夹路径
        :return: 新建文件夹请求结果
        """
        # 发送请求
        post_url = self.url + "/api/fs/mkdir"
        post_headers = {"Authorization": self.token}
        post_json = {"path": path}
        r = requests.post(
            url=post_url, headers=post_headers, json=post_json, timeout=self.timeout
        )
        # 获取请求结果
        return r.json()

    @Message.output_alist_remove
    @ApiResponse.alist_api_response
    def remove(self, path: str, names: list) -> dict:
        """
        删除文件/文件夹.

        :param path: 待删除文件/文件夹所在目录
        :param names: 待删除文件/文件夹列表
        :return: 删除文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/remove"
        post_headers = {"Authorization": self.token}
        post_json = {"dir": path, "names": names}
        r = requests.post(
            url=post_url, headers=post_headers, json=post_json, timeout=self.timeout
        )

        # 获取请求结果
        return r.json()


class TMDBApi:
    """
    调用TMDB api获取剧集相关信息
    TMDB api官方说明文档(https://developers.themoviedb.org/3)
    """

    def __init__(self, api_url: str, api_key: str):
        """
        初始化参数

        :param key: TMDB Api Key(V3)
        """

        self.api_url = "https://api.themoviedb.org/3"
        self.api_key = api_key
        self.timeout = 10

    @Message.output_tmdb_tv_info
    @ApiResponse.tmdb_api_response
    def tv_info(self, tv_id: str, language: str = "zh-CN") -> tuple:
        """
        根据提供的id获取剧集信息.

        :param tv_id: 剧集id
        :param language: TMDB搜索语言
        :return: 请求状态码与剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/tv/{tv_id}"
        post_params = {"api_key": self.api_key, "language": language}
        r = requests.get(post_url, params=post_params, timeout=self.timeout)
        # 获取请求结果
        return r.json(), r.status_code

    @Message.output_tmdb_search_tv
    @ApiResponse.tmdb_api_response
    def search_tv(self, keyword: str, language: str = "zh-CN") -> tuple:
        """
        根据关键字匹配剧集, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language:
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/search/tv"
        post_params = {"api_key": self.api_key, "query": keyword, "language": language}
        r = requests.get(post_url, params=post_params, timeout=self.timeout)

        # 获取请求结果
        return r.json(), r.status_code

    @Message.output_tmdb_tv_season_info
    @ApiResponse.tmdb_api_response
    def tv_season_info(
        self, tv_id: str, season_number: int, language: str = "zh-CN"
    ) -> tuple:
        """
        获取指定季度剧集信息.
        :param tv_id: 剧集id
        :param season_number: 指定第几季
        :param language: TMDB搜索语言
        :return: 返回获取指定季度剧集信息结果
        """

        # 发送请求
        post_url = f"{self.api_url}/tv/{tv_id}/season/{season_number}"
        post_params = {"api_key": self.api_key, "language": language}
        r = requests.get(post_url, params=post_params, timeout=self.timeout)

        # 获取请求结果
        return r.json(), r.status_code

    @Message.output_tmdb_movie_info
    @ApiResponse.tmdb_api_response
    def movie_info(self, movie_id: str, language: str = "zh-CN") -> tuple:
        """
        根据提供的id获取电影信息.

        :param movie_id: 电影id
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果, 不输出内容
        :return: 请求状态码与电影信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/movie/{movie_id}"
        post_params = {"api_key": self.api_key, "language": language}
        r = requests.get(post_url, params=post_params, timeout=self.timeout)

        # 获取请求结果
        return r.json(), r.status_code

    @Message.output_tmdb_search_movie
    @ApiResponse.tmdb_api_response
    def search_movie(self, keyword: str, language: str = "zh-CN") -> tuple:
        """
        根据关键字匹配电影, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language: TMDB搜索语言
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/search/movie"
        post_params = {"api_key": self.api_key, "query": keyword, "language": language}
        r = requests.get(post_url, params=post_params, timeout=self.timeout)

        # 获取请求结果
        return r.json(), r.status_code
