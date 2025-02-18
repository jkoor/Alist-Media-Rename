import os
from unittest import mock

from AlistMediaRename import Amr, Config
from test.utils import TestUtils


@mock.patch("builtins.input")
def test_tv_rename_id(mocked_input):
    # 模拟用户输入
    mocked_input.side_effect = ["1", "y"]
    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    tv_id = "45782"
    folderpath = "./tmp/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".mp4")
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".ass")
    amr.tv_rename_id(tv_id, "/files/test_amr/episode")
    for task in amr._taskManager.tasks_done:
        assert task.response.success
    TestUtils.delete_folder(folderpath)


@mock.patch("builtins.input")
def test_tv_rename_keyword(mocked_input):
    # 模拟用户输入
    mocked_input.side_effect = ["0", "1", ""]

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    keyword = "约会大作战"
    folderpath = "./tmp/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".mp4")
    TestUtils.generate_random_files(folderpath, 15, 1, "episode", ".ass")
    result = amr.tv_rename_keyword(keyword, "files/test_amr/episode")
    for task in amr._taskManager.tasks_done:
        assert task.response.success

    TestUtils.delete_folder(folderpath)


@mock.patch("builtins.input")
def test_movie_rename_id(mocked_input):
    # 模拟用户输入
    mocked_input.side_effect = ["1", "y"]

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    movie_id = "24428"
    folderpath = "./tmp/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".mp4")
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".ass")
    result = amr.movie_rename_id(movie_id, "files/test_amr/movie")
    for task in amr._taskManager.tasks_done:
        assert task.response.success

    TestUtils.delete_folder(folderpath)


@mock.patch("builtins.input")
def test_movie_rename_keyword(mocked_input):
    # 模拟用户输入
    mocked_input.side_effect = ["3", "1", " ", ""]

    # 初始化
    config = Config()
    config.alist.url = os.getenv("ALIST_URL", "")
    config.alist.user = os.getenv("ALIST_USER", "")
    config.alist.password = os.getenv("ALIST_PASSWORD", "")
    config.alist.totp = os.getenv("ALIST_TOTP", "")
    config.tmdb.api_key = os.getenv("TMDB_API_KEY", "")
    amr = Amr(config)

    keyword = "复仇者联盟"
    folderpath = "./tmp/files/test_amr/"
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".mp4")
    TestUtils.generate_random_files(folderpath, 2, 1, "movie", ".ass")
    result = amr.movie_rename_keyword(keyword, "files/test_amr/movie")
    for task in amr._taskManager.tasks_done:
        assert task.response.success

    TestUtils.delete_folder(folderpath)
