import logging
from typing import Union

from .api import AlistApi, TMDBApi
from .config import Config
from .models import RenameTask, Folder
from .output import Message, console
from .task import ApiTask, taskManager, TaskManager
from .utils import Helper


logger = logging.getLogger("Amr")


class Amr:
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器刮削识别剧集
    文件命名格式: {剧集名称}-S{季度}E{集数}.{该集标题}.{文件后缀}
    文件命名举例: 间谍过家家-S01E01.行动代号“枭”.mkv
    文件夹命名格式: {剧集名称} ({首播年份})
    文件夹命名举例: 间谍过家家 (2022)

    """

    def __init__(self, config: Union[Config, str], verbose: bool = False):
        """
        初始化参数
        :param config: 配置参数
        """

        logger.debug("Amr 初始化开始，配置文件路径")
        # 如果传入的是 Config 对象，直接使用；否则从路径加载
        if isinstance(config, Config):
            self.config = config
        else:
            self.config = Config(config)

        self._taskManager: TaskManager = taskManager
        self._taskManager.verbose = verbose

        logger.debug("登录Alist...")
        with console.status("登录Alist..."):
            # 初始化 AlistApi 和 TMDBApi
            self.alist = AlistApi(
                self.config.alist.url,
                self.config.alist.user,
                self.config.alist.password,
                self.config.alist.totp,
            )
            self.tmdb = TMDBApi(
                self.config.tmdb.api_key,
                self.config.tmdb.api_url,
            )

    # TAG: tv_rename_id
    def tv_rename_id(
        self,
        tv_id: str,
        folder_path: str,
        folder_password=None,
        first_number: str = "1-",
    ) -> bool:
        """
        根据TMDB剧集id获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param tv_id: 剧集id
        :param folder_path: 文件夹路径, 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从集数开始命名, 如first_name=5-, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        logger.info(
            f"---Amr tv_rename_id---\n"
            f"tv_id: {tv_id}\n"
            f"folder_path: {folder_path}\n"
            f"folder_password: {'******' if folder_password else 'None'}\n"
            f"first_number: {first_number}"
        )

        if folder_path == "":
            self.tv_info_id(tv_id, first_number)
            return True

        ### ------------------------ 获取文件列表 ------------------------ ####
        logger.debug("获取文件列表...")
        with console.status("获取文件列表..."):
            # Step 1: 刷新文件夹所在父文件夹，防止Alist未及时刷新，导致无法获取文件列表
            task_0_file_list: ApiTask = self.alist.file_list(
                Folder(path=folder_path).parent_path(), folder_password, True
            )
            # Step 2: 获取文件夹列表
            task_1_file_list: ApiTask = self.alist.file_list(
                folder_path, folder_password, True
            )

        ### ------------------------ 获取 TMDB 剧集/季度信息 ------------------------ ####
        # Step 3: 根据剧集 id 查找 TMDB 剧集信息
        logger.debug("查找指定剧集...")
        with console.status("查找指定剧集..."):
            task_2_tv_info: ApiTask = self.tmdb.tv_info(
                tv_id, self.config.tmdb.language
            )

            self._taskManager.add_tasks(task_0_file_list, task_2_tv_info)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        # Step 4: 根据查找信息选择季度
        index = Message.select_number(len(task_2_tv_info.response.data["seasons"]))
        season_number = task_2_tv_info.response.data["seasons"][index]["season_number"]
        logger.debug(f"选择季度: {season_number}")

        # Step 5: 获取剧集对应季每集信息
        logger.debug("获取季度信息...")
        with console.status("获取季度信息..."):
            task_3_tv_season_info: ApiTask = self.tmdb.tv_season_info(
                tv_id, season_number, self.config.tmdb.language
            )
            self._taskManager.add_tasks(task_3_tv_season_info, task_1_file_list)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 匹配剧集信息-文件列表 -------------------- ###
        # Step 5: 匹配剧集信息-文件列表

        # 获取剧集信息
        media_list, folder_media_list = Helper.create_tv_media_list(
            first_number,
            task_2_tv_info,
            task_3_tv_season_info,
            tv_id,
            self.config,
        )
        # 筛选视频文件和字幕文件
        video_file_list, subtitle_file_list = Helper.create_file_list(
            task_1_file_list, Folder(path=folder_path), self.config
        )

        # 匹配剧集信息/文件列表
        video_rename_list: list[RenameTask] = Helper.match_episode_files(
            media_list, video_file_list, self.config
        )
        subtitle_rename_list: list[RenameTask] = Helper.match_episode_files(
            media_list, subtitle_file_list, self.config
        )

        # 获取父文件夹重命名标题
        folder_rename_list: list[RenameTask] = Helper.create_folder_rename_list(
            Folder(path=folder_path), folder_media_list
        )

        ### ------------------------ 4. 进行重命名操作 -------------------- ###

        # Step 6: 输出重命名文件信息
        Message.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            folder_rename_list,
            self.config.amr.media_folder_rename,
        )

        # Step 7: 等待用户确认
        Message.require_confirmation()

        # Step 8: 进行文件重命名操作
        logger.debug("正在重命名文件...")
        with console.status("正在重命名文件..."):
            # 生成重命名任务列表
            tasks_4_video_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in video_rename_list
            ]
            tasks_4_subtitle_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in subtitle_rename_list
            ]
            tasks_4_folder_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in folder_rename_list
            ]
            self._taskManager.add_tasks(
                *tasks_4_video_rename_list, *tasks_4_subtitle_rename_list
            )
            self._taskManager.run_tasks(self.config.amr.rename_by_async)
            if self.config.amr.media_folder_rename:
                self._taskManager.add_tasks(*tasks_4_folder_rename_list)
                self._taskManager.run_tasks(self.config.amr.rename_by_async)
        # Step 9: 输出重命名结果
        Message.print_rename_result(
            tasks_4_video_rename_list,
            tasks_4_subtitle_rename_list,
            tasks_4_folder_rename_list,
            self.config.amr.media_folder_rename,
        )

        return True

    # TAG: tv_rename_keyword
    def tv_rename_keyword(
        self,
        keyword: str,
        folder_path: str,
        folder_password=None,
        first_number: str = "1-",
    ) -> bool:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param folder_password: 文件夹访问密码
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        logger.info(
            f"---Amr tv_rename_keyword---\n"
            f"keyword: {keyword}\n"
            f"folder_path: {folder_path}\n"
            f"folder_password: {'******' if folder_password else 'None'}\n"
            f"first_number: {first_number}"
        )

        ### ------------------------ 1. 查找 TMDB 剧集信息 ------------------------ ####
        # Step 1: 使用关键词查找剧集
        logger.debug("查找指定剧集...")
        with console.status("查找指定剧集..."):
            task_0_search_tv: ApiTask = self.tmdb.search_tv(
                keyword, self.config.tmdb.language
            )
            self._taskManager.add_tasks(task_0_search_tv)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # Step 2: 选择剧集
        selected_number = Message.select_number(
            len(task_0_search_tv.response.data["results"])
        )
        logger.debug(f"选择剧集: {selected_number}")
        tv_id = task_0_search_tv.response.data["results"][selected_number]["id"]
        tv_id: str = str(tv_id)

        # Step 3: 根据获取到的id调用 tv_rename_id 函数进行重命名
        self.tv_rename_id(tv_id, folder_path, folder_password, first_number)

        return True

    # TAG: tv_info_id
    def tv_info_id(
        self,
        tv_id: str,
        first_number: str = "1-",
    ) -> bool:
        """
        根据TMDB剧集id获取剧集标题,并输出查找信息.

        :param tv_id: 剧集id
        :param first_number: 从集数开始命名, 如first_name=5-, 则从第5集开始按顺序重命名
        :return: 查找请求结果
        """

        logger.info(
            f"---Amr tv_info_id---\ntv_id: {tv_id}\nfirst_number: {first_number}"
        )

        ### ------------------------ 获取 TMDB 剧集/季度信息 ------------------------ ####
        # Step 3: 根据剧集 id 查找 TMDB 剧集信息
        logger.debug("查找指定剧集...")
        with console.status("查找指定剧集..."):
            task_2_tv_info: ApiTask = self.tmdb.tv_info(
                tv_id, self.config.tmdb.language
            )

            self._taskManager.add_tasks(task_2_tv_info)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        # Step 4: 根据查找信息选择季度
        index = Message.select_number(len(task_2_tv_info.response.data["seasons"]))
        season_number = task_2_tv_info.response.data["seasons"][index]["season_number"]
        logger.debug(f"选择季度: {season_number}")

        # Step 5: 获取剧集对应季每集信息
        logger.debug("获取季度信息...")
        with console.status("获取季度信息..."):
            task_3_tv_season_info: ApiTask = self.tmdb.tv_season_info(
                tv_id, season_number, self.config.tmdb.language
            )
            self._taskManager.add_tasks(task_3_tv_season_info)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 查找剧集信息 -------------------- ###
        # Step 5:  查找剧集信息

        # 获取剧集信息
        media_list, folder_media_list = Helper.create_tv_media_list(
            first_number,
            task_2_tv_info,
            task_3_tv_season_info,
            tv_id,
            self.config,
        )

        # 输出剧集信息
        Message.print_tv_info(
            media_list,
        )

        return True

    # TAG: movie_rename_id
    def movie_rename_id(
        self, movie_id: str, folder_path: str, folder_password=None
    ) -> bool:
        """
        根据TMDB电影id获取电影标题,并将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param movie_id: 电影id
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        logger.info(
            f"---Amr movie_rename_id---\n"
            f"movie_id: {movie_id}\n"
            f"folder_path: {folder_path}\n"
            f"folder_password: {'******' if folder_password else 'None'}"
        )

        if folder_path == "":
            self.movie_info_id(movie_id)
            return True

        ### ------------------------ 1. 获取文件列表 -------------------- ###
        # Step 1: 获取文件列表
        logger.debug("获取文件列表...")
        with console.status("获取文件列表..."):
            # Step 1: 刷新文件夹所在父文件夹，防止Alist为及时刷新，导致无法获取文件列表
            task_0_file_list: ApiTask = self.alist.file_list(
                Folder(path=folder_path).parent_path(), folder_password, True
            )

            # Step 2: 获取文件夹列表
            task_1_file_list: ApiTask = self.alist.file_list(
                folder_path, folder_password, True
            )

        ### ------------------------ 2. 查找 TMDB 电影信息 ------------------------ ####
        # Step 1: 根据电影 id 查找 TMDB 电影信息
        logger.debug("查找指定电影...")
        with console.status("查找指定电影..."):
            task_2_movie_info: ApiTask = self.tmdb.movie_info(
                movie_id, self.config.tmdb.language
            )

            self._taskManager.add_tasks(task_0_file_list, task_2_movie_info)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

            self._taskManager.add_tasks(task_1_file_list)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 3. 匹配电影信息/文件列表 -------------------- ###
        # Step 3: 匹配电影信息/文件列表

        # 获取电影信息
        media_list, folder_media_list = Helper.create_movie_media_list(
            task_2_movie_info, movie_id, self.config
        )

        # 筛选视频文件和字幕文件
        video_file_list, subtitle_file_list = Helper.create_file_list(
            task_1_file_list, Folder(path=folder_path), self.config
        )

        # 匹配电影信息/文件列表
        video_rename_list: list[RenameTask] = Helper.match_episode_files(
            media_list, video_file_list, self.config
        )
        subtitle_rename_list: list[RenameTask] = Helper.match_episode_files(
            media_list, subtitle_file_list, self.config
        )

        # 获取父文件夹重命名标题
        folder_rename_list: list[RenameTask] = Helper.create_folder_rename_list(
            Folder(path=folder_path), folder_media_list
        )

        ### ------------------------ 4. 进行重命名操作 -------------------- ###
        # Step 4: 输出重命名文件信息
        Message.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            folder_rename_list,
            self.config.amr.media_folder_rename,
        )

        # Step 5: 等待用户确认
        Message.require_confirmation()

        # Step 6: 进行文件重命名操作
        with console.status("正在重命名文件..."):
            # 生成重命名任务列表
            tasks_4_video_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in video_rename_list
            ]
            tasks_4_subtitle_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in subtitle_rename_list
            ]
            tasks_4_folder_rename_list: list[ApiTask] = [
                self.alist.rename(name=task.target_name, path=task.full_path)
                for task in folder_rename_list
            ]
            self._taskManager.add_tasks(
                *tasks_4_video_rename_list, *tasks_4_subtitle_rename_list
            )
            self._taskManager.run_tasks(self.config.amr.rename_by_async)
            if self.config.amr.media_folder_rename:
                self._taskManager.add_tasks(*tasks_4_folder_rename_list)
                self._taskManager.run_tasks(self.config.amr.rename_by_async)

        # Step 7: 输出重命名结果
        Message.print_rename_result(
            tasks_4_video_rename_list,
            tasks_4_subtitle_rename_list,
            tasks_4_folder_rename_list,
            self.config.amr.media_folder_rename,
        )

        return True

    # TAG: movie_rename_keyword
    def movie_rename_keyword(
        self, keyword: str, folder_path: str, folder_password=None
    ) -> bool:
        """
        根据TMDB电影关键字获取电影标题,并批量将Alist指定文件夹中的视频文件及字幕文件重命名为电影标题.

        :param keyword: 电影关键词
        :param folder_path: 文件夹路径
        :param folder_password: 文件夹访问密码
        :return: 重命名请求结果
        """

        ### ------------------------ 1. 查找 TMDB 电影信息 ------------------------ ####
        # Step 1: 使用关键词查找电影
        with console.status("查找指定电影..."):
            task_0_search_movie: ApiTask = self.tmdb.search_movie(
                keyword, self.config.tmdb.language
            )
            self._taskManager.add_tasks(task_0_search_movie)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # Step 2: 选择电影
        selected_number = Message.select_number(
            len(task_0_search_movie.response.data["results"])
        )
        logger.debug(f"选择电影: {selected_number}")
        movie_id = task_0_search_movie.response.data["results"][selected_number]["id"]
        movie_id: str = str(movie_id)

        # Step 3: 根据获取到的id调用 movie_rename_id 函数进行重命名
        self.movie_rename_id(movie_id, folder_path, folder_password)

        return True

    # TAG: movie_info_id
    def movie_info_id(self, movie_id: str) -> bool:
        """
        根据TMDB电影id获取电影标题,并输出查找信息.

        :param movie_id: 电影id
        :return: 重命名请求结果
        """

        logger.info(f"---Amr movie_info_id---\nmovie_id: {movie_id}\n")

        ### ------------------------ 1. 查找 TMDB 电影信息 ------------------------ ####
        # Step 1: 根据电影 id 查找 TMDB 电影信息
        logger.debug("查找指定电影...")
        with console.status("查找指定电影..."):
            task_2_movie_info: ApiTask = self.tmdb.movie_info(
                movie_id, self.config.tmdb.language
            )

            self._taskManager.add_tasks(task_2_movie_info)
            self._taskManager.run_tasks(self.config.amr.rename_by_async)

        ### ------------------------ 3. 匹配电影信息/文件列表 -------------------- ###
        # Step 3: 匹配电影信息/文件列表

        # 获取电影信息
        media_list, folder_media_list = Helper.create_movie_media_list(
            task_2_movie_info, movie_id, self.config
        )

        return True
