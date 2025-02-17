import httpx
import pyotp

from .task import ApiTask, taskManager


class AlistApi:
    """
    Alist请求函数, 包含: 登录/获取文件列表/重命名文件/删除文件/新建文件夹/上传文件/获取下载链接/获取存储驱动信息
    Alist api官方文档: https://alist-v3.apifox.cn/
    """

    def __init__(
        self,
        url: str,
        user: str = "",
        password: str = "",
        totp_code: str = "",
        token: str = "",
    ):
        """
        初始化参数

        :param url: Alist网址
        :param user: 用户名
        :param password: 密码
        :param totp_code: totp验证码
        :param token: Token
        """

        self.url = url
        self.user = user
        self.password = password
        self.totp_code = totp_code
        self._token = self.get_token(token)

    def get_token(self, token) -> str:
        """
        获取Token

        :return: Token
        """
        if token != "":
            return token
        else:
            taskManager.add_tasks(self.login())
            (result,) = taskManager.run_sync()
            return result.data["token"]

    @ApiTask.create("alist", "login", raise_error=True)
    def login(self) -> httpx.Request:
        """
        获取登录Token

        :return: 获取Token请求结果
        """

        # 发送请求
        post_url = self.url + "/api/auth/login"
        post_datas = {
            "Username": self.user,
            "Password": self.password,
            "OtpCode": pyotp.TOTP(self.totp_code).now(),
        }

        return httpx.Request("POST", post_url, data=post_datas)

    @ApiTask.create("alist", "file_list", raise_error=True)
    def file_list(
        self,
        path: str = "/",
        password=None,
        refresh: bool = True,
        per_page: int = 0,
        page: int = 1,
    ) -> httpx.Request:
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
        post_headers = {"Authorization": self._token}
        post_params = {
            "path": path,
            "password": password,
            "refresh": refresh,
            "per_page": per_page,
            "page": page,
        }
        return httpx.Request("POST", post_url, headers=post_headers, json=post_params)

    @ApiTask.create("alist", "slient", raise_error=False)
    def rename(self, name: str, path: str) -> httpx.Request:
        """
        重命名文件/文件夹.

        :param name: 重命名名称
        :param path: 源文件/文件夹路径
        :return: 重命名文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/rename"
        post_headers = {"Authorization": self._token}
        post_json = {"name": name, "path": path}
        return httpx.Request("POST", post_url, headers=post_headers, json=post_json)

    @ApiTask.create("alist", "move", raise_error=False)
    def move(self, names: list, src_dir: str, dst_dir: str) -> httpx.Request:
        """
        移动文件/文件夹.
        :param names: 需要移动的文件名称列表
        :param src_dir: 需要移动的源文件所在文件夹
        :param dst_dir: 需要移动的目标文件夹
        :return: 移动文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/move"
        post_headers = {"Authorization": self._token}
        post_json = {"src_dir": src_dir, "dst_dir": dst_dir, "names": names}
        return httpx.Request("POST", post_url, headers=post_headers, json=post_json)

    @ApiTask.create("alist", "mkdir", raise_error=False)
    def mkdir(self, path: str) -> httpx.Request:
        """
        新建文件夹.

        :param path: 新建文件夹路径
        :return: 新建文件夹请求结果
        """
        # 发送请求
        post_url = self.url + "/api/fs/mkdir"
        post_headers = {"Authorization": self._token}
        post_json = {"path": path}
        return httpx.Request("POST", post_url, headers=post_headers, json=post_json)

    @ApiTask.create("alist", "remove", raise_error=False)
    def remove(self, path: str, names: list) -> httpx.Request:
        """
        删除文件/文件夹.

        :param path: 待删除文件/文件夹所在目录
        :param names: 待删除文件/文件夹列表
        :return: 删除文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + "/api/fs/remove"
        post_headers = {"Authorization": self._token}
        post_json = {"dir": path, "names": names}
        return httpx.Request("POST", post_url, headers=post_headers, json=post_json)


class TMDBApi:
    """
    调用TMDB api获取剧集相关信息
    TMDB api官方说明文档(https://developers.themoviedb.org/3)
    """

    def __init__(self, api_key: str, api_url: str = "https://api.themoviedb.org/3"):
        """
        初始化参数

        :param key: TMDB Api Key(V3)
        :param url: TMDB Api URL
        """

        self.api_url = api_url
        self.api_key = api_key
        self.timeout = 10

    @ApiTask.create("tmdb", "tv_info", raise_error=True)
    def tv_info(self, tv_id: str, language: str = "zh-CN") -> httpx.Request:
        """
        根据提供的id获取剧集信息.

        :param tv_id: 剧集id
        :param language: TMDB搜索语言
        :return: 请求状态码与剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/tv/{tv_id}"
        post_params = {"api_key": self.api_key, "language": language}
        return httpx.Request("GET", post_url, params=post_params)

    @ApiTask.create("tmdb", "search_tv", raise_error=True)
    def search_tv(self, keyword: str, language: str = "zh-CN") -> httpx.Request:
        """
        根据关键字匹配剧集, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language:
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/search/tv"
        post_params = {"api_key": self.api_key, "query": keyword, "language": language}
        return httpx.Request("GET", post_url, params=post_params)

    @ApiTask.create("tmdb", "tv_season_info", raise_error=True)
    def tv_season_info(
        self, tv_id: str, season_number: int, language: str = "zh-CN"
    ) -> httpx.Request:
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
        return httpx.Request("GET", post_url, params=post_params)

    @ApiTask.create("tmdb", "movie_info", raise_error=True)
    def movie_info(self, movie_id: str, language: str = "zh-CN") -> httpx.Request:
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
        return httpx.Request("GET", post_url, params=post_params)

    @ApiTask.create("tmdb", "search_movie", raise_error=True)
    def search_movie(self, keyword: str, language: str = "zh-CN") -> httpx.Request:
        """
        根据关键字匹配电影, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language: TMDB搜索语言
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = f"{self.api_url}/search/movie"
        post_params = {"api_key": self.api_key, "query": keyword, "language": language}
        return httpx.Request("GET", post_url, params=post_params)
