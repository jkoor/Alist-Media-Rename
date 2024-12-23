import asyncio
from functools import wraps
from typing import Callable
from .models import ApiResponseModel
from .output import console, Message


class Logger:
    _instance = None
    debug_mode = False
    verbose_mode = False
    log: list[ApiResponseModel] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance


logger = Logger()


# 处理异常
class HandleException:
    """
    异常处理类
    """

    @staticmethod
    def stop_on_error(func) -> Callable[..., ApiResponseModel]:
        """在错误时停止"""

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            result: ApiResponseModel = func(*args, **kwargs)
            if not result.success:
                console.print(result.model_dump()) if not logger.verbose_mode else None
                Message.exit()
            return result

        return wrapper

    @staticmethod
    def catch_exceptions(func) -> Callable[..., ApiResponseModel]:
        """
        捕获函数异常
        """

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> ApiResponseModel:
            # 捕获错误
            try:
                result = await func(*args, **kwargs)
                if logger.verbose_mode:
                    console.print(result.model_dump())
                logger.log.append(result)
                return result
            except Exception as e:
                if logger.debug_mode:
                    raise e
                result = ApiResponseModel(
                    success=False,
                    status_code=-1,
                    error=str(e),
                    data={},
                    function=func.__qualname__,
                    args=args,
                    kwargs=kwargs,
                )
                logger.log.append(result)
                if logger.verbose_mode:
                    console.print(result.model_dump())
                return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> ApiResponseModel:
            # 捕获错误

            try:
                result = func(*args, **kwargs)
                if logger.verbose_mode:
                    console.print(result.model_dump())
                logger.log.append(result)
                return result
            except Exception as e:
                if logger.debug_mode:
                    raise e
                result = ApiResponseModel(
                    success=False,
                    status_code=-1,
                    error=str(e),
                    data={},
                    function=func.__qualname__,
                    args=args,
                    kwargs=kwargs,
                )
                logger.log.append(result)
                if logger.verbose_mode:
                    console.print(result.model_dump())
                return result

        # return sync_wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper
