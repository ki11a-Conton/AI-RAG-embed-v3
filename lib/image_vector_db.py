"""Separate Chroma collection for CLIP image embeddings."""
import chromadb
from chromadb.config import Settings


class ImageVectorDb:
    """Store and query CLIP image embeddings in an isolated collection."""

    def __init__(
        self,
        persist_dir: str,
        embed_engine,
        collection_name: str = "clip_images",
    ):
        self._embed_engine = embed_engine
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _safe_metadata(record: dict, index: int) -> dict:
        meta = record.get("metadata", {})
        page = meta.get("page")
        return {
            "source": meta.get("source", "unknown"),
            "file_type": meta.get("file_type", "clip_image"),
            "page": page if page is not None else -1,
            "image_index": meta.get("image_index", index),
        }

    @staticmethod
    def _document_for(record: dict, meta: dict) -> str:
        if record.get("text"):
            return record["text"]
        source = meta.get("source", "unknown")
        image_index = meta.get("image_index", 0)
        page = meta.get("page")
        if page == -1:
            return f"Image {image_index} from {source}"
        return f"Image {image_index} from {source}, page {page}"

    def rebuild(self, image_records: list[dict]) -> None:
        """Rebuild the image embedding collection from image byte records."""
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        if not image_records:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        embeddings: list[list[float]] = []

        for index, record in enumerate(image_records):
            image_bytes = record.get("image_bytes")
            if not image_bytes:
                continue

            meta = self._safe_metadata(record, index)
            ids.append(str(index))
            metadatas.append(meta)
            documents.append(self._document_for(record, meta))
            embeddings.append(self._embed_engine.embed_image(image_bytes))

        if ids:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

    def query(self, question: str, k: int = 3) -> list[dict]:
        if k <= 0:
            return []
        total = self._collection.count()
        if total == 0:
            return []

        n = min(k, total)
        query_embedding = self._embed_engine.embed_text(question)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output = []
        for doc, meta, distance in zip(docs, metas, distances):
            meta = meta or {}
            page = meta.get("page")
            if page == -1:
                page = None
            output.append(
                {
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "file_type": meta.get("file_type", "clip_image"),
                    "page": page,
                    "image_index": meta.get("image_index"),
                    "chunk_index": None,
                    "distance": round(float(distance), 4),
                    "retrieval_path": "clip_image",
                }
            )

        return output

    def count(self) -> int:
        return self._collection.count()
