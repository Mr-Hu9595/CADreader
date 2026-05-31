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
├── .gitignore              ← Git忽略配置
├── src/
│   ├── __init__.py        ← 包入口，导出CADReader等
│   ├── engine.py           ← 核心解析引擎（支持规则+VLM双模式）
│   ├── vlm_parser.py       ← VLM增强解析（MiniMax understand_image）
│   └── parsers/            ← ezdxf_parser模块
│       ├── __init__.py
│       ├── dwg_parser.py   ← DXF/DWG基础解析器
│       ├── device_extractor.py ← 设备信息提取
│       ├── topology_builder.py ← 网络拓扑构建
│       ├── coord_extractor.py  ← 坐标提取
│       └── parse_network.py   ← 网络系统图解析
├── integration/
│   ├── __init__.py
│   ├── wiki_connector.py   ← Wiki知识库集成
│   ├── feishu_connector.py ← 飞书集成
│   └── quota_connector.py  ← 定额匹配集成
├── reports/
│   └── PHT-CAD详细调研报告.md ← PHT-CAD项目调研
├── data/                   ← 示例数据和测试输出
│   └── samples/
└── test/
    └── test_engine.py     ← 单元测试
```

---

## 技术栈

| 组件 | 技术 | 状态 |
|------|------|------|
| **核心引擎** | CADReader（规则引擎） | ✅ 已实现 |
| **VLM增强** | MiniMax understand_image | ✅ 已实现 |
| **中文字体** | Microsoft YaHei | ✅ 已支持 |
| **DXF解析** | ezdxf + DWGParser | ✅ 已实现 |
| **图像渲染** | matplotlib | ✅ 已实现 |
| **PDF处理** | PyMuPDF | 🔜 待实现 |
| **飞书集成** | FeiShuCLI (lark-cli) | 🔜 待实现 |

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

### 2. VLM智能解析 + 飞书上传统

```python
from cadreader import CADReader
from cadreader.integration import FeishuConnector

reader = CADReader()
connector = FeishuConnector()

# 1. VLM解析图纸
vlm_result = reader.parse_with_vlm("雾炮塔架.dxf", output_dir="./output")

# 2. 上传到飞书
doc = connector.parse_and_upload_vlm_result(
    vlm_result.get("vlm_result", {}),
    title="雾炮塔架解析报告"
)
print(f"飞书文档: {doc.url}")

# 3. 创建设备清单报告
doc2 = connector.create_device_report(
    devices=[{"id": "T001", "name": "测试设备", "spec": "规格A"}],
    title="设备清单"
)
```

### 3. 列出知识库节点

```python
connector = FeishuConnector()
spaces = connector.list_spaces()
for space in spaces:
    print(f"空间: {space['name']} ({space['space_id']})")
    nodes = connector.list_nodes(space_id=space['space_id'])
    for node in nodes:
        print(f"  - {node.get('title')}")
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

- [x] 研究PHT-CAD代码结构 - PHT-CAD为学术项目，仅含README和图片，无可运行代码
- [x] 迁移ezdxf_parser工具 - 从首山环保平台tools迁移DXF解析模块到src/parsers/
- [x] 实现DXF解析功能 - 使用DWGParser集成到CADReader._parse_dxf()
- [x] 实现VLM增强解析 - 使用MiniMax understand_image解析DXF图像
- [x] 解决中文字体问题 - 使用Microsoft YaHei字体支持中文渲染
- [x] 实现PDF解析功能 - PDF转图像 + VLM分析
- [x] 开发飞书集成 - FeishuConnector实现文档创建和更新
- [ ] 测试与现有skills的集成
- [ ] 完善错误处理和日志
- [ ] 编写API文档

---

## 开发进度

### 已完成

| 功能 | 文件 | 说明 |
|------|------|------|
| PHT-CAD研究 | reports/ | 确认PHT-CAD为纯学术项目，无公开模型权重 |
| DXF解析模块 | src/parsers/ | 从首山环保平台迁移ezdxf_parser |
| CADReader核心 | src/engine.py | 支持规则引擎解析 |
| VLM增强 | src/vlm_parser.py | 使用MiniMax understand_image |
| 中文字体 | src/vlm_parser.py | Microsoft YaHei字体支持 |
| GitHub同步 | - | 已推送至Mr-Hu9595/CADreader |

### 已实现API

```python
from cadreader import CADReader

reader = CADReader()

# 规则引擎解析（快速）
result = reader.parse("图纸.dxf")  # 返回ParsedDrawing

# VLM增强解析（智能）
vlm_result = reader.parse_with_vlm("图纸.dxf", output_dir="./output")

# 渲染图纸为图像
image_path = reader.parse_to_image("图纸.dxf", "output.png")
```

### 待开发

- PDF解析功能
- 飞书集成
- Wiki集成
- 批量处理优化

---

最后更新：2026-05-31