from lib.image_vector_db import ImageVectorDb


class FakeClipEngine:
    def __init__(self):
        self.image_calls = []
        self.text_calls = []

    def embed_image(self, image_bytes: bytes) -> list[float]:
        self.image_calls.append(image_bytes)
        if image_bytes == b"chart":
            return [1.0, 0.0]
        return [0.0, 1.0]

    def embed_text(self, text: str) -> list[float]:
        self.text_calls.append(text)
        return [1.0, 0.0]


def _records():
    return [
        {
            "image_bytes": b"chart",
            "text": "Image from report.pdf, page 2",
            "metadata": {
                "source": "report.pdf",
                "file_type": "clip_image",
                "page": 2,
                "image_index": 0,
            },
        },
        {
            "image_bytes": b"diagram",
            "text": "Image from notes.docx",
            "metadata": {
                "source": "notes.docx",
                "file_type": "clip_image",
                "page": None,
                "image_index": 1,
            },
        },
    ]


def test_image_vector_db_rebuild_and_query(tmp_path):
    engine = FakeClipEngine()
    db = ImageVectorDb(str(tmp_path), engine)

    db.rebuild(_records())
    results = db.query("find the chart", k=1)

    assert db.count() == 2
    assert engine.image_calls == [b"chart", b"diagram"]
    assert engine.text_calls == ["find the chart"]
    assert len(results) == 1
    assert results[0]["source"] == "report.pdf"
    assert results[0]["file_type"] == "clip_image"
    assert results[0]["page"] == 2
    assert results[0]["image_index"] == 0
    assert results[0]["retrieval_path"] == "clip_image"


def test_image_vector_db_empty_rebuild_clears_collection(tmp_path):
    engine = FakeClipEngine()
    db = ImageVectorDb(str(tmp_path), engine)

    db.rebuild(_records())
    assert db.count() == 2

    db.rebuild([])
    assert db.count() == 0
    assert db.query("anything", k=3) == []


def test_image_vector_db_query_invalid_k_skips_embedding(tmp_path):
    engine = FakeClipEngine()
    db = ImageVectorDb(str(tmp_path), engine)
    db.rebuild(_records())

    assert db.query("anything", k=0) == []
    assert engine.text_calls == []
