"""customer_service —— Phase 6 客服业务包。

必须先 import model：它会加载 .env（DeepSeek/LangSmith/代理）并设置
HF_HUB_OFFLINE，且必须在任何 langchain 库初始化之前生效（沿用项目铁律）。
"""

import model  # noqa: F401  仅触发 model.py 的顶层环境配置
