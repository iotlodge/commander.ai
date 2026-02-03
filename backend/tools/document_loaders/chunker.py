"""
Document chunking utility using LangChain
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import get_settings


class DocumentChunker:
    """
    Splits documents into overlapping chunks for embedding
    """

    def __init__(self):
        settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    async def chunk_document(
        self, content: str, metadata: dict | None = None
    ) -> list[dict]:
        """
        Split document into chunks with metadata

        Args:
            content: Document text content
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with content and metadata
        """
        metadata = metadata or {}

        # Split text into chunks
        chunks = self.text_splitter.split_text(content)

        # Build chunk dictionaries with metadata
        chunk_dicts = []
        for idx, chunk_text in enumerate(chunks):
            chunk_dict = {
                "content": chunk_text,
                "chunk_index": idx,
                "metadata": {
                    **metadata,
                    "total_chunks": len(chunks),
                },
            }
            chunk_dicts.append(chunk_dict)

        return chunk_dicts
