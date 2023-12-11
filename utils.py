import asyncio
from functools import wraps
import re
import sys
from natsort import natsorted
import colorama


class DebugDecorators:
    """
    工具类
    """

    debug_enabled = False
    output_enabled = True

    @staticmethod
    def catch_exceptions(func):
        """
        捕获函数异常
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 如果未启用调试模式，直接返回结果
            if DebugDecorators.debug_enabled:
                return func(*args, **kwargs)

            # 捕获错误
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(
                    f"{Tools.ColorStr.red("[ERROR]")}\nFunction: {func.__qualname__}\nArgs: {args}\nKwargs: {kwargs}\nMessage: {e}"
                )

                sys.exit(0)

        return wrapper

    @staticmethod
    def alist_login_required(func):
        """判断登录状态"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return func(self, *args, **kwargs)

            # 判断登录状态
            if self.login_success is False:
                # print(f"{Tools.ColorStr.red('[Alist●Login●Failure]\n')}操作失败，用户未登录")
                return {'message': '用户未登录'}
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

            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return login_result


            # 输出获取Token结果
            if login_result["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●Login ✗]')} 登录失败\t{login_result['message']}")
            else:
                print(f"{Tools.ColorStr.green('[Alist●Login ✓]')} 主页: {self.url}")
            return login_result

        return wrapper

    @staticmethod
    def output_alist_file_list(func):
        """输出文件列表信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败
            if return_data["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●List ✗]')} 获取文件列表失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}")
                return return_data

            # 文件夹为空
            if return_data["data"]["content"] is None:
                print(f"{Tools.ColorStr.green('[Alist●List ✓]')} 文件夹为空: {Tools.get_argument(1, 'path', args, kwargs)}")
                return return_data

            return return_data


            # 整理排序文件列表

            file_list = return_data["data"]["content"]
            folder_list = list(filter(lambda f: f["is_dir"] is True, file_list))
            file_list = list(filter(lambda f: f["is_dir"] is False, file_list))
            folder_list = natsorted(folder_list, key=lambda x: x["name"])
            file_list = natsorted(file_list, key=lambda x: x["name"])

            for file in folder_list:
                # 文件夹信息格式化
                file["modified"] = f"{file['modified'][:10]}  {file['modified'][11:19]}"
                file["size"] = ""
                file["name"] = f"[{file['name']}]"

            for file in file_list:
                file["modified"] = f"{file['modified'][:10]}  {file['modified'][11:19]}"
                if file["size"] >= 1000000000:  # 格式化GB级大小文件输出信息
                    file["size"] = f"{str(round(file['size'] / 1073741824, 2))}GB"
                elif file["size"] >= 1000000:  # 格式化MB级大小文件输出信息
                    file["size"] = f"{str(round(file['size'] / 1048576, 2))}MB"
                elif file["size"] >= 1000:  # 格式化KB级大小文件输出信息
                    file["size"] = f"{str(round(file['size'] / 1024, 2))}KB"
                else:  # 格式化B级大小文件输出信息
                    file["size"] = f"{str(file['size'])}B"

            # 输出格式化文件列表信息
            print(f"{Tools.ColorStr.green('[Alist●List●Success]')} 文件列表路径: {Tools.get_argument(1, 'path', args, kwargs)}")
            print(f"{'修改日期':<21s}{'文件大小':<10s}{'名    称':<26s}")
            print(f"{'--------------------':<25s}{'--------':<14s}{'--------------------':<30s}")
            for file in folder_list + file_list:
                print(f"{file['modified']:<25s}{file['size']:<14s}{file['name']}")
            print(f"\n  文件总数: {return_data['data']['total']}")
            print(f"  写入权限: {return_data['data']['write']}")
            print(f"  存储来源: {return_data['data']['provider']}\n")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_rename(func):
        """输出重命名信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出重命名结果
            if return_data["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●Rename ✗]')} 重命名失败: {Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}\n{return_data['message']}")
            else:
                print(f"{Tools.ColorStr.green('[Alist●Rename ✓]')} 重命名路径:{Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_move(func):
        """输出文件移动信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出重命名结果
            if return_data["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●Move ✗]')} 移动失败: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n{return_data['message']}")
            else:
                print(f"{Tools.ColorStr.green('[Alist●Move ✓]')} 移动路径: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出新建文件夹请求结果
            if return_data["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●Mkdir ✗]')} 文件夹创建失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}")
            else:
                print(f"{Tools.ColorStr.green('[Alist●Mkdir ✓]')} 文件夹创建路径: {Tools.get_argument(1, 'path', args, kwargs)}")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出删除文件/文件夹请求结果
            if return_data["message"] != "success":
                print(f"{Tools.ColorStr.red('[Alist●Remove ✗]')} 删除失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}\n{return_data['message']}")
            else:
                for name in Tools.get_argument(2, 'name', args, kwargs):
                    print(f"{Tools.ColorStr.green('[Alist●Remove ✓]')} 删除路径: {Tools.get_argument(1, 'path', args, kwargs)}/{name}")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出获取下载信息请求结果
            if return_data["message"] == "success":
                file = return_data["data"]
                print(f"\n{Tools.ColorStr.green('[Alist●DL_link ✓]')} 获取文件链接路径: {Tools.get_argument(1, 'path', args, kwargs)}")
                print(f"名称: {file['name']}\n来源: {file['provider']}\n直链: {self.url}/d{Tools.get_argument(1, 'path', args, kwargs)}\n源链: {file['raw_url']}")
            else:
                print(f"{Tools.ColorStr.red('[Alist●DL_link ✗]')} 获取文件链接失败: {Tools.get_argument(1, 'path', args, kwargs)}\n{return_data['message']}")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 输出已添加存储列表请求结果
            if return_data["message"] == "success":
                disks = return_data["data"]["content"]
                print(f"{Tools.ColorStr.green('[Alist●Disk ✓]')} 存储列表总数: {return_data['data']['total']}")
                print(f"{'驱 动':<14}{'状    态':^18}{'挂载路径'}")
                print(f"{'--------':<16}{'--------':^20}{'--------'}")
                for disk in disks:
                    print(f"{disk['driver']:<16}{disk['status']:^20}{disk['mount_path']}")
            else:
                print(f"{Tools.ColorStr.red('[Alist●Disk ✗]')} 获取存储驱动失败\n{return_data['message']}")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if 'success' in return_data and return_data['success'] is False:
                print(f"{Tools.ColorStr.red('[Tmdb●tv_info ✗]')} tv_id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\n{return_data['status_message']}")
                return return_data

            # 格式化输出请求结果
            first_air_year = return_data["first_air_date"][:4]
            name = return_data["name"]
            dir_name = f"{name} ({first_air_year})"
            print(f"{Tools.ColorStr.green('[Tmdb●tv_info ✓]')} {dir_name}")
            seasons = return_data["seasons"]
            print(f"{' 开播时间 ':<10}{'集 数':^8}{'序 号':^10}{'剧 名'}")
            print(f"{'----------':<12}{'----':^12}{'-----':^12}{'----------------'}")
            for season in seasons:
                print(
                    f"{str(season['air_date']):<12}{season['episode_count']:^12}{season['season_number']:^12}{season['name']}"
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

            # 如果未启用调试模式，直接返回结果
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if 'success' in return_data and return_data['success'] is False:
                print(f"{Tools.ColorStr.red('[Tmdb●search_tv ✗]')} Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data['status_message']}")
                return return_data
            if not return_data["results"]:
                print(f"{Tools.ColorStr.red('[Tmdb●search_tv ✗]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n查找不到任何相关剧集")
                return return_data

            # 格式化输出请求结果
            print(f"{Tools.ColorStr.green('[Tmdb●search_tv ✓]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")
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
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if 'success' in return_data and return_data['success'] is False:
                print(f"{Tools.ColorStr.red('[Tmdb●tv_season_info ✗]')} 剧集id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\t第 {Tools.get_argument(2, 'season_number', args, kwargs)} 季\n{return_data['status_message']}")
                return return_data

            return return_data

            # 格式化输出请求结果
            print(f"{Tools.ColorStr.green('[Tmdb●tv_season_info ✓]')} {return_data['name']}")
            print(f"{'序 号':<6}{'放映日期':<12}{'时 长':<10}{'标 题'}")
            print(f"{'----':<8}{'----------':<16}{'-----':<12}{'----------------'}")

            for episode in return_data["episodes"]:
                print(f"{episode['episode_number']:<8}{episode['air_date']:<16}{str(episode['runtime']) + 'min':<12}{episode['name']}")

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
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if 'success' in return_data and return_data['success'] is False:
                print(f"{Tools.ColorStr.red('[Tmdb●movie_info ✗]')} tv_id: {Tools.get_argument(1, 'movie_id', args, kwargs)}\n{return_data['status_message']}")
                return return_data

            # 格式化输出请求结果
            print(f"{Tools.ColorStr.green('[Tmdb●movie_info ✓]')} {return_data['title']} {return_data['release_date']}")
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
            if not DebugDecorators.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if 'success' in return_data and return_data['success'] is False:
                print(f"{Tools.ColorStr.red('[Tmdb●movie_info ✗]')} Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data['status_message']}")
                return return_data

            if not return_data["results"]:
                print(f"{Tools.ColorStr.red('[Tmdb●movie_info ✗]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n查找不到任何相关电影")
                return return_data

            # 格式化输出请求结果
            print(f"{Tools.ColorStr.green('[Tmdb●movie_info ✓]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")
            print(f"{' 首播时间 ':<8}{'序号':^14}{'电影标题'}")
            print(f"{'----------':<12}{'-----':^16}{'----------------'}")

            for i, result in enumerate(return_data["results"]):
                print(f"{result['release_date']:<12}{i:^16}{result['title']}")

            # 返回请求结果
            return return_data

        return wrapper


class Tools:
    """
    工具函数类
    """

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
    def ensure_slash(path: str) -> str:
        """确保路径以 / 开头并以 / 结尾"""
        if not path.startswith('/'):
            path = '/' + path
        if not path.endswith('/'):
            path = path + '/'
        return path

    @staticmethod
    def get_parent_path(path: str) -> str:
        """获取父目录路径"""
        path = Tools.ensure_slash(path)
        return path[:path[:-1].rfind('/') + 1]

    @staticmethod
    def filter_file(file_list: list, pattern: str) -> list:
        """筛选列表"""
        return [file for file in file_list if re.match(pattern, file)]

    @staticmethod
    def remove_intersection(a: list, b: list) -> tuple:
        """移除两个列表的交集"""
        a_dict = {item.rsplit('.', 1)[0]: item for item in a}
        b_set = set(b)
        intersection = set(a_dict.keys()) & b_set
        a = [a_dict[key] for key in a_dict if key not in intersection]
        b = [item for item in b if item not in intersection]
        return a, b

    @staticmethod
    def get_argument(arg_index: int, kwarg_name: str, args: list, kwargs: dict) -> str:
        """获取参数"""
        if len(args) > arg_index:
            return args[arg_index]
        return kwargs[kwarg_name]

    @staticmethod
    def run_tasks(func_list: list):
        """异步运行函数集"""
        async def run_task(func_list: list):
            """异步处理函数"""
            results = []  # 创建一个空字典来存储结果
            futures = []
            for func in func_list:
                future = loop.run_in_executor(None, func['func'], *func['args'])
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
        done = loop.run_until_complete(run_task(func_list))
        loop.close()
        return done

    @staticmethod
    def require_confirmation(notice_msg: str) -> dict:
        """确认操作"""
        print("")
        while True:
            signal = input(f"{notice_msg} 确定要重命名吗? [回车]确定, [n]取消\t")
            if signal.lower() == "":
                return True
            if signal.lower() == "n":
                return False
            continue
