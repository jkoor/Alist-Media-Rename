import os
from AlistMediaRename import Amr, Config


# 初始化
# config = Config()
# config.alist.url = os.getenv("ALIST_URL", "")
# config.alist.user = os.getenv("ALIST_USER", "")
# config.alist.password = os.getenv("ALIST_PASSWORD", "")
# config.alist.totp = os.getenv("ALIST_TOTP", "")
# config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
# amr = Amr(config)

# 第二种实例化方法，从文件中读取配置
amr = Amr("local.yaml") # 从文件中读取配置，文件不存在则会自动创建
amr.config.save('config.yaml') # 保存配置到文件

# 根据聚集关键词获取TMDb信息，并重命名‘dir’指定路径文件
# amr.tv_rename_keyword("刀剑神域", "/debug/test", first_number='1')
