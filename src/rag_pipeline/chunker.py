import uuid
import copy
from typing import List, Dict, Optional

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50, metadata: Optional[Dict] = None) -> List[Dict]:
    """
    Splits text into sliding-window chunks respecting word boundaries where possible.

    Args:
        text (str): The input text to chunk.
        chunk_size (int): The maximum size of each chunk in characters.
        chunk_overlap (int): The number of overlapping characters between chunks.
        metadata (dict): Optional metadata to attach to each chunk.

    Returns:
        list[dict]: List of chunks with 'chunk_id', 'text', and 'metadata'.
    """
    if not text:
        return []

    if metadata is None:
        metadata = {}

    words = text.split()
    chunks = []
    
    current_chunk = []
    current_length = 0

    word_idx = 0
    chunk_index = 0
    while word_idx < len(words):
        word = words[word_idx]
        word_len = len(word)
        
        if current_length + word_len + (1 if current_chunk else 0) <= chunk_size:
            current_chunk.append(word)
            current_length += word_len + (1 if current_chunk else 0)
            word_idx += 1
        else:
            if not current_chunk:
                # Word itself is larger than chunk_size, force it in
                current_chunk.append(word)
                word_idx += 1
                
            chunk_content = " ".join(current_chunk)
            chunk_meta = copy.deepcopy(metadata)
            chunk_meta["chunk_index"] = chunk_index
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_content,
                "metadata": chunk_meta
            })
            chunk_index += 1
            
            # Start new chunk with overlap
            overlap_words = []
            overlap_length = 0
            for w in reversed(current_chunk):
                if overlap_length + len(w) + (1 if overlap_words else 0) <= chunk_overlap:
                    overlap_words.insert(0, w)
                    overlap_length += len(w) + (1 if overlap_words else 0)
                else:
                    break
            
            current_chunk = overlap_words
            current_length = sum(len(w) for w in current_chunk) + max(0, len(current_chunk) - 1)

    if current_chunk:
        chunk_content = " ".join(current_chunk)
        chunk_meta = copy.deepcopy(metadata)
        chunk_meta["chunk_index"] = chunk_index
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "text": chunk_content,
            "metadata": chunk_meta
        })

    return chunks


class TextChunker:
    """TextChunker class wrapper for configurable chunking."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        return chunk_text(text, self.chunk_size, self.chunk_overlap, metadata)
