"""
image_captioner.py
Optional image-captioning client that uses an OpenAI-compatible vision model
to describe embedded images extracted from PDF / DOCX files.

Does **not** log or persist secrets.  The underlying ``openai.OpenAI`` client is
exposed as ``_client`` so tests can replace it with a mock without touching
the network.
"""
import base64


class ImageCaptioner:
    """Caption images via an OpenAI-compatible chat-completions vision model.

    Parameters
    ----------
    api_key : str
        API key for the provider.
    base_url : str
        Base URL of the chat-completions endpoint (e.g. ``https://api.openai.com/v1``).
    model : str
        Vision-capable model name (e.g. ``gpt-4o-mini``).
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        import openai as _openai

        # The raw key is consumed by the client constructor and **not** stored
        # separately, so it can never appear in logs, repr(), or error traces.
        self._client = _openai.OpenAI(api_key=api_key, base_url=base_url)
        self._model = model  # type: str

    def caption(self, image_bytes: bytes, context_hint: str = "") -> str:
        """Return a text description of *image_bytes*.

        Parameters
        ----------
        image_bytes : bytes
            Raw bytes of the image (PNG / JPEG / GIF / WebP / …).
        context_hint : str
            Optional hint prepended to the user prompt, e.g. surrounding
            page text or document name.

        Returns
        -------
        str
            The model's caption text, or an empty string if the response
            is empty.
        """
        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"

        system_text = (
            "You are an image captioning assistant. "
            "Describe the image accurately and concisely, "
            "including any text, data, or visual elements visible in the image."
        )
        user_text = "Please describe this image in detail."
        if context_hint:
            user_text = f"Context: {context_hint}\n\n{user_text}"

        messages = [
            {"role": "system", "content": system_text},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        content = response.choices[0].message.content
        return content or ""

    def __repr__(self) -> str:
        return f"ImageCaptioner(model={self._model!r})"
