"""公共模块：创建 DeepSeek 模型实例。

后续所有脚本都从这import，避免重复写接入代码。
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(model: str = "deepseek-chat", **kwargs) -> ChatOpenAI:
    """返回一个接好 DeepSeek 的 ChatOpenAI 实例。

    DeepSeek 的 HTTP 接口兼容 OpenAI，所以用官方 ChatOpenAI，
    只需覆盖 base_url 和 model。
    """
    return ChatOpenAI(
        model=model,
        base_url="https://api.deepseek.com",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )
