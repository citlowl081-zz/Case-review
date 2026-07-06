"""RAG Engine — document loading, chunking, embedding, retrieval."""
import sys
import os

# Make backend app accessible
_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
