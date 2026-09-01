#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decomposer 层：DAG 构建 + 任务拆分 + 依赖分析

将复杂任务分解为有向无环图（DAG），支持并行执行。
"""

from .dag_builder import DAGBuilder, TaskNode, DAG
from .task_splitter import TaskSplitter, SplitStrategy
from .dependency import DependencyAnalyzer

__all__ = [
    "DAGBuilder",
    "TaskNode",
    "DAG",
    "TaskSplitter",
    "SplitStrategy",
    "DependencyAnalyzer",
]
