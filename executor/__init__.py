#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executor 层：分阶段执行 + 并行工作者 + 结果组装

执行 DAG 任务，支持并行执行和结果组装。
"""

from .staged_executor import StagedExecutor, ExecutionResult
from .parallel_worker import ParallelWorker, WorkerConfig
from .assembler import Assembler, AssemblyResult

__all__ = [
    "StagedExecutor",
    "ExecutionResult",
    "ParallelWorker",
    "WorkerConfig",
    "Assembler",
    "AssemblyResult",
]
