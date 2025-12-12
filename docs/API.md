# API接口文档

本文档详细说明系统的各个模块接口和使用方法。

## 目录

1. [相机模块](#相机模块)
2. [检测模块](#检测模块)
3. [分割模块](#分割模块)
4. [立体匹配模块](#立体匹配模块)
5. [信息融合模块](#信息融合模块)
6. [风险评估模块](#风险评估模块)
7. [接口模块](#接口模块)
8. [显示模块](#显示模块)

---

## 相机模块

### StereoCamera

双目摄像头采集与预处理类。

#### 初始化

```python
from src.camera import StereoCamera

camera = StereoCamera(config_path="configs/system_config.yaml")
```

#### 方法

##### `open(left_camera_id=0, right_camera_id=1)`

打开双目摄像头。

**参数**:
- `left_camera_id` (int): 左相机设备ID，默认0
- `right_camera_id` (int): 右相机设备ID，默认1

**异常**: `RuntimeError` - 如果无法打开相机

##### `read() -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]`

读取并校正双目图像。

**返回**: `(left_rectified, right_rectified)` - 校正后的左右图像

**返回类型**: `Tuple[Optional[np.ndarray], Optional[np.ndarray]]`

##### `read_raw() -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]`

读取原始图像（不进行校正）。

**返回**: `(left_img, right_img)` - 原始左右图像

##### `release()`

释放相机资源。

#### 使用示例

```python
from src.camera import StereoCamera

with StereoCamera() as camera:
    camera.open(0, 1)
    left_img, right_img = camera.read()
    # 处理图像...
```

---

## 检测模块

### YOLODetector

YOLO目标检测器类。

#### 初始化

```python
from src.detection import YOLODetector

detector = YOLODetector(
    model_path="models/yolo_obstacle.hef",
    config_path="configs/system_config.yaml",
    device="auto"  # 'cpu', 'cuda', 'hailo', 'auto'
)
```

#### 方法

##### `detect(image: np.ndarray) -> List[Dict]`

执行目标检测。

**参数**:
- `image` (np.ndarray): 输入图像 (BGR格式)

**返回**: 检测结果列表，每个元素包含:
```python
{
    'bbox': [x1, y1, x2, y2],  # 边界框坐标
    'confidence': float,       # 置信度
    'class_id': int,           # 类别ID
    'class_name': str          # 类别名称
}
```

#### 使用示例

```python
from src.detection import YOLODetector
import cv2

detector = YOLODetector("models/yolo_obstacle.hef")
image = cv2.imread("test.jpg")
detections = detector.detect(image)

for det in detections:
    print(f"检测到: {det['class_name']}, 置信度: {det['confidence']:.2f}")
```

---

## 分割模块

### UNetSegmenter

U-Net分割器类。

#### 初始化

```python
from src.segmentation import UNetSegmenter

segmenter = UNetSegmenter(
    model_path="models/unet_obstacle.hef",
    config_path="configs/system_config.yaml",
    device="auto"
)
```

#### 方法

##### `segment(image: np.ndarray, bbox: Optional[List[float]] = None) -> np.ndarray`

执行分割。

**参数**:
- `image` (np.ndarray): 输入图像 (BGR格式)
- `bbox` (Optional[List[float]]): 可选的目标边界框 [x1, y1, x2, y2]

**返回**: 分割掩膜 (二值图像，0或255)

#### 使用示例

```python
from src.segmentation import UNetSegmenter
import cv2

segmenter = UNetSegmenter("models/unet_obstacle.hef")
image = cv2.imread("test.jpg")
mask = segmenter.segment(image, bbox=[100, 100, 300, 300])
```

---

## 立体匹配模块

### StereoMatcher

立体匹配器类。

#### 初始化

```python
from src.stereo import StereoMatcher

matcher = StereoMatcher(config_path="configs/system_config.yaml")
```

#### 方法

##### `compute_disparity(left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray`

计算视差图。

**参数**:
- `left_image` (np.ndarray): 左图像（灰度图）
- `right_image` (np.ndarray): 右图像（灰度图）

**返回**: 视差图（16位整数）

##### `compute_depth_map(disparity: np.ndarray) -> np.ndarray`

将视差图转换为深度图。

**参数**:
- `disparity` (np.ndarray): 视差图（16位整数）

**返回**: 深度图（米，浮点数）

##### `compute_disparity_and_depth(left_image: np.ndarray, right_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`

同时计算视差图和深度图。

**返回**: `(disparity, depth)` - 视差图和深度图

##### `get_depth_from_mask(depth_map: np.ndarray, mask: np.ndarray) -> float`

从深度图中提取掩膜区域的深度值。

**返回**: 深度值（米）

#### 使用示例

```python
from src.stereo import StereoMatcher
import cv2

matcher = StereoMatcher()
left_img = cv2.imread("left.jpg", cv2.IMREAD_GRAYSCALE)
right_img = cv2.imread("right.jpg", cv2.IMREAD_GRAYSCALE)

disparity, depth = matcher.compute_disparity_and_depth(left_img, right_img)
```

---

## 信息融合模块

### InfoFusion

信息融合器类。

#### 初始化

```python
from src.fusion import InfoFusion

fusion = InfoFusion(config_path="configs/system_config.yaml")
```

#### 方法

##### `fuse_detection_and_depth(detections: List[Dict], segmentation_masks: List[np.ndarray], depth_map: np.ndarray) -> List[Dict]`

融合检测、分割和深度信息。

**参数**:
- `detections`: YOLO检测结果列表
- `segmentation_masks`: 对应的分割掩膜列表
- `depth_map`: 深度图

**返回**: 融合后的障碍物信息列表，每个元素包含:
```python
{
    'bbox': [x1, y1, x2, y2],
    'mask': np.ndarray,
    'depth': float,
    '3d_position': [x, y, z],
    'confidence': float,
    'class_id': int,
    'class_name': str
}
```

##### `filter_by_depth(objects: List[Dict], min_depth: float = 0.1, max_depth: float = 10.0) -> List[Dict]`

根据深度范围过滤障碍物。

#### 使用示例

```python
from src.fusion import InfoFusion

fusion = InfoFusion()
fused_objects = fusion.fuse_detection_and_depth(
    detections, masks, depth_map
)
filtered = fusion.filter_by_depth(fused_objects, min_depth=0.5, max_depth=8.0)
```

---

## 风险评估模块

### RiskAssessor

碰撞风险评估器类。

#### 初始化

```python
from src.risk import RiskAssessor

assessor = RiskAssessor(config_path="configs/system_config.yaml")
```

#### 方法

##### `assess_risk(objects: List[Dict]) -> Dict`

评估碰撞风险。

**参数**:
- `objects`: 障碍物列表

**返回**: 风险评估结果:
```python
{
    'risk_level': 'safe' | 'warning' | 'danger',
    'risk_score': float (0-1),
    'nearest_object': Dict | None,
    'should_brake': bool
}
```

##### `assess_object_risk(obj: Dict) -> Dict`

评估单个障碍物的风险。

**返回**: 单个障碍物的风险评估

#### 使用示例

```python
from src.risk import RiskAssessor

assessor = RiskAssessor()
risk_info = assessor.assess_risk(objects)

if risk_info['should_brake']:
    print("需要刹车！")
```

---

## 接口模块

### BrakeInterface

刹车接口类。

#### 初始化

```python
from src.interface import BrakeInterface

brake = BrakeInterface()
```

#### 方法

##### `trigger_brake(risk_level: str = "danger", brake_level: float = 1.0)`

触发刹车。

##### `release_brake()`

释放刹车。

##### `get_brake_status() -> tuple[bool, float]`

获取刹车状态。

##### `brake_interface(risk_level: str)`

刹车接口函数（符合技术方案要求）。

##### `register_callback(callback)`

注册刹车回调函数。

#### 使用示例

```python
from src.interface import BrakeInterface

brake = BrakeInterface()

def brake_callback(risk_level, brake_level):
    print(f"刹车触发: {risk_level}, 力度: {brake_level}")

brake.register_callback(brake_callback)
brake.trigger_brake("danger", 1.0)
```

### RadarFusionInterface

雷达融合接口类。

#### 初始化

```python
from src.interface import RadarFusionInterface

radar_fusion = RadarFusionInterface()
```

#### 方法

##### `update_radar_data(radar_objects_list: list)`

更新雷达数据（符合技术方案要求）。

**参数**:
- `radar_objects_list`: 雷达目标列表，每个元素包含:
```python
{
    'distance': float,    # 距离（米）
    'velocity': float,    # 速度（米/秒）
    'azimuth': float,     # 方位角（度）
    'elevation': float    # 俯仰角（度，可选）
}
```

##### `fuse_with_vision(vision_objects: list, max_association_distance: float = 1.0) -> list`

将视觉目标与雷达目标进行数据关联。

#### 使用示例

```python
from src.interface import RadarFusionInterface

radar_fusion = RadarFusionInterface()

# 更新雷达数据
radar_data = [
    {'distance': 5.0, 'velocity': 0.0, 'azimuth': 10.0}
]
radar_fusion.update_radar_data(radar_data)

# 融合视觉和雷达数据
fused = radar_fusion.fuse_with_vision(vision_objects)
```

---

## 显示模块

### BEVDisplay

鸟瞰图显示类。

#### 初始化

```python
from src.display import BEVDisplay

display = BEVDisplay(config_path="configs/system_config.yaml")
```

#### 方法

##### `update(objects: List[Dict], risk_info: Dict, fps: float)`

更新显示。

**参数**:
- `objects`: 障碍物列表
- `risk_info`: 风险评估信息
- `fps`: 当前帧率

##### `handle_events() -> bool`

处理事件。

**返回**: 是否继续运行

##### `close()`

关闭显示。

#### 使用示例

```python
from src.display import BEVDisplay

display = BEVDisplay()

while True:
    display.update(objects, risk_info, fps)
    if not display.handle_events():
        break

display.close()
```

---

## 主系统

### ObstacleAvoidanceSystem

实时视觉避障系统主类。

#### 初始化

```python
from src.main import ObstacleAvoidanceSystem

system = ObstacleAvoidanceSystem(config_path="configs/system_config.yaml")
```

#### 方法

##### `run(left_camera_id: int = 0, right_camera_id: int = 1)`

运行主循环。

##### `run_with_images(left_image_path: str, right_image_path: str)`

使用图像文件运行（用于测试）。

##### `shutdown()`

关闭系统。

#### 使用示例

```python
from src.main import ObstacleAvoidanceSystem

system = ObstacleAvoidanceSystem()
system.run(left_camera_id=0, right_camera_id=1)
```

---

## 配置参数

主要配置在 `configs/system_config.yaml` 中，包括：

- **相机参数**: 内参、畸变系数、立体校正参数
- **模型路径**: YOLO和U-Net模型文件路径
- **检测参数**: 置信度阈值、NMS阈值
- **立体匹配参数**: SGBM算法参数
- **风险评估参数**: 距离阈值、风险阈值
- **显示参数**: 窗口尺寸、更新频率
- **Hailo配置**: 设备索引、批处理大小

详细配置说明请参考 `configs/system_config.yaml` 文件中的注释。

