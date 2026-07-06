"""Configurable clinical review agent — runs a single review dimension."""
import json
import sys
import os
from typing import List, Dict, Any

# Make backend modules accessible
_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.chain import get_llm
from rag.prompts import CORE_RULES, AGENT_CONFIGS
from rag.engine import search_and_rerank


class ReviewAgent:
    """A single-dimension clinical trial review agent.

    Each agent:
    1. Retrieves relevant context from the knowledge base
    2. Builds a specialized prompt
    3. Calls the LLM for review
    4. Parses the JSON response
    """

    def __init__(self, agent_key: str):
        config = AGENT_CONFIGS.get(agent_key)
        if not config:
            raise ValueError(f"Unknown agent: {agent_key}. Available: {list(AGENT_CONFIGS.keys())}")
        self.key = agent_key
        self.config = config
        self.name = config["name"]
        self.prompt_template = config["prompt_template"]

    def _retrieve_context(self, project_id: str, query: str, top_k: int = 8) -> str:
        """Search the knowledge base for relevant protocol sections."""
        try:
            results = search_and_rerank(project_id, query, top_k=top_k)
            if not results:
                return "（知识库中未找到相关方案文档）"

            parts = []
            for i, (doc, score) in enumerate(results, 1):
                source = doc.metadata.get("source", doc.metadata.get("filename", "未知文档"))
                page = doc.metadata.get("page", doc.metadata.get("page_number"))
                page_info = f", 第{page}页" if page else ""
                parts.append(f"[{i}] 来源: {source}{page_info} (相关度: {score:.2f})\n{doc.page_content}")
            return "\n\n---\n".join(parts)
        except Exception as e:
            return f"（检索失败: {str(e)}）"

    def build_prompt(self, context: str, subject_data: str) -> str:
        """Build the full prompt for this agent."""
        # Build a search query based on agent type
        search_queries = {
            "inclusion": "纳入标准 排除标准 入选条件",
            "timeline": "访视计划 访视窗口 时间要求",
            "ae": "不良事件 AE 记录 严重不良事件 SAE",
            "cm": "合并用药 禁用药物 合并治疗",
            "prick_test": "点刺试验 过敏原 皮肤试验",
            "lab": "实验室检查 正常值范围 异常值判断",
            "drug": "药物管理 药物发放 依从性 药物回收",
            "completeness": "病历书写 数据记录 文件管理",
        }
        query = search_queries.get(self.key, "")

        # Search knowledge base
        kb_context = self._retrieve_context(
            context.get("project_id", ""),
            query,
        ) if isinstance(context, dict) else ""

        return self.prompt_template.format(
            context=f"{kb_context}\n\n{context.get('protocol_context', '') if isinstance(context, dict) else str(context)}",
            subject_data=str(subject_data),
        )

    def run(self, context: Dict[str, Any], subject_data: str) -> Dict[str, Any]:
        """Execute this agent's review.

        Args:
            context: Dict with 'project_id', 'protocol_context', etc.
            subject_data: Concatenated text of all subject documents

        Returns:
            Dict with 'category', 'findings', and agent-specific summary
        """
        try:
            prompt = self.build_prompt(context, subject_data)
            system = f"你是临床试验质控专家，负责{self.name}。{CORE_RULES}"

            llm = get_llm(streaming=False)
            response = llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ])

            # Parse JSON from response
            return self._parse_response(response.content)

        except Exception as e:
            return {
                "category": self.key,
                "findings": [{
                    "type": "suggestion",
                    "title": f"{self.name}执行异常",
                    "severity": "medium",
                    "description": f"审核过程出错: {str(e)}",
                    "source_files": [],
                    "evidence": "",
                    "suggestion": "请人工复核该审核维度",
                    "query_statement": "",
                    "risk_impact": "自动审核未完成",
                }],
                f"{self.key}_summary": {"error": str(e)},
            }

    def _parse_response(self, raw_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response, with error handling."""
        text = raw_text.strip()

        # Remove markdown code fences
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
            # Try to find JSON block in the text
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            return {
                "category": self.key,
                "findings": [{
                    "type": "suggestion",
                    "title": "输出格式异常",
                    "severity": "medium",
                    "description": text[:1000],
                    "source_files": [],
                    "evidence": "",
                    "suggestion": "LLM输出格式不符合JSON规范，请人工审核以下内容",
                    "query_statement": "",
                    "risk_impact": "自动解析失败",
                }],
                f"{self.key}_summary": {"error": "JSON parse failed", "raw_output": text[:500]},
            }
