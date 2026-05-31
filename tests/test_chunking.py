"""tests/test_chunking.py"""
from lib.doc_loader import split_text_by_paragraphs


def test_empty_string():
    chunks = split_text_by_paragraphs("", chunk_size=500, chunk_overlap=50)
    assert chunks == []


def test_whitespace_only():
    chunks = split_text_by_paragraphs("   \n\n   ", chunk_size=500, chunk_overlap=50)
    assert chunks == []


def test_single_paragraph():
    text = "这是一段内容，不超过 chunk_size。"
    chunks = split_text_by_paragraphs(text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0][0] == text


def test_chinese_text():
    text = "自动控制原理是工程学科的核心课程。\n\n它研究系统如何自动调节输出以达到期望目标。\n\n时间常数是描述系统响应速度的重要参数。"
    chunks = split_text_by_paragraphs(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 1
    # 确保内容都覆盖了
    joined = " ".join(c for c, _ in chunks)
    assert "时间常数" in joined


def test_chunk_size_respected():
    """每个 chunk 长度不应超过 chunk_size（兜底切分时）"""
    long_text = "x" * 5000
    chunk_size = 200
    chunks = split_text_by_paragraphs(long_text, chunk_size=chunk_size, chunk_overlap=20)
    for chunk_text, _ in chunks:
        assert len(chunk_text) <= chunk_size, f"Chunk 长度 {len(chunk_text)} 超过 chunk_size {chunk_size}"


def test_overlap_equal_to_chunk_size_no_infinite_loop():
    """Bug 回归：chunk_overlap >= chunk_size 时不应死循环"""
    long_text = "B" * 100
    chunks = split_text_by_paragraphs(long_text, chunk_size=20, chunk_overlap=20)
    assert len(chunks) > 0


def test_overlap_greater_than_chunk_size_no_infinite_loop():
    """Bug 回归：chunk_overlap > chunk_size 时不应死循环"""
    long_text = "C" * 100
    chunks = split_text_by_paragraphs(long_text, chunk_size=20, chunk_overlap=30)
    assert len(chunks) > 0


def test_repeated_paragraphs_correct_char_start():
    """Bug 回归：重复段落应获得正确的 char_start 而非首个匹配的位置。

    text = 'AAA\\n\\nBBB\\n\\nAAA\\n\\nCCC' 中第二个 'AAA' 的真实偏移是 10，
    使用 chunk_size=10 会强制将其与 'CCC' 合并为第二个块。
    """
    text = 'AAA\n\nBBB\n\nAAA\n\nCCC'
    chunks = split_text_by_paragraphs(text, chunk_size=10, chunk_overlap=0)
    # AAA\n\nBBB (8 chars), adding AAA (+3+2=13) exceeds 10 => two chunks
    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
    assert chunks[0][0] == 'AAA\n\nBBB'
    assert chunks[0][1] == 0
    assert chunks[1][0] == 'AAA\n\nCCC'
    assert chunks[1][1] == 10, f"Expected char_start=10, got {chunks[1][1]}"
