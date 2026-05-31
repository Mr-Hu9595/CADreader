"""CADreader - 工程图纸智能解析工具

基于PHT-CAD的工程图纸阅读与理解系统
"""

__version__ = "0.2.0"
__author__ = "CADreader Team"
__license__ = "MIT"

from .engine import CADReader, ParsedDrawing, Primitive, Annotation, Constraint
from .parsers import DWGParser, DeviceExtractor, TopologyBuilder, CoordExtractor
from .pdf_parser import PDFParser, parse_pdf_structure, render_pdf_page

__all__ = [
    "CADReader",
    "ParsedDrawing",
    "Primitive",
    "Annotation",
    "Constraint",
    "DWGParser",
    "DeviceExtractor",
    "TopologyBuilder",
    "CoordExtractor",
    "PDFParser",
    "parse_pdf_structure",
    "render_pdf_page"
]