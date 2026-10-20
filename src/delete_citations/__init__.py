"""delete_citations package."""
from delete_citations.cleaner import detect_citations, remove_citations, replace_citations
from delete_citations.file.file import File

__all__ = ["File", "detect_citations", "remove_citations", "replace_citations"]
