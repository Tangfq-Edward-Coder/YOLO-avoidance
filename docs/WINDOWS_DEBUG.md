# Windows调试指南

本文档说明如何在Windows环境下调试实时视觉避障系统。

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行单目模式

```bash
# 使用默认摄像头（ID=0）
python src/main_mono.py

# 指定摄像头ID
python src/main_mono.py --camera 0

# 使用测试图像
python src/main_mono.py --test-image test.jpg
```

## 单目模式说明

Windows调试版本使用单目摄像头，通过以下方式模拟双目功能：

1. **深度估计**: 基于检测框大小估计深度
   - 使用相似三角形原理
   - 假设对象高度（默认1.7米，适用于人）
   - 公式: `depth = (focal_length * real_height) / pixel_height`

2. **视差图**: 创建假的视差图以保持兼容性
   - 基于估计的深度值计算
   - 仅用于显示和调试

## 功能限制

单目模式下的限制：

- ✅ **目标检测**: 完全支持（使用YOLO）
- ✅ **分割**: 支持（如果模型可用）
- ⚠️ **深度估计**: 基于检测框大小，精度较低
- ⚠️ **测距**: 相对误差较大（约10-20%）
- ❌ **立体匹配**: 不支持（需要双目）

## 配置说明

单目模式使用 `configs/system_config_mono.yaml` 配置文件，主要差异：

- `yolo_model`: 使用 `.pt` 格式（Windows不支持HEF）
- `hailo.enabled`: 设置为 `false`
- `detection_confidence`: 建议降低到0.25以检测更多目标

## 调试技巧

### 1. 检查摄像头

```python
import cv2

# 列出所有摄像头
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"摄像头 {i}: 可用")
        cap.release()
```

### 2. 测试检测

```python
from src.detection import YOLODetector
import cv2

detector = YOLODetector("yolov8n.pt")
image = cv2.imread("test.jpg")
detections = detector.detect(image)
print(f"检测到 {len(detections)} 个目标")
```

### 3. 性能监控

系统会自动显示：
- FPS（帧率）
- 处理时间（毫秒）
- 检测到的障碍物数量

## 常见错误及解决方案

### 错误1: ModuleNotFoundError: No module named 'src'
**问题**: 导入模块失败
**解决**: 
- 确保在项目根目录运行
- 代码已自动修复路径问题，直接运行即可
- 或使用模块方式: `python -m src.main_mono`

### 错误2: 摄像头无法打开
**问题**: `无法打开相机 (ID: 0)`
**解决**: 
- 检查摄像头是否被其他程序占用
- 尝试不同的摄像头ID（0, 1, 2...）
- 检查摄像头驱动是否正常

### 错误3: YOLO模型下载失败
**问题**: 首次运行需要下载模型
**解决**: 
- 确保网络连接正常
- 如果下载慢，可以手动下载模型文件

### 错误4: 配置文件不存在
**问题**: `FileNotFoundError: configs/system_config_mono.yaml`
**解决**: 确保在项目根目录运行，或使用 `--config` 指定配置文件路径

### 错误5: Pygame窗口无法显示
**问题**: 窗口不显示或黑屏
**解决**: 
- 检查是否有其他窗口遮挡
- 尝试调整窗口大小
- 检查显卡驱动

### 错误6: 深度估计不准确
**问题**: 深度值明显错误
**解决**: 
- 这是单目模式的正常限制
- 调整 `focal_length` 参数
- 调整对象高度假设值

### 错误7: PowerShell没有输出
**问题**: 运行后没有任何输出
**解决**: 
- 使用CMD: `cmd /c "python src/main_mono.py --camera 0"`
- 重定向到文件: `python src/main_mono.py --camera 0 > output.log 2>&1`
- 在IDE中运行（VSCode/PyCharm）

## 性能优化

### Windows特定优化

1. **使用GPU加速**:
   ```yaml
   # 在配置文件中，YOLO会自动使用GPU（如果可用）
   ```

2. **降低分辨率**:
   ```yaml
   camera:
     image_width: 320
     image_height: 240
   ```

3. **减少检测目标**:
   ```yaml
   models:
     detection_confidence: 0.5  # 提高阈值
   ```

## 运行方法

### 方法1: 直接运行（推荐）
```bash
python src/main_mono.py --camera 0
```

### 方法2: 使用模块方式
```bash
python -m src.main_mono --camera 0
```

### 方法3: 使用批处理文件
双击运行 `run_mono_fixed.bat`

### 方法4: 在IDE中运行
在VSCode/PyCharm等IDE中：
1. 确保工作目录设置为项目根目录
2. 直接运行 `src/main_mono.py`

## 如果PowerShell没有输出

PowerShell可能抑制了输出，尝试：

```bash
# 方法1: 使用CMD运行
cmd /c "python src/main_mono.py --camera 0"

# 方法2: 重定向到文件
python src/main_mono.py --camera 0 > output.log 2>&1
type output.log

# 方法3: 使用Python的-u参数
python -u src/main_mono.py
```

## 下一步

完成Windows调试后：

1. 在树莓派上部署完整系统
2. 进行双目相机标定
3. 转换模型为HEF格式
4. 使用Hailo-8加速

参考 `docs/DEPLOYMENT.md` 了解完整部署流程。

