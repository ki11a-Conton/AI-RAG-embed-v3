import re

from lib.llm_api import LlmApi

_PREAMBLE_PATTERNS = [
    r"^(here('s| is) (the |a )?(rewritten|revised|standalone) (query|question)[:\s]*)",
    r"^(i('ll| will) rewrite (this|it)[:\s]*)",
    r"^(rewritten[:\s]+)",
]
_CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")


class QueryEnhancer:
    def __init__(self, llm_api: LlmApi, docs_lang: str = "en"):
        self._llm = llm_api
        self._docs_lang = docs_lang

    @property
    def label(self) -> str:
        return "Enhanced Question"

    def enhance(self, question: str, history: list | None = None) -> str:
        prompt = self._build_prompt(question, history)
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self._llm.generate(messages)
            response = self._clean_response(response, question)
            return response if response else question
        except Exception:
            return question

    def _clean_response(self, response: str, question: str) -> str:
        response = response.strip()
        for pattern in _PREAMBLE_PATTERNS:
            response = re.sub(pattern, "", response, flags=re.IGNORECASE).strip()
        if len(response) > len(question) * 3:
            return question
        return response

    def _build_prompt(self, question: str, history: list | None = None) -> str:
        if history:
            conv_parts = []
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                conv_parts.append(f"{role}: {msg['content']}")
            conversation = "\n".join(conv_parts)
            return f"""Below is a conversation history. The user's latest question may refer to previous context.
Rewrite the latest question as a standalone query for retrieval in {self._docs_lang}.
Resolve any pronouns/ellipsis using the conversation history.
Output only the rewritten question, no explanation.

History:
{conversation}

Latest question: {question}
Rewritten:"""
        return f"""Rewrite the following question into a clear, standalone retrieval query in {self._docs_lang}.
Requirements:
1. Do NOT answer the question, only rewrite it.
2. Keep the original intent unchanged.
3. Expand abbreviations and resolve implicit references.
4. Preserve both original and {self._docs_lang} forms of key technical terms.
5. Output only the final rewritten query, no explanation.

Question: {question}
Rewritten:"""


class OfflineTranslator:
    """Argos Translate based local translator compatible with QueryEnhancer."""

    def __init__(self, from_lang: str = "zh", to_lang: str = "en"):
        self._from_lang = from_lang
        self._to_lang = to_lang

    @property
    def label(self) -> str:
        return "Translated Question"

    def _resolve_pronouns(self, question: str, history: list | None = None) -> str:
        if not history:
            return question
        last_user = next(
            (
                item.get("content", "")
                for item in reversed(history)
                if item.get("role") == "user"
            ),
            "",
        )
        if last_user and len(question.strip()) < 30:
            return f"Following up on '{last_user}': {question}"
        return question

    @staticmethod
    def download_language_pack(from_code: str = "zh", to_code: str = "en") -> None:
        """Download and install the Argos language package once."""
        import argostranslate.package

        print(">> 正在获取 Argos 语言包列表...")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()

        package = next(
            (
                item
                for item in available
                if item.from_code == from_code and item.to_code == to_code
            ),
            None,
        )
        if package is None:
            pairs = [(item.from_code, item.to_code) for item in available]
            raise RuntimeError(
                f"No Argos language package found for {from_code} -> {to_code}. "
                f"Available pairs: {pairs}"
            )

        print(f">> 正在下载 Argos 语言包 {from_code} -> {to_code}...")
        argostranslate.package.install_from_path(package.download())
        print(">> 语言包安装完成 ✅")

    def enhance(self, question: str, history: list | None = None) -> str:
        if not question.strip():
            return question
        if (
            self._from_lang.lower().startswith("zh")
            and not _CJK_PATTERN.search(question)
        ):
            return question
        try:
            import argostranslate.translate

            # Translate only the current question (no history wrapper)
            translated = argostranslate.translate.translate(
                question, self._from_lang, self._to_lang
            )
            if not translated:
                return question

            # After translation, wrap with history context if short follow-up
            if history:
                last_user = next(
                    (
                        item.get("content", "")
                        for item in reversed(history)
                        if item.get("role") == "user"
                    ),
                    "",
                )
                if last_user and len(question.strip()) < 30:
                    return f"Following up on '{last_user}': {translated}"

            return translated
        except Exception:
            return question


class MultiQueryEnhancer:
    """用 LLM 把原问题改写成 N 个不同角度的查询，返回 list[str]。"""

    def __init__(self, llm_api: LlmApi, n_queries: int = 3, docs_lang: str = "en"):
        self._llm = llm_api
        self._n = n_queries
        self._docs_lang = docs_lang

    @property
    def label(self) -> str:
        return "Multi-Query"

    def generate_queries(self, question: str) -> list[str]:
        """
        返回 N 个改写后的查询。第一个始终是原始问题（保底）。
        如果 LLM 调用失败，只返回 [question]。
        """
        prompt = self._build_prompt(question)
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self._llm.generate(messages)
            queries = self._parse_response(response, question)
            # 原始问题始终保留，放第一位
            if question not in queries:
                queries.insert(0, question)
            return queries[: self._n + 1]  # 最多返回 n+1 个（含原始）
        except Exception:
            return [question]

    def _build_prompt(self, question: str) -> str:
        return (
            f"You are a retrieval query optimizer. Given a user question, generate "
            f"{self._n} alternative search queries that capture different aspects or "
            f"phrasings of the same information need. The queries will be used to search "
            f"a document knowledge base written in {self._docs_lang}.\n\n"
            f"Requirements:\n"
            f"1. Each query should approach the topic from a different angle "
            f"(e.g., different terminology, broader context, specific detail).\n"
            f"2. Keep each query concise (under 30 words).\n"
            f"3. Output ONLY the queries, one per line, no numbering, no explanation.\n"
            f"4. Write all queries in {self._docs_lang}.\n\n"
            f"Original question: {question}\n\n"
            f"Alternative queries:"
        )

    def _parse_response(self, response: str, original: str) -> list[str]:
        lines = [line.strip() for line in response.strip().splitlines()]
        queries = []
        for line in lines:
            # 过滤掉空行、编号前缀（"1.", "-", "•"）
            line = re.sub(r"^[\d\.\-\•\*]+\s*", "", line).strip()
            if line and line != original and len(line) > 5:
                queries.append(line)
        return queries
