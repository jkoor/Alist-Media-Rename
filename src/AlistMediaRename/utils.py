import asyncio
from functools import wraps
import re
import sys
from typing import Any
from natsort import natsorted
import colorama
from .models import Task, TaskResult


class Debug:
    """
    工具类
    """

    debug_enabled = True
    output_enabled = True

    @staticmethod
    def catch_exceptions_not_stop(func):
        """
        捕获函数异常
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> TaskResult:
            # 捕获错误
            try:
                return TaskResult(
                    func_name=func.__qualname__,
                    args=list(args, **kwargs),
                    success=True,
                    data=func(*args, **kwargs),
                    error="",
                )

            except Exception as e:
                return TaskResult(
                    func_name=func.__qualname__,
                    args=list(args, **kwargs),
                    success=False,
                    data="",
                    error=str(e),
                )

        return wrapper

    @staticmethod
    def stop_on_error(result_list: list[TaskResult]):
        """在错误时停止"""
        for result in result_list:
            if not result.success:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 任务执行失败, 退出程序\n出错任务: {result.func_name}\n任务参数{result.args}\n错误信息: {result.error}\n"
                )
                sys.exit(0)


class PrintMessage:
    """打印消息类"""

    class ColorStr:
        """
        彩色字符串
        """

        @staticmethod
        def red(string: str) -> str:
            """红色字符串"""
            return colorama.Fore.RED + string + colorama.Fore.RESET

        @staticmethod
        def green(string: str) -> str:
            """绿色字符串"""
            return colorama.Fore.GREEN + string + colorama.Fore.RESET

        @staticmethod
        def yellow(string: str) -> str:
            """黄色字符串"""
            return colorama.Fore.YELLOW + string + colorama.Fore.RESET

    @staticmethod
    def alist_login_required(func):
        """判断登录状态"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return func(self, *args, **kwargs)

            # 判断登录状态
            if self.login_success is False:
                # print(f"{PrintMessage.ColorStr.red('[Alist●Login●Failure]\n')}操作失败，用户未登录")
                return {"message": "用户未登录"}
            login_result = func(self, *args, **kwargs)

            return login_result

        return wrapper

    @staticmethod
    def output_alist_login(func):
        """
        输出登录状态信息
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            login_result = func(self, *args, **kwargs)

            # 输出获取Token结果
            if login_result["message"] != "success":
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 登录失败\t{login_result['message']}"
                )
            else:
                print(f"{PrintMessage.ColorStr.green('[✓]')} 主页: {self.url}")
            return login_result

        return wrapper

    @staticmethod
    def output_alist_file_list(func):
        """输出文件信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 输出重命名结果
            if return_data["code"] != 200:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 获取文件列表失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}"
                )
                sys.exit(0)

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
            if return_data["message"] != "success":
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 重命名失败: {Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}\n{return_data['message']}"
                )
            else:
                print(
                    f"{PrintMessage.ColorStr.green('[✓]')} 重命名路径:{Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_move(func):
        """输出文件移动信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 输出重命名结果
            if return_data["message"] != "success":
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 移动失败: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n{return_data['message']}"
                )
            else:
                print(
                    f"{PrintMessage.ColorStr.green('[✓]')} 移动路径: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_mkdir(func):
        """输出新建文件/文件夹信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 输出新建文件夹请求结果
            if return_data["message"] != "success":
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 文件夹创建失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}"
                )
            else:
                print(
                    f"{PrintMessage.ColorStr.green('[✓]')} 文件夹创建路径: {Tools.get_argument(1, 'path', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_remove(func):
        """输出文件/文件夹删除信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 输出删除文件/文件夹请求结果
            if return_data["message"] != "success":
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 删除失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}\n{return_data['message']}"
                )
            else:
                for name in Tools.get_argument(2, "name", args, kwargs):
                    print(
                        f"{PrintMessage.ColorStr.green('[✓]')} 删除路径: {Tools.get_argument(1, 'path', args, kwargs)}/{name}"
                    )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_download_link(func):
        """输出文件下载链接信息"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return_data = func(self, *args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 输出获取下载信息请求结果
            if return_data["message"] == "success":
                file = return_data["data"]
                print(
                    f"\n{PrintMessage.ColorStr.green('[✓]')} 获取文件链接路径: {Tools.get_argument(1, 'path', args, kwargs)}"
                )
                print(
                    f"名称: {file['name']}\n来源: {file['provider']}\n直链: {self.url}/d{Tools.get_argument(1, 'path', args, kwargs)}\n源链: {file['raw_url']}"
                )
            else:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 获取文件链接失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_disk_list(func):
        """输出已添加存储列表"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return_data = func(self, *args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 输出已添加存储列表请求结果
            if return_data["message"] == "success":
                disks = return_data["data"]["content"]
                print(
                    f"{PrintMessage.ColorStr.green('[✓]')} 存储列表总数: {return_data['data']['total']}"
                )
                print(f"{'驱 动':<14}{'状    态':^18}{'挂载路径'}")
                print(f"{'--------':<16}{'--------':^20}{'--------'}")
                for disk in disks:
                    print(
                        f"{disk['driver']:<16}{disk['status']:^20}{disk['mount_path']}"
                    )
            else:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 获取存储驱动失败\n{return_data['message']}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_info(func):
        """输出剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if "success" in return_data and return_data["success"] is False:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} tv_id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\n{return_data['status_message']}"
                )
                return return_data

            # 格式化输出请求结果
            first_air_year = return_data["first_air_date"][:4]
            name = return_data["name"]
            dir_name = f"{name} ({first_air_year})"
            print(f"{PrintMessage.ColorStr.green('[✓]')} {dir_name}")
            seasons = return_data["seasons"]
            print(f"{' 开播时间 ':<10}{'集 数':^8}{'序 号':^10}{'剧 名'}")
            print(f"{'----------':<12}{'----':^12}{'-----':^12}{'----------------'}")
            for i, season in enumerate(seasons):
                print(
                    f"{str(season['air_date']):<12}{season['episode_count']:^12}{i:^12}{season['name']}"
                )
            print("")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_tv(func):
        """输出查找剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if "success" in return_data and return_data["success"] is False:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data['status_message']}"
                )
                return return_data
            if not return_data["results"]:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n    未查找到相关剧集"
                )
                return return_data

            # 格式化输出请求结果
            print(
                f"{PrintMessage.ColorStr.green('[✓]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}"
            )
            print(f"{' 开播时间 ':<8}{'序 号':^14}{'剧 名'}")
            print(f"{'----------':<12}{'-----':^16}{'----------------'}")
            for i, result in enumerate(return_data["results"]):
                print(f"{result['first_air_date']:<12}{i:^16}{result['name']}")
            print("")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_season_info(func):
        """输出剧集季度信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if "success" in return_data and return_data["success"] is False:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 剧集id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\t第 {Tools.get_argument(2, 'season_number', args, kwargs)} 季\n{return_data['status_message']}"
                )
                return return_data

            return return_data

            # 格式化输出请求结果
            print(f"{PrintMessage.ColorStr.green('[✓]')} {return_data['name']}")
            print(f"{'序 号':<6}{'放映日期':<12}{'时 长':<10}{'标 题'}")
            print(f"{'----':<8}{'----------':<16}{'-----':<12}{'----------------'}")

            for episode in return_data["episodes"]:
                print(
                    f"{episode['episode_number']:<8}{episode['air_date']:<16}{str(episode['runtime']) + 'min':<12}{episode['name']}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_movie_info(func):
        """输出电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if "success" in return_data and return_data["success"] is False:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} tv_id: {Tools.get_argument(1, 'movie_id', args, kwargs)}\n{return_data['status_message']}"
                )
                return return_data

            # 格式化输出请求结果
            print(
                f"{PrintMessage.ColorStr.green('[✓]')} {return_data['title']} {return_data['release_date']}"
            )
            print(f"[标语] {return_data['tagline']}")
            print(f"[剧集简介] {return_data['overview']}")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_movie(func):
        """输出查找电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if "success" in return_data and return_data["success"] is False:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data['status_message']}"
                )
                return return_data

            if not return_data["results"]:
                print(
                    f"{PrintMessage.ColorStr.red('[✗]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n查找不到任何相关电影"
                )
                return return_data

            # 格式化输出请求结果
            print(
                f"{PrintMessage.ColorStr.green('[✓]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}"
            )
            print(f"{' 首播时间 ':<8}{'序号':^14}{'电影标题'}")
            print(f"{'----------':<12}{'-----':^16}{'----------------'}")

            for i, result in enumerate(return_data["results"]):
                if "release_date" in result:
                    print(f"{result['release_date']:<12}{i:^16}{result['title']}")
                else:
                    print(f"{'xxxx-xx-xx':<12}{i:^16}{result['title']}")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def print_rename_info(
        video_rename_list: list[dict[str, str]],
        subtitle_rename_list: list[dict[str, str]],
        folder_rename: bool,
        renamed_folder_title: str | None,
        folder_path: str,
    ):
        """打印重命名信息"""
        # print("以下视频文件将会重命名: ")
        print(PrintMessage.ColorStr.yellow("以下视频文件将会重命名: "))
        for video in video_rename_list:
            print(f"{video['original_name']} -> {video['target_name']}")
        # print("以下字幕文件将会重命名: ")
        print(PrintMessage.ColorStr.yellow("以下字幕文件将会重命名: "))
        for subtitle in subtitle_rename_list:
            print(f"{subtitle['original_name']} -> {subtitle['target_name']}")
        if renamed_folder_title:
            print(
                f"{PrintMessage.ColorStr.yellow("文件夹重命名")}:\n {folder_path.split('/')[-2]} -> {renamed_folder_title}"
            )

    @staticmethod
    def require_confirmation() -> bool:
        """确认操作"""
        print("")
        while True:
            signal = input(
                f"确定要重命名吗? {PrintMessage.ColorStr.green("[回车]")}确定, {PrintMessage.ColorStr.red("[n]")}取消\t"
            )
            if signal.lower() == "":
                return True
            if signal.lower() == "n":
                sys.exit(0)
            continue

    @staticmethod
    def select_number(result_list: list[Any]) -> int:
        """根据查询结果选择序号"""
        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(result_list) == 1:
            return 0
        else:
            while True:
                # 获取到多项匹配结果，手动选择
                number = input(f"查询到以上结果，请输入对应{PrintMessage.ColorStr.green("[序号]")}, 输入{PrintMessage.ColorStr.red("[n]")}退出\t")
                if number.lower() == "n":
                    sys.exit(0)
                if number.isdigit() and 0 <= int(number) < len(result_list):
                    return int(number)


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
        # 若选择排除已重命名文件, 则过滤已重命名文件
        return natsorted([file for file in file_list if re.match(pattern, file)])

    @staticmethod
    def remove_intersection(a: list, b: list, exclude_renamed) -> tuple:
        """移除两个列表的交集"""
        if not exclude_renamed:
            return a, b
        a_dict = {item.rsplit(".", 1)[0]: item for item in a}
        b_set = set(b)
        intersection = set(a_dict.keys()) & b_set
        a = [a_dict[key] for key in a_dict if key not in intersection]
        b = [item for item in b if item not in intersection]
        return a, b

    @staticmethod
    def get_argument(
        arg_index: int, kwarg_name: str, args: list | tuple, kwargs: dict
    ) -> str:
        """获取参数"""
        if len(args) > arg_index:
            return args[arg_index]
        return kwargs[kwarg_name]

    @staticmethod
    def match_episode_files(
        episode_list: list[str], file_list: list[str], first_number
    ) -> list[dict[str, str]]:
        """匹配剧集文件"""
        episode_list = episode_list[first_number - 1 :]
        file_rename_list = [
            {"original_name": x, "target_name": y + "." + x.split(".")[-1]}
            for x, y in zip(file_list, episode_list)
        ]
        return file_rename_list

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


class Tasks:
    """多任务运行（异步/同步）"""

    @staticmethod
    def exec_function(func, args):
        """执行函数"""
        decorated_func = Debug.catch_exceptions_not_stop(func)
        return decorated_func(*args)

    @staticmethod
    def run_sync_tasks(task_list: list[Task]) -> list[TaskResult]:
        """同步运行函数集"""

        results = []

        for task in task_list:
            results.append(Tasks.exec_function(task.func, task.args))
        return results

    @staticmethod
    def run_async_tasks(task_list: list[Task]) -> list[TaskResult]:
        """异步运行函数集"""

        async def run_task():
            """异步处理函数"""
            results = []  # 创建一个空字典来存储结果
            futures = []
            for task in task_list:
                future = loop.run_in_executor(
                    None, Tasks.exec_function, task.func, task.args
                )
                futures.append(future)
            for future in futures:
                results.append(await future)
            return results
            # done, pending = await asyncio.wait(futures)
            # 将结果与执行函数对应起来
            # for future in done:
            #     results.append(future.result())
            # return results, pending

        loop = asyncio.new_event_loop()
        done = loop.run_until_complete(run_task())
        loop.close()
        return done

    @staticmethod
    def run(task_list: list[Task], async_mode: bool) -> list[TaskResult]:
        """运行函数集"""
        if async_mode:
            return Tasks.run_async_tasks(task_list)
        return Tasks.run_sync_tasks(task_list)
