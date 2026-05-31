#!/usr/bin/env python3
"""数据合并脚本 - 整合所有解析结果到统一知识库"""
import sys
import json
import csv
from pathlib import Path
from datetime import datetime


def load_json(path: Path) -> dict:
    """加载JSON文件"""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv(path: Path) -> list:
    """加载CSV文件"""
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def merge_devices() -> list:
    """合并所有设备数据"""
    base_dir = Path(r"D:\工作\日常工作\首山碳材环保管控平台\data")

    # 数据源
    sources = {
        '现有知识库': base_dir / "设备台账" / "项目知识库_v2.json",
        '雾炮设备': base_dir / "图纸解析结果" / "设备清单" / "雾炮设备.json",
        '网络设备': base_dir / "图纸解析结果" / "网络拓扑" / "网络拓扑关系.csv",
    }

    all_devices = []
    seen_ids = set()

    # 1. 加载现有知识库
    existing = load_json(sources['现有知识库'])
    for dev in existing.get('设备数据库', []):
        all_devices.append(dev)
        seen_ids.add(dev.get('设备编号'))

    print(f"从现有知识库加载: {len(existing.get('设备数据库', []))}条目")

    # 2. 加载雾炮设备
    wopaoc = load_json(sources['雾炮设备'])
    wopaoc_count = 0
    for dev in wopaoc:
        dev_id = dev.get('设备编号')
        if dev_id and dev_id not in seen_ids:
            all_devices.append({
                '设备编号': dev_id,
                '设备类型': '雾炮设备',
                '设备名称': dev.get('设备名称', f"雾炮塔架 {dev_id}"),
                'X坐标': dev.get('X坐标'),
                'Y坐标': dev.get('Y坐标'),
                '数据来源': '图纸解析'
            })
            seen_ids.add(dev_id)
            wopaoc_count += 1

    print(f"从雾炮设备添加: {wopaoc_count}条目")

    # 3. 加载网络设备
    network = load_csv(sources['网络设备'])
    network_count = 0
    for dev in network:
        dev_id = dev.get('设备编号')
        if dev_id and dev_id not in seen_ids:
            # 解析坐标字段
            coord_str = dev.get('坐标', '{}')
            try:
                coord = eval(coord_str) if isinstance(coord_str, str) else coord_str
                x = coord.get('X', 0) if isinstance(coord, dict) else 0
                y = coord.get('Y', 0) if isinstance(coord, dict) else 0
            except:
                x, y = 0, 0

            all_devices.append({
                '设备编号': dev_id,
                '设备类型': dev.get('设备类型', '网络设备'),
                '设备名称': dev.get('设备类型', '网络设备'),
                'X坐标': x,
                'Y坐标': y,
                '数据来源': '图纸解析'
            })
            seen_ids.add(dev_id)
            network_count += 1

    print(f"从网络设备添加: {network_count}条目")

    return all_devices


def main():
    print("=" * 50)
    print("开始合并数据...")
    print("=" * 50)

    devices = merge_devices()
    print(f"\n设备总数: {len(devices)}")

    # 按设备类型统计
    types = {}
    for dev in devices:
        t = dev.get('设备类型', '未知')
        types[t] = types.get(t, 0) + 1

    print("\n设备类型分布:")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # 构建新版知识库
    knowledge_base = {
        '项目名称': '首山碳材环保管控平台',
        '版本': '3.0',
        '生成时间': datetime.now().isoformat(),
        '数据来源': [
            '设备材料采购清单汇总表20260421.xlsx',
            'TSP设备清单-20260205.pdf',
            '微站设备清单-20260205.pdf',
            '监控设备清单-20260205.pdf',
            '首山焦化四期初步设计图纸',
            '图纸解析结果_v1'
        ],
        '设备数据库': devices,
        '统计': {
            '总设备数': len(devices),
            '类型分布': types
        }
    }

    # 保存
    output_path = Path(r"D:\工作\日常工作\首山碳材环保管控平台\data\设备台账\项目知识库_v3.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    print(f"\n知识库已更新: {output_path}")
    print(f"版本: 3.0")


if __name__ == '__main__':
    main()
