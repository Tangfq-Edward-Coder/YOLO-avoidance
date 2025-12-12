# 部署文档

本文档详细说明如何将实时视觉避障系统部署到树莓派5 + Hailo-8硬件平台上。

## 目录

1. [硬件准备](#硬件准备)
2. [系统环境配置](#系统环境配置)
3. [软件安装](#软件安装)
4. [相机标定](#相机标定)
5. [模型准备与转换](#模型准备与转换)
6. [系统配置](#系统配置)
7. [运行系统](#运行系统)
8. [故障排除](#故障排除)

---

## 硬件准备

### 必需硬件

- **树莓派5** (8GB RAM推荐)
- **Hailo-8 AI加速模块** (M.2版本)
- **适配Hailo-8 M.2接口的树莓派扩展板**
- **双目摄像头** (推荐OAK-D-Lite或两个全局快门相机)
- **MicroSD卡** (至少64GB，Class 10或更高)
- **电源适配器** (5V 5A，官方推荐)
- **散热风扇** (推荐，确保Hailo-8稳定运行)
- **HDMI线** (用于调试)
- **键盘和鼠标** (用于初始配置)

### 硬件组装步骤

1. **安装Hailo-8模块**
   - 将Hailo-8 M.2模块插入扩展板的M.2接口
   - 确保连接牢固，注意防静电

2. **连接扩展板到树莓派**
   - 将扩展板通过GPIO接口连接到树莓派5
   - 检查所有连接是否牢固

3. **安装散热风扇**
   - 将散热风扇连接到树莓派的GPIO电源引脚
   - 确保Hailo-8模块有良好的散热

4. **连接双目摄像头**
   - 根据摄像头类型连接（USB或CSI接口）
   - 记录左右相机的设备ID（通常为/dev/video0和/dev/video1）

---

## 系统环境配置

### 1. 安装Raspberry Pi OS

1. **下载Raspberry Pi OS**
   - 访问 https://www.raspberrypi.com/software/
   - 下载Raspberry Pi Imager

2. **烧录系统**
   ```bash
   # 使用Raspberry Pi Imager将系统烧录到MicroSD卡
   # 推荐使用64位版本（Raspberry Pi OS 64-bit）
   ```

3. **首次启动配置**
   - 插入SD卡，连接电源、显示器、键盘鼠标
   - 完成初始设置（语言、时区、WiFi等）
   - 启用SSH（可选，便于远程访问）

### 2. 系统更新

```bash
# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git wget curl vim build-essential
```

### 3. 配置GPU内存

```bash
# 编辑配置文件
sudo nano /boot/firmware/config.txt

# 添加或修改以下行（为GPU分配128MB内存）
gpu_mem=128

# 保存并重启
sudo reboot
```

---

## 软件安装

### 1. 安装Python环境

```bash
# 安装Python 3.11（如果未预装）
sudo apt install -y python3.11 python3.11-venv python3-pip

# 创建虚拟环境（推荐）
python3 -m venv ~/obstacle_avoidance_env
source ~/obstacle_avoidance_env/bin/activate
```

### 2. 安装Hailo-8驱动和SDK

```bash
# 创建工作目录
mkdir -p ~/hailo_workspace
cd ~/hailo_workspace

# 下载Hailo SDK（需要从Hailo官网获取）
# 注意：需要注册Hailo账户并下载SDK
wget https://hailo.ai/downloads/hailo-platform-*.tar.gz

# 解压并安装
tar -xzf hailo-platform-*.tar.gz
cd hailo-platform-*/
./install.sh

# 验证安装
hailortcli fw-control identify
```

### 3. 安装项目依赖

```bash
# 进入项目目录
cd ~/YCTarget

# 激活虚拟环境（如果使用）
source ~/obstacle_avoidance_env/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 如果使用Hailo-8，安装Hailo Python包
pip install hailo-platform
```

### 4. 安装系统依赖

```bash
# OpenCV系统依赖
sudo apt install -y libopencv-dev python3-opencv

# Pygame依赖
sudo apt install -y python3-pygame

# GStreamer（可选）
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly python3-gst-1.0
```

---

## 相机标定

### 1. 准备标定板

- 打印棋盘格标定板（推荐9x6或10x7）
- 确保标定板平整，无明显弯曲

### 2. 采集标定图像

```bash
# 运行标定脚本（需要自行实现或使用OpenCV示例）
python scripts/calibrate_stereo.py \
    --left-camera 0 \
    --right-camera 1 \
    --images-dir ./calibration_images \
    --board-width 9 \
    --board-height 6 \
    --square-size 0.025
```

### 3. 更新配置文件

将标定结果更新到 `configs/system_config.yaml`:

```yaml
camera:
  left_camera_matrix: [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
  right_camera_matrix: [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
  left_dist_coeffs: [k1, k2, p1, p2, k3]
  right_dist_coeffs: [k1, k2, p1, p2, k3]
  stereo:
    R: [[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]]
    T: [tx, ty, tz]
    # ... 其他参数
```

---

## 模型准备与转换

### 1. 训练模型（在PC/服务器上）

#### YOLO模型训练

```bash
# 准备数据集（YOLO格式）
# data.yaml格式：
# train: /path/to/train/images
# val: /path/to/val/images
# nc: 3
# names: ['person', 'car', 'obstacle']

# 训练YOLOv11
python src/yolov8_train.py \
    --model yolov11n.pt \
    --data data.yaml \
    --epochs 100 \
    --imgsz 640 \
    --batch 16 \
    --device 0
```

#### U-Net模型训练

```bash
# 准备分割数据集（图像+掩膜）
# 训练U-Net（需要自行实现训练脚本）
python src/train_unet.py \
    --data-dir ./segmentation_data \
    --epochs 50 \
    --batch-size 8
```

### 2. 模型转换

#### 转换为ONNX格式

```bash
# YOLO转ONNX
python scripts/export_yolo_to_onnx.py \
    --weights runs/train/yolov11n/weights/best.pt \
    --output models/yolo_obstacle.onnx \
    --imgsz 640

# U-Net转ONNX
python scripts/export_unet_to_onnx.py \
    --weights runs/train/unet/weights/best.pth \
    --output models/unet_obstacle.onnx \
    --imgsz 640
```

#### 转换为Hailo HEF格式

```bash
# 安装Hailo Dataflow Compiler (HDF)
# 从Hailo官网下载并安装

# 转换YOLO模型
hailo compile \
    --input models/yolo_obstacle.onnx \
    --output models/yolo_obstacle.hef \
    --input-shape 1,3,640,480 \
    --calibration-dataset calibration_images/

# 转换U-Net模型
hailo compile \
    --input models/unet_obstacle.onnx \
    --output models/unet_obstacle.hef \
    --input-shape 1,3,640,480 \
    --calibration-dataset calibration_images/
```

### 3. 部署模型到树莓派

```bash
# 将HEF文件复制到树莓派
scp models/*.hef pi@raspberrypi.local:~/YCTarget/models/

# 或使用U盘直接复制
```

---

## 系统配置

### 1. 更新配置文件

编辑 `configs/system_config.yaml`:

```yaml
models:
  yolo_model: "models/yolo_obstacle.hef"  # 或 .onnx/.pt
  unet_model: "models/unet_obstacle.hef"   # 或 .onnx

camera:
  image_width: 640
  image_height: 480
  baseline: 0.12  # 根据实际标定结果修改

hailo:
  enabled: true
  device_index: 0
```

### 2. 测试相机

```bash
# 测试左相机
v4l2-ctl --device=/dev/video0 --list-formats

# 测试右相机
v4l2-ctl --device=/dev/video1 --list-formats

# 使用OpenCV测试
python -c "import cv2; cap = cv2.VideoCapture(0); ret, img = cap.read(); print('Left camera OK' if ret else 'Left camera FAIL')"
python -c "import cv2; cap = cv2.VideoCapture(1); ret, img = cap.read(); print('Right camera OK' if ret else 'Right camera FAIL')"
```

### 3. 测试Hailo-8

```bash
# 检查Hailo设备
hailortcli fw-control identify

# 测试模型加载
python -c "import hailo_platform; print('Hailo OK')"
```

---

## 运行系统

### 1. 基本运行

```bash
# 激活虚拟环境
source ~/obstacle_avoidance_env/bin/activate

# 进入项目目录
cd ~/YCTarget

# 运行系统
python src/main.py \
    --config configs/system_config.yaml \
    --left-camera 0 \
    --right-camera 1
```

### 2. 使用测试图像运行

```bash
python src/main.py \
    --test-image-left test_data/left_001.jpg \
    --test-image-right test_data/right_001.jpg
```

### 3. 后台运行

```bash
# 使用nohup
nohup python src/main.py > system.log 2>&1 &

# 或使用systemd服务（推荐）
sudo cp scripts/obstacle_avoidance.service /etc/systemd/system/
sudo systemctl enable obstacle_avoidance.service
sudo systemctl start obstacle_avoidance.service

# 查看日志
sudo journalctl -u obstacle_avoidance.service -f
```

### 4. 性能监控

```bash
# 监控CPU和内存
htop

# 监控GPU
vcgencmd measure_temp

# 监控Hailo温度（如果支持）
hailortcli fw-control identify
```

---

## 故障排除

### 1. 相机无法打开

**问题**: `无法打开左相机 (ID: 0)`

**解决方案**:
```bash
# 检查相机设备
ls -l /dev/video*

# 检查权限
sudo usermod -a -G video $USER
# 重新登录

# 检查v4l2驱动
sudo modprobe v4l2loopback
```

### 2. Hailo-8未识别

**问题**: `未找到Hailo设备`

**解决方案**:
```bash
# 检查设备连接
lsusb | grep Hailo

# 检查驱动
dmesg | grep hailo

# 重新加载驱动
sudo modprobe hailo_pci  # 或相应的驱动模块
```

### 3. 模型加载失败

**问题**: `Hailo模型文件不存在` 或 `模型格式错误`

**解决方案**:
```bash
# 检查模型文件
ls -lh models/*.hef

# 验证HEF文件
hailortcli parse-hef models/yolo_obstacle.hef

# 检查模型路径配置
cat configs/system_config.yaml | grep model
```

### 4. 性能问题

**问题**: FPS低于15，延迟过高

**解决方案**:
```bash
# 降低输入分辨率
# 编辑 configs/system_config.yaml
models:
  input_size: [320, 240]  # 从640x480降低

# 减少检测置信度阈值
models:
  detection_confidence: 0.6  # 从0.5提高

# 关闭不必要的显示
# 在代码中注释掉显示更新部分
```

### 5. 内存不足

**问题**: `MemoryError` 或系统卡顿

**解决方案**:
```bash
# 增加交换空间
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# 设置 CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 减少批处理大小
# 编辑配置文件
hailo:
  batch_size: 1
```

### 6. 显示问题

**问题**: Pygame窗口无法显示

**解决方案**:
```bash
# 设置显示环境变量
export DISPLAY=:0

# 检查X11
echo $DISPLAY

# 如果使用SSH，启用X11转发
ssh -X pi@raspberrypi.local
```

---

## 性能优化建议

1. **使用Hailo-8加速**: 确保模型转换为HEF格式并在Hailo上运行
2. **优化图像分辨率**: 根据实际需求调整输入分辨率
3. **多线程处理**: 启用配置文件中的多线程选项
4. **减少不必要的计算**: 只在需要时进行分割
5. **使用硬件加速**: 启用树莓派的GPU加速（如果支持）

---

## 联系与支持

如遇到问题，请检查：
1. 系统日志: `~/YCTarget/system.log`
2. Hailo日志: `~/.hailo/logs/`
3. 系统日志: `sudo journalctl -xe`

更多信息请参考项目README.md文件。

