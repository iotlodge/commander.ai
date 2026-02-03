"""
DOCX document loader using LangChain
"""

from langchain_community.document_loaders import Docx2txtLoader

from backend.tools.document_loaders.base import BaseDocumentLoader


class DocxLoader(BaseDocumentLoader):
    """Loads DOCX documents using docx2txt via LangChain"""

    async def load(self, file_path: str) -> str:
        """
        Load DOCX and extract text content

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text content
        """
        loader = Docx2txtLoader(file_path)
        documents = await loader.aload()

        # Combine all document parts
        full_text = "\n\n".join([doc.page_content for doc in documents])

        return full_text
