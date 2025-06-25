import importlib.resources
from ruamel.yaml import YAML
from .models import Settings
from .output import Message


class Config:
    """配置参数"""

    def __init__(self, filepath: str = ""):
        """初始化参数"""
        self.filepath = filepath
        self.settings = Settings()
        self._yaml = YAML()

        if self.filepath != "":
            try:
                self.load(self.filepath)

            except Exception as e:
                Message.error(f"加载配置文件失败: {e}")
                self.set()
                self.save(self.filepath)

    @property
    def alist(self):
        return self.settings.alist

    @property
    def tmdb(self):
        return self.settings.tmdb

    @property
    def amr(self):
        return self.settings.amr

    def info(self):
        """显示配置参数"""
        return self.settings.model_dump_json()

    def set(self):
        """设置配置参数"""
        info = Message.config_input()
        self.settings.alist.url = info["url"]
        self.settings.alist.user = info["user"]
        self.settings.alist.password = info["password"]
        self.settings.alist.totp = info["totp"]
        self.settings.tmdb.api_key = info["api_key"]

    def save(self, filepath: str, output: bool = True):
        """保存配置"""

        self._yaml.preserve_quotes = True
        with (
            importlib.resources.files("AlistMediaRename")
            .joinpath("default.yaml")
            .open("r", encoding="utf-8") as f
        ):
            default_config = self._yaml.load(f)

        # 更新默认配置
        for key, value in self.settings.alist.model_dump().items():
            default_config["alist"][key] = value
        for key, value in self.settings.tmdb.model_dump().items():
            default_config["tmdb"][key] = value
        for key, value in self.settings.amr.model_dump().items():
            default_config["amr"][key] = value

        # 保存配置
        with open(filepath, "w", encoding="utf-8") as file:
            self._yaml.dump(default_config, file)

        if output:
            Message.success(
                f"配置文件保存路径: {filepath}\n其余自定义设置请修改保存后的配置文件"
            )

        return True

    def load(self, filepath: str, output: bool = True):
        """加载配置"""

        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read()
        config_data = self._yaml.load(data)
        # 验证配置文件
        version: int = self.settings.version
        self.settings: Settings = Settings.model_validate(config_data)
        if version != config_data.get("version", 0):
            Message.warning("配置文件版本不匹配，已更新配置文件")
            self.settings.version = version
            self.save(filepath, output=False)

        if output:
            Message.success(f"配置文件加载路径: {filepath}")

        return True
