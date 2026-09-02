#!/usr/bin/env python3
"""IT-01 核心路由引擎测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router.complexity import ComplexityAssessor, ComplexityLevel
from router.model_selector import ModelSelector, ModelTier
from router.cost_optimizer import CostOptimizer, BudgetConfig
from decomposer.dag_builder import DAGBuilder, TaskNode, TaskStatus, DAG
from decomposer.task_splitter import TaskSplitter, SplitStrategy
from decomposer.dependency import DependencyAnalyzer
from executor.staged_executor import StagedExecutor, ExecutionResult
from executor.assembler import Assembler, AssemblyResult
from executor.parallel_worker import ParallelWorker, WorkerConfig
from models.registry import ModelRegistry
from router.model_selector import ModelProfile


def test_complexity_assessor():
    assessor = ComplexityAssessor()
    result = assessor.assess("实现用户登录功能")
    assert result.level in (ComplexityLevel.HIGH, ComplexityLevel.MEDIUM)
    assert 0 <= result.score <= 1
    assert 0 <= result.confidence <= 1


def test_model_selector():
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.HIGH, task_type="code_generation")
    assert selection.tier == ModelTier.A
    assert selection.estimated_cost > 0


def test_dag_builder():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    assert len(dag.nodes) > 0
    assert len(dag.critical_path) > 0


def test_dependency_analyzer():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    analyzer = DependencyAnalyzer()
    analysis = analyzer.analyze(dag)
    assert not analysis.has_cycle
    assert analysis.parallel_width > 0


def test_staged_executor():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    result = executor.execute(dag)
    assert result.status == TaskStatus.COMPLETED
    assert result.cost >= 0


def test_assembler():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    executor.execute(dag)
    assembler = Assembler()
    result = assembler.assemble(dag)
    assert result.success is True
    assert result.total_cost >= 0


def test_model_registry():
    registry = ModelRegistry()
    models_list = registry.list_all()
    assert len(models_list) >= 6
    tier_a = registry.list_by_tier("tier-a")
    assert len(tier_a) >= 2


def test_cost_optimizer():
    optimizer = CostOptimizer(budget=BudgetConfig(daily_limit=10.0, monthly_limit=200.0))
    optimizer.record_cost(
        model_name="Claude Sonnet",
        tier=ModelTier.MID,
        input_tokens=1000,
        output_tokens=500,
        cost=0.003,
        task_type="code_generation",
    )
    report = optimizer.get_daily_report()
    assert report.total_cost > 0


def test_task_splitter():
    splitter = TaskSplitter()
    subtasks = splitter.split("实现用户登录功能")
    assert len(subtasks) > 0


def test_dag_save_load_roundtrip(tmp_path):
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    path = tmp_path / "dag.json"
    dag.save(path)
    loaded = DAG.load(path)
    assert len(loaded.nodes) == len(dag.nodes)
    for nid in dag.nodes:
        assert nid in loaded.nodes


if __name__ == "__main__":
    test_complexity_assessor()
    test_model_selector()
    test_dag_builder()
    test_dependency_analyzer()
    test_staged_executor()
    test_assembler()
    test_model_registry()
    test_cost_optimizer()
    test_task_splitter()
    print("\n=== 所有测试通过 ===")
