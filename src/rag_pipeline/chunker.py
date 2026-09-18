import uuid
import copy
import re
from typing import List, Dict, Optional

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    metadata: Optional[Dict] = None
) -> List[Dict]:
    """
    Splits text into sliding-window chunks preserving paragraph and sentence boundaries
    (\\n\\n, \\n, ., ?, !) so sentences are not sliced mid-word or mid-thought.

    Args:
        text (str): The input text to chunk.
        chunk_size (int): The maximum size of each chunk in characters (default: 1000).
        chunk_overlap (int): The number of overlapping characters between chunks (default: 150).
        metadata (dict): Optional metadata to attach to each chunk.

    Returns:
        List[Dict]: List of chunks with 'chunk_id', 'text', and 'metadata'.
    """
    if not text or not text.strip():
        return []

    if metadata is None:
        metadata = {}

    # Normalize line endings
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split preserving paragraph breaks (\n\n), line breaks (\n), and sentence boundaries (.?! followed by whitespace)
    # Using capturing parentheses keeps delimiters in the resulting list
    boundary_pattern = r'(\n\n+|\n|(?<=[.?!])\s+)'
    raw_segments = re.split(boundary_pattern, normalized)

    # Sub-split any segment exceeding chunk_size by words/whitespace
    segments = []
    for seg in raw_segments:
        if not seg:
            continue
        if len(seg) > chunk_size:
            # Word-level fallback for segments longer than chunk_size
            word_pieces = re.split(r'(\s+)', seg)
            segments.extend(p for p in word_pieces if p)
        else:
            segments.append(seg)

    chunks = []
    i = 0
    n = len(segments)
    chunk_index = 0

    while i < n:
        # Skip leading whitespace segments at the start of a chunk
        while i < n and segments[i].strip() == "":
            i += 1
        if i >= n:
            break

        current_segments = []
        current_length = 0
        j = i

        while j < n:
            seg = segments[j]
            seg_len = len(seg)
            # If adding this segment would exceed chunk_size and we already have some text
            if current_length + seg_len > chunk_size and current_segments:
                break
            current_segments.append(seg)
            current_length += seg_len
            j += 1

        chunk_content = "".join(current_segments).strip()
        if chunk_content:
            chunk_meta = copy.deepcopy(metadata)
            chunk_meta["chunk_index"] = chunk_index
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_content,
                "metadata": chunk_meta
            })
            chunk_index += 1

        if j >= n:
            break

        # Calculate overlap for the next chunk: backtrack from j towards i
        overlap_length = 0
        next_i = j
        k = j - 1
        while k >= i:
            seg_len = len(segments[k])
            if overlap_length + seg_len <= chunk_overlap:
                overlap_length += seg_len
                next_i = k
                k -= 1
            else:
                break

        # Ensure forward progress: next_i must strictly advance past i
        if next_i <= i:
            next_i = i + 1

        i = next_i

    return chunks


class TextChunker:
    """TextChunker class wrapper for configurable boundary-aware chunking."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        return chunk_text(text, self.chunk_size, self.chunk_overlap, metadata)
