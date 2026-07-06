"""通用工具函数."""
from datetime import datetime


def fmt_datetime(dt: datetime) -> str:
    """安全地将 datetime 格式化为 ISO 字符串，处理 None 值。

    替代项目中多处重复的 `x.isoformat() if x else ""` 模式。
    """
    return dt.isoformat() if dt else ""


def truncate_text(text: str, max_len: int = 300) -> str:
    """截断文本到指定长度，超出部分用 ... 表示。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
