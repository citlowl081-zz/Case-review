"""Utility functions for the clinical QC system."""
import os
import re
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


# ── Security ──

def safe_path_component(s: str, max_length: int = 100) -> str:
    """Validate a user-supplied path component to prevent path traversal.

    Raises ValueError if the string contains dangerous characters.
    """
    if not s or not isinstance(s, str):
        raise ValueError("Path component must be a non-empty string")
    if len(s) > max_length:
        raise ValueError(f"Path component too long (max {max_length} chars)")
    # Block path traversal sequences
    if ".." in s or "/" in s or "\\" in s:
        raise ValueError("Path component contains invalid characters")
    # Allow only alphanumeric, Chinese chars, hyphens, underscores, dots
    if not re.match(r'^[\w一-鿿\-. ]+$', s):
        raise ValueError("Path component contains unsafe characters")
    return s


# ── Paths ──

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"


def get_project_dir(project_id: str) -> Path:
    """Get the data directory for a project."""
    return PROJECTS_DIR / project_id


def get_subject_dir(project_id: str, subject_code: str) -> Path:
    """Get the data directory for a subject within a project."""
    return PROJECTS_DIR / project_id / "raw" / f"subject_{subject_code}"


def get_report_dir(project_id: str) -> Path:
    """Get the reports directory for a project."""
    return PROJECTS_DIR / project_id / "reports"


def ensure_project_dirs(project_id: str):
    """Create all necessary directories for a project."""
    dirs = [
        get_project_dir(project_id) / "raw" / "protocol",
        get_project_dir(project_id) / "raw" / "investigator_brochure",
        get_project_dir(project_id) / "raw" / "drug_manual",
        get_project_dir(project_id) / "reports",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def ensure_subject_dirs(project_id: str, subject_code: str):
    """Create all necessary directories for a subject."""
    base = get_subject_dir(project_id, subject_code)
    subdirs = ["screening", "visits", "lab_reports", "ae_cm", "other"]
    for d in subdirs:
        (base / d).mkdir(parents=True, exist_ok=True)


# ── File helpers ──

def save_uploaded_file(uploaded_file, dest_dir: Path, filename: str = None) -> tuple:
    """Save an uploaded file to destination directory.
    Returns (saved_filename, full_path, file_size).
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = uploaded_file.name

    # Ensure unique filename
    base, ext = os.path.splitext(filename)
    saved_name = filename
    counter = 1
    while (dest_dir / saved_name).exists():
        saved_name = f"{base}_{counter}{ext}"
        counter += 1

    full_path = dest_dir / saved_name

    # Handle both file-like objects and paths
    if hasattr(uploaded_file, 'getbuffer'):
        with open(full_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    elif hasattr(uploaded_file, 'read'):
        content = uploaded_file.read()
        with open(full_path, "wb") as f:
            f.write(content)
    else:
        shutil.copy(str(uploaded_file), str(full_path))

    file_size = os.path.getsize(full_path)
    return saved_name, str(full_path), file_size


def get_file_format(filename: str) -> str:
    """Determine file format from extension."""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".txt": "txt",
        ".md": "txt",
        ".csv": "xlsx",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".tiff": "image",
        ".bmp": "image",
    }
    return mapping.get(ext, "other")


def format_timestamp(ts: str = None) -> str:
    """Format a timestamp for display."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return ts[:16] if len(ts) >= 16 else ts


def truncate_text(text: str, max_len: int = 200) -> str:
    """Truncate text to max_len characters, adding ellipsis if truncated."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def safe_json_loads(s: str) -> any:
    """Safely parse JSON string, returning empty dict/list on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {} if s and s.startswith("{") else []
