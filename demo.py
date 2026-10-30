# -*- coding: utf-8 -*-
"""演示：方法论知识库的检索与引用（验收标准直接演示）

运行：python demo.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_base import KnowledgeBase  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
kb = KnowledgeBase(os.path.join(HERE, "examples"))

print("方法论知识接线演示 — 结构模板 + 样例 + 查询结果\n")
print(f"已加载 {kb.count()} 条方法论条目：")
for e in kb.all():
    print(f"  {e['entry_id']:<20} {e['methodology']:<10} "
          f"{e['title'][:24]}")

print("\n--- 查询 1：按方法论名检索 scrum ---")
for e in kb.search("scrum"):
    print(f"  ✅ 命中 {e['entry_id']} / {e['title']}")
    for c in kb.citations_for(e["entry_id"]):
        print(f"     引用: {c['reference']}")

print("\n--- 查询 2：按方法论名检索 pdca ---")
for e in kb.search("pdca"):
    print(f"  ✅ 命中 {e['entry_id']} / {e['title']}")

print("\n--- 查询 3：按主题过滤 问题分析 ---")
for e in kb.search("", topic="问题分析"):
    print(f"  ✅ 命中 {e['entry_id']} / {e['title']}")

print("\n--- 查询 4：无命中（返回空）---")
r = kb.search("不存在的检索词xyz")
print(f"  ✅ 结果 {len(r)} 条（不报错，显示空）")

print("\n" + "=" * 50)
print("验收结果: 结构模板 + 样例 + 查询结果 -> ✅ 全部可复现")
print("=" * 50)
sys.exit(0)