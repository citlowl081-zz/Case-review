"""12-section clinical trial QC report builder."""
import json
from typing import List, Dict, Any
from datetime import datetime


class ReportBuilder:
    """Builds a structured 12-section clinical trial QC report.

    Sections:
    1. 总体结论
    2. 资料完整性检查
    3. 受试者时间轴
    4. 明确问题
    5. 疑似问题 / 建议确认
    6. AE 与合并用药专项审核
    7. 点刺试验专项审核
    8. 入排标准专项审核
    9. 药物管理与依从性审核
    10. 建议发起的澄清问题
    11. 建议修改或补充记录
    12. 无法判断但需要补充资料的事项
    """

    def __init__(self, project_name: str, subject_code: str):
        self.project_name = project_name
        self.subject_code = subject_code

    def build(self, review_result: Dict[str, Any],
              subject_docs: List = None,
              project_docs: List = None) -> str:
        """Build the complete 12-section Markdown report."""
        sections = []

        # Section 1: Overall Conclusion
        sections.append(self._section_1_overall(review_result))

        # Section 2: Document Completeness
        sections.append(self._section_2_completeness(subject_docs or [], project_docs or []))

        # Section 3: Timeline
        sections.append(self._section_3_timeline(review_result))

        # Section 4: Definite Issues
        sections.append(self._section_4_definite_issues(review_result))

        # Section 5: Suspected Issues
        sections.append(self._section_5_suspected_issues(review_result))

        # Section 6: AE & CM Special Review
        sections.append(self._section_6_ae_cm(review_result))

        # Section 7: Prick Test
        sections.append(self._section_7_prick_test(review_result))

        # Section 8: Inclusion/Exclusion
        sections.append(self._section_8_inclusion(review_result))

        # Section 9: Drug Management
        sections.append(self._section_9_drug(review_result))

        # Section 10: Queries
        sections.append(self._section_10_queries(review_result))

        # Section 11: Suggested Corrections
        sections.append(self._section_11_corrections(review_result))

        # Section 12: Insufficient Data
        sections.append(self._section_12_insufficient(review_result))

        return "\n\n".join(sections)

    # ── Section Builders ──

    def _section_1_overall(self, result: Dict) -> str:
        conclusion = result.get("conclusion", "unknown")
        risk = result.get("risk_summary", "")
        stats = result.get("stats", {})

        conclusion_label = {
            "no_issue": "✅ 无明显问题",
            "needs_confirm": "⚠️ 存在需确认问题",
            "has_issue": "❌ 存在明确问题",
            "critical": "🚨 可能影响入组或数据质量",
        }.get(conclusion, "❓ 未知")

        return f"""# 临床试验病历质控审核报告

## 1. 总体结论

**{conclusion_label}**

{risk}

### 审核统计
| 指标 | 数量 |
|------|------|
| 发现总数 | {stats.get('total_findings', 0)} |
| 明确问题 | {stats.get('definite', 0)} |
| 疑似问题 | {stats.get('suspected', 0)} |
| 建议确认 | {stats.get('suggestion', 0)} |
| 高风险 | {stats.get('high_severity', 0)} |
| 中风险 | {stats.get('medium_severity', 0)} |
| 低风险 | {stats.get('low_severity', 0)} |

---
*审核时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*项目: {self.project_name}*
*受试者: {self.subject_code}*
"""

    def _section_2_completeness(self, subject_docs: List, project_docs: List) -> str:
        lines = ["## 2. 资料完整性检查", ""]

        lines.append("### 已上传项目文件")
        if project_docs:
            for d in project_docs:
                dtype = getattr(d, 'doc_type', '') or ''
                fname = getattr(d, 'original_filename', '') or getattr(d, 'filename', '')
                lines.append(f"- [{dtype}] {fname}")
        else:
            lines.append("- （无项目文件信息）")

        lines.append("")
        lines.append("### 已上传受试者资料")
        if subject_docs:
            for d in subject_docs:
                dtype = getattr(d, 'doc_type', '') or ''
                fname = getattr(d, 'original_filename', '') or getattr(d, 'filename', '')
                lines.append(f"- [{dtype}] {fname}")
        else:
            lines.append("- （无受试者资料信息）")

        return "\n".join(lines)

    def _section_3_timeline(self, result: Dict) -> str:
        events = result.get("timeline_events", [])
        lines = ["## 3. 受试者时间轴", ""]

        if not events:
            lines.append("（未提取到时间轴事件，可能因受试者资料不足）")
            return "\n".join(lines)

        lines.append("| 时间 | 事件 | 来源文件 | 疑点 |")
        lines.append("|------|------|----------|------|")
        for ev in events:
            date = ev.get("date", ev.get("event_date", ""))
            event = ev.get("event", ev.get("event_name", ""))
            source = ev.get("source_file", "")
            has_issue = "⚠️" if ev.get("has_issue") else "✅"
            issue_desc = ev.get("issue_description", "")
            cell = f"{has_issue} {issue_desc}" if issue_desc else has_issue
            lines.append(f"| {date} | {event} | {source} | {cell} |")

        return "\n".join(lines)

    def _section_4_definite_issues(self, result: Dict) -> str:
        findings = [f for f in result.get("all_findings", []) if f.get("type") == "definite"]
        return self._findings_table("4. 明确问题", findings)

    def _section_5_suspected_issues(self, result: Dict) -> str:
        findings = [f for f in result.get("all_findings", []) if f.get("type") in ("suspected", "suggestion")]
        return self._findings_table("5. 疑似问题 / 建议确认", findings)

    def _section_6_ae_cm(self, result: Dict) -> str:
        lines = ["## 6. AE 与合并用药专项审核", ""]
        for key, label in [("ae", "AE审核"), ("cm", "合并用药审核")]:
            agent = result.get("agent_results", {}).get(key, {})
            lines.append(f"### {label}")
            summary = agent.get(f"{key}_summary", {})
            if summary:
                lines.append(f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```")
            else:
                lines.append("（暂无数据）")
            lines.append("")
        return "\n".join(lines)

    def _section_7_prick_test(self, result: Dict) -> str:
        lines = ["## 7. 点刺试验专项审核", ""]
        agent = result.get("agent_results", {}).get("prick_test", {})
        summary = agent.get("prick_test_summary", {})
        if summary:
            lines.append(f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```")
        else:
            lines.append("（未进行点刺试验审核或受试者无点刺试验资料）")
        return "\n".join(lines)

    def _section_8_inclusion(self, result: Dict) -> str:
        lines = ["## 8. 入排标准专项审核", ""]
        agent = result.get("agent_results", {}).get("inclusion", {})
        summary = agent.get("inclusion_summary", {})
        if summary:
            lines.append(f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```")
        else:
            lines.append("（暂无数据）")
        return "\n".join(lines)

    def _section_9_drug(self, result: Dict) -> str:
        lines = ["## 9. 药物管理与依从性审核", ""]
        agent = result.get("agent_results", {}).get("drug", {})
        summary = agent.get("drug_summary", {})
        if summary:
            lines.append(f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```")
        else:
            lines.append("（暂无数据）")
        return "\n".join(lines)

    def _section_10_queries(self, result: Dict) -> str:
        lines = ["## 10. 建议发起的澄清问题", ""]
        agent = result.get("agent_results", {}).get("query", {})
        queries = agent.get("queries", [])
        if not queries:
            # Fallback: generate from findings
            queries = self._gen_queries_from_findings(result.get("all_findings", []))

        if not queries:
            lines.append("（无需发起澄清问题）")
            return "\n".join(lines)

        lines.append("| 序号 | 优先级 | 类型 | 问题描述 | 建议澄清语句 |")
        lines.append("|------|--------|------|----------|-------------|")
        for q in queries:
            qid = q.get("query_id", "-")
            prio = q.get("priority", "medium")
            prio_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(prio, "")
            cat = q.get("review_category", "")
            desc = q.get("title", q.get("description", ""))[:100]
            qtext = q.get("query_text", q.get("query_statement", ""))[:200]
            lines.append(f"| {qid} | {prio_emoji} {prio} | {cat} | {desc} | {qtext} |")

        return "\n".join(lines)

    def _section_11_corrections(self, result: Dict) -> str:
        lines = ["## 11. 建议修改或补充记录", ""]
        findings = result.get("all_findings", [])
        corrections = [f for f in findings if f.get("suggestion") and "补充" in str(f.get("suggestion", ""))]
        if not corrections:
            lines.append("（暂无需要补充或修改的记录）")
            lines.append("")
            lines.append("> ⚠️ 注意：只能建议补充或澄清，不能替研究者编造病历内容。")
            return "\n".join(lines)

        for i, f in enumerate(corrections[:20], 1):
            lines.append(f"**{i}.** {f.get('title', '')}")
            lines.append(f"> 建议: {f.get('suggestion', '')}")
            lines.append("")
        lines.append("> ⚠️ 注意：只能建议补充或澄清，不能替研究者编造病历内容。")
        return "\n".join(lines)

    def _section_12_insufficient(self, result: Dict) -> str:
        lines = ["## 12. 无法判断但需要补充资料的事项", ""]
        findings = result.get("all_findings", [])
        insufficient = [f for f in findings if f.get("type") == "suggestion"
                       and ("无法判断" in str(f.get("description", ""))
                            or "方案依据未见" in str(f.get("evidence", ""))
                            or "缺少" in str(f.get("description", "")))]
        if not insufficient:
            lines.append("（所有审核项目均有足够资料进行判断）")
            return "\n".join(lines)

        for i, f in enumerate(insufficient[:20], 1):
            lines.append(f"**{i}.** {f.get('title', '')}")
            lines.append(f"> 描述: {f.get('description', '')}")
            lines.append(f"> 建议: {f.get('suggestion', '')}")
            lines.append("")
        return "\n".join(lines)

    # ── Helpers ──

    def _findings_table(self, title: str, findings: list) -> str:
        lines = [f"## {title}", ""]
        if not findings:
            lines.append("（无）")
            return "\n".join(lines)

        lines.append("| # | 类型 | 风险 | 问题描述 | 涉及文件 | 依据 | 建议 |")
        lines.append("|---|------|------|----------|----------|------|------|")
        for i, f in enumerate(findings[:50], 1):
            sev = f.get("severity", "medium")
            sev_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "")
            desc = (f.get("description", "") or "")[:150]
            src = self._fmt_sources(f.get("source_files", ""))
            ev = (f.get("evidence", "") or "")[:100]
            sug = (f.get("suggestion", "") or "")[:100]
            lines.append(f"| {i} | {f.get('review_category', '')} | {sev_emoji}{sev} | {desc} | {src} | {ev} | {sug} |")

        return "\n".join(lines)

    @staticmethod
    def _fmt_sources(sources) -> str:
        if isinstance(sources, list):
            return ", ".join(str(s) for s in sources[:3])
        if isinstance(sources, str):
            try:
                parsed = json.loads(sources)
                if isinstance(parsed, list):
                    return ", ".join(str(s) for s in parsed[:3])
            except (json.JSONDecodeError, TypeError):
                pass
            return sources[:100]
        return str(sources)[:100]

    @staticmethod
    def _gen_queries_from_findings(findings: list) -> list:
        """Fallback: generate queries directly from findings."""
        queries = []
        for i, f in enumerate(findings, 1):
            if f.get("query_statement"):
                queries.append({
                    "query_id": f"Q-{i:03d}",
                    "priority": f.get("severity", "medium"),
                    "review_category": f.get("review_category", ""),
                    "title": f.get("title", ""),
                    "query_text": f.get("query_statement", ""),
                })
        return queries
