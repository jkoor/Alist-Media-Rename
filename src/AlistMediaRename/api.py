import pyotp
import requests
from .utils import PrintMessage

# from requests_toolbelt import MultipartEncoder


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

    @PrintMessage.output_alist_login
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

    @PrintMessage.output_alist_file_list
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

    @PrintMessage.output_alist_rename
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

    @PrintMessage.output_alist_move
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

    @PrintMessage.output_alist_mkdir
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

    @PrintMessage.output_alist_remove
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

    @PrintMessage.output_alist_download_link
    def download_link(self, path: str, password=None) -> dict:
        """
        获取文件下载链接.

        :param path: 文件路径
        :param password: 文件访问密码
        :return: 获取文件下载链接请求结果
        """
        # 发送请求
        post_url = self.url + "/api/fs/get"
        post_headers = {"Authorization": self.token}
        post_json = {"path": path, "password": password}
        r = requests.post(
            url=post_url, headers=post_headers, json=post_json, timeout=self.timeout
        )
        # 获取请求结果
        return r.json()

    def upload(self, path: str, file: str) -> dict:
        """
        上传文件.

        :param path: 上传路径(包含文件) 如/abc/test.txt
        :param file: 源文件路径(包含文件) 如/abc/test.txt
        :return: 返回上传文件请求结果
        """

        print(
            "由于上传文件需要调用第三方库：requests_toolbelt, "
            "而主程序又用不到上传操作, 所以该函数代码被注释掉了, "
            "如有需要请取消代码注释, 并把最上方调用代码取消注释!"
        )
        #     # 发送请求
        #     post_url = self.url + '/api/fs/put'
        #     upload_file = open(file, "rb")
        #     # post_data = MultipartEncoder({upload_file.name: upload_file})
        #     post_data = MultipartEncoder({upload_file.name: upload_file})
        #     post_headers = {
        #         'Authorization': self.token,
        #         'File-path': parse.quote(path),
        #         'Content-Type': post_data.content_type
        #     }
        #     r = requests.put(url=post_url, headers=post_headers, data=post_data)
        #     # 获取请求结果
        #     return_data = r.json()
        #
        #     # 静默返回请求结果,不输出内容
        #     if silent:
        #         return return_data

        # 输出内容提醒颜色
        # failure_msg = colorama.Fore.RED + '\n[Upload●Failure]' + colorama.Fore.RESET
        # success_msg = colorama.Fore.GREEN + '\n[Upload●Success]' + colorama.Fore.RESET

        #     # 输出上传文件请求结果
        #     if return_data['message'] == 'success':
        #         print(f"{success_msg} 上传路径: {path}\t本地路径: {file}")
        #     else:
        #         print(f"{failure_msg} 上传失败: {path}\t本地路径: {file}\n{return_data['message']}")
        #
        #     # 返回请求结果
        #     return return_data

        return {"注意": "查看输出内容"}

    @PrintMessage.output_alist_disk_list
    def disk_list(self) -> dict:
        """
        获取已添加存储列表.

        :return: 获取已添加存储列表请求结果
        """

        # 发送请求
        post_url = self.url + "/api/admin/storage/list"
        post_headers = {"Authorization": self.token}
        r = requests.get(url=post_url, headers=post_headers, timeout=self.timeout)
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

    @PrintMessage.output_tmdb_tv_info
    def tv_info(self, tv_id: str, language: str = "zh-CN") -> dict:
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
        return r.json()

    @PrintMessage.output_tmdb_search_tv
    def search_tv(self, keyword: str, language: str = "zh-CN") -> dict:
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
        return r.json()

    @PrintMessage.output_tmdb_tv_season_info
    def tv_season_info(
        self, tv_id: str, season_number: int, language: str = "zh-CN"
    ) -> dict:
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
        return r.json()

    @PrintMessage.output_tmdb_movie_info
    def movie_info(self, movie_id: str, language: str = "zh-CN") -> dict:
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
        return r.json()

    @PrintMessage.output_tmdb_search_movie
    def search_movie(self, keyword: str, language: str = "zh-CN") -> dict:
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
        return r.json()
