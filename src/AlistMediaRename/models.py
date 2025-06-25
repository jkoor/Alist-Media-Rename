import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator, Field


class AlistConfig(BaseModel):
    """Alist配置参数"""

    # Alist 主页链接
    url: str = ""
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

    # TMDB Api Url
    api_url: str = "https://api.themoviedb.org/3"
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
    media_folder_rename: bool = True
    # 电影文件命名格式
    movie_name_format: str = "{name} ({year})"
    # 电影父文件夹命名格式
    movie_folder_name_format: str = "{name} ({year})"
    # 剧集文件命名格式
    tv_name_format: str = "{name}-S{season:0>2}E{episode:0>2}.{title}"
    # 剧集父文件夹命名格式
    tv_folder_name_format: str = "{name} ({year})"
    # 视频文件匹配正则表达式
    video_regex_pattern: str = r"(?i).*\.(avi|flv|wmv|mov|mp4|mkv|rm|rmvb)$"
    # 字幕文件匹配正则表达式
    subtitle_regex_pattern: str = r"(?i).*\.(ass|srt|ssa|sub)$"


class Settings(BaseModel):
    """配置"""

    alist: AlistConfig = AlistConfig()
    tmdb: TmdbConfig = TmdbConfig()
    amr: AmrConfig = AmrConfig()
    version: int = 1


class Formated_Variables:
    """重命名格式变量"""

    class movie(BaseModel):
        """电影重命名格式变量"""

        name: str  # 电影名称
        original_name: str  # 原始电影名称
        collection_name: str
        year: str  # 电影年份
        release_date: str  # 电影上映日期
        language: str  # 语言
        region: str  # 地区
        rating: float  # 评分
        tmdb_id: str  # TMDB ID

    class tv(BaseModel):
        """剧集重命名格式变量"""

        name: str  # 剧集名称
        original_name: str  # 原始剧集名称
        year: str  # 剧集年份
        first_air_date: str  # 剧集播放日期
        language: str  # 语言
        region: str  # 地区
        rating: float  # 剧集评分
        season: int  # 剧集季度
        season_year: str  # 季度年份
        tmdb_id: str  # TMDB ID

    class episode(BaseModel):
        """剧集重命名格式变量"""

        episode: int  # 单集编号
        air_date: str  # 单集播放日期
        episode_rating: float  # 单集评分
        title: str  # 单集标题


class Folder(BaseModel):
    path: str = Field(default="")

    def __str__(self):
        return self.path

    def parent_path(self):
        return self.path[: self.path[:-1].rfind("/") + 1]

    def current_path(self):
        return self.path.split("/")[-2]

    @field_validator("path", mode="after")
    @classmethod
    def ensure_slash(cls, path: str) -> str:
        """确保路径以 / 开头并以 / 结尾"""
        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path = path + "/"
        return path


class MediaMeta(BaseModel):
    """媒体元数据"""

    # 输入参数
    media_type: str  # 媒体类型, movie or tv
    rename_format: str  # 文件重命名格式
    movie_format_variables: Optional[Formated_Variables.movie]  # 格式变量
    tv_format_variables: Optional[Formated_Variables.tv]  # 格式变量
    episode_format_variables: Optional[Formated_Variables.episode]  # 格式变量

    # 自动生成参数
    fullname: str = ""  # 完整文件名

    # 根据文件重命名格式和格式变量生成目标文件名
    @model_validator(mode="after")
    def get_fullname(self) -> "MediaMeta":
        if self.media_type == "movie":
            if self.movie_format_variables is None:
                raise ValueError("movie_format_variables is None")
            fullname = self.rename_format.format(
                **self.movie_format_variables.model_dump()
            )
        elif self.media_type == "tv":
            if self.tv_format_variables is None:
                raise ValueError("tv_format_variables is None")
            if self.episode_format_variables is None:
                fullname = self.rename_format.format(
                    **self.tv_format_variables.model_dump()
                )
            else:
                fullname = self.rename_format.format(
                    **self.tv_format_variables.model_dump(),
                    **self.episode_format_variables.model_dump(),
                )
        else:
            raise ValueError("Unknown media type")

        # 替换非法字符为下划线
        illegal_char = r"[\/:*?\"<>|]"
        fullname = re.sub(illegal_char, "_", fullname)
        self.fullname = fullname

        return self


class FileMeta(BaseModel):
    """重命名文件元数据"""

    # 输入参数
    filename: str  # 原始完整文件名
    folder_path: Folder  # 文件夹路径

    # 自动生成参数
    prefix_name: str = ""  # 原始无后缀文件名
    extension: str = ""  # 文件扩展名

    @model_validator(mode="after")
    def get_prefix_name_and_extension(self) -> "FileMeta":
        parts = self.filename.rsplit(".", 1)
        if len(parts) == 2:
            prefix, suffix = parts
            suffix = "." + suffix
        else:
            prefix, suffix = self.filename, ""
        self.prefix_name = prefix
        self.extension = suffix
        return self


class RenameTask(BaseModel):
    """重命名任务"""

    # 输入参数
    file_meta: FileMeta  # 文件元数据
    media_meta: MediaMeta  # 媒体元数据

    # 自动生成参数
    original_name: str = ""  # 原始文件名
    target_name: str = ""  # 目标文件名
    folder_path: Folder = Folder()  # 文件夹路径
    full_path: str = ""  # 重命名文件路径

    @model_validator(mode="after")
    # 提取参数
    def get_args(self) -> "RenameTask":
        self.original_name = self.file_meta.filename
        self.target_name = self.media_meta.fullname + self.file_meta.extension
        self.folder_path = self.file_meta.folder_path
        self.full_path = self.folder_path.path + self.original_name
        return self


class ApiResponse(BaseModel):
    success: bool
    status_code: int
    error: str
    data: dict


class ApiResponseError(Exception):
    pass
