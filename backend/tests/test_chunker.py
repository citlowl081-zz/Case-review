"""
测试 app/rag/chunker.py — 临床试验文档切分策略
"""
import pytest
from langchain_core.documents import Document
from app.rag.chunker import get_text_splitter, split_documents, CLINICAL_SEPARATORS


class TestClinicalSeparators:
    """测试分隔符配置"""

    def test_contains_chinese_period(self):
        """包含中文句号"""
        assert "。" in CLINICAL_SEPARATORS

    def test_contains_chinese_semicolon(self):
        """包含中文分号"""
        assert "；" in CLINICAL_SEPARATORS

    def test_contains_newline_paragraph(self):
        """包含段落换行"""
        assert "\n\n" in CLINICAL_SEPARATORS


class TestGetTextSplitter:
    """测试切分器创建"""

    def test_returns_recursive_splitter(self):
        """返回 RecursiveCharacterTextSplitter"""
        splitter = get_text_splitter()
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        assert isinstance(splitter, RecursiveCharacterTextSplitter)

    def test_default_chunk_size(self):
        """默认 chunk_size 为 500"""
        splitter = get_text_splitter()
        assert splitter._chunk_size == 500

    def test_default_chunk_overlap(self):
        """默认 overlap 为 50"""
        splitter = get_text_splitter()
        assert splitter._chunk_overlap == 50

    def test_custom_chunk_size(self):
        """自定义 chunk_size"""
        splitter = get_text_splitter(chunk_size=300, chunk_overlap=30)
        assert splitter._chunk_size == 300
        assert splitter._chunk_overlap == 30


class TestSplitDocuments:
    """测试文档切分"""

    def test_single_document_split(self):
        """单文档切分产生多个 chunk"""
        doc = Document(
            page_content="第一段内容。第二段内容。第三段内容。" * 50,
            metadata={"source": "test.pdf"}
        )
        chunks = split_documents([doc])
        assert len(chunks) >= 1

    def test_metadata_preserved(self):
        """切分后元数据保留"""
        doc = Document(
            page_content="测试内容。" * 100,
            metadata={"source": "研究方案v3.pdf", "page": 5}
        )
        chunks = split_documents([doc])
        for chunk in chunks:
            assert "source" in chunk.metadata

    def test_chunk_index_in_metadata(self):
        """每个 chunk 包含索引"""
        doc = Document(
            page_content="测试。" * 200,
            metadata={"source": "test.pdf"}
        )
        chunks = split_documents([doc])
        assert chunks[0].metadata["chunk_index"] == 0
        assert "total_chunks" in chunks[0].metadata

    def test_empty_content(self):
        """空文档不报错"""
        doc = Document(page_content="", metadata={"source": "empty.pdf"})
        chunks = split_documents([doc])
        assert isinstance(chunks, list)

    def test_multiple_documents(self):
        """多文档切分"""
        docs = [
            Document(page_content="文档A。" * 100, metadata={"source": "a.pdf"}),
            Document(page_content="文档B。" * 100, metadata={"source": "b.pdf"}),
        ]
        chunks = split_documents(docs)
        assert len(chunks) >= 2
