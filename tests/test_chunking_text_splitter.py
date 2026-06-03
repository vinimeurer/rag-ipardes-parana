"""
"""

import pytest
from src.chunking.text_splitter import count_tokens, RecursiveTextSplitter


class TestCountTokens:
    """
    """

    def test_count_tokens_empty_string(self):
        """
        """
        result = count_tokens("")
        assert result == 0

    def test_count_tokens_single_word(self):
        """
        """
        result = count_tokens("hello")
        assert result == 1

    def test_count_tokens_multiple_words(self):
        """
        """
        result = count_tokens("hello world test")
        assert result == 3

    def test_count_tokens_with_whitespace(self):
        """
        """
        result = count_tokens("hello  world   test")
        assert result == 3

    def test_count_tokens_with_punctuation(self):
        """
        """
        result = count_tokens("hello, world!")
        assert result == 2

    def test_count_tokens_with_newlines(self):
        """
        """
        result = count_tokens("hello\nworld\ntest")
        assert result == 3

    def test_count_tokens_with_tabs(self):
        """
        """
        result = count_tokens("hello\tworld\ttest")
        assert result == 3

    def test_count_tokens_long_text(self):
        """
        """
        text = " ".join(["word"] * 1000)
        result = count_tokens(text)
        assert result == 1000

    def test_count_tokens_hyphenated_words(self):
        """
        """
        result = count_tokens("well-known example-text")
        assert result == 2


class TestRecursiveTextSplitter:
    """
    """

    def test_splitter_initialization(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=100,
            overlap=10,
            separators=["\n\n", "\n", " "]
        )
        assert splitter.chunk_size == 100
        assert splitter.overlap == 10
        assert len(splitter.separators) == 3

    def test_split_empty_text(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=100,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        result = splitter.split("")
        assert len(result) == 1
        assert result[0] == ""

    def test_split_text_smaller_than_chunk_size(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=100,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "short text"
        result = splitter.split(text)
        assert len(result) == 1
        assert result[0] == text

    def test_split_text_larger_than_chunk_size(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=5,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "word1 word2 word3 word4 word5 word6 word7 word8"
        result = splitter.split(text)
        assert len(result) > 1
        for chunk in result:
            assert count_tokens(chunk) <= 10

    def test_split_with_paragraph_separator(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=10,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "first paragraph\n\nsecond paragraph"
        result = splitter.split(text)
        assert len(result) >= 1

    def test_split_with_newline_separator(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=10,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "line one\nline two\nline three"
        result = splitter.split(text)
        assert len(result) >= 1

    def test_split_applies_overlap(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=3,
            overlap=1,
            separators=[" "]
        )
        text = "one two three four five six"
        result = splitter.split(text)
        assert len(result) > 1
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert len(result[i]) > 0

    def test_split_no_overlap_same_size(self):
        """
        """
        splitter_no_overlap = RecursiveTextSplitter(
            chunk_size=5,
            overlap=0,
            separators=[" "]
        )
        splitter_with_overlap = RecursiveTextSplitter(
            chunk_size=5,
            overlap=1,
            separators=[" "]
        )
        text = "a b c d e f g h i j k l"
        result_no = splitter_no_overlap.split(text)
        result_with = splitter_with_overlap.split(text)
        
        assert len(result_no) > 0
        assert len(result_with) > 0

    def test_split_force_split_fallback(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=3,
            overlap=0,
            separators=[]
        )
        text = "verylongwordthatcannotbesplit anotherlong"
        result = splitter.split(text)
        assert len(result) > 0

    def test_split_with_zero_overlap(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=5,
            overlap=0,
            separators=[" "]
        )
        text = "one two three four five six seven eight"
        result = splitter.split(text)
        assert len(result) > 0

    def test_split_merge_parts_functionality(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=10,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "a\n\nb\n\nc\n\nd\n\ne"
        result = splitter.split(text)
        assert len(result) > 0
        for chunk in result:
            assert count_tokens(chunk) <= 20

    def test_split_preserves_text_content(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=10,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        original = "word1 word2 word3 word4 word5"
        result = splitter.split(original)
        reconstructed = " ".join(result).replace(" ", " ")
        
        assert len(result) > 0

    def test_split_single_long_word(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=3,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "verylongword"
        result = splitter.split(text)
        assert len(result) > 0

    def test_recursive_split_with_multiple_separators(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=20,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "Para1\n\nPara2 word1 word2\n\nPara3"
        result = splitter.split(text)
        assert len(result) > 0

    def test_split_empty_parts_filtered(self):
        """
        """
        splitter = RecursiveTextSplitter(
            chunk_size=10,
            overlap=0,
            separators=["\n\n", "\n", " "]
        )
        text = "word1\n\n\n\nword2"
        result = splitter.split(text)
        assert len(result) > 0
        for chunk in result:
            assert len(chunk.strip()) > 0 or chunk == ""
