"""
DeepSeek 服务层 - 调用 DeepSeek API 生成简报（业务逻辑在 report_service 编排）
"""
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class DeepSeekService:
    """调用 DeepSeek Chat API"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL
        self.model = model or DEEPSEEK_MODEL
        self._client = None

    def _client_or_new(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def chat(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """
        单轮对话，返回助手回复文本。
        
        Args:
            system: 系统提示
            user: 用户消息
            max_tokens: 最大生成 token 数
            
        Returns:
            助手回复内容；失败时返回空字符串或抛出异常
        """
        client = self._client_or_new()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            stream=False,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text
