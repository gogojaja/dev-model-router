#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAG 构建器模块

将任务分解为有向无环图（DAG），支持依赖分析和并行执行。
"""

from __future__ import annotations

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Tuple
from pathlib import Path
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """任务节点"""
    id: str  # 唯一标识
    name: str  # 任务名称
    description: str  # 任务描述
    task_type: str  # 任务类型 ("code_generation" | "testing" | "documentation" | "review")
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务 ID 列表
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None  # 执行结果
    error: Optional[str] = None  # 错误信息
    model_tier: Optional[str] = None  # 分配的模型 tier
    estimated_cost: float = 0.0  # 预估成本
    actual_cost: float = 0.0  # 实际成本


@dataclass
class DAG:
    """
    有向无环图

    表示任务分解后的依赖关系图。
    """
    root_task: str  # 根任务描述
    nodes: Dict[str, TaskNode] = field(default_factory=dict)  # 所有节点
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def ready_tasks(self) -> List[TaskNode]:
        """获取可立即执行的任务（所有依赖已完成）"""
        ready = []
        for node in self.nodes.values():
            if node.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self.nodes[dep].status == TaskStatus.COMPLETED
                for dep in node.dependencies
                if dep in self.nodes
            )
            if deps_met:
                ready.append(node)
        return ready

    @property
    def is_complete(self) -> bool:
        """检查 DAG 是否已完成"""
        return all(
            node.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for node in self.nodes.values()
        )

    @property
    def is_failed(self) -> bool:
        """检查 DAG 是否有失败任务"""
        return any(
            node.status == TaskStatus.FAILED
            for node in self.nodes.values()
        )

    @property
    def total_cost(self) -> float:
        """计算总成本"""
        return sum(node.actual_cost for node in self.nodes.values())

    @property
    def critical_path(self) -> List[str]:
        """计算关键路径（最长依赖链）"""
        # 使用动态规划计算最长路径
        def longest_path(node_id: str) -> int:
            node = self.nodes[node_id]
            if not node.dependencies:
                return 1
            return 1 + max(
                longest_path(dep)
                for dep in node.dependencies
                if dep in self.nodes
            )

        # 找到最长路径的起点
        max_length = 0
        start_node = None
        for node_id in self.nodes:
            length = longest_path(node_id)
            if length > max_length:
                max_length = length
                start_node = node_id

        # 回溯关键路径
        if start_node is None:
            return []

        path = [start_node]
        current = start_node
        while self.nodes[current].dependencies:
            # 选择最长的依赖
            next_node = max(
                self.nodes[current].dependencies,
                key=lambda dep: longest_path(dep) if dep in self.nodes else 0
            )
            if next_node in self.nodes:
                path.append(next_node)
                current = next_node
            else:
                break

        return list(reversed(path))

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "root_task": self.root_task,
            "created_at": self.created_at.isoformat(),
            "nodes": {
                node_id: {
                    "id": node.id,
                    "name": node.name,
                    "description": node.description,
                    "task_type": node.task_type,
                    "dependencies": node.dependencies,
                    "status": node.status.value,
                    "result": node.result,
                    "error": node.error,
                    "model_tier": node.model_tier,
                    "estimated_cost": node.estimated_cost,
                    "actual_cost": node.actual_cost,
                }
                for node_id, node in self.nodes.items()
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Path):
        """保存到文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> DAG:
        """从文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dag = cls(root_task=data["root_task"])
        dag.created_at = datetime.fromisoformat(data["created_at"])

        for node_id, node_data in data["nodes"].items():
            dag.nodes[node_id] = TaskNode(
                id=node_data["id"],
                name=node_data["name"],
                description=node_data["description"],
                task_type=node_data["task_type"],
                dependencies=node_data["dependencies"],
                status=TaskStatus(node_data["status"]),
                result=node_data.get("result"),
                error=node_data.get("error"),
                model_tier=node_data.get("model_tier"),
                estimated_cost=node_data.get("estimated_cost", 0.0),
                actual_cost=node_data.get("actual_cost", 0.0),
            )

        return dag


class DAGBuilder:
    """
    DAG 构建器

    Usage:
        builder = DAGBuilder()
        dag = builder.build("实现用户登录功能")
        print(dag.to_json())
    """

    def build(self, task_description: str, context: Optional[Dict] = None) -> DAG:
        """
        构建 DAG

        Args:
            task_description: 任务描述
            context: 上下文信息（可选）

        Returns:
            DAG: 任务依赖图
        """
        from .task_splitter import TaskSplitter, SplitStrategy

        dag = DAG(root_task=task_description)

        complexity = (context or {}).get("complexity", "medium")
        splitter = TaskSplitter()
        subtasks = splitter.split_smart(
            task_description,
            complexity=complexity,
            strategy=SplitStrategy.HYBRID,
        )

        for st in subtasks:
            dag.nodes[st.id] = TaskNode(
                id=st.id,
                name=st.name,
                description=st.description,
                task_type=st.task_type,
                dependencies=st.dependencies,
            )

        return dag

    def build_custom(
        self,
        task_description: str,
        custom_tasks: List[Dict],
    ) -> DAG:
        """
        构建自定义 DAG

        Args:
            task_description: 任务描述
            custom_tasks: 自定义任务列表

        Returns:
            DAG: 任务依赖图
        """
        dag = DAG(root_task=task_description)

        for task in custom_tasks:
            dag.nodes[task["id"]] = TaskNode(
                id=task["id"],
                name=task["name"],
                description=task["description"],
                task_type=task["task_type"],
                dependencies=task.get("dependencies", []),
            )

        return dag
