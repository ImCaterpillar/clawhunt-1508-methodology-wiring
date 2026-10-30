# 设置与运行

零第三方依赖，无需安装任何包。

## 环境要求

- Python 3.8+（标准库：json / os / sys / re）

## 快速验证

```bash
# 在项目根目录
python run_tests.py        # 27 项验收断言，期望 PASS 27 / FAIL 0
python demo.py             # 检索与引用演示，期望退出码 0
```

## 在自己的代码中使用

```python
from knowledge_base import KnowledgeBase

# 加载样例目录（自动 schema 校验 + 索引）
kb = KnowledgeBase("examples")

# 检索（可检索）：按关键词
hits = kb.search("scrum")            # -> Scrum 条目列表
# 按主题过滤
agile_ones = kb.search("", topic="敏捷研发")
# 按方法论过滤
pdca = kb.search("", methodology="PDCA")
print(kb.count(), "条已索引")

# 引用（可引用）：拿某条目的来源
for c in kb.citations_for("method-scrum-01"):
    print(c["reference"], "-", c["excerpt"])

# 新增一条方法论
entry = {
  "entry_id": "method-kanban-04",
  "title": "看板方法",
  "methodology": "Kanban",
  "topic": "流程管理",
  "summary": "可视化在制品与流程瓶颈，按拉动规则持续交付。",
  "steps": [
    {"order": 1, "action": "可视化工作流（列/泳道）"},
    {"order": 2, "action": "限制在制品 WIP，按拉动流转"}
  ],
  "applicable_scenarios": ["运维支持", "流水线优化"],
  "cited_sources": [{"source_id": "src-kanban-guide",
                     "reference": "Kanban Guide (2023)",
                     "excerpt": "Kanban is a strategy for optimizing flow."}],
  "tags": ["flow", "visual-management"],
  "created_at": "2026-10-30"
}
kb.add_entry(entry)   # 自动校验，非法即抛 KnowledgeError
```

## 常见问题

- **检索不到怎么办？** 检查关键词是否在 title/topic/tags/methodology 里；
  中文主题需用 `topic=` 参数精确过滤（测试 9 示范）。
- **条目被拒？** 对照 schema 9 必填字段；`steps` 至少 2 步、
  `cited_sources` 至少 1 条、`created_at` 用 YYYY-MM-DD、不能有额外字段。
- **Windows 中文乱码？** 脚本已内置 UTF-8 重配置。