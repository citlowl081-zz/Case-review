---
name: unit-test
description: 为 Python/TypeScript 代码自动生成单元测试、执行测试、输出覆盖率报告
user-invocable: true
---

# 单元测试技能

当用户输入 `/unit-test` 或请求创建/运行单元测试时，按以下流程执行。

## 流程

### Step 1 — 确认范围

如果用户没有明确指定，询问：
- 测试哪个文件/模块？
- Python (pytest) 还是 TypeScript (vitest)？

### Step 2 — 分析代码

用 Read 读取目标文件，识别所有可测试的函数、类方法、API 端点。

### Step 3 — 生成测试

**Python**：测试文件放 `backend/tests/test_<模块名>.py`
**TypeScript**：测试文件放被测文件同级的 `__tests__/` 目录

每个函数至少覆盖：正常输入、边界值、异常输入。

### Step 4 — 执行并报告

```bash
# Python
cd backend && source venv/bin/activate && python -m pytest tests/<test_file> -v --cov=<module> --cov-report=term-missing

# TypeScript
cd frontend && npx vitest run --reporter=verbose
```

### Step 5 — 输出报告

给出：通过/失败数量、覆盖率百分比、未覆盖的代码行。

## 规则

- API Key 等敏感信息必须 mock，不得硬编码
- 数据库测试用 SQLite `:memory:` 模式
- 异步函数加 `@pytest.mark.asyncio`
