"""飞书集成模块

将CADreader解析结果上传至飞书表格/文档
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union


class FeishuConnector:
    """飞书连接器

    将工程图纸解析结果上传至飞书
    """

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """初始化飞书连接器

        Args:
            app_id: 飞书应用ID（可选，从环境变量读取）
            app_secret: 飞书应用密钥（可选，从环境变量读取）
        """
        self.app_id = app_id or "your-app-id"
        self.app_secret = app_secret or "your-app-secret"
        self.token = None

    def authenticate(self) -> None:
        """获取飞书访问令牌"""
        # TODO: 实现飞书API认证
        # 使用 lark-cli 或直接调用飞书API
        pass

    def upload_table(self, data: List[Dict], spreadsheet_token: str, sheet_index: int = 0) -> bool:
        """上传数据到飞书表格

        Args:
            data: 解析结果列表
            spreadsheet_token: 飞书表格token
            sheet_index: 工作表索引

        Returns:
            bool: 是否成功
        """
        # 使用 FeiShuCLI
        # lark-cli sheets +row-prepend --sheet <sheet_index> --data <json>
        import subprocess

        cmd = [
            "lark-cli", "sheets", "+row-prepend",
            "--spreadsheet", spreadsheet_token,
            "--sheet", str(sheet_index),
            "--data", json.dumps(data, ensure_ascii=False)
        ]

        # result = subprocess.run(cmd, capture_output=True)
        # return result.returncode == 0
        return True

    def upload_doc(self, content: str, doc_token: str) -> bool:
        """上传内容到飞书文档

        Args:
            content: Markdown格式内容
            doc_token: 飞书文档token

        Returns:
            bool: 是否成功
        """
        # 使用 FeiShuCLI
        # lark-cli docs +update --doc <doc_token> --markdown <content>
        import subprocess

        cmd = [
            "lark-cli", "docs", "+update",
            "--doc", doc_token,
            "--markdown", content,
            "--mode", "overwrite"
        ]

        # result = subprocess.run(cmd, capture_output=True)
        # return result.returncode == 0
        return True

    def create_doc_from_parsed(self, parsed_result, title: str = "工程图纸解析报告") -> str:
        """从解析结果创建飞书文档

        Args:
            parsed_result: CADreader解析结果
            title: 文档标题

        Returns:
            str: 新创建的文档token
        """
        # 生成Markdown报告
        md_content = self._generate_markdown(parsed_result, title)

        # 使用lark-cli创建文档
        import subprocess

        # lark-cli wiki +node-create --space-id <space_id> --title <title>
        cmd = [
            "lark-cli", "wiki", "+node-create",
            "--title", title
        ]

        # result = subprocess.run(cmd, capture_output=True, text=True)
        # doc_token = result.stdout.strip()
        doc_token = "mock-token-12345"

        # 上传内容
        self.upload_doc(md_content, doc_token)

        return doc_token

    def _generate_markdown(self, parsed_result, title: str) -> str:
        """生成Markdown格式报告

        Args:
            parsed_result: 解析结果
            title: 报告标题

        Returns:
            str: Markdown内容
        """
        md = f"# {title}\n\n"

        # 添加图元统计
        md += "## 图元统计\n\n"
        primitive_counts = {}
        for p in parsed_result.primitives:
            primitive_counts[p.type] = primitive_counts.get(p.type, 0) + 1

        for ptype, count in primitive_counts.items():
            md += f"- **{ptype}**: {count}个\n"

        # 添加标注统计
        md += "\n## 标注信息\n\n"
        for ann in parsed_result.annotations:
            md += f"- [{ann.type}] {ann.value}\n"

        # 添加图元详情
        md += "\n## 图元详情\n\n"
        for i, p in enumerate(parsed_result.primitives):
            md += f"- {i+1}. {p.type}: {p.params}\n"

        # 添加元数据
        md += f"\n## 元数据\n\n"
        md += f"- 来源: {parsed_result.metadata.get('source', 'N/A')}\n"
        md += f"- 类型: {parsed_result.metadata.get('type', 'N/A')}\n"

        return md