"""Document parsers — unified interface for PDF, DOCX, XLSX, TXT."""
from parsers.base import ParseResult
from parsers.pdf_parser import PDFParser
from parsers.docx_parser import DocxParser
from parsers.excel_parser import ExcelParser
from parsers.txt_parser import TxtParser

PARSERS = {
    "pdf": PDFParser(),
    "docx": DocxParser(),
    "xlsx": ExcelParser(),
    "txt": TxtParser(),
}


def parse_document(file_path: str, file_format: str) -> "ParseResult":
    """Parse a document using the appropriate parser.

    Args:
        file_path: Absolute path to the document
        file_format: One of 'pdf', 'docx', 'xlsx', 'txt'

    Returns:
        ParseResult with extracted text, tables, and metadata
    """
    parser = PARSERS.get(file_format)
    if parser is None:
        # Default to text parser
        parser = PARSERS["txt"]
    return parser.parse(file_path)


__all__ = ["ParseResult", "PDFParser", "DocxParser", "ExcelParser", "TxtParser", "parse_document"]
