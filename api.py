# -*- coding: utf-8 -*-
# @Time : 2023/4/28/0028 18:10
# @Author : JKOR
# @File : api.py
# @Software: PyCharm

import pyotp
import requests
from natsort import natsorted
# from requests_toolbelt import MultipartEncoder


class AlistApi:
    """
    Alist请求函数, 包含: 登录/获取文件列表/重命名文件/删除文件/新建文件夹/上传文件/获取下载链接/获取存储驱动信息
    """

    def __init__(self, url: str, user: str, password: str, totp_code: str):
        """
        初始化参数.

        :param url: Alist 主页链接
        :param user: Alist 登录账号
        :param password: Alist 登录密码
        :param totp_code: Alist 2FA 验证码
        """

        self.url = url
        self.user = user
        self.password = password
        self.totp_code = pyotp.TOTP(totp_code)  # 使用self.totp_code.now() 生成实时 TOTP 验证码
        self.token = ''
        self.login_status = None
        self.login()

    def login(self, silent: bool = False) -> dict:
        """
        获取登录Token.

        :param silent: 静默返回请求结果,不输出内容
        :return: 获取Token请求结果
        """

        # 发送请求
        post_url = self.url + '/api/auth/login'
        post_datas = dict(Username=self.user,
                          Password=self.password,
                          OtpCode=self.totp_code.now())
        r = requests.post(url=post_url, data=post_datas)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出获取Token结果
        if return_data['message'] != 'success':
            self.login_status = False
            print("\n[Alist Failure✕] Alist登录失败\t2FA验证码: {}\n{}\n".format(
                post_datas['OtpCode'], return_data['message']))
            return return_data
        else:
            self.token = return_data['data']['token']
            self.login_status = True
            print("\n[Alist Success✓] Alist登录成功")

        # 返回请求结果
        return return_data

    def file_list(self,
                  path: str = '/',
                  password=None,
                  refresh: bool = True,
                  per_page: int = 0,
                  page: int = 1,
                  silent: bool = False) -> dict:
        """
        获取文件列表,并格式化输出所有文件名称.

        :param path: 路径, 默认为首页/
        :param password: 路径访问密码, 默认为空
        :param refresh: 是否强制刷新文件夹, 默认为否
        :param per_page: 每页显示文件数量, 默认为0, 获取全部
        :param page: 当前页数, 默认为1;
        :param silent: 静默返回请求结果,不输出内容
        :return: 获取文件列表请求结果
        """

        # 发送请求
        post_url = self.url + '/api/fs/list'
        post_headers = dict(Authorization=self.token)
        post_params = dict(path=path,
                           password=password,
                           refresh=refresh,
                           per_page=per_page,
                           page=page)
        r = requests.post(url=post_url,
                          headers=post_headers,
                          params=post_params)
        # 获取请求结果
        return_data = r.json()

        # 整理排序文件列表
        if return_data['message'] == 'success':
            file_list = return_data['data']['content']
            file_list_0 = list(filter(lambda f: f['is_dir'] is True,
                                      file_list))
            file_list_1 = list(
                filter(lambda f: f['is_dir'] is False, file_list))
            file_list_0 = natsorted(file_list_0, key=lambda x: x['name'])
            file_list_1 = natsorted(file_list_1, key=lambda x: x['name'])

            for i in range(len(file_list_0)):
                # 文件夹信息格式化
                file_list_0[i]['modified'] = "{0}  {1}".format(
                    file_list_0[i]['modified'][:10],
                    file_list_0[i]['modified'][11:19])
                file_list_0[i]['size'] = ""
                file_list_0[i]['name'] = "[{0}]".format(file_list_0[i]['name'])

            for i in range(len(file_list_1)):
                file_list_1[i]['modified'] = "{0}  {1}".format(
                    file_list_1[i]['modified'][:10],
                    file_list_1[i]['modified'][11:19])
                if file_list_1[i]['size'] >= 1000000000:  # 格式化GB级大小文件显示信息
                    file_list_1[i]['size'] = '{0}GB'.format(
                        str(round(file_list_1[i]['size'] / 1073741824, 2)))
                elif file_list_1[i]['size'] >= 1000000:  # 格式化MB级大小文件显示信息
                    file_list_1[i]['size'] = '{0}MB'.format(
                        str(round(file_list_1[i]['size'] / 1048576, 2)))
                elif file_list_1[i]['size'] >= 1000:  # 格式化KB级大小文件显示信息
                    file_list_1[i]['size'] = '{0}KB'.format(
                        str(round(file_list_1[i]['size'] / 1024, 2)))
                else:  # 格式化B级大小文件显示信息
                    file_list_1[i]['size'] = '{0}B'.format(
                        str(file_list_1[i]['size']))

            return_data['folder_list'] = file_list_0
            return_data['file_list'] = file_list_1

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 获取失败则输出相关信息
        if return_data['message'] != 'success':
            print("[Alist Failure✕] 文件列表路径: {0}\n{1}".format(
                path, return_data['message']))
            return return_data

        # 输出格式化文件列表信息
        print("\n[Alist Success✓] 文件列表路径: {0}".format(path))
        print("{:<21s}{:<10s}{:<26s}".format("修改日期", "文件大小", "名    称"))
        print("{:<25s}{:<14s}{:<30s}".format("--------------------",
                                             "--------",
                                             "--------------------"))
        for file in (file_list_0 + file_list_1):
            print("{:<25s}{:<14s}{}".format(file['modified'], file['size'],
                                            file['name']))
        print("\n  文件总数: {0}".format(return_data['data']['total']))
        print("  写入权限: {0}".format(return_data['data']['write']))
        print("  存储来源: {0}\n".format(return_data['data']['provider']))

        # 返回请求结果
        return return_data

    def rename(self, name: str, path: str, silent: bool = False) -> dict:
        """
        重命名文件/文件夹.

        :param name: 重命名名称
        :param path: 源文件/文件夹路径
        :param silent: 静默返回请求结果,不输出内容
        :return: 重命名文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + '/api/fs/rename'
        post_headers = dict(Authorization=self.token)
        post_json = dict(name=name, path=path)
        r = requests.post(url=post_url, headers=post_headers, json=post_json)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出重命名结果
        if return_data['message'] != 'success':
            print("[Alist Failure✕] 重命名路径: {0} -> {1}\n{2}".format(
                path.split('/')[-1], name, return_data['message']))
        else:
            print("[Alist Success✓] 重命名路径:{0} -> {1}".format(path.split('/')[-1], name))

        # 返回请求结果
        return return_data

    def move(self,
             names: list,
             src_dir: str,
             dst_dir: str,
             silent: bool = False) -> dict:
        """
        移动文件/文件夹.
        :param names: 需要移动的文件名称列表
        :param src_dir: 需要移动的源文件所在文件夹
        :param dst_dir: 需要移动的目标文件夹
        :param silent: 静默返回请求结果,不输出内容
        :return: 移动文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + '/api/fs/move'
        post_headers = dict(Authorization=self.token)
        post_json = dict(src_dir=src_dir, dst_dir=dst_dir, names=names)
        r = requests.post(url=post_url, headers=post_headers, json=post_json)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出重命名结果
        if return_data['message'] != 'success':
            print("[Alist Failure✕] 移动失败: {0} -> {1}\n{2}".format(
                src_dir, dst_dir, return_data['message']))
        else:
            print("[Alist Success✓] 移动路径:{0} -> {1}".format(src_dir, dst_dir))

        # 返回请求结果
        return return_data

    def mkdir(self, path: str, silent: bool = False) -> dict:
        """
        新建文件夹.

        :param path: 新建文件夹路径
        :param silent: 静默返回请求结果,不输出内容
        :return: 新建文件夹请求结果
        """
        # 发送请求
        post_url = self.url + '/api/fs/mkdir'
        post_headers = dict(Authorization=self.token)
        post_json = dict(path=path)
        r = requests.post(url=post_url, headers=post_headers, json=post_json)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出新建文件夹请求结果
        if return_data['message'] != 'success':
            print("[Alist Failure✕] 文件夹创建路径: {0}\n{1}".format(
                path, return_data['message']))
        else:
            print("[Alist Success✓] 文件夹创建路径: {0}".format(path))

        # 返回请求结果
        return return_data

    def remove(self, path: str, names: list, silent: bool = False) -> dict:
        """
        删除文件/文件夹.

        :param path: 待删除文件/文件夹所在目录
        :param names: 待删除文件/文件夹列表
        :param silent: 静默返回请求结果,不输出内容
        :return: 删除文件/文件夹请求结果
        """

        # 发送请求
        post_url = self.url + '/api/fs/remove'
        post_headers = dict(Authorization=self.token)
        post_json = dict(dir=path, names=names)
        r = requests.post(url=post_url, headers=post_headers, json=post_json)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果, 不输出消息
        if silent:
            return return_data

        # 输出删除文件/文件夹请求结果
        if return_data['message'] != 'success':
            print("[Alist Failure✕] 删除路径: {0}\n{1}".format(
                path, return_data['message']))
        else:
            for name in names:
                print("[Alist Success✓] 删除路径: {0}/{1}".format(path, name))

        # 返回请求结果
        return return_data

    def download_link(self,
                      path: str,
                      password=None,
                      silent: bool = False) -> dict:
        """
        获取文件下载链接.

        :param path: 文件路径
        :param password: 文件访问密码
        :param silent: 静默返回请求结果,不输出内容
        :return: 获取文件下载链接请求结果
        """
        # 发送请求
        post_url = self.url + '/api/fs/get'
        post_headers = dict(Authorization=self.token)
        post_json = dict(path=path, password=password)
        r = requests.post(url=post_url, headers=post_headers, json=post_json)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出获取下载信息请求结果
        if return_data['message'] == 'success':
            file = return_data['data']
            print("\n[Alist Success✓] 下载文件所在路径: {0}".format(path))
            print(
                "           名称: {0}\n           来源: {1}\n           直链: {2}\n           源链: {3}"
                .format(file['name'], file['provider'], f"{self.url}/d{path}",
                        file['raw_url']))
        else:
            print("[Alist Failure✕] 文件列表路径: {0}\n{1}".format(
                path, return_data['message']))

        # 返回请求结果
        return return_data

    # def upload(self, path: str, file: str, silent: bool = False) -> dict:
    #     """
    #     上传文件.
    #
    #     :param path: 上传路径(包含文件) 如/abc/test.txt
    #     :param file: 源文件路径(包含文件) 如/abc/test.txt
    #     :param silent: 静默返回请求结果,不输出内容
    #     :return: 返回上传文件请求结果
    #     """
    #
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
    #
    #     # 输出上传文件请求结果
    #     if return_data['message'] == 'success':
    #         print("[Alist Success✓] 上传路径: {0}\t本地路径: {1}".format(path, file))
    #     else:
    #         print("[Alist Failure✕] 上传失败路径: {0}\t本地路径: {1}\n{2}".format(
    #             path, file, return_data['message']))
    #
    #     # 返回请求结果
    #     return return_data

    def disk_list(self, silent: bool = False) -> dict:
        """
        获取已添加存储列表.

        :param silent: 静默返回请求结果,不输出内容
        :return: 获取已添加存储列表请求结果
        """

        # 发送请求
        post_url = self.url + '/api/admin/storage/list'
        post_headers = dict(Authorization=self.token)
        r = requests.get(url=post_url, headers=post_headers)
        # 获取请求结果
        return_data = r.json()

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出已添加存储列表请求结果
        if return_data['message'] == 'success':
            disks = return_data['data']['content']
            print("\n[Alist Success] 存储列表总数: {0}".format(
                return_data['data']['total']))
            print("{:<14}{:^18}{}".format('驱 动', '状    态', '挂载路径'))
            print("{:<16}{:^20}{}".format("--------", "--------", "--------"))
            for disk in disks:
                print("{:<16}{:^20}{}".format(disk['driver'], disk['status'],
                                              disk['mount_path']))
        else:
            print("[Alist Failure✕] 获取存储驱动失败\n{0}".format(
                return_data['message']))

        # 返回请求结果
        return return_data


class TMDBApi:
    """
    调用TMDB api获取剧集相关信息
    """

    def __init__(self, key: str):
        """
        初始化参数

        :param key: TMDB Api Key(V3)
        """

        self.key = key
        self.api_url = "https://api.themoviedb.org/3"

    def tv_info(self, tv_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据提供的id获取剧集信息.

        :param tv_id: 剧集id
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果, 不输出内容
        :return: 请求状态码与剧集信息请求结果
        """

        # 发送请求
        post_url = "{0}/tv/{1}".format(self.api_url, tv_id)
        post_params = dict(api_key=self.key, language=language)
        r = requests.get(post_url, params=post_params)

        # 获取请求结果
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print("[TMDB SearchID Failure✕] tv_id: {0}\n{1}".format(
                tv_id, return_data['status_message']))
            return return_data

        # 格式化输出请求结果
        first_air_year = return_data['first_air_date'][:4]
        name = return_data['name']
        dir_name = "{0} ({1})".format(name, first_air_year)
        print("\n[TMDB Success✓] {}".format(dir_name))
        seasons = return_data['seasons']
        print("{:<10}{:^8}{:^10}{}".format(" 开播时间 ", "集 数", "序 号", "剧 名"))
        print("{:<12}{:^12}{:^12}{}".format("----------", "----", "-----",
                                            "----------------"))
        for season in seasons:
            print("{:<12}{:^12}{:^12}{}".format(str(season['air_date']),
                                                season['episode_count'],
                                                season['season_number'],
                                                season['name']))
        print("")

        # 返回请求结果
        return return_data

    def search_tv(self, keyword: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据关键字匹配剧集, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language:
        :param silent: 静默返回请求结果,不输出内容
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = "{0}/search/tv".format(self.api_url)
        post_params = dict(api_key=self.key, query=keyword, language=language)
        r = requests.get(post_url, params=post_params)

        # 获取请求结果
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print("[TMDB Failure✕] Keyword: {0}\n{1}".format(
                keyword, return_data['status_message']))
            return return_data

        if len(return_data['results']) == 0:
            print('[TMDB Failure✕] 关键词[{0}]查找不到任何相关剧集'.format(keyword))
            return return_data

        # 格式化输出请求结果
        print('\n[TMDB Success✓] 关键词[{0}]查找结果如下: '.format(keyword))
        print("{:<8}{:^14}{}".format(" 首播时间 ", "序号", "剧 名"))
        print("{:<12}{:^16}{}".format("----------", "-----",
                                      "----------------"))

        for i, result in enumerate(return_data['results']):
            print("{:<12}{:^16}{}".format(result['first_air_date'], i,
                                          result['name']))

        # 返回请求结果
        return return_data

    def tv_season_info(self,
                       tv_id: str,
                       season_number: int,
                       language: str = 'zh-CN',
                       silent: bool = False) -> dict:
        """
        获取指定季度剧集信息.
        :param tv_id: 剧集id
        :param season_number: 指定第几季
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果,不输出内容
        :return: 返回获取指定季度剧集信息结果
        """

        # 发送请求
        post_url = "{0}/tv/{1}/season/{2}".format(self.api_url, tv_id,
                                                  season_number)
        post_params = dict(api_key=self.key, language=language)
        r = requests.get(post_url, params=post_params)

        # 获取请求结果
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print("[TMDB Failure✕] 剧集id: {0}\t第 {1} 季\n{2}".format(
                tv_id, season_number, return_data['status_message']))
            return return_data

        # 格式化输出请求结果
        print("\n[TMDB Success✓] {} 第 {} 季 ".format(return_data['name'],
                                                    season_number))
        print("{:6}{:<12}{:<10}{}".format("序 号", "放映日期", "时 长", "标 题"))
        print("{:8}{:<16}{:<12}{}".format("----", "----------", "-----",
                                          "----------------"))

        for episode in return_data['episodes']:
            print("{:<8}{:<16}{:<12}{}".format(episode['episode_number'],
                                               episode['air_date'],
                                               str(episode['runtime']) + 'min',
                                               episode['name']))

        # 返回请求结果
        return return_data
