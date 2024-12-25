from pydantic import BaseModel


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


class RenameTask(BaseModel):
    """重命名任务"""

    original_name: str = ""  # 原始文件名
    target_name: str = ""  # 目标文件名
    folder_path: str = ""  # 文件夹路径


class ApiResponseModel(BaseModel):
    success: bool
    status_code: int
    error: str
    data: dict
    function: str
    args: tuple
    kwargs: dict
