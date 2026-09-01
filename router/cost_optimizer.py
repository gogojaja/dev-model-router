#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本优化器模块

提供预算控制、成本追踪、成本报告等功能。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path

from .model_selector import ModelTier, ModelProfile


@dataclass
class BudgetConfig:
    """预算配置"""
    daily_limit: float  # 每日预算上限（美元）
    monthly_limit: float  # 每月预算上限（美元）
    alert_threshold: float = 0.8  # 告警阈值（80%）
    hard_limit: bool = True  # 是否强制执行预算上限


@dataclass
class CostRecord:
    """成本记录"""
    timestamp: datetime
    model_name: str
    tier: ModelTier
    input_tokens: int
    output_tokens: int
    cost: float
    task_type: str
    task_id: Optional[str] = None


@dataclass
class CostReport:
    """成本报告"""
    period: str  # "daily" | "monthly"
    start_date: datetime
    end_date: datetime
    total_cost: float
    by_tier: Dict[str, float]
    by_model: Dict[str, float]
    budget_utilization: float  # 预算使用率（0.0 ~ 1.0）
    is_over_budget: bool


class CostOptimizer:
    """
    成本优化器

    Usage:
        optimizer = CostOptimizer(budget=BudgetConfig(daily_limit=10.0, monthly_limit=200.0))
        optimizer.record_cost(model_name="Claude Opus", tier=ModelTier.A, ...)
        report = optimizer.get_daily_report()
    """

    def __init__(
        self,
        budget: Optional[BudgetConfig] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        初始化成本优化器

        Args:
            budget: 预算配置（可选）
            storage_path: 成本记录存储路径（可选）
        """
        self.budget = budget
        self.storage_path = storage_path
        self._records: List[CostRecord] = []

        if storage_path and storage_path.exists():
            self._load_records()

    def record_cost(
        self,
        model_name: str,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        task_type: str = "general",
        task_id: Optional[str] = None,
    ):
        """
        记录成本

        Args:
            model_name: 模型名称
            tier: 模型 tier
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            cost: 实际成本（美元）
            task_type: 任务类型
            task_id: 任务 ID（可选）
        """
        record = CostRecord(
            timestamp=datetime.now(),
            model_name=model_name,
            tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            task_type=task_type,
            task_id=task_id,
        )
        self._records.append(record)

        if self.storage_path:
            self._save_records()

        # 检查预算
        if self.budget:
            self._check_budget()

    def get_daily_report(self, date: Optional[datetime] = None) -> CostReport:
        """
        获取每日成本报告

        Args:
            date: 日期（默认今天）

        Returns:
            CostReport: 成本报告
        """
        if date is None:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return self._generate_report(start, end, "daily")

    def get_monthly_report(self, date: Optional[datetime] = None) -> CostReport:
        """
        获取每月成本报告

        Args:
            date: 日期（默认本月）

        Returns:
            CostReport: 成本报告
        """
        if date is None:
            date = datetime.now()

        start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)

        return self._generate_report(start, end, "monthly")

    def _generate_report(
        self, start: datetime, end: datetime, period: str
    ) -> CostReport:
        """生成成本报告"""
        records = [
            r for r in self._records
            if start <= r.timestamp < end
        ]

        total_cost = sum(r.cost for r in records)

        by_tier: Dict[str, float] = {}
        by_model: Dict[str, float] = {}
        for r in records:
            tier_key = r.tier.value
            by_tier[tier_key] = by_tier.get(tier_key, 0) + r.cost
            by_model[r.model_name] = by_model.get(r.model_name, 0) + r.cost

        # 计算预算使用率
        budget_utilization = 0.0
        is_over_budget = False
        if self.budget:
            if period == "daily":
                limit = self.budget.daily_limit
            else:
                limit = self.budget.monthly_limit
            budget_utilization = total_cost / limit if limit > 0 else 0
            is_over_budget = self.budget.hard_limit and total_cost > limit

        return CostReport(
            period=period,
            start_date=start,
            end_date=end,
            total_cost=total_cost,
            by_tier=by_tier,
            by_model=by_model,
            budget_utilization=budget_utilization,
            is_over_budget=is_over_budget,
        )

    def _check_budget(self):
        """检查预算并告警"""
        if not self.budget:
            return

        report = self.get_daily_report()
        if report.budget_utilization >= self.budget.alert_threshold:
            print(f"[warning] 每日预算使用率已达 {report.budget_utilization:.1%}")
        if report.is_over_budget:
            print(f"[error] 每日预算已超支！总成本: ${report.total_cost:.2f}")

    def _save_records(self):
        """保存成本记录到文件"""
        if not self.storage_path:
            return

        data = []
        for r in self._records:
            data.append({
                "timestamp": r.timestamp.isoformat(),
                "model_name": r.model_name,
                "tier": r.tier.value,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost": r.cost,
                "task_type": r.task_type,
                "task_id": r.task_id,
            })

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_records(self):
        """从文件加载成本记录"""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            self._records.append(CostRecord(
                timestamp=datetime.fromisoformat(item["timestamp"]),
                model_name=item["model_name"],
                tier=ModelTier(item["tier"]),
                input_tokens=item["input_tokens"],
                output_tokens=item["output_tokens"],
                cost=item["cost"],
                task_type=item["task_type"],
                task_id=item.get("task_id"),
            ))
