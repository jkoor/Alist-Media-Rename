import logging
import os
from typing import Optional
from rich.logging import RichHandler
from AlistMediaRename.output import console as rich_console_instance  # 可以考虑复用

# 获取根 logger
logger = logging.getLogger("Amr")  # 为您的应用创建一个专用的 logger 实例

# 默认的日志格式，如果需要可以硬编码或作为参数传递
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"


def setup_logging(
    verbose: bool = False,  # 来自 --verbose 的布尔值
    file_log_path: Optional[str] = None,  # 来自 --log-file
    file_log_level: str = "INFO",  # 来自 --log-level，或硬编码默认值
):
    """
    根据命令行参数配置日志系统。

    :param verbose: 是否启用在控制台输出详细日志。
    :param file_log_path: 日志文件的路径。如果为 None，则不记录到文件。
    :param file_log_level: 文件日志的级别字符串 (e.g., "INFO", "DEBUG").
    :param log_format: 日志记录的格式字符串。
    """
    logger.setLevel(
        logging.DEBUG
    )  # 设置根 logger 的级别为 DEBUG，由 handlers 控制实际输出级别

    # 清理现有的 handlers，防止重复日志
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()  # 关闭旧的 handler

    # --- 控制台 Handler ---
    # 使用 RichHandler 替代 StreamHandler
    # 您可以根据需要配置 RichHandler 的参数，例如：
    # rich_tracebacks=True (默认False) - 使用rich格式化异常堆栈
    # markup=True (默认False) - 允许在日志消息中使用rich的标记语言
    # show_time=True (默认True), show_level=True (默认True), show_path=True (默认True)
    # keywords: 一个字符串列表，RichHandler 会高亮这些关键词
    console_handler = RichHandler(
        level=logging.NOTSET,  # RichHandler 内部会处理级别，这里可以设置为NOTSET，由logger本身和verbosity决定
        console=rich_console_instance,  # 如果想复用 output.py 中的 console 实例
        show_path=True,  # 可以调整是否显示路径，默认是 True
        markup=True,  # 启用 markup 可以让日志消息更丰富
        rich_tracebacks=True,  # 推荐启用，错误堆栈更美观
        tracebacks_show_locals=False,  # 根据需要决定是否显示本地变量
        log_time_format="[%Y-%m-%d %H:%M:%S.%f]",  # 自定义时间格式
    )

    if verbose:
        console_handler.setLevel(logging.INFO)
    else:
        console_handler.setLevel(logging.WARNING)  # 默认只显示警告及以上级别

    # RichHandler 不需要传统的 Formatter，它有自己的格式化方式
    # 如果需要自定义 RichHandler 输出的每个部分，通常通过其构造函数参数来完成，
    # 而不是设置一个 logging.Formatter。
    # 不过，如果你仍然想用标准 formatter 控制消息体本身（message部分），可以这样做：
    # msg_formatter = logging.Formatter("%(message)s") # 只格式化消息本身
    # console_handler.setFormatter(msg_formatter) # 但通常不这么用 RichHandler

    logger.addHandler(console_handler)

    # 文件 Handler (如果指定了路径)
    if verbose and file_log_path:
        try:
            # 确保日志文件目录存在
            log_dir = os.path.dirname(file_log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)  # exist_ok=True 避免并发问题
            file_log_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            file_handler = logging.FileHandler(
                file_log_path, mode="a", encoding="utf-8"
            )
            # 设置文件处理器的级别
            # file_actual_level = getattr(logging, file_log_level.upper(), logging.DEBUG)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_log_formatter)
            logger.addHandler(file_handler)
            logger.info(
                f"文件日志已启用。日志文件: {os.path.abspath(file_log_path)}, 级别: {file_log_level.upper()}"
            )
        except Exception as e:
            logger.error(f"配置文件日志失败 ({file_log_path}): {e}", exc_info=True)
            # 确保控制台能看到这个错误
            logger.error(f"无法初始化文件日志处理器: {e}")  # 再次记录，确保显示

    else:
        logger.info("文件日志未启用 (未提供 --log-file 参数)。")
