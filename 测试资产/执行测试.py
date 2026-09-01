#!/usr/bin/env python3
"""IT-01 测试执行脚本"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router.complexity import ComplexityAssessor, ComplexityLevel
from router.model_selector import ModelSelector, ModelTier
from router.cost_optimizer import CostOptimizer, BudgetConfig
from decomposer.dag_builder import DAGBuilder, TaskStatus
from decomposer.dependency import DependencyAnalyzer
from executor.staged_executor import StagedExecutor
from executor.assembler import Assembler
from models.registry import ModelRegistry

results = []


def record(case_id, desc, expected, actual, passed):
    status = "PASS" if passed else "FAIL"
    results.append({"case_id": case_id, "desc": desc, "expected": expected, "actual": actual, "status": status})
    print(f"[{status}] {case_id}: {desc}")
    assert passed, f"{case_id}: {desc} — expected {expected}, got {actual}"


def test_case_001():
    assessor = ComplexityAssessor()
    result = assessor.assess("求和列表")
    record("TC-001", "简单任务复杂度评估", "level=low", f"level={result.level.value}", result.level == ComplexityLevel.LOW)


def test_case_002():
    assessor = ComplexityAssessor()
    result = assessor.assess("实现用户登录功能")
    record("TC-002", "中等任务复杂度评估", "level=medium", f"level={result.level.value}", result.level == ComplexityLevel.MEDIUM)


def test_case_003():
    assessor = ComplexityAssessor()
    result = assessor.assess("设计微服务架构")
    record("TC-003", "复杂任务复杂度评估", "level=high", f"level={result.level.value}", result.level == ComplexityLevel.HIGH)


def test_case_004():
    assessor = ComplexityAssessor()
    try:
        result = assessor.assess("")
        record("TC-004", "空任务描述", "不崩溃", f"level={result.level.value}", True)
    except Exception as e:
        record("TC-004", "空任务描述", "不崩溃", f"异常: {e}", False)


def test_case_005():
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.HIGH, task_type="code_generation")
    record("TC-005", "高复杂度模型选择", "tier=tier-a", f"tier={selection.tier.value}", selection.tier == ModelTier.A)


def test_case_006():
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.MEDIUM, task_type="code_generation")
    record("TC-006", "中复杂度模型选择", "tier=tier-mid", f"tier={selection.tier.value}", selection.tier == ModelTier.MID)


def test_case_007():
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.LOW, task_type="code_generation")
    record("TC-007", "低复杂度模型选择", "tier=tier-exec", f"tier={selection.tier.value}", selection.tier == ModelTier.EXEC)


def test_case_008():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    record("TC-008", "DAG构建", "nodes>0", f"nodes={len(dag.nodes)}", len(dag.nodes) > 0)


def test_case_009():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    record("TC-009", "DAG关键路径", "critical_path>0", f"critical_path={len(dag.critical_path)}", len(dag.critical_path) > 0)


def test_case_010():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    result = executor.execute(dag)
    record("TC-010", "分阶段执行", "status=completed", f"status={result.status.value}", result.status == TaskStatus.COMPLETED)


def test_case_011():
    optimizer = CostOptimizer()
    optimizer.record_cost(
        model_name="Claude Sonnet",
        tier=ModelTier.MID,
        input_tokens=1000,
        output_tokens=500,
        cost=0.003,
        task_type="code_generation",
    )
    report = optimizer.get_daily_report()
    record("TC-011", "成本追踪", "cost>0", f"cost=${report.total_cost:.4f}", report.total_cost > 0)


def test_case_012():
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
    record("TC-012", "预算告警", "is_over_budget=True", f"is_over_budget={report.is_over_budget}", report.is_over_budget)


def test_case_013():
    builder = DAGBuilder()
    dag = builder.build("实现用户登录功能")
    executor = StagedExecutor()
    executor.execute(dag)
    assembler = Assembler()
    result = assembler.assemble(dag)
    record("TC-013", "结果组装", "success=true", f"success={result.success}", result.success)


def test_case_014():
    assessor = ComplexityAssessor()
    result = assessor.assess("测试任务")
    record("TC-014", "assess命令", "level有效", f"level={result.level.value}", result.level in (ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH))


def test_case_015():
    selector = ModelSelector()
    selection = selector.select(ComplexityLevel.HIGH)
    record("TC-015", "select命令", "输出模型", f"model={selection.model.name}", selection.model is not None)


def test_case_016():
    builder = DAGBuilder()
    dag = builder.build("测试任务")
    record("TC-016", "decompose命令", "输出JSON", f"nodes={len(dag.nodes)}", len(dag.nodes) > 0)


def test_case_017():
    builder = DAGBuilder()
    dag = builder.build("测试任务")
    executor = StagedExecutor()
    result = executor.execute(dag)
    record("TC-017", "execute命令", "输出结果", f"status={result.status.value}", result.status == TaskStatus.COMPLETED)


def test_case_018():
    builder = DAGBuilder()
    dag = builder.build("测试任务")
    executor = StagedExecutor()
    executor.execute(dag)
    assembler = Assembler()
    result = assembler.assemble(dag)
    record("TC-018", "assemble命令", "输出报告", f"success={result.success}", result.success)


def test_case_019():
    assessor = ComplexityAssessor()
    start = time.time()
    assessor.assess("测试任务")
    rt = time.time() - start
    record("TC-019", "评估响应时间", "RT<5s", f"RT={rt:.4f}s", rt < 5)


def test_case_020():
    registry = ModelRegistry()
    tier_a = registry.list_by_tier("tier-a")
    record("TC-020", "低成本优先", "tier-a>=2", f"tier-a={len(tier_a)}", len(tier_a) >= 2)


if __name__ == "__main__":
    test_case_001()
    test_case_002()
    test_case_003()
    test_case_004()
    test_case_005()
    test_case_006()
    test_case_007()
    test_case_008()
    test_case_009()
    test_case_010()
    test_case_011()
    test_case_012()
    test_case_013()
    test_case_014()
    test_case_015()
    test_case_016()
    test_case_017()
    test_case_018()
    test_case_019()
    test_case_020()

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n=== 测试结果: {passed} PASS, {failed} FAIL, {passed + failed} TOTAL ===")
