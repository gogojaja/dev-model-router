#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务复杂度评估模块

支持三种评估模式：
1. 关键词路由：基于关键词匹配快速评估
2. 分类器路由：基于 DistilBERT 分类器准确评估
3. 混合路由：关键词 + 分类器联合决策
"""

from __future__ import annotations

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple


class ComplexityLevel(Enum):
    """任务复杂度等级"""
    LOW = "low"          # 简单任务：sum/list/define/格式转换
    MEDIUM = "medium"    # 中等任务：实现功能/写测试/文档
    HIGH = "high"        # 复杂任务：架构设计/调试/推理


@dataclass
class ComplexityResult:
    """复杂度评估结果"""
    level: ComplexityLevel
    score: float  # 0.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0
    method: str  # "keyword" | "classifier" | "hybrid"
    reasoning: str  # 评估理由


class ComplexityAssessor:
    """
    任务复杂度评估器

    Usage:
        assessor = ComplexityAssessor()
        result = assessor.assess("实现用户登录功能")
        print(result.level)  # ComplexityLevel.HIGH
    """

    # 关键词定义
    LOW_KEYWORDS = {
        "sum", "list", "define", "format", "convert", "print", "show",
        "求和", "列表", "定义", "格式化", "转换", "打印", "显示",
        "rename", "move", "copy", "delete", "create", "add",
        "重命名", "移动", "复制", "删除", "创建", "添加",
    }

    HIGH_KEYWORDS = {
        "prove", "derive", "explain why", "design", "architect", "optimize",
        "证明", "推导", "解释为什么", "设计", "架构", "优化",
        "debug", "refactor", "integrate", "migrate", "scale",
        "调试", "重构", "集成", "迁移", "扩展",
        "implement", "build", "develop", "create system",
        "实现", "构建", "开发", "创建系统",
    }

    MEDIUM_KEYWORDS = {
        "write", "implement", "function", "class", "module",
        "写", "实现", "函数", "类", "模块",
        "test", "document", "analyze", "review",
        "测试", "文档", "分析", "审查",
    }

    def __init__(self, mode: str = "keyword"):
        """
        初始化评估器

        Args:
            mode: 评估模式 ("keyword" | "classifier" | "hybrid")
        """
        self.mode = mode
        self._classifier = None

        if mode in ("classifier", "hybrid"):
            self._load_classifier()

    def _load_classifier(self):
        """加载 DistilBERT 分类器（延迟加载）"""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            model_name = "distilbert-base-uncased"
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                model_name, num_labels=3
            )
            self._model.eval()
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._model.to(self._device)
        except ImportError:
            print("[warning] transformers/torch 未安装，回退到关键词模式")
            self.mode = "keyword"

    def assess(self, task_description: str) -> ComplexityResult:
        """
        评估任务复杂度

        Args:
            task_description: 任务描述

        Returns:
            ComplexityResult: 评估结果
        """
        if self.mode == "keyword":
            return self._assess_keyword(task_description)
        elif self.mode == "classifier":
            return self._assess_classifier(task_description)
        elif self.mode == "hybrid":
            return self._assess_hybrid(task_description)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _assess_keyword(self, task: str) -> ComplexityResult:
        """关键词路由"""
        task_lower = task.lower()

        low_score = sum(1 for kw in self.LOW_KEYWORDS if kw in task_lower)
        high_score = sum(1 for kw in self.HIGH_KEYWORDS if kw in task_lower)
        medium_score = sum(1 for kw in self.MEDIUM_KEYWORDS if kw in task_lower)

        total = low_score + high_score + medium_score
        if total == 0:
            # 无关键词匹配，默认中等
            return ComplexityResult(
                level=ComplexityLevel.MEDIUM,
                score=0.5,
                confidence=0.3,
                method="keyword",
                reasoning="无关键词匹配，默认中等复杂度"
            )

        if high_score > low_score and high_score > medium_score:
            level = ComplexityLevel.HIGH
            score = min(1.0, 0.6 + high_score * 0.1)
        elif low_score > medium_score:
            level = ComplexityLevel.LOW
            score = max(0.0, 0.4 - low_score * 0.1)
        else:
            level = ComplexityLevel.MEDIUM
            score = 0.5

        confidence = min(1.0, total * 0.2)

        return ComplexityResult(
            level=level,
            score=score,
            confidence=confidence,
            method="keyword",
            reasoning=f"关键词匹配: low={low_score}, medium={medium_score}, high={high_score}"
        )

    def _assess_classifier(self, task: str) -> ComplexityResult:
        """分类器路由"""
        if self._model is None:
            return self._assess_keyword(task)

        import torch

        inputs = self._tokenizer(
            task, return_tensors="pt", truncation=True, max_length=512
        ).to(self._device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        probs = probs.cpu().numpy()[0]
        pred_idx = probs.argmax()
        confidence = float(probs[pred_idx])

        levels = [ComplexityLevel.LOW, ComplexityLevel.MEDIUM, ComplexityLevel.HIGH]
        level = levels[pred_idx]
        score = float(probs[2])  # HIGH 的概率作为 score

        return ComplexityResult(
            level=level,
            score=score,
            confidence=confidence,
            method="classifier",
            reasoning=f"分类器预测: low={probs[0]:.3f}, medium={probs[1]:.3f}, high={probs[2]:.3f}"
        )

    def _assess_hybrid(self, task: str) -> ComplexityResult:
        """混合路由：关键词 + 分类器联合决策"""
        keyword_result = self._assess_keyword(task)
        classifier_result = self._assess_classifier(task)

        # 加权平均（分类器权重0.7，关键词权重0.3）
        if keyword_result.confidence > 0.6 and classifier_result.confidence < 0.5:
            # 关键词高置信度，分类器低置信度 → 信任关键词
            final_level = keyword_result.level
            final_score = keyword_result.score
            final_confidence = keyword_result.confidence
            method = "hybrid-keyword"
        elif classifier_result.confidence > 0.7:
            # 分类器高置信度 → 信任分类器
            final_level = classifier_result.level
            final_score = classifier_result.score
            final_confidence = classifier_result.confidence
            method = "hybrid-classifier"
        else:
            # 两者都不高置信度 → 加权平均
            score = 0.3 * keyword_result.score + 0.7 * classifier_result.score
            if score > 0.7:
                final_level = ComplexityLevel.HIGH
            elif score > 0.3:
                final_level = ComplexityLevel.MEDIUM
            else:
                final_level = ComplexityLevel.LOW
            final_score = score
            final_confidence = max(keyword_result.confidence, classifier_result.confidence) * 0.8
            method = "hybrid-weighted"

        return ComplexityResult(
            level=final_level,
            score=final_score,
            confidence=final_confidence,
            method=method,
            reasoning=f"hybrid: keyword={keyword_result.level.value}({keyword_result.confidence:.2f}), classifier={classifier_result.level.value}({classifier_result.confidence:.2f})"
        )
