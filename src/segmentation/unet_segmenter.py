"""
U-Net精细分割模块
支持CPU、GPU和Hailo-8推理
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path
import yaml

try:
    import hailo_platform
    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False


class UNetSegmenter:
    """U-Net分割器，用于对检测到的目标进行精细分割"""
    
    def __init__(
        self,
        model_path: str,
        config_path: str = "configs/system_config.yaml",
        device: str = "auto"
    ):
        """
        初始化U-Net分割器
        
        Args:
            model_path: 模型文件路径（支持.onnx, .hef格式）
            config_path: 配置文件路径
            device: 设备类型 ('cpu', 'cuda', 'hailo', 'auto')
        """
        self.model_path = Path(model_path)
        self.config = self._load_config(config_path)
        self.model_config = self.config['models']
        
        # 输入尺寸
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
            else:
                return "cpu"
        return device
    
    def _init_model(self):
        """初始化模型"""
        if self.device == "hailo":
            self._init_hailo_model()
        elif self.device == "cpu":
            self._init_cpu_model()
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
    
    def _init_cpu_model(self):
        """初始化CPU模型（使用ONNX）"""
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError("CPU模式需要安装onnxruntime")
        
        if self.model_path.suffix != '.onnx':
            raise ValueError("CPU模式仅支持ONNX格式")
        
        self.ort_session = ort.InferenceSession(
            str(self.model_path),
            providers=['CPUExecutionProvider']
        )
    
    def segment(
        self,
        image: np.ndarray,
        bbox: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        执行分割
        
        Args:
            image: 输入图像 (BGR格式)
            bbox: 可选的目标边界框 [x1, y1, x2, y2]，如果提供则只分割该区域
        
        Returns:
            分割掩膜 (二值图像，0或255)
        """
        # 如果提供了bbox，裁剪图像
        if bbox is not None:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(image.shape[1], x2)
            y2 = min(image.shape[0], y2)
            roi = image[y1:y2, x1:x2]
        else:
            roi = image
            x1, y1 = 0, 0
        
        # 执行分割
        if self.device == "hailo":
            mask = self._segment_hailo(roi)
        elif self.device == "cpu":
            mask = self._segment_cpu(roi)
        else:
            raise RuntimeError(f"不支持的设备类型: {self.device}")
        
        # 如果裁剪了图像，需要将掩膜映射回原图尺寸
        if bbox is not None:
            full_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
            full_mask[y1:y2, x1:x2] = mask
            mask = full_mask
        
        return mask
    
    def _segment_hailo(self, image: np.ndarray) -> np.ndarray:
        """使用Hailo进行分割"""
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
        mask = self._postprocess_hailo(output, image.shape)
        return mask
    
    def _segment_cpu(self, image: np.ndarray) -> np.ndarray:
        """使用CPU进行分割"""
        # 预处理
        input_image = self._preprocess(image)
        
        # 推理
        input_name = self.ort_session.get_inputs()[0].name
        output = self.ort_session.run(None, {input_name: input_image})
        
        # 后处理
        mask = self._postprocess_cpu(output[0], image.shape)
        return mask
    
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
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Hailo输出后处理
        假设输出为 [batch, 1, H, W] 或 [batch, H, W]
        """
        if len(output.shape) == 4:
            output = output[0, 0]  # 移除batch和channel维度
        elif len(output.shape) == 3:
            output = output[0]  # 移除batch维度
        
        # 调整大小到原图尺寸
        mask = cv2.resize(output, (image_shape[1], image_shape[0]))
        
        # 二值化
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        return mask
    
    def _postprocess_cpu(
        self,
        output: np.ndarray,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """CPU输出后处理"""
        if len(output.shape) == 4:
            output = output[0, 0]  # 移除batch和channel维度
        elif len(output.shape) == 3:
            output = output[0]  # 移除batch维度
        
        # 调整大小到原图尺寸
        mask = cv2.resize(output, (image_shape[1], image_shape[0]))
        
        # 二值化
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        return mask
    
    def __del__(self):
        """析构函数"""
        if self.hailo_device is not None:
            try:
                self.hailo_device.release()
            except:
                pass

