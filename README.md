# dev-model-router

> 多模型分层编排工具：高阶模型拆解任务→低阶模型执行子任务→高阶模型组装调试

---

## 特性

- ✅ **任务复杂度评估**：关键词/分类器/混合三种模式
- ✅ **智能模型选择**：Tier-A/Tier-Mid/Tier-Exec 三层模型自动匹配
- ✅ **DAG 任务分解**：复杂任务→有向无环图→按依赖并行执行
- ✅ **分阶段执行**：生成→修复→精炼，每阶段选不同模型
- ✅ **成本优化**：预算控制、成本追踪、成本报告
- ✅ **结果组装**：自动合并子任务结果为最终输出

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 评估任务复杂度

```bash
python -m cli assess "实现用户登录功能"
# 输出: 复杂度: high, 分数: 0.85, 置信度: 0.72
```

### 3. 选择模型

```bash
python -m cli select "实现用户登录功能" --task-type code_generation
# 输出: 选择模型: Claude Opus, Tier: tier-a
```

### 4. 分解任务为 DAG

```bash
python -m cli decompose "实现用户登录功能" --output tasks.json
# 输出: 生成 DAG: tasks.json, 任务数: 6, 关键路径: 4 步
```

### 5. 执行 DAG

```bash
python -m cli execute tasks.json --budget 1.0
# 输出: 执行结果: completed, 总成本: $0.1250
```

### 6. 组装结果

```bash
python -m cli assemble tasks.json --text
# 输出: 任务执行报告
```

---

## 架构

```
dev-model-router/
├── router/                    # 路由层
│   ├── complexity.py          # 任务复杂度评估
│   ├── model_selector.py      # 模型选择器
│   └── cost_optimizer.py      # 成本优化器
├── decomposer/                # 分解层
│   ├── dag_builder.py         # DAG 构建器
│   ├── task_splitter.py       # 任务拆分器
│   └── dependency.py          # 依赖分析
├── executor/                  # 执行层
│   ├── staged_executor.py     # 分阶段执行器
│   ├── parallel_worker.py     # 并行工作者
│   └── assembler.py           # 结果组装器
├── models/                    # 模型档案
│   └── registry.py            # 模型注册表
├── cli.py                     # CLI 入口
├── requirements.txt           # 依赖
├── pyproject.toml             # 打包配置
└── README.md                  # 本文件
```

---

## 使用示例

### Python API

```python
from router import ComplexityAssessor, ModelSelector
from decomposer import DAGBuilder
from executor import StagedExecutor, Assembler

# 1. 评估复杂度
assessor = ComplexityAssessor()
result = assessor.assess("实现用户登录功能")
print(f"复杂度: {result.level.value}")

# 2. 选择模型
selector = ModelSelector()
selection = selector.select(result.level, task_type="code_generation")
print(f"选择模型: {selection.model.name}")

# 3. 分解任务
builder = DAGBuilder()
dag = builder.build("实现用户登录功能")
print(f"任务数: {len(dag.nodes)}")

# 4. 执行
executor = StagedExecutor()
exec_result = executor.execute(dag)
print(f"执行结果: {exec_result.status.value}")

# 5. 组装
assembler = Assembler()
assembly = assembler.assemble(dag)
print(f"组装成功: {assembly.success}")
```

### 分阶段执行（Stagewise Cascade）

```python
from router import ModelSelector

selector = ModelSelector()
selections = selector.get_staged_selections("code_generation")

for stage, selection in selections.items():
    print(f"{stage}: {selection.model.name} (${selection.estimated_cost:.4f})")
# 输出:
# planning: Claude Opus ($0.0525)
# generation: Claude Sonnet ($0.0105)
# review: Claude Opus ($0.0525)
# fix: Claude Sonnet ($0.0105)
# refine: Claude Sonnet ($0.0105)
```

---

## 模型 Tier

| Tier | 模型 | 适用场景 | 成本 |
|------|------|----------|------|
| Tier-A | Claude Opus, GPT-4.1 | 复杂推理、架构设计、调试 | 高 |
| Tier-Mid | Claude Sonnet, GPT-4.1-mini | 代码生成、单元测试、文档 | 中 |
| Tier-Exec | Claude Haiku, GPT-4.1-nano | 格式转换、批量处理、简单任务 | 低 |

---

## 许可证

MIT License

---

## 版本

- v1.0.0 — 初始版本
