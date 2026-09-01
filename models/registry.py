#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型注册表模块

管理模型信息、性能档案和配置。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    provider: str  # "anthropic" | "openai" | "google" | "deepseek"
    model_id: str  # API 模型 ID
    tier: str  # "tier-a" | "tier-mid" | "tier-exec"
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    pass_at_1: float = 0.0
    fix_at_1: float = 0.0
    strengths: List[str] = field(default_factory=list)
    notes: str = ""


class ModelRegistry:
    """
    模型注册表

    Usage:
        registry = ModelRegistry()
        registry.register(ModelInfo(name="Claude Opus", ...))
        model = registry.get("Claude Opus")
    """

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._load_defaults()

    def _load_defaults(self):
        """加载默认模型"""
        defaults = [
            ModelInfo(
                name="Claude Opus",
                provider="anthropic",
                model_id="claude-opus-4-20250514",
                tier="tier-a",
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                max_tokens=32000,
                pass_at_1=0.92,
                fix_at_1=0.88,
                strengths=["complex_reasoning", "architecture", "debugging"],
            ),
            ModelInfo(
                name="Claude Sonnet",
                provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                tier="tier-mid",
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                max_tokens=16000,
                pass_at_1=0.85,
                fix_at_1=0.80,
                strengths=["code_generation", "testing"],
            ),
            ModelInfo(
                name="Claude Haiku",
                provider="anthropic",
                model_id="claude-haiku-3-5-20241022",
                tier="tier-exec",
                cost_per_1k_input=0.0008,
                cost_per_1k_output=0.004,
                max_tokens=8000,
                pass_at_1=0.75,
                fix_at_1=0.70,
                strengths=["simple_tasks", "formatting"],
            ),
            ModelInfo(
                name="GPT-4.1",
                provider="openai",
                model_id="gpt-4.1",
                tier="tier-a",
                cost_per_1k_input=0.002,
                cost_per_1k_output=0.008,
                max_tokens=32000,
                pass_at_1=0.90,
                fix_at_1=0.85,
                strengths=["general", "creative"],
            ),
            ModelInfo(
                name="GPT-4.1-mini",
                provider="openai",
                model_id="gpt-4.1-mini",
                tier="tier-mid",
                cost_per_1k_input=0.0004,
                cost_per_1k_output=0.0016,
                max_tokens=16000,
                pass_at_1=0.82,
                fix_at_1=0.78,
                strengths=["code_generation", "testing"],
            ),
            ModelInfo(
                name="GPT-4.1-nano",
                provider="openai",
                model_id="gpt-4.1-nano",
                tier="tier-exec",
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

    def register(self, model: ModelInfo):
        """注册模型"""
        self._models[model.name] = model

    def get(self, name: str) -> Optional[ModelInfo]:
        """获取模型"""
        return self._models.get(name)

    def list_all(self) -> List[ModelInfo]:
        """列出所有模型"""
        return list(self._models.values())

    def list_by_tier(self, tier: str) -> List[ModelInfo]:
        """按 tier 列出模型"""
        return [m for m in self._models.values() if m.tier == tier]

    def list_by_provider(self, provider: str) -> List[ModelInfo]:
        """按供应商列出模型"""
        return [m for m in self._models.values() if m.provider == provider]

    def save(self, path: Path):
        """保存到文件"""
        data = {
            name: {
                "name": m.name,
                "provider": m.provider,
                "model_id": m.model_id,
                "tier": m.tier,
                "cost_per_1k_input": m.cost_per_1k_input,
                "cost_per_1k_output": m.cost_per_1k_output,
                "max_tokens": m.max_tokens,
                "pass_at_1": m.pass_at_1,
                "fix_at_1": m.fix_at_1,
                "strengths": m.strengths,
                "notes": m.notes,
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
            self._models[name] = ModelInfo(**model_data)
