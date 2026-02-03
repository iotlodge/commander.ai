"""
Document loaders for various file types
"""

from backend.tools.document_loaders.base import BaseDocumentLoader
from backend.tools.document_loaders.pdf_loader import PDFLoader
from backend.tools.document_loaders.docx_loader import DocxLoader
from backend.tools.document_loaders.text_loader import TextLoader
from backend.tools.document_loaders.chunker import DocumentChunker

__all__ = [
    "BaseDocumentLoader",
    "PDFLoader",
    "DocxLoader",
    "TextLoader",
    "DocumentChunker",
]
