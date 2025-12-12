"""
双目摄像头采集与预处理模块
支持畸变校正和立体校正
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, Optional
import yaml
from pathlib import Path


class StereoCamera:
    """双目摄像头类，负责图像采集、校正和预处理"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化双目摄像头
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.camera_config = self.config['camera']
        
        # 初始化相机参数
        self._init_camera_params()
        
        # 初始化相机设备
        self.left_camera: Optional[cv2.VideoCapture] = None
        self.right_camera: Optional[cv2.VideoCapture] = None
        
        # 校正映射表
        self.left_map1: Optional[np.ndarray] = None
        self.left_map2: Optional[np.ndarray] = None
        self.right_map1: Optional[np.ndarray] = None
        self.right_map2: Optional[np.ndarray] = None
        
        # 立体校正映射
        self._init_rectification_maps()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_camera_params(self):
        """初始化相机参数"""
        # 相机内参矩阵
        self.left_camera_matrix = np.array(
            self.camera_config['left_camera_matrix'], dtype=np.float32
        )
        self.right_camera_matrix = np.array(
            self.camera_config['right_camera_matrix'], dtype=np.float32
        )
        
        # 畸变系数
        self.left_dist_coeffs = np.array(
            self.camera_config['left_dist_coeffs'], dtype=np.float32
        )
        self.right_dist_coeffs = np.array(
            self.camera_config['right_dist_coeffs'], dtype=np.float32
        )
        
        # 立体校正参数
        stereo_config = self.camera_config['stereo']
        self.R = np.array(stereo_config['R'], dtype=np.float32)
        self.T = np.array(stereo_config['T'], dtype=np.float32)
        self.R1 = np.array(stereo_config['R1'], dtype=np.float32)
        self.R2 = np.array(stereo_config['R2'], dtype=np.float32)
        self.P1 = np.array(stereo_config['P1'], dtype=np.float32)
        self.P2 = np.array(stereo_config['P2'], dtype=np.float32)
        
        # 处理Q矩阵，支持表达式字符串（如 "-1/0.12"）
        from src.utils.config_utils import parse_matrix
        Q_processed = parse_matrix(stereo_config['Q'])
        self.Q = np.array(Q_processed, dtype=np.float32)
        
        # 图像尺寸
        self.image_width = self.camera_config['image_width']
        self.image_height = self.camera_config['image_height']
        self.image_size = (self.image_width, self.image_height)
        
        # 基线距离
        self.baseline = self.camera_config['baseline']
        self.focal_length = self.camera_config['focal_length']
    
    def _init_rectification_maps(self):
        """初始化立体校正映射表"""
        # 计算校正映射
        self.left_map1, self.left_map2 = cv2.initUndistortRectifyMap(
            self.left_camera_matrix,
            self.left_dist_coeffs,
            self.R1,
            self.P1,
            self.image_size,
            cv2.CV_16SC2
        )
        
        self.right_map1, self.right_map2 = cv2.initUndistortRectifyMap(
            self.right_camera_matrix,
            self.right_dist_coeffs,
            self.R2,
            self.P2,
            self.image_size,
            cv2.CV_16SC2
        )
    
    def open(self, left_camera_id: int = 0, right_camera_id: int = 1):
        """
        打开双目摄像头
        
        Args:
            left_camera_id: 左相机设备ID
            right_camera_id: 右相机设备ID
        """
        self.left_camera = cv2.VideoCapture(left_camera_id)
        self.right_camera = cv2.VideoCapture(right_camera_id)
        
        if not self.left_camera.isOpened():
            raise RuntimeError(f"无法打开左相机 (ID: {left_camera_id})")
        if not self.right_camera.isOpened():
            raise RuntimeError(f"无法打开右相机 (ID: {right_camera_id})")
        
        # 设置相机参数
        self.left_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_width)
        self.left_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_height)
        self.right_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_width)
        self.right_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_height)
    
    def read(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        读取并校正双目图像
        
        Returns:
            (left_rectified, right_rectified): 校正后的左右图像
        """
        if self.left_camera is None or self.right_camera is None:
            raise RuntimeError("相机未打开，请先调用 open() 方法")
        
        ret_left, left_img = self.left_camera.read()
        ret_right, right_img = self.right_camera.read()
        
        if not ret_left or not ret_right:
            return None, None
        
        # 立体校正
        left_rectified = cv2.remap(
            left_img, self.left_map1, self.left_map2, cv2.INTER_LINEAR
        )
        right_rectified = cv2.remap(
            right_img, self.right_map1, self.right_map2, cv2.INTER_LINEAR
        )
        
        return left_rectified, right_rectified
    
    def read_raw(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        读取原始图像（不进行校正）
        
        Returns:
            (left_img, right_img): 原始左右图像
        """
        if self.left_camera is None or self.right_camera is None:
            raise RuntimeError("相机未打开，请先调用 open() 方法")
        
        ret_left, left_img = self.left_camera.read()
        ret_right, right_img = self.right_camera.read()
        
        if not ret_left or not ret_right:
            return None, None
        
        return left_img, right_img
    
    def release(self):
        """释放相机资源"""
        if self.left_camera is not None:
            self.left_camera.release()
        if self.right_camera is not None:
            self.right_camera.release()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()

