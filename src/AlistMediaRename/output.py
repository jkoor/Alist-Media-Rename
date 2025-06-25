import logging
from typing import Callable
from rich import box
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from .models import RenameTask, MediaMeta
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import ApiTask


console = Console()
logger = logging.getLogger("Amr.Output")


class UserExit(Exception):
    pass
    # sys.exit(0)


class Message:
    @staticmethod
    def config_input():
        url = Prompt.ask(
            Message.question("请输入Alist地址", printf=False),
            default="http://127.0.0.1:5244",
        )
        user = Prompt.ask(Message.question("请输入账号", printf=False))
        password = Prompt.ask(Message.question("请输入登录密码", printf=False))
        totp = Prompt.ask(
            Message.question(
                "请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请跳过",
                printf=False,
            ),
            default="",
        )
        api_key = Prompt.ask(
            Message.question(
                "请输入TMDB API密钥，用于从TMDB获取剧集/电影信息\t申请链接: https://www.themoviedb.org/settings/api\n",
                printf=False,
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
        log_message = f":white_check_mark: {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def error(message: str, printf: bool = True):
        log_message = f":x: {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def warning(message: str, printf: bool = True):
        log_message = f":warning:  {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def ask(message: str, printf: bool = True):
        log_message = f":bell: {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def info(message: str, printf: bool = True):
        log_message = f":information:  {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def congratulation(message: str, printf: bool = True):
        log_message = f"\n:party_popper: {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def exit():
        # raise UserExit("用户主动退出")
        log_message = "用户主动退出"
        logger.debug(log_message)
        sys.exit(1)

    @staticmethod
    def question(message: str, printf: bool = True):
        log_message = f":abc: {message}"
        logger.debug(log_message)
        # 如果printf为True，则打印到控制台
        if printf:
            console.print(log_message)
        return log_message

    @staticmethod
    def text_regex(text: str):
        t = Text(text)
        # t.highlight_regex(r"\d(.*).", "cyan")
        # t.highlight_regex(r"^[^-]+", "blue")
        t.highlight_regex(r"(?<=E)\d+(?=.)", "bright_cyan")
        # t.highlight_regex(r"[^.]+(?=\.\w+$)", "magenta")
        return t

    @staticmethod
    def print_rename_info(
        video_rename_list: list[RenameTask],
        subtitle_rename_list: list[RenameTask],
        folder_rename_list: list[RenameTask],
        folder_rename: bool,
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
                    logger.debug(f"{video.original_name} -> {video.target_name}"),
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
                logger.debug(f"{subtitle.original_name} -> {subtitle.target_name}")
            console.print(table)
        if folder_rename:
            Message.info(
                f"文件夹重命名: [grey53]{folder_rename_list[0].original_name}[/grey53] [grey70]->[/grey70] {folder_rename_list[0].target_name}"
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
    def select_number(length: int) -> int:
        """根据查询结果选择序号"""
        # 若查找结果只有一项，则无需选择，直接进行下一步
        if length == 1:
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
                if number.isdigit() and 0 <= int(number) < length:
                    return int(number)

    @staticmethod
    def print_rename_result(
        tasks_4_video_rename_list: list["ApiTask"],
        tasks_4_subtitle_rename_list: list["ApiTask"],
        tasks_4_folder_rename_list: list["ApiTask"],
        folder_rename: bool,
    ):
        """打印重命名结果"""

        video_count = len(tasks_4_video_rename_list)
        video_error_count = 0
        subtitle_count = len(tasks_4_subtitle_rename_list)
        subtitle_error_count = 0
        folder_count = len(tasks_4_folder_rename_list) if folder_rename else 0
        folder_error_count = 0
        error_list: list["ApiTask"] = []

        # 统计视频重命名结果
        for task in tasks_4_video_rename_list:
            if not task.response.success:
                video_error_count += 1
                error_list.append(task)

        # 统计字幕重命名结果
        for task in tasks_4_subtitle_rename_list:
            if not task.response.success:
                subtitle_error_count += 1
                error_list.append(task)

        # 统计文件夹重命名结果
        for task in tasks_4_folder_rename_list:
            if not task.response.success:
                folder_error_count += 1
                error_list.append(task)

        # 输出错误信息
        if video_error_count + subtitle_error_count + folder_error_count > 0:
            table = Table(box=box.SIMPLE, title="重命名失败列表")
            table.add_column("原文件名", justify="left", style="grey53")
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left")
            table.add_column("错误信息", justify="left")
            for task in error_list:
                table.add_row(
                    task.args["path"].split("/")[-1],
                    "->",
                    Message.text_regex(task.args["name"]),
                    task.response.error,
                )
                logger.debug(
                    f"重命名失败: {task.args['path'].split('/')[-1]} -> {task.args['name']}, 错误信息: {task.response.error}"
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

    @staticmethod
    def print_tv_info(media_list: list["MediaMeta"]) -> None:
        """打印剧集信息"""

        if len(media_list) == 0:
            Message.error("未找到剧集信息")
            return

        table = Table(box=box.SIMPLE)
        table.add_column("播放日期", justify="left", style="cyan")
        table.add_column("序号", justify="center", style="magenta")
        # table.add_column("评分", justify="center", style="green")
        table.add_column("剧集名称", justify="left", style="green")
        table.add_column("重命名标题", justify="left")

        for media in media_list:
            if media.media_type == "tv" and media.episode_format_variables:
                table.add_row(
                    media.episode_format_variables.air_date,
                    str(round(media.episode_format_variables.episode, 2)),
                    media.episode_format_variables.title,
                    media.fullname,
                )
            else:
                logger.warning(f"MediaMeta类型错误: {media.media_type}")

        console.print(table)


class OutputParser:
    """打印消息类"""

    @staticmethod
    def parser(type: str) -> Callable[..., None]:
        """设置解析器"""

        PARSER_MAP = {
            "slient": OutputParser.slient_output,
            "default": OutputParser.default_output,
            "login": OutputParser.output_alist_login,
            "file_list": OutputParser.output_alist_file_list,
            "rename": OutputParser.output_alist_rename,
            "move": OutputParser.output_alist_move,
            "mkdir": OutputParser.output_alist_mkdir,
            "remove": OutputParser.output_alist_remove,
            "tv_info": OutputParser.output_tmdb_tv_info,
            "search_tv": OutputParser.output_tmdb_search_tv,
            "tv_season_info": OutputParser.output_tmdb_tv_season_info,
            "movie_info": OutputParser.output_tmdb_movie_info,
            "search_movie": OutputParser.output_tmdb_search_movie,
        }

        if type in PARSER_MAP:
            return PARSER_MAP[type]
        else:
            raise ValueError(f"OutputParser '{type}' not found")

    @staticmethod
    def slient_output(api_task: "ApiTask") -> None:
        """静默输出"""
        pass

    @staticmethod
    def default_output(api_task: "ApiTask") -> None:
        """默认输出"""

        # 输出请求结果
        if api_task.response.success:
            Message.success(f"请求成功: {api_task.args}")
        else:
            Message.error(f"请求失败: {api_task.args}\n   {api_task.response.error}")

    @staticmethod
    def output_alist_login(api_task: "ApiTask") -> None:
        """
        输出登录状态信息
        """

        # 输出获取Token结果
        if api_task.response.success:
            Message.success("登陆成功")
        else:
            Message.error("登录失败")

    @staticmethod
    def output_alist_file_list(api_task: "ApiTask") -> None:
        """输出文件信息"""

        # 输出结果
        if not api_task.response.success:
            Message.error(
                f"获取文件列表失败: {api_task.args.get('path')}\n   {api_task.response.error}"
            )

    @staticmethod
    def output_alist_rename(api_task: "ApiTask") -> None:
        """输出重命名信息"""

        pass
        # 输出重命名结果
        if not api_task.response.success:
            Message.error(
                f"重命名失败: {api_task.args.get('path', '').split('/')[-1]} -> {api_task.args.get('name')}"
            )
        else:
            Message.success(
                f"重命名路径: {api_task.args.get('path', '').split('/')[-1]} -> {api_task.args.get('name')}"
            )

    @staticmethod
    def output_alist_move(api_task: "ApiTask") -> None:
        """输出文件移动信息"""

        # 输出移动结果
        if api_task.response.success:
            Message.success(
                f"移动路径: {api_task.args.get('src_dir')} -> {api_task.args.get('dst_dir')}"
            )
        else:
            Message.error(
                f"移动失败: {api_task.args.get('src_dir')} -> {api_task.args.get('dst_dir')}"
            )

    @staticmethod
    def output_alist_mkdir(api_task: "ApiTask") -> None:
        """输出新建文件/文件夹信息"""

        # 输出新建文件夹请求结果
        if api_task.response.success:
            Message.success(f"文件夹创建路径: {api_task.args.get('path')}")
        else:
            Message.error(f"文件夹创建失败: {api_task.args.get('path')}")

    @staticmethod
    def output_alist_remove(api_task: "ApiTask") -> None:
        """输出文件/文件夹删除信息"""

        # 输出删除文件/文件夹请求结果
        if api_task.response.success:
            for name in api_task.args.get("name", []):
                Message.success(f"删除路径: {api_task.args.get('path')}/{name}")
        else:
            Message.error(f"删除失败: {api_task.args.get('path')}")

    @staticmethod
    def output_tmdb_tv_info(api_task: "ApiTask") -> None:
        """输出剧集信息"""

        # 请求失败则输出失败信息
        if api_task.response.success:
            # 格式化输出请求结果
            first_air_year = api_task.response.data["first_air_date"][:4]
            name = api_task.response.data["name"]
            dir_name = f"{name} ({first_air_year})"
            Message.success(dir_name)
            seasons = api_task.response.data["seasons"]
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
                logger.debug(
                    f"剧集信息: {season['name']} ({season['air_date']}) 集数: {season['episode_count']}"
                )
            console.print(table)
        else:
            Message.error(f"tv_id: {api_task.args.get('tv_id')}")

    @staticmethod
    def output_tmdb_search_tv(api_task: "ApiTask") -> None:
        """输出查找剧集信息"""

        # 输出请求结果
        if api_task.response.success:
            Message.success(f"关键词: {api_task.args.get('keyword')}")
            table = Table(box=box.SIMPLE)
            table.add_column("开播时间", justify="center", style="cyan")
            table.add_column("TMDB ID", justify="center", style="magenta")
            table.add_column("序号", justify="center", style="green")
            table.add_column("剧名", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(api_task.response.data["results"]):
                table.add_row(r["first_air_date"], str(r["id"]), str(i), r["name"])
                logger.debug(
                    f"剧集信息: {r['name']} ({r['first_air_date']}) TMDB ID: {r['id']}"
                )
            console.print(table)
        else:
            Message.error(f"关键词: {api_task.args.get('keyword')}")

    @staticmethod
    def output_tmdb_tv_season_info(api_task: "ApiTask") -> None:
        """输出剧集季度信息"""

        # 请求失败则输出失败信息
        if not api_task.response.success:
            Message.error(
                f"剧集id: {api_task.args.get('tv_id')}\t第 {api_task.args.get('season_number')} 季"
            )

    @staticmethod
    def output_tmdb_movie_info(api_task: "ApiTask") -> None:
        """输出电影信息"""

        # 格式化输出请求结果
        if api_task.response.success:
            Message.success(
                f"{api_task.response.data['title']} {api_task.response.data['release_date']}"
            )

            console.print(f"[标语] {api_task.response.data['tagline']}")
            console.print(f"[电影简介] {api_task.response.data['overview']}")

        # 请求失败则输出失败信息
        else:
            Message.error(f"tv_id: {api_task.args.get('movie_id')}")

    @staticmethod
    def output_tmdb_search_movie(api_task: "ApiTask") -> None:
        """输出查找电影信息"""

        if api_task.response.success:
            Message.success(f"关键词: {api_task.args.get('keyword')}")

            table = Table(box=box.SIMPLE)
            table.add_column("首映时间", justify="center", style="cyan")
            table.add_column("TMDB ID", justify="center", style="magenta")
            table.add_column("序号", justify="center", style="green")
            table.add_column("电影标题", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(api_task.response.data["results"]):
                table.add_row(r["release_date"], str(r["id"]), str(i), r["title"])
                logger.debug(
                    f"电影信息: {r['title']} ({r['release_date']}) TMDB ID: {r['id']}"
                )
            console.print(table)

        # 请求失败则输出失败信息
        else:
            Message.error(f"Keyword: {api_task.args.get('keyword')}")
