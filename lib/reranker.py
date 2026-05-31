"""
reranker.py
基于 CrossEncoder 的重排序模块（可选）。
在向量检索 top-k 之后，用 reranker 对结果重新评分并取 top-n，提高检索质量。

推荐模型：
- BAAI/bge-reranker-base  （中英混合）
- BAAI/bge-reranker-large （精度更高，更慢）
"""


class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError("请安装 sentence-transformers：pip install sentence-transformers")

        print(f">> Loading reranker model: {model_name} ...", end="", flush=True)
        self.model = CrossEncoder(model_name)
        print(" done")

    def rerank(
        self, query: str, items: list[dict], top_n: int = 5, translated_query: str | None = None
    ) -> list[dict]:
        """
        对检索结果重新评分并排序，返回 top_n 个结果。

        Args:
            query: 用户原始问题
            items: VectorDb.query() 返回的结果列表
            top_n: 返回数量
            translated_query: 增强/翻译后的问题（若提供则用于 CrossEncoder 评分，
                              否则使用原始 query）

        Returns:
            重排序后的结果（已加入 rerank_score 字段）
        """
        if not items:
            return []

        score_query = translated_query if translated_query else query
        pairs = [(score_query, item["text"]) for item in items]
        scores = self.model.predict(pairs)

        for item, score in zip(items, scores):
            item["rerank_score"] = round(float(score), 4)

        items = sorted(items, key=lambda x: x["rerank_score"], reverse=True)
        return items[:top_n]
