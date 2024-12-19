# TODO: 尝试解决log输出问题

from functools import wraps
import sys
from typing import Callable
from rich import print as rprint
from .models import ApiResponseModel


# debug_mode = False
# verbose_mode = False
# logger = []


class Logger:
    _instance = None
    debug_mode = True
    verbose_mode = False
    log = []

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
                rprint(result.model_dump()) if not logger.verbose_mode else None
                sys.exit(0)
            return result

        return wrapper

    @staticmethod
    def catch_exceptions(func) -> Callable[..., ApiResponseModel]:
        """
        捕获函数异常
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponseModel:
            # 捕获错误

            try:
                result = func(*args, **kwargs)
                if logger.verbose_mode:
                    rprint(result.model_dump())
                return result
            except Exception as e:
                if logger.debug_mode:
                    print("yes")
                    # raise e
                result = ApiResponseModel(
                    success=False,
                    status_code=-1,
                    error=str(e),
                    data={},
                    function=func.__qualname__,
                    args=args,
                    kwargs=kwargs,
                )
                if logger.verbose_mode:
                    rprint(result.model_dump())
                return result

        return wrapper
