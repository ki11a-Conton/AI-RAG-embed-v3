import os
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

_QUERY_PREFIXES = {
    "mxbai": "Represent this sentence for searching relevant passages: ",
    "bge": "Represent this sentence for searching relevant passages: ",
    "e5": "query: ",
}


def _get_query_prefix(model_name: str) -> str:
    name = model_name.lower()
    for key, prefix in _QUERY_PREFIXES.items():
        if key in name:
            return prefix
    return ""


def _get_cached_model_path(model_name: str) -> str | None:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    repo_cache = cache_root / ("models--" + model_name.replace("/", "--"))
    snapshots_dir = repo_cache / "snapshots"
    if not snapshots_dir.is_dir():
        return None
    snapshots = [
        path for path in snapshots_dir.iterdir()
        if path.is_dir() and (path / "config.json").exists()
    ]
    if not snapshots:
        return None
    newest = max(snapshots, key=lambda path: path.stat().st_mtime)
    return str(newest)


class EmbedEngine:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._query_prefix = _get_query_prefix(model_name)
        model_path = _get_cached_model_path(model_name) or model_name
        self._model = SentenceTransformer(model_path)

    # 查询向量：按模型系列选择 query prefix，未知模型不加
    def get_embedding(self, text: str) -> list[float]:
        return self._model.encode(self._query_prefix + text).tolist()

    # 文档向量：不加 prefix
    def embed_documents(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        return self._model.encode(
            texts, batch_size=batch_size, show_progress_bar=False
        ).tolist()

    # 保留旧名兼容
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)


class CLIPEmbedEngine:
    """Standalone, optional local CLIP embedding engine.

    Lazily imports ``transformers`` and ``PIL`` so that the heavy
    dependencies are only loaded on first use.  Designed to be fully
    mockable: patch ``transformers.CLIPModel`` / ``CLIPProcessor``
    and ``PIL.Image`` before calling any embed method.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self._model = None
        self._processor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self):
        """Lazy-load the CLIP model and processor on first call."""
        if self._model is not None:
            return
        from transformers import CLIPModel, CLIPProcessor

        self._model = CLIPModel.from_pretrained(self.model_name)
        self._processor = CLIPProcessor.from_pretrained(self.model_name)
        self._model.eval()

    @staticmethod
    def _l2_normalize(tensor) -> "torch.Tensor":
        import torch

        return tensor / tensor.norm(dim=-1, keepdim=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Encode raw image bytes into a unit-norm CLIP embedding.

        Returns a plain Python ``list[float]``.
        """
        self._ensure_loaded()

        from PIL import Image
        import io
        import torch

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt")
        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
        image_features = self._l2_normalize(image_features)
        return image_features.squeeze().tolist()

    def embed_text(self, text: str) -> list[float]:
        """Encode a text string into a unit-norm CLIP embedding.

        Returns a plain Python ``list[float]``.
        """
        self._ensure_loaded()

        import torch

        inputs = self._processor(text=text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            text_features = self._model.get_text_features(**inputs)
        text_features = self._l2_normalize(text_features)
        return text_features.squeeze().tolist()
