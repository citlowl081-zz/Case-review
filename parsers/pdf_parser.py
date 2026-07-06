"""PDF parser using pdfplumber — extracts text and tables."""
from parsers.base import BaseParser, ParseResult


class PDFParser(BaseParser):
    name = "pdf"
    formats = ["pdf"]

    def parse(self, file_path: str) -> ParseResult:
        try:
            import pdfplumber
        except ImportError:
            return ParseResult(
                success=False,
                error="pdfplumber not installed. Run: pip install pdfplumber",
            )

        result = ParseResult(success=True)

        try:
            with pdfplumber.open(file_path) as pdf:
                result.page_count = len(pdf.pages)
                text_parts = []

                for i, page in enumerate(pdf.pages):
                    # Extract page text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[第{i+1}页]\n{page_text}")

                    # Extract tables from page
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            result.tables.append(table)
                            # Render table as text
                            table_text = self._table_to_text(table)
                            result.tables_text.append(table_text)

                result.text = "\n\n".join(text_parts)

        except Exception as e:
            result.success = False
            result.error = f"PDF解析失败: {str(e)}"

        return result

    def _table_to_text(self, table: list) -> str:
        """Convert a table (list of rows) to readable text."""
        if not table:
            return ""
        lines = []
        for row in table:
            cells = [str(cell) if cell is not None else "" for cell in row]
            lines.append(" | ".join(cells))
        return "\n".join(lines)
