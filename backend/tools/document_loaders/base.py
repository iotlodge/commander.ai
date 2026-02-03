"""
Base document loader interface
"""

from abc import ABC, abstractmethod


class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders"""

    @abstractmethod
    async def load(self, file_path: str) -> str:
        """
        Load document and return text content

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content from the document
        """
        pass
