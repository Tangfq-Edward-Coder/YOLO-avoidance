"""
单目深度估计模块
用于Windows调试，基于检测框大小估计深度
"""
from __future__ import annotations

import numpy as np
import cv2
from typing import Tuple


class MonoDepthEstimator:
    """单目深度估计器（基于检测框大小）"""
    
    def __init__(
        self,
        reference_distance: float = 2.0,
        reference_size: float = 100.0,
        focal_length: float = 800.0
    ):
        """
        初始化单目深度估计器
        
        Args:
            reference_distance: 参考距离（米）
            reference_size: 参考尺寸（像素）
            focal_length: 焦距（像素）
        """
        self.reference_distance = reference_distance
        self.reference_size = reference_size
        self.focal_length = focal_length
    
    def estimate_depth_from_bbox(
        self,
        bbox: list,
        object_height_m: float = 1.7
    ) -> float:
        """
        基于边界框大小估计深度
        
        Args:
            bbox: 边界框 [x1, y1, x2, y2]
            object_height_m: 对象实际高度（米），默认1.7米（人）
        
        Returns:
            估计的深度值（米）
        """
        x1, y1, x2, y2 = bbox
        bbox_height = y2 - y1
        
        if bbox_height <= 0:
            return np.nan
        
        # 使用相似三角形原理：depth = (focal_length * real_height) / pixel_height
        depth = (self.focal_length * object_height_m) / bbox_height
        
        return float(depth)
    
    def create_depth_map(
        self,
        image_shape: Tuple[int, int],
        detections: list,
        default_depth: float = 5.0
    ) -> np.ndarray:
        """
        创建深度图（基于检测结果）
        
        Args:
            image_shape: 图像尺寸 (height, width)
            detections: 检测结果列表
            default_depth: 默认深度值（米）
        
        Returns:
            深度图
        """
        depth_map = np.full(image_shape, default_depth, dtype=np.float32)
        
        for det in detections:
            bbox = det['bbox']
            depth = self.estimate_depth_from_bbox(bbox)
            
            if not np.isnan(depth) and depth > 0:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(image_shape[1], x2)
                y2 = min(image_shape[0], y2)
                
                # 在边界框区域内填充深度值
                depth_map[y1:y2, x1:x2] = depth
        
        return depth_map
    
    def compute_disparity_and_depth(
        self,
        left_image: np.ndarray,
        right_image: np.ndarray,
        detections: list
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算视差图和深度图（单目模式）
        
        Args:
            left_image: 左图像（实际是单目图像）
            right_image: 右图像（实际是单目图像）
            detections: 检测结果列表
        
        Returns:
            (disparity, depth): 视差图和深度图
        """
        h, w = left_image.shape[:2]
        
        # 创建深度图
        depth_map = self.create_depth_map((h, w), detections)
        
        # 创建假的视差图（用于兼容性）
        # 视差 = (focal_length * baseline) / depth
        baseline = 0.12  # 假设基线距离
        disparity_map = np.zeros((h, w), dtype=np.float32)
        valid_mask = depth_map > 0
        disparity_map[valid_mask] = (self.focal_length * baseline) / depth_map[valid_mask]
        disparity_map = (disparity_map * 16).astype(np.uint16)  # 转换为16位整数格式
        
        return disparity_map, depth_map

