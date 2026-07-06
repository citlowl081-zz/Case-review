"""OCR parser placeholder — for scanned PDFs and images.

Dependencies (not installed by default due to size ~500MB):
    pip install paddleocr paddlepaddle

Usage:
    from parsers.ocr_parser import OCRParser
    parser = OCRParser()
    result = parser.parse("scanned_report.jpg")
"""
from parsers.base import BaseParser, ParseResult


class OCRParser(BaseParser):
    name = "ocr"
    formats = ["image", "png", "jpg", "jpeg", "tiff", "bmp"]

    def parse(self, file_path: str) -> ParseResult:
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            return ParseResult(
                success=False,
                error=(
                    "PaddleOCR 未安装。OCR功能需要额外安装：\n"
                    "  pip install paddleocr paddlepaddle\n"
                    "安装包约 500MB，首次使用需下载模型文件。\n"
                    "如果你不需要OCR（电子版PDF/Word可直接解析），可以忽略此功能。"
                ),
            )

        result = ParseResult(success=True, page_count=1)

        try:
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            results = ocr.ocr(file_path, cls=True)

            if not results or not results[0]:
                return ParseResult(
                    success=False,
                    error="OCR 未识别到任何文字，请确认图片清晰度",
                )

            text_parts = []
            for line in results[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # Recognized text
                    text_parts.append(text)

            result.text = "\n".join(text_parts)

        except Exception as e:
            result.success = False
            result.error = f"OCR识别失败: {str(e)}"

        return result
