from AlistMediaRename import Amr
from importlib.metadata import version
import click


@click.command(
    options_metavar="[选项]",
    epilog="主页: https://github.com/jkoor/Alist-Media-Rename",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.argument("keyword", type=str, required=True, metavar="关键词")
@click.option("-d", "--dir", type=str, required=True, help="Alist剧集文件所在文件夹")
@click.option(
    "-c",
    "--config",
    type=str,
    default="./config.yaml",
    show_default=True,
    help="指定配置文件路径, 默认为程序所在路径(可选)",
)
@click.option("-i", "--id", is_flag=True, help="通过id搜索TMDB剧集信息(可选)")
@click.option("-m", "--movie", is_flag=True, help="搜索电影而不是剧集")
@click.option(
    "-n",
    "--number",
    type=int,
    default='1',
    show_default=True,
    help="指定从第几集开始重命名(可选)",
)
@click.option("-p", "--password", type=str, help="文件访问密码(可选)")
@click.version_option(
    version("AlistMediaRename"), "-v", "--version", help="显示版本信息"
)
def start(config, dir, id, keyword, movie, number, password):
    """
    利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器识别剧集信息\n
    用例: amr 刀剑神域 -d /阿里云盘/刀剑神域/
    """
    amr = Amr(config)

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
