"""
立体匹配模块
使用SGBM算法计算视差图
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, Optional
import yaml


class StereoMatcher:
    """立体匹配器，用于计算视差图"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化立体匹配器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        stereo_config = self.config['stereo_matching']
        
        # 创建SGBM匹配器
        self.stereo = cv2.StereoSGBM_create(
            minDisparity=stereo_config['min_disparity'],
            numDisparities=stereo_config['num_disparities'],
            blockSize=stereo_config['block_size'],
            P1=stereo_config['P1'],
            P2=stereo_config['P2'],
            disp12MaxDiff=stereo_config['disp12MaxDiff'],
            preFilterCap=stereo_config['preFilterCap'],
            uniquenessRatio=stereo_config['uniquenessRatio'],
            speckleWindowSize=stereo_config['speckleWindowSize'],
            speckleRange=stereo_config['speckleRange'],
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
        )
        
        # 相机参数
        self.camera_config = self.config['camera']
        self.baseline = self.camera_config['baseline']
        self.focal_length = self.camera_config['focal_length']
        
        # 处理Q矩阵，支持表达式字符串（如 "-1/0.12"）
        from src.utils.config_utils import parse_matrix
        Q_processed = parse_matrix(self.camera_config['stereo']['Q'])
        self.Q = np.array(Q_processed, dtype=np.float32)
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def compute_disparity(
        self,
        left_image: np.ndarray,
        right_image: np.ndarray
    ) -> np.ndarray:
        """
        计算视差图
        
        Args:
            left_image: 左图像（灰度图）
            right_image: 右图像（灰度图）
        
        Returns:
            视差图（16位整数）
        """
        # 确保输入是灰度图
        if len(left_image.shape) == 3:
            left_gray = cv2.cvtColor(left_image, cv2.COLOR_BGR2GRAY)
        else:
            left_gray = left_image
        
        if len(right_image.shape) == 3:
            right_gray = cv2.cvtColor(right_image, cv2.COLOR_BGR2GRAY)
        else:
            right_gray = right_image
        
        # 计算视差
        disparity = self.stereo.compute(left_gray, right_gray)
        
        return disparity
    
    def compute_depth_map(self, disparity: np.ndarray) -> np.ndarray:
        """
        将视差图转换为深度图
        
        Args:
            disparity: 视差图（16位整数）
        
        Returns:
            深度图（米，浮点数）
        """
        # 转换为浮点数并处理无效值
        disparity_float = disparity.astype(np.float32) / 16.0  # SGBM输出需要除以16
        disparity_float[disparity_float == 0] = np.nan
        
        # 计算深度：Z = (f * B) / d
        depth = (self.focal_length * self.baseline) / disparity_float
        
        return depth
    
    def compute_disparity_and_depth(
        self,
        left_image: np.ndarray,
        right_image: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        同时计算视差图和深度图
        
        Args:
            left_image: 左图像
            right_image: 右图像
        
        Returns:
            (disparity, depth): 视差图和深度图
        """
        disparity = self.compute_disparity(left_image, right_image)
        depth = self.compute_depth_map(disparity)
        
        return disparity, depth
    
    def get_depth_from_mask(
        self,
        depth_map: np.ndarray,
        mask: np.ndarray
    ) -> float:
        """
        从深度图中提取掩膜区域的深度值（使用中位数）
        
        Args:
            depth_map: 深度图
            mask: 二值掩膜（0或255）
        
        Returns:
            深度值（米）
        """
        # 将掩膜转换为布尔数组
        mask_bool = (mask > 128).astype(bool)
        
        # 提取掩膜区域的深度值
        depths = depth_map[mask_bool]
        depths = depths[~np.isnan(depths)]  # 移除NaN值
        depths = depths[depths > 0]  # 移除无效值
        
        if len(depths) == 0:
            return np.nan
        
        # 使用中位数作为代表值（更稳健）
        depth_value = np.median(depths)
        
        return float(depth_value)

