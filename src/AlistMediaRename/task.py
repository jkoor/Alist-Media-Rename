import asyncio
from functools import wraps
import inspect
import json
import logging
import sys
from typing import Any, Callable, Coroutine

import httpx

from .models import ApiResponse
from .output import OutputParser

logger = logging.getLogger("Amr.Task")  # 获取子 logger


class CatchException:
    """
    捕获异常
    """

    @staticmethod
    def catch_api_exceptions(func) -> Callable[..., ApiResponse]:
        """捕获任务异常"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponse:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return ApiResponse(success=False, status_code=-1, error=str(e), data={})

        return wrapper

    @staticmethod
    def catch_api_exceptions_async(
        func,
    ) -> Callable[..., Coroutine[Any, Any, ApiResponse]]:
        """捕获任务异常"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> ApiResponse:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return ApiResponse(success=False, status_code=-1, error=str(e), data={})

        return wrapper


class ApiTask:
    """API请求任务"""

    def __init__(
        self,
        func: Callable[..., httpx.Request],
        args: tuple,
        kwargs: dict,
        response_parser: Callable[..., ApiResponse],
        output_parser: Callable[..., None],
        raise_error: bool,
    ) -> None:
        # 初始化参数
        self.func: Callable[..., httpx.Request] = func  # API请求函数
        self._args: tuple = args  # 函数参数
        self._kwargs: dict = kwargs  # 函数关键字参数

        self.response_parser: Callable[..., ApiResponse] = response_parser  # 解析器
        self.output_parser: Callable[..., None] = output_parser  # 输出解析器
        self.raise_error: bool = raise_error  # 是否在错误时停止

        self.request: httpx.Request  # API请求
        self.response: ApiResponse  # 请求结果

    @property
    def args(self):
        # 获取函数签名
        sig = inspect.signature(self.func)

        # 获取参数名
        # param_names = list(sig.parameters.keys())

        # 确定位置参数和关键字参数
        bound_args = sig.bind(*self._args, **self._kwargs)

        # 获取匹配的参数
        matched_args = bound_args.arguments

        # 返回匹配结果
        return matched_args

    @property
    def model_dump(self) -> dict:
        """返回任务模型信息"""
        return {
            "func": self.func,
            "args": self.args,
            "response": self.response,
        }

    def send_request_sync(self, client=httpx.Client()) -> ApiResponse:
        """同步发送网络请求"""
        self.request = self.func(*self._args, **self._kwargs)
        try:
            response: httpx.Response = client.send(self.request)
            self.response = self.response_parser(response)
        except Exception as e:
            self.response = ApiResponse(
                success=False, status_code=-1, error=str(e), data={}
            )

        self.output_parser(self)
        if not self.response.success and self.raise_error:
            # raise ApiResponseError(self.response.error)
            sys.exit(1)

        return self.response

    async def send_request_async(self, client=httpx.AsyncClient()) -> ApiResponse:
        """异步发送网络请求"""
        self.request = self.func(*self._args, **self._kwargs)
        try:
            response: httpx.Response = await client.send(self.request)
            self.response = self.response_parser(response)
        except Exception as e:
            self.response = ApiResponse(
                success=False, status_code=-1, error=str(e), data={}
            )
        self.output_parser(self)
        if not self.response.success and self.raise_error:
            # raise ApiResponseError()
            sys.exit(1)
        return self.response

    @classmethod
    def create(
        cls, api_response_parser: str, output_parser: str, raise_error: bool
    ) -> Callable[..., Callable[..., "ApiTask"]]:
        """创建任务实例"""

        def decorator(func) -> Callable[..., "ApiTask"]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> "ApiTask":
                return cls(
                    func,
                    args,
                    kwargs,
                    ApiResponseParser.parser(api_response_parser),
                    OutputParser.parser(output_parser),
                    raise_error,
                )

            return wrapper

        return decorator


class ApiResponseParser:
    """API请求结果解析器"""

    @staticmethod
    def parser(type: str) -> Callable[..., ApiResponse]:
        """设置解析器"""

        PARSER_MAP = {
            "alist": ApiResponseParser.alist_api_response,
            "tmdb": ApiResponseParser.tmdb_api_response,
        }

        if type in PARSER_MAP:
            return PARSER_MAP[type]
        else:
            raise ValueError(f"ApiResponseParser '{type}' not found")

    @staticmethod
    def alist_api_response(response: httpx.Response) -> ApiResponse:
        """
        封装Alist api返回信息.
        """

        rawdata = response.json()

        if rawdata["message"] == "success":
            return ApiResponse(
                success=True,
                status_code=rawdata["code"],
                error="",
                data=rawdata["data"] if rawdata["data"] else {},
            )
        else:
            return ApiResponse(
                success=False,
                status_code=rawdata["code"],
                error=rawdata["message"],
                data=rawdata["data"] if rawdata["data"] else {},
            )

    @staticmethod
    def tmdb_api_response(response: httpx.Response) -> ApiResponse:
        """
        封装TMDB api返回信息装饰器.
        """

        rawdata = response.json()

        if response.status_code != 200:
            return ApiResponse(
                success=False,
                status_code=response.status_code,
                error=rawdata.get("status_message", ""),
                data=rawdata,
            )

        if "results" in rawdata and rawdata["results"] == []:
            return ApiResponse(
                success=False,
                status_code=200,
                error="指定关键词未查找到相关信息",
                data=rawdata,
            )
        else:
            return ApiResponse(
                success=True,
                status_code=200,
                error="",
                data=rawdata,
            )


class TaskManager:
    """任务管理器"""

    _instance = None  # 用于存储唯一的实例

    def __init__(self, verbose: bool = False) -> None:
        self._sync_client = httpx.Client()
        self._async_client = httpx.AsyncClient()
        self.tasks_pending: list[ApiTask] = []
        self.tasks_done: list[ApiTask] = []
        self.tasks_recently: list[ApiTask] = []

        self.verbose = verbose
        self.raise_error = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def add_tasks(self, *tasks: ApiTask):
        """添加任务到任务列表"""
        for task in tasks:
            if isinstance(task, ApiTask):
                self.tasks_pending.append(task)
            else:
                raise TypeError("Only ApiTask instances can be added.")

    def run_tasks(self, async_: bool = False) -> list[ApiResponse]:
        """运行任务"""
        self.tasks_recently = self.tasks_pending.copy()
        if async_:
            result = self.run_async()
        else:
            result = self.run_sync()
        # if self.verbose:
        #     for task in self.tasks_recently:
        #         console.print(task.model_dump)
        for task in self.tasks_recently:
            logger.info(
                f"Task: {task.func.__name__}, Args: {task.args}, Success: {task.response.success}, Error: {task.response.error}"
            )
            logger.debug(
                f"任务 '{task.func.__name__}' 的原始数据: \n{json.dumps(task.response.data, indent=2, ensure_ascii=False)}"
            )
        return result

    def run_sync(self) -> list[ApiResponse]:
        """同步运行所有任务"""

        results: list[ApiResponse] = []

        for task in self.tasks_pending:
            result: ApiResponse = task.send_request_sync(self._sync_client)
            results.append(result)
            self.tasks_done.append(task)  # 保存结果
        self.tasks_pending.clear()  # 清空任务列表
        return results

    def run_async(self) -> list[ApiResponse]:
        """异步运行所有任务"""

        async def async_run() -> list[ApiResponse]:
            tasks = [
                task.send_request_async(self._async_client)
                for task in self.tasks_pending
            ]
            results: list[ApiResponse] = await asyncio.gather(*tasks)
            self.tasks_done.extend(self.tasks_pending)  # 保存结果
            self.tasks_pending.clear()  # 清空任务列表
            return results

        # return asyncio.run(async_run())
        loop = asyncio.get_event_loop()  # 获取当前事件循环
        results = loop.run_until_complete(async_run())  # 在当前事件循环中运行异步任务
        return results


taskManager = TaskManager()
