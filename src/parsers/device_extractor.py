"""设备信息提取器"""
from typing import List, Dict, Any, Optional
import re
from .dwg_parser import DWGParser


class DeviceExtractor:
    """设备信息提取器"""

    # 设备类型正则匹配
    DEVICE_PATTERNS = {
        '交换机': r'^SW\d+$',           # SW01, SW02
        '光模块': r'^FAP19-FB-G\d+/\d+$',  # FAP19-FB-G1/2
        '电口模块': r'^-S\d+-RJ45$',    # -S086-RJ45
        '雾炮': r'^WP-\d+$',            # WP-01, WP-02
        'TSP监测': r'^T\d+$',           # T001, T002
        '微站': r'^WZ-[A-Z]$',          # WZ-A, WZ-B
        '监控': r'^S-\d+$',             # S-075, S-076
        '光纤收发器': r'^Fiber',         # Fiber-xxx
    }

    def __init__(self):
        self.devices = []

    def extract_from_parser(self, parser: DWGParser) -> List[Dict[str, Any]]:
        """从DWG解析器提取设备信息"""
        blocks = parser.get_blocks()
        texts = parser.get_texts()

        # 建立文字标注与位置的映射
        text_by_pos = self._group_texts_by_position(texts)

        # 提取设备
        for block in blocks:
            device = self._identify_device(block)
            if device:
                device['坐标'] = block['location']
                device['图纸来源'] = parser.dwg_path
                self.devices.append(device)

        return self.devices

    def _identify_device(self, block: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """识别设备类型"""
        name = block['name']
        attribs = block.get('attribs', {})

        # 尝试从块名称匹配
        for dev_type, pattern in self.DEVICE_PATTERNS.items():
            if re.match(pattern, name):
                return {
                    '设备编号': name,
                    '设备类型': dev_type,
                    '属性': attribs,
                    '旋转角度': block.get('rotation', 0)
                }

        # 尝试从属性中识别
        for tag, value in attribs.items():
            for dev_type, pattern in self.DEVICE_PATTERNS.items():
                if re.match(pattern, str(value)):
                    return {
                        '设备编号': str(value),
                        '设备类型': dev_type,
                        '属性': attribs,
                        '旋转角度': block.get('rotation', 0)
                    }

        return None

    def _group_texts_by_position(self, texts: List[Dict[str, Any]], tolerance: float = 50) -> Dict:
        """将文字按位置分组"""
        grouped = {}
        for text in texts:
            if text['location'] is None:
                continue
            x, y = text['location'][0], text['location'][1]
            key = (round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(text['text'])
        return grouped

    def to_json(self) -> List[Dict[str, Any]]:
        """导出为JSON格式"""
        return self.devices

    def to_csv_rows(self) -> List[Dict[str, Any]]:
        """导出为CSV格式（扁平化）"""
        rows = []
        for dev in self.devices:
            row = {
                '设备编号': dev.get('设备编号'),
                '设备类型': dev.get('设备类型'),
                'X坐标': dev.get('坐标', (None, None, None))[0] if dev.get('坐标') else None,
                'Y坐标': dev.get('坐标', (None, None, None))[1] if dev.get('坐标') else None,
                'Z坐标': dev.get('坐标', (None, None, None))[2] if dev.get('坐标') else None,
                '旋转角度': dev.get('旋转角度'),
                '图纸来源': dev.get('图纸来源'),
            }
            rows.append(row)
        return rows