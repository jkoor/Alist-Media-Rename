from api import AlistApi, TMDBApi
from config import Config
from utils import DebugDecorators, Tools, Task, Tasks

class AlistMediaRename:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self, filepath: str | None = None):
        """
        初始化参数
        :param config: 配置参数
        """

        self.config = Config(filepath)

        # 初始化 AlistApi 和 TMDBApi
        self.alist = AlistApi(
            self.config.alist.url,
            self.config.alist.user,
            self.config.alist.password,
            self.config.alist.totp,
        )
        if self.config.alist.guest_mode is False:
            self.alist.login()
        self.tmdb = TMDBApi(self.config.tmdb.api_key)

    def tv_rename_id(
        self, tv_id: str, folder_path: str, folder_password=None, first_number: int = 1
    ) -> dict:
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
        result = {"success": False, "function": "", "rawdata": ""}

        # 根据剧集 id 查找 TMDB 剧集信息
        # 刷新文件夹所在父文件夹

        tasks = Tasks()
        task_0 = Task()


        # if self.config.rename_by_async:
        #     func_list = [
        #         {"func": self.tmdb.tv_info, "args": [tv_id, self.config.tmdb_language]},
        #         {
        #             "func": self.alist.file_list,
        #             "args": [Tools.get_parent_path(folder_path), folder_password, True],
        #         },
        #     ]

        #     tv_info_result = Tools.run_tasks(func_list)[0]
        # else:
        #     tv_info_result = self.tmdb.tv_info(tv_id, self.config.tmdb_language)
        #     self.alist.file_list(
        #         Tools.get_parent_path(folder_path), folder_password, True
        #     )

        # 若查找失败则停止，并返回结果
        if "success" in tv_info_result and tv_info_result["success"] is False:
            result["function"] = "tmdb.tv_info"
            result["rawdata"] = tv_info_result
            return result

        notice_msg = Tools.ColorStr.yellow("[Notice !]")

        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(tv_info_result["seasons"]) == 1:
            # 获取剧集对应季每集标题
            season_number = tv_info_result["seasons"][0]["season_number"]
            if self.config.rename_by_async:
                func_list = []
                func_list = [
                    {
                        "func": self.tmdb.tv_season_info,
                        "args": [
                            tv_id,
                            tv_info_result["seasons"][0]["season_number"],
                            self.config.tmdb_language,
                        ],
                    },
                    {
                        "func": self.alist.file_list,
                        "args": [folder_path, folder_password, True],
                    },
                ]
                tv_season_info, file_list_data = Tools.run_tasks(func_list)
            else:
                tv_season_info = self.tmdb.tv_season_info(
                    tv_id,
                    tv_info_result["seasons"][0]["season_number"],
                    self.config.tmdb_language,
                )
                file_list_data = self.alist.file_list(
                    folder_path, folder_password, True
                )
            # 若获取失败则停止， 并返回结果
            if "success" in tv_season_info and tv_season_info["success"] is False:
                print(
                    f"{Tools.ColorStr.red('[TvInfo ✗]')} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}"
                )
                return result
        else:
            # 获取到多项匹配结果，手动选择
            while True:
                season_number = input(
                    f"{notice_msg} 该剧集有多季,请输入对应[序号], 输入[n]退出\t"
                )
                if season_number == "n":
                    result["rawdata"] = "用户输入[n], 已主动退出选择剧集季数"
                    result["success"] = True
                    return result

                season_number = int(season_number)
                break

            # 获取剧集对应季每集信息
            if self.config.rename_by_async:
                func_list = []
                func_list = [
                    {
                        "func": self.tmdb.tv_season_info,
                        "args": [tv_id, season_number, self.config.tmdb_language],
                    },
                    {
                        "func": self.alist.file_list,
                        "args": [folder_path, folder_password, True],
                    },
                ]
                tv_season_info, file_list_data = Tools.run_tasks(func_list)
            else:
                tv_season_info = self.tmdb.tv_season_info(
                    tv_id, season_number, self.config.tmdb_language
                )
                file_list_data = self.alist.file_list(
                    folder_path, folder_password, True
                )

            # 若获取失败则停止， 并返回结果
            if "success" in tv_season_info and tv_season_info["success"] is False:
                print(
                    f"{Tools.ColorStr.red('[TvInfo ✗]')} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}"
                )
                result["function"] = "tv_season_info"
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
            print(
                f"{Tools.ColorStr.red('List ✗')} 获取文件列表失败: {folder_path}\n{file_list_data['message']}"
            )
            return result

        # 获取视频字幕文件列表
        file_list = list(map(lambda x: x["name"], file_list_data["data"]["content"]))
        video_list = natsorted(
            Tools.filter_file(file_list, self.config.video_regex_pattern)
        )
        subtitle_list = natsorted(
            Tools.filter_file(file_list, self.config.subtitle_regex_pattern)
        )
        # 若排除已重命名文件, 则过滤已重命名文件
        if self.config.exclude_renamed:
            video_list, episode_list = Tools.remove_intersection(
                video_list, episode_list
            )
            subtitle_list, episode_list_1 = Tools.remove_intersection(
                subtitle_list, episode_list_1
            )
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
            tv_folder_name = (
                f"{tv_info_result['name']} ({tv_info_result['first_air_date'][:4]})"
            )
            print(
                f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {tv_folder_name}"
            )
        if self.config.media_folder_rename == 2:
            tv_folder_name = self.config.tv_season_format.format(
                season=tv_season_info["season_number"],
                name=tv_info_result["name"],
                year=tv_info_result["first_air_date"][:4],
            )
            print(
                f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {tv_folder_name}"
            )

        # 等待用户确认
        if not Tools.require_confirmation(notice_msg):
            result["rawdata"] = "用户输入[n], 已主动取消重命名"
            return result

        # 进行重命名操作
        if self.config.rename_by_async:
            func_list = []
            for file in video_rename_list + subtitle_rename_list:
                func_list.append(
                    {
                        "func": self.alist.rename,
                        "args": [
                            file["target_name"],
                            folder_path + file["original_name"],
                        ],
                    }
                )
            done = Tools.run_tasks(func_list)
        else:
            for file in video_rename_list + subtitle_rename_list:
                self.alist.rename(
                    file["target_name"], folder_path + file["original_name"]
                )

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")

        # 刷新文件列表
        self.alist.file_list(path=folder_path, password=folder_password, refresh=True)

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        if self.config.media_folder_rename == 1 or self.config.media_folder_rename == 2:
            self.alist.rename(tv_folder_name, folder_path[:-1])

        result["success"] = True
        return result
