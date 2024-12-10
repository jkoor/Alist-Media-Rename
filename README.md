从 The Movie Database(TMDb) 获取剧集/电影信息，并对 Alist 指定媒体文件重命名，便于播放器刮削识别剧集/电影。测试Kodi, Nplayer, Infuse均可正确识别媒体信息。

![](./tutorial.gif)



## ToDo

- [x] 重命名异步操作，速度已较上个版本快数十倍
- [x] 自动通过 Alist 2FA 验证
- [x] 支持电影/剧集文件重命名
- [x] 根据关键字/TMDbID 搜索媒体信息
- [x] 从指定季数、指定集数开始重命名文件
- [x] 自动排除已重命名成功的文件
- [x] 指定文件重命名格式



## 安装依赖&注意事项

1. 环境配置

   Python(>=3.6)，建议使用 3.10 版本，已在 Windwos 11/Linux 测试通过。

2. 安装依赖

   从 PyPI 安装包

   `pip install AlistMediaRename`

   从 PyPI 升级包

   `pip install --upgrade AlistMediaRename`

   > 若想使用本地模块请进行操作：
   > 
   > 下载项目中的文件到本地，建议使用 git 命令`git clone https://github.com/jkoor/Alist-Media-Rename.git`
   > 安装以下四个库：`requests`, `pyotp`, `natsort`, `colorama`, `pydantic`

4. 下载`src/main.py` 主程序文件

5. 获取 TMDb API 密钥

   首次运行会要去输入 TMDb API 密钥， 用于获取 TMDb 电影/剧集信息，可前往 TMDb 官网免费申请，链接：https://developers.themoviedb.org/3/getting-started/introduction


6. Alist 2FA 验证（未开启可跳过）

   若用户开启了 Alist 2FA 验证功能，则需要提供验证密钥（非6位验证码），可通过保存验证码的对应 APP 获取，或者扫描初次绑定的二维码，可获取一串代码，最后的 sercet 字段即为 base64 密钥，格式为一串包含数字和字母的长字段，如：2ELR4M···KVH563X

   

## 快速开始

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

| 参数            | 类型 | 默认          | 说明                                      |
| --------------- | :--: | ------------- | ----------------------------------------- |
| keyword         | 必须 |               | TMDb 搜索字段                             |
| -d              | 必须 |               | Alist 文件夹路径                          |
| -i, --id        | 可选 |               | 根据 TMDb id 获取剧集/电影信息            |
| -m, --movie     | 可选 |               | 查找电影信息，而不是剧集                  |
| -p, --password  | 可选 | None          | Alist 文件夹访问密码                      |
| -n, --number    | 可选 | 1             | 指定从第几集开始命名                      |
| -c, --config    | 可选 | ./config.json | 指定配置文件路径                          |
| -f, --folderdir | 可选 | 1             | 覆盖配置文件中的`media_folder_rename`参数 |
| -h, --help      |  /   |               | 显示使用帮助信息                          |
| -v, --version   |  /   |               | 显示版本信息                              |

**配置文件**

在本地保存的配置文件中，除基本的登录参数外，还包含几个可配置项，根据注释修改即可。


## 模块使用

若需要在其他 Python 文件中调用本程序，可参考以下内容：

在`AlistMediaRename`文件夹定义了一个类Amr()，根据代码注释要求传入相关参数，即可调用本程序的主函数

```python
from AlistMediaRename import Amr, Config

# 第一种实例化方法，定义一个配置项
config = Config()
config.alist.url = "xxx"
config.alist.user = "xxx"
config.alist.password = "xxx"
config.alist.totp = "xxx"
config.tmdb.api_key = "xxx"
config.save("./config.json") # 保存配置到文件
config.load("./config.json") # 从文件中读取配置
amr = Amr(config)
# 第二种实例化方法，从文件中读取配置
amr = Amr("./config.json") # 从文件中读取配置，文件不存在则会自动创建

# 根据电影id获取TMDb信息，并重命名‘dir’指定路径文件
amr.movie_rename_id('keyword', 'dir', 'password')
# 根据电影关键词获取TMDb信息，并重命名‘dir’指定路径文件
amr.movie_rename_keyword('keyword', 'dir', 'password')
# 根据剧集id获取TMDb信息，并重命名‘dir’指定路径文件
amr.tv_rename_id('keyword', 'dir', 'password')
# 根据剧集关键词获取TMDb信息，并重命名‘dir’指定路径文件
amr.tv_rename_keyword('keyword', 'dir', 'password')

```



## 最后

- 本项目是受到了 GitHub 中一个获取TMDb信息并对本地文件重命名项目的启发：[wklchris/Media-Renamer](https://github.com/wklchris/Media-Renamer)

- TMDb Api 在短时间内频繁使用会限制使用，如出现此情况请稍后再试

- 欢迎邮件联系，一起交流探讨：oharcy@outlook.com

- 本程序使用 TMDB API，但未经 TMDB 认可或认证。

  ![](https://www.themoviedb.org/assets/2/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg)
