#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果组装器模块

将多个子任务的执行结果组装为最终结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from ..decomposer.dag_builder import DAG, TaskNode, TaskStatus


@dataclass
class AssemblyResult:
    """组装结果"""
    success: bool
    final_output: Dict[str, Any]  # 最终输出
    assembled_from: List[str]  # 来源任务 ID
    total_cost: float = 0.0
    errors: List[str] = field(default_factory=list)


class Assembler:
    """
    结果组装器

    Usage:
        assembler = Assembler()
        result = assembler.assemble(dag)
        print(result.final_output)
    """

    def assemble(
        self,
        dag: DAG,
        output_format: str = "dict",
    ) -> AssemblyResult:
        """
        组装 DAG 执行结果

        Args:
            dag: 已执行完成的 DAG
            output_format: 输出格式 ("dict" | "json" | "text")

        Returns:
            AssemblyResult: 组装结果
        """
        # 收集所有已完成任务的结果
        completed_tasks = []
        errors = []

        for node_id, node in dag.nodes.items():
            if node.status == TaskStatus.COMPLETED:
                completed_tasks.append(node)
            elif node.status == TaskStatus.FAILED:
                errors.append(f"任务 {node_id} 失败: {node.error}")

        # 组装结果
        final_output = self._merge_results(completed_tasks, output_format)

        return AssemblyResult(
            success=dag.is_complete and not errors,
            final_output=final_output,
            assembled_from=[node.id for node in completed_tasks],
            total_cost=dag.total_cost,
            errors=errors,
        )

    def _merge_results(
        self,
        tasks: List[TaskNode],
        output_format: str,
    ) -> Dict[str, Any]:
        """合并任务结果"""
        merged = {
            "tasks": {},
            "summary": {
                "total_tasks": len(tasks),
                "completed_tasks": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "failed_tasks": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            },
        }

        for task in tasks:
            merged["tasks"][task.id] = {
                "name": task.name,
                "description": task.description,
                "task_type": task.task_type,
                "status": task.status.value,
                "result": task.result,
                "model_used": task.model_tier,
                "cost": task.actual_cost,
            }

        # 添加汇总信息
        merged["summary"]["total_cost"] = sum(t.actual_cost for t in tasks)
        merged["summary"]["models_used"] = list(set(
            t.model_tier for t in tasks if t.model_tier
        ))

        return merged

    def assemble_to_text(self, dag: DAG) -> str:
        """
        将结果组装为可读文本

        Args:
            dag: 已执行完成的 DAG

        Returns:
            str: 可读文本结果
        """
        result = self.assemble(dag, output_format="dict")

        lines = [
            "# 任务执行报告",
            "",
            f"## 总结",
            f"- 总任务数: {result.final_output['summary']['total_tasks']}",
            f"- 完成任务数: {result.final_output['summary']['completed_tasks']}",
            f"- 失败任务数: {result.final_output['summary']['failed_tasks']}",
            f"- 总成本: ${result.final_output['summary']['total_cost']:.4f}",
            f"- 使用模型: {', '.join(result.final_output['summary']['models_used'])}",
            "",
            "## 任务详情",
        ]

        for task_id, task_info in result.final_output["tasks"].items():
            lines.extend([
                f"### {task_info['name']} ({task_id})",
                f"- 类型: {task_info['task_type']}",
                f"- 状态: {task_info['status']}",
                f"- 模型: {task_info['model_used']}",
                f"- 成本: ${task_info['cost']:.4f}",
                f"- 结果: {task_info['result']}",
                "",
            ])

        if result.errors:
            lines.extend([
                "## 错误",
                *[f"- {error}" for error in result.errors],
            ])

        return "\n".join(lines)
