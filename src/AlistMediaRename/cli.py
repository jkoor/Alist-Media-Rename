from typing import Union
from importlib.metadata import version

from AlistMediaRename import Amr
from AlistMediaRename.logger_setup import setup_logging, logger
import click
from rich.traceback import install
import time

install(show_locals=False, suppress=[click])


@click.command(
    options_metavar="[选项]",
    epilog="主页: https://github.com/jkoor/Alist-Media-Rename",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.argument("keyword", type=str, required=True, metavar="关键词")
@click.option(
    "-c",
    "--config",
    type=str,
    default="./config.yaml",
    show_default=True,
    help="指定配置文件路径, 默认为程序所在路径(可选)",
)
@click.option("-d", "--dir", type=str, default="", help="Alist剧集文件所在文件夹")
@click.option("-i", "--id", is_flag=True, help="通过id搜索TMDB剧集信息(可选)")
@click.option("-m", "--movie", is_flag=True, help="搜索电影而不是剧集")
@click.option(
    "-n",
    "--number",
    type=str,
    default="1-",
    # show_default=True,
    help="指定剧集编号开始重命名(可选)",
)
@click.option("-p", "--password", type=str, help="文件访问密码(可选)")
@click.option(
    "--folder/--no-folder", default=None, help="是否对父文件夹进行重命名(可选)"
)
@click.option("--suffix", type=str, help="在文件名后添加自定义后缀(可选)")
@click.option("--verbose", is_flag=True, help="显示详细信息(可选)")
@click.option("--log-file", type=str, help="输出日志文件路径(可选)", default=None)
@click.version_option(
    version("AlistMediaRename"), "-v", "--version", help="显示版本信息"
)
def start(
    config: str,
    dir: str,
    folder: Union[bool, None],
    id: bool,
    keyword: str,
    movie: bool,
    number: str,
    password: str,
    suffix: str,
    verbose: bool,
    log_file: Union[str, None] = None,
):
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器识别剧集信息\n
    用例: amr 刀剑神域 -d /阿里云盘/刀剑神域/

    \f
    :param config: 配置文件路径
    :param dir: Alist剧集文件所在文件夹
    :param folder: 是否对父文件夹进行重命名
    :param id: 通过id搜索TMDB剧集信息
    :param keyword: 关键词
    :param movie: 搜索电影而不是剧集
    :param number: 指定从第几集开始重命名
    :param password: 文件访问密码
    :param suffix: 在文件名后添加自定义后缀
    :param verbose: 显示详细信息
    """

    # 初始化日志系统，现在传递命令行参数
    password_str: str = "*" * len(password) if password else ""
    if log_file is None:
        log_file = f"log_file_{time.strftime('%Y%m%d_%H%M%S')}.log"  # 默认日志文件名格式: log_file_YYYYMMDD_HHMMSS.log
    setup_logging(verbose=verbose, file_log_path=log_file)
    logger.info(
        f"应用启动，参数: keyword='{keyword}', config='{config}', dir='{dir}', folder='{folder}',id={id}, movie={movie}, number='{number}', password='{password_str}', verbose={verbose}, log_file='log_file', log_level='log_level'"
    )

    try:
        logger.debug("开始初始化 Amr 实例")

        amr = Amr(config=config, verbose=verbose)

        # 设置文件名后缀选项
        if suffix:
            amr.config.settings.amr.movie_name_format += suffix
            amr.config.settings.amr.movie_folder_name_format += suffix
            amr.config.settings.amr.tv_name_format += suffix
            amr.config.settings.amr.tv_folder_name_format += suffix

        # 设置文件夹重命名选项
        if folder is not None:
            amr.config.settings.amr.media_folder_rename = folder

        logger.debug("Amr 实例初始化完成")

        # TMDB搜索电影
        if movie:
            if id:
                amr.movie_rename_id(keyword, dir, password)
            else:
                amr.movie_rename_keyword(keyword, dir, password)
        # TMDB搜索剧集
        else:
            if id:
                amr.tv_rename_id(keyword, dir, password, number)
            else:
                amr.tv_rename_keyword(keyword, dir, password, number)
        logger.info("任务完成")
    except Exception as e:
        logger.info(f"应用顶层出现未捕获错误: {e}", exc_info=True)
        from AlistMediaRename.output import console

        console.print(
            f"[bold red]发生了一个严重错误，详情请查看日志文件 (如果已配置)。错误信息: {e}[/bold red]"
        )


if __name__ == "__main__":
    start()
