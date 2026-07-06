"""
测试 app/rag/loader.py — 文档加载器工厂
"""
import pytest
import tempfile
import os
from app.rag.loader import load_document


class TestLoadDocument:
    """测试文档加载"""

    def test_load_txt_file(self):
        """加载 TXT 文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("这是一份临床试验方案文档。\n包含筛选期检查项目。")
            f.flush()
            path = f.name

        try:
            docs = load_document(path, "txt")
            assert len(docs) >= 1
            assert any("临床试验" in d.page_content for d in docs)
        finally:
            os.unlink(path)

    def test_load_markdown_file(self):
        """加载 Markdown 文件"""
        pytest.importorskip("unstructured")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 研究方案\n\n## 筛选标准\n\n- 年龄 18-75 岁")
            f.flush()
            path = f.name

        try:
            docs = load_document(path, "md")
            assert len(docs) >= 1
            content = " ".join(d.page_content for d in docs)
            assert "研究方案" in content
        finally:
            os.unlink(path)

    def test_load_csv_file(self):
        """加载 CSV 文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
            f.write("访视,日期,检查项目\nV1,2026-01-15,血常规\nV2,2026-02-01,心电图")
            f.flush()
            path = f.name

        try:
            docs = load_document(path, "csv")
            assert len(docs) >= 1
            content = " ".join(d.page_content for d in docs)
            assert "V1" in content or "访视" in content
        finally:
            os.unlink(path)

    def test_unknown_extension_falls_back_to_text(self):
        """未知扩展名回退到文本加载"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False, encoding="utf-8") as f:
            f.write("测试内容")
            f.flush()
            path = f.name

        try:
            docs = load_document(path, "xyz")
            assert len(docs) >= 1
        finally:
            os.unlink(path)

    def test_nonexistent_file_raises_error(self):
        """不存在的文件抛出异常"""
        with pytest.raises(Exception):
            load_document("/nonexistent/path/file.pdf", "pdf")
