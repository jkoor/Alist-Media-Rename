import re
from natsort import natsorted

from AlistMediaRename.models import ApiResponse
from .config import Config
from .models import MediaMeta, Formated_Variables, FileMeta, RenameTask, Folder
from .task import ApiTask


class Utils:
    """
    工具函数类
    """

    @staticmethod
    def filter_file(file_list: list[str], pattern: str) -> list[str]:
        """筛选列表，并以自然排序返回"""

        return natsorted([file for file in file_list if re.match(pattern, file)])

    @staticmethod
    def parse_page_ranges(page_ranges: str, total_pages: int) -> list[int]:
        """
        解析分页格式的字符串，并返回一个包含所有项的列表。

        示例:
        输入: "1,2-4,7,10-13", 11
        输出: [1, 2, 3, 4, 7, 10, 11]

        输入: "3", 13
        输出: [3]

        输入: "3-", 13
        输出: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        """
        pages = []
        ranges = page_ranges.split(",")
        for r in ranges:
            if not r:
                continue
            if "-" in r:
                start, end = r.split("-")
                start = int(start)
                end = int(end) if end and int(end) <= total_pages else total_pages
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(r))

        # 去重并排序
        pages = sorted(set(pages))
        return pages


class Helper:
    @staticmethod
    def create_tv_media_list(
        first_number: str,
        task_2_tv_info: ApiTask,
        task_3_tv_season_info: ApiTask,
        tmdb_id: str,
        config: Config,
    ) -> tuple[list[MediaMeta], list[MediaMeta]]:
        """创建媒体元数据"""

        # 创建格式化变量
        fv_tv = Formated_Variables.tv(
            name=task_2_tv_info.response.data["name"],
            original_name=task_2_tv_info.response.data["original_name"],
            year=task_2_tv_info.response.data["first_air_date"][:4],
            first_air_date=task_2_tv_info.response.data["first_air_date"],
            language=task_2_tv_info.response.data["original_language"],
            region=task_2_tv_info.response.data["origin_country"][0],
            rating=task_2_tv_info.response.data["vote_average"],
            season=task_3_tv_season_info.response.data["season_number"],
            season_year=task_3_tv_season_info.response.data["air_date"][:4]
            if task_3_tv_season_info.response.data["air_date"]
            else "0000",
            tmdb_id=tmdb_id,
        )

        # 提取 episode_number 列表
        episode_numbers = [
            ep["episode_number"]
            for ep in task_3_tv_season_info.response.data["episodes"]
        ]

        # 创建媒体元数据列表
        indexs: list[int] = Utils.parse_page_ranges(
            first_number,
            max(episode_numbers) if episode_numbers else 1,
        )

        # 取交集
        indexs = list(set(indexs) & set(episode_numbers))

        media_list: list[MediaMeta] = []
        for ep in task_3_tv_season_info.response.data["episodes"]:
            if ep["episode_number"] not in indexs:
                continue

            # FIXME: 处理没有日期的空剧集
            # 创建格式化变量
            try:
                fv_episode = Formated_Variables.episode(
                    episode=ep["episode_number"],
                    air_date=ep["air_date"],
                    episode_rating=ep["vote_average"],
                    title=ep["name"],
                )
            except Exception:
                continue

            media_list.append(
                MediaMeta(
                    media_type="tv",
                    rename_format=config.amr.tv_name_format,
                    movie_format_variables=None,
                    tv_format_variables=fv_tv,
                    episode_format_variables=fv_episode,
                )
            )

        # 创建文件夹媒体元数据列表
        folder_media_list: list[MediaMeta] = [
            MediaMeta(
                media_type="tv",
                rename_format=config.amr.tv_folder_name_format,
                movie_format_variables=None,
                tv_format_variables=fv_tv,
                episode_format_variables=None,
            )
        ]

        return media_list, folder_media_list

    @staticmethod
    def create_movie_media_list(
        task_2_movie_info: ApiTask,
        tmdb_id: str,
        config: Config,
    ) -> tuple[list[MediaMeta], list[MediaMeta]]:
        """创建媒体元数据"""

        # 创建格式化变量
        fv_movie = Formated_Variables.movie(
            name=task_2_movie_info.response.data["title"],
            original_name=task_2_movie_info.response.data["original_title"],
            collection_name=task_2_movie_info.response.data["belongs_to_collection"][
                "name"
            ]
            if task_2_movie_info.response.data["belongs_to_collection"]
            else "",
            year=task_2_movie_info.response.data["release_date"][:4],
            release_date=task_2_movie_info.response.data["release_date"],
            language=task_2_movie_info.response.data["original_language"],
            region=task_2_movie_info.response.data["origin_country"][0],
            rating=task_2_movie_info.response.data["vote_average"],
            tmdb_id=tmdb_id,
        )
        # 创建媒体元数据列表
        indexs: list[int] = [1]
        media_list: list[MediaMeta] = []
        for i in indexs:
            media_list.append(
                MediaMeta(
                    media_type="movie",
                    rename_format=config.amr.movie_name_format,
                    movie_format_variables=fv_movie,
                    tv_format_variables=None,
                    episode_format_variables=None,
                )
            )
        # 创建文件夹媒体元数据列表
        folder_media_list: list[MediaMeta] = [
            MediaMeta(
                media_type="movie",
                rename_format=config.amr.tv_folder_name_format,
                movie_format_variables=fv_movie,
                tv_format_variables=None,
                episode_format_variables=None,
            )
        ]

        return media_list, folder_media_list

    @staticmethod
    def create_file_list(
        task_1_file_list: ApiTask,
        folder_path: Folder,
        config: Config,
    ) -> tuple[list[FileMeta], list[FileMeta]]:
        """创建文件列表"""

        result_file_list: ApiResponse = task_1_file_list.response

        file_list: list[str] = list(
            map(lambda x: x["name"], result_file_list.data["content"])
        )

        video_file_list: list[FileMeta] = [
            FileMeta(filename=file, folder_path=folder_path)
            for file in Utils.filter_file(file_list, config.amr.video_regex_pattern)
        ]
        subtitle_file_list: list[FileMeta] = [
            FileMeta(filename=file, folder_path=folder_path)
            for file in Utils.filter_file(file_list, config.amr.subtitle_regex_pattern)
        ]
        return video_file_list, subtitle_file_list

    @staticmethod
    def match_episode_files(
        media_list: list[MediaMeta], file_list: list[FileMeta], config: Config
    ) -> list[RenameTask]:
        """匹配文件"""

        # 创建完整列表
        rename_list_all: list[RenameTask] = []
        # 文件名已符合要求，不需要重命名的列表
        rename_list_matched: list[RenameTask] = []
        # 创建排除已重命名的列表
        rename_list_no_matched: list[RenameTask] = []

        # 创建待重命名队列
        pending_file_list: list[FileMeta] = []
        pending_media_list: list[MediaMeta] = media_list.copy()

        # 优先匹配已重命名的文件
        for i, file in enumerate(file_list):
            is_matched = False
            j = -1
            for _, media in enumerate(pending_media_list):
                if file.prefix_name == media.fullname:
                    rename_list_matched.append(
                        RenameTask(media_meta=media, file_meta=file)
                    )
                    is_matched = True
                    j = _
                    break
            if is_matched:
                pending_media_list.pop(j)
            else:
                pending_file_list.append(file)

        # 匹配未重命名的文件
        for file, meida in zip(pending_file_list, pending_media_list):
            rename_list_no_matched.append(RenameTask(media_meta=meida, file_meta=file))

        # 匹配全部文件
        for file, meida in zip(file_list, media_list):
            rename_list_all.append(RenameTask(media_meta=media, file_meta=file))

        return rename_list_no_matched if config.amr.exclude_renamed else rename_list_all

    @staticmethod
    def create_folder_rename_list(
        folder_path: Folder, folder_media_list: list[MediaMeta]
    ) -> list[RenameTask]:
        """创建文件夹重命名列表"""

        file: FileMeta = FileMeta(
            filename=folder_path.current_path(),
            folder_path=Folder(path=folder_path.parent_path()),
        )
        folder_rename_list: list[RenameTask] = [
            RenameTask(media_meta=media, file_meta=file) for media in folder_media_list
        ]

        return folder_rename_list
