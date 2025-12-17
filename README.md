# 省实未来汽车 - 多模态AI视觉辅助驾驶系统（视觉避障组）

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8/v10-red.svg)](https://ultralytics.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

本项目实现了一套完整的实时视觉避障与道路风险预警系统，部署于树莓派5B + Hailo-8硬件平台。系统利用双目摄像头，通过深度学习模型（YOLO目标检测 + U-Net场景分割）准确识别并定位周围障碍物，实现道路风险预警和碰撞时间估算，将结果实时显示在7英寸触摸屏上，并为主动刹车预留接口。

## ✨ 主要特性

- 🚀 **实时性能**: 系统帧率 ≥ 15 FPS，端到端延迟 ≤ 150ms
- 🎯 **高精度检测**: YOLO目标检测，支持person、car、bicycle三类目标
- 📏 **精确测距**: 20米范围内测距误差 ≤ 10%
- ⚡ **Hailo-8加速**: 支持Hailo-8 AI加速模块，提供26 TOPS算力
- 🛣️ **道路风险预警**: 
  - 中长期风险：低能见度、路面湿滑
  - 短期风险：弯道、狭窄路段
- ⏱️ **TTC估算**: 基于连续帧数据计算碰撞时间，TTC≤3.0秒时触发紧急警报
- 🔊 **语音提示**: 实时语音播报风险预警信息
- 🖥️ **PyQt界面**: 7英寸触摸屏实时显示，支持交互操作

## 📋 项目总览

### 硬件平台
- **主计算单元**: 树莓派5B (8GB RAM)
- **AI加速单元**: Hailo-8 AI加速卡 (M.2接口)
- **视觉传感器**: UVC摄像头 × 4（2个双目 + 2个环视）
- **人机交互**: 7英寸触摸显示屏
- **电源**: 官方UPS模块 + CUKTECH15移动电源

### 核心功能
1. **目标检测**: YOLO检测person、car、bicycle三类目标
2. **双目测距**: SGBM立体匹配，20米内误差≤10%
3. **场景分割**: U-Net识别路面、车道线、天空等场景元素
4. **道路风险预警**: 
   - 中长期：低能见度、路面湿滑
   - 短期：弯道、狭窄路段
5. **TTC估算**: 碰撞时间计算与预警
6. **语音提示**: 实时风险播报
7. **UI显示**: PyQt5界面，实时显示检测结果和风险信息

## 🏗️ 系统架构

```
双目摄像头 → 图像采集与预处理 → YOLO目标检测 → U-Net场景分割
                ↓                      ↓
            立体匹配 → 深度计算 → 信息融合 → TTC估算
                ↓                      ↓
            道路风险分析 ← 碰撞风险评估 → 预警决策
                ↓                      ↓
            PyQt界面显示 ← 语音提示 ← 刹车接口
```

## 📁 目录结构

```
YCTarget/
├── configs/                      # 配置文件目录
│   └── system_config.yaml        # 系统配置文件
│
├── docs/                         # 文档目录
│   ├── API_Reference.md          # API接口文档
│   ├── Deployment_Manual.md     # 部署手册
│   └── Test_Report.md            # 测试报告
│
├── scripts/                      # 工具脚本目录
│   ├── calibrate_stereo.py      # 双目相机标定脚本
│   ├── setup.sh                  # 环境配置脚本
│   ├── start_system.sh          # 一键启动脚本
│   └── obstacle_avoidance.service  # systemd服务文件
│
├── src/                          # 源代码目录
│   ├── camera/                  # 相机模块
│   │   └── stereo_camera.py     # 双目摄像头
│   │
│   ├── detection/               # 检测模块
│   │   └── yolo_detector.py     # YOLO目标检测器
│   │
│   ├── segmentation/            # 分割模块
│   │   └── unet_segmenter.py    # U-Net分割器
│   │
│   ├── stereo/                  # 立体匹配模块
│   │   └── stereo_matcher.py    # SGBM立体匹配
│   │
│   ├── fusion/                  # 信息融合模块
│   │   └── info_fusion.py       # 信息融合器
│   │
│   ├── risk/                    # 风险评估模块
│   │   ├── risk_assessor.py     # 碰撞风险评估
│   │   ├── road_risk_assessor.py  # 道路风险预警
│   │   └── ttc_estimator.py     # TTC估算
│   │
│   ├── interface/               # 接口模块
│   │   └── brake_interface.py  # 刹车接口
│   │
│   ├── audio/                   # 音频模块
│   │   └── voice_alert.py      # 语音提示
│   │
│   ├── display/                 # 显示模块
│   │   └── pyqt_display.py     # PyQt5显示界面
│   │
│   └── main.py                  # 主程序入口
│
├── models/                       # 模型文件目录（需自行添加）
│   └── .gitkeep
│
├── requirements.txt              # Python依赖列表
├── LICENSE                       # MIT许可证
└── README.md                    # 项目主文档（本文件）
```

## 🚀 快速开始

### 1. 环境要求

- **硬件**: 树莓派5B (8GB RAM) + Hailo-8 M.2模块 + 双目摄像头
- **系统**: Raspberry Pi OS (64-bit) 或 Ubuntu Server for ARM64
- **Python**: 3.9+

### 2. 环境配置

运行自动化配置脚本：

```bash
sudo bash scripts/setup.sh
```

脚本将自动完成：
- 系统包更新
- 基础依赖安装（OpenCV、Python等）
- 语音提示依赖安装（espeak）
- Python虚拟环境创建
- 系统服务配置

### 3. 相机标定

使用双目相机标定脚本：

```bash
python scripts/calibrate_stereo.py \
    --images-dir ./calibration_images \
    --board-width 9 \
    --board-height 6 \
    --square-size 0.025
```

将标定结果更新到 `configs/system_config.yaml`。

### 4. 模型准备

将训练好的模型文件放入 `models/` 目录：
- `yolo_obstacle.hef` 或 `yolo_obstacle.onnx` - YOLO目标检测模型
- `unet_obstacle.hef` 或 `unet_obstacle.onnx` - U-Net场景分割模型

### 5. 配置系统

编辑 `configs/system_config.yaml`，配置：
- 相机参数（标定结果）
- 模型路径
- 检测参数
- 风险评估参数
- TTC估算参数
- 语音提示参数

### 6. 启动系统

#### 方式一：一键启动脚本

```bash
bash scripts/start_system.sh
```

#### 方式二：手动启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行主程序
python src/main.py --left-camera 0 --right-camera 1
```

#### 方式三：系统服务（开机自启）

```bash
# 启用服务
sudo systemctl enable visual-obstacle-avoidance.service

# 启动服务
sudo systemctl start visual-obstacle-avoidance.service

# 查看状态
sudo systemctl status visual-obstacle-avoidance.service
```

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [部署手册](docs/Deployment_Manual.md) | 详细的硬件安装、软件配置和部署步骤 |
| [API参考](docs/API_Reference.md) | 完整的API接口说明 |
| [测试报告](docs/Test_Report.md) | 详细的测试数据和验收结果 |

## 🧩 核心模块说明

| 模块 | 类名 | 功能说明 |
|------|------|----------|
| **相机模块** | `StereoCamera` | 双目摄像头采集与预处理，支持畸变校正和立体校正 |
| **检测模块** | `YOLODetector` | YOLO目标检测，支持CPU、GPU和Hailo-8推理 |
| **分割模块** | `UNetSegmenter` | U-Net场景分割，识别路面、车道线等场景元素 |
| **立体匹配** | `StereoMatcher` | SGBM立体匹配，计算视差图和深度图 |
| **信息融合** | `InfoFusion` | 融合检测、分割和深度信息，计算障碍物3D坐标 |
| **碰撞风险评估** | `RiskAssessor` | 根据距离评估碰撞风险等级 |
| **道路风险预警** | `RoadRiskAssessor` | 中长期和短期道路风险判断 |
| **TTC估算** | `TTCEstimator` | 基于连续帧数据计算碰撞时间 |
| **语音提示** | `VoiceAlert` | 实时语音播报风险预警信息 |
| **显示模块** | `PyQtDisplay` | PyQt5界面，实时显示检测结果和风险信息 |

详细API说明请参考 [API参考文档](docs/API_Reference.md)。

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **处理帧率** | ≥ 15 FPS | 整体系统（包含检测、分割、测距与显示） |
| **测距精度** | 误差 ≤ 10% | 20米范围内的深度测量精度 |
| **系统延迟** | ≤ 150ms | 端到端延迟（从图像采集到界面更新） |
| **风险预警准确率** | ≥ 90% | 中长期风险判断准确率100%，短期风险≥90% |
| **TTC预警** | TTC ≤ 3.0秒 | 可靠触发紧急语音警报 |
| **系统稳定性** | ≥ 2小时 | 连续运行无死机、卡顿、内存泄漏 |

## ⚙️ 配置说明

主要配置文件：`configs/system_config.yaml`

主要配置项：
- **相机参数**: 内参、畸变系数、立体校正参数
- **模型路径**: YOLO和U-Net模型文件路径
- **检测参数**: 置信度阈值、NMS阈值
- **风险评估**: 距离阈值、风险阈值
- **道路风险预警**: 中长期和短期风险阈值
- **TTC估算**: 默认自车速度、警告阈值
- **语音提示**: 启用状态、语言代码
- **显示参数**: 窗口尺寸、更新频率

详细配置说明请参考配置文件中的注释。

## 🧪 测试与验收

### 验收标准（KPI）

| 类别 | 验收项目 | 具体标准 | 测试方法 |
|------|---------|---------|---------|
| **性能** | 感知实时性 | FPS ≥ 15帧/秒 | 在树莓派5B+Hailo-8平台上运行系统，记录平均FPS |
| **性能** | 测距精度 | 20米内误差 ≤ 10% | 使用已知距离的标定物测试，计算平均误差 |
| **功能** | 目标检测 | 可稳定检测并区别人、车、自行车三类目标 | 在校园实景视频中，目视检查检测框与类别的准确性 |
| **功能** | 风险预警（中长期） | 对"低能见度"、"路面湿滑"两种场景，准确率100% | 使用4段标准测试视频进行验证 |
| **功能** | 风险预警（短期） | 在400米环路行驶中，能有效预警弯道和狭窄路段，综合准确率≥90% | 实车测试，记录预警触发与人工判断的一致性 |
| **功能** | TTC预警 | 对模拟障碍物，能在TTC≤3.0秒时可靠触发紧急语音警报 | 使用移动的模拟障碍物（如遥控车）进行测试 |
| **系统** | 稳定性 | 连续运行2小时无死机、卡顿、内存泄漏 | 压力测试，记录系统状态 |
| **系统** | 易用性 | 支持一键启动，上电后自动运行 | 断电后重新上电，检查系统是否自动进入工作状态 |

详细测试报告请参考 [测试报告](docs/Test_Report.md)。

## 🔧 故障排除

### 常见问题

1. **相机无法打开**
   - 检查相机连接和权限
   - 运行 `sudo usermod -a -G video $USER` 添加用户到video组

2. **Hailo-8无法识别**
   - 检查Hailo-8驱动是否正确安装
   - 运行 `hailo_platform scan_devices` 检查设备

3. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认模型格式（.hef或.onnx）与设备匹配

4. **语音提示不工作**
   - 检查espeak是否安装：`apt-get install espeak`
   - 检查语音提示是否在配置中启用

5. **性能不达标**
   - 检查是否使用Hailo-8加速
   - 调整输入图像尺寸
   - 优化检测阈值

更多故障排除信息请参考 [部署手册](docs/Deployment_Manual.md)。

## 📝 开发路线图

- [x] 核心功能实现（检测、分割、深度估计）
- [x] 道路风险预警（中长期和短期）
- [x] TTC估算与预警
- [x] 语音提示功能
- [x] PyQt5界面开发
- [x] 一键启动脚本
- [x] 完整文档编写
- [ ] 多传感器融合支持
- [ ] Web界面支持
- [ ] 性能监控工具
- [ ] 单元测试覆盖

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。

## 👥 贡献

欢迎提交Issue和Pull Request！

## 📮 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**项目状态**: ✅ 完成  
**最后更新**: 2024年
