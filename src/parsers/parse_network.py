#!/usr/bin/env python3
"""网络系统图专项解析脚本

解析首山碳材料治理项目网络系统图251209.xlsx
提取：交换机、路由器、光纤配线架、网络设备、连接关系
"""
import sys
import os
import json
import csv
import re
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_network_excel(xlsx_path: str, output_dir: str):
    """解析网络系统图Excel

    从DwgExporter导出的Excel中提取：
    1. 网络设备（交换机SW、路由器RX/TX、光纤配线架ODF、光纤终端盒FAP）
    2. 文字标注（设备名称、位置、端口信息）
    3. 线段连接关系
    """
    logger.info(f"开始解析网络系统图: {xlsx_path}")

    # 读取Excel（限制行数避免内存问题）
    df = pd.read_excel(xlsx_path, sheet_name=0, nrows=20000)
    logger.info(f"读取到 {len(df)} 行数据")

    # 提取各种元素
    devices = []      # 块引用设备
    mtexts = []       # 多行文本
    lines = []        # 线段
    circles = []      # 圆（可能用于设备）

    # 筛选BlockReference
    block_refs = df[df['Description'] == '<AcDbBlockReference>']
    logger.info(f"BlockReference数量: {len(block_refs)}")

    # 筛选MText
    mtext_df = df[df['Description'] == '<AcDbMText>']
    logger.info(f"MText数量: {len(mtext_df)}")

    # 筛选Line
    line_df = df[df['Description'] == '<AcDbLine>']
    logger.info(f"Line数量: {len(line_df)}")

    # 筛选Circle
    circle_df = df[df['Description'] == '<AcDbCircle>']
    logger.info(f"Circle数量: {len(circle_df)}")

    # 从MText中提取网络设备信息
    network_devices = []
    device_positions = {}  # 设备名 -> 位置
    text_items = []

    # 网络设备关键词
    device_patterns = {
        'SW': '交换机',
        'ODF': '光纤配线架',
        'FAP': '光纤终端盒',
        'RX': '路由器',
        'TX': '发送器',
        'ORA': '光接收放大器',
        'S0': '光纤配线架',
    }

    # 解析MText内容
    for _, row in mtext_df.iterrows():
        content = str(row.get('Contents', ''))
        text_str = str(row.get('Text', ''))
        pos = str(row.get('Position', ''))

        if content and content not in ['nan', '\"\"', '']:
            # 清理转义字符
            clean_content = content.replace('\\P', '\n').replace('\\{', '{').replace('\\}', '}')

            # 查找设备名称
            for pattern, dev_type in device_patterns.items():
                if pattern in clean_content:
                    # 提取设备编号
                    match = re.search(rf'{pattern}(\d+)', clean_content)
                    if match:
                        dev_id = f"{pattern}{match.group(1)}"
                    else:
                        dev_id = pattern

                    # 提取坐标
                    coords = parse_position(pos)

                    device_info = {
                        '设备编号': dev_id,
                        '设备类型': dev_type,
                        '原始文本': clean_content[:100],
                        '坐标': coords,
                        '来源': 'MText'
                    }
                    network_devices.append(device_info)
                    device_positions[dev_id] = coords

            # 记录所有有意义的文本
            if len(clean_content) > 2:
                text_items.append({
                    '内容': clean_content[:200],
                    '坐标': parse_position(pos)
                })

    # 合并重复设备
    unique_devices = {}
    for dev in network_devices:
        dev_id = dev['设备编号']
        if dev_id not in unique_devices:
            unique_devices[dev_id] = dev

    network_devices = list(unique_devices.values())
    logger.info(f"提取到 {len(network_devices)} 个网络设备")
    logger.info(f"提取到 {len(text_items)} 条文本标注")

    # 从Line提取连接关系
    connections = []
    for _, row in line_df.iterrows():
        start = str(row.get('Start Point', row.get('StartPoint', '')))
        end = str(row.get('End Point', row.get('EndPoint', '')))
        if start != 'nan' and end != 'nan':
            connections.append({
                '起点': parse_position(start),
                '终点': parse_position(end),
                '类型': '连接线'
            })

    logger.info(f"提取到 {len(connections)} 条线段")

    # 统计信息
    device_types = {}
    for dev in network_devices:
        dtype = dev['设备类型']
        device_types[dtype] = device_types.get(dtype, 0) + 1

    # 创建输出目录
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON输出
    result = {
        '图纸文件': xlsx_path,
        '解析时间': datetime.now().isoformat(),
        '设备清单': network_devices,
        '文字标注': text_items[:500] if text_items else [],
        '连接线段': connections[:200] if connections else [],
        '统计': {
            '总设备数': len(network_devices),
            '设备类型分布': device_types,
            '文本标注数': len(text_items),
            '连接线段数': len(connections)
        }
    }

    json_path = output_dir / '网络系统图_解析结果.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON结果已保存: {json_path}")

    # CSV输出（设备清单）
    if network_devices:
        csv_path = output_dir / '网络拓扑关系.csv'
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['设备编号', '设备类型', '坐标', '来源', '原始文本'])
            writer.writeheader()
            for dev in network_devices:
                writer.writerow({
                    '设备编号': dev['设备编号'],
                    '设备类型': dev['设备类型'],
                    '坐标': str(dev['坐标']),
                    '来源': dev['来源'],
                    '原始文本': dev['原始文本'][:50]
                })
        logger.info(f"CSV结果已保存: {csv_path}")

    return result


def parse_position(pos_str):
    """解析位置字符串 'x, y, z' 为字典"""
    if not pos_str or pos_str == 'nan':
        return {'X': 0, 'Y': 0, 'Z': 0}

    try:
        # 常见格式: 'x, y, z' 或 '[x, y, z]'
        pos_str = str(pos_str).strip('[]')
        parts = pos_str.split(',')
        if len(parts) >= 2:
            return {
                'X': float(parts[0].strip()),
                'Y': float(parts[1].strip()),
                'Z': float(parts[2].strip()) if len(parts) > 2 else 0
            }
    except:
        pass

    return {'X': 0, 'Y': 0, 'Z': 0}


if __name__ == '__main__':
    xlsx_path = r"D:\工作\日常工作\首山碳材环保管控平台\首山四期图纸\首山焦化四期初步设计图纸-20251209\2、网络设计\首山碳材料治理项目网络系统图251209_dwg_20260507_155935.xlsx"
    output_dir = r"D:\工作\日常工作\首山碳材环保管控平台\data\图纸解析结果\网络拓扑"

    if not os.path.exists(xlsx_path):
        logger.error(f"文件不存在: {xlsx_path}")
        sys.exit(1)

    result = parse_network_excel(xlsx_path, output_dir)
    print(f"\n解析完成!")
    print(f"  - 设备总数: {result['统计']['总设备数']}")
    for dtype, count in result['统计']['设备类型分布'].items():
        print(f"    - {dtype}: {count}")
    print(f"  - 文本标注: {result['统计']['文本标注数']}")
    print(f"  - 连接线段: {result['统计']['连接线段数']}")