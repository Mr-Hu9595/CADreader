# CADreader - 工程图纸智能解析工具

基于PHT-CAD的工程图纸阅读与理解系统。

## 核心能力

- 🔍 **图纸解析**：从工程图纸中识别点、线、圆、弧四种原子组件
- 📐 **标注提取**：同时解析几何图层 + 标注图层（尺寸、公差）
- 📊 **结构化输出**：输出JSON格式，可直接集成到工作流
- 🔗 **工具链集成**：与wiki、FeiShuCLI、数据提取等skills无缝对接

## 项目背景

CADreader是对PHT-CAD（复旦大学开源项目，arXiv:2503.18147）的工程应用封装，专注于解决工程制图和工程图纸阅读的实际问题。

## 与AiAgents技能体系的融合

```
PDF图纸 → CADreader解析 → 结构化数据 → 飞书/Wiki/定额匹配
```

| 工具链 | 说明 |
|--------|------|
| CADreader → Wiki | 将图纸信息整理上传至飞书知识库 |
| CADreader → 材料计划助手 | 从图纸提取尺寸填入材料计划 |
| CADreader → quota-matcher | 从图纸提取工程量进行定额匹配 |

## 快速开始

```python
from cadreader import CADReader

reader = CADReader()
result = reader.parse("工程图纸.jpg")
print(result)
```

## 目录结构

```
cadreader/
├── src/              # 核心代码
├── docs/             # 文档
├── reports/          # 研究报告
├── test/             # 测试
├── data/             # 示例数据
└── integration/      # 工具链集成
```

## 参考

- [PHT-CAD GitHub](https://github.com/yuwen-chen616/PHT-CAD)
- [ParaCAD数据集](https://www.modelscope.cn/datasets/yuwenbonnie/ParaCAD-Dataset/summary)
- [论文 arXiv:2503.18147](https://arxiv.org/abs/2503.18147)

## License

MIT