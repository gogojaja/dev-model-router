#!/usr/bin/env python3
"""IT-02 增强功能测试"""
import sys
import os

sys.path.insert(0, '/Volumes/BR256G/dev-model-router')

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

results = []


def record(case_id, desc, expected, actual, passed):
    status = "PASS" if passed else "FAIL"
    results.append({"case_id": case_id, "desc": desc, "expected": expected, "actual": actual, "status": status})
    print(f"[{status}] {case_id}: {desc}")


def test_smart_split_high():
    """智能拆分-高复杂度"""
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("实现用户登录功能", complexity="high")
    record("TC-IT2-001", "智能拆分-高复杂度", "len>=8", f"len={len(subtasks)}", len(subtasks) >= 8)


def test_smart_split_low():
    """智能拆分-低复杂度"""
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("求和列表", complexity="low")
    record("TC-IT2-002", "智能拆分-低复杂度", "len<=4", f"len={len(subtasks)}", len(subtasks) <= 4)


def test_cost_prediction():
    """成本预测"""
    optimizer = CostOptimizer()
    prediction = optimizer.predict_cost(task_count=6)
    has_predictions = len(prediction.get("predictions_by_tier", {})) == 3
    record("TC-IT2-003", "成本预测", "3 tiers", f"tiers={len(prediction.get('predictions_by_tier', {}))}", has_predictions)


def test_cache_set_get():
    """缓存设置和获取"""
    cache = ResultCache()
    key = cache.make_key("test task", task_type="code_generation")
    cache.set(key, {"result": "test"})
    cached = cache.get(key)
    record("TC-IT2-004", "缓存设置和获取", "cached=True", f"cached={cached is not None}", cached is not None)


def test_cache_expiry():
    """缓存过期"""
    cache = ResultCache(ttl=0.01)
    cache.set("key1", "value1", ttl=0.01)
    import time
    time.sleep(0.02)
    cached = cache.get("key1")
    record("TC-IT2-005", "缓存过期", "expired=None", f"cached={cached}", cached is None)


def test_cache_hit_rate():
    """缓存命中率"""
    cache = ResultCache()
    cache.set("key1", "value1")
    cache.get("key1")
    cache.get("key2")
    cache.get("key3")
    record("TC-IT2-006", "缓存命中率", "hit_rate>0", f"hit_rate={cache.hit_rate:.2f}", cache.hit_rate > 0)


def test_custom_stages():
    """自定义阶段执行"""
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
    record("TC-IT2-007", "自定义阶段执行", "completed", f"status={result.status.value}", result.status == TaskStatus.COMPLETED)


def test_parallel_with_cache():
    """带缓存的并行执行"""
    from decomposer.dag_builder import TaskNode
    cache = ResultCache()
    worker = ParallelWorker(config=WorkerConfig(max_workers=2))
    tasks = [
        TaskNode(id="t1", name="task1", description="test task 1", task_type="code_generation", dependencies=[]),
        TaskNode(id="t2", name="task2", description="test task 2", task_type="code_generation", dependencies=[]),
    ]
    results_list = worker.execute_with_cache(tasks, cache=cache)
    record("TC-IT2-008", "带缓存的并行执行", "len=2", f"len={len(results_list)}", len(results_list) == 2)


def test_budget_alert():
    """预算告警"""
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
    record("TC-IT2-009", "预算告警", "is_over_budget=True", f"is_over_budget={report.is_over_budget}", report.is_over_budget)


def test_split_strategy():
    """拆分策略"""
    splitter = TaskSplitter()
    subtasks = splitter.split_smart("实现用户登录功能", strategy=SplitStrategy.PARALLEL)
    record("TC-IT2-010", "拆分策略", "len>0", f"len={len(subtasks)}", len(subtasks) > 0)


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

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n=== IT-02 测试结果: {passed} PASS, {failed} FAIL, {passed + failed} TOTAL ===")
