"""CADreader - 工程图纸智能解析工具

基于PHT-CAD的工程图纸阅读与理解系统
"""

__version__ = "0.1.0"
__author__ = "CADreader Team"
__license__ = "MIT"

from .engine import CADReader

__all__ = ["CADReader"]