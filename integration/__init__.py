"""CADreader集成模块

与其他skills的集成接口
"""

from .feishu_connector import FeishuConnector
from .wiki_connector import WikiConnector
from .quota_connector import QuotaConnector

__all__ = ["FeishuConnector", "WikiConnector", "QuotaConnector"]