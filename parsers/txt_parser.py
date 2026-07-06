"""Plain text / Markdown parser."""
import os
from parsers.base import BaseParser, ParseResult


class TxtParser(BaseParser):
    name = "txt"
    formats = ["txt", "md", "csv"]

    def parse(self, file_path: str) -> ParseResult:
        result = ParseResult(success=True, page_count=1)

        try:
            # Try UTF-8 first, fall back to other encodings
            for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        result.text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return ParseResult(
                    success=False,
                    error=f"无法解码文件 {os.path.basename(file_path)}，尝试了多种编码均失败",
                )

            # Add file size to metadata
            result.metadata["file_size"] = os.path.getsize(file_path)
            result.metadata["encoding"] = encoding

        except Exception as e:
            result.success = False
            result.error = f"文本文件读取失败: {str(e)}"

        return result
