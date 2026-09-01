#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖分析模块

分析任务依赖关系，检测循环依赖，计算并行度。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List, Set, Tuple

from .dag_builder import DAG, TaskNode


@dataclass
class DependencyAnalysis:
    """依赖分析结果"""
    has_cycle: bool  # 是否存在循环依赖
    parallel_width: int  # 并行宽度（最大可并行任务数）
    critical_path_length: int  # 关键路径长度
    total_tasks: int  # 总任务数
    independent_tasks: List[str]  # 独立任务（无依赖）
    dependency_chains: List[List[str]]  # 依赖链


class DependencyAnalyzer:
    """
    依赖分析器

    Usage:
        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze(dag)
        print(analysis.parallel_width)  # 3
    """

    def analyze(self, dag: DAG) -> DependencyAnalysis:
        """
        分析 DAG 依赖关系

        Args:
            dag: 任务依赖图

        Returns:
            DependencyAnalysis: 分析结果
        """
        # 检测循环依赖
        has_cycle = self._detect_cycle(dag)

        # 计算并行宽度
        parallel_width = self._calculate_parallel_width(dag)

        # 计算关键路径长度
        critical_path_length = len(dag.critical_path)

        # 找出独立任务
        independent_tasks = [
            node_id for node_id, node in dag.nodes.items()
            if not node.dependencies
        ]

        # 提取依赖链
        dependency_chains = self._extract_chains(dag)

        return DependencyAnalysis(
            has_cycle=has_cycle,
            parallel_width=parallel_width,
            critical_path_length=critical_path_length,
            total_tasks=len(dag.nodes),
            independent_tasks=independent_tasks,
            dependency_chains=dependency_chains,
        )

    def _detect_cycle(self, dag: DAG) -> bool:
        """检测循环依赖（DFS）"""
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dep in dag.nodes[node_id].dependencies:
                if dep in dag.nodes:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in dag.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def _calculate_parallel_width(self, dag: DAG) -> int:
        """计算并行宽度（最大可并行任务数）"""
        # 使用拓扑排序计算每层可并行任务数
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for node_id, node in dag.nodes.items():
            for dep in node.dependencies:
                if dep in dag.nodes:
                    in_degree[node_id] += 1

        max_parallel = 0
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while current_level:
            max_parallel = max(max_parallel, len(current_level))
            next_level = []
            for node_id in current_level:
                for other_id, other_node in dag.nodes.items():
                    if node_id in other_node.dependencies:
                        in_degree[other_id] -= 1
                        if in_degree[other_id] == 0:
                            next_level.append(other_id)
            current_level = next_level

        return max_parallel

    def _extract_chains(self, dag: DAG) -> List[List[str]]:
        """提取依赖链"""
        chains = []
        visited = set()

        def dfs_chain(node_id: str, current_chain: List[str]):
            if node_id in visited:
                return
            visited.add(node_id)
            current_chain.append(node_id)

            # 找到所有依赖当前节点的任务
            dependents = [
                other_id for other_id, other_node in dag.nodes.items()
                if node_id in other_node.dependencies and other_id not in visited
            ]

            if not dependents:
                chains.append(current_chain.copy())
            else:
                for dep in dependents:
                    dfs_chain(dep, current_chain.copy())

        for node_id in dag.nodes:
            if node_id not in visited:
                dfs_chain(node_id, [])

        return chains

    def get_execution_order(self, dag: DAG) -> List[List[str]]:
        """
        获取执行顺序（分层，同层可并行）

        Returns:
            List[List[str]]: 每层的任务 ID 列表
        """
        in_degree = {node_id: 0 for node_id in dag.nodes}
        for node_id, node in dag.nodes.items():
            for dep in node.dependencies:
                if dep in dag.nodes:
                    in_degree[node_id] += 1

        layers = []
        current_layer = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while current_layer:
            layers.append(current_layer)
            next_layer = []
            for node_id in current_layer:
                for other_id, other_node in dag.nodes.items():
                    if node_id in other_node.dependencies:
                        in_degree[other_id] -= 1
                        if in_degree[other_id] == 0:
                            next_layer.append(other_id)
            current_layer = next_layer

        return layers
