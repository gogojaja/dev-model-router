#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型选择器模块

根据任务复杂度选择最优模型 tier：
- Tier-A（高阶推理）：复杂推理、架构设计、调试
- Tier-Mid（中阶执行）：代码生成、单元测试、文档
- Tier-Exec（低阶执行）：格式转换、批量处理、简单任务
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from .complexity import ComplexityLevel


class ModelTier(Enum):
    """模型 tier 等级"""
    A = "tier-a"        # 高阶推理模型（Claude Opus, GPT-4.1, Gemini 2.5 Pro）
    MID = "tier-mid"    # 中阶执行模型（Claude Sonnet, GPT-4.1-mini, Gemini 2.5 Flash）
    EXEC = "tier-exec"  # 低阶执行模型（Claude Haiku, GPT-4.1-nano, Gemini 2.0 Flash）


@dataclass
class ModelProfile:
    """模型档案"""
    name: str
    tier: ModelTier
    provider: str  # "anthropic" | "openai" | "google" | "deepseek"
    model_id: str  # API 模型 ID
    cost_per_1k_input: float  # 每 1K token 输入成本（美元）
    cost_per_1k_output: float  # 每 1K token 输出成本（美元）
    max_tokens: int  # 最大输出 token 数
    pass_at_1: float  # pass@1 准确率（0.0 ~ 1.0）
    fix_at_1: float  # fix@1 修复率（0.0 ~ 1.0）
    strengths: List[str] = field(default_factory=list)  # 优势领域


@dataclass
class ModelSelection:
    """模型选择结果"""
    tier: ModelTier
    model: ModelProfile
    reason: str
    estimated_cost: float  # 预估成本（美元）


class ModelSelector:
    """
    模型选择器

    Usage:
        selector = ModelSelector()
        selection = selector.select(ComplexityLevel.HIGH, task_type="code_generation")
        print(selection.model.name)  # "Claude Opus"
    """

    def __init__(self, profiles: Optional[Dict[ModelTier, List[ModelProfile]]] = None):
        """
        初始化模型选择器

        Args:
            profiles: 自定义模型档案库（可选，默认从 ModelRegistry 加载）
        """
        if profiles is not None:
            self.profiles = profiles
        else:
            from models.registry import ModelRegistry
            registry = ModelRegistry()
            self.profiles = registry.to_profiles_by_tier()

    def select(
        self,
        complexity: ComplexityLevel,
        task_type: str = "general",
        budget: Optional[float] = None,
        prefer_provider: Optional[str] = None,
    ) -> ModelSelection:
        """
        根据任务复杂度选择最优模型

        Args:
            complexity: 任务复杂度
            task_type: 任务类型 ("code_generation" | "testing" | "documentation" | "general")
            budget: 预算上限（美元，可选）
            prefer_provider: 偏好供应商（可选）

        Returns:
            ModelSelection: 选择结果
        """
        # 根据复杂度选择 tier
        tier = self._complexity_to_tier(complexity)

        # 获取该 tier 的模型列表
        candidates = self.profiles.get(tier, [])
        if not candidates:
            raise ValueError(f"No models available for tier {tier}")

        # 过滤偏好供应商
        if prefer_provider:
            filtered = [m for m in candidates if m.provider == prefer_provider]
            if filtered:
                candidates = filtered

        # 过滤预算
        if budget is not None:
            filtered = [m for m in candidates if m.cost_per_1k_input <= budget]
            if filtered:
                candidates = filtered

        # 按 pass@1 排序，选择最优
        candidates.sort(key=lambda m: m.pass_at_1, reverse=True)
        best = candidates[0]

        # 计算预估成本（假设平均 1K 输入 + 0.5K 输出）
        estimated_cost = best.cost_per_1k_input * 1 + best.cost_per_1k_output * 0.5

        reason = f"complexity={complexity.value}, tier={tier.value}, pass@1={best.pass_at_1:.2f}"

        return ModelSelection(
            tier=tier,
            model=best,
            reason=reason,
            estimated_cost=estimated_cost,
        )

    def _complexity_to_tier(self, complexity: ComplexityLevel) -> ModelTier:
        """复杂度→tier 映射"""
        mapping = {
            ComplexityLevel.HIGH: ModelTier.A,
            ComplexityLevel.MEDIUM: ModelTier.MID,
            ComplexityLevel.LOW: ModelTier.EXEC,
        }
        return mapping[complexity]

    def get_staged_selections(
        self, task_type: str = "code_generation"
    ) -> Dict[str, ModelSelection]:
        """
        获取分阶段模型选择（用于 Stagewise Cascade）

        Args:
            task_type: 任务类型

        Returns:
            各阶段的模型选择
        """
        return {
            "planning": self.select(ComplexityLevel.HIGH, task_type),
            "generation": self.select(ComplexityLevel.MEDIUM, task_type),
            "review": self.select(ComplexityLevel.HIGH, task_type),
            "fix": self.select(ComplexityLevel.MEDIUM, task_type),
            "refine": self.select(ComplexityLevel.MEDIUM, task_type),
        }
