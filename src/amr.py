from api import AlistApi, TMDBApi
from config import Config
from utils import Tools, Tasks, PrintMessage, Debug
from models import Task, TaskResult, Formated_Variables


class AlistMediaRename:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self, config_filepath: str | None = None):
        """
        初始化参数
        :param config: 配置参数
        """

        self.config = Config(config_filepath)

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
    ) -> list[TaskResult]:
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

        ### ------------------------ 1. 查找 TMDB 剧集信息 ------------------------ ####
        # 任务列表
        # task_0: 根据剧集 id 查找 TMDB 剧集信息
        task_0_tmdb_tv_info = Task(
            name="根据剧集 id 查找 TMDB 剧集信息",
            func=self.tmdb.tv_info,
            args=[tv_id, self.config.tmdb.language],
        )
        # task_1: 刷新文件夹所在父文件夹，防止Alist为及时刷新，导致无法获取文件列表
        task_1_alist_file_list = Task(
            name="刷新文件夹所在父文件夹",
            func=self.alist.file_list,
            args=[Tools.get_parent_path(folder_path), folder_password, True],
        )
        # 运行任务
        [result_0_tmdb_tv_info, result_1_alist_file_list] = Tasks.run(
            [task_0_tmdb_tv_info, task_1_alist_file_list],
            self.config.amr.rename_by_async,
        )
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_0_tmdb_tv_info])

        ### ------------------------ 2. 获取剧集对应季度每集信息/文件列表 -------------------- ###
        # 选择季度
        season_number = Tools.select_number(result_0_tmdb_tv_info.data["seasons"])
        # 任务列表
        # task_2: 获取剧集对应季每集信息
        task_2_tmdb_tv_season_info = Task(
            name="获取剧集对应季每集信息",
            func=self.tmdb.tv_season_info,
            args=[tv_id, season_number, self.config.tmdb.language],
        )
        # task_3: 获取文件夹列表
        task_3_alist_file_list = Task(
            name="刷新文件夹列表",
            func=self.alist.file_list,
            args=[folder_path, folder_password, True],
        )
        # 运行任务
        [result_2_tmdb_tv_season_info, result_3_alist_file_list] = Tasks.run(
            [task_2_tmdb_tv_season_info, task_3_alist_file_list],
            self.config.amr.rename_by_async,
        )
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_2_tmdb_tv_season_info, result_3_alist_file_list])

        ### ------------------------ 3. 匹配剧集信息/文件列表 -------------------- ###

        # 保存剧集标题
        episode_list = list(
            map(
                lambda x: self.config.amr.tv_name_format.format(
                    name=result_0_tmdb_tv_info.data["name"],
                    season=result_2_tmdb_tv_season_info.data["season_number"],
                    episode=x["episode_number"],
                    title=x["name"],
                ),
                result_2_tmdb_tv_season_info.data["episodes"],
            )
        )

        episode_list_subtitle = episode_list.copy()

        # 获取视频字幕文件列表
        file_list = list(
            map(lambda x: x["name"], result_3_alist_file_list.data["data"]["content"])
        )
        # 筛选视频文件和字幕文件
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )
        # 过滤已重命名文件
        video_list, episode_list = Tools.remove_intersection(
            video_list, episode_list, self.config.amr.exclude_renamed
        )
        subtitle_list, episode_list_subtitle = Tools.remove_intersection(
            subtitle_list, episode_list_subtitle, self.config.amr.exclude_renamed
        )
        # 匹配剧集信息/文件列表
        video_rename_list = Tools.match_episode_files(
            episode_list, video_list, first_number
        )
        subtitle_rename_list = Tools.match_episode_files(
            episode_list_subtitle, subtitle_list, first_number
        )

        # TAG: tv_rename_id
        ### ------------------------ 4. 进行重命名操作 -------------------- ###
        # 获取父文件夹重命名标题
        renamed_folder_title = Tools.get_renamed_folder_title(
            result_0_tmdb_tv_info.data,
            result_2_tmdb_tv_season_info.data,
            folder_path,
            self.config.amr.media_folder_rename,
            self.config.amr.tv_season_format,
        )

        # 输出提醒消息
        PrintMessage.print_rename_info(
            video_rename_list, subtitle_rename_list, renamed_folder_title, folder_path
        )

        # 等待用户确认
        Tools.require_confirmation()

        # 进行文件重命名操作
        # 任务列表
        tasks_4_alist_rename = []
        for file in video_rename_list + subtitle_rename_list:
            tasks_4_alist_rename.append(
                Task(
                    name="重命名文件",
                    func=self.alist.rename,
                    args=[file["target_name"], folder_path + file["original_name"]],
                )
            )
        # 运行任务
        results_4_alist_rename = Tasks.run(
            tasks_4_alist_rename, self.config.amr.rename_by_async
        )

        # 刷新文件列表
        # self.alist.file_list(path=folder_path, password=folder_password, refresh=True)

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        # 任务列表
        # task_5: 重命名父文件夹
        task_5_alist_rename = Task(
            name="重命名父文件夹",
            func=self.alist.rename,
            args=[renamed_folder_title, folder_path[:-1]],
        )
        # 运行任务
        if renamed_folder_title != "":
            result_5_alist_rename = Tasks.run(
                [task_5_alist_rename], self.config.amr.rename_by_async
            )
        else:
            result_5_alist_rename = TaskResult(
                func_name="重命名父文件夹", args=(), success=True, data=None, error=""
            )

        result = [
            result_0_tmdb_tv_info,
            result_1_alist_file_list,
            result_2_tmdb_tv_season_info,
            result_3_alist_file_list,
            *results_4_alist_rename,
            result_5_alist_rename,
        ]

        return result

    def tv_rename_keyword(
        self,
        keyword: str,
        folder_path: str,
        folder_password=None,
        first_number: int = 1,
    ) -> list[TaskResult]:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        ### ------------------------ 1. 查找 TMDB 剧集信息 ------------------------ ####
        # 使用关键词查找剧集
        task_0_tmdb_search_tv = Task(
            name="使用关键词查找剧集",
            func=self.tmdb.search_tv,
            args=[keyword, self.config.tmdb.language],
        )
        # 运行任务
        [result_0_tmdb_search_tv] = Tasks.run(
            [task_0_tmdb_search_tv], self.config.amr.rename_by_async
        )
        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # 选择剧集
        selected_number = Tools.select_number(result_0_tmdb_search_tv.data["results"])
        tv_id = result_0_tmdb_search_tv.data["results"][selected_number]["id"]

        # 根据获取到的id进行重命名
        rename_result = self.tv_rename_id(
            tv_id, folder_path, folder_password, first_number
        )

        return [result_0_tmdb_search_tv, *rename_result]

    def movie_rename_id(
        self, movie_id: str, folder_path: str, folder_password=None
    ) -> dict:
        """
        根据TMDB电影id获取电影标题,并将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param movie_id: 电影id
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        # 确保路径以 / 开头并以 / 结尾
        folder_path = Tools.ensure_slash(folder_path)

        ### ------------------------ 1. 查找 TMDB 电影信息 ------------------------ ####
        # 任务列表
        # task_0: 根据电影 id 查找 TMDB 电影信息
        task_0_tmdb_movie_info = Task(
            name="根据电影 id 查找 TMDB 电影信息",
            func=self.tmdb.movie_info,
            args=[movie_id, self.config.tmdb.language],
        )
        # task_1: 刷新文件夹所在父文件夹，防止Alist为及时刷新，导致无法获取文件列表
        task_1_alist_file_list = Task(
            name="刷新文件夹所在父文件夹",
            func=self.alist.file_list,
            args=[Tools.get_parent_path(folder_path), folder_password, True],
        )
        # 运行任务
        [result_0_tmdb_movie_info, result_1_alist_file_list] = Tasks.run(
            [task_0_tmdb_movie_info, task_1_alist_file_list],
            self.config.amr.rename_by_async,
        )
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_0_tmdb_movie_info])

        ### ------------------------ 2. 获取文件列表 -------------------- ###
        # 任务列表
        # task_2: 获取文件夹列表
        task_2_alist_file_list = Task(
            name="获取文件列表",
            func=self.alist.file_list,
            args=[folder_path, folder_password, True],
        )
        # 运行任务
        [result_2_alist_file_list] = Tasks.run(
            [task_2_alist_file_list], self.config.amr.rename_by_async
        )
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_2_alist_file_list])

        ### ------------------------ 3. 匹配电影信息/文件列表 -------------------- ###

        formated_variables = Formated_Variables.movie(
            name=result_0_tmdb_movie_info.data["name"],
            original_name=result_0_tmdb_movie_info.data["original_title"],
            year=result_0_tmdb_movie_info.data["release_date"][:4],
            release_date=result_0_tmdb_movie_info.data["release_date"],
            language=result_0_tmdb_movie_info.data["original_language"],
            region=result_0_tmdb_movie_info.data["origin_country"][0],
            rating=result_0_tmdb_movie_info.data["vote_average"],
        )

        # 获取电影标题
        movie_title = result_0_tmdb_movie_info.data["title"]
        movie_release_year = result_0_tmdb_movie_info.data["release_date"][:4]
        # 创建包含源文件名以及目标文件名列表
        target_name = self.config.amr.movie_name_format.format(
            title=movie_title, year=movie_release_year
        )

        file_list = list(
            map(lambda x: x["name"], result_2_alist_file_list.data["data"]["content"])
        )
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )
        # 匹配剧集信息/文件列表
        video_rename_list = Tools.match_episode_files(video_list, video_list, 1)
        subtitle_rename_list = Tools.match_episode_files(
            subtitle_list, subtitle_list, 1
        )

        # TAG: movie_rename_id
        ### ------------------------ 4. 进行重命名操作 -------------------- ###

        # 获取父文件夹重命名标题
        renamed_folder_title = Tools.get_renamed_folder_title(
            result_0_tmdb_tv_info.data,
            result_2_tmdb_tv_season_info.data,
            folder_path,
            self.config.amr.media_folder_rename,
            self.config.amr.tv_season_format,
        )

        # 输出提醒消息
        PrintMessage.print_rename_info(
            video_rename_list, subtitle_rename_list, renamed_folder_title, folder_path
        )

        # 等待用户确认
        Tools.require_confirmation()

        # 输出提醒消息
        print(f"\n{notice_msg} 仅会将首个视频/字幕文件重命名:")
        for video in video_rename_list:
            print(f"{video['original_name']} -> {video['target_name']}")
            break
        for subtitle in subtitle_rename_list:
            print(f"{subtitle['original_name']} -> {subtitle['target_name']}")
            break

        if self.config.media_folder_rename == 1:
            movie_folder_name = f"{movie_info_result['title']} ({movie_info_result['release_date'][:4]})"
            print(
                f"\n{notice_msg} 文件夹重命名: {folder_path.split('/')[-2]} -> {movie_folder_name}"
            )

        # 用户确认
        if not Tools.require_confirmation(notice_msg):
            result["rawdata"] = "用户输入[n], 已主动取消重命名"
            return result

        # 进行重命名操作
        result["success"] = True
        for files in video_rename_list, subtitle_rename_list:
            for file in files:
                self.alist.rename(
                    file["target_name"], folder_path + file["original_name"]
                )
                break

        print(f"{'':-<30}\n{notice_msg} 文件重命名操作完成")
        # 刷新文件列表
        file_list_data = self.alist.file_list(
            path=folder_path, password=folder_password, refresh=True
        )

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        if self.config.media_folder_rename == 1:
            self.alist.rename(movie_folder_name, folder_path[:-1])

        result["success"] = True
        return result
