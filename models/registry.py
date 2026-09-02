#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型注册表模块

管理模型信息、性能档案和配置。
"""

from __future__ import annotations

import json
from typing import Optional, Dict, List
from pathlib import Path

from router.model_selector import ModelProfile, ModelTier


class ModelRegistry:
    """
    模型注册表

    Usage:
        registry = ModelRegistry()
        registry.register(ModelProfile(name="Claude Opus", ...))
        model = registry.get("Claude Opus")
    """

    def __init__(self):
        self._models: Dict[str, ModelProfile] = {}
        self._load_defaults()

    def _load_defaults(self):
        """加载默认模型"""
        defaults = [
            ModelProfile(
                name="Claude Opus",
                tier=ModelTier.A,
                provider="anthropic",
                model_id="claude-opus-4-20250514",
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                max_tokens=32000,
                pass_at_1=0.92,
                fix_at_1=0.88,
                strengths=["complex_reasoning", "architecture", "debugging", "code_generation"],
            ),
            ModelProfile(
                name="Claude Sonnet",
                tier=ModelTier.MID,
                provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                max_tokens=16000,
                pass_at_1=0.85,
                fix_at_1=0.80,
                strengths=["code_generation", "testing", "documentation"],
            ),
            ModelProfile(
                name="Claude Haiku",
                tier=ModelTier.EXEC,
                provider="anthropic",
                model_id="claude-haiku-3-5-20241022",
                cost_per_1k_input=0.0008,
                cost_per_1k_output=0.004,
                max_tokens=8000,
                pass_at_1=0.75,
                fix_at_1=0.70,
                strengths=["simple_tasks", "formatting", "batch_processing"],
            ),
            ModelProfile(
                name="GPT-4.1",
                tier=ModelTier.A,
                provider="openai",
                model_id="gpt-4.1",
                cost_per_1k_input=0.002,
                cost_per_1k_output=0.008,
                max_tokens=32000,
                pass_at_1=0.90,
                fix_at_1=0.85,
                strengths=["general", "creative", "code_generation"],
            ),
            ModelProfile(
                name="GPT-4.1-mini",
                tier=ModelTier.MID,
                provider="openai",
                model_id="gpt-4.1-mini",
                cost_per_1k_input=0.0004,
                cost_per_1k_output=0.0016,
                max_tokens=16000,
                pass_at_1=0.82,
                fix_at_1=0.78,
                strengths=["code_generation", "testing"],
            ),
            ModelProfile(
                name="GPT-4.1-nano",
                tier=ModelTier.EXEC,
                provider="openai",
                model_id="gpt-4.1-nano",
                cost_per_1k_input=0.0001,
                cost_per_1k_output=0.0004,
                max_tokens=8000,
                pass_at_1=0.70,
                fix_at_1=0.65,
                strengths=["simple_tasks", "formatting"],
            ),
        ]

        for model in defaults:
            self._models[model.name] = model

    def register(self, model: ModelProfile):
        """注册模型"""
        self._models[model.name] = model

    def get(self, name: str) -> Optional[ModelProfile]:
        """获取模型"""
        return self._models.get(name)

    def list_all(self) -> List[ModelProfile]:
        """列出所有模型"""
        return list(self._models.values())

    def list_by_tier(self, tier: str) -> List[ModelProfile]:
        """按 tier 列出模型"""
        return [m for m in self._models.values() if m.tier.value == tier]

    def list_by_provider(self, provider: str) -> List[ModelProfile]:
        """按供应商列出模型"""
        return [m for m in self._models.values() if m.provider == provider]

    def to_profiles_by_tier(self) -> Dict[ModelTier, List[ModelProfile]]:
        """返回按 tier 分组的模型档案（供 ModelSelector 使用）"""
        profiles: Dict[ModelTier, List[ModelProfile]] = {
            ModelTier.A: [],
            ModelTier.MID: [],
            ModelTier.EXEC: [],
        }
        for model in self._models.values():
            profiles.setdefault(model.tier, []).append(model)
        return profiles

    def save(self, path: Path):
        """保存到文件"""
        data = {
            name: {
                "name": m.name,
                "tier": m.tier.value,
                "provider": m.provider,
                "model_id": m.model_id,
                "cost_per_1k_input": m.cost_per_1k_input,
                "cost_per_1k_output": m.cost_per_1k_output,
                "max_tokens": m.max_tokens,
                "pass_at_1": m.pass_at_1,
                "fix_at_1": m.fix_at_1,
                "strengths": m.strengths,
            }
            for name, m in self._models.items()
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: Path):
        """从文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for name, model_data in data.items():
            if "tier" in model_data and isinstance(model_data["tier"], str):
                model_data["tier"] = ModelTier(model_data["tier"])
            self._models[name] = ModelProfile(**model_data)
