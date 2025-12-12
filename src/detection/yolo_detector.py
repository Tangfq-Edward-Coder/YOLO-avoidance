"""
YOLO目标检测模块
支持CPU、GPU和Hailo-8推理
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import yaml

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

try:
    import hailo_platform
    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False


class YOLODetector:
    """YOLO目标检测器"""
    
    def __init__(
        self,
        model_path: str,
        config_path: str = "configs/system_config.yaml",
        device: str = "auto"
    ):
        """
        初始化YOLO检测器
        
        Args:
            model_path: 模型文件路径（支持.pt, .onnx, .hef格式）
            config_path: 配置文件路径
            device: 设备类型 ('cpu', 'cuda', 'hailo', 'auto')
        """
        self.model_path = Path(model_path)
        self.config = self._load_config(config_path)
        self.model_config = self.config['models']
        
        # 检测参数
        self.conf_threshold = self.model_config['detection_confidence']
        self.nms_threshold = self.model_config['nms_threshold']
        self.input_size = tuple(self.model_config['input_size'])
        
        # 设备选择
        self.device = self._select_device(device)
        
        # 初始化模型
        self.model = None
        self.hailo_device = None
        self._init_model()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _select_device(self, device: str) -> str:
        """自动选择设备"""
        if device == "auto":
            if HAILO_AVAILABLE and self.model_path.suffix == '.hef':
                return "hailo"
            elif ULTRALYTICS_AVAILABLE:
                return "ultralytics"
            else:
                return "cpu"
        return device
    
    def _init_model(self):
        """初始化模型"""
        if self.device == "hailo":
            self._init_hailo_model()
        elif self.device == "ultralytics":
            self._init_ultralytics_model()
        else:
            raise RuntimeError(f"不支持的设备类型: {self.device}")
    
    def _init_hailo_model(self):
        """初始化Hailo模型"""
        if not HAILO_AVAILABLE:
            raise RuntimeError("Hailo平台未安装，请安装hailo_platform")
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Hailo模型文件不存在: {self.model_path}")
        
        # 初始化Hailo设备
        devices = hailo_platform.scan_devices()
        if not devices:
            raise RuntimeError("未找到Hailo设备")
        
        self.hailo_device = hailo_platform.Device(devices[0])
        with self.hailo_device:
            # 加载HEF模型
            self.model = hailo_platform.HEF(self.model_path)
            self.network_group = self.model.configure(self.hailo_device)
    
    def _init_ultralytics_model(self):
        """初始化Ultralytics模型"""
        if not ULTRALYTICS_AVAILABLE:
            raise RuntimeError("Ultralytics未安装，请安装ultralytics")
        
        if self.model_path.suffix == '.hef':
            raise ValueError("Ultralytics不支持HEF格式，请使用.pt或.onnx格式")
        
        self.model = YOLO(str(self.model_path))
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        执行目标检测
        
        Args:
            image: 输入图像 (BGR格式)
        
        Returns:
            检测结果列表，每个元素包含:
            {
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'class_id': int,
                'class_name': str
            }
        """
        if self.device == "hailo":
            return self._detect_hailo(image)
        elif self.device == "ultralytics":
            return self._detect_ultralytics(image)
        else:
            raise RuntimeError(f"不支持的设备类型: {self.device}")
    
    def _detect_hailo(self, image: np.ndarray) -> List[Dict]:
        """使用Hailo进行推理"""
        if self.hailo_device is None:
            raise RuntimeError("Hailo设备未初始化")
        
        # 预处理
        input_image = self._preprocess(image)
        
        # 推理
        with self.hailo_device:
            input_vstreams = self.network_group.get_input_vstreams()
            output_vstreams = self.network_group.get_output_vstreams()
            
            with self.network_group.activate():
                input_vstreams[0].send(input_image)
                output = output_vstreams[0].recv()
        
        # 后处理
        detections = self._postprocess_hailo(output, image.shape)
        return detections
    
    def _detect_ultralytics(self, image: np.ndarray) -> List[Dict]:
        """使用Ultralytics进行推理"""
        results = self.model.predict(
            image,
            conf=self.conf_threshold,
            iou=self.nms_threshold,
            imgsz=self.input_size,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = result.names[cls_id]
                
                detections.append({
                    'bbox': box.tolist(),
                    'confidence': conf,
                    'class_id': cls_id,
                    'class_name': cls_name
                })
        
        return detections
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 调整大小
        resized = cv2.resize(image, self.input_size)
        # 归一化
        normalized = resized.astype(np.float32) / 255.0
        # 转换为RGB
        rgb = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)
        # 调整维度 (H, W, C) -> (1, C, H, W)
        transposed = np.transpose(rgb, (2, 0, 1))
        batched = np.expand_dims(transposed, axis=0)
        return batched
    
    def _postprocess_hailo(
        self,
        output: np.ndarray,
        image_shape: Tuple[int, int, int]
    ) -> List[Dict]:
        """
        Hailo输出后处理
        注意：这里需要根据实际模型输出格式进行调整
        """
        detections = []
        h, w = image_shape[:2]
        
        # 假设输出格式为 [batch, num_detections, 6]
        # 6 = [x1, y1, x2, y2, conf, cls]
        if len(output.shape) == 3:
            output = output[0]  # 移除batch维度
        
        for det in output:
            if det[4] < self.conf_threshold:
                continue
            
            # 缩放坐标到原图尺寸
            x1 = int(det[0] * w / self.input_size[0])
            y1 = int(det[1] * h / self.input_size[1])
            x2 = int(det[2] * w / self.input_size[0])
            y2 = int(det[3] * h / self.input_size[1])
            
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(det[4]),
                'class_id': int(det[5]),
                'class_name': f"class_{int(det[5])}"
            })
        
        return detections
    
    def __del__(self):
        """析构函数"""
        if self.hailo_device is not None:
            try:
                self.hailo_device.release()
            except:
                pass

