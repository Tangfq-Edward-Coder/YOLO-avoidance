# 部署手册

本文档提供省实未来汽车视觉避障系统的完整部署指南。

## 目录

- [硬件准备](#硬件准备)
- [软件环境配置](#软件环境配置)
- [相机标定](#相机标定)
- [模型准备](#模型准备)
- [系统配置](#系统配置)
- [系统启动](#系统启动)
- [故障排除](#故障排除)

## 硬件准备

### 硬件清单

| 组件 | 型号/规格 | 数量 | 说明 |
|------|----------|------|------|
| 主计算单元 | 树莓派5B (8GB RAM) | 1 | 系统主控 |
| AI加速单元 | Hailo-8 AI加速卡 (M.2接口) | 1 | 提供26 TOPS算力 |
| 电源与UPS | 官方UPS模块、CUKTECH15移动电源 | 1套 | 稳定电力供应 |
| 视觉传感器 | UVC摄像头 (全局快门推荐) | 4 | 2个双目+2个环视 |
| 人机交互界面 | 7英寸触摸显示屏 | 1 | 实时显示 |
| 辅助配件 | 适配Hailo-8的树莓派M.2扩展板、主动散热风扇 | 1套 | 硬件连接与散热 |

### 硬件组装步骤

1. **安装Hailo-8模块**
   - 将Hailo-8 M.2模块插入树莓派M.2扩展板
   - 确保连接牢固

2. **连接摄像头**
   - 前向双目相机：连接到USB端口0和1
   - 环视相机（可选）：连接到USB端口2和3

3. **连接显示屏**
   - 将7英寸触摸屏连接到树莓派
   - 配置显示分辨率（建议1280x720）

4. **电源连接**
   - 连接UPS模块和移动电源
   - 确保电源稳定

5. **散热配置**
   - 安装主动散热风扇
   - 确保良好通风

## 软件环境配置

### 1. 系统要求

- **操作系统**: Raspberry Pi OS (64-bit) 或 Ubuntu Server for ARM64
- **Python**: 3.9+
- **存储空间**: 至少16GB可用空间

### 2. 自动化配置

运行环境配置脚本：

```bash
sudo bash scripts/setup.sh
```

脚本将自动完成：
- 系统包更新
- 基础依赖安装（OpenCV、Python等）
- 语音提示依赖安装（espeak）
- Python虚拟环境创建
- 系统服务配置

### 3. 手动配置（可选）

如果自动化脚本失败，可以手动配置：

#### 3.1 更新系统

```bash
sudo apt update
sudo apt upgrade -y
```

#### 3.2 安装基础依赖

```bash
sudo apt install -y \
    python3 python3-pip python3-venv \
    git build-essential cmake \
    libopencv-dev python3-opencv \
    espeak espeak-data
```

#### 3.3 安装Hailo-8 SDK（可选）

如果使用Hailo-8加速，参考Hailo官方文档安装SDK：
https://hailo.ai/developer-zone/

#### 3.4 创建Python虚拟环境

```bash
cd /opt/visual_obstacle_avoidance
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 用户权限配置

添加用户到video组（访问摄像头）：

```bash
sudo usermod -a -G video $USER
```

重新登录或运行：

```bash
newgrp video
```

## 相机标定

### 1. 采集标定图像

使用标定板（如9x6棋盘格）采集至少20对图像：

```bash
python scripts/calibrate_stereo.py \
    --images-dir ./calibration_images \
    --board-width 9 \
    --board-height 6 \
    --square-size 0.025
```

### 2. 更新配置文件

将标定结果更新到 `configs/system_config.yaml`：

```yaml
camera:
  left_camera_matrix: [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
  right_camera_matrix: [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
  left_dist_coeffs: [k1, k2, p1, p2, k3]
  right_dist_coeffs: [k1, k2, p1, p2, k3]
  stereo:
    R: [[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]]
    T: [tx, ty, tz]
    R1: [[...]]
    R2: [[...]]
    P1: [[...]]
    P2: [[...]]
    Q: [[...]]
```

## 模型准备

### 1. 模型训练

#### YOLO模型训练

准备数据集（YOLO格式），至少2000张已标注图像：

```bash
# 数据集结构
dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/

# 训练模型
python train_yolo.py \
    --model yolov8n.pt \
    --data dataset.yaml \
    --epochs 100 \
    --imgsz 640 \
    --batch 16
```

#### U-Net模型训练

准备场景分割数据集，训练U-Net模型识别路面、车道线、天空等。

### 2. 模型转换

#### 转换为Hailo HEF格式

使用Hailo工具链将模型转换为HEF格式：

```bash
# YOLO转换
hailo model zoo compile yolo --target hailo8 \
    --input-model yolo_obstacle.onnx \
    --output yolo_obstacle.hef

# U-Net转换
hailo model zoo compile unet --target hailo8 \
    --input-model unet_obstacle.onnx \
    --output unet_obstacle.hef
```

### 3. 部署模型

将模型文件放入 `models/` 目录：

```bash
cp yolo_obstacle.hef models/
cp unet_obstacle.hef models/
```

## 系统配置

编辑 `configs/system_config.yaml`，配置：

### 1. 相机参数

更新标定结果。

### 2. 模型路径

```yaml
models:
  yolo_model: "models/yolo_obstacle.hef"
  unet_model: "models/unet_obstacle.hef"
```

### 3. 检测参数

```yaml
models:
  detection_confidence: 0.5
  nms_threshold: 0.4
```

### 4. 风险评估参数

```yaml
risk_assessment:
  safe_distance: 3.0
  warning_distance: 2.0
  danger_distance: 1.0
  brake_distance: 0.8
```

### 5. 道路风险预警参数

```yaml
road_risk_assessment:
  low_visibility_brightness_threshold: 80
  low_visibility_contrast_threshold: 30
  wet_road_texture_threshold: 0.3
  curve_curvature_threshold: 0.1
  narrow_road_density_threshold: 0.4
```

### 6. TTC估算参数

```yaml
ttc_estimation:
  default_ego_speed: 5.0
  warning_threshold: 5.0
  emergency_threshold: 3.0
```

### 7. 语音提示参数

```yaml
voice_alert:
  enabled: true
  language: "zh-CN"
```

## 系统启动

### 方式一：一键启动脚本

```bash
bash scripts/start_system.sh
```

### 方式二：手动启动

```bash
cd /opt/visual_obstacle_avoidance
source venv/bin/activate
python src/main.py --left-camera 0 --right-camera 1
```

### 方式三：系统服务（开机自启）

```bash
# 启用服务
sudo systemctl enable visual-obstacle-avoidance.service

# 启动服务
sudo systemctl start visual-obstacle-avoidance.service

# 查看状态
sudo systemctl status visual-obstacle-avoidance.service

# 查看日志
sudo journalctl -u visual-obstacle-avoidance.service -f
```

## 故障排除

### 常见问题

#### 1. 相机无法打开

**症状**: 程序报错"无法打开相机"

**解决方案**:
- 检查相机连接
- 检查用户权限：`sudo usermod -a -G video $USER`
- 检查设备ID：`ls /dev/video*`

#### 2. Hailo-8无法识别

**症状**: 程序报错"未找到Hailo设备"

**解决方案**:
- 检查Hailo-8驱动：`hailo_platform scan_devices`
- 检查M.2连接
- 重新安装Hailo SDK

#### 3. 模型加载失败

**症状**: 程序报错"模型文件不存在"或"模型格式错误"

**解决方案**:
- 检查模型文件路径
- 确认模型格式（.hef或.onnx）
- 检查模型文件权限

#### 4. 语音提示不工作

**症状**: 没有语音输出

**解决方案**:
- 检查espeak安装：`apt-get install espeak`
- 检查配置：`voice_alert.enabled: true`
- 测试语音：`espeak "测试"`

#### 5. 性能不达标

**症状**: FPS < 15或延迟 > 150ms

**解决方案**:
- 检查是否使用Hailo-8加速
- 降低输入图像分辨率
- 优化检测阈值
- 检查CPU/GPU使用率

#### 6. 系统崩溃

**症状**: 程序异常退出

**解决方案**:
- 检查日志：`journalctl -u visual-obstacle-avoidance.service`
- 检查内存使用：`free -h`
- 检查温度：`vcgencmd measure_temp`
- 增加散热

### 性能优化建议

1. **使用Hailo-8加速**: 将模型转换为HEF格式
2. **调整输入分辨率**: 根据性能需求调整
3. **优化检测阈值**: 平衡精度和速度
4. **多线程处理**: 启用配置文件中的多线程选项
5. **减少不必要的计算**: 只在需要时进行分割

### 日志查看

```bash
# 系统服务日志
sudo journalctl -u visual-obstacle-avoidance.service -f

# 应用日志（如果配置了日志文件）
tail -f /opt/visual_obstacle_avoidance/logs/app.log
```

---

**注意**: 如遇到其他问题，请参考项目GitHub Issues或联系技术支持。

