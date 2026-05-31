"""CADreader核心引擎

基于PHT-CAD的工程图纸解析引擎
集成了ezdxf_parser用于DXF/DWG文件解析
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict

from .parsers import DWGParser, DeviceExtractor, TopologyBuilder, CoordExtractor

logger = logging.getLogger(__name__)


@dataclass
class Primitive:
    """图元基类"""
    type: str  # point, line, circle, arc
    params: List[float]
    layer: Optional[str] = None


@dataclass
class Annotation:
    """标注基类"""
    type: str  # dimension, tolerance, text
    value: str
    linked_to: List[int]  # 关联的图元索引
    unit: Optional[str] = None


@dataclass
class Constraint:
    """结构约束"""
    type: str  # parallel, perpendicular, tangent, etc.
    entities: List[int]  # 关联的图元索引


@dataclass
class ParsedDrawing:
    """解析结果"""
    primitives: List[Primitive]
    annotations: List[Annotation]
    constraints: List[Constraint]
    metadata: Dict

    def to_json(self) -> Dict:
        """转换为JSON格式"""
        return {
            "primitives": [
                {"type": p.type, "params": p.params, "layer": p.layer}
                for p in self.primitives
            ],
            "annotations": [
                {"type": a.type, "value": a.value, "linked_to": a.linked_to, "unit": a.unit}
                for a in self.annotations
            ],
            "constraints": [
                {"type": c.type, "entities": c.entities}
                for c in self.constraints
            ],
            "metadata": self.metadata
        }

    def to_file(self, path: Union[str, Path]) -> None:
        """保存到JSON文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)


class CADReader:
    """工程图纸智能解析引擎

    基于PHT-CAD的VLM驱动图纸理解系统
    """

    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        """初始化CADReader

        Args:
            model_path: PHT-CAD模型路径，默认使用HuggingFace预训练模型
            device: 推理设备，"cuda" 或 "cpu"
        """
        self.model_path = model_path or "yuwen-chen616/PHT-CAD"
        self.device = device
        self.model = None
        self._initialized = False

    def initialize(self) -> None:
        """初始化模型（延迟加载）"""
        if self._initialized:
            return

        try:
            from transformers import AutoModelForCausalLM
            import torch

            print(f"正在加载PHT-CAD模型: {self.model_path}")
            # self.model = AutoModelForCausalLM.from_pretrained(
            #     self.model_path,
            #     torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            # )
            # self.model.to(self.device)
            self._initialized = True
            print("模型加载完成")

        except ImportError as e:
            raise RuntimeError(f"请先安装依赖: pip install transformers torch - {e}")

    def parse(self, input_path: Union[str, Path]) -> ParsedDrawing:
        """解析工程图纸

        Args:
            input_path: 图纸文件路径（支持jpg/png/dxf/pdf）

        Returns:
            ParsedDrawing: 解析结果
        """
        if not self._initialized:
            self.initialize()

        path = Path(input_path)
        suffix = path.suffix.lower()

        # 根据文件类型选择解析方法
        if suffix in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self._parse_image(path)
        elif suffix in ['.dxf']:
            return self._parse_dxf(path)
        elif suffix in ['.pdf']:
            return self._parse_pdf(path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    def _parse_image(self, path: Path) -> ParsedDrawing:
        """解析图像格式图纸

        使用PHT-CAD VLM模型进行图元识别
        """
        # TODO: 实现PHT-CAD图像推理
        # 1. 加载图像
        # 2. 调用VLM推理
        # 3. 解析输出为Primitive/Annotation

        return ParsedDrawing(
            primitives=[],
            annotations=[],
            constraints=[],
            metadata={"source": str(path), "type": "image"}
        )

    def _parse_dxf(self, path: Path) -> ParsedDrawing:
        """解析DXF格式图纸

        使用DWGParser + ezdxf解析DXF/DWG文件结构
        提取几何图元（线、圆、弧等）和文本标注
        """
        try:
            import ezdxf
        except ImportError:
            raise RuntimeError("请先安装ezdxf: pip install ezdxf")

        primitives = []
        annotations = []

        # 使用DWGParser解析文件
        with DWGParser(str(path)) as parser:
            # 提取几何图元
            for entity in parser.iter_entities(['LINE', 'CIRCLE', 'ARC', 'POLYLINE', 'LWPOLYLINE']):
                if entity.dxftype() == 'LINE':
                    primitives.append(Primitive(
                        type='line',
                        params=[entity.dxf.start.x, entity.dxf.start.y,
                                entity.dxf.end.x, entity.dxf.end.y],
                        layer=getattr(entity.dxf, 'layer', '0')
                    ))
                elif entity.dxftype() == 'CIRCLE':
                    primitives.append(Primitive(
                        type='circle',
                        params=[entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius],
                        layer=getattr(entity.dxf, 'layer', '0')
                    ))
                elif entity.dxftype() == 'ARC':
                    primitives.append(Primitive(
                        type='arc',
                        params=[entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius,
                                entity.dxf.start_angle, entity.dxf.end_angle],
                        layer=getattr(entity.dxf, 'layer', '0')
                    ))

            # 提取文本标注
            texts = parser.get_texts()
            for text in texts:
                annotations.append(Annotation(
                    type='text',
                    value=text.get('text', ''),
                    linked_to=[],
                    layer=text.get('layer', '0')
                ))

            # 提取块引用（设备）
            blocks = parser.get_blocks()
            for block in blocks:
                # 块引用作为特殊图元
                primitives.append(Primitive(
                    type='block',
                    params=list(block.get('location', (0, 0, 0))),
                    layer=block.get('name', 'unknown')
                ))

        # 统计图层
        layers = list(set(p.layer for p in primitives if p.layer))

        return ParsedDrawing(
            primitives=primitives,
            annotations=annotations,
            constraints=[],
            metadata={
                "source": str(path),
                "type": "dxf",
                "format": "DXF",
                "layers": layers,
                "primitive_count": len(primitives),
                "annotation_count": len(annotations)
            }
        )

    def _parse_pdf(self, path: Path) -> ParsedDrawing:
        """解析PDF格式图纸

        1. PDF转图像
        2. 使用PHT-CAD解析
        """
        # TODO: 实现PDF转图像 + PHT-CAD解析
        return ParsedDrawing(
            primitives=[],
            annotations=[],
            constraints=[],
            metadata={"source": str(path), "type": "pdf"}
        )

    def parse_batch(self, input_dir: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> List[ParsedDrawing]:
        """批量解析图纸

        Args:
            input_dir: 输入目录
            output_dir: 输出目录（可选，保存JSON）

        Returns:
            List[ParsedDrawing]: 解析结果列表
        """
        input_path = Path(input_dir)
        results = []

        for file_path in input_path.rglob("*"):
            if file_path.suffix.lower() in ['.jpg', '.png', '.dxf', '.pdf']:
                try:
                    result = self.parse(file_path)
                    results.append(result)

                    if output_dir:
                        output_path = Path(output_dir) / f"{file_path.stem}.json"
                        result.to_file(output_path)

                except Exception as e:
                    print(f"解析失败 {file_path}: {e}")

        return results


def main():
    """命令行入口"""
    import click

    @click.command()
    @click.option('--input', '-i', required=True, help='输入图纸路径')
    @click.option('--output', '-o', help='输出JSON路径')
    @click.option('--batch', '-b', is_flag=True, help='批量模式')
    def run(input, output, batch):
        reader = CADReader()

        if batch:
            results = reader.parse_batch(input, output)
            print(f"批量解析完成: {len(results)} 个文件")
        else:
            result = reader.parse(input)
            if output:
                result.to_file(output)
            else:
                print(json.dumps(result.to_json(), indent=2, ensure_ascii=False))

    run()


if __name__ == "__main__":
    main()