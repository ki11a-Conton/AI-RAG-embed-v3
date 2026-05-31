import time

from openai import OpenAI

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # 秒


class LlmApi:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.3,
        thinking_mode: bool = False,
        timeout: int = 60,
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._thinking_mode = thinking_mode
        self._timeout = timeout

    def generate(self, messages: list[dict]) -> str:
        return "".join(self.generate_stream(messages))

    def generate_stream(self, messages: list[dict]):
        extra_body = {}
        if self._thinking_mode:
            extra_body["thinking_mode"] = True

        # 重试只在建立连接阶段进行。
        # 一旦开始 yield token，就不能再重试：
        # 已发出的 token 无法撤回，重试会导致输出重复。
        last_err = None
        stream = None
        for attempt in range(MAX_RETRIES):
            try:
                stream = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=self._temperature,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                    timeout=self._timeout,
                )
                break  # 连接成功，退出重试循环
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])

        if stream is None:
            raise last_err

        # 流建立后直接迭代，中途出错直接抛出（不重试，避免 token 重复）
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
