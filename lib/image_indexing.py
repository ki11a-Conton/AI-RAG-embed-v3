"""Image captioning and optional CLIP image-index helpers."""

import time

from lib.doc_loader import load_document_images
from lib.logger import get_logger
from lib.pipeline import _clip_image_enabled

logger = get_logger(__name__)


def _init_image_captioner(config: dict):
    if not config.get("image_caption_enabled", False):
        return None

    from lib.image_captioner import ImageCaptioner

    try:
        nested = config.get("image_caption", {})
        return ImageCaptioner(
            api_key=config.get("image_caption_api_key") or nested.get("api_key", ""),
            base_url=config.get(
                "image_caption_api_base_url",
                nested.get("api_base_url", "https://api.openai.com/v1"),
            ) or nested.get("api_base_url", "https://api.openai.com/v1"),
            model=config.get("image_caption_model") or nested.get("model", "gpt-4o-mini"),
        )
    except Exception as exc:
        logger.warning("Failed to initialize image captioner: %s", exc)
        return None


def _rebuild_clip_image_index(config: dict, docs_dir: str, persist_dir: str) -> None:
    if not _clip_image_enabled(config):
        return

    from lib.embed_engine import CLIPEmbedEngine
    from lib.image_vector_db import ImageVectorDb

    print(">> Loading document images for CLIP... ", end="", flush=True)
    t0 = time.perf_counter()
    image_records = load_document_images(docs_dir)
    print(
        f"\r\033[K>> Loaded {len(image_records)} document images"
        f"  [{time.perf_counter() - t0:.1f}s]"
    )

    print(">> Building CLIP image index... ", end="", flush=True)
    t1 = time.perf_counter()
    clip_engine = CLIPEmbedEngine(
        model_name=config.get("clip_model_name", "openai/clip-vit-base-patch32")
    )
    image_store = ImageVectorDb(persist_dir=persist_dir, embed_engine=clip_engine)
    image_store.rebuild(image_records)
    print(
        f"\r\033[K>> Building CLIP image index... done"
        f"  [{time.perf_counter() - t1:.1f}s]"
    )
