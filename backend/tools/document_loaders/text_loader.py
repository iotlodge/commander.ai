"""
Text file loader for plain text, markdown, and RTF
"""

from langchain_community.document_loaders import TextLoader as LCTextLoader

from backend.tools.document_loaders.base import BaseDocumentLoader


class TextLoader(BaseDocumentLoader):
    """Loads plain text files (.txt, .md, .rtf)"""

    async def load(self, file_path: str) -> str:
        """
        Load text file

        Args:
            file_path: Path to text file

        Returns:
            File contents as string
        """
        loader = LCTextLoader(file_path, encoding="utf-8")
        documents = await loader.aload()

        # Combine all documents (usually just one for text files)
        full_text = "\n\n".join([doc.page_content for doc in documents])

        return full_text
