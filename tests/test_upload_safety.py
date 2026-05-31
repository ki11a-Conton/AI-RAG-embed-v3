from pathlib import Path

import pytest

from lib.upload_safety import find_upload_conflicts, save_uploaded_files


class UploadedFile:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getbuffer(self):
        return memoryview(self._content)


def test_find_upload_conflicts_only_returns_existing_names(tmp_path: Path):
    (tmp_path / "existing.md").write_text("old", encoding="utf-8")
    uploaded = [
        UploadedFile("existing.md", b"new"),
        UploadedFile("new.md", b"fresh"),
    ]

    assert find_upload_conflicts(str(tmp_path), uploaded) == ["existing.md"]


def test_save_uploaded_files_writes_all_files(tmp_path: Path):
    uploaded = [
        UploadedFile("a.md", b"alpha"),
        UploadedFile("b.md", b"beta"),
    ]

    saved_count = save_uploaded_files(str(tmp_path), uploaded)

    assert saved_count == 2
    assert (tmp_path / "a.md").read_bytes() == b"alpha"
    assert (tmp_path / "b.md").read_bytes() == b"beta"


def test_traversal_ignored_in_conflict_detection(tmp_path: Path):
    (tmp_path / "real.md").write_text("real", encoding="utf-8")
    uploaded = [
        UploadedFile("real.md", b"new"),
        UploadedFile("../outside.txt", b"hack"),
        UploadedFile("..", b"hack"),
        UploadedFile(r"..\outside.txt", b"hack"),
    ]

    assert find_upload_conflicts(str(tmp_path), uploaded) == ["real.md"]


def test_traversal_save_raises_valueerror(tmp_path: Path):
    uploaded = UploadedFile("../outside.txt", b"malicious")

    with pytest.raises(ValueError):
        save_uploaded_files(str(tmp_path), [uploaded])

    assert not (tmp_path.parent / "outside.txt").exists()
    assert not list(tmp_path.iterdir())


def test_windows_traversal_save_raises_valueerror(tmp_path: Path):
    uploaded = UploadedFile(r"..\outside.txt", b"malicious")

    with pytest.raises(ValueError):
        save_uploaded_files(str(tmp_path), [uploaded])

    assert not (tmp_path / r"..\outside.txt").exists()
    assert not list(tmp_path.iterdir())


def test_empty_filename_raises_valueerror(tmp_path: Path):
    uploaded = UploadedFile("", b"data")

    with pytest.raises(ValueError):
        save_uploaded_files(str(tmp_path), [uploaded])

    assert not list(tmp_path.iterdir())


def test_normal_filename_still_works(tmp_path: Path):
    uploaded = [UploadedFile("normal.md", b"hello")]

    saved_count = save_uploaded_files(str(tmp_path), uploaded)

    assert saved_count == 1
    assert (tmp_path / "normal.md").read_bytes() == b"hello"
    assert find_upload_conflicts(str(tmp_path), uploaded) == ["normal.md"]
