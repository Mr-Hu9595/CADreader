# -*- coding: utf-8 -*-
"""CADreader VLM原型 - 使用MiniMax理解DXF图像

将DXF文件渲染为图像，然后使用MiniMax VLM进行理解和解析
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class VLMAnalysisResult:
    """VLM分析结果"""
    devices: List[Dict]  # 识别出的设备
    dimensions: List[Dict]  # 尺寸标注
    annotations: List[str]  # 文本标注
    technical_requirements: List[str]  # 技术要求
    raw_response: str  # 原始响应
    confidence: float  # 置信度


class DXFToImageRenderer:
    """DXF转图像渲染器"""

    def __init__(self):
        self.fig_size = (16, 12)  # 图像尺寸英寸
        self.dpi = 150  # 分辨率
        self._setup_chinese_font()

    def _setup_chinese_font(self):
        """设置中文字体支持"""
        import matplotlib.pyplot as plt

        # 尝试多个中文字体
        chinese_fonts = [
            'Microsoft YaHei',
            'SimHei',
            'Microsoft JhengHei',
            'Noto Sans CJK SC',
        ]

        # 查找可用的中文字体
        import matplotlib.font_manager as fm
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        self.font_name = 'Microsoft YaHei'  # 默认字体
        for font in chinese_fonts:
            if font in available_fonts:
                self.font_name = font
                break

        # 设置matplotlib全局字体
        plt.rcParams['font.sans-serif'] = [self.font_name] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        print(f"使用字体: {self.font_name}")

    def render(self, dxf_path: str, output_path: Optional[str] = None) -> str:
        """将DXF渲染为PNG图像

        Args:
            dxf_path: DXF文件路径
            output_path: 输出图像路径（可选）

        Returns:
            str: 生成的图像路径
        """
        try:
            import ezdxf
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from matplotlib.patches import FancyArrowPatch, Circle, Arc, Polygon
            import numpy as np
        except ImportError as e:
            raise RuntimeError(f"请先安装依赖: pip install ezdxf matplotlib numpy - {e}")

        logger.info(f"渲染DXF: {dxf_path}")

        # 读取DXF文件
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 创建图形
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.5)

        # 统计信息
        entities_count = {'LINE': 0, 'CIRCLE': 0, 'ARC': 0, 'TEXT': 0, 'MTEXT': 0, 'INSERT': 0, 'LWPOLYLINE': 0, 'POLYLINE': 0}

        # 遍历实体并绘制
        for entity in msp:
            try:
                etype = entity.dxftype()

                if etype == 'LINE':
                    ax.plot([entity.dxf.start.x, entity.dxf.end.x],
                            [entity.dxf.start.y, entity.dxf.end.y],
                            'b-', linewidth=0.5)
                    entities_count['LINE'] += 1

                elif etype == 'CIRCLE':
                    circle = Circle((entity.dxf.center.x, entity.dxf.center.y),
                                    entity.dxf.radius,
                                    fill=False, edgecolor='green', linewidth=0.5)
                    ax.add_patch(circle)
                    entities_count['CIRCLE'] += 1

                elif etype == 'ARC':
                    arc = Arc((entity.dxf.center.x, entity.dxf.center.y),
                               entity.dxf.radius * 2, entity.dxf.radius * 2,
                               angle=0,
                               theta1=entity.dxf.start_angle,
                               theta2=entity.dxf.end_angle,
                               color='green', linewidth=0.5)
                    ax.add_patch(arc)
                    entities_count['ARC'] += 1

                elif etype == 'TEXT':
                    x, y = entity.dxf.insert.x, entity.dxf.insert.y
                    text = entity.dxf.text
                    if hasattr(entity.dxf, 'height'):
                        fontsize = min(entity.dxf.height, 12)
                    else:
                        fontsize = 8
                    ax.text(x, y, text, fontsize=fontsize, color='red',
                            fontfamily='sans-serif', fontproperties=self.font_name)
                    entities_count['TEXT'] += 1

                elif etype == 'MTEXT':
                    if hasattr(entity, 'text'):
                        x, y = entity.dxf.insert.x, entity.dxf.insert.y
                        ax.text(x, y, entity.text[:50], fontsize=6, color='red',
                               fontfamily='sans-serif', fontproperties=self.font_name)
                        entities_count['MTEXT'] += 1

                elif etype == 'INSERT':
                    # 块引用
                    x, y = entity.dxf.insert.x, entity.dxf.insert.y
                    block_name = entity.dxf.name
                    ax.plot(x, y, 'ko', markersize=3)
                    ax.text(x, y, block_name[:10], fontsize=5, color='blue', alpha=0.7,
                            fontfamily='sans-serif', fontproperties=self.font_name)
                    entities_count['INSERT'] += 1

                elif etype in ['LWPOLYLINE', 'POLYLINE']:
                    points = []
                    if hasattr(entity, 'get_points'):
                        for point in entity.get_points():
                            points.append((point[0], point[1]))
                    if points:
                        xs, ys = zip(*points)
                        ax.plot(xs, ys, 'b-', linewidth=0.5)
                    entities_count['LWPOLYLINE'] += 1

            except Exception as e:
                continue

        # 设置标题和标签
        total = sum(entities_count.values())
        ax.set_title(f"DXF: {Path(dxf_path).name} ({total} entities)", fontsize=10)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        # 输出统计
        stats = ", ".join([f"{k}:{v}" for k, v in entities_count.items() if v > 0])
        logger.info(f"实体统计: {stats}")

        # 保存图像
        if output_path is None:
            output_path = str(Path(dxf_path).with_suffix('.png'))

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"图像已保存: {output_path}")
        return output_path


class MiniMaxVLMAnalyzer:
    """MiniMax VLM分析器"""

    def __init__(self):
        self.prompt_template = """你是一个专业的工程图纸阅读助手。请分析这张工程图纸（DXF渲染图），提取以下信息：

1. **设备清单**：识别图纸中的设备，列出设备名称、编号和位置
2. **尺寸标注**：识别图纸中的尺寸信息，包括数值和单位
3. **文本标注**：识别所有文字标注内容
4. **技术要求**：识别图纸中的技术说明或要求
5. **坐标系**：说明图纸的坐标原点位置

请用JSON格式输出，格式如下：
{
    "devices": [
        {"name": "设备名称", "id": "编号", "location": "位置描述", "coords": [x, y]}
    ],
    "dimensions": [
        {"value": "尺寸值", "unit": "单位", "location": "位置"}
    ],
    "annotations": ["文字内容1", "文字内容2"],
    "technical_requirements": ["技术要求1", "技术要求2"],
    "coordinate_system": {"origin": "原点位置", "unit": "单位"},
    "summary": "图纸概述"
}
"""

    def analyze_image(self, image_path: str) -> Dict:
        """使用MiniMax VLM分析图像

        Args:
            image_path: 图像文件路径

        Returns:
            Dict: 分析结果
        """
        try:
            # 使用mcp__MiniMax__understand_image工具
            from mcp__MiniMax__understand_image import mcp__MiniMax__understand_image
        except ImportError:
            # 工具未导入，尝试直接调用
            pass

        # 读取图像并转为base64
        with open(image_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')

        # 构建prompt
        prompt = self.prompt_template

        logger.info(f"调用MiniMax VLM分析图像: {image_path}")

        # 实际使用时通过MCP工具调用
        # 这里先返回模拟结果用于测试流程
        return {
            "status": "pending",
            "image_path": image_path,
            "message": "请通过MCP工具调用mcp__MiniMax__understand_image"
        }


class VLMEnhancedCADReader:
    """VLM增强的CAD图纸阅读器"""

    def __init__(self):
        self.renderer = DXFToImageRenderer()
        self.vlm = MiniMaxVLMAnalyzer()

    def parse(self, dxf_path: str, output_dir: Optional[str] = None) -> VLMAnalysisResult:
        """解析DXF图纸

        Args:
            dxf_path: DXF文件路径
            output_dir: 输出目录（可选）

        Returns:
            VLMAnalysisResult: VLM分析结果
        """
        dxf_path = Path(dxf_path)
        if not dxf_path.exists():
            raise FileNotFoundError(f"文件不存在: {dxf_path}")

        # Step 1: 将DXF渲染为图像
        logger.info("Step 1: 渲染DXF为图像")
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            image_path = str(output_dir / f"{dxf_path.stem}.png")
        else:
            image_path = str(dxf_path.with_suffix('.png'))

        rendered_path = self.renderer.render(str(dxf_path), image_path)

        # Step 2: 使用VLM分析图像
        logger.info("Step 2: VLM分析图像")
        analysis = self.vlm.analyze_image(rendered_path)

        return analysis

    def parse_and_explain(self, dxf_path: str) -> str:
        """解析DXF并生成说明

        Args:
            dxf_path: DXF文件路径

        Returns:
            str: 解析说明
        """
        result = self.parse(dxf_path)

        explanation = f"""
=== DXF图纸解析结果 ===

文件: {dxf_path}

1. 设备清单:
{json.dumps(result.get('devices', []), indent=2, ensure_ascii=False)}

2. 尺寸标注:
{json.dumps(result.get('dimensions', []), indent=2, ensure_ascii=False)}

3. 文本标注:
{json.dumps(result.get('annotations', []), indent=2, ensure_ascii=False)}

4. 技术要求:
{json.dumps(result.get('technical_requirements', []), indent=2, ensure_ascii=False)}

5. 坐标系:
{json.dumps(result.get('coordinate_system', {}), indent=2, ensure_ascii=False)}

原始响应:
{result.get('raw_response', '')}

"""

        return explanation


def test_with_minimax(image_path: str, prompt: str = None):
    """使用MiniMax understand_image测试

    Args:
        image_path: 图像路径
        prompt: 提示词（可选）
    """
    if prompt is None:
        prompt = """你是一个专业的工程图纸阅读助手。请分析这张工程图纸，提取：
1. 设备清单（名称、编号、位置）
2. 尺寸标注（数值、单位）
3. 文本标注（所有文字）
4. 技术要求

请尽量详细地提取信息，以JSON格式输出。"""

    # 调用MiniMax MCP工具
    try:
        result = mcp__MiniMax__understand_image(
            image_source=image_path,
            prompt=prompt
        )
        return result
    except Exception as e:
        logger.error(f"MiniMax调用失败: {e}")
        return {"error": str(e)}


def parse_with_vlm(dxf_path: str, output_dir: str = None) -> Dict:
    """使用VLM解析DXF图纸的完整流程

    Args:
        dxf_path: DXF文件路径
        output_dir: 输出目录

    Returns:
        Dict: 解析结果
    """
    renderer = DXFToImageRenderer()

    # Step 1: 渲染DXF为图像
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = str(output_dir / f"{Path(dxf_path).stem}.png")
    else:
        image_path = str(Path(dxf_path).with_suffix('.png'))

    logger.info("Step 1: 渲染DXF为图像")
    renderer.render(dxf_path, image_path)
    logger.info(f"图像已保存: {image_path}")

    # Step 2: 调用MiniMax VLM分析
    logger.info("Step 2: 调用MiniMax VLM分析")
    prompt = """你是一个专业的工程图纸阅读助手。请分析这张工程图纸，提取以下信息：

1. **设备清单**：识别图纸中的设备，列出设备名称、编号和位置
2. **尺寸标注**：识别图纸中的尺寸信息，包括数值和单位
3. **文本标注**：识别所有文字标注内容
4. **技术要求**：识别图纸中的技术说明或要求

请用JSON格式输出，格式如下：
{
    "devices": [
        {"name": "设备名称", "id": "编号", "location": "位置描述", "coords": [x, y]}
    ],
    "dimensions": [
        {"value": "尺寸值", "unit": "单位", "location": "位置"}
    ],
    "annotations": ["文字内容1", "文字内容2"],
    "technical_requirements": ["技术要求1", "技术要求2"],
    "summary": "图纸概述"
}"""

    try:
        result = mcp__MiniMax__understand_image(
            image_source=image_path,
            prompt=prompt
        )
        return {
            "status": "success",
            "image_path": image_path,
            "vlm_result": result
        }
    except Exception as e:
        logger.error(f"VLM分析失败: {e}")
        return {
            "status": "error",
            "image_path": image_path,
            "error": str(e)
        }


def main():
    """主函数 - 测试VLM DXF解析"""
    import argparse

    parser = argparse.ArgumentParser(description='VLM增强的DXF图纸解析')
    parser.add_argument('--input', '-i', required=True, help='DXF文件路径')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--test-minimax', '-t', action='store_true', help='测试MiniMax VLM')
    parser.add_argument('--render-only', '-r', action='store_true', help='仅渲染不分析')

    args = parser.parse_args()

    reader = VLMEnhancedCADReader()

    if args.render_only:
        # 仅渲染
        output_dir = args.output or str(Path(args.input).parent)
        image_path = f"{output_dir}/{Path(args.input).stem}.png"
        reader.renderer.render(args.input, image_path)
        print(f"图像已保存: {image_path}")
    elif args.test_minimax:
        # 测试MiniMax
        output_dir = args.output or str(Path(args.input).parent)
        image_path = f"{output_dir}/{Path(args.input).stem}.png"

        # 先渲染
        reader.renderer.render(args.input, image_path)
        print(f"图像已保存: {image_path}")
        print("正在调用MiniMax VLM分析...")

        # 调用MiniMax
        result = test_with_minimax(image_path)
        print("\n=== 分析结果 ===")
        print(result)
    else:
        # 完整解析
        result = reader.parse(args.input, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()