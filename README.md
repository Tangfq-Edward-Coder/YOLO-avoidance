# 基于树莓派与Hailo-8的实时视觉避障系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8/v11-red.svg)](https://ultralytics.com/)

本项目实现了一套完整的实时视觉避障系统，部署于树莓派5 + Hailo-8硬件平台。系统利用双目摄像头，通过深度学习模型（YOLO目标检测 + U-Net精细分割）准确识别并定位周围障碍物，将结果实时显示在模拟车载雷达界面上，并为主动刹车和多传感器融合预留接口。

## ✨ 主要特性

- 🚀 **实时性能**: 系统帧率 ≥ 15 FPS，端到端延迟 ≤ 150ms
- 🎯 **高精度检测**: YOLO目标检测 mAP@0.5 ≥ 0.85
- 📏 **精确测距**: 5米范围内相对误差 ≤ 5%
- ⚡ **Hailo-8加速**: 支持Hailo-8 AI加速模块，提供26 TOPS算力
- 🔄 **完整流水线**: 从图像采集到界面显示的完整处理流程
- 🧩 **模块化设计**: 清晰的代码结构，易于扩展和维护
- 💻 **Windows调试**: 支持Windows单目模式调试，便于开发测试


## 系统架构

```
双目摄像头 → 图像采集与预处理 → YOLO目标检测 → U-Net精细分割
                ↓
            立体匹配 → 深度计算 → 信息融合 → 碰撞风险评估
                ↓
            3D雷达界面显示 ← 刹车接口 ← 雷达融合接口
```

## 📁 目录结构

```
YCTarget/
├── configs/                      # 配置文件目录
│   ├── system_config.yaml        # 双目模式系统配置（生产环境）
│   └── system_config_mono.yaml   # 单目模式系统配置（Windows调试）
│
├── docs/                         # 文档目录
│   ├── API.md                    # API接口文档
│   ├── DEPLOYMENT.md             # 部署文档（树莓派）
│   ├── WINDOWS_DEBUG.md          # Windows调试指南
│   ├── PROJECT_STRUCTURE.md      # 项目结构说明
│   ├── PROJECT_SUMMARY.md        # 项目实现总结
│   └── QUICK_REFERENCE.md        # 快速参考指南
│
├── scripts/                      # 工具脚本目录
│   ├── calibrate_stereo.py      # 双目相机标定脚本
│   ├── install.sh               # Linux安装脚本
│   └── obstacle_avoidance.service  # systemd服务文件
│
├── src/                          # 源代码目录
│   ├── camera/                  # 相机模块
│   │   ├── __init__.py
│   │   ├── stereo_camera.py     # 双目摄像头
│   │   └── mono_camera.py       # 单目摄像头（Windows调试）
│   │
│   ├── detection/               # 检测模块
│   │   ├── __init__.py
│   │   └── yolo_detector.py     # YOLO目标检测器
│   │
│   ├── segmentation/            # 分割模块
│   │   ├── __init__.py
│   │   └── unet_segmenter.py    # U-Net分割器
│   │
│   ├── stereo/                  # 立体匹配模块
│   │   ├── __init__.py
│   │   ├── stereo_matcher.py    # SGBM立体匹配
│   │   └── mono_depth_estimator.py  # 单目深度估计（Windows调试）
│   │
│   ├── fusion/                  # 信息融合模块
│   │   ├── __init__.py
│   │   └── info_fusion.py       # 信息融合器
│   │
│   ├── risk/                    # 风险评估模块
│   │   ├── __init__.py
│   │   └── risk_assessor.py     # 风险评估器
│   │
│   ├── interface/               # 接口模块
│   │   ├── __init__.py
│   │   └── brake_interface.py  # 刹车和雷达融合接口
│   │
│   ├── display/                 # 显示模块
│   │   ├── __init__.py
│   │   └── bev_display.py       # 鸟瞰图显示
│   │
│   ├── main.py                  # 双目模式主程序（生产环境）
│   └── main_mono.py             # 单目模式主程序（Windows调试，支持多种显示模式）
│
├── models/                       # 模型文件目录（需自行添加）
│   └── .gitkeep                 # Git占位文件
│
├── requirements.txt              # Python依赖列表
├── run_mono.bat                 # Windows启动脚本
├── README.md                    # 项目主文档（本文件）
└── README_WINDOWS.md            # Windows快速指南
```

## 🚀 快速开始

### Windows调试模式（推荐用于开发测试）

如果您在Windows环境下进行开发调试，可以使用单目模式：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行单目模式（使用默认摄像头）
python src/main_mono.py --camera 0

# 3. 或使用批处理脚本
run_mono.bat
```

详细说明请参考 [Windows调试指南](README_WINDOWS.md) 和 [Windows调试文档](docs/WINDOWS_DEBUG.md)。

### 树莓派部署模式（生产环境）

#### 1. 环境要求

- **硬件**: 树莓派5 (8GB RAM) + Hailo-8 M.2模块 + 双目摄像头
- **系统**: Raspberry Pi OS 64-bit
- **Python**: 3.11+

#### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv obstacle_avoidance_env
source obstacle_avoidance_env/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 安装Hailo-8 SDK（如果使用Hailo加速）
# 参考 docs/DEPLOYMENT.md
```

#### 3. 配置系统

1. **相机标定**: 使用 `scripts/calibrate_stereo.py` 进行双目相机标定
2. **更新配置**: 将标定结果更新到 `configs/system_config.yaml`
3. **准备模型**: 将训练好的模型文件（.hef或.onnx）放入 `models/` 目录

#### 4. 运行系统

```bash
# 基本运行（双目模式）
python src/main.py --left-camera 0 --right-camera 1

# 使用测试图像
python src/main.py \
    --test-image-left test_data/left_001.jpg \
    --test-image-right test_data/right_001.jpg

# 查看帮助
python src/main.py --help
```

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [部署文档](docs/DEPLOYMENT.md) | 详细的硬件安装、软件配置和部署步骤 |
| [Windows调试指南](README_WINDOWS.md) | Windows环境快速开始指南 |
| [Windows调试文档](docs/WINDOWS_DEBUG.md) | Windows调试详细说明和故障排除 |
| [API文档](docs/API.md) | 完整的API接口说明 |
| [快速参考](docs/QUICK_REFERENCE.md) | 常用命令和配置快速参考 |
| [项目结构](docs/PROJECT_STRUCTURE.md) | 项目目录结构详细说明 |
| [项目总结](docs/PROJECT_SUMMARY.md) | 项目实现总结 |

## 🧩 核心模块说明

| 模块 | 类名 | 功能说明 |
|------|------|----------|
| **相机模块** | `StereoCamera` / `MonoCamera` | 双目/单目摄像头采集与预处理，支持畸变校正和立体校正 |
| **检测模块** | `YOLODetector` | YOLO目标检测，支持CPU、GPU和Hailo-8推理 |
| **分割模块** | `UNetSegmenter` | U-Net精细分割，对检测目标进行像素级分割 |
| **立体匹配** | `StereoMatcher` / `MonoDepthEstimator` | SGBM立体匹配或单目深度估计，计算深度图 |
| **信息融合** | `InfoFusion` | 融合检测、分割和深度信息，计算障碍物3D坐标 |
| **风险评估** | `RiskAssessor` | 碰撞风险评估，根据距离计算风险等级并触发刹车决策 |
| **接口模块** | `BrakeInterface` / `RadarFusionInterface` | 刹车接口和雷达融合接口 |
| **显示模块** | `BEVDisplay` | 鸟瞰图显示，实时3D雷达界面可视化 |

详细API说明请参考 [API文档](docs/API.md)。

## 🎓 模型训练与转换

### YOLO模型训练

```bash
# 准备数据集（YOLO格式）
# data.yaml格式：
# train: /path/to/train/images
# val: /path/to/val/images
# nc: 3
# names: ['person', 'car', 'obstacle']

# 训练模型
python src/yolov8_train.py \
    --model yolov11n.pt \
    --data data.yaml \
    --epochs 100 \
    --imgsz 640 \
    --batch 16 \
    --device 0
```

### 模型转换

参考 [部署文档](docs/DEPLOYMENT.md) 中的模型转换章节，将训练好的模型转换为Hailo HEF格式。

**注意**: Windows调试模式下可以使用 `.pt` 或 `.onnx` 格式，树莓派生产环境建议使用 `.hef` 格式以获得最佳性能。

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **处理帧率** | ≥ 15 FPS | 整体系统（包含检测、分割、测距与显示） |
| **检测精度** | mAP@0.5 ≥ 0.85 | YOLO目标检测模型在自定义数据集上的精度 |
| **测距精度** | 相对误差 ≤ 5% | 5米范围内的深度测量精度 |
| **系统延迟** | ≤ 150ms | 端到端延迟（从图像采集到界面更新） |

**注意**: 单目模式下的测距精度会有所降低（约10-20%误差），建议在生产环境使用双目模式。

## ⚙️ 配置说明

主要配置文件：

- **`configs/system_config.yaml`**: 双目模式系统配置（生产环境）
- **`configs/system_config_mono.yaml`**: 单目模式系统配置（Windows调试）

主要配置项：

- **相机参数**: 内参、畸变系数、立体校正参数
- **模型路径**: YOLO和U-Net模型文件路径
- **检测参数**: 置信度阈值、NMS阈值
- **风险评估**: 距离阈值、风险阈值
- **显示参数**: 窗口尺寸、更新频率

详细配置说明请参考配置文件中的注释。

## 🔧 故障排除

- **Windows环境**: 参考 [Windows调试文档](docs/WINDOWS_DEBUG.md)
- **树莓派环境**: 参考 [部署文档](docs/DEPLOYMENT.md) 中的故障排除章节
- **常见问题**: 参考 [快速参考](docs/QUICK_REFERENCE.md)

## 🛣️ 开发路线图

- [x] 核心功能实现（检测、分割、深度估计）
- [x] Windows调试模式支持
- [x] 完整文档编写
- [ ] GStreamer流水线集成
- [ ] 多线程优化
- [ ] 性能监控工具
- [ ] 单元测试覆盖
- [ ] 更多传感器融合支持

## 📝 使用模式对比

| 特性 | 双目模式（生产） | 单目模式（调试） |
|------|----------------|----------------|
| **平台** | 树莓派5 + Hailo-8 | Windows |
| **摄像头** | 双目摄像头 | 单目摄像头 |
| **深度精度** | 高（≤5%误差） | 中（10-20%误差） |
| **Hailo加速** | ✅ 支持 | ❌ 不支持 |
| **立体匹配** | ✅ 支持 | ❌ 不支持 |
| **适用场景** | 生产部署 | 开发调试 |


---

## ⚠️ 重要提示

1. **相机标定**: 本项目需要根据实际硬件配置进行相机标定
2. **模型训练**: 需要准备自定义数据集并训练模型
3. **详细步骤**: 请参考 [部署文档](docs/DEPLOYMENT.md) 了解完整流程
4. **Windows调试**: 建议先在Windows环境下完成功能验证，再部署到树莓派
