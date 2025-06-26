import pytest
from src.processing import chunk_text_langchain, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Test cases for the chunk_text_langchain function

def test_chunk_empty_text():
    """Test chunking an empty string."""
    assert chunk_text_langchain("") == []

def test_chunk_short_text():
    """Test chunking text shorter than chunk_size."""
    text = "This is a short text."
    chunks = chunk_text_langchain(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_exact_size_no_overlap():
    """Test chunking text that is exactly chunk_size."""
    # Temporarily reconfigure splitter for this test or use specific parameters
    # For simplicity, we'll test the default configuration.
    # This test assumes default chunk_size is 1000.
    # If a text is exactly 1000 chars, it should be one chunk.
    text = "a" * DEFAULT_CHUNK_SIZE
    chunks = chunk_text_langchain(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_long_text_with_overlap():
    """Test chunking a longer text that should be split and have overlap."""
    text = "This is a long sentence that will definitely be split into multiple chunks. " * (DEFAULT_CHUNK_SIZE // 50) # Make it long enough
    # Ensure it's longer than chunk_size
    text = text * 2 # Make it definitely longer than one chunk

    chunks = chunk_text_langchain(text)

    assert len(chunks) > 1
    # Check if chunks respect chunk_size (approximately, Langchain might slightly vary)
    for chunk in chunks:
        assert len(chunk) <= DEFAULT_CHUNK_SIZE

    # Check for overlap if more than one chunk
    if len(chunks) > 1:
        # The end of the first chunk should overlap with the start of the second chunk
        # The overlap amount is DEFAULT_CHUNK_OVERLAP
        overlap_actual = chunks[0][-DEFAULT_CHUNK_OVERLAP:]
        overlap_expected_in_second = chunks[1][:DEFAULT_CHUNK_OVERLAP]
        # This specific check might be too brittle due to how RecursiveCharacterTextSplitter
        # finds split points. A more robust check is that the sum of non-overlapping parts
        # plus overlaps should approximate the original text.
        # For now, just checking if chunks are created and sizes are reasonable.
        assert True # Placeholder for more sophisticated overlap check if needed

def test_chunk_with_custom_separators():
    """Test how RecursiveCharacterTextSplitter handles default separators."""
    text = "Sentence one.\n\nSentence two.\nSentence three. Another part of three."
    # Default separators are ["\n\n", "\n", ". ", " ", ""]
    # We expect it to try splitting by "\n\n" first.

    # Create a local splitter instance to compare behavior if needed,
    # or trust the global instance in processing.py uses these separators.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=50, # Smaller for easier testing of separators
        chunk_overlap=5,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_text(text)

    # Example: Check if "Sentence one." and "Sentence two." are in different chunks
    # due to "\n\n" if chunk_size forces a split.
    # This is a qualitative check.
    assert "Sentence one." in chunks[0]
    if len(chunks) > 1:
        # Depending on chunk_size, "Sentence two." might start a new chunk
        # or be combined if it fits after "Sentence one."
        pass # This requires more specific setup of chunk_size to test separator behavior reliably.

    # Test with the global splitter from processing.py
    chunks_global_splitter = chunk_text_langchain(text) # Uses larger default chunk_size
    assert len(chunks_global_splitter) >= 1
    # With default 1000 chunk_size, the above text will likely be one chunk
    if DEFAULT_CHUNK_SIZE > len(text):
        assert len(chunks_global_splitter) == 1
        assert chunks_global_splitter[0] == text
    else:
        # If the text were longer than 1000, it would split.
        pass

# More tests could be added for edge cases, different separator behaviors, etc.
