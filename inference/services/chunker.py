"""Chunking service using LlamaIndex for semantic and recursive splitting."""

import os
from typing import List, Optional, Tuple

from ..models.classification import ChunkMetadata


class ChunkingService:
    """Service for splitting long text into manageable chunks."""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the chunking service.
        
        Args:
            config: Optional configuration dict. Falls back to environment variables.
        """
        config = config or {}
        
        self.strategy = os.getenv(
            "CHUNKING_STRATEGY",
            config.get("strategy", "semantic")
        )
        self.max_chunk_size = int(os.getenv(
            "CHUNKING_MAX_SIZE",
            config.get("max_chunk_size", 4096)
        ))
        self.overlap = int(os.getenv(
            "CHUNKING_OVERLAP",
            config.get("overlap", 200)
        ))
        self.threshold = int(os.getenv(
            "CHUNKING_THRESHOLD",
            config.get("threshold_tokens", 8000)
        ))
        
        # Lazy-load parsers to avoid import overhead
        self._semantic_parser = None
        self._recursive_parser = None
    
    def _get_semantic_parser(self):
        """Lazy-load the semantic splitter."""
        if self._semantic_parser is None:
            from llama_index.core.node_parser import SemanticSplitterNodeParser
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            
            embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._semantic_parser = SemanticSplitterNodeParser(
                buffer_size=1,
                breakpoint_percentile_threshold=95,
                embed_model=embed_model
            )
        return self._semantic_parser
    
    def _get_recursive_parser(self):
        """Lazy-load the recursive sentence splitter."""
        if self._recursive_parser is None:
            from llama_index.core.node_parser import SentenceSplitter
            
            self._recursive_parser = SentenceSplitter(
                chunk_size=self.max_chunk_size,
                chunk_overlap=self.overlap
            )
        return self._recursive_parser
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        Uses a simple heuristic of ~4 characters per token.
        
        Args:
            text: The text to estimate.
            
        Returns:
            Estimated token count.
        """
        return len(text) // 4
    
    def should_chunk(self, text: str) -> bool:
        """
        Determine if text needs chunking based on token count.
        
        Args:
            text: The text to check.
            
        Returns:
            True if chunking is recommended.
        """
        return self.estimate_tokens(text) > self.threshold
    
    def chunk(self, text: str) -> Tuple[List[str], List[ChunkMetadata]]:
        """
        Split text into chunks using the configured strategy.
        
        Args:
            text: The text to chunk.
            
        Returns:
            Tuple of (list of chunk texts, list of chunk metadata).
        """
        from llama_index.core import Document
        
        doc = Document(text=text)
        
        # Select parser based on strategy
        if self.strategy == "semantic":
            parser = self._get_semantic_parser()
        else:
            parser = self._get_recursive_parser()
        
        nodes = parser.get_nodes_from_documents([doc])
        
        chunks = []
        metadata = []
        
        # Track character positions
        current_pos = 0
        
        for i, node in enumerate(nodes):
            chunk_text = node.text
            chunks.append(chunk_text)
            
            # Find actual position in original text
            start_pos = text.find(chunk_text[:50], current_pos)  # Use first 50 chars to find
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)
            
            metadata.append(ChunkMetadata(
                chunk_index=i,
                total_chunks=len(nodes),
                start_char=start_pos,
                end_char=end_pos,
                token_estimate=self.estimate_tokens(chunk_text)
            ))
            
            current_pos = end_pos
        
        return chunks, metadata
    
    def chunk_simple(self, text: str) -> List[str]:
        """
        Simple chunking that returns only the text chunks.
        
        Args:
            text: The text to chunk.
            
        Returns:
            List of chunk texts.
        """
        chunks, _ = self.chunk(text)
        return chunks
    
    def set_strategy(self, strategy: str) -> None:
        """
        Change the chunking strategy at runtime.
        
        Args:
            strategy: Either 'semantic' or 'recursive'.
        """
        if strategy not in ("semantic", "recursive"):
            raise ValueError(f"Invalid strategy: {strategy}. Use 'semantic' or 'recursive'.")
        self.strategy = strategy
