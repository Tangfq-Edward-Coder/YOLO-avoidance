# API参考文档

本文档提供省实未来汽车视觉避障系统的完整API接口说明。

## 目录

- [相机模块](#相机模块)
- [检测模块](#检测模块)
- [分割模块](#分割模块)
- [立体匹配模块](#立体匹配模块)
- [信息融合模块](#信息融合模块)
- [风险评估模块](#风险评估模块)
- [TTC估算模块](#ttc估算模块)
- [语音提示模块](#语音提示模块)
- [显示模块](#显示模块)

## 相机模块

### `StereoCamera`

双目摄像头采集与预处理类。

#### `__init__(config_path: str)`

初始化双目相机。

**参数**:
- `config_path`: 配置文件路径

#### `open(left_camera_id: int, right_camera_id: int)`

打开双目相机。

**参数**:
- `left_camera_id`: 左相机设备ID
- `right_camera_id`: 右相机设备ID

#### `read() -> Tuple[np.ndarray, np.ndarray]`

读取一帧图像。

**返回**:
- `(left_image, right_image)`: 左右图像（BGR格式）

#### `release()`

释放相机资源。

## 检测模块

### `YOLODetector`

YOLO目标检测器。

#### `__init__(model_path: str, config_path: str, device: str = "auto")`

初始化YOLO检测器。

**参数**:
- `model_path`: 模型文件路径（支持.pt, .onnx, .hef格式）
- `config_path`: 配置文件路径
- `device`: 设备类型 ('cpu', 'cuda', 'hailo', 'auto')

#### `detect(image: np.ndarray) -> List[Dict]`

执行目标检测。

**参数**:
- `image`: 输入图像（BGR格式）

**返回**:
- 检测结果列表，每个元素包含：
  ```python
  {
      'bbox': [x1, y1, x2, y2],  # 边界框
      'class': str,               # 类别名称
      'confidence': float,        # 置信度
      'class_id': int             # 类别ID
  }
  ```

## 分割模块

### `UNetSegmenter`

U-Net场景分割器。

#### `__init__(model_path: str, config_path: str, device: str = "auto")`

初始化U-Net分割器。

**参数**:
- `model_path`: 模型文件路径（支持.onnx, .hef格式）
- `config_path`: 配置文件路径
- `device`: 设备类型 ('cpu', 'hailo', 'auto')

#### `segment_full_image(image: np.ndarray) -> np.ndarray`

对整个图像进行场景分割。

**参数**:
- `image`: 输入图像（BGR格式）

**返回**:
- 场景分割掩膜（像素级分割图）

#### `segment(image: np.ndarray, bbox: Optional[List[float]] = None) -> np.ndarray`

执行分割。

**参数**:
- `image`: 输入图像（BGR格式）
- `bbox`: 可选的目标边界框 [x1, y1, x2, y2]

**返回**:
- 分割掩膜（二值图像，0或255）

## 立体匹配模块

### `StereoMatcher`

SGBM立体匹配器。

#### `__init__(config_path: str)`

初始化立体匹配器。

**参数**:
- `config_path`: 配置文件路径

#### `compute_disparity_and_depth(left_image: np.ndarray, right_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`

计算视差图和深度图。

**参数**:
- `left_image`: 左图像
- `right_image`: 右图像

**返回**:
- `(disparity_map, depth_map)`: 视差图和深度图

## 信息融合模块

### `InfoFusion`

信息融合器。

#### `__init__(config_path: str)`

初始化信息融合器。

**参数**:
- `config_path`: 配置文件路径

#### `fuse_detection_and_depth(detections: List[Dict], masks: List[np.ndarray], depth_map: np.ndarray) -> List[Dict]`

融合检测和深度信息。

**参数**:
- `detections`: 检测结果列表
- `masks`: 分割掩膜列表
- `depth_map`: 深度图

**返回**:
- 融合后的障碍物列表，每个元素包含：
  ```python
  {
      'bbox': [x1, y1, x2, y2],
      'class': str,
      'confidence': float,
      'depth': float,              # 深度（米）
      '3d_position': [x, y, z],   # 3D坐标
      'mask': np.ndarray           # 分割掩膜
  }
  ```

#### `filter_by_depth(objects: List[Dict], min_depth: float, max_depth: float) -> List[Dict]`

按深度过滤障碍物。

**参数**:
- `objects`: 障碍物列表
- `min_depth`: 最小深度（米）
- `max_depth`: 最大深度（米）

**返回**:
- 过滤后的障碍物列表

## 风险评估模块

### `RiskAssessor`

碰撞风险评估器。

#### `__init__(config_path: str)`

初始化风险评估器。

**参数**:
- `config_path`: 配置文件路径

#### `assess_risk(objects: List[Dict]) -> Dict`

评估碰撞风险。

**参数**:
- `objects`: 障碍物列表

**返回**:
- 风险评估结果：
  ```python
  {
      'risk_level': 'safe' | 'warning' | 'danger',
      'risk_score': float,        # 风险分数 (0-1)
      'nearest_object': Dict | None,
      'should_brake': bool
  }
  ```

### `RoadRiskAssessor`

道路风险预警器。

#### `__init__(config_path: str)`

初始化道路风险预警器。

**参数**:
- `config_path`: 配置文件路径

#### `assess_long_term_risks(image: np.ndarray) -> Dict[str, bool]`

评估中长期风险。

**参数**:
- `image`: 输入图像

**返回**:
- 中长期风险标志位：
  ```python
  {
      'low_visibility': bool,  # 低能见度
      'wet_road': bool         # 路面湿滑
  }
  ```

#### `assess_short_term_risks(segmentation_mask: Optional[np.ndarray], detected_objects: list) -> Dict[str, bool]`

评估短期风险。

**参数**:
- `segmentation_mask`: 场景分割结果
- `detected_objects`: 检测到的障碍物列表

**返回**:
- 短期风险标志位：
  ```python
  {
      'curve': bool,      # 弯道
      'narrow_road': bool  # 狭窄路段
  }
  ```

#### `assess_all_risks(image: np.ndarray, segmentation_mask: Optional[np.ndarray] = None, detected_objects: list = None) -> Dict`

评估所有道路风险。

**返回**:
- 所有风险标志位：
  ```python
  {
      'long_term': {
          'low_visibility': bool,
          'wet_road': bool
      },
      'short_term': {
          'curve': bool,
          'narrow_road': bool
      }
  }
  ```

## TTC估算模块

### `TTCEstimator`

碰撞时间估算器。

#### `__init__(ego_speed: float = 0.0, history_size: int = 10, min_frames_for_ttc: int = 2)`

初始化TTC估算器。

**参数**:
- `ego_speed`: 自车速度（米/秒）
- `history_size`: 历史记录大小
- `min_frames_for_ttc`: 计算TTC所需的最少帧数

#### `update_ego_speed(speed: float)`

更新自车速度。

**参数**:
- `speed`: 自车速度（米/秒）

#### `estimate_ttc(objects: List[Dict], current_time: Optional[float] = None) -> List[Dict]`

估算所有目标的TTC。

**参数**:
- `objects`: 当前帧检测到的障碍物列表
- `current_time`: 当前时间戳（秒）

**返回**:
- 带TTC信息的障碍物列表，每个元素额外包含：
  ```python
  {
      'ttc': float | None,      # TTC值（秒）
      'ttc_valid': bool          # TTC是否有效
  }
  ```

#### `get_nearest_object_ttc(objects_with_ttc: List[Dict]) -> Optional[Dict]`

获取最近障碍物的TTC。

**参数**:
- `objects_with_ttc`: 带TTC信息的障碍物列表

**返回**:
- 最近障碍物的信息（包含TTC），如果没有则返回None

#### `trigger_brake_alert(ttc_value: float, threshold: float = 3.0) -> bool`

判断是否需要触发紧急刹车警报。

**参数**:
- `ttc_value`: TTC值（秒）
- `threshold`: TTC阈值（秒）

**返回**:
- 是否需要触发警报

## 语音提示模块

### `VoiceAlert`

语音提示类。

#### `__init__(enabled: bool = True)`

初始化语音提示。

**参数**:
- `enabled`: 是否启用语音提示

#### `speak(text: str, lang: str = 'zh-CN')`

播放语音。

**参数**:
- `text`: 要播放的文本
- `lang`: 语言代码（默认中文）

#### `alert_low_visibility()`

低能见度警报。

#### `alert_wet_road()`

路面湿滑警报。

#### `alert_curve()`

弯道警报。

#### `alert_narrow_road()`

狭窄路段警报。

#### `alert_ttc_warning(ttc_value: Optional[float] = None)`

TTC紧急警报。

**参数**:
- `ttc_value`: TTC值（可选）

#### `alert_obstacle_danger()`

障碍物危险警报。

#### `alert_obstacle_warning()`

障碍物警告。

#### `custom_alert(text: str)`

自定义警报。

**参数**:
- `text`: 自定义文本

## 显示模块

### `PyQtDisplay`

PyQt5主显示窗口。

#### `__init__(config_path: str)`

初始化显示窗口。

**参数**:
- `config_path`: 配置文件路径

#### `set_process_callback(callback)`

设置处理回调函数。

**参数**:
- `callback`: 回调函数，返回 (frame, results)

#### `start_processing()`

开始处理。

#### `stop_processing()`

停止处理。

#### `log(message: str)`

添加日志。

**参数**:
- `message`: 日志消息

#### `show()`

显示窗口。

#### `close()`

关闭窗口。

---

**注意**: 详细的类方法和参数说明请参考源代码注释。

