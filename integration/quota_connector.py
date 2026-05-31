"""定额匹配集成模块

将图纸解析结果用于定额匹配
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ExtractedQuantity:
    """提取的工程量"""
    name: str  # 工程量名称
    value: float  # 数值
    unit: str  # 单位
    source: str  # 来源（图元索引）


class QuotaConnector:
    """定额匹配连接器

    从解析结果中提取工程量，用于 quota-matcher
    """

    def __init__(self):
        """初始化定额连接器"""
        pass

    def extract_quantities(self, parsed_result) -> List[ExtractedQuantity]:
        """从解析结果中提取工程量

        Args:
            parsed_result: CADreader解析结果

        Returns:
            List[ExtractedQuantity]: 工程量列表
        """
        quantities = []

        # 从标注中提取尺寸
        for ann in parsed_result.annotations:
            if ann.type == "dimension":
                qty = self._parse_dimension(ann)
                if qty:
                    quantities.append(qty)

        # 从图元中计算工程量
        for p in parsed_result.primitives:
            if p.type == "line":
                # 计算线长度
                length = self._calculate_line_length(p.params)
                quantities.append(ExtractedQuantity(
                    name="延长米",
                    value=length,
                    unit="m",
                    source=f"line_{p.layer}"
                ))
            elif p.type == "circle":
                # 计算圆周长
                circumference = self._calculate_circumference(p.params)
                quantities.append(ExtractedQuantity(
                    name="周长",
                    value=circumference,
                    unit="m",
                    source=f"circle_{p.layer}"
                ))

        return quantities

    def _parse_dimension(self, annotation) -> Optional[ExtractedQuantity]:
        """解析尺寸标注

        Args:
            annotation: Annotation对象

        Returns:
            ExtractedQuantity: 提取的工程量
        """
        import re

        # 解析尺寸值，如 "3×2.5mm" 或 "100±0.1"
        value_str = annotation.value

        # 提取数值
        numbers = re.findall(r'[\d.]+', value_str)
        if not numbers:
            return None

        # 提取单位
        units = re.findall(r'[a-zA-Z]+', value_str)
        unit = units[-1] if units else "mm"

        # 处理复合尺寸（如 3×2.5）
        if '×' in value_str or 'x' in value_str.lower():
            # 面积
            value = 1.0
            for n in numbers:
                value *= float(n)
            name = "面积"
        else:
            value = float(numbers[0])
            name = "长度"

        return ExtractedQuantity(
            name=name,
            value=value,
            unit=unit,
            source=f"annotation_{annotation.type}"
        )

    def _calculate_line_length(self, params: List[float]) -> float:
        """计算线段长度

        Args:
            params: [x1, y1, x2, y2]

        Returns:
            float: 长度
        """
        import math
        x1, y1, x2, y2 = params[:4]
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)

    def _calculate_circumference(self, params: List[float]) -> float:
        """计算圆周长

        Args:
            params: [cx, cy, r]

        Returns:
            float: 周长
        """
        import math
        r = params[2] if len(params) >= 3 else 0
        return 2 * math.pi * r

    def export_for_quota_matcher(self, quantities: List[ExtractedQuantity]) -> Dict:
        """导出为quota-matcher格式

        Args:
            quantities: 工程量列表

        Returns:
            Dict: 格式化的工程量数据
        """
        # 转换为quota-matcher期望的格式
        return {
            "items": [
                {
                    "name": q.name,
                    "value": q.value,
                    "unit": q.unit,
                    "source": q.source
                }
                for q in quantities
            ],
            "total_count": len(quantities)
        }

    def generate_quota_request(self, quantities: List[ExtractedQuantity], description: str = "") -> str:
        """生成定额匹配请求

        Args:
            quantities: 工程量列表
            description: 额外描述

        Returns:
            str: 匹配请求字符串
        """
        lines = [f"工程量清单（共{len(quantities)}项）"]
        if description:
            lines.append(f"描述: {description}")
        lines.append("")

        for i, q in enumerate(quantities, 1):
            lines.append(f"{i}. {q.name}: {q.value} {q.unit}")

        return "\n".join(lines)