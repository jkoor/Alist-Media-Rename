from .models import Settings
from .utils import PrintMessage


class Config:
    """配置参数"""

    def __init__(self, filepath = None):
        """初始化参数"""
        self.filepath = filepath
        self.settings = Settings()

        if self.filepath:
            try:
                self.load(self.filepath)
                
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                print("请重新设置配置参数")
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
        self.settings.alist.url = input("请输入Alist地址\n")
        self.settings.alist.user = input("请输入账号\n")
        self.settings.alist.password = input("请输入登录密码\n")
        self.settings.alist.totp = input(
            "请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请[回车]跳过\n"
        )
        self.settings.tmdb.api_key = input("请输入TMDB api密钥(V3)\n")

    def save(self, filepath: str, output: bool = True):
        """保存配置"""

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(self.settings.model_dump_json())

        if output:
            print(f"\n{PrintMessage.ColorStr.green("[✓]")} 配置文件保存路径: {filepath}")
            print("其余自定义设置请修改保存后的配置文件")

        return True

    def load(self, filepath: str, output: bool = True):
        """加载配置"""

        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read()

        self.settings = Settings.model_validate_json(data)

        if output:
            print(f"\n{PrintMessage.ColorStr.green("[✓]")} 配置文件加载路径: {filepath}")

        return True
