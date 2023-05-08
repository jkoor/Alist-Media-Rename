# Alist Media Rename

---

从 The Movie Database(TMDb) 获取剧集/电影信息，并对 Alist 指定媒体文件重命名，便于播放器刮削识别剧集/电影。测试Kodi, Nplayer, Infuse均可正确识别媒体信息。

![](https://raw.githubusercontent.com/jkoor/AlistMediaRename/main/tutorial.gif)



## ToDo

---

- [x] 自动通过 Alist 2FA 验证
- [x] 支持电影/剧集文件重命名
- [x] 根据关键字/TMDbID 搜索媒体信息
- [x] 从指定季数、指定集数开始重命名文件
- [x] 自动创建剧名、季度文件夹，并整理媒体文件
- [x] 自定义文件重命名格式
- [x] 指定TMDb获取信息及重命名语言，默认为简体中文
- [ ] 自动识别媒体文件，重命名并整理到相应文件夹



## 安装依赖&注意事项

---

1. 环境配置

​	Python(>=3.6)，建议使用 3.10 版本，已在 Windwos 11/Linux 测试通过。

2. 下载项目中的文件到本地，建议使用 git 命令`git clone `

3. 进入项目文件夹使用`pip install -r requirements.txt`安装依赖，或者手动安装以下四个库：

   - requests    用于建立 http 连接获取信息

   - pyotp       用于计算 Alist 2FA 验证码

   - natsort     用于对媒体文件进行更加合理的排序

   - colorama    用于交互中输出彩色提醒文字

4. 获取 TMDb API 密钥

   首次运行会要去输入 TMDb API 密钥， 用于获取 TMDb 电影/剧集信息，可前往 TMDb 官网免费申请，链接：https://developers.themoviedb.org/3/getting-started/introduction


5. Alist 2FA 验证（未开启可跳过）

   若用户开启了 Alist 2FA 验证功能，则需要提供验证密钥（非6位验证码），可通过保存验证码的对应 APP 获取，或者扫描初次绑定的二维码，可获取一串代码，最后的 sercet 字段即为 base64 密钥，格式为一串包含数字和字母的长字段，如：2ELR4M···KVH563X

   

## 快速开始

---

初始使用请按提示输入 Alist 网址、账号、密码、2FA 密钥以及 TMDb API 密钥，配置信息会保存在同目录下`config.json`文件中。

**使用方法**

```
# 根据剧集关键字获取剧集信息，并对指定文件夹中的媒体文件重命名
python main.py [剧集关键字] -d [Alist 文件夹路径]

# 根据剧集id精确获取剧集信息，并对指定文件夹中的媒体文件重命名
python main.py -i [剧集id] -d [Alist 文件夹路径]

# 指定从剧集第几集开始重命名，请加上 -n [number] 参数
python main.py [剧集关键字] -d [Alist 文件夹路径] -n [集数]

# 若要对电影文件进行重命名，请加上 -m 参数
python main.py -m [电影关键字] -d [Alist 文件夹路径]
python main.py -m -i [电影id] -d [Alist 文件夹路径]

# 若 Alist 指定文件夹设有访问密码，请加上 -p [password] 参数
python main.py [剧集关键字] -d [Alist 文件夹路径] -p [路径访问密码]

# 获取完整使用帮助信息
python main.py -h
```

**举个例子**

TMDb 的剧集/电影 id 为对应网址中的数字，如剧集[《刀剑神域》](https://www.themoviedb.org/tv/45782)的 id 为 45782，电影《[刀剑神域：序列之争](https://www.themoviedb.org/movie/413594)》的 id 为 413594

剧集《刀剑神域》的视频及字幕文件在 Alist 网盘中路径为：/阿里云盘/动漫/SAO/

文件重命名前后对比：1.mp4 -> 刀剑神域-S01E01.剑的世界.mp4

```
# 通过关键字获取剧集信息，并重命名文件
python main.py 刀剑神域 -d /阿里云盘/动漫/SAO

# 通过剧集 id 获取剧集信息，并重命名文件，文件访问密码为123
python main.py -i 45782 -d /阿里云盘/动漫/SAO -p 123
```

电影《刀剑神域：序列之争》的视频及字幕文件在 Alist 网盘中路径为：/阿里云盘/电影/SAO

```
# 通过关键字获取电影信息，并重命名文件
python main.py -m 刀剑神域 -d /阿里云盘/电影/SAO

# 通过电影 id 获取电影信息，并重命名文件，文件访问密码为123
python main.py -m -i 413594 -d /阿里云盘/电影/SAO -p 123
```

完整参数列表：python main.py -[?] [keyword] -d [dir]

| 参数           | 类型 | 默认          | 说明                           |
| -------------- | :--: | ------------- | ------------------------------ |
| keyword        | 必须 |               | TMDb 搜索字段                  |
| -d             | 必须 |               | Alist 文件夹路径               |
| -i, --id       | 可选 |               | 根据 TMDb id 获取剧集/电影信息 |
| -m, --movie    | 可选 |               | 查找电影信息，而不是剧集       |
| -p, --password | 可选 | None          | Alist 文件夹访问密码           |
| -n, --number   | 可选 | 1             | 指定从第几集开始命名           |
| -c, --config   | 可选 | ./config.json | 指定配置文件路径               |
| --debug        | 可选 |               | debug 模式，输出更加详细的信息 |
| -h, --help     |  /   |               | 显示使用帮助信息               |

**配置文件**

在本地保存的配置文件中，除基本的登录参数外，在`settings`字段中包含以下几个可配置项

1. tmdb_language: zh-CN

指定TMDb获取信息及重命名语言，遵循 ISO 639-1 标准，默认为`zh-CN`

2. media_folder_rename: true/false

指定是否对父文件夹重命名，命名格式为【剧名 (首播年份)】，如：刀剑神域 (2012)，默认为`false`

3. tv_name_format： {name}-S{season:0>2}E{episode:0>2}.{title}

文件命名格式，使用python的`format()`函数识别，若不了解，请勿随机改动。

默认命名：刀剑神域-S01E01.剑的世界.mp4

更改举例：{name}-第{season:0>1}季-第{episode:0>3}集

文件命名：刀剑神域-第1季-第001集.mp4

4. tv_season_dir: true/false

5. tv_season_format: Season {season}

是否创建季度文件夹，以及季度文件夹命名格式。设置为`true`则会在 Alist 路径中创建剧集对应季度的文件夹，并将剧集移动到季度文	件夹中，默认命名格式举例：Season 1

>若有较多的剧集/电影文件，为方便播放器搜刮以及后期维护整理，建议创建剧名文件夹与季度文件夹。
>
>开启 media_folder_rename 和 tv_season_dir 功能后，文件树大致为：
>
>
>
>SAO               ------->     刀剑神域 (2012)
>├─ 1.ass                       └─Season 1
>├─ ······                               ├─ 刀剑神域-S01E01.剑的世界.ass
>└─ 12.mp4                        ├─ ······
>                                                └─ 刀剑神域-S01E12.结衣的心.mp4

6. video_suffix_list
7. subtitle_suffix_list

需要识别的视频/字幕文件扩展名



## 调用函数

---

若需要在其他 Python 文件中调用本程序，可参考以下内容：

Alist Media Rename
├─ api.py  # Alist请求api函数以及TMDb获取信息函数
├─ meida_rename.py  # 实现获取信息并重命名的主函数
└─ main.py  # 程序运行主函数

在`meida_rename.py`中定义了一个类`AlistMediaRename()`，根据代码注释要求传入相关参数，即可调用本程序的主函数

```python
from media_name import AlistMediaRename

# 定义类
amr = AlistMediaRename('alist_url', 'alist_user', 'alist_password', 'alist_totp','tmdb_key', 'debug')
# 根据电影id获取TMDb信息，并重命名‘dir’指定路径文件
amr.movie_rename_id('keyword', 'dir', 'password')
# 根据电影关键词获取TMDb信息，并重命名‘dir’指定路径文件
amr.movie_rename_keyword('keyword', 'dir', 'password')
# 根据剧集id获取TMDb信息，并重命名‘dir’指定路径文件
amr.tv_rename_id('keyword', 'dir', 'password')
# 根据剧集关键词获取TMDb信息，并重命名‘dir’指定路径文件
amr.tv_rename_keyword('keyword', 'dir', 'password')

```

在`api`文件中定义了两个类，一个是 `AlistApi()`，一个是`TMDBApi`

`AlistApi()`目前已经实现了对 Alist 文件的常用操作，包括：获取文件列表/新建文件夹/重命名/删除/移动/上传/获取下载链接。

```python
from api import AlistApi
# 定义类，类初始化时会调用login()函数，自动登录
alist = AlistApi('url', 'user', 'password', 'totp_code')
# 获取指定路径文件列表
alist.file_list('path', 'password')
# 重命名指定路径文件/文件夹
alist.rename('name', 'path')
# 移动文件到指定路径
alist.move([names], 'src_dir', 'dst_dir')
# 新建文件夹
alist.mkdir('path')
# 删除文件/文件夹
alist.remove('path', [names])
# 获取文件下载链接
alist.download_link('path', 'password')
# 上传文件
alist.upload('path', 'file')
# 获取存储驱动列表
alist.disk_list()

```



## 最后

---

- 本项目是受到了 GitHub 中一个获取TMDb信息并对本地文件重命名项目的启发：[wklchris/Media-Renamer](https://github.com/wklchris/Media-Renamer)

- 欢迎提交 issue 反馈 bug 或功能性建议
- TMDb Api 在短时间内频繁使用会限制使用，如出现此情况请稍后再试
