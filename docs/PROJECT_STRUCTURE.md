# 项目结构说明

本文档详细说明项目的目录结构和文件组织。

## 完整目录树

```
YCTarget/
│
├── configs/                          # 配置文件目录
│   ├── system_config.yaml            # 双目模式系统配置（生产环境）
│   └── system_config_mono.yaml      # 单目模式系统配置（Windows调试）
│
├── docs/                             # 文档目录
│   ├── API.md                       # API接口文档
│   ├── DEPLOYMENT.md                # 部署文档（树莓派）
│   ├── WINDOWS_DEBUG.md             # Windows调试指南
│   ├── PROJECT_SUMMARY.md           # 项目实现总结
│   ├── PROJECT_STRUCTURE.md         # 项目结构说明（本文档）
│   └── QUICK_REFERENCE.md           # 快速参考指南
│
├── scripts/                          # 工具脚本目录
│   ├── calibrate_stereo.py          # 双目相机标定脚本
│   ├── install.sh                   # Linux安装脚本
│   └── obstacle_avoidance.service   # systemd服务文件
│
├── src/                              # 源代码目录
│   ├── camera/                      # 相机模块
│   │   ├── __init__.py
│   │   ├── stereo_camera.py        # 双目摄像头类
│   │   └── mono_camera.py          # 单目摄像头类（Windows调试）
│   │
│   ├── detection/                    # 检测模块
│   │   ├── __init__.py
│   │   └── yolo_detector.py        # YOLO检测器
│   │
│   ├── segmentation/                 # 分割模块
│   │   ├── __init__.py
│   │   └── unet_segmenter.py       # U-Net分割器
│   │
│   ├── stereo/                       # 立体匹配模块
│   │   ├── __init__.py
│   │   ├── stereo_matcher.py       # SGBM立体匹配器
│   │   └── mono_depth_estimator.py # 单目深度估计器（Windows调试）
│   │
│   ├── fusion/                       # 信息融合模块
│   │   ├── __init__.py
│   │   └── info_fusion.py          # 信息融合器
│   │
│   ├── risk/                         # 风险评估模块
│   │   ├── __init__.py
│   │   └── risk_assessor.py        # 风险评估器
│   │
│   ├── interface/                    # 接口模块
│   │   ├── __init__.py
│   │   └── brake_interface.py      # 刹车和雷达融合接口
│   │
│   ├── display/                      # 显示模块
│   │   ├── __init__.py
│   │   └── bev_display.py           # 鸟瞰图显示
│   │
│   ├── main.py                       # 双目模式主程序（生产环境）
│   └── main_mono.py                 # 单目模式主程序（Windows调试，支持多种显示模式）
│
├── models/                           # 模型文件目录（用户添加）
│   └── .gitkeep                     # Git占位文件
│
├── .gitignore                        # Git忽略文件
├── requirements.txt                  # Python依赖列表
├── run_mono.bat                     # Windows启动脚本
├── README.md                         # 项目主文档
└── README_WINDOWS.md                 # Windows快速指南
```

## 模块说明

### 配置文件 (`configs/`)

- **system_config.yaml**: 双目模式系统配置文件，包含所有模块的参数设置（生产环境）
- **system_config_mono.yaml**: 单目模式系统配置文件（Windows调试）

### 文档 (`docs/`)

- **API.md**: 详细的API接口文档，包含所有类和方法的说明
- **DEPLOYMENT.md**: 完整的部署文档，包含硬件安装、软件配置等（树莓派）
- **WINDOWS_DEBUG.md**: Windows调试详细指南和故障排除
- **PROJECT_SUMMARY.md**: 项目实现总结
- **QUICK_REFERENCE.md**: 快速参考指南，常用命令和配置

### 工具脚本 (`scripts/`)

- **calibrate_stereo.py**: 双目相机标定脚本
- **install.sh**: 快速安装脚本，自动安装系统依赖
- **obstacle_avoidance.service**: systemd服务文件，用于系统服务管理

### 源代码 (`src/`)

#### 相机模块 (`camera/`)
- **stereo_camera.py**: 双目摄像头采集与预处理
  - 图像采集
  - 畸变校正
  - 立体校正
- **mono_camera.py**: 单目摄像头适配器（Windows调试）
  - 单目图像采集
  - 模拟双目输出（用于兼容）

#### 检测模块 (`detection/`)
- **yolo_detector.py**: YOLO目标检测
  - 支持多种推理后端
  - Hailo-8加速支持

#### 分割模块 (`segmentation/`)
- **unet_segmenter.py**: U-Net精细分割
  - ROI分割
  - Hailo-8加速支持

#### 立体匹配模块 (`stereo/`)
- **stereo_matcher.py**: SGBM立体匹配
  - 视差计算
  - 深度计算
- **mono_depth_estimator.py**: 单目深度估计（Windows调试）
  - 基于检测框大小的深度估计
  - 创建深度图

#### 信息融合模块 (`fusion/`)
- **info_fusion.py**: 信息融合
  - 检测、分割、深度融合
  - 3D坐标计算

#### 风险评估模块 (`risk/`)
- **risk_assessor.py**: 碰撞风险评估
  - 风险等级计算
  - 刹车决策

#### 接口模块 (`interface/`)
- **brake_interface.py**: 刹车和雷达融合接口
  - 刹车接口
  - 雷达融合接口

#### 显示模块 (`display/`)
- **bev_display.py**: 鸟瞰图显示
  - Pygame渲染
  - 实时可视化

#### 主程序
- **main.py**: 双目模式主程序（生产环境）
  - `ObstacleAvoidanceSystem`: 主系统类
  - 整合所有模块
  - 主循环控制
- **main_mono.py**: 单目模式主程序（Windows调试）
  - `MonoObstacleAvoidanceSystem`: 单目模式主系统类
  - 支持单目摄像头
  - 使用单目深度估计

## 数据流

```
图像采集 (stereo_camera)
    ↓
目标检测 (yolo_detector)
    ↓
精细分割 (unet_segmenter)
    ↓
立体匹配 (stereo_matcher)
    ↓
信息融合 (info_fusion)
    ↓
风险评估 (risk_assessor)
    ↓
显示输出 (bev_display)
    ↓
接口调用 (brake_interface)
```

## 依赖关系

```
main.py
├── camera (stereo_camera)
├── detection (yolo_detector)
├── segmentation (unet_segmenter)
├── stereo (stereo_matcher)
├── fusion (info_fusion)
│   ├── detection
│   ├── segmentation
│   └── stereo
├── risk (risk_assessor)
│   └── fusion
├── interface (brake_interface, radar_fusion)
│   └── risk
└── display (bev_display)
    ├── fusion
    └── risk
```

## 文件大小估算

- **配置文件**: ~5KB
- **源代码**: ~50KB
- **文档**: ~100KB
- **脚本**: ~10KB
- **总计**: ~165KB（不含模型文件）

## 扩展建议

### 添加新模块

1. 在 `src/` 下创建新目录
2. 实现模块类
3. 创建 `__init__.py` 导出
4. 在 `main.py` 中集成
5. 更新配置文件

### 添加新功能

1. 在相应模块中添加方法
2. 更新API文档
3. 添加单元测试（如果实现）
4. 更新README

## 维护建议

1. **代码组织**: 保持模块化结构
2. **文档更新**: 代码变更时同步更新文档
3. **配置管理**: 使用配置文件而非硬编码
4. **错误处理**: 添加适当的异常处理
5. **日志记录**: 添加日志功能（未来改进）

---

**最后更新**: 2024年

