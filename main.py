# -*- coding: utf-8 -*-
# @Time : 2023/5/1/0001 18:10
# @Author : JKOR
# @File : main.py
# @Software: PyCharm

import json

from media_name import AlistMediaRename


def load_config(config_path):
    # 读取配置文件
    try:
        config = json.load(open(config_path, "r"))
    # 若文件不存在则创建文件
    except FileNotFoundError:
        settings = dict(video_suffix_list=[
            'mp4', 'mkv', 'flv', 'avi', 'mpg', 'mpeg', 'mov'
        ],
                        subtitle_suffix_list=['srt', 'ass', 'stl'],
                        tmdb_lanuage="zh-CN",
                        tv_folder_rename=False,
                        tv_season_dir=False)

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
        json.dump(config, open(config_path, "w"))
        print("\n配置文件保存路径: {}".format(config_path))
        print("其余自定义设置请修改保存后的配置文件")
    return config


def main():
    config = load_config('./config.json')
    amr = AlistMediaRename(config['alist_url'], config['alist_user'],
                           config['alist_password'], config['alist_totp'],
                           config['tmdb_key'])
    for k in config['settings']:
        exec(f"amr.{k} = config['settings']['{k}']")
    amr.media_rename_id('67075-100', '阿里云盘/来自分享/转生贤者的异世界生活/')
    # amr.media_rename_keyword('转生贤者的异世界生', '阿里云盘/来自分享/转生贤者的异世界生活/')


main()
