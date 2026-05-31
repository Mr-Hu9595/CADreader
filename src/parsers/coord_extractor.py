"""坐标提取器"""
from typing import List, Dict, Any, Tuple
from .dwg_parser import DWGParser


class CoordExtractor:
    """设备空间坐标提取器"""

    def __init__(self):
        self.coordinates = []

    def extract_from_parser(self, parser: DWGParser, device_map: Dict[str, Dict] = None) -> List[Dict[str, Any]]:
        """从DWG解析器提取坐标信息

        Args:
            parser: DWG解析器实例
            device_map: 设备编号到设备信息的映射，用于关联
        """
        blocks = parser.get_blocks()
        device_map = device_map or {}

        for block in blocks:
            coord_info = {
                '设备编号': block['name'],
                'X': block['location'][0],
                'Y': block['location'][1],
                'Z': block['location'][2] if len(block['location']) > 2 else 0,
                '旋转角度': block.get('rotation', 0),
                '图纸文件': parser.dwg_path
            }

            # 关联设备信息
            if block['name'] in device_map:
                coord_info['设备类型'] = device_map[block['name']].get('设备类型')
                coord_info['设备名称'] = device_map[block['name']].get('设备名称')

            self.coordinates.append(coord_info)

        return self.coordinates

    def to_csv(self) -> List[Dict[str, Any]]:
        """导出为CSV格式"""
        return self.coordinates

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """获取坐标边界 (min_x, min_y, max_x, max_y)"""
        if not self.coordinates:
            return (0, 0, 0, 0)

        xs = [c['X'] for c in self.coordinates]
        ys = [c['Y'] for c in self.coordinates]

        return (min(xs), min(ys), max(xs), max(ys))