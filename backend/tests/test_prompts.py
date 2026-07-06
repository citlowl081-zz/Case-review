"""
测试 app/rag/prompts.py — Prompt 模板
"""
import pytest
from app.rag.prompts import (
    QA_SYSTEM_PROMPT,
    QUERY_REWRITE_PROMPT,
    VISIT_WINDOW_REVIEW_PROMPT,
    INCLUSION_EXCLUSION_REVIEW_PROMPT,
    AE_LOGIC_REVIEW_PROMPT,
    CONSISTENCY_REVIEW_PROMPT,
    REVIEW_PROMPTS,
    REVIEW_TYPE_LABELS,
)


class TestQAPrompt:
    """测试问答 Prompt"""

    def test_contains_context_placeholder(self):
        """包含 {context} 占位符"""
        assert "{context}" in QA_SYSTEM_PROMPT

    def test_contains_question_placeholder(self):
        """包含 {question} 占位符"""
        assert "{question}" in QA_SYSTEM_PROMPT

    def test_references_citation_format(self):
        """提到引用格式 [1][2][3]"""
        assert "[1]" in QA_SYSTEM_PROMPT or "引用" in QA_SYSTEM_PROMPT

    def test_formats_correctly(self):
        """Prompt 可以正确格式化"""
        result = QA_SYSTEM_PROMPT.format(context="测试文档内容", question="测试问题")
        assert "测试文档内容" in result
        assert "测试问题" in result
        assert "{context}" not in result


class TestQueryRewritePrompt:
    """测试查询重写 Prompt"""

    def test_contains_history_placeholder(self):
        """包含 {history}"""
        assert "{history}" in QUERY_REWRITE_PROMPT

    def test_contains_question_placeholder(self):
        """包含 {question}"""
        assert "{question}" in QUERY_REWRITE_PROMPT


class TestReviewPrompts:
    """测试审核 Prompt 模板"""

    def test_all_four_review_types_exist(self):
        """4 种审核类型都存在"""
        assert len(REVIEW_PROMPTS) == 4
        assert "visit_window" in REVIEW_PROMPTS
        assert "inclusion_exclusion" in REVIEW_PROMPTS
        assert "ae_logic" in REVIEW_PROMPTS
        assert "consistency" in REVIEW_PROMPTS

    def test_all_review_labels_exist(self):
        """所有审核类型有中文标签"""
        for key in REVIEW_PROMPTS:
            assert key in REVIEW_TYPE_LABELS
            assert len(REVIEW_TYPE_LABELS[key]) > 0

    def test_visit_window_prompt_mentions_window(self):
        """访视审核提到窗口期"""
        assert "窗口" in VISIT_WINDOW_REVIEW_PROMPT or "访视" in VISIT_WINDOW_REVIEW_PROMPT

    def test_ae_prompt_mentions_ae(self):
        """AE 审核提到不良事件"""
        assert "AE" in AE_LOGIC_REVIEW_PROMPT or "不良事件" in AE_LOGIC_REVIEW_PROMPT

    def test_all_prompts_contain_context_placeholder(self):
        """所有审核 Prompt 包含 {context}"""
        for key, prompt in REVIEW_PROMPTS.items():
            assert "{context}" in prompt, f"{key} 缺少 {{context}}"

    def test_all_prompts_contain_content_placeholder(self):
        """所有审核 Prompt 包含 {content}"""
        for key, prompt in REVIEW_PROMPTS.items():
            assert "{content}" in prompt, f"{key} 缺少 {{content}}"
