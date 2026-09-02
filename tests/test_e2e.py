#!/usr/bin/env python3
"""E2E 链路测试：task → assess → select → decompose → execute → assemble"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router.complexity import ComplexityAssessor, ComplexityLevel
from router.model_selector import ModelSelector, ModelTier
from decomposer.dag_builder import DAGBuilder, TaskStatus, DAG
from decomposer.dependency import DependencyAnalyzer
from executor.staged_executor import StagedExecutor
from executor.assembler import Assembler


def test_e2e_full_pipeline(tmp_path):
    task = "实现用户登录功能"

    assessor = ComplexityAssessor()
    complexity = assessor.assess(task)
    assert complexity.level in (ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH)

    selector = ModelSelector()
    selection = selector.select(complexity.level, task_type="code_generation")
    assert selection.model is not None
    assert selection.tier in (ModelTier.A, ModelTier.MID, ModelTier.EXEC)

    builder = DAGBuilder()
    dag = builder.build(task)
    assert len(dag.nodes) > 0

    analyzer = DependencyAnalyzer()
    analysis = analyzer.analyze(dag)
    assert not analysis.has_cycle

    dag_path = tmp_path / "dag.json"
    dag.save(dag_path)
    loaded = DAG.load(dag_path)
    assert len(loaded.nodes) == len(dag.nodes)

    executor = StagedExecutor()
    result = executor.execute(loaded)
    assert result.status == TaskStatus.COMPLETED

    assembler = Assembler()
    assembly = assembler.assemble(loaded)
    assert assembly.success is True
    assert assembly.total_cost >= 0


def test_e2e_low_complexity(tmp_path):
    task = "求和列表"

    assessor = ComplexityAssessor()
    complexity = assessor.assess(task)
    assert complexity.level == ComplexityLevel.LOW

    selector = ModelSelector()
    selection = selector.select(complexity.level)
    assert selection.tier == ModelTier.EXEC

    builder = DAGBuilder()
    dag = builder.build(task)
    executor = StagedExecutor()
    result = executor.execute(dag)
    assert result.status == TaskStatus.COMPLETED


def test_e2e_high_complexity(tmp_path):
    task = "设计微服务架构并实现服务注册发现"

    assessor = ComplexityAssessor()
    complexity = assessor.assess(task)
    assert complexity.level == ComplexityLevel.HIGH

    selector = ModelSelector()
    selection = selector.select(complexity.level, task_type="code_generation")
    assert selection.tier == ModelTier.A

    builder = DAGBuilder()
    dag = builder.build(task, context={"complexity": "high"})
    assert len(dag.nodes) >= 6

    executor = StagedExecutor()
    result = executor.execute(dag)
    assert result.status == TaskStatus.COMPLETED

    assembler = Assembler()
    assembly = assembler.assemble(dag)
    assert assembly.success is True


def test_e2e_empty_task():
    assessor = ComplexityAssessor()
    result = assessor.assess("")
    assert result.level in (ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH)


def test_e2e_cost_tracking():
    from router.cost_optimizer import CostOptimizer, BudgetConfig

    optimizer = CostOptimizer(budget=BudgetConfig(daily_limit=100.0, monthly_limit=2000.0))

    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    result = executor.execute(dag)
    assert result.status == TaskStatus.COMPLETED

    report = optimizer.get_daily_report()
    assert report.budget_utilization >= 0
    assert report.is_over_budget is False
