"""
PDF document loader using LangChain
"""

from langchain_community.document_loaders import PyPDFLoader

from backend.tools.document_loaders.base import BaseDocumentLoader


class PDFLoader(BaseDocumentLoader):
    """Loads PDF documents using PyPDF via LangChain"""

    async def load(self, file_path: str) -> str:
        """
        Load PDF and extract text content

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text from all pages
        """
        loader = PyPDFLoader(file_path)
        pages = await loader.aload()

        # Combine all pages into single text
        full_text = "\n\n".join([page.page_content for page in pages])

        return full_text
