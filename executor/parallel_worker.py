#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行工作者模块

支持多任务并行执行的工作池。
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future

from ..decomposer.dag_builder import TaskNode, TaskStatus


@dataclass
class WorkerConfig:
    """工作者配置"""
    max_workers: int = 4  # 最大并行数
    timeout: float = 300.0  # 单任务超时（秒）
    retry_count: int = 3  # 重试次数
    queue_size: int = 100  # 任务队列大小


@dataclass
class WorkerResult:
    """工作者执行结果"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict] = None
    error: Optional[str] = None
    worker_id: int = 0
    duration: float = 0.0


class ParallelWorker:
    """
    并行工作者

    Usage:
        worker = ParallelWorker(config=WorkerConfig(max_workers=4))
        results = worker.execute(tasks)
    """

    def __init__(
        self,
        config: Optional[WorkerConfig] = None,
        task_executor: Optional[Callable] = None,
    ):
        """
        初始化并行工作者

        Args:
            config: 工作者配置
            task_executor: 任务执行函数
        """
        self.config = config or WorkerConfig()
        self.task_executor = task_executor or self._default_executor
        self._task_queue: queue.Queue = queue.Queue(maxsize=self.config.queue_size)
        self._results: List[WorkerResult] = []
        self._lock = threading.Lock()

    def execute(
        self,
        tasks: List[TaskNode],
        model_selections: Optional[Dict[str, Any]] = None,
    ) -> List[WorkerResult]:
        """
        并行执行任务

        Args:
            tasks: 任务列表
            model_selections: 模型选择结果

        Returns:
            List[WorkerResult]: 执行结果列表
        """
        self._results = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures: Dict[Future, TaskNode] = {}

            for task in tasks:
                future = executor.submit(
                    self._execute_with_retry,
                    task,
                    model_selections.get(task.id) if model_selections else None,
                )
                futures[future] = task

            for future in futures:
                try:
                    result = future.result(timeout=self.config.timeout)
                    self._results.append(result)
                except Exception as e:
                    task = futures[future]
                    self._results.append(WorkerResult(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        error=str(e),
                    ))

        return self._results

    def _execute_with_retry(
        self,
        task: TaskNode,
        model_selection: Any,
    ) -> WorkerResult:
        """带重试的执行"""
        last_error = None

        for attempt in range(self.config.retry_count):
            try:
                start_time = __import__("time").time()
                result = self.task_executor(task, model_selection)
                duration = __import__("time").time() - start_time

                return WorkerResult(
                    task_id=task.id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    worker_id=threading.current_thread().ident or 0,
                    duration=duration,
                )
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    __import__("time").sleep(1 * (attempt + 1))  # 指数退避

        return WorkerResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            error=f"重试 {self.config.retry_count} 次后失败: {last_error}",
        )

    def _default_executor(
        self, task: TaskNode, model_selection: Any
    ) -> Dict:
        """默认执行器"""
        return {
            "task_id": task.id,
            "status": "completed",
            "output": f"Task {task.id} executed",
        }
