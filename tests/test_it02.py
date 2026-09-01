#!/usr/bin/env python3
"""IT-02 增强功能测试"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router.complexity import ComplexityAssessor, ComplexityLevel
from router.model_selector import ModelSelector, ModelTier
from router.cost_optimizer import CostOptimizer, BudgetConfig
from router.cache import ResultCache
from decomposer.dag_builder import DAGBuilder, TaskStatus
from decomposer.task_splitter import TaskSplitter, SplitStrategy
from decomposer.dependency import DependencyAnalyzer
from executor.staged_executor import StagedExecutor
from executor.assembler import Assembler
from executor.parallel_worker import ParallelWorker, WorkerConfig


def test_smart_split_high():
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("实现用户登录功能", complexity="high")
    assert len(subtasks) >= 8


def test_smart_split_low():
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("求和列表", complexity="low")
    assert len(subtasks) <= 4


def test_cost_prediction():
    optimizer = CostOptimizer()
    prediction = optimizer.predict_cost(task_count=6)
    assert len(prediction.get("predictions_by_tier", {})) == 3
    assert prediction["task_count"] == 6
    assert prediction["estimated_total"] > 0


def test_cache_set_get():
    cache = ResultCache()
    key = cache.make_key("test task", task_type="code_generation")
    cache.set(key, {"result": "test"})
    cached = cache.get(key)
    assert cached is not None
    assert cached == {"result": "test"}


def test_cache_expiry():
    cache = ResultCache(ttl=0.01)
    cache.set("key1", "value1", ttl=0.01)
    time.sleep(0.02)
    cached = cache.get("key1")
    assert cached is None


def test_cache_hit_rate():
    cache = ResultCache()
    cache.set("key1", "value1")
    cache.get("key1")
    cache.get("key2")
    cache.get("key3")
    assert cache.hit_rate > 0


def test_custom_stages():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    stages = [
        {"name": "planning", "tasks": ["plan"]},
        {"name": "design", "tasks": ["design"]},
        {"name": "implement", "tasks": ["implement"]},
        {"name": "test", "tasks": ["test"]},
    ]
    result = executor.execute_with_stages(dag, stages)
    assert result.status == TaskStatus.COMPLETED


def test_parallel_with_cache():
    from decomposer.dag_builder import TaskNode
    cache = ResultCache()
    worker = ParallelWorker(config=WorkerConfig(max_workers=2))
    tasks = [
        TaskNode(id="t1", name="task1", description="test task 1", task_type="code_generation", dependencies=[]),
        TaskNode(id="t2", name="task2", description="test task 2", task_type="code_generation", dependencies=[]),
    ]
    results = worker.execute_with_cache(tasks, cache=cache)
    assert len(results) == 2
    assert all(r.status == TaskStatus.COMPLETED for r in results)


def test_budget_alert():
    optimizer = CostOptimizer(budget=BudgetConfig(daily_limit=0.001, monthly_limit=0.001))
    optimizer.record_cost(
        model_name="Claude Opus",
        tier=ModelTier.A,
        input_tokens=1000,
        output_tokens=500,
        cost=0.010,
        task_type="code_generation",
    )
    report = optimizer.get_daily_report()
    assert report.is_over_budget is True


def test_split_strategy():
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("实现用户登录功能", strategy=SplitStrategy.PARALLEL)
    assert len(subtasks) > 0


if __name__ == "__main__":
    test_smart_split_high()
    test_smart_split_low()
    test_cost_prediction()
    test_cache_set_get()
    test_cache_expiry()
    test_cache_hit_rate()
    test_custom_stages()
    test_parallel_with_cache()
    test_budget_alert()
    test_split_strategy()
    print("\n=== IT-02 所有测试通过 ===")
