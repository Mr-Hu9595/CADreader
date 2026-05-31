# PHT-CAD 详细调研报告

> 生成时间：2026-05-31
> 研究对象：PHT-CAD（渐进分层调优的CAD参数化图元分析框架）
> GitHub：https://github.com/yuwen-chen616/PHT-CAD

---

## 一、项目概述

| 项目 | 信息 |
|------|------|
| **GitHub** | https://github.com/yuwen-chen616/PHT-CAD |
| **论文** | arXiv:2503.18147 |
| **机构** | 复旦大学（Ke Niu, Yuwen Chen, Haiyang Yu, Zhuofan Chen, Xianghui Que, Bin Li, Xiangyang Xue） |
| **开源** | ✅ 有GitHub代码，数据集在ModelScope |
| **最新更新** | 2026-05-25 |
| **许可证** | 开源（具体许可证见GitHub） |

---

## 二、核心能力（与text-to-CAD的本质区别）

**PHT-CAD不是生成工具，而是解析工具。**

| 能力 | 说明 |
|------|------|
| **2D参数化图元分析(PPA)** | 从工程图纸（图像/DXF/PDF）中识别4种原子组件：点、线、圆、弧 |
| **几何层+标注层同时解析** | 同时提取几何图形和尺寸标注信息（这是与其他项目的根本区别） |
| **结构约束推理** | 理解图元之间的几何约束关系 |
| **VLM驱动** | 利用视觉-语言模型的推理能力 |
| **输出结构化JSON** | 将图纸信息转换为可编程的结构化数据 |

---

## 三、技术架构

```
输入工程图纸
    ↓
VLM (视觉-语言模型，如Qwen)
    ↓
四个专用回归头
├── 点回归头 → 识别点坐标
├── 线回归头 → 识别线的端点/参数
├── 圆回归头 → 识别圆的圆心/半径
└── 弧回归头 → 识别弧的参数
    ↓
高效混合参数化(EHP)表示
    ↓
输出：结构化JSON（几何+标注）
```

### 3.1 高效混合参数化（EHP）

EHP方法用四种原子组件表示2D工程图纸：

| 组件 | 参数 |
|------|------|
| 点 (point) | (x, y) 坐标 |
| 线 (line) | 端点坐标或数学表达式 |
| 圆 (circle) | 圆心(x, y) + 半径r |
| 弧 (arc) | 起止点 + 半径 + 方向 |

### 3.2 渐进分层调优（PHT）

三阶段训练范式：

| 阶段 | 目标 | 能力 |
|------|------|------|
| 第一阶段 | 感知单个基元 | 识别点/线/圆/弧 |
| 第二阶段 | 推理结构约束 | 理解图元之间的关系 |
| 第三阶段 | 对齐标注层 | 将尺寸标注与几何图形关联 |

---

## 四、ParaCAD数据集

| 规模 | 数量 |
|------|------|
| 训练集 | **1026万张**标注工程图纸 |
| 测试集 | **3000张**真实工业图纸 |
| 下载地址 | https://www.modelscope.cn/datasets/yuwenbonnie/ParaCAD-Dataset/summary |

### 数据集特点

1. **首个同时包含几何图层 + 标注图层**的CAD参数化数据集
2. 解决了现有数据集的两大问题：
   - 缺少标注图层（尺寸、功能符号、工艺说明）
   - 缺少真实数据（高结构复杂性、复杂相互关系、物理约束）
3. 数据处理流程：DXF文件 → 尺寸标注 → 几何约束提取 → 结构化JSON

### 数据格式

```json
{
  "primitives": [
    {"type": "line", "params": [x1, y1, x2, y2]},
    {"type": "circle", "params": [cx, cy, r]},
    {"type": "arc", "params": [x1, y1, x2, y2, r, direction]}
  ],
  "annotations": [
    {"type": "dimension", "value": "3×2.5mm", "linked_to": [0]},
    {"type": "tolerance", "value": "±0.1", "linked_to": [0]}
  ],
  "constraints": [
    {"type": "parallel", "entities": [0, 1]},
    {"type": "perpendicular", "entities": [1, 2]}
  ]
}
```

---

## 五、性能指标

### 精确草图图像测试

| 方法 | Acc↑ | ParamMSE↓ | ImgMSE↓ | CD↓ | CF1↑ | PF1↑ |
|------|------|-----------|---------|-----|------|------|
| PICASSO | 0.751 | 281 | 0.075 | 0.729 | - | - |
| **PHT-CAD** | **0.859** | **52** | **0.003** | - | **0.868** | **0.917** |

### 手绘草图图像测试

| 方法 | Acc↑ | ParamMSE↓ | ImgMSE↓ | CD↓ | CF1↑ | PF1↑ |
|------|------|-----------|---------|-----|------|------|
| PICASSO | 0.658 | 365 | 0.117 | 1.090 | - | - |
| **PHT-CAD** | **0.795** | **11** | **0.005** | **0.010** | **0.762** | **0.867** |

### 零样本评估

| 方法 | Acc↑ | ParamMSE↓ | ImgMSE↓ | CD↓ | CF1↑ | PF1↑ |
|------|------|-----------|---------|-----|------|------|
| **PHT-CAD** | **0.923** | **50** | **0.003** | **0.106** | **0.860** | **0.910** |

> ↑越高越好，↓越低越好

### 关键结论

- 草图图像准确率提升**6%**
- 手绘草图准确率提升**13.7%**
- 零样本Acc达**92.3%**，泛化能力强

---

## 六、如何利用PHT-CAD实现工程制图和图纸阅读

### 路线图

```
阶段一：理解能力
└── 输入工程图纸 → PHT-CAD解析 → 结构化JSON（几何+标注）
    ├── 识别图元类型（点/线/圆/弧）
    ├── 提取几何参数（坐标/半径/角度）
    ├── 提取标注信息（尺寸/公差）
    └── 理解结构约束

阶段二：应用构建
├── 应用1：工程图纸数字化
│   └── 将纸质/PDF图纸转为结构化数据
├── 应用2：智能审图
│   └── 自动检测尺寸标注完整性
├── 应用3：图纸比对
│   └── 比对两个版本图纸的差异
└── 应用4：数据抽取
    └── 抽取关键信息填入Excel/数据库

阶段三：集成工作流
├── 集成ezdxf：解析真实DXF文件
├── 集成AutoCAD API：读写DWG文件
└── 集成飞书：通过lark-cli上传结构化数据
```

### 方案A：直接使用Demo（快速验证）

访问地址：https://3122-61-169-124-162.ngrok-free.app/

功能：上传工程图纸图像，查看解析结果

### 方案B：本地部署（生产级）

```bash
# 1. 克隆项目
git clone https://github.com/yuwen-chen616/PHT-CAD.git
cd PHT-CAD

# 2. 安装依赖
conda create -n pht-cad python=3.10
conda activate pht-cad
pip install torch torchvision
pip install transformers  # VLM基座
pip install gradio        # Web UI

# 3. 下载ParaCAD数据集
# 访问 https://www.modelscope.cn/datasets/yuwenbonnie/ParaCAD-Dataset/summary

# 4. 推理示例
python inference.py --input ./test_drawing.jpg --output result.json
```

### 方案C：API封装（集成到自己的工作流）

```python
import json
import base64
from transformers import AutoModelForCausalLM

class PHT-CAD-Engine:
    def __init__(self, model_path="yuwen-chen616/pht-cad"):
        self.model = AutoModelForCausalLM.from_pretrained(model_path)

    def parse_drawing(self, image_path):
        # 1. 读取图纸图像
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        # 2. 调用VLM推理
        result = self.model.infer({
            "image": img_data,
            "task": "cad_primitive_analysis"
        })

        # 3. 提取图元和标注
        primitives = result["primitives"]  # 点/线/圆/弧
        annotations = result["annotations"]  # 尺寸/公差

        # 4. 输出结构化JSON
        return {
            "primitives": primitives,
            "annotations": annotations,
            "constraints": result["constraints"]
        }

# 使用示例
engine = PHT-CAD-Engine()
result = engine.parse_drawing("工程图纸.jpg")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 七、与现有工具链的集成

| 工具 | 集成方式 | 作用 |
|------|---------|------|
| **ezdxf** | PHT-CAD解析 → ezdxf写入DXF | 将AI解析结果写回CAD文件 |
| **pdf2dxf转换器** | PDF → DWG → PHT-CAD | 处理PDF格式工程图 |
| **飞书API** | PHT-CAD → JSON → lark-cli | 将图纸数据录入飞书表格 |
| **Excel** | PHT-CAD → JSON → openpyxl | 将标注数据填入Excel |

---

## 八、实际应用场景示例

### 场景1：机电安装工程图纸数字化

```
输入：GB50303-2015 建筑电气工程施工质量验收规范 PDF
↓
pdf2dxf转换：PDF → DWG
↓
PHT-CAD解析：DWG → 结构化JSON
├── 图元：线(导线)、圆(接线端子)、弧(弯头)
├── 标注：尺寸(3×2.5mm)、公差(±0.1)
└── 图层：几何层、标注层
↓
输出：结构化数据 → 录入飞书表格 → 生成报告
```

### 场景2：智能审图

```
上传工程图纸 → PHT-CAD解析 → 检查标注完整性
├── 是否有尺寸标注？
├── 是否有公差标注？
└── 图层是否完整？
↓
输出：审图报告（标注缺失列表）
```

### 场景3：图纸版本比对

```
旧版图纸 → PHT-CAD → JSON_v1
新版图纸 → PHT-CAD → JSON_v2
↓
diff(JSON_v1, JSON_v2) → 差异报告
├── 新增图元
├── 删除图元
└── 参数变更
```

---

## 九、总结

**PHT-CAD是目前最适合工程制图和工程图纸阅读的开源项目**，因为：

| 优势 | 说明 |
|------|------|
| ✅ **唯一性** | 唯一开源的VLM驱动工程图纸理解项目 |
| ✅ **完整性** | 同时处理几何图层 + 标注图层 |
| ✅ **实用性** | 输出结构化JSON，可直接集成到工作流 |
| ✅ **大规模数据** | 1026万张训练数据，3000张真实测试图 |
| ✅ **高性能** | 准确率提升13.7%，零样本Acc达92.3% |

**与text-to-CAD的根本区别**：

| 项目 | 输入 | 输出 | 用途 |
|------|------|------|------|
| text-to-CAD | 文本描述 | 3D几何体 | 从零生成CAD模型 |
| **PHT-CAD** | 工程图纸图像 | 结构化JSON | 理解和解析现有图纸 |

---

## 十、下一步行动

1. **体验Demo**：访问 https://3122-61-169-124-162.ngrok-free.app/ 上传工程图纸测试
2. **研究数据集**：下载ParaCAD数据集，了解数据结构
3. **本地部署**：按照GitHub说明部署PHT-CAD
4. **集成工作流**：将PHT-CAD集成到机电安装工程资料收集流程中

---

## 十一、参考链接

| 类型 | 链接 |
|------|------|
| GitHub | https://github.com/yuwen-chen616/PHT-CAD |
| 论文 | https://arxiv.org/abs/2503.18147 |
| 数据集 | https://www.modelscope.cn/datasets/yuwenbonnie/ParaCAD-Dataset/summary |
| Demo | https://3122-61-169-124-162.ngrok-free.app/ |

---

## 十二、引用

```bibtex
@article{pht-cad,
  title={PHT-CAD: Efficient CAD Parametric Primitive Analysis with Progressive Hierarchical Tuning},
  author={Niu, Ke and Chen, Yuwen and Yu, Haiyang and Chen, Zhuofan and Que, Xianghui and Li, Bin and Xue, Xiangyang},
  journal={arXiv preprint arXiv:2503.18147},
  year={2025}
}
```