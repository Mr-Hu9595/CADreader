# -*- coding: utf-8 -*-
"""CADreader PDF解析模块

使用PyMuPDF解析PDF工程图纸
支持文本提取、图像提取、表格识别
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """PDF页面"""
    page_num: int
    width: float
    height: float
    text_blocks: List['TextBlock']
    images: List['ImageBlock']
    tables: List['TableBlock']


@dataclass
class TextBlock:
    """文本块"""
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str
    color: str


@dataclass
class ImageBlock:
    """图像块"""
    image_data: bytes
    bbox: Tuple[float, float, float, float]
    width: int
    height: int
    format: str  # png/jpeg/etc


@dataclass
class TableBlock:
    """表格块"""
    rows: List[List[str]]
    bbox: Tuple[float, float, float, float]


class PDFParser:
    """PDF工程图纸解析器

    使用PyMuPDF提取PDF中的文本、图像、表格信息
    """

    def __init__(self, pdf_path: str):
        """初始化PDF解析器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.doc = None
        self._loaded = False

    def load(self) -> 'PDFParser':
        """加载PDF文件"""
        import fitz
        logger.info(f"加载PDF: {self.pdf_path}")
        self.doc = fitz.open(self.pdf_path)
        self._loaded = True
        return self

    def close(self):
        """关闭PDF文件"""
        if self.doc:
            self.doc.close()
            self.doc = None
            self._loaded = False

    def __enter__(self):
        return self.load()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_page_count(self) -> int:
        """获取页数"""
        if not self._loaded:
            self.load()
        return len(self.doc)

    def parse_page(self, page_num: int) -> PDFPage:
        """解析指定页面

        Args:
            page_num: 页码（从0开始）

        Returns:
            PDFPage: 解析结果
        """
        if not self._loaded:
            self.load()

        page = self.doc[page_num]
        rect = page.rect

        # 提取文本
        text_blocks = self._extract_text(page)

        # 提取图像
        images = self._extract_images(page)

        # 尝试识别表格
        tables = self._extract_tables(page)

        return PDFPage(
            page_num=page_num,
            width=rect.width,
            height=rect.height,
            text_blocks=text_blocks,
            images=images,
            tables=tables
        )

    def _extract_text(self, page) -> List[TextBlock]:
        """提取页面文本"""
        text_blocks = []

        # 方法1: 使用get_text()获取全部文本块
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_blocks.append(TextBlock(
                            text=span["text"],
                            bbox=(span["bbox"][0], span["bbox"][1],
                                  span["bbox"][2], span["bbox"][3]),
                            font_size=span.get("size", 0),
                            font_name=span.get("font", ""),
                            color=span.get("color", "")
                        ))

        return text_blocks

    def _extract_images(self, page) -> List[ImageBlock]:
        """提取页面图像"""
        images = []

        # 获取图像列表
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = self.doc.extract_image(xref)

            if base_image:
                images.append(ImageBlock(
                    image_data=base_image["image"],
                    bbox=(0, 0, 0, 0),  # 图像位置需要单独获取
                    width=base_image.get("width", 0),
                    height=base_image.get("height", 0),
                    format=base_image.get("ext", "png")
                ))

        return images

    def _extract_tables(self, page) -> List[TableBlock]:
        """提取表格（简单实现）"""
        tables = []

        # 简单表格检测：查找由线条组成的矩形区域
        # 这是一个基础实现，更复杂的表格识别需要机器学习
        text = page.get_text("text")

        # 检测可能的表格结构（多个换行符分隔的类似格式文本）
        lines = text.split('\n')
        if len(lines) > 3:
            # 简单检查是否有规律的列分隔
            # 这需要更复杂的算法，这里先返回一个空列表
            pass

        return tables

    def parse_all(self) -> List[PDFPage]:
        """解析所有页面

        Returns:
            List[PDFPage]: 所有页面的解析结果
        """
        if not self._loaded:
            self.load()

        pages = []
        for page_num in range(len(self.doc)):
            pages.append(self.parse_page(page_num))

        return pages

    def render_to_image(self, page_num: int = 0, dpi: int = 150) -> bytes:
        """将指定页面渲染为图像

        Args:
            page_num: 页码
            dpi: 分辨率

        Returns:
            bytes: PNG图像数据
        """
        import fitz

        if not self._loaded:
            self.load()

        page = self.doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        return pix.tobytes("png")

    def render_all_to_images(self, output_dir: str, dpi: int = 150) -> List[str]:
        """将所有页面渲染为图像

        Args:
            output_dir: 输出目录
            dpi: 分辨率

        Returns:
            List[str]: 生成的图像文件路径列表
        """
        import fitz

        if not self._loaded:
            self.load()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        image_paths = []
        pdf_name = Path(self.pdf_path).stem

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            image_path = output_path / f"{pdf_name}_page{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))

        return image_paths


def parse_pdf_structure(pdf_path: str) -> Dict:
    """解析PDF文件结构

    Args:
        pdf_path: PDF文件路径

    Returns:
        Dict: 解析结果
    """
    parser = PDFParser(pdf_path)

    with parser:
        result = {
            "pdf_path": pdf_path,
            "page_count": parser.get_page_count(),
            "pages": []
        }

        for page_num in range(parser.get_page_count()):
            page = parser.parse_page(page_num)

            page_info = {
                "page_num": page_num,
                "width": page.width,
                "height": page.height,
                "text_count": len(page.text_blocks),
                "image_count": len(page.images),
                "table_count": len(page.tables),
                "texts": [
                    {
                        "text": tb.text,
                        "bbox": tb.bbox,
                        "font_size": tb.font_size
                    }
                    for tb in page.text_blocks[:100]  # 限制数量
                ]
            }

            result["pages"].append(page_info)

    return result


def render_pdf_page(pdf_path: str, page_num: int = 0, output_path: str = None, dpi: int = 150) -> str:
    """将PDF页面渲染为图像

    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从0开始）
        output_path: 输出图像路径（可选）
        dpi: 分辨率

    Returns:
        str: 生成的图像路径
    """
    parser = PDFParser(pdf_path)

    with parser:
        if output_path is None:
            output_path = str(Path(pdf_path).with_suffix(f'_page{page_num + 1}.png'))

        image_data = parser.render_to_image(page_num, dpi)

        with open(output_path, 'wb') as f:
            f.write(image_data)

    return output_path


def main():
    """测试PDF解析"""
    import argparse

    parser = argparse.ArgumentParser(description='PDF工程图纸解析')
    parser.add_argument('--input', '-i', required=True, help='PDF文件路径')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--render', '-r', action='store_true', help='渲染为图像')

    args = parser.parse_args()

    print(f"解析PDF: {args.input}")

    # 结构解析
    result = parse_pdf_structure(args.input)
    print(f"页数: {result['page_count']}")

    for page in result['pages'][:3]:
        print(f"  页面 {page['page_num']}: {page['width']}x{page['height']}, "
              f"文本{page['text_count']}个, 图像{page['image_count']}个")

    # 渲染为图像
    if args.render:
        output_dir = args.output or str(Path(args.input).parent)
        parser = PDFParser(args.input)
        with parser:
            paths = parser.render_all_to_images(output_dir)
            print(f"渲染完成: {len(paths)} 个图像")
            for p in paths:
                print(f"  - {p}")


if __name__ == '__main__':
    main()