# -*- coding: utf-8 -*-
# @Time : 2023/4/29/0029 20:18
# @Author : JKOR
# @File : media_name.py
# @Software: PyCharm

from api import AlistApi, TMDBApi


class AlistMediaRename:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    # todo: 自定义重命名文件格式
    # todo: 文件夹重命名以及季度文件夹重命名
    # todo: 获取TMDB电影信息并重命名

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
        :param debug: debug模式, 输出信息更加详细
        """

        # ----Settings Start----
        # 需要识别的视频及字幕格式
        self.video_suffix_list = ['mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov']
        self.subtitle_suffix_list = ['srt', 'ass', 'stl']
        # TMDB 搜索语言
        self.tmdb_language = "zh-CN"
        # 是否重命名父文件夹名称
        self.tv_folder_rename = False
        # 是否创建对应季文件夹，并将剧集文件移动到其中
        self.tv_season_dir = False
        # ------Settings End------

        # 初始化参数
        self.alist_url = alist_url
        self.alist_user = alist_user
        self.alist_password = alist_password
        self.alist_totp = alist_totp
        self.tmdb_key = tmdb_key
        self.debug = debug

        # 初始化AlistApi类, TMDBApi类
        self.alist = AlistApi(self.alist_url, self.alist_user,
                              self.alist_password, self.alist_totp)
        if not self.alist.login_status:
            while True:
                input()
        self.tmdb = TMDBApi(self.tmdb_key)

    def media_rename_id(self,
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
            tv_season_info = self.tmdb.tv_season_info(
                tv_id,
                tv_info_result['seasons'][0]['season_number'],
                language=self.tmdb_language,
                silent=self.debug)
            result['result'].append(tv_info_result)
            season_number = 1
            # 若获取失败则停止， 并返回结果
            if tv_season_info['request_code'] != 200:
                print("[TMDB Failure✕] 剧集id: {}\t{} 第 {} 季\n{}".format(
                    tv_id, tv_info_result['name'], season_number,
                    tv_season_info['status_message']))
                return result
        else:
            # 获取到多项匹配结果，手动选择
            while True:
                season_number = input("[Notice!] 该剧集有多季,请输入对应[序号], 输入n退出\t")
                active_number = list(range(len(tv_info_result['seasons'])))
                active_number = list(map(lambda x: str(x), active_number))
                if season_number == 'n':
                    result['result'].append("用户输入[n], 已主动退出选择剧集季数")
                    return result
                elif season_number in active_number:
                    season_number = int(season_number)
                    break
                else:
                    continue

            # 获取剧集对应季每集信息
            tv_season_info = self.tmdb.tv_season_info(tv_id,
                                                      season_number,
                                                      language=self.tmdb_language,
                                                      silent=self.debug)
            result['result'].append(tv_season_info)
            # 若获取失败则停止， 并返回结果
            if tv_season_info['request_code'] != 200:
                print("[TMDB Failure✕] 剧集id: {}\t{} 第 {} 季\n{}".format(
                    tv_id, tv_info_result['name'], season_number,
                    tv_season_info['status_message']))
                return result

        # 保存剧集标题
        episodes = list(
            map(
                lambda x: "{}-S{:0>2}E{:0>2}.{}".format(
                    tv_info_result['name'], tv_season_info['season_number'], x[
                        'episode_number'], x['name']),
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
            print("[Alist Failure✕] 文件列表路径: {0}\n{1}".format(
                folder_path, file_list_data['message']))
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
        print("\n[Notice!] 以下视频文件将会重命名: ")
        for video in video_rename_list:
            print("{} -> {}".format(video['original_name'],
                                    video['target_name']))
        print("\n[Notice!] 以下字幕文件将会重命名: ")
        for subtitle in subtitle_rename_list:
            print("{} -> {}".format(subtitle['original_name'],
                                    subtitle['target_name']))

        # 用户确认
        print("")
        while True:
            signal = input("[Notice!] 确定要重命名吗? 输入y确定, n取消\t")
            if signal.lower() == 'y':
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
                                              silent=self.debug)
            result['result'].append(rename_result)
            if rename_result['message'] != 'success':
                # 若部分文件命名失败， 则将success参数设为False， 并输出失败原因
                result['success'] = False
                # print("[Alist Failure✕] 重命名失败: {0} -> {1}\n{2}".format(
                #     file['target_name'], file['original_name'],
                #     rename_result['message']))

        print("{:-<30}\n{}".format("", "文件重命名全部完成"))
        # 刷新文件列表
        file_list_data = self.alist.file_list(path=folder_path,
                                              password=folder_password,
                                              refresh=True,
                                              silent=self.debug)
        result['result'].append(file_list_data)
        return result

    def media_rename_keyword(self,
                             keyword: str,
                             folder_path: str,
                             folder_password=None,
                             first_number: int = 1) -> dict:
        """
        根据TMDB剧集id获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

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
            rename_result = self.media_rename_id(
                search_result['results'][0]['id'], folder_path,
                folder_password, first_number)
            result['result'] += (rename_result['result'])
            return result

        # 若有多项, 则手动选择
        while True:
            tv_number = input("[Notice!] 查找到多个结果, 请输入对应[序号], 输入n退出\t")
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
        rename_result = self.media_rename_id(tv_id, folder_path,
                                             folder_password, first_number)
        result['result'] += (rename_result['result'])
        return result
