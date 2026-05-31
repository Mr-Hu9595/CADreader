"""Wiki知识库集成模块

将解析结果整理上传至飞书Wiki知识库
"""

from typing import Dict, List, Optional
from pathlib import Path


class WikiConnector:
    """Wiki知识库连接器

    将工程图纸信息整理上传至飞书Wiki
    """

    def __init__(self, space_id: Optional[str] = None):
        """初始化Wiki连接器

        Args:
            space_id: 飞书知识库空间ID
        """
        self.space_id = space_id or "your-space-id"

    def create_node(self, title: str, parent_node_id: Optional[str] = None) -> str:
        """创建Wiki节点

        Args:
            title: 节点标题
            parent_node_id: 父节点ID（可选）

        Returns:
            str: 新创建的节点token
        """
        import subprocess

        cmd = [
            "lark-cli", "wiki", "+node-create",
            "--space-id", self.space_id,
            "--title", title
        ]

        if parent_node_id:
            cmd.extend(["--parent", parent_node_id])

        # result = subprocess.run(cmd, capture_output=True, text=True)
        # return result.stdout.strip()
        return "mock-node-token"

    def upload_content(self, node_token: str, content: str, format: str = "markdown") -> bool:
        """上传内容到Wiki节点

        Args:
            node_token: 节点token
            content: 内容（Markdown格式）
            format: 内容格式

        Returns:
            bool: 是否成功
        """
        # 使用lark-cli更新节点内容
        import subprocess

        cmd = [
            "lark-cli", "docs", "+update",
            "--doc", node_token,
            "--markdown", content,
            "--mode", "overwrite"
        ]

        # result = subprocess.run(cmd, capture_output=True)
        # return result.returncode == 0
        return True

    def upload_parsed_drawing(self, parsed_result, category: str = "机电安装工程") -> str:
        """上传解析结果到Wiki

        Args:
            parsed_result: CADreader解析结果
            category: 分类（如"机电安装工程"）

        Returns:
            str: 创建的节点token
        """
        # 1. 生成内容
        content = self._generate_wiki_content(parsed_result, category)

        # 2. 创建节点
        title = f"工程图纸解析_{Path(parsed_result.metadata.get('source', 'unknown')).stem}"
        node_token = self.create_node(title)

        # 3. 上传内容
        self.upload_content(node_token, content)

        return node_token

    def _generate_wiki_content(self, parsed_result, category: str) -> str:
        """生成Wiki格式内容

        Args:
            parsed_result: 解析结果
            category: 分类

        Returns:
            str: Wiki Markdown内容
        """
        md = f"# {category} - 工程图纸解析报告\n\n"

        # 基本信息
        md += "## 基本信息\n\n"
        md += f"- 文件来源: {parsed_result.metadata.get('source', 'N/A')}\n"
        md += f"- 文件类型: {parsed_result.metadata.get('type', 'N/A')}\n"
        md += f"- 解析时间: {parsed_result.metadata.get('timestamp', 'N/A')}\n\n"

        # 图元统计
        md += "## 图元统计\n\n"
        md += "| 图元类型 | 数量 |\n"
        md += "|----------|------|\n"

        primitive_counts = {}
        for p in parsed_result.primitives:
            primitive_counts[p.type] = primitive_counts.get(p.type, 0) + 1

        for ptype, count in primitive_counts.items():
            md += f"| {ptype} | {count} |\n"

        # 图元详情
        md += "\n## 图元详情\n\n"
        md += "| 序号 | 类型 | 参数 | 图层 |\n"
        md += "|------|------|------|------|\n"

        for i, p in enumerate(parsed_result.primitives):
            params_str = ", ".join([str(x) for x in p.params])
            layer = p.layer or "默认"
            md += f"| {i+1} | {p.type} | {params_str} | {layer} |\n"

        # 标注信息
        if parsed_result.annotations:
            md += "\n## 标注信息\n\n"
            md += "| 类型 | 值 | 关联图元 | 单位 |\n"
            md += "|------|---|----------|------|\n"

            for ann in parsed_result.annotations:
                linked = ", ".join([str(x) for x in ann.linked_to])
                unit = ann.unit or "N/A"
                md += f"| {ann.type} | {ann.value} | {linked} | {unit} |\n"

        # 结构约束
        if parsed_result.constraints:
            md += "\n## 结构约束\n\n"
            for c in parsed_result.constraints:
                md += f"- {c.type}: 图元{', '.join([str(x) for x in c.entities])}\n"

        return md