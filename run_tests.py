# -*- coding: utf-8 -*-
"""方法论知识接线主流程验证 —— 对应验收标准
「提交结构模板、样例及查询结果」

零第三方依赖。打印每条验收标准的实测结果。
"""
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_base import KnowledgeBase, KnowledgeError, validate  # noqa

PASS, FAIL = [], []
OK = "\u2705"
NO = "\u274c"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = OK if cond else NO
    line = "  " + mark + " " + name
    if detail:
        line += " -- " + detail
    print(line)


print("=" * 78)
print("Methodology Knowledge Wiring -- acceptance verification")
print("=" * 78)
print("Acceptance: 结构模板、样例及查询结果\n")

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.join(HERE, "examples")
SCHEMA_PATH = os.path.join(HERE, "schema",
                           "methodology_entry.schema.json")

# 1. 结构模板可加载 draft-07
schema = json.load(open(SCHEMA_PATH, encoding="utf-8"))
check("1. schema loadable, draft-07",
      schema.get("$schema", "").endswith("draft-07/schema#"),
      "title=" + str(schema.get("title")))

# 2. 模板声明必填字段（9 个）
req = set(schema.get("required", []))
check("2. schema declares required fields",
      req == {"entry_id", "title", "methodology", "topic",
              "summary", "steps", "applicable_scenarios",
              "cited_sources", "created_at"},
      f"required={len(req)}")

# 3. 样例文件存在（3 合法 + 1 反例）
legal = sorted(f for f in os.listdir(EX)
               if f.startswith("method-") and f.endswith(".json")
               and "invalid" not in f)
invalid = [f for f in os.listdir(EX)
           if "invalid" in f and f.endswith(".json")]
check("3. three legal samples + invalid counter-example",
      len(legal) == 3 and len(invalid) >= 1, f"legal={legal}")

# 4. 三条合法样例全部通过 schema
kb = KnowledgeBase(EX)
check("4. all three entried loaded", kb.count() == 3,
      f"count={kb.count()}")

# 5. 每条样例都有引用来源（可引用）
all_entries = kb.all()
cite_ok = all(len(e.get("cited_sources", [])) >= 1 for e in all_entries)
check("5. every entry has cited sources", cite_ok,
      f"entries={len(all_entries)}")

# 6. 每条样例都有步骤（可执行）
step_ok = all(len(e.get("steps", [])) >= 2 for e in all_entries)
check("6. every entry has actionable steps", step_ok,
      "min 2 steps each")

# 7. 查询结果：按方法论名检索
scrum = kb.search("scrum")
check("7. search 'scrum' returns Scrum entry",
      len(scrum) == 1 and scrum[0]["methodology"] == "Scrum",
      f"hits={[e['entry_id'] for e in scrum]}")

# 8. 查询结果：按主题/标签检索
analysis = kb.search("analysis")
check("8. search 'analysis' returns 5W2H",
      any(e["methodology"] == "5W2H" for e in analysis),
      f"hits={[e['entry_id'] for e in analysis]}")

# 9. 查询结果：组合过滤（topic=质量改进）
quality = kb.search("", topic="质量改进")
check("9. topic filter '质量改进' returns PDCA",
      len(quality) == 1 and quality[0]["methodology"] == "PDCA",
      f"hits={[e['entry_id'] for e in quality]}")

# 10. 查询结果：无命中返回空（不报错）
none = kb.search("量子纠缠检索词xyz")
check("10. no-match returns empty", none == [], f"hits={len(none)}")

# 11. 引用可回链
cites = kb.citations_for("method-scrum-01")
check("11. citations retrievable",
      len(cites) == 1 and "Scrum" in cites[0]["reference"],
      str(cites[0].get("reference", ""))[:60])

# 12. 反例被 schema 拒绝（缺字段/空数组/额外字段）
bad = json.load(open(os.path.join(EX, "method-invalid-99.json"),
                     encoding="utf-8"))
errs = validate(bad, schema)
check("12. invalid entry rejected by schema", len(errs) >= 4,
      f"{len(errs)} errors -> {errs[:3]}")
try:
    kb.add_entry(bad)
    check("12b. invalid entry rejected at load", False, "未抛错")
except KnowledgeError as e:
    check("12b. invalid entry rejected at load", True, str(e)[:60])
# 13. 反例确实不进入正常库
check("13. invalid entry excluded from kb", kb.count() == 3,
      f"count={kb.count()}")

# 14. 查询演示命令可运行（demo.py）
r = subprocess.run([sys.executable, "demo.py"], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace")
check("14. demo.py exit=0", r.returncode == 0,
      f"exit={r.returncode}")

# 15. 交付齐套（9 文件）
refs = ["knowledge_base.py", "run_tests.py", "demo.py",
        "schema/methodology_entry.schema.json",
        "examples/method-scrum-01.json",
        "examples/method-5w2h-02.json",
        "examples/method-pdca-03.json",
        "examples/method-invalid-99.json",
        "README.md", "SETUP.md",
        "docs/验收对照.md", "docs/实现说明.md", "docs/验证记录.md"]
broken = [r for r in refs if not os.path.isfile(os.path.join(HERE, r))]
check("15. delivery set complete (13 files)", not broken,
      "broken=" + str(broken) if broken else str(len(refs)) + " files")

# ═══════════════════════════════════════════════════════════════════
# 全量审核组（16+）：文档 vs 实现 / 攻击面 / 基准 / 脱敏
# 一次 run_tests.py = 全部审核维度，买家可一键复现
# ═══════════════════════════════════════════════════════════════════

print("\n-- 全量审核组 A：文档 vs 实现 --")

# 16. 零第三方依赖
src = open(os.path.join(HERE, "knowledge_base.py"),
           encoding="utf-8").read()
imports = [l.split()[1].split(".")[0]
           for l in src.splitlines()
           if (l.startswith("import ") or l.startswith("from "))
           and "knowledge_base" not in l]
check("16. zero third-party deps",
      all(m in {"json", "os", "sys", "re"} for m in imports),
      f"imports={imports}")

# 17. SETUP 新增条目流程可跑（合法新条目能进库）
import copy  # noqa
new_entry = copy.deepcopy(kb.all()[0])
new_entry["entry_id"] = "method-kanban-04"
new_entry["methodology"] = "Kanban"
new_entry["title"] = "看板方法"
try:
    kb.add_entry(new_entry)
    check("17. SETUP add-entry flow works", True,
          f"count={kb.count()}")
except KnowledgeError as e:
    check("17. SETUP add-entry flow works", False, str(e)[:60])

print("\n-- 全量审核组 B：攻击面/边界 --")

# 18. 空目录 / 缺失目录不崩
import tempfile  # noqa
with tempfile.TemporaryDirectory() as _td:
    m = KnowledgeBase(_td)
    check("18. empty dir -> 0 entries", m.count() == 0,
          f"count={m.count()}")
try:
    KnowledgeBase(os.path.join(tempfile.gettempdir(),
                               "clawhunt-1508-missing-xyz"))
    check("18b. missing dir tolerated", True, "no crash")
except Exception as e:
    check("18b. missing dir tolerated", False,
          f"raised {type(e).__name__}: {str(e)[:40]}")

# 19. 重复 entry_id 拒绝
try:
    dup = copy.deepcopy(kb.all()[0])
    kb.add_entry(dup)
    check("19. duplicate entry_id rejected", False)
except KnowledgeError as e:
    check("19. duplicate entry_id rejected", True,
          f"{str(e)[:50]}")

# 20. 超长字段 / 空字段被 schema 拒
overlen = copy.deepcopy(new_entry)
overlen["title"] = "x" * 200
check("20. oversized title rejected",
      any("title" in e for e in validate(overlen, schema)),
      str([e for e in validate(overlen, schema) if "title" in e][:1]))
empty_steps = copy.deepcopy(new_entry)
empty_steps["steps"] = []
check("20b. empty steps rejected",
      any("steps" in e for e in validate(empty_steps, schema)))

# 21. 大量条目（100 条）检索正确性
kb_bulk = KnowledgeBase()
for i in range(100):
    e = copy.deepcopy(new_entry)
    e["entry_id"] = f"method-bulk-{i:03d}"
    e["topic"] = "bulk"
    e["tags"] = ["bulk", f"t{i:03d}"]
    kb_bulk.add_entry(e)
hits100 = kb_bulk.search("t099")
check("21. 100 entries search still correct",
      len(hits100) == 1 and hits100[0]["entry_id"] == "method-bulk-099",
      f"hits={len(hits100)}")

print("\n-- 全量审核组 C：README 承诺命令一致性 --")

# 22. demo.py 输出含关键字样且退出 0（已在上文 14 检查 exit，这里查内容）
import subprocess  # noqa
r22 = subprocess.run([sys.executable, "demo.py"], cwd=HERE,
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace")
check("22. demo output has key query results",
      "method-scrum-01" in r22.stdout
      and "method-pdca-03" in r22.stdout
      and "结果 0 条" in r22.stdout,
      "key strings present")

# 23. README 反例命令（缺失必填被拒）真实输出
r23 = subprocess.run(
    [sys.executable, "-c",
     "import json; from knowledge_base import validate;"
     "s=json.load(open('schema/methodology_entry.schema.json',"
     "encoding='utf-8'));"
     "bad=json.load(open('examples/method-invalid-99.json',"
     "encoding='utf-8'));"
     "errs=validate(bad,s); print(len(errs),'errors')"],
    cwd=HERE, capture_output=True, text=True, encoding="utf-8",
    errors="replace")
check("23. README counter-example cmd matches",
      "errors" in r23.stdout and r23.returncode == 0,
      f"out={r23.stdout.strip()[:30]!r}")

print("\n-- 全量审核组 D：脱敏合规 --")

# 24. 交付物不含真实手机号/身份证/密钥/本机路径
# 只扫交付文件（排除 run_tests.py 自身——它含用于检测的字符串字面量）
hits_priv = []
scan_files = []
for root, _, files in os.walk(HERE):
    if "__pycache__" in root:
        continue
    for fn in files:
        if fn == "run_tests.py":
            continue
        if not fn.endswith((".py", ".json", ".md", ".schema.json")):
            continue
        scan_files.append(os.path.join(root, fn))
for fp in scan_files:
    t = open(fp, encoding="utf-8", errors="replace").read()
    for pat in ("C:\\", "D:\\", "Caterpillar", "Documents"):
        if pat in t or re.search(r"1[3-9]\d{9}", t) or "cph_" in t \
                or "ghp_" in t:
            hits_priv.append(f"{os.path.relpath(fp, HERE)}:{pat}")
check("24. no sensitive data in deliverables", not hits_priv,
      str(hits_priv[:4]) if hits_priv else "clean")

print()
print("=" * 78)
print("Result: PASS " + str(len(PASS)) + "   FAIL " + str(len(FAIL)))
print("=" * 78)
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)