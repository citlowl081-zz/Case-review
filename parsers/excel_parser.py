"""Excel parser using openpyxl + pandas."""
from parsers.base import BaseParser, ParseResult


class ExcelParser(BaseParser):
    name = "excel"
    formats = ["xlsx", "xls", "csv"]

    def parse(self, file_path: str) -> ParseResult:
        try:
            import pandas as pd
        except ImportError:
            return ParseResult(
                success=False,
                error="pandas not installed. Run: pip install pandas openpyxl",
            )

        result = ParseResult(success=True)

        try:
            # Read all sheets
            xls = pd.ExcelFile(file_path, engine="openpyxl")
            text_parts = []

            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                text_parts.append(f"=== Sheet: {sheet_name} ===")

                # Convert DataFrame to text description
                text_parts.append(f"行数: {len(df)}, 列数: {len(df.columns)}")
                text_parts.append(f"列名: {', '.join(str(c) for c in df.columns)}")

                # Sample data as text
                # Limit rows to avoid exceeding token limits
                df_sample = df.head(100)
                text_parts.append(df_sample.to_string(index=False))

                # Store as table
                table_data = [list(df.columns)]  # Header
                for _, row in df_sample.iterrows():
                    table_data.append([str(v) if pd.notna(v) else "" for v in row])
                result.tables.append(table_data)

                # Text representation
                lines = [" | ".join(str(c) for c in df.columns)]
                for _, row in df_sample.iterrows():
                    lines.append(" | ".join(str(v) if pd.notna(v) else "" for v in row))
                result.tables_text.append("\n".join(lines))

            result.text = "\n\n".join(text_parts)

        except Exception as e:
            result.success = False
            result.error = f"Excel解析失败: {str(e)}"

        return result
