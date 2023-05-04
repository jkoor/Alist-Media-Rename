# -*- coding: utf-8 -*-
# @Time : 2023/5/1/0001 18:10
# @Author : JKOR
# @File : main.py
# @Software: PyCharm

import argparse
import json

from media_name import AlistMediaRename


def load_config(config_path):
    # 读取配置文件
    try:
        config = json.load(open(config_path, "r", encoding='utf-8'))
    # 若文件不存在则创建文件
    except FileNotFoundError:
        settings = dict(tmdb_language="zh-CN",
                        filename_format="{name}-S{season:0>2}E{episode:0>2}.{title}",
                        media_folder_rename=False,
                        media_season_dir=False,
                        media_season_format="Season {season}",
                        video_suffix_list=['mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov'],
                        subtitle_suffix_list=['srt', 'ass', 'stl'])

        alist_url = input("请输入Alist地址\n")
        alist_user = input("请输入账号\n")
        alist_password = input("请输入登录密码\n")
        alist_totp = input("请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请[回车]跳过\n")
        tmdb_key = input("请输入TMDB api密钥(V3)\n")
        config = dict(alist_url=alist_url,
                      alist_user=alist_user,
                      alist_password=alist_password,
                      alist_totp=alist_totp,
                      tmdb_key=tmdb_key,
                      settings=settings)
        json.dump(config, open(config_path, "w", encoding='utf-8'), indent=4)
        print("\n配置文件保存路径: {}".format(config_path))
        print("其余自定义设置请修改保存后的配置文件")
    return config


def test():
    # 读取配置文件
    config = load_config('./local.json')
    amr = AlistMediaRename(config['alist_url'], config['alist_user'],
                           config['alist_password'], config['alist_totp'],
                           config['tmdb_key'], True)
    # 自定义设置覆盖
    for k in config['settings']:
        exec(f"amr.{k} = config['settings']['{k}']")

    # amr.media_rename_id('42885', '/test/abc/123/4', '123')
    # amr.media_rename_keyword('刀剑神域', '/test/abc/123/4', '123')
    amr.media_rename_keyword('从零开始', '/test/abc/123/4', '123')


def main(arg):
    """ 重命名主函数"""
    # 读取配置文件
    config = load_config(arg['config_path'])
    amr = AlistMediaRename(config['alist_url'], config['alist_user'],
                           config['alist_password'], config['alist_totp'],
                           config['tmdb_key'], arg['debug'])
    # 自定义设置覆盖
    for k in config['settings']:
        exec(f"amr.{k} = config['settings']['{k}']")

    if arg['id']:
        amr.media_rename_id(arg['keyword'], arg['dir'], arg['password'], arg['number'])
    else:
        amr.media_rename_keyword(arg['keyword'], arg['dir'], arg['password'], arg['number'])


def command() -> dict:
    """
    设置命令行参数
    :return: 返回运行参数
    """
    # todo: 命令行添加操作提醒颜色

    parser = argparse.ArgumentParser(
        description="利用TMDB api获取剧集标题, 并对Alist对应剧集文件进行重命名, 便于播放器识别剧集",
        usage="python %(prog)s [options] keyword -d path",
        epilog="用例: python main.py 刀剑神域 -d /阿里云盘/刀剑神域/")
    parser.add_argument('-v', '--version', action='version',
                        version='AlistMediaRename version : v 1.0', help='显示版本信息')
    parser.add_argument("keyword", help="TMDB剧集查找字段")
    parser.add_argument("-d", "--dir", action='store', required=True, help="Alist剧集文件所在文件夹, 结尾需加/")
    parser.add_argument("-i", "--id", action="store_true", help="通过id搜索TMDB剧集信息(可选)")
    parser.add_argument("-c", "--config", action="store", help="指定配置文件路径, 默认为程序所在路径(可选)",
                        default='./config.json')
    parser.add_argument("-p", "--password", action="store", help="文件访问密码(可选)")
    parser.add_argument("-n", "--number", action="store", type=int, default=1,
                        help="指定从第几集开始重命名, 默认为1(可选)")
    parser.add_argument("--debug", action="store_false", default=True, help="debug模式, 输出信息更加详细")
    args = parser.parse_args()
    return dict(keyword=args.keyword,
                dir=args.dir,
                id=args.id,
                config_path=args.config,
                password=args.password,
                number=args.number,
                debug=args.debug)


if __name__ == '__main__':
    # test()
    argument = command()
    main(argument)
