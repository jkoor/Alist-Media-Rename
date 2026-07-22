from types import SimpleNamespace

import pytest

from AlistMediaRename import Config
from AlistMediaRename.models import FileMeta, Folder
from AlistMediaRename.output import Message
from AlistMediaRename.utils import Helper


def _task(data):
    return SimpleNamespace(response=SimpleNamespace(data=data))


def _tv_info_task():
    return _task(
        {
            "name": "测试剧集",
            "original_name": "Test Show",
            "first_air_date": "2020-01-01",
            "original_language": "en",
            "origin_country": ["US"],
            "vote_average": 8.0,
        }
    )


def _season_task(number, episodes):
    return _task(
        {
            "season_number": number,
            "air_date": f"202{number}-01-01",
            "episodes": [
                {
                    "episode_number": episode,
                    "air_date": f"202{number}-01-{episode:02}",
                    "vote_average": 8.0,
                    "name": f"第{episode}集",
                }
                for episode in episodes
            ],
        }
    )


def test_parse_number_ranges_supports_multiple_seasons():
    assert Message.parse_number_ranges("1,3-4,2,4-", 5) == [1, 2, 3, 4, 5]


@pytest.mark.parametrize("value", ["", "1,,2", "a", "1-0", "1-6", "-1"])
def test_parse_number_ranges_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        Message.parse_number_ranges(value, 5)


def test_selected_seasons_are_combined_in_season_order():
    config = Config()
    config.amr.tv_name_format = "{name}-S{season:0>2}E{episode:0>2}.{title}"

    tv_info = _tv_info_task()
    season_one, _ = Helper.create_tv_media_list(
        "1-", tv_info, _season_task(1, [1, 2]), "123", config
    )
    season_two, _ = Helper.create_tv_media_list(
        "1-", tv_info, _season_task(2, [1, 2]), "123", config
    )

    files = [
        FileMeta(filename=f"{number:02}.mkv", folder_path=Folder(path="/测试剧集/"))
        for number in range(1, 5)
    ]
    rename_tasks = Helper.match_episode_files(season_one + season_two, files, config)

    assert [task.target_name for task in rename_tasks] == [
        "测试剧集-S01E01.第1集.mkv",
        "测试剧集-S01E02.第2集.mkv",
        "测试剧集-S02E01.第1集.mkv",
        "测试剧集-S02E02.第2集.mkv",
    ]
    assert all(task.full_path.startswith("/测试剧集/") for task in rename_tasks)


def test_folder_rename_replaces_the_entire_name_when_it_contains_a_dot():
    config = Config()
    _, folder_media_list = Helper.create_tv_media_list(
        "1-", _tv_info_task(), _season_task(1, [1]), "123", config
    )

    rename_task = Helper.create_folder_rename_list(
        Folder(path="/影视/测试剧集.1080p/"), folder_media_list
    )[0]

    assert rename_task.original_name == "测试剧集.1080p"
    assert rename_task.target_name == "测试剧集 (2020)"
