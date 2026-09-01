#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dev-model-router CLI 入口

Usage:
    python -m router assess "任务描述"
    python -m router decompose "任务描述" --output tasks.json
    python -m router execute tasks.json
    python -m router assemble results/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from router import ComplexityAssessor, ComplexityLevel, ModelSelector, ModelTier
from decomposer import DAGBuilder, TaskSplitter, DependencyAnalyzer
from decomposer.dag_builder import DAG
from executor import StagedExecutor, Assembler
from models import ModelRegistry


def cmd_assess(args):
    """评估任务复杂度"""
    assessor = ComplexityAssessor(mode=args.mode)
    result = assessor.assess(args.task)

    print(f"任务: {args.task}")
    print(f"复杂度: {result.level.value}")
    print(f"分数: {result.score:.3f}")
    print(f"置信度: {result.confidence:.3f}")
    print(f"方法: {result.method}")
    print(f"理由: {result.reasoning}")

    if args.json:
        print(json.dumps({
            "level": result.level.value,
            "score": result.score,
            "confidence": result.confidence,
            "method": result.method,
            "reasoning": result.reasoning,
        }, indent=2, ensure_ascii=False))


def cmd_select(args):
    """选择模型"""
    assessor = ComplexityAssessor()
    selector = ModelSelector()

    complexity = assessor.assess(args.task).level
    selection = selector.select(
        complexity,
        task_type=args.task_type,
        budget=args.budget,
    )

    print(f"任务: {args.task}")
    print(f"复杂度: {complexity.value}")
    print(f"选择模型: {selection.model.name}")
    print(f"Tier: {selection.tier.value}")
    print(f"理由: {selection.reason}")
    print(f"预估成本: ${selection.estimated_cost:.4f}")

    if args.json:
        print(json.dumps({
            "complexity": complexity.value,
            "model": selection.model.name,
            "tier": selection.tier.value,
            "reason": selection.reason,
            "estimated_cost": selection.estimated_cost,
        }, indent=2, ensure_ascii=False))


def cmd_decompose(args):
    """分解任务为 DAG"""
    builder = DAGBuilder()
    dag = builder.build(args.task)

    # 保存到文件
    output_path = Path(args.output)
    dag.save(output_path)

    print(f"任务: {args.task}")
    print(f"生成 DAG: {output_path}")
    print(f"任务数: {len(dag.nodes)}")
    print(f"关键路径: {len(dag.critical_path)} 步")

    # 分析依赖
    analyzer = DependencyAnalyzer()
    analysis = analyzer.analyze(dag)
    print(f"并行宽度: {analysis.parallel_width}")
    print(f"是否有循环依赖: {analysis.has_cycle}")

    if args.json:
        print(json.dumps(dag.to_dict(), indent=2, ensure_ascii=False))


def cmd_execute(args):
    """执行 DAG"""
    # 加载 DAG
    dag_path = Path(args.dag)
    dag = DAG.load(dag_path)

    print(f"加载 DAG: {dag_path}")
    print(f"任务数: {len(dag.nodes)}")

    # 执行
    executor = StagedExecutor()
    result = executor.execute(dag, budget=args.budget, parallel=args.parallel)

    print(f"执行结果: {result.status.value}")
    print(f"总成本: ${result.cost:.4f}")

    if result.error:
        print(f"错误: {result.error}")

    if args.json:
        print(json.dumps({
            "status": result.status.value,
            "cost": result.cost,
            "error": result.error,
        }, indent=2, ensure_ascii=False))


def cmd_assemble(args):
    """组装结果"""
    # 加载 DAG
    dag_path = Path(args.dag)
    dag = DAG.load(dag_path)

    # 组装
    assembler = Assembler()
    result = assembler.assemble(dag)

    print(f"组装成功: {result.success}")
    print(f"总成本: ${result.total_cost:.4f}")
    print(f"来源任务: {', '.join(result.assembled_from)}")

    if result.errors:
        print(f"错误: {result.errors}")

    # 输出到文件
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.final_output, f, indent=2, ensure_ascii=False)
        print(f"结果已保存: {output_path}")

    if args.text:
        text_result = assembler.assemble_to_text(dag)
        print(text_result)


def cmd_models(args):
    """列出模型"""
    registry = ModelRegistry()

    if args.tier:
        models = registry.list_by_tier(args.tier)
    elif args.provider:
        models = registry.list_by_provider(args.provider)
    else:
        models = registry.list_all()

    for model in models:
        print(f"{model.name} ({model.tier})")
        print(f"  供应商: {model.provider}")
        print(f"  模型 ID: {model.model_id}")
        print(f"  成本: ${model.cost_per_1k_input:.4f}/1K输入, ${model.cost_per_1k_output:.4f}/1K输出")
        print(f"  pass@1: {model.pass_at_1:.2f}, fix@1: {model.fix_at_1:.2f}")
        print(f"  优势: {', '.join(model.strengths)}")
        print()


def cmd_cost(args):
    """查看成本报告"""
    from router.cost_optimizer import CostOptimizer

    optimizer = CostOptimizer()
    report = optimizer.get_daily_report()

    print("# 成本报告")
    print(f"## 今日")
    print(f"- 总成本: ${report.total_cost:.4f}")
    print(f"- 预算使用率: {report.budget_utilization:.1%}")
    print(f"- 是否超支: {'是' if report.is_over_budget else '否'}")

    if report.by_tier:
        print(f"\n## 按 Tier")
        for tier, cost in report.by_tier.items():
            print(f"- {tier}: ${cost:.4f}")

    if report.by_model:
        print(f"\n## 按模型")
        for model, cost in report.by_model.items():
            print(f"- {model}: ${cost:.4f}")

    if args.json:
        print(json.dumps({
            "total_cost": report.total_cost,
            "budget_utilization": report.budget_utilization,
            "is_over_budget": report.is_over_budget,
            "by_tier": report.by_tier,
            "by_model": report.by_model,
        }, indent=2, ensure_ascii=False))


def cmd_config(args):
    """管理配置"""
    import os

    config = {
        "daily_budget": os.environ.get("DAILY_BUDGET", "10.0"),
        "monthly_budget": os.environ.get("MONTHLY_BUDGET", "200.0"),
        "default_mode": os.environ.get("DEFAULT_MODE", "keyword"),
        "cache_ttl": os.environ.get("CACHE_TTL", "3600"),
        "max_cache_size": os.environ.get("MAX_CACHE_SIZE", "1000"),
    }

    if args.action == "list":
        print("# 配置列表")
        for key, value in config.items():
            print(f"{key} = {value}")
    elif args.action == "get":
        if args.key in config:
            print(f"{args.key} = {config[args.key]}")
        else:
            print(f"未知配置项: {args.key}")
    elif args.action == "set":
        print(f"设置 {args.key} = {args.value}")
        print("提示: 实际设置请通过环境变量或 .env 文件")


def main():
    parser = argparse.ArgumentParser(
        description="dev-model-router: 多模型分层编排工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # assess 命令
    assess_parser = subparsers.add_parser("assess", help="评估任务复杂度")
    assess_parser.add_argument("task", help="任务描述")
    assess_parser.add_argument("--mode", choices=["keyword", "classifier", "hybrid"], default="keyword")
    assess_parser.add_argument("--json", action="store_true")
    assess_parser.set_defaults(func=cmd_assess)

    # select 命令
    select_parser = subparsers.add_parser("select", help="选择模型")
    select_parser.add_argument("task", help="任务描述")
    select_parser.add_argument("--task-type", default="general")
    select_parser.add_argument("--budget", type=float)
    select_parser.add_argument("--json", action="store_true")
    select_parser.set_defaults(func=cmd_select)

    # decompose 命令
    decompose_parser = subparsers.add_parser("decompose", help="分解任务为 DAG")
    decompose_parser.add_argument("task", help="任务描述")
    decompose_parser.add_argument("--output", default="tasks.json")
    decompose_parser.add_argument("--json", action="store_true")
    decompose_parser.set_defaults(func=cmd_decompose)

    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="执行 DAG")
    execute_parser.add_argument("dag", help="DAG 文件路径")
    execute_parser.add_argument("--budget", type=float)
    execute_parser.add_argument("--parallel", action="store_true", default=True)
    execute_parser.add_argument("--json", action="store_true")
    execute_parser.set_defaults(func=cmd_execute)

    # assemble 命令
    assemble_parser = subparsers.add_parser("assemble", help="组装结果")
    assemble_parser.add_argument("dag", help="DAG 文件路径")
    assemble_parser.add_argument("--output", help="输出文件路径")
    assemble_parser.add_argument("--text", action="store_true")
    assemble_parser.set_defaults(func=cmd_assemble)

    # models 命令
    models_parser = subparsers.add_parser("models", help="列出模型")
    models_parser.add_argument("--tier", choices=["tier-a", "tier-mid", "tier-exec"])
    models_parser.add_argument("--provider", choices=["anthropic", "openai", "google", "deepseek"])
    models_parser.set_defaults(func=cmd_models)

    # cost 命令
    cost_parser = subparsers.add_parser("cost", help="查看成本报告")
    cost_parser.add_argument("--json", action="store_true")
    cost_parser.set_defaults(func=cmd_cost)

    # config 命令
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_parser.add_argument("action", choices=["list", "get", "set"], help="操作类型")
    config_parser.add_argument("--key", help="配置键")
    config_parser.add_argument("--value", help="配置值")
    config_parser.set_defaults(func=cmd_config)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
