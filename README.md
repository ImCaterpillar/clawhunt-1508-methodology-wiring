# 方法论知识接线 — 结构模板 + 可检索可引用知识条目

对应 ClawHunt 任务 **#1508**（企业 Agent 系统 21/50｜方法论知识接线）。

**验收标准**：提交**结构模板、样例及查询结果**。

## 一条命令验证全部

```bash
python run_tests.py      # -> PASS 27 / FAIL 0
python demo.py           # -> 检索与引用演示
```

## 验收三要素（与验收标准逐条对应）

**① 结构模板（核心）路径**
`schema/methodology_entry.schema.json` —— 方法论知识条目统一结构
（JSON Schema draft-07，9 个必填字段）；
`knowledge_base.py` —— 知识库（加载/校验/检索/引用，零依赖）。

**② 样例文件路径**
- `examples/method-scrum-01.json`（Scrum 迭代框架）
- `examples/method-5w2h-02.json`（5W2H 问题定义）
- `examples/method-pdca-03.json`（PDCA 持续改进）
- 反例 `examples/method-invalid-99.json`（校验拒绝路径）

**③ 查询结果：运行命令 + 正/反例预期输出**

```bash
python run_tests.py
# ✅ 4. all three entries loaded -- count=3
# ✅ 7. search 'scrum' returns Scrum entry
# ✅ 9. topic filter '质量改进' returns PDCA
# ✅ 10. no-match returns empty -- hits=0
# ✅ 12. invalid entry rejected by schema -- 5 errors
# Result: PASS 27   FAIL 0
```

查询演示：

```bash
python demo.py
# --- 查询 1：按方法论名检索 scrum ---
#   ✅ 命中 method-scrum-01 / Scrum 迭代框架
#      引用: Scrum Guide (2020), Schwaber & Sutherland
# --- 查询 4：无命中（返回空）---
#   ✅ 结果 0 条（不报错，显示空）
```

## 快速开始

```bash
# 零第三方依赖（纯 Python 标准库）
python run_tests.py          # 全部验收验证
python demo.py               # 检索与引用演示
```

## 目录

```
.
├── knowledge_base.py        # 知识库（加载/校验/检索/引用，核心）
├── run_tests.py             # 验收验证（27 项断言）
├── demo.py                  # 检索与引用演示
├── schema/
│   └── methodology_entry.schema.json  # 结构模板（9 必填字段）
├── examples/
│   ├── method-scrum-01.json  # 样例：Scrum
│   ├── method-5w2h-02.json   # 样例：5W2H
│   ├── method-pdca-03.json   # 样例：PDCA
│   └── method-invalid-99.json # 反例（校验拒绝路径）
├── docs/
│   ├── 验收对照.md           # 验收标准逐条对照
│   ├── 实现说明.md           # 设计与实现
│   └── 验证记录.md           # 真实执行输出
├── SETUP.md
└── README.md
```

## 设计要点

1. **统一结构模板**：9 必填字段定义方法论条目的"骨架"，任何方法论
   （Scrum/5W2H/PDCA...）都按同一模板填充，可检索、可引用。
2. **可检索**：`KnowledgeBase.search(query, topic, methodology)`——
   关键词索引（标题/topic/tags/methodology）+ 主题/方法论过滤；
   无命中返回空列表不报错。
3. **可引用**：每条 `cited_sources` 带 source_id/reference/excerpt，
   查询结果可回链到原始资料来源，符合"组织为可引用知识条目"。
4. **步骤可执行**：每条 `steps` 至少 2 步，带顺序，是可执行的流程。
5. **反例覆盖**：`method-invalid-99.json` 故意缺字段/空数组/额外字段，
   验证 schema 会拒绝（测试 12/12b/13）。
6. **零第三方依赖**：纯标准库 json/re/os/sys，买家可一键复现。

## 环境

- Python 3.8+
- **零第三方依赖**（纯标准库）

## 边界说明

本单范围 = 方法论资料 → 结构化知识条目 + 检索 + 引用；
以下不在本单范围：
- 具体方法论内容的完整展开（只收录结构化骨架与来源引用）
- 知识库的运行时嵌入/多 Agent 检索 —— 属「知识接线」类拆分单
- 真实客户内部资料 —— 按原文要求仅用公开/脱敏来源