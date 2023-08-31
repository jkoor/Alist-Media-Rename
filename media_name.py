# -*- coding: utf-8 -*-
# @Time : 2023/4/29/0029 20:18
# @Author : JKOR
# @File : media_name.py
# @Software: PyCharm

import time
from api import AlistApi, TMDBApi
import colorama


class AlistMediaRename:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self,
                 alist_url: str,
                 alist_user: str,
                 alist_password: str,
                 alist_totp: str,
                 tmdb_key: str,
                 debug: bool = True):
        """
        初始化参数
        :param alist_url: Alist 主页链接
        :param alist_user: Alist 登录账号
        :param alist_password: Alist 登录密码
        :param alist_totp: Alist 2FA 验证码
        :param tmdb_key: TMDB Api Key(V3)
        :param debug: debug模式, 输出信息更加详细, ※True为关闭debug, False为开启debug
        """

        # ----Settings Start----
        # TMDB 搜索语言
        self.tmdb_language = "zh-CN"
        # 文件重命名格式
        self.tv_name_format = "{name}-S{season:0>2}E{episode:0>2}.{title}"
        # 是否重命名父文件夹名称
        self.media_folder_rename = False
        # 是否创建对应季文件夹，并将剧集文件移动到其中
        self.tv_season_dir = False
        # 季度文件夹命名格式
        self.tv_season_format = "Season {season}"
        # 需要识别的视频及字幕格式
        self.video_suffix_list = ['mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov']
        self.subtitle_suffix_list = ['srt', 'ass', 'stl']
        # ------Settings End------

        # 初始化参数
        self.alist_url = alist_url
        self.alist_user = alist_user
        self.alist_password = alist_password
        self.alist_totp = alist_totp
        self.tmdb_key = tmdb_key
        # debug模式, 输出信息更加详细, ※True为关闭debug, False为开启debug
        self.debug = debug

        # 初始化AlistApi类, TMDBApi类
        self.alist = AlistApi(self.alist_url, self.alist_user,
                              self.alist_password, self.alist_totp)
        if not self.alist.login_success:
            while True:
                input()
        self.tmdb = TMDBApi(self.tmdb_key)

    def tv_rename_id(self,
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

        if folder_path[-1] != '/':
            folder_path += '/'

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        # 设置返回数据
        result = dict(success=False,
                      args=dict(tv_id=tv_id,
                                folder_path=folder_path,
                                folder_password=folder_password,
                                first_number=first_number),
                      result=[])

        # 根据剧集id 查找TMDB剧集信息
        tv_info_result = self.tmdb.tv_info(tv_id, language=self.tmdb_language, silent=False)
        result['result'].append(tv_info_result)

        # 若查找失败则停止，并返回结果
        if tv_info_result['request_code'] != 200:
            return result

        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(tv_info_result['seasons']) == 1:
            # 获取剧集对应季每集标题
            season_number = tv_info_result['seasons'][0]['season_number']
            tv_season_info = self.tmdb.tv_season_info(
                tv_id,
                tv_info_result['seasons'][0]['season_number'],
                language=self.tmdb_language,
                silent=self.debug)
            result['result'].append(tv_info_result)
            # 若获取失败则停止， 并返回结果
            if tv_season_info['request_code'] != 200:
                failure_msg = colorama.Fore.RED + '\n[TvInfo●Failure]' + colorama.Fore.RESET
                print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
                return result
        else:
            # 获取到多项匹配结果，手动选择
            while True:
                season_number = input(f"{notice_msg} 该剧集有多季,请输入对应[序号], 输入[n]退出\t")
                # active_number = list(range(len(tv_info_result['seasons'])))
                # active_number = list(map(lambda x: str(x), active_number))
                if season_number == 'n':
                    result['result'].append("用户输入[n], 已主动退出选择剧集季数")
                    return result
                else:
                    season_number = int(season_number)
                    break
                # else:
                #     continue

            # 获取剧集对应季每集信息
            tv_season_info = self.tmdb.tv_season_info(tv_id,
                                                      season_number,
                                                      language=self.tmdb_language,
                                                      silent=self.debug)
            result['result'].append(tv_season_info)
            # 若获取失败则停止， 并返回结果
            if tv_season_info['request_code'] != 200:
                failure_msg = colorama.Fore.RED + '\n[TvInfo●Failure]' + colorama.Fore.RESET
                print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
                return result

        # 保存剧集标题
        episodes = list(
            map(
                lambda x: self.tv_name_format.format(
                    name=tv_info_result['name'], season=tv_season_info['season_number'], episode=x[
                        'episode_number'], title=x['name']),
                tv_season_info['episodes']))

        episodes = episodes[first_number - 1:]

        # 获取Alist文件列表
        file_list_data = self.alist.file_list(path=folder_path,
                                              password=folder_password,
                                              refresh=True,
                                              silent=self.debug)
        result['result'].append(file_list_data)
        # 获取失败则停止，返回结果
        if file_list_data['message'] != 'success':
            # 输出内容提醒颜色
            failure_msg = colorama.Fore.RED + '\n[List●Failure]' + colorama.Fore.RESET
            print(f"{failure_msg} 获取文件列表失败: {folder_path}\n{file_list_data['message']}")
            return result

        # 创建包含源文件名以及目标文件名列表
        file_list = list(map(lambda x: x['name'], file_list_data['file_list']))
        video_list = list(
            filter(lambda x: x.split(".")[-1] in self.video_suffix_list,
                   file_list))
        subtitle_list = list(
            filter(lambda x: x.split(".")[-1] in self.subtitle_suffix_list,
                   file_list))
        video_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                  target_name=y + '.' + x.split(".")[-1]),
                video_list, episodes))
        subtitle_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                  target_name=y + '.' + x.split(".")[-1]),
                subtitle_list, episodes))

        # 输出提醒消息
        print(f"\n{notice_msg} 以下视频文件将会重命名: ")
        for video in video_rename_list:
            print("{} -> {}".format(video['original_name'],
                                    video['target_name']))
        print(f"\n{notice_msg} 以下字幕文件将会重命名: ")
        for subtitle in subtitle_rename_list:
            print("{} -> {}".format(subtitle['original_name'],
                                    subtitle['target_name']))

        if self.media_folder_rename:
            tv_folder_name = f"{tv_info_result['name']} ({tv_info_result['first_air_date'][:4]})"
            print(f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {tv_folder_name}")
        if self.tv_season_dir:
            season_dir_name = self.tv_season_format.format(season=season_number)
            print(f"{notice_msg} 剧集文件将移动到[{season_dir_name}]")

        # 用户确认
        print("")
        while True:
            signal = input(f"{notice_msg} 确定要重命名吗? [回车]确定, [n]取消\t")
            if signal.lower() == '':
                break
            elif signal.lower() == 'n':
                result['result'].append("用户输入[n], 已主动取消重命名")
                return result
            else:
                continue

        # 进行重命名操作
        result['success'] = True
        for file in video_rename_list + subtitle_rename_list:
            rename_result = self.alist.rename(file['target_name'],
                                              folder_path +
                                              file['original_name'],
                                              silent=False)
            result['result'].append(rename_result)
            if rename_result['message'] != 'success':
                # 若部分文件命名失败， 则将success参数设为False， 并输出失败原因
                result['success'] = False
                if self.debug:
                    failure_msg = colorama.Fore.RED + '\n[Rename●Failure]' + colorama.Fore.RESET
                    print(f"{failure_msg} 重命名失败: {file['original_name']} -> {file['target_name']}\n{rename_result['message']}")
            
            time.sleep(1)

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")
        # 刷新文件列表
        file_list_data = self.alist.file_list(path=folder_path,
                                              password=folder_password,
                                              refresh=True,
                                              silent=self.debug)
        result['result'].append(file_list_data)

        # 创建季度文件夹, 并将该季度剧集移动到相应季度中 格式: Season 1
        if self.tv_season_dir:
            season_path = folder_path + season_dir_name
            # 获取修改后文件列表
            move_list = list(map(lambda x: x['target_name'], video_rename_list)) + list(
                map(lambda x: x['target_name'], subtitle_rename_list))
            season_mkdir_result = self.alist.mkdir(season_path)
            result['result'].append(season_mkdir_result)
            season_dir_remove_result = self.alist.move(move_list, folder_path, season_path, silent=False)
            result['result'].append(season_dir_remove_result)
        # 重命名父文件夹 格式: 刀剑神域 (2012)
        if self.media_folder_rename:
            tv_folder_rename_result = self.alist.rename(tv_folder_name, folder_path, silent=False)
            result['result'].append(tv_folder_rename_result)

        return result

    def tv_rename_keyword(self,
                          keyword: str,
                          folder_path: str,
                          folder_password=None,
                          first_number: int = 1) -> dict:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        # 创建返回数据
        result = dict(success=False,
                      args=dict(keyword=keyword,
                                folder_path=folder_path,
                                folder_password=folder_password,
                                first_number=first_number),
                      result=[])
        # 使用关键词查找剧集
        search_result = self.tmdb.search_tv(keyword, language=self.tmdb_language)
        result['result'].append(search_result)
        # 查找失败则停止, 并返回结果
        if search_result['request_code'] != 200 or len(
                search_result['results']) == 0:
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result['results']) == 1:
            rename_result = self.tv_rename_id(
                search_result['results'][0]['id'], folder_path,
                folder_password, first_number)
            result['result'] += (rename_result['result'])
            return result

        # 若有多项, 则手动选择
        while True:
            tv_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result['results'])))
            active_number = list(map(lambda x: str(x), active_number))
            if tv_number == 'n':
                result['result'].append("用户输入[n], 已主动退出选择匹配剧集")
                return result
            elif tv_number in active_number:
                tv_id = search_result['results'][int(tv_number)]['id']
                break
            else:
                continue

        # 根据获取到的id进行重命名
        rename_result = self.tv_rename_id(tv_id, folder_path,
                                          folder_password, first_number)
        result['result'] += (rename_result['result'])
        return result

    def movie_rename_id(self,
                        movie_id: str,
                        folder_path: str,
                        folder_password=None) -> dict:
        """
        根据TMDB电影id获取电影标题,并将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param movie_id: 电影id
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        if folder_path[-1] != '/':
            folder_path += '/'

        # 设置返回数据
        result = dict(success=False,
                      args=dict(movie_id=movie_id, folder_path=folder_path, folder_password=folder_password, ),
                      result=[])

        # 根据电影id 查找TMDB电影信息
        movie_info_result = self.tmdb.movie_info(movie_id, language=self.tmdb_language, silent=False)
        result['result'].append(movie_info_result)

        # 若查找失败则停止，并返回结果
        if movie_info_result['request_code'] != 200:
            return result

        # 获取Alist文件列表
        file_list_data = self.alist.file_list(path=folder_path,
                                              password=folder_password,
                                              refresh=True,
                                              silent=self.debug)
        result['result'].append(file_list_data)
        # 获取失败则停止，返回结果
        if file_list_data['message'] != 'success':
            failure_msg = colorama.Fore.RED + '\n[List●Failure]' + colorama.Fore.RESET
            print(f"{failure_msg} 获取文件列表失败: {folder_path}\n{file_list_data['message']}")
            return result

        # 创建包含源文件名以及目标文件名列表
        target_name = "{} ({})".format(movie_info_result['title'], movie_info_result['release_date'][:4])

        file_list = list(map(lambda x: x['name'], file_list_data['file_list']))
        video_list = list(
            filter(lambda x: x.split(".")[-1] in self.video_suffix_list,
                   file_list))
        subtitle_list = list(
            filter(lambda x: x.split(".")[-1] in self.subtitle_suffix_list,
                   file_list))
        video_rename_list = list(
            map(
                lambda x: dict(original_name=x,
                               target_name=target_name + '.' + x.split(".")[-1]),
                video_list))
        subtitle_rename_list = list(
            map(
                lambda x: dict(original_name=x,
                               target_name=target_name + '.' + x.split(".")[-1]),
                subtitle_list))

        # 输出提醒消息
        print(f"\n{notice_msg} 仅会将首个视频/字幕文件重命名:")
        for video in video_rename_list:
            print("{} -> {}".format(video['original_name'],
                                    video['target_name']))
            break
        for subtitle in subtitle_rename_list:
            print("{} -> {}".format(subtitle['original_name'],
                                    subtitle['target_name']))
            break

        if self.media_folder_rename:
            movie_folder_name = f"{movie_info_result['title']} ({movie_info_result['release_date'][:4]})"
            print(f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {movie_folder_name}")

        # 用户确认
        print("")
        while True:
            signal = input(f"{notice_msg} 确定要重命名吗? [回车]确定, [n]取消\t")
            if signal.lower() == '':
                break
            elif signal.lower() == 'n':
                result['result'].append("用户输入[n], 已主动取消重命名")
                return result
            else:
                continue

        # 进行重命名操作
        result['success'] = True
        for files in video_rename_list, subtitle_rename_list:
            for file in files:
                rename_result = self.alist.rename(file['target_name'],
                                                  folder_path + file['original_name'],
                                                  silent=self.debug)
                result['result'].append(rename_result)
                if rename_result['message'] != 'success':
                    # 若部分文件命名失败， 则将success参数设为False， 并输出失败原因
                    result['success'] = False
                    if self.debug:
                        failure_msg = colorama.Fore.RED + '\n[Rename●Failure]' + colorama.Fore.RESET
                        print(f"{failure_msg} 重命名失败: {file['original_name']} -> {file['target_name']}\n{rename_result['message']}")
                break

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")
        # 刷新文件列表
        file_list_data = self.alist.file_list(path=folder_path,
                                              password=folder_password,
                                              refresh=True,
                                              silent=self.debug)
        result['result'].append(file_list_data)

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        if self.media_folder_rename:
            movie_folder_rename_result = self.alist.rename(movie_folder_name, folder_path, silent=False)
            result['result'].append(movie_folder_rename_result)

        return result

    def movie_rename_keyword(self,
                             keyword: str,
                             folder_path: str,
                             folder_password=None) -> dict:
        """
        根据TMDB电影关键字获取电影标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param keyword: 电影关键词
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.YELLOW + '[Notice!]' + colorama.Fore.RESET

        # 创建返回数据
        result = dict(success=False,
                      args=dict(keyword=keyword,
                                folder_path=folder_path,
                                folder_password=folder_password),
                      result=[])
        # 使用关键词查找剧集
        search_result = self.tmdb.search_movie(keyword, language=self.tmdb_language)
        result['result'].append(search_result)
        # 查找失败则停止, 并返回结果
        if search_result['request_code'] != 200 or len(
                search_result['results']) == 0:
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result['results']) == 1:
            rename_result = self.movie_rename_id(
                search_result['results'][0]['id'], folder_path,
                folder_password)
            result['result'] += (rename_result['result'])
            return result

        # 若有多项, 则手动选择
        while True:
            movie_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result['results'])))
            active_number = list(map(lambda x: str(x), active_number))
            if movie_number == 'n':
                result['result'].append("用户输入[n], 已主动退出选择匹配电影")
                return result
            elif movie_number in active_number:
                movie_id = search_result['results'][int(movie_number)]['id']
                break
            else:
                continue

        # 根据获取到的id进行重命名
        rename_result = self.movie_rename_id(movie_id, folder_path, folder_password)
        result['result'] += (rename_result['result'])
        return result
