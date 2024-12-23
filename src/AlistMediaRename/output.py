from functools import wraps
import sys
from typing import Any, Union, Callable
from rich import box
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from .models import ApiResponseModel, RenameTask
from .utils import Tools


console = Console()


class Message:
    @staticmethod
    def config_input():
        url = Prompt.ask(
            Message.question("请输入Alist地址"), default="http://127.0.0.1:5244"
        )
        user = Prompt.ask(Message.question("请输入账号"))
        password = Prompt.ask(Message.question("请输入登录密码"))
        totp = Prompt.ask(
            Message.question(
                "请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请跳过"
            ),
            default="",
        )
        api_key = Prompt.ask(
            Message.question(
                "请输入TMDB API密钥，用于从TMDB获取剧集/电影信息\t申请链接: https://www.themoviedb.org/settings/api\n"
            )
        )
        return {
            "url": url,
            "user": user,
            "password": password,
            "totp": totp,
            "api_key": api_key,
        }

    @staticmethod
    def success(message: str, printf: bool = True):
        if printf:
            console.print(f":white_check_mark: {message}")
        return f":white_check_mark: {message}"

    @staticmethod
    def error(message: str, printf: bool = True):
        if printf:
            console.print(f":x: {message}")
        return f":x: {message}"

    @staticmethod
    def warning(message: str, printf: bool = True):
        if printf:
            console.print(f":warning:  {message}")
        return f":warning:  {message}"

    @staticmethod
    def ask(message: str, printf: bool = True):
        if printf:
            console.print(f":bell: {message}")
        return f":bell: {message}"

    @staticmethod
    def info(message: str, printf: bool = True):
        if printf:
            console.print(f":information:  {message}")
        return f":information:  {message}"

    @staticmethod
    def congratulation(message: str, printf: bool = True):
        if printf:
            console.print(f"\n:party_popper: {message}")
        return f":party_popper: {message}"

    @staticmethod
    def exit():
        from .api import sync_client

        sync_client.close()
        sys.exit(0)

    @staticmethod
    def question(message: str, printf: bool = True):
        if printf:
            console.print(f":abc: {message}")
        return f":abc: {message}"

    @staticmethod
    def text_regex(text: str):
        t = Text(text)
        # t.highlight_regex(r"\d(.*).", "cyan")
        # t.highlight_regex(r"^[^-]+", "blue")
        t.highlight_regex(r"(?<=E)\d+(?=.)", "bright_cyan")
        # t.highlight_regex(r"[^.]+(?=\.\w+$)", "magenta")
        return t


class Output:
    """打印消息类"""

    @staticmethod
    def output_alist_login(func) -> Callable[..., ApiResponseModel]:
        """
        输出登录状态信息
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs) -> ApiResponseModel:
            login_result: ApiResponseModel = func(self, *args, **kwargs)

            # 输出获取Token结果
            if login_result.success:
                Message.success(f"主页: {self.url}")
            else:
                Message.error(f"登录失败\t{login_result.error}")
            return login_result

        return wrapper

    @staticmethod
    def output_alist_file_list(func) -> Callable[..., ApiResponseModel]:
        """输出文件信息"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出结果
            if not return_data.success:
                Message.error(
                    f"获取文件列表失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.error}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_rename(func):
        """输出重命名信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 输出重命名结果
            # if return_data["message"] != "success":
            #     Message.error(
            #         f"重命名失败: {Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}\n{return_data.error}"
            #     )
            # else:
            #     Message.success(
            #         f"重命名路径:{Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}"
            #     )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_move(func) -> Callable[..., ApiResponseModel]:
        """输出文件移动信息"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出移动结果
            if not return_data.success:
                Message.error(
                    f"移动失败: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n   {return_data.error}"
                )
            else:
                Message.success(
                    f"移动路径: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_mkdir(func) -> Callable[..., ApiResponseModel]:
        """输出新建文件/文件夹信息"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出新建文件夹请求结果
            if not return_data.success:
                Message.error(
                    f"文件夹创建失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.error}"
                )
            else:
                Message.success(
                    f"文件夹创建路径: {Tools.get_argument(1, 'path', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_remove(func) -> Callable[..., ApiResponseModel]:
        """输出文件/文件夹删除信息"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出删除文件/文件夹请求结果
            if not return_data.success:
                Message.error(
                    f"删除失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.error}"
                )
            else:
                for name in Tools.get_argument(2, "name", args, kwargs):
                    Message.success(
                        f"删除路径: {Tools.get_argument(1, 'path', args, kwargs)}/{name}"
                    )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_info(func) -> Callable[..., ApiResponseModel]:
        """输出剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"tv_id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\n   {return_data.error}"
                )
                return return_data

            # 格式化输出请求结果
            first_air_year = return_data.data["first_air_date"][:4]
            name = return_data.data["name"]
            dir_name = f"{name} ({first_air_year})"
            Message.success(dir_name)
            seasons = return_data.data["seasons"]
            table = Table(box=box.SIMPLE)
            table.add_column("开播时间", justify="center", style="cyan")
            table.add_column("集数", justify="center", style="magenta")
            table.add_column("序号", justify="center", style="green")
            table.add_column("剧名", justify="left", no_wrap=True)
            # table.add_column(footer="共计: " + str(len(seasons)), style="grey53")
            for i, season in enumerate(seasons):
                table.add_row(
                    season["air_date"],
                    str(season["episode_count"]),
                    str(i),
                    season["name"],
                )
            console.print(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_tv(func):
        """输出查找剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n   {return_data.error}"
                )
                return return_data
            # if not return_data.data["results"]:
            #     Message.error(
            #         f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n    未查找到相关剧集"
            #     )
            #     return return_data

            Message.success(f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")
            table = Table(box=box.SIMPLE)
            table.add_column("开播时间", justify="center", style="cyan")
            table.add_column("序号", justify="center", style="green")
            table.add_column("剧名", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(return_data.data["results"]):
                table.add_row(r["first_air_date"], str(i), r["name"])
            console.print(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_season_info(func):
        """输出剧集季度信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"剧集id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\t第 {Tools.get_argument(2, 'season_number', args, kwargs)} 季\n   {return_data.error}"
                )

            return return_data

            # # 格式化输出请求结果
            # print(f"{Message.ColorStr.green('[✓]')} {return_data['name']}")
            # print(f"{'序 号':<6}{'放映日期':<12}{'时 长':<10}{'标 题'}")
            # print(f"{'----':<8}{'----------':<16}{'-----':<12}{'----------------'}")

            # for episode in return_data["episodes"]:
            #     print(
            #         f"{episode['episode_number']:<8}{episode['air_date']:<16}{str(episode['runtime']) + 'min':<12}{episode['name']}"
            #     )

            # # 返回请求结果
            # return return_data

        return wrapper

    @staticmethod
    def output_tmdb_movie_info(func):
        """输出电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"tv_id: {Tools.get_argument(1, 'movie_id', args, kwargs)}\n   {return_data.error}"
                )
                return return_data

            # 格式化输出请求结果
            Message.success(
                f"{return_data.data['title']} {return_data.data['release_date']}"
            )

            console.print(f"[标语] {return_data.data['tagline']}")

            console.print(f"[剧集简介] {return_data.data['overview']}")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_movie(func):
        """输出查找电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data.error}"
                )
                return return_data

            Message.success(f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")

            table = Table(box=box.SIMPLE)
            table.add_column("首播时间", justify="center", style="cyan")
            table.add_column("序号", justify="center", style="green")
            table.add_column("电影标题", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(return_data.data["results"]):
                table.add_row(r["release_date"], str(i), r["title"])
            console.print(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def print_rename_info(
        video_rename_list: list[RenameTask],
        subtitle_rename_list: list[RenameTask],
        folder_rename: bool,
        renamed_folder_title: Union[str, None],
        folder_path: str,
    ):
        """打印重命名信息"""
        if len(video_rename_list) > 0:
            Message.info(f"以下视频文件将会重命名: 共计 {len(video_rename_list)}")
            table = Table(box=box.SIMPLE)
            table.add_column("原文件名", justify="left", style="grey53", no_wrap=True)
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left", no_wrap=True)
            for video in video_rename_list:
                table.add_row(
                    Message.text_regex(video.original_name),
                    "->",
                    Message.text_regex(video.target_name),
                )
            console.print(table)
        if len(subtitle_rename_list) > 0:
            Message.info(f"以下字幕文件将会重命名: 共计 {len(subtitle_rename_list)}")
            table = Table(box=box.SIMPLE)
            table.add_column("原文件名", justify="left", style="grey53", no_wrap=True)
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left", no_wrap=True)
            for subtitle in subtitle_rename_list:
                table.add_row(
                    Message.text_regex(subtitle.original_name),
                    "->",
                    Message.text_regex(subtitle.target_name),
                )
            console.print(table)
        if folder_rename:
            Message.info(
                f"文件夹重命名: [grey53]{folder_path.split('/')[-2]}[/grey53] [grey70]->[/grey70] {renamed_folder_title}"
            )

    @staticmethod
    def require_confirmation() -> bool:
        """确认操作"""

        signal = Confirm.ask(
            Message.warning("确定要重命名吗? ", printf=False), default=True
        )

        if signal:
            return True
        else:
            Message.congratulation("See you!")
            Message.exit()
            return False

    @staticmethod
    def select_number(result_list: list[Any]) -> int:
        """根据查询结果选择序号"""
        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(result_list) == 1:
            return 0
        else:
            while True:
                # 获取到多项匹配结果，手动选择
                number = Prompt.ask(
                    Message.ask(
                        "查询到以上结果，请输入对应[green]序号[/green], 输入[red] n [/red]退出",
                        printf=False,
                    )
                )
                if number.lower() == "n":
                    Message.congratulation("See you!")
                    Message.exit()
                if number.isdigit() and 0 <= int(number) < len(result_list):
                    return int(number)

    @staticmethod
    def print_rename_result(
        results: list[ApiResponseModel],
        video_count: int,
        subtitle_count: int,
        folder_count: int,
    ):
        """打印重命名结果"""

        video_error_count = 0
        subtitle_error_count = 0
        folder_error_count = 0
        error_list: list[ApiResponseModel] = []

        # 统计视频重命名结果
        for i in range(video_count):
            if not results[i].success:
                video_error_count += 1
                error_list.append(results[i])

        # 统计字幕重命名结果
        for i in range(video_count, video_count + subtitle_count):
            if not results[i].success:
                subtitle_error_count += 1
                error_list.append(results[i])

        # 统计文件夹重命名结果
        if not results[-1].success:
            folder_error_count += 1
            error_list.append(results[-1])

        # 输出错误信息
        if video_error_count + subtitle_error_count + folder_error_count > 0:
            table = Table(box=box.SIMPLE, title="重命名失败列表")
            table.add_column("原文件名", justify="left", style="grey53")
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left")
            table.add_column("错误信息", justify="left")
            for result in error_list:
                table.add_row(
                    result.args[1].split("/")[-1],
                    "->",
                    Message.text_regex(result.args[0]),
                    result.error,
                )
            console.print(table)

        # 输出重命名结果，成功失败数量
        if video_error_count > 0 and video_count > 0:
            Message.error(
                f"视频文件:  成功 [green]{video_count - video_error_count}[/green], 失败 [red]{video_error_count}[/red]"
            )
        elif video_error_count == 0 and video_count > 0:
            Message.success(f"视频文件: 成功 [green]{video_count}[/green]")
        if subtitle_error_count > 0 and subtitle_count > 0:
            Message.error(
                f"字幕文件: 成功 [green]{subtitle_count - subtitle_error_count}[/green], 失败 [red]{subtitle_error_count}[/red]"
            )
        elif subtitle_error_count == 0 and subtitle_count > 0:
            Message.success(f"字幕文件: 成功 [green]{subtitle_count}[/green]")
        if folder_error_count > 0 and folder_count > 0:
            Message.error(
                f"父文件夹: 成功 [green]{folder_count - folder_error_count}[/green], 失败 [red]{folder_error_count}[/red]"
            )
        elif folder_error_count == 0 and folder_count > 0:
            Message.success(f"父文件夹: 成功 [green]{folder_count}[/green]")

        # 程序运行结束
        Message.congratulation("重命名完成")
        Message.exit()
