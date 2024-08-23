from typing import Callable
from pydantic import BaseModel


class AlistConfig(BaseModel):
    """Alist配置参数"""

    # Alist 主页链接
    url: str = "https://alist.nn.ci"
    # 使用游客权限，无需登录
    guest_mode: bool = False
    # Alist 登录账号
    user: str = ""
    # Alist 登录密码
    password: str = ""
    # Alist 2FA 验证码
    totp: str = ""


class TmdbConfig(BaseModel):
    """Tmdb配置参数"""

    # TMDB Api Key(V3)
    api_key: str = ""
    # TMDB 搜索语言
    language: str = "zh-CN"


class AmrConfig(BaseModel):
    """AMR配置参数"""

    # 是否排除已重命名文件
    exclude_renamed: bool = True
    # 使用异步方式加快重命名操作
    rename_by_async: bool = True
    # 是否重命名父文件夹
    media_folder_rename: int = 1
    # 季度文件夹命名格式
    tv_season_format: str = "Season {season}"
    # 视频文件匹配正则表达式
    video_regex_pattern: str = r"(?i).*\.(avi|flv|wmv|mov|mp4|mkv|rm|rmvb)$"
    # 字幕文件匹配正则表达式
    subtitle_regex_pattern: str = r"(?i).*\.(ass|srt|ssa|sub)$"


class Settings(BaseModel):
    """配置"""

    alist: AlistConfig = AlistConfig()
    tmdb: TmdbConfig = TmdbConfig()
    amr: AmrConfig = AmrConfig()


class Task(BaseModel):
    """任务"""

    # 任务名称
    name: str
    # 任务函数
    func: Callable
    # 任务参数
    args: dict = {}

class TaskResult(BaseModel):
    """任务结果"""

    # 任务名称
    name: str
    # 任务函数
    func_name: str
    # 任务参数
    args: dict
    # 任务结果
    success: bool = False
    # 返回数据
    result: dict
    # 任务异常
    error: str|None = None


