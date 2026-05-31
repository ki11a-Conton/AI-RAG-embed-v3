"""Hybrid retrieval helpers – RRF fusion of vector + BM25 results."""


def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    top_n: int,
    k: int = 60,
) -> list[dict]:
    """Fuse two ranked lists with Reciprocal Rank Fusion.

    Builds a stable identity from ``(source, chunk_index)`` when
    available, then ``(source, page)``, and finally ``(source, text)``.

    Chunks that appear in *both* lists receive a higher combined score
    because they contribute ``1/(k+rank)`` from each list.

    Parameters
    ----------
    vector_results : list[dict]
        Chunks from the vector store (already ranked by distance).
    bm25_results : list[dict]
        Chunks from the BM25 index (already ranked by BM25 score).
    top_n : int
        Number of chunks to return after fusion.
    k : int
        RRF smoothing constant (default 60, standard choice).

    Returns
    -------
    list[dict]
        Fused chunks, each a shallow copy with an added ``rrf_score``
        field.  Overlapping chunks rank higher.
    """
    if top_n <= 0:
        return []

    # ── stable identity ──────────────────────────────────────
    def _identity(chunk: dict):
        source = chunk.get("source", "unknown")
        ci = chunk.get("chunk_index")
        page = chunk.get("page")
        # Prefer source+chunk_index; page can differ between loaders while the
        # chunk identity remains the same.
        if ci is not None:
            return ("ci", source, ci)
        if page is not None:
            return ("pg", source, page)
        # Last resort: (source, text)
        return ("txt", source, chunk.get("text", ""))

    rrf_scores: dict[tuple, float] = {}
    chunk_map: dict[tuple, dict] = {}

    for rank, chunk in enumerate(vector_results, start=1):
        ident = _identity(chunk)
        rrf_scores[ident] = rrf_scores.get(ident, 0.0) + 1.0 / (k + rank)
        chunk_map.setdefault(ident, chunk)

    for rank, chunk in enumerate(bm25_results, start=1):
        ident = _identity(chunk)
        rrf_scores[ident] = rrf_scores.get(ident, 0.0) + 1.0 / (k + rank)
        chunk_map.setdefault(ident, chunk)

    # sort by RRF score descending
    sorted_ids = sorted(rrf_scores, key=lambda i: rrf_scores[i], reverse=True)

    result: list[dict] = []
    for ident in sorted_ids[:top_n]:
        merged = dict(chunk_map[ident])          # shallow copy
        merged["rrf_score"] = rrf_scores[ident]
        result.append(merged)

    return result
