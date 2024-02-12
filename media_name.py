# -*- coding: utf-8 -*-
# @Time : 2023/4/29/0029 20:18
# @Author : JKOR
# @File : media_name.py
# @Software: PyCharm

from dataclasses import dataclass
import json
import colorama
from natsort import natsorted
from api import AlistApi, TMDBApi
from utils import DebugDecorators, Tools


@dataclass
class Config:
    """参数设置类"""

    # Alist 主页链接
    alist_url: str = ""
    # Alist 登录账号
    alist_user: str = ""
    # Alist 登录密码
    alist_password: str = ""
    # Alist 2FA 验证码
    alist_totp: str = ""
    # 使用游客权限，无需登录
    alist_guest: bool = False
    # TMDB Api Key(V3)
    tmdb_key: str = ""
    # TMDB 搜索语言
    tmdb_language: str = "zh-CN"
    # 文件重命名格式
    tv_name_format: str = "{name}-S{season:0>2}E{episode:0>2}.{title}"
    # 是否排除已重命名文件
    exclude_renamed: bool = True
    # 使用异步方式加快重命名操作
    rename_by_async: bool = True
    # 是否重命名父文件夹
    media_folder_rename: int = 1
    # 季度文件夹命名格式
    tv_season_format: str = "Season {season}"
    # 视频文件匹配正则表达式
    video_regex_pattern: str = r'(?i).*\.(avi|flv|wmv|mov|mp4|mkv|rm|rmvb)$'
    # 字幕文件匹配正则表达式
    subtitle_regex_pattern: str = r'(?i).*\.(ass|srt|ssa|sub)$'

    @DebugDecorators.catch_exceptions
    def load(self, filepath: str):
        """读取配置"""
        # 读取配置文件
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                config = json.load(file)
                # 将字典的键值对转化为对象的属性
                for key, value in config.items():
                    setattr(self, key, value)

            return True
        # 若文件不存在则创建文件
        except FileNotFoundError:
            self.alist_url = input("请输入Alist地址\n")
            self.alist_user = input("请输入账号\n")
            self.alist_password = input("请输入登录密码\n")
            self.alist_totp = input("请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请[回车]跳过\n")
            self.tmdb_key = input("请输入TMDB api密钥(V3)\n")
            return self.save(filepath)

    @DebugDecorators.catch_exceptions
    def save(self, filepath: str, output: bool = True):
        """保存配置"""
        dict_config = vars(self)
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(dict_config, file, indent=4)

        if output:
            print(f"\n配置文件保存路径: {filepath}")
            print("其余自定义设置请修改保存后的配置文件")

        return True


class AlistMediaRename:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self, config: Config):
        """
        初始化参数
        :param config: 配置参数
        """

        self.config = config
        self.debug = DebugDecorators.debug_enabled
        # 初始化 AlistApi 和 TMDBApi
        self.alist = AlistApi(self.config.alist_url, self.config.alist_user, self.config.alist_password, self.config.alist_totp)
        if self.config.alist_guest is False:
            self.alist.login()
        self.tmdb = TMDBApi(self.config.tmdb_key)

    @DebugDecorators.catch_exceptions
    def tv_rename_id(
        self,
        tv_id: str,
        folder_path: str,
        folder_password=None,
        first_number: int = 1) -> dict:

        """
        根据TMDB剧集id获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param tv_id: 剧集id
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        # 确保路径以 / 开头并以 / 结尾
        folder_path = Tools.ensure_slash(folder_path)

        # 设置返回数据
        result = {"success": False, 'function': '', 'rawdata': ''}

        # 根据剧集 id 查找 TMDB 剧集信息
        # 刷新文件夹所在父文件夹
        if self.config.rename_by_async:
            func_list = [
                {"func": self.tmdb.tv_info, "args": [tv_id, self.config.tmdb_language]},
                {"func": self.alist.file_list, "args": [Tools.get_parent_path(folder_path), folder_password, True]}
                    ]
            
            tv_info_result = Tools.run_tasks(func_list)[0]
        else:
            tv_info_result = self.tmdb.tv_info(tv_id, self.config.tmdb_language)
            self.alist.file_list(Tools.get_parent_path(folder_path), folder_password, True)

        # 若查找失败则停止，并返回结果
        if 'success' in tv_info_result and tv_info_result['success'] is False:
            result['function'] = 'tmdb.tv_info'
            result['rawdata'] = tv_info_result
            return result

        notice_msg = Tools.ColorStr.yellow('[Notice !]')

        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(tv_info_result["seasons"]) == 1:
            # 获取剧集对应季每集标题
            season_number = tv_info_result["seasons"][0]["season_number"]
            if self.config.rename_by_async:
                func_list = []
                func_list = [
                    {"func": self.tmdb.tv_season_info, "args": [tv_id, tv_info_result["seasons"][0]["season_number"], self.config.tmdb_language]},
                    {"func": self.alist.file_list, "args": [folder_path, folder_password, True]}
                        ]
                tv_season_info, file_list_data = Tools.run_tasks(func_list)
            else:
                tv_season_info = self.tmdb.tv_season_info(tv_id, tv_info_result["seasons"][0]["season_number"], self.config.tmdb_language)
                file_list_data = self.alist.file_list(folder_path, folder_password, True)
            # 若获取失败则停止， 并返回结果
            if 'success' in tv_season_info and tv_season_info['success'] is False:
                print(
                    f"{Tools.ColorStr.red('[TvInfo ✗]')} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}"
                )
                return result
        else:
            # 获取到多项匹配结果，手动选择
            while True:
                season_number = input(f"{notice_msg} 该剧集有多季,请输入对应[序号], 输入[n]退出\t")
                if season_number == "n":
                    result["rawdata"] = ("用户输入[n], 已主动退出选择剧集季数")
                    result["success"] = True
                    return result

                season_number = int(season_number)
                break

            # 获取剧集对应季每集信息
            if self.config.rename_by_async:
                func_list = []
                func_list = [
                    {"func": self.tmdb.tv_season_info, "args": [tv_id, season_number, self.config.tmdb_language]},
                    {"func": self.alist.file_list, "args": [folder_path, folder_password, True]}
                        ]
                tv_season_info, file_list_data = Tools.run_tasks(func_list)
            else:
                tv_season_info = self.tmdb.tv_season_info(tv_id, season_number, self.config.tmdb_language)
                file_list_data = self.alist.file_list(folder_path, folder_password, True)

            # 若获取失败则停止， 并返回结果
            if 'success' in tv_season_info and tv_season_info['success'] is False:
                print(f"{Tools.ColorStr.red('[TvInfo ✗]')} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
                result["function"] = 'tv_season_info'
                result["rawdata"] = tv_season_info
                return result

        # 保存剧集标题
        episode_list = list(
            map(
                lambda x: self.config.tv_name_format.format(
                    name=tv_info_result["name"],
                    season=tv_season_info["season_number"],
                    episode=x["episode_number"],
                    title=x["name"],
                ),
                tv_season_info["episodes"],
            )
        )

        episode_list_1 = episode_list.copy()

        # 获取失败则停止，返回结果
        if file_list_data["message"] != "success":
            print(f"{Tools.ColorStr.red('List ✗')} 获取文件列表失败: {folder_path}\n{file_list_data['message']}")
            return result

        # 获取视频字幕文件列表
        file_list = list(map(lambda x: x["name"], file_list_data['data']['content']))
        video_list = natsorted(Tools.filter_file(file_list, self.config.video_regex_pattern))
        subtitle_list = natsorted(Tools.filter_file(file_list, self.config.subtitle_regex_pattern))
        # 若排除已重命名文件, 则过滤已重命名文件
        if self.config.exclude_renamed:
            video_list, episode_list = Tools.remove_intersection(video_list, episode_list)
            subtitle_list, episode_list_1 = Tools.remove_intersection(subtitle_list, episode_list_1)
        # 创建包含源文件名以及目标文件名列表
        episode_list = episode_list[first_number - 1 :]
        episode_list_1 = episode_list_1[first_number - 1 :]
        video_rename_list = [
            {"original_name": x, "target_name": y + "." + x.split(".")[-1]}
            for x, y in zip(video_list, episode_list)
        ]
        subtitle_rename_list = [
            {"original_name": x, "target_name": y + "." + x.split(".")[-1]}
            for x, y in zip(subtitle_list, episode_list_1)
        ]

        # 输出提醒消息
        print(f"\n{notice_msg} 以下视频文件将会重命名: ")
        for video in video_rename_list:
            print(f"{video['original_name']} -> {video['target_name']}")
        print(f"\n{notice_msg} 以下字幕文件将会重命名: ")
        for subtitle in subtitle_rename_list:
            print(f"{subtitle['original_name']} -> {subtitle['target_name']}")

        # 父文件夹重命名逻辑
        if self.config.media_folder_rename == 1:
            tv_folder_name = f"{tv_info_result['name']} ({tv_info_result['first_air_date'][:4]})"
            print(f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {tv_folder_name}")
        if self.config.media_folder_rename == 2:
            tv_folder_name = self.config.tv_season_format
            print(f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {tv_folder_name}")


        # 等待用户确认
        if not Tools.require_confirmation(notice_msg):
            result["rawdata"] = "用户输入[n], 已主动取消重命名"
            return result

        # 进行重命名操作
        if self.config.rename_by_async:
            func_list = []
            for file in video_rename_list + subtitle_rename_list:
                func_list.append({"func": self.alist.rename, "args": [file["target_name"], folder_path + file["original_name"]]})
            done = Tools.run_tasks(func_list)
        else:
            for file in video_rename_list + subtitle_rename_list:
                self.alist.rename(file["target_name"], folder_path + file["original_name"])

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")

        # 刷新文件列表
        self.alist.file_list(path=folder_path, password=folder_password, refresh=True)

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        if self.config.media_folder_rename == 1:
            self.alist.rename(tv_folder_name, folder_path[:-1])
        if self.config.media_folder_rename == 2:
            self.alist.rename(self.config.tv_season_format, folder_path[:-1])

        result["success"] = True
        return result

    @DebugDecorators.catch_exceptions
    def tv_rename_keyword(
        self, keyword: str, folder_path: str, folder_password=None, first_number: int = 1
    ) -> dict:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + "[Notice!]" + colorama.Fore.RESET

        # 设置返回数据
        result = {"success": False, 'function': '', 'rawdata': ''}

        # 使用关键词查找剧集
        search_result = self.tmdb.search_tv(keyword, language=self.config.tmdb_language)

        # 查找失败则停止, 并返回结果
        if 'success' in search_result and search_result['success'] is False:
            return result

        if not search_result["results"]:
            result['function'] = 'tmdb.sarch_tv'
            result['rawdata'] = search_result
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result["results"]) == 1:
            rename_result = self.tv_rename_id(
                search_result["results"][0]["id"], folder_path, folder_password, first_number
            )

            return result

        # 若有多项, 则手动选择
        while True:
            tv_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result["results"])))
            active_number = list(map(str, active_number))
            if tv_number == "n":
                result["rawdata"] = ("用户输入[n], 已主动退出选择匹配剧集")
                result["success"] = True
                return result
            if tv_number in active_number:
                tv_id = search_result["results"][int(tv_number)]["id"]
                break

            continue

        # 根据获取到的id进行重命名
        rename_result = self.tv_rename_id(tv_id, folder_path, folder_password, first_number)
        return rename_result

    @DebugDecorators.catch_exceptions
    def movie_rename_id(self, movie_id: str, folder_path: str, folder_password=None) -> dict:
        """
        根据TMDB电影id获取电影标题,并将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param movie_id: 电影id
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        notice_msg = Tools.ColorStr.yellow('[Notice !]')

        # 确保路径以 / 开头并以 / 结尾
        folder_path = Tools.ensure_slash(folder_path)

        # 设置返回数据
        result = {"success": False, 'function': '', 'rawdata': ''}

        # 根据电影id 查找TMDB电影信息
        if self.config.rename_by_async:
            func_list = [
                {"func": self.tmdb.movie_info, "args": [movie_id, self.config.tmdb_language]},
                {"func": self.alist.file_list, "args": [Tools.get_parent_path(folder_path), folder_password, True]}
                    ]
            
            movie_info_result = Tools.run_tasks(func_list)[0]
        else:
            movie_info_result = self.tmdb.movie_info(movie_id, self.config.tmdb_language)
            self.alist.file_list(Tools.get_parent_path(folder_path), folder_password, True)

        # 若查找失败则停止，并返回结果
        if 'success' in movie_info_result and movie_info_result['success'] is False:
            return result

        # 获取Alist文件列表
        file_list_data = self.alist.file_list(path=folder_path, password=folder_password, refresh=True)

        # 创建包含源文件名以及目标文件名列表
        target_name = f"{movie_info_result['title']} ({movie_info_result['release_date'][:4]})"

        file_list = list(map(lambda x: x["name"], file_list_data["data"]['content']))
        video_list = natsorted(Tools.filter_file(file_list, self.config.video_regex_pattern))
        subtitle_list = natsorted(Tools.filter_file(file_list, self.config.subtitle_regex_pattern))
        video_rename_list = [
            {"original_name": x, "target_name": target_name + "." + x.split(".")[-1]}
            for x in video_list
        ]
        subtitle_rename_list = [
            {"original_name": x, "target_name": target_name + "." + x.split(".")[-1]}
            for x in subtitle_list
        ]

        # 输出提醒消息
        print(f"\n{notice_msg} 仅会将首个视频/字幕文件重命名:")
        for video in video_rename_list:
            print(f"{video['original_name']} -> {video['target_name']}")
            break
        for subtitle in subtitle_rename_list:
            print(f"{subtitle['original_name']} -> {subtitle['target_name']}")
            break

        if self.config.media_folder_rename == 1:
            movie_folder_name = (
                f"{movie_info_result['title']} ({movie_info_result['release_date'][:4]})"
            )
            print(f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {movie_folder_name}")

        # 用户确认
        if not Tools.require_confirmation(notice_msg):
            result["rawdata"] = "用户输入[n], 已主动取消重命名"
            return result

        # 进行重命名操作
        result["success"] = True
        for files in video_rename_list, subtitle_rename_list:
            for file in files:
                self.alist.rename(file["target_name"], folder_path + file["original_name"])
                break

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")
        # 刷新文件列表
        file_list_data = self.alist.file_list(path=folder_path, password=folder_password, refresh=True)


        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        if self.config.media_folder_rename == 1:
            self.alist.rename(movie_folder_name, folder_path[:-1])

        result["success"] = True
        return result

    @DebugDecorators.catch_exceptions
    def movie_rename_keyword(self, keyword: str, folder_path: str, folder_password=None) -> dict:
        """
        根据TMDB电影关键字获取电影标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param keyword: 电影关键词
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + "[Notice!]" + colorama.Fore.RESET

        # 创建返回数据
        result = {"success": False, 'function': '', 'rawdata': ''}

        # 使用关键词查找剧集
        search_result = self.tmdb.search_movie(keyword, language=self.config.tmdb_language)

        # 查找失败则停止, 并返回结果
        if 'success' in search_result and search_result['success'] is False:
            return result
        if not search_result["results"]:
            result['function'] = 'tmdb.sarch_movie'
            result['rawdata'] = search_result
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result["results"]) == 1:
            rename_result = self.movie_rename_id(
                search_result["results"][0]["id"], folder_path, folder_password
            )
            result["result"] += rename_result["result"]
            return result

        # 若有多项, 则手动选择
        while True:
            movie_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result["results"])))
            active_number = list(map(str, active_number))
            if movie_number == "n":
                result["rawdata"] = ("用户输入[n], 已主动退出选择匹配电影")
                return result
            if movie_number in active_number:
                movie_id = search_result["results"][int(movie_number)]["id"]
                break
            continue

        # 根据获取到的id进行重命名
        rename_result = self.movie_rename_id(movie_id, folder_path, folder_password)
        return rename_result
