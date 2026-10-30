# -*- coding: utf-8 -*-
"""方法论知识接线：把方法论资料组织为可检索、可引用的知识条目。

对应 ClawHunt 任务 #1508（企业 Agent 系统 21/50｜方法论知识接线），
验收标准：**提交结构模板、样例及查询结果**。

设计：
  - 统一结构模板 `schema/methodology_entry.schema.json`（draft-07 必要
    子集校验，内置实现，零第三方依赖）
  - 每个方法论一条 JSON 条目（examples/method-*.json），含可追溯的
    引用来源（cited_sources）与可执行步骤（steps）
  - `KnowledgeBase`：
      · 加载全部条目 → schema 校验 → 建立索引（按 topic/tags/
        methodology/文本关键词）
      · 检索（可检索）：按关键词/主题/方法论名称查询，返回命中条目
      · 引用（可引用）：每条命中带着来源引用（cited_sources），
        可回链到原始资料
  - 查询验证：命令式查询示例 + 预期结果断言（对应"查询结果"交付物）
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class KnowledgeError(Exception):
    pass


# ── 迷你 JSON Schema draft-07 必要子集（与系列单同款）────────────
def _type_ok(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path="$"):
    errors = []
    if "type" in schema and not _type_ok(instance, schema["type"]):
        return [f"{path}: 期望 {schema['type']} 实为 {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: 值 {instance!r} 不在允许集合 {schema['enum']}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(instance)} < {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: 长度 {len(instance)} > {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: 值 {instance!r} 不匹配模式 {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < {schema['minimum']}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} < {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(instance, dict):
        if "required" in schema:
            for k in schema["required"]:
                if k not in instance:
                    errors.append(f"{path}: 缺少必填字段 {k!r}")
        if schema.get("additionalProperties") is False \
                and "properties" in schema:
            for k in instance:
                if k not in schema["properties"]:
                    errors.append(f"{path}: 不允许的额外字段 {k!r}")
        if "properties" in schema:
            for k, sub in schema["properties"].items():
                if k in instance:
                    errors += validate(instance[k], sub, f"{path}.{k}")
    return errors


class KnowledgeBase:
    """方法论知识条目库：加载/校验/检索/引用。"""

    def __init__(self, entries_dir=None):
        here = os.path.dirname(os.path.abspath(__file__))
        self.schema = json.load(open(
            os.path.join(here, "schema", "methodology_entry.schema.json"),
            encoding="utf-8"))
        self._entries = {}
        self._index = {}          # 关键词(小写) -> set(entry_id)
        if entries_dir:
            self.load_dir(entries_dir)

    # ── 加载 ─────────────────────────────────────────────────────
    def load_dir(self, d):
        if not os.path.isdir(d):
            return 0
        files = sorted(f for f in os.listdir(d)
                       if f.startswith("method-") and f.endswith(".json")
                       and "invalid" not in f)
        n = 0
        for fn in files:
            cfg = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            self.add_entry(cfg)
            n += 1
        return n

    def add_entry(self, entry):
        errs = validate(entry, self.schema)
        if errs:
            raise KnowledgeError("条目校验失败: " + "; ".join(errs[:5]))
        eid = entry["entry_id"]
        if eid in self._entries:
            raise KnowledgeError(f"重复 entry_id: {eid}")
        self._entries[eid] = entry
        # 建索引
        keys = {entry.get("topic", "").lower(),
                entry.get("methodology", "").lower()}
        keys |= {t.lower() for t in entry.get("tags", [])}
        for s in self._tokenize(entry.get("title", "")):
            keys.add(s)
        for k in keys:
            if k:
                self._index.setdefault(k, set()).add(eid)
        return eid

    @staticmethod
    def _tokenize(text):
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    # ── 检索（可检索）────────────────────────────────────────────
    def search(self, query, topic=None, methodology=None):
        """按关键词/主题/方法论名称检索，返回命中条目列表（带引用）。

        query 为空时按 topic/methodology 过滤全部。
        """
        tokens = self._tokenize(query)
        hits = set(self._entries.keys())
        if tokens:
            hits = set()
            for t in tokens:
                if t in self._index:
                    hits |= self._index[t]
        if topic:
            hits = {i for i in hits
                    if self._entries[i].get("topic", "").lower()
                    == topic.lower()}
        if methodology:
            hits = {i for i in hits
                    if self._entries[i].get("methodology", "").lower()
                    == methodology.lower()}
        return [self._entries[i] for i in sorted(hits)]

    def get(self, entry_id):
        return self._entries.get(entry_id)

    def all(self):
        return [self._entries[i] for i in sorted(self._entries)]

    def count(self):
        return len(self._entries)

    def entries(self):
        return sorted(self._entries)

    # ── 引用（可引用）────────────────────────────────────────────
    def citations_for(self, entry_id):
        """返回某条目的引用来源清单（含摘录，可回链）。"""
        e = self._entries.get(entry_id)
        if not e:
            return []
        return list(e.get("cited_sources", []))