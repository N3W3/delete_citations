"""delete_citations package."""
from delete_citations.cleaner import (
    DEFAULT_CITATION_PATTERN,
    detect_citations,
    remove_citations,
    replace_citations,
)
from delete_citations.directory import (
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORED_DIRS,
    BatchResult,
    Directory,
    FileReport,
)
from delete_citations.file.file import File

__all__ = [
    "DEFAULT_CITATION_PATTERN",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORED_DIRS",
    "BatchResult",
    "Directory",
    "File",
    "FileReport",
    "detect_citations",
    "remove_citations",
    "replace_citations",
]
