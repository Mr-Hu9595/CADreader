# -*- coding: utf-8 -*-
"""飞书集成模块

将CADreader解析结果上传至飞书表格/文档/知识库
支持 lark-cli 命令行工具
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FeishuDoc:
    """飞书文档"""
    token: str
    url: str
    title: str


@dataclass
class FeishuTable:
    """飞书表格"""
    token: str
    url: str
    sheet_title: str


class FeishuConnector:
    """飞书连接器

    使用lark-cli将工程图纸解析结果上传至飞书
    """

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """初始化飞书连接器

        Args:
            app_id: 飞书应用ID（可选）
            app_secret: 飞书应用密钥（可选）
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None

    def _run_lark_cli(self, args: List[str], input_data: Optional[str] = None) -> subprocess.CompletedProcess:
        """运行lark-cli命令

        Args:
            args: 命令参数列表
            input_data: 可选的输入数据（用于stdin）

        Returns:
            subprocess.CompletedProcess: 命令结果
        """
        # Windows上需要使用.cmd扩展名
        import platform
        cli_cmd = "lark-cli.cmd" if platform.system() == "Windows" else "lark-cli"
        cmd = [cli_cmd] + args
        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=input_data,
                encoding='utf-8',
                shell=True  # Windows需要shell=True来执行.cmd文件
            )
            if result.returncode != 0:
                logger.warning(f"命令失败: {result.stderr}")
            return result
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            raise

    def _run_lark_cli_with_stdin(self, args: List[str], stdin_data: str) -> subprocess.CompletedProcess:
        """运行lark-cli命令，通过stdin传递数据

        Args:
            args: 命令参数列表
            stdin_data: 通过stdin传递的数据

        Returns:
            subprocess.CompletedProcess: 命令结果
        """
        import platform
        cli_cmd = "lark-cli.cmd" if platform.system() == "Windows" else "lark-cli"
        cmd = [cli_cmd] + args
        logger.info(f"执行命令(STDIN): {' '.join(cmd)[:50]}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=stdin_data,
                encoding='utf-8',
                shell=True
            )
            if result.returncode != 0:
                logger.warning(f"命令失败: {result.stderr}")
            return result
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            raise

    def create_document(self, title: str, parent_node_token: Optional[str] = None,
                        space_id: Optional[str] = None,
                        initial_content: str = "") -> Optional[FeishuDoc]:
        """创建飞书文档

        Args:
            title: 文档标题
            parent_node_token: 父节点token（可选）
            space_id: 知识库空间ID（可选）
            initial_content: 初始内容（Markdown格式，可选）

        Returns:
            FeishuDoc: 创建的文档信息，失败返回None
        """
        args = ["docs", "+create", "--title", title, "--markdown", "-"]

        if parent_node_token:
            args.extend(["--parent-node-token", parent_node_token])
        if space_id:
            args.extend(["--wiki-space", space_id])

        # 如果没有初始内容，使用一个空行
        if not initial_content:
            initial_content = "\n"

        result = self._run_lark_cli_with_stdin(args, initial_content)

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                doc_token = output.get("data", {}).get("doc_id", output.get("data", {}).get("doc", {}).get("token", ""))
                doc_url = output.get("data", {}).get("doc_url", output.get("data", {}).get("doc", {}).get("url", ""))
                return FeishuDoc(token=doc_token, url=doc_url, title=title)
            except json.JSONDecodeError:
                logger.info(f"文档创建输出: {result.stdout}")
                return FeishuDoc(token="created", url="", title=title)
        else:
            logger.error(f"文档创建失败: {result.stderr}")
            return None

    def update_document(self, doc_token: str, markdown_content: str) -> bool:
        """更新飞书文档内容

        Args:
            doc_token: 文档token
            markdown_content: Markdown格式内容

        Returns:
            bool: 是否成功
        """
        # 使用stdin传递markdown内容（避免shell转义问题）
        args = ["docs", "+update", "--doc", doc_token, "--markdown", "-", "--mode", "overwrite"]

        result = self._run_lark_cli_with_stdin(args, markdown_content)

        if result.returncode == 0:
            logger.info(f"文档更新成功")
            return True
        else:
            logger.error(f"文档更新失败: {result.stderr}")
            return False

    def list_spaces(self) -> List[Dict]:
        """列出所有可访问的知识库空间

        Returns:
            List[Dict]: 空间列表
        """
        result = self._run_lark_cli(["wiki", "+space-list"])

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                spaces = output.get("data", {}).get("spaces", [])
                return [
                    {"space_id": s.get("space_id"), "name": s.get("name")}
                    for s in spaces
                ]
            except json.JSONDecodeError:
                return []
        return []

    def list_nodes(self, space_id: Optional[str] = None, parent_node_token: Optional[str] = None) -> List[Dict]:
        """列出知识库节点

        Args:
            space_id: 空间ID（可选）
            parent_node_token: 父节点token（可选）

        Returns:
            List[Dict]: 节点列表
        """
        args = ["wiki", "+node-list"]
        if space_id:
            args.extend(["--space-id", space_id])
        if parent_node_token:
            args.extend(["--parent-node-token", parent_node_token])

        result = self._run_lark_cli(args)

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                nodes = output.get("data", {}).get("nodes", [])
                return nodes
            except json.JSONDecodeError:
                return []
        return []

    def upload_to_sheet(self, data: List[Dict], spreadsheet_token: str,
                        sheet_index: int = 0) -> bool:
        """上传数据到飞书表格

        Args:
            data: 数据列表（每项为字典）
            spreadsheet_token: 表格token
            sheet_index: 工作表索引

        Returns:
            bool: 是否成功
        """
        # 将数据转为JSON格式
        data_json = json.dumps(data, ensure_ascii=False)

        args = [
            "sheets", "+row-prepend",
            "--spreadsheet", spreadsheet_token,
            "--sheet", str(sheet_index),
            "--data", data_json
        ]

        result = self._run_lark_cli(args)
        return result.returncode == 0

    def parse_and_upload_vlm_result(self, vlm_result: Dict, title: str = "工程图纸解析报告",
                                    parent_node_token: Optional[str] = None) -> Optional[FeishuDoc]:
        """解析VLM结果并上传到飞书

        Args:
            vlm_result: VLM解析结果（包含devices, dimensions, annotations等）
            title: 文档标题
            parent_node_token: 父节点token（可选）

        Returns:
            FeishuDoc: 创建的文档，失败返回None
        """
        # 生成Markdown报告
        md_content = self._generate_vlm_markdown(vlm_result, title)

        # 创建文档
        doc = self.create_document(title, parent_node_token=parent_node_token)
        if not doc:
            logger.error("文档创建失败")
            return None

        # 更新文档内容
        if self.update_document(doc.token, md_content):
            return doc
        else:
            logger.error("文档内容更新失败")
            return None

    def _generate_vlm_markdown(self, vlm_result: Dict, title: str) -> str:
        """生成VLM结果的Markdown格式

        Args:
            vlm_result: VLM解析结果
            title: 标题

        Returns:
            str: Markdown内容
        """
        md = f"# {title}\n\n"

        # 设备清单
        if "devices" in vlm_result and vlm_result["devices"]:
            md += "## 设备清单\n\n"
            md += "| 编号 | 名称 | 位置 | 坐标 |\n"
            md += "|------|------|------|------|\n"
            for device in vlm_result["devices"]:
                dev_id = device.get("id", "-")
                name = device.get("name", "-")
                location = device.get("location", "-")
                coords = device.get("coords", [])
                coords_str = f"[{coords[0]:.0f}, {coords[1]:.0f}]" if coords else "-"
                md += f"| {dev_id} | {name} | {location} | {coords_str} |\n"
            md += "\n"

        # 尺寸标注
        if "dimensions" in vlm_result and vlm_result["dimensions"]:
            md += "## 尺寸标注\n\n"
            for dim in vlm_result["dimensions"]:
                value = dim.get("value", "-")
                unit = dim.get("unit", "")
                location = dim.get("location", "")
                md += f"- **{value}** {unit} ({location})\n"
            md += "\n"

        # 文本标注
        if "annotations" in vlm_result and vlm_result["annotations"]:
            md += "## 文本标注\n\n"
            for ann in vlm_result["annotations"][:50]:  # 限制数量
                md += f"- {ann}\n"
            if len(vlm_result["annotations"]) > 50:
                md += f"- ... 共 {len(vlm_result['annotations'])} 条\n"
            md += "\n"

        # 技术要求
        if "technical_requirements" in vlm_result and vlm_result["technical_requirements"]:
            md += "## 技术要求\n\n"
            for req in vlm_result["technical_requirements"]:
                md += f"- {req}\n"
            md += "\n"

        # 图层信息
        if "layers" in vlm_result and vlm_result["layers"]:
            md += "## 图层信息\n\n"
            for layer in vlm_result["layers"]:
                md += f"- {layer}\n"
            md += "\n"

        # 概述
        if "summary" in vlm_result:
            md += f"## 概述\n\n{vlm_result['summary']}\n\n"

        return md

    def create_device_report(self, devices: List[Dict], title: str = "设备清单报告",
                             parent_node_token: Optional[str] = None) -> Optional[FeishuDoc]:
        """创建设备清单报告

        Args:
            devices: 设备列表
            title: 报告标题
            parent_node_token: 父节点token

        Returns:
            FeishuDoc: 创建的文档
        """
        # 生成Markdown
        md = f"# {title}\n\n"
        md += f"## 设备统计\n\n共 {len(devices)} 台设备\n\n"

        # 按设备类型分组统计
        by_category = {}
        for dev in devices:
            category = dev.get("category", "未分类")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(dev)

        md += "### 按类型分类\n\n"
        for category, devs in by_category.items():
            md += f"- **{category}**: {len(devs)} 台\n"

        md += "\n### 设备详情\n\n"
        md += "| 编号 | 名称 | 规格 | 数量 | 类型 |\n"
        md += "|------|------|------|------|------|\n"
        for dev in devices:
            dev_id = dev.get("id", "-")
            name = dev.get("name", "-")
            spec = dev.get("spec", "-")
            qty = dev.get("quantity", 1)
            category = dev.get("category", "-")
            md += f"| {dev_id} | {name} | {spec} | {qty} | {category} |\n"

        # 创建文档
        doc = self.create_document(title, parent_node_token=parent_node_token)
        if doc:
            self.update_document(doc.token, md)

        return doc


def upload_parse_result_to_feishu(parse_result, feishu_connector: FeishuConnector,
                                   title: str = "工程图纸解析报告") -> Optional[FeishuDoc]:
    """将CADreader解析结果上传到飞书

    Args:
        parse_result: CADReader.parse()返回的ParsedDrawing对象
        feishu_connector: FeishuConnector实例
        title: 文档标题

    Returns:
        FeishuDoc: 创建的文档，失败返回None
    """
    # 转换为VLM格式（简化版）
    vlm_result = {
        "annotations": [a.value for a in parse_result.annotations[:100]],
        "metadata": parse_result.metadata,
        "summary": f"从 {parse_result.metadata.get('source', 'Unknown')} 解析"
    }

    # 设备（从块引用提取）
    devices = []
    for p in parse_result.primitives:
        if p.type == 'block' and p.layer:
            devices.append({
                "id": p.layer,
                "name": "设备",
                "location": "",
                "coords": p.params[:2] if p.params else []
            })

    if devices:
        vlm_result["devices"] = devices

    return feishu_connector.parse_and_upload_vlm_result(vlm_result, title)


def main():
    """测试飞书集成"""
    import argparse

    parser = argparse.ArgumentParser(description='飞书集成测试')
    parser.add_argument('--list-spaces', action='store_true', help='列出知识库空间')
    parser.add_argument('--create-doc', help='创建文档标题')

    args = parser.parse_args()

    connector = FeishuConnector()

    if args.list_spaces:
        print("获取知识库空间列表...")
        spaces = connector.list_spaces()
        for space in spaces:
            print(f"  - {space.get('name')} ({space.get('space_id')})")

    if args.create_doc:
        print(f"创建文档: {args.create_doc}")
        doc = connector.create_document(args.create_doc)
        if doc:
            print(f"文档已创建: {doc.token}")


if __name__ == '__main__':
    main()