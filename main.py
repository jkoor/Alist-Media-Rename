# -*- coding: utf-8 -*-
# @Time : 2023/5/1/0001 18:10
# @Author : JKOR
# @File : main.py
# @Software: PyCharm

import argparse

from media_name import AlistMediaRename, Config


def main(arg):
    """重命名主函数"""
    # 读取配置文件

    config = Config()
    config.load(arg["config_path"])
    config.save(arg["config_path"], output=False)

    amr = AlistMediaRename(config)

    # 自定义设置覆盖
    if arg['media_folder_rename']:
        amr.config.media_folder_rename = arg['media_folder_rename']
    if arg['noasync']:
        amr.config.rename_by_async = False
    if arg['debug']:
        amr.debug = True

    # TMDB搜索电影
    if arg["movie"]:
        if arg["id"]:
            amr.movie_rename_id(arg["keyword"], arg["dir"], arg["password"])
        else:
            amr.movie_rename_keyword(arg["keyword"], arg["dir"], arg["password"])
    # TMDB搜索剧集
    else:
        if arg["id"]:
            amr.tv_rename_id(arg["keyword"], arg["dir"], arg["password"], arg["number"])
        else:
            amr.tv_rename_keyword(arg["keyword"], arg["dir"], arg["password"], arg["number"])


def command() -> dict:
    """
    设置命令行参数
    :return: 返回运行参数
    """

    parser = argparse.ArgumentParser(
        description="利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器识别剧集",
        usage="python %(prog)s [options] keyword -d path",
        epilog="用例: python main.py 刀剑神域 -d /阿里云盘/刀剑神域/",
    )

    # 必选参数
    parser.add_argument("keyword", help="TMDB剧集查找字段")
    parser.add_argument("-d", "--dir", action="store", required=True, help="Alist剧集文件所在文件夹, 结尾需加/")
    # 可选参数
    parser.add_argument(
        "-c", "--config", action="store", help="指定配置文件路径, 默认为程序所在路径(可选)", default="./config.json"
    )
    parser.add_argument(
        "-f", "--folderdir", action="store", default= 1, help="重命名父文件夹(可选)"
    )
    parser.add_argument("-i", "--id", action="store_true", help="通过id搜索TMDB剧集信息(可选)")
    parser.add_argument("-m", "--movie", action="store_true", help="搜索电影而不是剧集")
    parser.add_argument(
        "-n", "--number", action="store", type=int, default=1, help="指定从第几集开始重命名, 默认为1(可选)"
    )
    parser.add_argument("-p", "--password", action="store", help="文件访问密码(可选)")
    parser.add_argument("--noasync", action="store_true", help="不使用异步方式加快重命名操作")
    parser.add_argument("--debug", action="store_true", help="Debug 模式")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="AlistMediaRename version : v2.0",
        help="显示版本信息",
    )
    args = parser.parse_args()
    return {
        "keyword": args.keyword,
        "dir": args.dir,
        "id": args.id,
        "movie": args.movie,
        "media_folder_rename": int(args.folderdir),
        "config_path": args.config,
        "password": args.password,
        "number": args.number,
        "noasync": args.noasync,
        "debug": args.debug
    }


if __name__ == "__main__":
    argument = command()
    main(argument)
