import os
from test.utils import TestUtils
from AlistMediaRename import Amr, Config


def test_tv_rename_id(monkeypatch):
    # 模拟用户输入
    inputs = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    tv_id = "45782"
    folderpath = "./test/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".mp4")
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".ass")
    results = amr.tv_rename_id(tv_id, "files/test_amr/episode")
    for result in results:
        assert result.success

    TestUtils.delete_folder(folderpath)


def test_tv_rename_keyword(monkeypatch):
    # 模拟用户输入
    inputs = iter(["0", "1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    keyword = "约会大作战"
    folderpath = "./test/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".mp4")
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".ass")
    results = amr.tv_rename_keyword(keyword, "files/test_amr/episode")
    for result in results:
        assert result.success
    TestUtils.delete_folder(folderpath)


def test_movie_rename_id(monkeypatch):
    # 模拟用户输入
    inputs = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    movie_id = "24428"
    folderpath = "./test/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".mp4")
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".ass")
    results = amr.movie_rename_id(movie_id, "files/test_amr/movie")
    for result in results:
        assert result.success
    TestUtils.delete_folder(folderpath)


def test_movie_rename_keyword(monkeypatch):
    # 模拟用户输入
    inputs = iter(["3", "1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    keyword = "复仇者联盟"
    folderpath = "./test/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".mp4")
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".ass")
    results = amr.movie_rename_keyword(keyword, "files/test_amr/movie")
    for result in results:
        assert result.success
    TestUtils.delete_folder(folderpath)
