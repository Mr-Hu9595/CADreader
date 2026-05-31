# CLAUDE.md - CADreader 工程图纸智能解析工具

## 项目概述

CADreader是基于PHT-CAD（复旦大学开源项目）的工程图纸智能解析工具，专注于工程制图和工程图纸阅读理解。

**核心能力**：
- 从工程图纸（图像/DXF/PDF）中识别4种原子组件：点、线、圆、弧
- 同时解析几何图层 + 标注图层（尺寸、公差）
- 输出结构化JSON，可直接集成到工作流

**定位**：作为AiAgents技能体系中的**图纸解析引擎**，与wiki（知识库）、数据提取、材料计划助手等形成互补。

---

## 与现有skills的融合

```
AiAgents/skills/
├── wiki/                    ← 知识库：收集整理规范标准、技术资料
├── 数据提取/                 ← 数据提取：从PDF/Word/Excel提取数据
├── cadreader/              ← 【新】图纸解析：读取和理解工程图纸 ⭐
├── searcher/                ← 搜索：网络信息查询
├── quota-matcher/          ← 定额匹配：工程量清单智能匹配
├── 材料计划助手/             ← 材料计划：数据填入格式文件
├── FeiShuCLI/              ← 飞书：日历、消息、文档、表格
└── ...
```

### 融合场景

| 场景 | 工具链 |
|------|--------|
| **收集规范时**：下载GB50303-2015 PDF → **cadreader解析** → wiki存储 | PDF → cadreader → wiki |
| **材料计划**：图纸中提取尺寸 → **cadreader提取** → 材料计划助手 | cadreader → 材料计划助手 |
| **定额匹配**：提取工程量 → **cadreader提取** → quota-matcher | cadreader → quota-matcher |
| **报告生成**：图纸解析结果 → **cadreader处理** → 数据提取生成报告 | cadreader → 数据提取 |
| **飞书上传统**：解析结果 → **cadreader结构化** → FeiShuCLI上传 | cadreader → FeiShuCLI |

---

## 项目结构

```
cadreader/
├── CLAUDE.md                 ← 本文件
├── README.md                 ← 项目说明
├── LICENSE                  ← 开源许可证
├── requirements.txt         ← Python依赖
├── setup.py                 ← 安装脚本
├── src/
│   ├── __init__.py
│   ├── engine.py            ← 核心解析引擎
│   ├── parser.py            ← 多格式解析器(DXF/PDF/图像)
│   ├── extractor.py         ← 图元提取器
│   └── integrator.py        ← 与其他skills的集成模块
├── docs/
│   ├── architecture.md      ← 架构设计
│   ├── integration.md       ← 集成指南
│   └── api.md               ← API文档
├── reports/
│   └── PHT-CAD详细调研报告.md  ← PHT-CAD项目调研
├── test/
│   └── test_engine.py       ← 单元测试
├── data/
│   └── samples/             ← 示例图纸
├── integration/
│   ├── wiki_connector.py    ← wiki知识库集成
│   ├── feishu_connector.py  ← 飞书集成
│   └── quota_connector.py   ← 定额匹配集成
└── scripts/
    ├── parse_drawing.py     ← 单图解析脚本
    └── batch_parse.py       ← 批量解析脚本
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| **核心模型** | PHT-CAD（VLM + 四回归头） |
| **VLM基座** | QwenVL / LLaVA |
| **DXF解析** | ezdxf |
| **PDF处理** | pdf2dxf / PyMuPDF |
| **飞书集成** | FeiShuCLI (lark-cli) |
| **数据存储** | JSON / CSV / 飞书表格 |

---

## 使用方法

### 1. 解析工程图纸

```python
from cadreader import CADReader

reader = CADReader()
result = reader.parse("工程图纸.jpg")

# 输出结构化JSON
print(result)
# {
#   "primitives": [
#     {"type": "line", "params": [x1, y1, x2, y2]},
#     {"type": "circle", "params": [cx, cy, r]}
#   ],
#   "annotations": [
#     {"type": "dimension", "value": "3×2.5mm", "linked_to": [0]},
#     {"type": "tolerance", "value": "±0.1"}
#   ]
# }
```

### 2. 批量解析

```bash
python scripts/batch_parse.py --input ./drawings/ --output ./results/
```

### 3. 集成到飞书

```python
from cadreader.integrator import FeishuConnector

connector = FeishuConnector()
connector.upload_result(result, doc_id="<飞书文档ID>")
```

---

## 数据来源

- **PHT-CAD**：https://github.com/yuwen-chen616/PHT-CAD
- **ParaCAD数据集**：https://www.modelscope.cn/datasets/yuwenbonnie/ParaCAD-Dataset/summary
- **论文**：arXiv:2503.18147

---

## 注意事项

1. **数据真实性**：解析结果必须复核，不得捏造
2. **版权合规**：仅处理自有或授权的工程图纸
3. **版本跟踪**：定期同步PHT-CAD更新

---

## 下一步计划

- [ ] 研究PHT-CAD代码结构
- [ ] 设计CADreader核心引擎
- [ ] 开发与wiki的集成接口
- [ ] 开发与FeiShuCLI的集成接口
- [ ] 编写使用文档和API文档

---

最后更新：2026-05-31