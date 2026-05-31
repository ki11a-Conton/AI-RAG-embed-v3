import os


def _validate_filename(name: str, docs_dir: str) -> str:
    """Validate that *name* is a safe filename to join with *docs_dir*.

    Raises ``ValueError`` if *name* is empty, is ``.`` or ``..``,
    contains any path-separator character (``/`` or ``\\``), or would
    resolve to a location outside *docs_dir*.

    Returns the joined save path when valid.
    """
    if not name:
        raise ValueError("Empty filename is not allowed")
    if name in (".", ".."):
        raise ValueError(f"Invalid filename: {name!r}")
    if "/" in name or "\\" in name:
        raise ValueError(
            f"Filename must not contain path components: {name!r}"
        )
    # Defense in depth: verify that the resolved absolute path stays
    # inside docs_dir.
    save_path = os.path.join(docs_dir, name)
    resolved = os.path.abspath(save_path)
    docs_abs = os.path.abspath(docs_dir)
    if os.path.commonpath([docs_abs, resolved]) != docs_abs:
        raise ValueError(f"Filename resolves outside docs_dir: {name!r}")
    return save_path


def find_upload_conflicts(docs_dir: str, uploaded_files) -> list[str]:
    conflicts = []
    for uploaded in uploaded_files:
        try:
            _validate_filename(uploaded.name, docs_dir)
        except ValueError:
            continue  # ignore invalid names (silently skip)
        save_path = os.path.join(docs_dir, uploaded.name)
        if os.path.exists(save_path):
            conflicts.append(uploaded.name)
    return conflicts


def save_uploaded_files(docs_dir: str, uploaded_files) -> int:
    saved_count = 0
    for uploaded in uploaded_files:
        save_path = _validate_filename(uploaded.name, docs_dir)
        with open(save_path, "wb") as out:
            out.write(uploaded.getbuffer())
        saved_count += 1
    return saved_count
