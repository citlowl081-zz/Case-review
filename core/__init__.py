"""Re-export settings from existing backend config for use in new modules."""
import sys
import os

# Add backend to path so we can import from backend/app
_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.core.config import settings  # noqa: E402

__all__ = ["settings"]
