"""MCP server for read-only RAG knowledge base search.

Usage:
    python mcp_server.py

This starts a stdio-based MCP server exposing the ``search_knowledge_base`` tool.
Clients (e.g. Claude Desktop, VS Code extension) can invoke it to retrieve
relevant chunks from the RAG index.
"""
from __future__ import annotations

import contextlib
import sys

from mcp.server.fastmcp import FastMCP

from lib.config import load_config
from lib.output_writer import _format_source_citation
from lib.pipeline import _init_search_system, _retrieve_context_chunks

# MCP server instance

mcp = FastMCP(
    "rag-knowledge-base",
    instructions="Search the RAG knowledge base for relevant document chunks.",
)

# Lazy-loaded component cache (avoids re-initialising on every call)

_components: tuple | None = None


def _get_components() -> tuple:
    """Return (store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index, config)."""
    global _components
    if _components is None:
        config = load_config()
        with contextlib.redirect_stdout(sys.stderr):
            store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = _init_search_system(config)
        _components = (store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index, config)
    return _components


# Helper: format chunk list into a readable string


def _format_chunks(
    question: str,
    chunks: list[dict],
    rewritten_question: str | None = None,
) -> str:
    """Format retrieved chunks into a human-readable string with citations."""
    lines: list[str] = [f"Question: {question}"]
    if rewritten_question and rewritten_question != question:
        lines.append(f"Enhanced query: {rewritten_question}")
    lines.append(f"Found {len(chunks)} chunk(s):\n")

    for i, chunk in enumerate(chunks, 1):
        citation = _format_source_citation(chunk)
        lines.append(f"--- Chunk {i} ---")
        lines.append(citation)
        lines.append(chunk.get("text", ""))
        rp = chunk.get("retrieval_path")
        if rp:
            lines.append(f"(retrieval path: {rp})")
        lines.append("")

    return "\n".join(lines)


# Read-only MCP tool


@mcp.tool(description="Search the RAG knowledge base for relevant chunks by question.")
def search_knowledge_base(question: str) -> str:
    """Retrieve relevant context chunks for a given question.

    Parameters
    ----------
    question : str
        The search question or query string.

    Returns
    -------
    str
        Formatted text with relevant chunks and source citations, or a
        message indicating no content was found.
    """
    if not question or not question.strip():
        return "Please provide a non-empty question."

    store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index, config = _get_components()

    with contextlib.redirect_stdout(sys.stderr):
        chunks, rewritten_question = _retrieve_context_chunks(
            store,
            question.strip(),
            config,
            query_enhancer=query_enhancer,
            messages_history=None,
            reranker=reranker,
            bm25_index=bm25_index,
            parent_store=parent_store,
            multi_query_enhancer=multi_query_enhancer,
        )

    if not chunks:
        return f"No relevant content found for: {question}"

    return _format_chunks(question, chunks, rewritten_question)


# CLI entry point


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
