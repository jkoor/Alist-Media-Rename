import re
from typing import Union
from natsort import natsorted
from .models import RenameTask


class Tools:
    """
    工具函数类
    """

    @staticmethod
    def ensure_slash(path: str) -> str:
        """确保路径以 / 开头并以 / 结尾"""
        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path = path + "/"
        return path

    @staticmethod
    def get_parent_path(path: str) -> str:
        """获取父目录路径"""
        path = Tools.ensure_slash(path)
        return path[: path[:-1].rfind("/") + 1]

    @staticmethod
    def filter_file(file_list: list, pattern: str) -> list:
        """筛选列表，并以自然排序返回"""

        return natsorted([file for file in file_list if re.match(pattern, file)])

    @staticmethod
    def parse_page_ranges(page_ranges: str, total_pages: int) -> list:
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

    @staticmethod
    def match_episode_files(
        original_list: list[str],
        target_list: list[str],
        folder_path: str,
        exclude_renamed: bool,
        first_number: str = "1",
    ) -> list[RenameTask]:
        """匹配文件"""

        # 创建重命名列表
        rename_list_no_filter: list[RenameTask] = []
        # 创建排除已重命名的列表
        rename_list_filter: list[RenameTask] = []

        # 创建hash表和队列
        rename_list: list[RenameTask] = [RenameTask()] * len(target_list)
        target_dict: dict[str, int] = {item: i for i, item in enumerate(target_list)}
        queue = []

        # 优先匹配已重命名的文件
        for i, item in enumerate(original_list):
            if item.rsplit(".", 1)[0] in target_list:
                rename_list[target_dict[item.rsplit(".", 1)[0]]] = RenameTask(
                    original_name=item, target_name=item, folder_path=folder_path
                )
            else:
                queue.append(item)

        # 匹配未重命名的文件
        for i in range(len(target_list)):
            if rename_list[i] != RenameTask():
                rename_list_no_filter.append(rename_list[i])
            if (
                rename_list[i] == RenameTask()
                and len(queue) > 0
                and i + 1 in Tools.parse_page_ranges(first_number, len(target_list))
            ):
                original_name: str = queue.pop(0)
                target_name = target_list[i] + "." + original_name.rsplit(".", 1)[1]
                rename_list_no_filter.append(
                    RenameTask(
                        original_name=original_name,
                        target_name=target_name,
                        folder_path=folder_path,
                    )
                )
                rename_list_filter.append(
                    RenameTask(
                        original_name=original_name,
                        target_name=target_name,
                        folder_path=folder_path,
                    )
                )

        return rename_list_filter if exclude_renamed else rename_list_no_filter

    @staticmethod
    def get_argument(
        arg_index: int, kwarg_name: str, args: Union[list, tuple], kwargs: dict
    ) -> str:
        """获取参数"""
        if len(args) > arg_index:
            return args[arg_index]
        return kwargs[kwarg_name]

    @staticmethod
    def get_renamed_folder_title(
        tv_info_result, tv_season_info, folder_path, rename_type, tv_season_format
    ) -> str:
        """文件夹重命名类型"""
        if rename_type == 1:
            renamed_folder_title = (
                f"{tv_info_result['name']} ({tv_info_result['first_air_date'][:4]})"
            )
        elif rename_type == 2:
            renamed_folder_title = tv_season_format.format(
                season=tv_season_info["season_number"],
                name=tv_info_result["name"],
                year=tv_info_result["first_air_date"][:4],
            )
        else:
            renamed_folder_title = ""
        return renamed_folder_title

    @staticmethod
    def replace_illegal_char(filename: str, extend=True) -> str:
        """替换非法字符"""
        illegal_char = r"[\/:*?\"<>|]" if extend else r"[/]"
        return re.sub(illegal_char, "_", filename)
