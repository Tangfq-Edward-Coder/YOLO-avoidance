"""
单目摄像头适配器
用于Windows调试，将单目摄像头模拟为双目
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, Optional


class MonoCamera:
    """单目摄像头类，用于Windows调试"""
    
    def __init__(self, camera_id: int = 0, image_width: int = 640, image_height: int = 480):
        """
        初始化单目摄像头
        
        Args:
            camera_id: 相机设备ID
            image_width: 图像宽度
            image_height: 图像高度
        """
        self.camera_id = camera_id
        self.image_width = image_width
        self.image_height = image_height
        self.camera: Optional[cv2.VideoCapture] = None
    
    def open(self):
        """打开摄像头"""
        self.camera = cv2.VideoCapture(self.camera_id)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"无法打开相机 (ID: {self.camera_id})")
        
        # 设置相机参数
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_height)
        
        print(f"成功打开单目摄像头 (ID: {self.camera_id})")
        print(f"分辨率: {self.image_width}x{self.image_height}")
    
    def read(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        读取图像（模拟双目，返回相同的图像）
        
        Returns:
            (left_image, right_image): 左右图像（实际是同一图像）
        """
        if self.camera is None:
            raise RuntimeError("相机未打开，请先调用 open() 方法")
        
        ret, image = self.camera.read()
        
        if not ret:
            return None, None
        
        # 调整大小
        if image.shape[1] != self.image_width or image.shape[0] != self.image_height:
            image = cv2.resize(image, (self.image_width, self.image_height))
        
        # 返回相同的图像作为左右图像（用于调试）
        return image.copy(), image.copy()
    
    def read_raw(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        读取原始图像
        
        Returns:
            (left_image, right_image): 左右图像
        """
        return self.read()
    
    def release(self):
        """释放相机资源"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()

