import asyncio
import time

import httpx
import pytest

from AlistMediaRename.models import ApiResponse
from AlistMediaRename.task import ApiTask, TaskManager


def _task(operation, started, completed):
    def request_factory():
        return httpx.Request("POST", "https://example.invalid")

    task = ApiTask(
        request_factory,
        (),
        {},
        operation,
        lambda response: ApiResponse(success=True, status_code=200, error="", data={}),
        lambda api_task: None,
        False,
    )

    async def send(client):
        started.append(time.perf_counter())
        await asyncio.sleep(0.01)
        task.response = ApiResponse(success=True, status_code=200, error="", data={})
        completed.append(time.perf_counter())
        return task.response

    task.send = send
    return task


@pytest.fixture
def task_manager():
    manager = TaskManager()
    manager.tasks_pending.clear()
    manager.tasks_done.clear()
    manager.limit_rate = 10
    manager.rename_interval = 0
    manager._last_rename_batch_completed = None
    yield manager
    manager.tasks_pending.clear()
    manager.rename_interval = 0
    manager._last_rename_batch_completed = None


def test_rename_tasks_wait_between_concurrent_batches(task_manager):
    started = []
    completed = []
    task_manager.limit_rate = 2
    task_manager.rename_interval = 0.03
    task_manager.add_tasks(
        *[_task("alist.rename", started, completed) for _ in range(4)]
    )

    asyncio.run(task_manager._execute())

    assert abs(started[0] - started[1]) < 0.02
    assert min(started[2:]) - max(completed[:2]) >= 0.025


def test_rename_interval_does_not_delay_non_rename_tasks(task_manager):
    started = []
    completed = []
    task_manager.limit_rate = 2
    task_manager.rename_interval = 0.1
    task_manager.add_tasks(
        *[_task("tmdb.tv_info", started, completed) for _ in range(2)]
    )

    started_at = time.perf_counter()
    asyncio.run(task_manager._execute())

    assert time.perf_counter() - started_at < 0.05
    assert abs(started[0] - started[1]) < 0.02
