"""DWG文件解析器 - 使用ezdxf库"""
import ezdxf
from typing import Iterator, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DWGParser:
    """DWG图纸解析器"""

    def __init__(self, dwg_path: str):
        self.dwg_path = dwg_path
        self.doc = None
        self.modelspace = None

    def open(self) -> 'DWGParser':
        """打开DWG文件"""
        logger.info(f"Opening DWG: {self.dwg_path}")
        self.doc = ezdxf.readfile(self.dwg_path)
        self.modelspace = self.doc.modelspace()
        return self

    def close(self):
        """关闭DWG文件"""
        if self.doc:
            self.doc.close()
            self.doc = None
            self.modelspace = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def iter_entities(self, entity_types: List[str] = None) -> Iterator[Any]:
        """迭代实体

        Args:
            entity_types: 要提取的实体类型列表，如['INSERT', 'TEXT', 'LINE']
                         如果为None，则提取所有实体
        """
        if not self.modelspace:
            raise RuntimeError("DWG file not opened. Call open() first.")

        for entity in self.modelspace:
            if entity_types is None or entity.dxftype() in entity_types:
                yield entity

    def get_blocks(self) -> List[Dict[str, Any]]:
        """提取所有块引用及其属性"""
        blocks = []
        for entity in self.iter_entities(['INSERT']):
            block_info = {
                'name': entity.dxf.name,
                'location': (entity.dxf.insert.x, entity.dxf.insert.y, entity.dxf.insert.z),
                'rotation': entity.dxf.rotation,
                'attribs': {}
            }
            # 提取属性
            if entity.has_attributes:
                for attr in entity.get_attributes():
                    block_info['attribs'][attr.dxf.tag] = attr.dxf.text
            blocks.append(block_info)
        return blocks

    def get_texts(self) -> List[Dict[str, Any]]:
        """提取所有文字"""
        texts = []
        for entity in self.iter_entities(['TEXT', 'MTEXT']):
            text_info = {
                'text': entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text,
                'location': (entity.dxf.insert.x, entity.dxf.insert.y) if entity.dxftype() == 'TEXT' else None,
            }
            texts.append(text_info)
        return texts

    def get_lines(self) -> List[Dict[str, Any]]:
        """提取所有直线"""
        lines = []
        for entity in self.iter_entities(['LINE']):
            line_info = {
                'start': (entity.dxf.start.x, entity.dxf.start.y),
                'end': (entity.dxf.end.x, entity.dxf.end.y),
            }
            lines.append(line_info)
        return lines