"""Orchestrator — coordinates all review agents and builds the final report."""
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from datetime import datetime

_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from agents.review_agent import ReviewAgent
from rag.prompts import AGENT_CONFIGS

# Agents that run independently (1-8, query agent runs after)
REVIEW_AGENT_KEYS = ["inclusion", "timeline", "ae", "cm", "prick_test", "lab", "drug", "completeness"]
QUERY_AGENT_KEY = "query"


class Orchestrator:
    """Orchestrates the full clinical trial QC review pipeline.

    Usage:
        orch = Orchestrator()
        result = orch.run_review(
            project_id="...",
            protocol_context="方案文本...",
            subject_data="受试者所有文档合并文本...",
            progress_callback=my_callback,  # optional
        )
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def run_review(
        self,
        project_id: str,
        protocol_context: str = "",
        subject_data: str = "",
        progress_callback=None,
        run_agents: List[str] = None,
    ) -> Dict[str, Any]:
        """Run the full review pipeline.

        Args:
            project_id: Project UUID
            protocol_context: Concatenated text of protocol/IB/drug manual documents
            subject_data: Concatenated text of all subject documents
            progress_callback: Optional fn(agent_name, status) for progress updates
            run_agents: Optional list of agent keys to run (default: all 8)

        Returns:
            Dict with all findings, timeline events, and summary
        """
        context = {
            "project_id": project_id,
            "protocol_context": protocol_context,
        }

        agents_to_run = run_agents or REVIEW_AGENT_KEYS
        all_findings = []
        timeline_events = []
        agent_results = {}

        # ── Phase 1: Run agents 1-8 in parallel ──
        if progress_callback:
            progress_callback("orchestrator", "starting")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for key in agents_to_run:
                if key == QUERY_AGENT_KEY:
                    continue  # Query agent runs after
                if key not in AGENT_CONFIGS:
                    continue
                agent = ReviewAgent(key)
                future = executor.submit(agent.run, context, subject_data)
                futures[future] = key

            completed = 0
            total = len(futures)
            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result(timeout=300)  # 5 min timeout per agent
                    agent_results[key] = result

                    # Collect findings
                    findings = result.get("findings", [])
                    for f in findings:
                        if "review_category" not in f:
                            f["review_category"] = key
                    all_findings.extend(findings)

                    # Collect timeline events from timeline agent
                    if key == "timeline":
                        timeline_events = result.get("timeline_events", [])

                except Exception as e:
                    agent_results[key] = {
                        "category": key,
                        "findings": [{
                            "type": "suggestion",
                            "title": f"{AGENT_CONFIGS[key]['name']}执行超时",
                            "severity": "low",
                            "description": f"审核超时或异常: {str(e)}",
                            "source_files": [],
                            "evidence": "",
                            "suggestion": "请人工复核该审核维度",
                            "query_statement": "",
                            "risk_impact": "自动审核未完成",
                        }],
                    }
                    all_findings.extend(agent_results[key]["findings"])

                completed += 1
                if progress_callback:
                    progress_callback(key, f"completed ({completed}/{total})")

        # ── Phase 2: Run query agent with all findings ──
        if progress_callback:
            progress_callback("query", "generating queries...")

        query_result = self._run_query_agent(all_findings)
        agent_results["query"] = query_result

        # ── Phase 3: Build summary ──
        conclusion, risk_summary = self._assess_overall(all_findings)

        if progress_callback:
            progress_callback("orchestrator", "done")

        return {
            "agent_results": agent_results,
            "all_findings": all_findings,
            "timeline_events": timeline_events,
            "conclusion": conclusion,
            "risk_summary": risk_summary,
            "stats": {
                "total_findings": len(all_findings),
                "definite": len([f for f in all_findings if f.get("type") == "definite"]),
                "suspected": len([f for f in all_findings if f.get("type") == "suspected"]),
                "suggestion": len([f for f in all_findings if f.get("type") == "suggestion"]),
                "high_severity": len([f for f in all_findings if f.get("severity") == "high"]),
                "medium_severity": len([f for f in all_findings if f.get("severity") == "medium"]),
                "low_severity": len([f for f in all_findings if f.get("severity") == "low"]),
            },
        }

    def _run_query_agent(self, all_findings: list) -> Dict[str, Any]:
        """Run the query generation agent with findings from all other agents."""
        from rag.prompts import QUERY_PROMPT, CORE_RULES
        from langchain_core.messages import HumanMessage, SystemMessage
        from app.rag.chain import get_llm

        findings_text = json.dumps(all_findings, ensure_ascii=False, indent=2)
        if len(findings_text) > 30000:
            # Truncate if too long - keep findings with highest severity
            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_findings = sorted(
                all_findings,
                key=lambda f: (priority_order.get(f.get("severity", "low"), 2), f.get("type", "suggestion") != "definite"),
            )
            findings_text = json.dumps(sorted_findings[:50], ensure_ascii=False, indent=2)

        prompt = QUERY_PROMPT.format(all_findings=findings_text)
        system = f"你是临床试验质控Query撰写专家。{CORE_RULES}"

        try:
            llm = get_llm(streaming=False)
            response = llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ])
            return self._parse_json(response.content)
        except Exception as e:
            return {"category": "query", "queries": [], "query_summary": {"error": str(e)}}

    @staticmethod
    def _assess_overall(findings: list) -> tuple:
        """Determine overall conclusion based on findings."""
        high_count = len([f for f in findings if f.get("severity") == "high"])
        definite_count = len([f for f in findings if f.get("type") == "definite"])

        if high_count >= 2 or definite_count >= 5:
            conclusion = "critical"  # 可能影响入组或数据质量
            risk_text = f"发现 {high_count} 个高风险问题和 {definite_count} 个明确问题，建议重点关注并及时处理"
        elif high_count >= 1 or definite_count >= 2:
            conclusion = "has_issue"  # 存在明确问题
            risk_text = f"发现 {high_count} 个高风险问题和 {definite_count} 个明确问题"
        elif definite_count >= 1 or len([f for f in findings if f.get("type") == "suspected"]) >= 3:
            conclusion = "needs_confirm"  # 存在需确认问题
            risk_text = f"发现 {definite_count} 个明确问题和若干疑似问题，建议逐项确认"
        elif len(findings) == 0:
            conclusion = "no_issue"
            risk_text = "未发现明显问题，审核资料质量良好"
        else:
            conclusion = "needs_confirm"
            risk_text = f"发现 {len(findings)} 个疑似问题或建议，建议复核确认"

        return conclusion, risk_text

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"category": "query", "queries": [], "parse_error": True, "raw": text[:500]}
