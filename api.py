# -*- coding: utf-8 -*-
# @Time : 2023/4/28/0028 18:10
# @Author : JKOR
# @File : api.py
# @Software: PyCharm

import pyotp
import requests
from natsort import natsorted
import colorama


# from requests_toolbelt import MultipartEncoder


class AlistApi:
    """
    Alist请求函数, 包含: 登录/获取文件列表/重命名文件/删除文件/新建文件夹/上传文件/获取下载链接/获取存储驱动信息
    \nAlist api非官方说明文档(来自网友分享): https://zhuanlan.zhihu.com/p/587004798
    """

    def __init__(self, url: str, user: str, password: str, totp_code: str):
        """
        初始化参数.

        :param url: Alist 主页链接
        :param user: Alist 登录账号
        :param password: Alist 登录密码
        :param totp_code: Alist 2FA 验证码
        """
        if url[-1] == '/':
            url = url[:-1]
        self.url = url
        self.user = user
        self.password = password
        self.totp_code = pyotp.TOTP(totp_code)  # 使用self.totp_code.now() 生成实时 TOTP 验证码
        self.token = ''
        self.login_success = None
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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Login●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Login●Success]' + colorama.Fore.RESET

        # 输出获取Token结果
        if return_data['message'] != 'success':
            self.login_success = False
            print(f"{failure_msg} Alist登录失败\t2FA验证码: {post_datas['OtpCode']}\n{return_data['message']}\n")
            return return_data
        else:
            self.token = return_data['data']['token']
            self.login_success = True
            print(f"{success_msg} Alist登录成功\t主页: {self.url}")

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
            # 若文件夹为空, 则停止运行
            if return_data['data']['content'] is None:
                return_data['message'] = "文件夹为空"
                return return_data

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[List●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[List●Success]' + colorama.Fore.RESET

        # 获取失败则输出相关信息
        if return_data['message'] != 'success':
            print(f"{failure_msg} 获取文件列表失败: {path}\n{return_data['message']}")
            return return_data

        # 输出格式化文件列表信息
        print(f"{success_msg} 文件列表路径: {path}")
        print("{:<21s}{:<10s}{:<26s}".format("修改日期", "文件大小", "名    称"))
        print("{:<25s}{:<14s}{:<30s}".format("--------------------",
                                             "--------",
                                             "--------------------"))
        for file in (file_list_0 + file_list_1):
            print("{:<25s}{:<14s}{}".format(file['modified'], file['size'],
                                            file['name']))
        print(f"\n  文件总数: {return_data['data']['total']}")
        print(f"  写入权限: {return_data['data']['write']}")
        print(f"  存储来源: {return_data['data']['provider']}\n")

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Rename●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Rename●Success]' + colorama.Fore.RESET

        # 输出重命名结果
        if return_data['message'] != 'success':
            print(f"{failure_msg} 重命名失败: {path} -> {name}\n{return_data['message']}")
        else:
            print(f"{success_msg} 重命名路径:{path} -> {name}")

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Move●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Move●Success]' + colorama.Fore.RESET

        # 输出重命名结果
        if return_data['message'] != 'success':
            print(f"{failure_msg} 移动失败: {src_dir} -> {dst_dir}\n{return_data['message']}")
        else:
            print(f"{success_msg} 移动路径: {src_dir} -> {dst_dir}")

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Mkdir●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Mkdir●Success]' + colorama.Fore.RESET

        # 输出新建文件夹请求结果
        if return_data['message'] != 'success':
            print(f"{failure_msg} 文件夹创建失败: {path}\n{return_data['message']}")
        else:
            print(f"{success_msg} 文件夹创建路径: {path}")

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Remove●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Remove●Success]' + colorama.Fore.RESET

        # 输出删除文件/文件夹请求结果
        if return_data['message'] != 'success':
            print(f"{failure_msg} 删除失败: {path}\n{return_data['message']}")
        else:
            for name in names:
                print(f"{success_msg} 删除路径: {path}/{name}")

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[DL_link●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[DL_link●Success]' + colorama.Fore.RESET

        # 输出获取下载信息请求结果
        if return_data['message'] == 'success':
            file = return_data['data']
            print(f"\n{success_msg} 获取文件链接路径: {path}")
            print(f"名称: {file['name']}\n来源: {file['provider']}\n直链: {self.url}/d{path}\n源链: file['raw_url']")
        else:
            print(f"{failure_msg} 获取文件链接失败: {path}\n{return_data['message']}")

        # 返回请求结果
        return return_data

    def upload(self, path: str, file: str, silent: bool = False) -> dict:
        """
        上传文件.

        :param path: 上传路径(包含文件) 如/abc/test.txt
        :param file: 源文件路径(包含文件) 如/abc/test.txt
        :param silent: 静默返回请求结果,不输出内容
        :return: 返回上传文件请求结果
        """

        print("由于上传文件需要调用第三方库：requests_toolbelt, "
              "而主程序又用不到上传操作, 所以该函数代码被注释掉了, "
              "如有需要请取消代码注释, 并把最上方调用代码取消注释!")

        return {'注意': '查看输出内容'}

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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[Disk●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[Disk●Success]' + colorama.Fore.RESET

        # 输出已添加存储列表请求结果
        if return_data['message'] == 'success':
            disks = return_data['data']['content']
            print(f"{success_msg} 存储列表总数: {return_data['data']['total']}")
            print("{:<14}{:^18}{}".format('驱 动', '状    态', '挂载路径'))
            print("{:<16}{:^20}{}".format("--------", "--------", "--------"))
            for disk in disks:
                print("{:<16}{:^20}{}".format(disk['driver'], disk['status'], disk['mount_path']))
        else:
            print(f"{failure_msg} 获取存储驱动失败\n{return_data['message']}")

        # 返回请求结果
        return return_data


class TMDBApi:
    """
    调用TMDB api获取剧集相关信息
    \nTMDB api官方说明文档(https://developers.themoviedb.org/3)
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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[TvInfo●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[TvInfo●Success]' + colorama.Fore.RESET

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print(f"{failure_msg} tv_id: {tv_id}\n{return_data['status_message']}")
            return return_data

        # 格式化输出请求结果
        first_air_year = return_data['first_air_date'][:4]
        name = return_data['name']
        dir_name = f"{name} ({first_air_year})"
        print(f"{success_msg} {dir_name}")
        seasons = return_data['seasons']
        print("{:<10}{:^8}{:^10}{}".format(" 开播时间 ", "集 数", "序 号", "剧 名"))
        print("{:<12}{:^12}{:^12}{}".format("----------", "----", "-----", "----------------"))
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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[TvSearch●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[TvSearch●Success]' + colorama.Fore.RESET

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print(f"{failure_msg} Keyword: {keyword}\n{return_data['status_message']}")
            return return_data

        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{keyword}]查找不到任何相关剧集")
            return return_data

        # 格式化输出请求结果
        print(f"{success_msg} 关键词[{keyword}]查找结果如下: ")
        print("{:<8}{:^14}{}".format(" 首播时间 ", "序号", "剧 名"))
        print("{:<12}{:^16}{}".format("----------", "-----", "----------------"))

        for i, result in enumerate(return_data['results']):
            print("{:<12}{:^16}{}".format(result['first_air_date'], i, result['name']))

        print("")
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

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[TvSeason●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[TvSeason●Success]' + colorama.Fore.RESET

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print(f"{failure_msg} 剧集id: {tv_id}\t第 {season_number} 季\n{return_data['status_message']}")
            return return_data

        # 格式化输出请求结果
        print(f"{success_msg} {return_data['name']} 第 {season_number} 季 ")
        print("{:6}{:<12}{:<10}{}".format("序 号", "放映日期", "时 长", "标 题"))
        print("{:8}{:<16}{:<12}{}".format("----", "----------", "-----", "----------------"))

        for episode in return_data['episodes']:
            print("{:<8}{:<16}{:<12}{}".format(episode['episode_number'],
                                               episode['air_date'],
                                               str(episode['runtime']) + 'min',
                                               episode['name']))

        # 返回请求结果
        return return_data

    def movie_info(self, movie_id: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据提供的id获取电影信息.

        :param movie_id: 电影id
        :param language: TMDB搜索语言
        :param silent: 静默返回请求结果, 不输出内容
        :return: 请求状态码与电影信息请求结果
        """

        # 发送请求
        post_url = "{0}/movie/{1}".format(self.api_url, movie_id)
        post_params = dict(api_key=self.key, language=language)
        r = requests.get(post_url, params=post_params)

        # 获取请求结果
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[MovieInfo●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[MovieInfo●Success]' + colorama.Fore.RESET

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print(F"{failure_msg} tv_id: {movie_id}\n{return_data['status_message']}")
            return return_data

        # 格式化输出请求结果
        print(f"{success_msg} {return_data['title']} {return_data['release_date']}")
        print(f"[标语] {return_data['tagline']}")
        print(f"[剧集简介] {return_data['overview']}")

        # 返回请求结果
        return return_data

    def search_movie(self, keyword: str, language: str = 'zh-CN', silent: bool = False) -> dict:
        """
        根据关键字匹配电影, 获取相关信息.

        :param keyword: 剧集搜索关键词
        :param language:
        :param silent: 静默返回请求结果,不输出内容
        :return: 匹配剧集信息请求结果
        """

        # 发送请求
        post_url = "{0}/search/movie".format(self.api_url)
        post_params = dict(api_key=self.key, query=keyword, language=language)
        r = requests.get(post_url, params=post_params)

        # 获取请求结果
        return_data = r.json()
        return_data['request_code'] = r.status_code

        # 静默返回请求结果,不输出内容
        if silent:
            return return_data

        # 输出内容提醒颜色
        failure_msg = colorama.Fore.RED + '\n[MovieSearch●Failure]' + colorama.Fore.RESET
        success_msg = colorama.Fore.GREEN + '\n[MovieSearch●Success]' + colorama.Fore.RESET

        # 请求失败则输出失败信息
        if r.status_code != 200:
            print(f"{failure_msg} Keyword: {keyword}\n{return_data['status_message']}")
            return return_data

        if len(return_data['results']) == 0:
            print(f"{failure_msg} 关键词[{keyword}]查找不到任何相关剧集")
            return return_data

        # 格式化输出请求结果
        print(f"{success_msg} 关键词[{keyword}]查找结果如下: ")
        print("{:<8}{:^14}{}".format(" 首播时间 ", "序号", "电影标题"))
        print("{:<12}{:^16}{}".format("----------", "-----", "----------------"))

        for i, result in enumerate(return_data['results']):
            print("{:<12}{:^16}{}".format(result['release_date'], i, result['title']))

        # 返回请求结果
        return return_data
