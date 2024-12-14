from typing import Union
from AlistMediaRename import Amr
from importlib.metadata import version
import click


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
@click.option("-d", "--dir", type=str, required=True, help="Alist剧集文件所在文件夹")
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
    """
    amr = Amr(config)

    if folder is not None:
        amr.config.settings.amr.media_folder_rename = folder

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


if __name__ == "__main__":
    start()
