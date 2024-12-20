from typing import Union

from .api import AlistApi, TMDBApi
from .config import Config
from .log import logger  # noqa: F401
from .models import ApiResponseModel, Formated_Variables, RenameTask
from .output import Output, console
from .utils import Tools


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

        with console.status("登录Alist..."):
            # 初始化 AlistApi 和 TMDBApi
            self.alist = AlistApi(
                self.config.alist.url,
                self.config.alist.user,
                self.config.alist.password,
                self.config.alist.totp,
            )
            self.tmdb = TMDBApi(self.config.tmdb.api_url, self.config.tmdb.api_key)

            # Step 0: 登录Alist
            self.alist.login()

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

        # 确保路径以 / 开头并以 / 结尾
        folder_path = Tools.ensure_slash(folder_path)

        ### ------------------------ 获取文件列表 ------------------------ ####
        with console.status("获取文件列表..."):
            # Step 1: 刷新文件夹所在父文件夹，防止Alist未及时刷新，导致无法获取文件列表
            self.alist.file_list(
                Tools.get_parent_path(folder_path), folder_password, True
            )
            # Step 2: 获取文件夹列表
            result_file_list: ApiResponseModel = self.alist.file_list(
                folder_path, folder_password, True
            )

        ### ------------------------ 获取 TMDB 剧集/季度信息 ------------------------ ####
        # TODO: 修改电影输出信息
        # Step 3: 根据剧集 id 查找 TMDB 剧集信息
        with console.status("查找指定剧集..."):
            result_tv_info: ApiResponseModel = self.tmdb.tv_info(
                tv_id, self.config.tmdb.language
            )

        # Step 4: 根据查找信息选择季度
        season_number = Output.select_number(result_tv_info.data["seasons"])
        season_number = result_tv_info.data["seasons"][season_number]["season_number"]

        # Step 5: 获取剧集对应季每集信息
        with console.status("获取季度信息..."):
            result_tv_season_info: ApiResponseModel = self.tmdb.tv_season_info(
                tv_id, season_number, self.config.tmdb.language
            )

        ### ------------------------ 匹配剧集信息-文件列表 -------------------- ###
        # Step 5: 匹配剧集信息-文件列表
        fv_tv = Formated_Variables.tv(
            name=result_tv_info.data["name"],
            original_name=result_tv_info.data["original_name"],
            year=result_tv_info.data["first_air_date"][:4],
            first_air_date=result_tv_info.data["first_air_date"],
            language=result_tv_info.data["original_language"],
            region=result_tv_info.data["origin_country"][0],
            rating=result_tv_info.data["vote_average"],
            season=result_tv_season_info.data["season_number"],
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
                result_tv_season_info.data["episodes"],
            )
        )
        episode_list_subtitle = episode_list_video.copy()

        # 获取文件列表
        file_list = list(map(lambda x: x["name"], result_file_list.data["content"]))
        # 筛选视频文件和字幕文件
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )

        # 匹配剧集信息/文件列表
        video_rename_list: list[RenameTask] = Tools.match_episode_files(
            video_list,
            episode_list_video,
            folder_path,
            self.config.amr.exclude_renamed,
            first_number,
        )
        subtitle_rename_list: list[RenameTask] = Tools.match_episode_files(
            subtitle_list,
            episode_list_subtitle,
            folder_path,
            self.config.amr.exclude_renamed,
            first_number,
        )

        # 获取父文件夹重命名标题
        folder_rename_title = self.config.amr.folder_name_format.format(**vars(fv_tv))

        ### ------------------------ 4. 进行重命名操作 -------------------- ###

        # Step 6: 输出重命名文件信息
        Output.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            self.config.amr.media_folder_rename,
            folder_rename_title,
            folder_path,
        )

        # Step 7: 等待用户确认
        Output.require_confirmation()

        # Step 8: 进行文件重命名操作
        with console.status("正在重命名文件..."):
            # 重命名文件
            result_rename_list: list[ApiResponseModel] = self.alist.rename_list(
                video_rename_list + subtitle_rename_list,
                async_mode=self.config.amr.rename_by_async,
            )

            # 重命名父文件夹 格式: 复仇者联盟 (2012)
            folder_count = 0
            if self.config.amr.media_folder_rename:
                folder_count = 1
                folder_rename_list: list[RenameTask] = [
                    RenameTask(
                        original_name="",
                        target_name=folder_rename_title,
                        folder_path=folder_path,
                    )
                ]
                result_folder_rename: list[ApiResponseModel] = self.alist.rename_list(
                    folder_rename_list, async_mode=self.config.amr.rename_by_async
                )
            else:
                result_folder_rename = [
                    ApiResponseModel(
                        success=True,
                        status_code=200,
                        error="",
                        data={"result": "未重命名父文件夹"},
                        function="重命名父文件夹",
                        args=(),
                        kwargs={},
                    )
                ]

        # Step 9: 输出重命名结果
        # TODO: 使用装饰器输出重命名结果
        Output.print_rename_result(
            result_rename_list + result_folder_rename,
            len(video_rename_list),
            len(subtitle_rename_list),
            folder_count,
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

        ### ------------------------ 1. 查找 TMDB 剧集信息 ------------------------ ####
        # Step 1: 使用关键词查找剧集
        with console.status("查找指定剧集..."):
            result_search_tv: ApiResponseModel = self.tmdb.search_tv(
                keyword, self.config.tmdb.language
            )

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # Step 2: 选择剧集
        selected_number = Output.select_number(result_search_tv.data["results"])
        tv_id = result_search_tv.data["results"][selected_number]["id"]

        # Step 3: 根据获取到的id调用 tv_rename_id 函数进行重命名
        self.tv_rename_id(tv_id, folder_path, folder_password, first_number)

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

        # 确保路径以 / 开头并以 / 结尾
        folder_path = Tools.ensure_slash(folder_path)

        ### ------------------------ 1. 获取文件列表 -------------------- ###
        with console.status("获取文件列表..."):
            # Step 1: 刷新文件夹所在父文件夹，防止Alist为及时刷新，导致无法获取文件列表
            self.alist.file_list(
                Tools.get_parent_path(folder_path), folder_password, True
            )

            # Step 2: 获取文件夹列表
            result_file_list: ApiResponseModel = self.alist.file_list(
                folder_path, folder_password, True
            )

        ### ------------------------ 2. 查找 TMDB 电影信息 ------------------------ ####
        # Step 1: 根据电影 id 查找 TMDB 电影信息
        with console.status("查找指定电影..."):
            result_movie_info: ApiResponseModel = self.tmdb.movie_info(
                movie_id, self.config.tmdb.language
            )

        ### ------------------------ 3. 匹配电影信息/文件列表 -------------------- ###
        # Step 3: 匹配电影信息/文件列表
        fv_movie = Formated_Variables.movie(
            name=result_movie_info.data["title"],
            original_name=result_movie_info.data["original_title"],
            year=result_movie_info.data["release_date"][:4],
            release_date=result_movie_info.data["release_date"],
            language=result_movie_info.data["original_language"],
            region=result_movie_info.data["origin_country"][0],
            rating=result_movie_info.data["vote_average"],
        )

        # 创建包含源文件名以及目标文件名列表
        target_name = self.config.amr.movie_name_format.format(**vars(fv_movie))

        file_list = list(map(lambda x: x["name"], result_file_list.data["content"]))
        video_list = Tools.filter_file(file_list, self.config.amr.video_regex_pattern)
        subtitle_list = Tools.filter_file(
            file_list, self.config.amr.subtitle_regex_pattern
        )
        # 匹配剧集信息/文件列表
        video_rename_list: list[RenameTask] = Tools.match_episode_files(
            video_list, [target_name], folder_path, self.config.amr.exclude_renamed, "1"
        )
        subtitle_rename_list: list[RenameTask] = Tools.match_episode_files(
            subtitle_list,
            [target_name],
            folder_path,
            self.config.amr.exclude_renamed,
            "1",
        )
        # 获取父文件夹重命名标题
        folder_rename_title = self.config.amr.folder_name_format.format(
            **vars(fv_movie)
        )

        ### ------------------------ 4. 进行重命名操作 -------------------- ###
        # Step 4: 输出重命名文件信息
        Output.print_rename_info(
            video_rename_list,
            subtitle_rename_list,
            self.config.amr.media_folder_rename,
            folder_rename_title,
            folder_path,
        )

        # Step 5: 等待用户确认
        Output.require_confirmation()

        # Step 6: 进行文件重命名操作
        with console.status("正在重命名文件..."):
            # 重命名文件
            result_rename_list: list[ApiResponseModel] = self.alist.rename_list(
                video_rename_list + subtitle_rename_list,
                async_mode=self.config.amr.rename_by_async,
            )

            # 重命名父文件夹 格式: 复仇者联盟 (2012)
            folder_count = 0
            if self.config.amr.media_folder_rename:
                folder_count = 1
                folder_rename_list: list[RenameTask] = [
                    RenameTask(
                        original_name="",
                        target_name=folder_rename_title,
                        folder_path=folder_path,
                    )
                ]
                result_folder_rename: list[ApiResponseModel] = self.alist.rename_list(
                    folder_rename_list, async_mode=self.config.amr.rename_by_async
                )
            else:
                result_folder_rename = [
                    ApiResponseModel(
                        success=True,
                        status_code=200,
                        error="",
                        data={"result": "未重命名父文件夹"},
                        function="重命名父文件夹",
                        args=(),
                        kwargs={},
                    )
                ]

        # Step 7: 输出重命名结果
        Output.print_rename_result(
            result_rename_list + result_folder_rename,
            len(video_rename_list),
            len(subtitle_rename_list),
            folder_count,
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
            result_search_movie: ApiResponseModel = self.tmdb.search_movie(
                keyword, self.config.tmdb.language
            )

        ### ------------------------ 2. 获取剧集 TMDB ID ------------------------------ ###
        # Step 2: 选择电影
        selected_number = Output.select_number(result_search_movie.data["results"])
        movie_id = result_search_movie.data["results"][selected_number]["id"]

        # Step 3: 根据获取到的id调用 movie_rename_id 函数进行重命名
        self.movie_rename_id(movie_id, folder_path, folder_password)

        return True
