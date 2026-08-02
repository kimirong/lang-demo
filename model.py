"""公共模块：创建 DeepSeek 模型 / 本地 Embedding 实例。

后续所有脚本都从这import，避免重复写接入代码。
注意：本模块必须在脚本里【第一个】被 import —— 因为这里要设置
HF_HUB_OFFLINE 离线变量，而 huggingface_hub 在 import 时就会把
该值缓存成常量，设晚了就失效（模型已缓存时联网校验会挂起很久）。
"""

import os

# 在 import 任何可能引入 huggingface_hub 的库之前设置离线变量。
# 模型已缓存就强制离线加载（中国网络无法直连 huggingface.co）。
if os.getenv("HF_HUB_OFFLINE") is None and os.path.isdir(
    os.path.expanduser("~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5")
):
    os.environ["HF_HUB_OFFLINE"] = "1"

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
