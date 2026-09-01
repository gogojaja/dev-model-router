#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分阶段执行器模块

执行 DAG 任务，支持分阶段执行和模型选择。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime

from ..decomposer.dag_builder import DAG, TaskNode, TaskStatus
from ..router.model_selector import ModelSelector, ModelTier
from ..router.complexity import ComplexityAssessor, ComplexityLevel


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    cost: float = 0.0
    duration: float = 0.0  # 执行时间（秒）


@dataclass
class ExecutionPlan:
    """执行计划"""
    dag: DAG
    layers: List[List[str]]  # 每层的任务 ID 列表
    model_selections: Dict[str, Any]  # 每个任务的模型选择
    total_estimated_cost: float = 0.0


class StagedExecutor:
    """
    分阶段执行器

    Usage:
        executor = StagedExecutor()
        result = executor.execute(dag)
        print(result)
    """

    def __init__(
        self,
        model_selector: Optional[ModelSelector] = None,
        complexity_assessor: Optional[ComplexityAssessor] = None,
        task_executor: Optional[Callable] = None,
    ):
        """
        初始化执行器

        Args:
            model_selector: 模型选择器（可选）
            complexity_assessor: 复杂度评估器（可选）
            task_executor: 任务执行函数（可选，默认使用内置执行器）
        """
        self.model_selector = model_selector or ModelSelector()
        self.complexity_assessor = complexity_assessor or ComplexityAssessor()
        self.task_executor = task_executor or self._default_task_executor

    def execute(
        self,
        dag: DAG,
        budget: Optional[float] = None,
        parallel: bool = True,
    ) -> ExecutionResult:
        """
        执行 DAG

        Args:
            dag: 任务依赖图
            budget: 预算上限（可选）
            parallel: 是否并行执行

        Returns:
            ExecutionResult: 执行结果
        """
        # 生成执行计划
        plan = self._create_execution_plan(dag)

        # 检查预算
        if budget and plan.total_estimated_cost > budget:
            return ExecutionResult(
                task_id="root",
                status=TaskStatus.FAILED,
                error=f"预估成本 ${plan.total_estimated_cost:.2f} 超出预算 ${budget:.2f}",
            )

        # 按层执行
        for layer in plan.layers:
            if parallel:
                # 并行执行同层任务
                self._execute_layer_parallel(layer, dag, plan)
            else:
                # 顺序执行
                for task_id in layer:
                    self._execute_task(task_id, dag, plan)

            # 检查是否有失败任务
            if dag.is_failed:
                return ExecutionResult(
                    task_id="root",
                    status=TaskStatus.FAILED,
                    error=f"任务执行失败: {self._get_failed_tasks(dag)}",
                )

        # 返回最终结果
        return ExecutionResult(
            task_id="root",
            status=TaskStatus.COMPLETED if dag.is_complete else TaskStatus.FAILED,
            result={"total_cost": dag.total_cost, "tasks_completed": len(dag.nodes)},
            cost=dag.total_cost,
        )

    def _create_execution_plan(self, dag: DAG) -> ExecutionPlan:
        """创建执行计划"""
        # 使用依赖分析器获取执行顺序
        from ..decomposer.dependency import DependencyAnalyzer
        analyzer = DependencyAnalyzer()
        layers = analyzer.get_execution_order(dag)

        # 为每个任务选择模型
        model_selections = {}
        total_cost = 0.0

        for layer in layers:
            for task_id in layer:
                node = dag.nodes[task_id]
                complexity = self.complexity_assessor.assess(node.description)
                selection = self.model_selector.select(complexity.level, node.task_type)
                model_selections[task_id] = selection
                node.model_tier = selection.tier.value
                node.estimated_cost = selection.estimated_cost
                total_cost += selection.estimated_cost

        return ExecutionPlan(
            dag=dag,
            layers=layers,
            model_selections=model_selections,
            total_estimated_cost=total_cost,
        )

    def _execute_layer_parallel(
        self,
        layer: List[str],
        dag: DAG,
        plan: ExecutionPlan,
    ):
        """并行执行一层任务"""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(layer)) as executor:
            futures = {
                executor.submit(self._execute_task, task_id, dag, plan): task_id
                for task_id in layer
            }

            for future in concurrent.futures.as_completed(futures):
                task_id = futures[future]
                try:
                    future.result()
                except Exception as e:
                    dag.nodes[task_id].status = TaskStatus.FAILED
                    dag.nodes[task_id].error = str(e)

    def _execute_task(self, task_id: str, dag: DAG, plan: ExecutionPlan):
        """执行单个任务"""
        node = dag.nodes[task_id]
        node.status = TaskStatus.RUNNING

        start_time = datetime.now()

        try:
            # 调用任务执行函数
            result = self.task_executor(node, plan.model_selections[task_id])
            node.result = result
            node.status = TaskStatus.COMPLETED
        except Exception as e:
            node.error = str(e)
            node.status = TaskStatus.FAILED
        finally:
            end_time = datetime.now()
            node.actual_cost = plan.model_selections[task_id].estimated_cost

    def _default_task_executor(
        self, node: TaskNode, model_selection: Any
    ) -> Dict:
        """默认任务执行器（占位实现）"""
        # 实际使用时需要替换为真实的模型调用
        return {
            "task_id": node.id,
            "model": model_selection.model.name,
            "status": "completed",
            "output": f"Task {node.id} completed with {model_selection.model.name}",
        }

    def _get_failed_tasks(self, dag: DAG) -> List[str]:
        """获取失败任务列表"""
        return [
            node_id for node_id, node in dag.nodes.items()
            if node.status == TaskStatus.FAILED
        ]
