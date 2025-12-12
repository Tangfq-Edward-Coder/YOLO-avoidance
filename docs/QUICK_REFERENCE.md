# 快速参考指南

本文档提供常用命令和配置的快速参考。

## 常用命令

### 系统运行

```bash
# 基本运行
python src/main.py --left-camera 0 --right-camera 1

# 使用测试图像
python src/main.py \
    --test-image-left test_data/left_001.jpg \
    --test-image-right test_data/right_001.jpg

# 指定配置文件
python src/main.py --config configs/system_config.yaml
```

### 相机标定

```bash
# 双目相机标定
python scripts/calibrate_stereo.py \
    --images-dir ./calibration_images \
    --board-width 9 \
    --board-height 6 \
    --square-size 0.025 \
    --output calibration_result.yaml
```

### 模型训练

```bash
# YOLO训练
python src/yolov8_train.py \
    --model yolov11n.pt \
    --data data.yaml \
    --epochs 100 \
    --imgsz 640 \
    --batch 16 \
    --device 0
```

### 系统服务

```bash
# 安装服务
sudo cp scripts/obstacle_avoidance.service /etc/systemd/system/
sudo systemctl enable obstacle_avoidance.service
sudo systemctl start obstacle_avoidance.service

# 查看日志
sudo journalctl -u obstacle_avoidance.service -f

# 停止服务
sudo systemctl stop obstacle_avoidance.service
```

## 配置文件路径

- **系统配置**: `configs/system_config.yaml`
- **相机标定结果**: `calibration_result.yaml`
- **模型文件**: `models/`
- **日志文件**: `logs/` 或 `system.log`

## 关键参数

### 相机参数
- `left_camera_id`: 左相机设备ID（默认0）
- `right_camera_id`: 右相机设备ID（默认1）
- `image_width`: 图像宽度（默认640）
- `image_height`: 图像高度（默认480）
- `baseline`: 基线距离（米，需标定）

### 检测参数
- `detection_confidence`: 检测置信度阈值（默认0.5）
- `nms_threshold`: NMS阈值（默认0.4）
- `input_size`: 模型输入尺寸（默认[640, 480]）

### 风险评估参数
- `safe_distance`: 安全距离（米，默认3.0）
- `warning_distance`: 警告距离（米，默认2.0）
- `danger_distance`: 危险距离（米，默认1.0）
- `brake_distance`: 刹车距离（米，默认0.8）

### 显示参数
- `window_width`: 窗口宽度（默认1280）
- `window_height`: 窗口高度（默认720）
- `bev_range`: 鸟瞰图范围（米，默认10.0）
- `target_fps`: 目标帧率（默认15）

## 故障排除命令

```bash
# 检查相机设备
ls -l /dev/video*

# 测试相机
v4l2-ctl --device=/dev/video0 --list-formats

# 检查Hailo设备
hailortcli fw-control identify

# 检查Python环境
python3 --version
pip list | grep -E "(opencv|numpy|ultralytics)"

# 查看系统资源
htop
vcgencmd measure_temp

# 检查日志
tail -f system.log
sudo journalctl -xe
```

## 性能优化参数

### 提高帧率
```yaml
models:
  input_size: [320, 240]  # 降低分辨率
  detection_confidence: 0.6  # 提高阈值

performance:
  multi_threading: true
  num_threads: 4
```

### 提高精度
```yaml
models:
  input_size: [1280, 720]  # 提高分辨率
  detection_confidence: 0.3  # 降低阈值

stereo_matching:
  num_disparities: 128  # 增加视差范围
```

## 快捷键

- `ESC`: 退出程序
- `Q`: 退出程序（如果支持）

## 环境变量

```bash
# 设置显示（SSH连接时）
export DISPLAY=:0

# Python路径
export PYTHONPATH=$PYTHONPATH:~/YCTarget

# Hailo路径（如果不在默认位置）
export HAILO_SDK_PATH=/path/to/hailo/sdk
```

## 常用Python代码片段

### 初始化系统
```python
from src.main import ObstacleAvoidanceSystem

system = ObstacleAvoidanceSystem("configs/system_config.yaml")
system.run(left_camera_id=0, right_camera_id=1)
```

### 单独使用检测器
```python
from src.detection import YOLODetector
import cv2

detector = YOLODetector("models/yolo_obstacle.hef")
image = cv2.imread("test.jpg")
detections = detector.detect(image)
```

### 更新雷达数据
```python
from src.interface import RadarFusionInterface

radar = RadarFusionInterface()
radar_data = [
    {'distance': 5.0, 'velocity': 0.0, 'azimuth': 10.0}
]
radar.update_radar_data(radar_data)
```

## 文件结构快速查找

- **主程序**: `src/main.py`
- **相机模块**: `src/camera/stereo_camera.py`
- **检测模块**: `src/detection/yolo_detector.py`
- **分割模块**: `src/segmentation/unet_segmenter.py`
- **立体匹配**: `src/stereo/stereo_matcher.py`
- **信息融合**: `src/fusion/info_fusion.py`
- **风险评估**: `src/risk/risk_assessor.py`
- **接口模块**: `src/interface/brake_interface.py`
- **显示模块**: `src/display/bev_display.py`

## 联系信息

- **部署文档**: `docs/DEPLOYMENT.md`
- **API文档**: `docs/API.md`
- **项目总结**: `docs/PROJECT_SUMMARY.md`

