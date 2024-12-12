# TODO: 改用httpx库, 以支持原生异步请求
# TODO: 使用click改写输出信息，将交互操作解构
# TODO: 加入保存日志功能
# TODO: 命令行加入父文件夹重命名选项

from typing import Union
from .api import AlistApi, TMDBApi
from .config import Config
from .utils import Tools, Tasks, PrintMessage, Debug
from .models import Task, TaskResult, Formated_Variables


class Amr:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self, config: Union[Config, str]):
        """
        初始化参数
        :param config: 配置参数
        """

        self.config = config if type(config) is Config else Config(config)

        # 初始化 AlistApi 和 TMDBApi
        self.alist = AlistApi(
            self.config.alist.url,
            self.config.alist.user,
            self.config.alist.password,
            self.config.alist.totp,
        )
        self.tmdb = TMDBApi(self.config.tmdb.api_url, self.config.tmdb.api_key)
        # 登录Alist
        Debug.stop_on_error([self.init_login()])

    def init_login(self) -> TaskResult:
        """
        登录Alist

        :return: 登录结果
        """

        # 任务列表
        # task_0: 登录Alist
        task_0_alist_login = Task(
            name="登录Alist",
            func=self.alist.login,
            args=[],
        )
        # 运行任务
        if self.config.alist.guest_mode:
            result_0_alist_login = TaskResult(
                func_name="登录Alist",
                args=[],
                success=True,
                data={"result": "游客模式无需登录"},
                error="",
            )
        [result_0_alist_login] = Tasks.run([task_0_alist_login], False)

        return result_0_alist_login

    def tv_rename_id(
        self, tv_id: str, folder_path: str, folder_password=None, first_number: str = '1'
    ) -> list[TaskResult]:
        """
        根据TMDB剧集id获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param tv_id: 剧集id
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
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
        # task_1: 刷新文件夹所在父文件夹，防止Alist未及时刷新，导致无法获取文件列表
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
        season_number = PrintMessage.select_number(
            result_0_tmdb_tv_info.data["seasons"]
        )
        season_number = result_0_tmdb_tv_info.data["seasons"][season_number][
            "season_number"
        ]
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

        fv_tv = Formated_Variables.tv(
            name=result_0_tmdb_tv_info.data["name"],
            original_name=result_0_tmdb_tv_info.data["original_name"],
            year=result_0_tmdb_tv_info.data["first_air_date"][:4],
            first_air_date=result_0_tmdb_tv_info.data["first_air_date"],
            language=result_0_tmdb_tv_info.data["original_language"],
            region=result_0_tmdb_tv_info.data["origin_country"][0],
            rating=result_0_tmdb_tv_info.data["vote_average"],
            season=result_2_tmdb_tv_season_info.data["season_number"],
        )

        # 创建包含源文件名以及目标文件名列表
        # 保存剧集标题
        episode_list_video = list(
            map(
                lambda x: self.config.amr.tv_name_format.format(
                    **vars(fv_tv),
                    episode=x["episode_number"],
                    air_date=x["air_date"],
                    episode_rating=x["vote_average"],
                    title=x["name"],
                ),
                result_2_tmdb_tv_season_info.data["episodes"],
            )
        )
        episode_list_subtitle = episode_list_video.copy()

        # 获取文件列表
        file_list = list(
            map(lambda x: x["name"], result_3_alist_file_list.data["data"]["content"])
        )
        # 筛选视频文件和字幕文件
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )

        # 匹配剧集信息/文件列表
        video_rename_list = Tools.match_episode_files(
            video_list,
            episode_list_video,
            self.config.amr.exclude_renamed,
            first_number,
        )
        subtitle_rename_list = Tools.match_episode_files(
            subtitle_list,
            episode_list_subtitle,
            self.config.amr.exclude_renamed,
            first_number,
        )

        # 获取父文件夹重命名标题
        folder_rename_title = self.config.amr.folder_name_format.format(**vars(fv_tv))

        ### ------------------------ 4. 进行重命名操作 -------------------- ###

        # 输出提醒消息
        PrintMessage.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            self.config.amr.media_folder_rename,
            folder_rename_title,
            folder_path,
        )

        # 等待用户确认
        PrintMessage.require_confirmation()

        # 进行文件重命名操作
        # 任务列表
        # task_4: 重命名文件
        tasks_4_alist_rename = []
        for file in video_rename_list + subtitle_rename_list:
            tasks_4_alist_rename.append(
                Task(
                    name="重命名文件",
                    func=self.alist.rename,
                    args=[
                        Tools.replace_illegal_char(file["target_name"]),
                        folder_path + file["original_name"],
                    ],
                )
            )
        # 运行任务
        results_4_alist_rename = Tasks.run(
            tasks_4_alist_rename, self.config.amr.rename_by_async
        )

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        # 任务列表
        # task_5: 重命名父文件夹
        task_5_alist_rename = Task(
            name="重命名父文件夹",
            func=self.alist.rename,
            args=[Tools.replace_illegal_char(folder_rename_title), folder_path[:-1]],
        )
        # 运行任务
        if self.config.amr.media_folder_rename:
            [result_5_alist_rename] = Tasks.run(
                [task_5_alist_rename], self.config.amr.rename_by_async
            )
        else:
            [result_5_alist_rename] = [
                TaskResult(
                    func_name="重命名父文件夹",
                    args=[],
                    success=True,
                    data={"result": "未重命名父文件夹"},
                    error="",
                )
            ]

        ### ------------------------ 5. 刷新文件夹 -------------------- ###
        # 任务列表
        # task_6: 刷新父文件夹
        task_6_alist_file_list = Task(
            name="刷新父文件夹",
            func=self.alist.file_list,
            args=[Tools.get_parent_path(folder_path), folder_password, True],
        )
        # task_7: 刷新文件夹
        if self.config.amr.media_folder_rename:
            task_7_alist_file_list = Task(
                name="刷新文件夹",
                func=self.alist.file_list,
                args=[
                    f"{Tools.get_parent_path(folder_path)}{folder_rename_title}/",
                    folder_password,
                    True,
                ],
            )
        else:
            task_7_alist_file_list = Task(
                name="刷新文件夹",
                func=self.alist.file_list,
                args=[folder_path, folder_password, True],
            )

        # 运行任务
        [result_6_alist_file_list, result_7_alist_file_list] = Tasks.run(
            [task_6_alist_file_list, task_7_alist_file_list], False
        )

        ### ------------------------ 6. 返回结果 -------------------- ###
        result = [
            result_0_tmdb_tv_info,
            result_1_alist_file_list,
            result_2_tmdb_tv_season_info,
            result_3_alist_file_list,
            *results_4_alist_rename,
            result_5_alist_rename,
            result_6_alist_file_list,
            result_7_alist_file_list,
        ]

        return result

    def tv_rename_keyword(
        self,
        keyword: str,
        folder_path: str,
        folder_password=None,
        first_number: str = '1',
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
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_0_tmdb_search_tv])

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # 选择剧集
        selected_number = PrintMessage.select_number(
            result_0_tmdb_search_tv.data["results"]
        )
        tv_id = result_0_tmdb_search_tv.data["results"][selected_number]["id"]

        # 根据获取到的id进行重命名
        rename_result = self.tv_rename_id(
            tv_id, folder_path, folder_password, first_number
        )

        return [result_0_tmdb_search_tv, *rename_result]

    def movie_rename_id(
        self, movie_id: str, folder_path: str, folder_password=None
    ) -> list[TaskResult]:
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

        fv_movie = Formated_Variables.movie(
            name=result_0_tmdb_movie_info.data["title"],
            original_name=result_0_tmdb_movie_info.data["original_title"],
            year=result_0_tmdb_movie_info.data["release_date"][:4],
            release_date=result_0_tmdb_movie_info.data["release_date"],
            language=result_0_tmdb_movie_info.data["original_language"],
            region=result_0_tmdb_movie_info.data["origin_country"][0],
            rating=result_0_tmdb_movie_info.data["vote_average"],
        )

        # 创建包含源文件名以及目标文件名列表
        target_name = self.config.amr.movie_name_format.format(**vars(fv_movie))

        file_list = list(
            map(lambda x: x["name"], result_2_alist_file_list.data["data"]["content"])
        )
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )
        # 匹配剧集信息/文件列表
        video_rename_list = Tools.match_episode_files(
            video_list, [target_name], self.config.amr.exclude_renamed, '1'
        )
        subtitle_rename_list = Tools.match_episode_files(
            subtitle_list, [target_name], self.config.amr.exclude_renamed, '1'
        )
        # 获取父文件夹重命名标题
        folder_rename_title = self.config.amr.folder_name_format.format(
            **vars(fv_movie)
        )

        ### ------------------------ 4. 进行重命名操作 -------------------- ###
        # 输出提醒消息
        PrintMessage.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            self.config.amr.media_folder_rename,
            folder_rename_title,
            folder_path,
        )

        # 等待用户确认
        PrintMessage.require_confirmation()

        # 进行文件重命名操作
        # 任务列表
        # task_3: 重命名文件
        tasks_3_alist_rename = []
        for file in video_rename_list + subtitle_rename_list:
            tasks_3_alist_rename.append(
                Task(
                    name="重命名文件",
                    func=self.alist.rename,
                    args=[
                        Tools.replace_illegal_char(file["target_name"]),
                        folder_path + file["original_name"],
                    ],
                )
            )
        # 运行任务
        results_3_alist_rename = Tasks.run(
            tasks_3_alist_rename, self.config.amr.rename_by_async
        )

        # 重命名父文件夹 格式: 复仇者联盟 (2012)
        # 任务列表
        # task_4: 重命名父文件夹
        task_4_alist_rename = Task(
            name="重命名父文件夹",
            func=self.alist.rename,
            args=[Tools.replace_illegal_char(folder_rename_title), folder_path[:-1]],
        )
        # 运行任务
        if self.config.amr.media_folder_rename:
            [result_4_alist_rename] = Tasks.run(
                [task_4_alist_rename], self.config.amr.rename_by_async
            )
        else:
            [result_4_alist_rename] = [
                TaskResult(
                    func_name="重命名父文件夹",
                    args=[],
                    success=True,
                    data={"result": "未重命名父文件夹"},
                    error="",
                )
            ]

        ### ------------------------ 5. 刷新文件夹 -------------------- ###
        # 任务列表
        # task_5: 刷新父文件夹
        task_5_alist_file_list = Task(
            name="刷新父文件夹",
            func=self.alist.file_list,
            args=[Tools.get_parent_path(folder_path), folder_password, True],
        )
        # task_6: 刷新文件夹
        if self.config.amr.media_folder_rename:
            task_6_alist_file_list = Task(
                name="刷新文件夹",
                func=self.alist.file_list,
                args=[
                    f"{Tools.get_parent_path(folder_path)}{folder_rename_title}/",
                    folder_password,
                    True,
                ],
            )
        else:
            task_6_alist_file_list = Task(
                name="刷新文件夹",
                func=self.alist.file_list,
                args=[folder_path, folder_password, True],
            )

        # 运行任务
        [result_5_alist_file_list, result_6_alist_file_list] = Tasks.run(
            [task_5_alist_file_list, task_6_alist_file_list], False
        )

        ### ------------------------ 5. 返回结果 -------------------- ###
        result = [
            result_0_tmdb_movie_info,
            result_1_alist_file_list,
            result_2_alist_file_list,
            *results_3_alist_rename,
            result_4_alist_rename,
            result_5_alist_file_list,
            result_6_alist_file_list,
        ]

        return result

    def movie_rename_keyword(
        self, keyword: str, folder_path: str, folder_password=None
    ) -> list[TaskResult]:
        """
        根据TMDB电影关键字获取电影标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param keyword: 电影关键词
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        ### ------------------------ 1. 查找 TMDB 电影信息 ------------------------ ####
        # 使用关键词查找剧集
        task_0_tmdb_search_movie = Task(
            name="使用关键词查找剧集",
            func=self.tmdb.search_movie,
            args=[keyword, self.config.tmdb.language],
        )
        # 运行任务
        [result_0_tmdb_search_movie] = Tasks.run(
            [task_0_tmdb_search_movie], self.config.amr.rename_by_async
        )
        # 判断运行结果, 若出现错误则停止运行
        Debug.stop_on_error([result_0_tmdb_search_movie])

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # 选择剧集
        selected_number = PrintMessage.select_number(
            result_0_tmdb_search_movie.data["results"]
        )
        movie_id = result_0_tmdb_search_movie.data["results"][selected_number]["id"]

        # 根据获取到的id进行重命名
        rename_result = self.movie_rename_id(movie_id, folder_path, folder_password)

        return [result_0_tmdb_search_movie, *rename_result]
