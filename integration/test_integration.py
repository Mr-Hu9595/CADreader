# -*- coding: utf-8 -*-
"""CADreader与现有skills集成测试

测试场景：
1. CADreader + FeiShuCLI: 解析DXF图纸并上传到Wiki知识库
2. CADreader + 数据提取: 提取设备清单并结构化
3. CADreader + quota-matcher: 提取工程量进行定额匹配
"""

import sys
import os
import json
from pathlib import Path

# 添加cadreader根目录到路径
base_path = r"D:\工作\AiAgents\skills\cadreader"
sys.path.insert(0, base_path)

from src import CADReader
from integration.feishu_connector import FeishuConnector


def test_dxf_to_feishu():
    """测试1: DXF图纸解析 + 飞书上传统一工作流"""
    print("\n" + "="*60)
    print("测试1: DXF图纸解析 + 飞书上传统一工作流")
    print("="*60)

    # 1. 初始化
    reader = CADReader()
    connector = FeishuConnector()

    # 2. DXF文件路径
    dxf_path = r"D:\工作\日常工作\首山碳材环保管控平台\首山四期图纸\10米高雾炮塔架土建基础图 - 20251209.dxf"

    if not Path(dxf_path).exists():
        print(f"文件不存在: {dxf_path}")
        return None

    # 3. 先渲染DXF为图像
    print("\nStep 1: 渲染DXF为图像...")
    try:
        image_path = reader.parse_to_image(dxf_path, r"D:\工作\AiAgents\skills\cadreader\data\test_dxf.png")
        print(f"图像已保存: {image_path}")
    except Exception as e:
        print(f"渲染失败: {e}")
        return None

    # 4. VLM解析需要MCP环境，这里仅返回图像路径供手动测试
    print("\nStep 2: VLM分析需要MCP环境，请在Claude Code中调用mcp__MiniMax__understand_image测试")
    print(f"图像路径: {image_path}")
    return image_path


def test_dxf_to_device_list():
    """测试2: DXF图纸解析 + 设备清单提取（不依赖transformers）"""
    print("\n" + "="*60)
    print("测试2: DXF图纸解析 + 设备清单提取（核心功能）")
    print("="*60)

    # 1. 直接使用DWGParser解析DXF
    dxf_path = r"D:\工作\日常工作\首山碳材环保管控平台\首山四期图纸\10米高雾炮塔架土建基础图 - 20251209.dxf"

    if not Path(dxf_path).exists():
        print(f"文件不存在: {dxf_path}")
        return None

    print("\nStep 1: 使用DWGParser解析DXF...")
    from src.parsers import DWGParser

    with DWGParser(dxf_path) as parser:
        # 统计实体
        entities = list(parser.iter_entities())
        print(f"  总实体数: {len(entities)}")

        # 统计类型
        type_counts = {}
        for e in entities:
            t = e.dxftype()
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"  实体类型统计: {type_counts}")

        # 提取文本
        texts = parser.get_texts()
        print(f"  文本数量: {len(texts)}")

        # 提取块引用
        blocks = parser.get_blocks()
        print(f"  块引用数量: {len(blocks)}")

    # 2. 提取设备（从块引用）
    devices = []
    for block in blocks:
        if block.get('name'):
            devices.append({
                "id": block.get('name'),
                "name": "块引用",
                "location": "",
                "coords": block.get('location', [])[:2] if block.get('location') else []
            })

    print(f"\nStep 2: 设备清单")
    print(f"  块引用设备: {len(devices)}")
    for d in devices[:5]:
        print(f"    - {d['id']}: {d['coords']}")

    # 3. 文本标注
    annotations = [t.get('text', '') for t in texts if t.get('text', '').strip()]
    print(f"  文本标注: {len(annotations)}")
    for i, ann in enumerate(annotations[:5]):
        text = ann[:50].replace('\n', ' ')
        print(f"    {i+1}. {text}")

    return {
        "devices": devices,
        "annotations": annotations
    }


def test_pdf_to_feishu():
    """测试3: PDF解析 + 飞书上传统一工作流"""
    print("\n" + "="*60)
    print("测试3: PDF设备清单解析 + 飞书上传统一工作流")
    print("="*60)

    # 1. 初始化
    reader = CADReader()
    connector = FeishuConnector()

    # 2. PDF文件路径
    pdf_path = r"D:\工作\日常工作\首山碳材环保管控平台\首山四期图纸\首山焦化四期初步设计图纸-20251209\1、无组织TSP、微站部分\2，工艺图\2、TSP设备清单-20260205.pdf"

    if not Path(pdf_path).exists():
        print(f"文件不存在: {pdf_path}")
        return None

    # 3. PDF结构解析
    print("\nStep 1: PDF结构解析...")
    pdf_result = reader.parse(pdf_path)
    print(f"  页数: {pdf_result.metadata.get('page_count', 0)}")
    print(f"  文本数: {pdf_result.metadata.get('text_count', 0)}")
    print(f"  图像数: {pdf_result.metadata.get('image_count', 0)}")

    # 4. 渲染PDF为图像用于VLM
    print("\nStep 2: 渲染PDF为图像...")
    output_dir = r"D:\工作\AiAgents\skills\cadreader\data"
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir=output_dir) as f:
        image_path = f.name

    from cadreader.pdf_parser import render_pdf_page
    render_pdf_page(pdf_path, page_num=0, output_path=image_path, dpi=150)
    print(f"  图像: {image_path}")

    return image_path


def main():
    """主测试函数"""
    print("CADreader Skills集成测试")
    print("="*60)

    # 测试1: DXF + 飞书
    test_dxf_to_feishu()

    # 测试2: DXF设备清单提取
    test_dxf_to_device_list()

    # 测试3: PDF + 飞书
    test_pdf_to_feishu()

    print("\n" + "="*60)
    print("测试完成!")


if __name__ == '__main__':
    main()
