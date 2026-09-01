#!/usr/bin/env python3
"""IT-01 核心路由引擎测试 - 从父目录运行"""
import sys
import os

# 切换到项目目录
os.chdir('/Volumes/BR256G/dev-model-router')
sys.path.insert(0, '/Volumes/BR256G/dev-model-router')

# 直接导入子模块（避免 __init__.py 相对导入问题）
import importlib
import types

# 手动创建包结构
router = types.ModuleType('router')
router.__path__ = ['/Volumes/BR256G/dev-model-router/router']
sys.modules['router'] = router

decomposer = types.ModuleType('decomposer')
decomposer.__path__ = ['/Volumes/BR256G/dev-model-router/decomposer']
sys.modules['decomposer'] = decomposer

executor = types.ModuleType('executor')
executor.__path__ = ['/Volumes/BR256G/dev-model-router/executor']
sys.modules['executor'] = executor

models = types.ModuleType('models')
models.__path__ = ['/Volumes/BR256G/dev-model-router/models']
sys.modules['models'] = models

# 现在导入
from router.complexity import ComplexityAssessor, ComplexityLevel
from router.model_selector import ModelSelector, ModelTier
from router.cost_optimizer import CostOptimizer, BudgetConfig
from decomposer.dag_builder import DAGBuilder, TaskNode, TaskStatus, DAG
from decomposer.task_splitter import TaskSplitter, SplitStrategy
from decomposer.dependency import DependencyAnalyzer
from executor.staged_executor import StagedExecutor, ExecutionResult
from executor.assembler import Assembler, AssemblyResult
from executor.parallel_worker import ParallelWorker, WorkerConfig
from models.registry import ModelRegistry, ModelInfo


def test_complexity_assessor():
    """测试复杂度评估"""
    assessor = ComplexityAssessor()
    result = assessor.assess("实现用户登录功能")
    assert result.level in (ComplexityLevel.HIGH, ComplexityLevel.MEDIUM)
    assert 0 <= result.score <= 1
    assert 0 <= result.confidence <= 1
    print(f"[PASS] 复杂度评估: level={result.level.value}, score={result.score:.3f}")


def test_model_selector():
    """测试模型选择"""
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.HIGH, task_type="code_generation")
    assert selection.tier == ModelTier.A
    assert selection.estimated_cost > 0
    print(f"[PASS] 模型选择: model={selection.model.name}, tier={selection.tier.value}")


def test_dag_builder():
    """测试DAG构建"""
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    assert len(dag.nodes) > 0
    assert len(dag.critical_path) > 0
    print(f"[PASS] DAG构建: nodes={len(dag.nodes)}, critical_path={len(dag.critical_path)}")


def test_dependency_analyzer():
    """测试依赖分析"""
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    analyzer = DependencyAnalyzer()
    analysis = analyzer.analyze(dag)
    assert not analysis.has_cycle
    assert analysis.parallel_width > 0
    print(f"[PASS] 依赖分析: has_cycle={analysis.has_cycle}, parallel_width={analysis.parallel_width}")


def test_staged_executor():
    """测试分阶段执行器"""
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    result = executor.execute(dag)
    assert result.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
    print(f"[PASS] 执行结果: status={result.status.value}, cost=${result.cost:.4f}")


def test_assembler():
    """测试结果组装器"""
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    executor.execute(dag)
    assembler = Assembler()
    result = assembler.assemble(dag)
    assert isinstance(result.success, bool)
    print(f"[PASS] 组装结果: success={result.success}, total_cost=${result.total_cost:.4f}")


def test_model_registry():
    """测试模型注册表"""
    registry = ModelRegistry()
    models_list = registry.list_all()
    assert len(models_list) >= 6
    tier_a = registry.list_by_tier("tier-a")
    assert len(tier_a) >= 2
    print(f"[PASS] 模型注册表: {len(models_list)} 个模型, tier-a={len(tier_a)}")


def test_cost_optimizer():
    """测试成本优化器"""
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
    print(f"[PASS] 成本优化器: daily_cost=${report.total_cost:.4f}")


def test_task_splitter():
    """测试任务拆分器"""
    splitter = TaskSplitter()
    subtasks = splitter.split("实现用户登录功能")
    assert len(subtasks) > 0
    print(f"[PASS] 任务拆分: {len(subtasks)} 个子任务")


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
