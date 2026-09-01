#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务拆分器模块

将复杂任务拆分为可并行执行的子任务。
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List


class SplitStrategy(Enum):
    """拆分策略"""
    SEQUENTIAL = "sequential"    # 顺序执行（依赖强）
    PARALLEL = "parallel"        # 并行执行（无依赖）
    PIPELINE = "pipeline"        # 流水线执行（弱依赖）
    HYBRID = "hybrid"            # 混合策略


@dataclass
class SubTask:
    """子任务"""
    id: str
    name: str
    description: str
    task_type: str
    dependencies: List[str]
    estimated_complexity: str  # "low" | "medium" | "high"
    estimated_cost: float


class TaskSplitter:
    """
    任务拆分器

    Usage:
        splitter = TaskSplitter()
        subtasks = splitter.split("实现用户登录功能")
        print(subtasks)
    """

    # 任务拆分模板
    SPLIT_TEMPLATES = {
        "code_generation": [
            {"id": "design", "name": "设计", "task_type": "architecture", "dependencies": []},
            {"id": "implement_core", "name": "核心实现", "task_type": "code_generation", "dependencies": ["design"]},
            {"id": "implement_utils", "name": "工具函数", "task_type": "code_generation", "dependencies": ["design"]},
            {"id": "test", "name": "单元测试", "task_type": "testing", "dependencies": ["implement_core", "implement_utils"]},
            {"id": "integrate", "name": "集成", "task_type": "code_generation", "dependencies": ["test"]},
        ],
        "documentation": [
            {"id": "api_doc", "name": "API 文档", "task_type": "documentation", "dependencies": []},
            {"id": "user_guide", "name": "用户指南", "task_type": "documentation", "dependencies": []},
            {"id": "examples", "name": "示例代码", "task_type": "documentation", "dependencies": ["api_doc"]},
        ],
        "testing": [
            {"id": "unit_tests", "name": "单元测试", "task_type": "testing", "dependencies": []},
            {"id": "integration_tests", "name": "集成测试", "task_type": "testing", "dependencies": ["unit_tests"]},
            {"id": "e2e_tests", "name": "端到端测试", "task_type": "testing", "dependencies": ["integration_tests"]},
        ],
    }

    def split(
        self,
        task_description: str,
        strategy: SplitStrategy = SplitStrategy.PIPELINE,
        max_subtasks: int = 10,
    ) -> List[SubTask]:
        """
        拆分任务

        Args:
            task_description: 任务描述
            strategy: 拆分策略
            max_subtasks: 最大子任务数

        Returns:
            List[SubTask]: 子任务列表
        """
        # 根据任务描述判断类型
        task_type = self._detect_task_type(task_description)

        # 获取拆分模板
        template = self.SPLIT_TEMPLATES.get(task_type, self.SPLIT_TEMPLATES["code_generation"])

        # 生成子任务
        subtasks = []
        for i, task in enumerate(template[:max_subtasks]):
            subtasks.append(SubTask(
                id=task["id"],
                name=task["name"],
                description=f"{task['name']}: {task_description}",
                task_type=task["task_type"],
                dependencies=task["dependencies"],
                estimated_complexity="medium",
                estimated_cost=0.0,
            ))

        return subtasks

    def split_by_complexity(
        self,
        task_description: str,
        complexity_scores: Dict[str, float],
    ) -> List[SubTask]:
        """
        根据复杂度拆分任务

        Args:
            task_description: 任务描述
            complexity_scores: 各部分的复杂度分数

        Returns:
            List[SubTask]: 子任务列表
        """
        subtasks = []
        for i, (part, score) in enumerate(complexity_scores.items()):
            if score > 0.7:
                complexity = "high"
            elif score > 0.3:
                complexity = "medium"
            else:
                complexity = "low"

            subtasks.append(SubTask(
                id=f"subtask_{i}",
                name=part,
                description=f"{part}: {task_description}",
                task_type="code_generation",
                dependencies=[],
                estimated_complexity=complexity,
                estimated_cost=score * 0.01,  # 简单估算
            ))

        return subtasks

    def split_smart(
        self,
        task_description: str,
        complexity: str = "medium",
        strategy: SplitStrategy = SplitStrategy.HYBRID,
    ) -> List[SubTask]:
        """
        智能任务拆分（IT-02增强）

        Args:
            task_description: 任务描述
            complexity: 复杂度级别 (low/medium/high)
            strategy: 拆分策略

        Returns:
            List[SubTask]: 子任务列表
        """
        task_type = self._detect_task_type(task_description)

        # 根据策略选择模板
        if strategy == SplitStrategy.HYBRID:
            if complexity == "high":
                template = self._get_hybrid_high_template(task_type)
            elif complexity == "low":
                template = self._get_hybrid_low_template(task_type)
            else:
                template = self.SPLIT_TEMPLATES.get(task_type, self.SPLIT_TEMPLATES["code_generation"])
        else:
            template = self.SPLIT_TEMPLATES.get(task_type, self.SPLIT_TEMPLATES["code_generation"])

        subtasks = []
        for i, task in enumerate(template):
            subtasks.append(SubTask(
                id=task["id"],
                name=task["name"],
                description=f"{task['name']}: {task_description}",
                task_type=task["task_type"],
                dependencies=task["dependencies"],
                estimated_complexity=complexity,
                estimated_cost=0.0,
            ))

        return subtasks

    def _get_hybrid_high_template(self, task_type: str) -> List[Dict]:
        """高复杂度混合模板"""
        if task_type == "code_generation":
            return [
                {"id": "requirements", "name": "需求分析", "task_type": "planning", "dependencies": []},
                {"id": "architecture", "name": "架构设计", "task_type": "architecture", "dependencies": ["requirements"]},
                {"id": "interface", "name": "接口定义", "task_type": "architecture", "dependencies": ["architecture"]},
                {"id": "core_impl", "name": "核心实现", "task_type": "code_generation", "dependencies": ["interface"]},
                {"id": "util_impl", "name": "工具实现", "task_type": "code_generation", "dependencies": ["interface"]},
                {"id": "unit_test", "name": "单元测试", "task_type": "testing", "dependencies": ["core_impl", "util_impl"]},
                {"id": "integration", "name": "集成测试", "task_type": "testing", "dependencies": ["unit_test"]},
                {"id": "review", "name": "代码审查", "task_type": "review", "dependencies": ["integration"]},
                {"id": "docs", "name": "文档编写", "task_type": "documentation", "dependencies": ["core_impl"]},
            ]
        return self.SPLIT_TEMPLATES.get(task_type, self.SPLIT_TEMPLATES["code_generation"])

    def _get_hybrid_low_template(self, task_type: str) -> List[Dict]:
        """低复杂度混合模板"""
        if task_type == "code_generation":
            return [
                {"id": "quick_plan", "name": "快速规划", "task_type": "planning", "dependencies": []},
                {"id": "implement", "name": "实现", "task_type": "code_generation", "dependencies": ["quick_plan"]},
                {"id": "verify", "name": "验证", "task_type": "testing", "dependencies": ["implement"]},
            ]
        return self.SPLIT_TEMPLATES.get(task_type, self.SPLIT_TEMPLATES["code_generation"])

    def _detect_task_type(self, task_description: str) -> str:
        """检测任务类型"""
        task_lower = task_description.lower()

        if any(kw in task_lower for kw in ["test", "测试", "验证"]):
            return "testing"
        elif any(kw in task_lower for kw in ["doc", "文档", "说明"]):
            return "documentation"
        else:
            return "code_generation"
