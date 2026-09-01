#!/usr/bin/env python3
"""CLI 冒烟测试（subprocess 级）"""
import subprocess
import sys
import json
from pathlib import Path

CLI = [sys.executable, str(Path(__file__).resolve().parent.parent / "cli.py")]
TASK = "实现用户登录功能"


def _run(*args, check=True):
    result = subprocess.run(
        [*CLI, *args],
        capture_output=True, text=True, timeout=30,
    )
    if check:
        assert result.returncode == 0, f"CLI {args} failed: {result.stderr}"
    return result


def test_cli_help():
    r = _run("--help")
    assert "dev-model-router" in r.stdout
    assert "assess" in r.stdout
    assert "decompose" in r.stdout


def test_cli_assess():
    r = _run("assess", TASK)
    assert "复杂度" in r.stdout
    assert "分数" in r.stdout


def test_cli_assess_json():
    r = _run("assess", TASK, "--json")
    assert "复杂度" in r.stdout
    json_start = r.stdout.index("{")
    data = json.loads(r.stdout[json_start:])
    assert data["level"] in ("low", "medium", "high")
    assert 0 <= data["score"] <= 1


def test_cli_select():
    r = _run("select", TASK)
    assert "选择模型" in r.stdout
    assert "Tier" in r.stdout


def test_cli_decompose(tmp_path):
    out = tmp_path / "dag.json"
    r = _run("decompose", TASK, "--output", str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert "nodes" in data
    assert len(data["nodes"]) > 0


def test_cli_execute(tmp_path):
    dag_path = tmp_path / "dag.json"
    _run("decompose", TASK, "--output", str(dag_path))
    r = _run("execute", str(dag_path))
    assert "执行结果" in r.stdout
    assert "completed" in r.stdout


def test_cli_assemble(tmp_path):
    dag_path = tmp_path / "dag.json"
    _run("decompose", TASK, "--output", str(dag_path))
    _run("execute", str(dag_path))
    r = _run("assemble", str(dag_path))
    assert "组装成功" in r.stdout


def test_cli_models():
    r = _run("models")
    assert "Claude" in r.stdout or "GPT" in r.stdout or "Gemini" in r.stdout


def test_cli_models_tier():
    r = _run("models", "--tier", "tier-a")
    assert "Claude" in r.stdout


def test_cli_cost():
    r = _run("cost")
    assert "成本报告" in r.stdout
    assert "总成本" in r.stdout


def test_cli_config_list():
    r = _run("config", "list")
    assert "daily_budget" in r.stdout
    assert "monthly_budget" in r.stdout
