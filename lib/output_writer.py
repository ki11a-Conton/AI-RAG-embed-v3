import os
import re
import shutil
from datetime import datetime

from lib.config import PROJECT_DIR


def _sanitize_name(text: str, max_len: int = 60) -> str:
    name = text.strip().replace(" ", "_")
    name = re.sub(r"[^\w\-]", "", name)
    return name[:max_len]


def _cleanup_output_dirs(output_root: str, max_output_dirs: int) -> None:
    if max_output_dirs <= 0:
        return
    existing_dirs = sorted(
        (
            os.path.join(output_root, name)
            for name in os.listdir(output_root)
            if os.path.isdir(os.path.join(output_root, name))
        ),
        key=os.path.getmtime,
    )
    while len(existing_dirs) > max_output_dirs:
        shutil.rmtree(existing_dirs.pop(0))


def _init_output_dir(first_question: str, max_output_dirs: int = 50) -> str:
    output_root = os.path.join(PROJECT_DIR, "output")
    os.makedirs(output_root, exist_ok=True)
    prefix = _sanitize_name(first_question)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    dirpath = os.path.join(output_root, f"{prefix}_{stamp}")
    os.makedirs(dirpath, exist_ok=True)
    _cleanup_output_dirs(output_root, max_output_dirs)
    return dirpath


def _sanitize_chunk(text: str) -> str:
    text = text.strip("`")
    text = text.replace("```", "``")
    return text


def _format_source_citation(chunk: dict) -> str:
    source = chunk.get("source", "unknown")
    page = chunk.get("page")
    chunk_index = chunk.get("chunk_index")
    if page is not None:
        return f"[Source: {source}, Page {page}]"
    if chunk_index is not None:
        return f"[Source: {source}, Chunk {chunk_index}]"
    return f"[Source: {source}]"


def _get_enhance_label(query_enhancer) -> str:
    return getattr(query_enhancer, "label", "Enhanced Question")


def _export_round(
    out_dir: str,
    index: int,
    question: str,
    chunks: list[dict],
    answer: str,
    rewritten_question: str | None = None,
    enhance_label: str = "Enhanced Question",
) -> None:
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        citation = _format_source_citation(chunk)
        safe_text = _sanitize_chunk(chunk["text"] if isinstance(chunk, dict) else chunk)
        score_info = ""
        if isinstance(chunk, dict):
            dist = chunk.get("distance")
            rerank = chunk.get("rerank_score")
            if rerank is not None:
                score_info = f" | rerank_score={rerank}"
            elif dist is not None:
                score_info = f" | distance={dist}"
        context_blocks.append(
            f"**Chunk {i}** {citation}{score_info}\n\n```text\n{safe_text}\n```"
        )

    text = f"========== *Round {index}* ==========\n\n"
    text += f"**Question:**\n\n```text\n{question}\n```\n\n"
    if rewritten_question and rewritten_question != question:
        text += f"**{enhance_label}:**\n\n```text\n{rewritten_question}\n```\n\n"
    text += f"**Answer:**\n\n{answer}\n\n"
    text += "========== *Retrieved Context* ==========\n\n"
    text += "\n\n".join(context_blocks) + "\n"

    filepath = os.path.join(out_dir, f"{index:02d}_round.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
