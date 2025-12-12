"""
信息融合模块
融合检测、分割和深度信息，计算3D坐标
"""
from __future__ import annotations

import numpy as np
from typing import List, Dict, Tuple, Optional
import cv2
import yaml


class InfoFusion:
    """信息融合器，融合检测、分割和深度信息"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化信息融合器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.camera_config = self.config['camera']
        
        # 相机内参
        self.camera_matrix = np.array(
            self.camera_config['left_camera_matrix'], dtype=np.float32
        )
        
        # 处理Q矩阵，支持表达式字符串（如 "-1/0.12"）
        from src.utils.config_utils import parse_matrix
        Q_processed = parse_matrix(self.camera_config['stereo']['Q'])
        self.Q = np.array(Q_processed, dtype=np.float32)
        
        # 图像尺寸
        self.image_width = self.camera_config['image_width']
        self.image_height = self.camera_config['image_height']
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def fuse_detection_and_depth(
        self,
        detections: List[Dict],
        segmentation_masks: List[np.ndarray],
        depth_map: np.ndarray
    ) -> List[Dict]:
        """
        融合检测、分割和深度信息
        
        Args:
            detections: YOLO检测结果列表
            segmentation_masks: 对应的分割掩膜列表
            depth_map: 深度图
        
        Returns:
            融合后的障碍物信息列表，每个元素包含:
            {
                'bbox': [x1, y1, x2, y2],
                'mask': np.ndarray,
                'depth': float,
                '3d_position': [x, y, z],
                'confidence': float,
                'class_id': int,
                'class_name': str
            }
        """
        fused_objects = []
        
        for i, detection in enumerate(detections):
            # 获取对应的分割掩膜
            if i < len(segmentation_masks):
                mask = segmentation_masks[i]
            else:
                # 如果没有分割掩膜，使用bbox创建简单掩膜
                x1, y1, x2, y2 = [int(v) for v in detection['bbox']]
                mask = np.zeros((self.image_height, self.image_width), dtype=np.uint8)
                mask[y1:y2, x1:x2] = 255
            
            # 从深度图中提取深度值
            depth = self._extract_depth_from_mask(depth_map, mask)
            
            if np.isnan(depth) or depth <= 0:
                continue  # 跳过无效深度
            
            # 计算3D位置（使用bbox中心点）
            x1, y1, x2, y2 = [int(v) for v in detection['bbox']]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # 获取中心点的深度
            center_depth = depth_map[center_y, center_x]
            if np.isnan(center_depth) or center_depth <= 0:
                center_depth = depth
            
            # 计算3D坐标（相机坐标系）
            x3d, y3d, z3d = self._pixel_to_3d(center_x, center_y, center_depth)
            
            fused_objects.append({
                'bbox': detection['bbox'],
                'mask': mask,
                'depth': float(depth),
                '3d_position': [float(x3d), float(y3d), float(z3d)],
                'confidence': detection['confidence'],
                'class_id': detection['class_id'],
                'class_name': detection['class_name']
            })
        
        return fused_objects
    
    def _extract_depth_from_mask(
        self,
        depth_map: np.ndarray,
        mask: np.ndarray
    ) -> float:
        """
        从深度图中提取掩膜区域的深度值
        
        Args:
            depth_map: 深度图
            mask: 二值掩膜
        
        Returns:
            深度值（米）
        """
        # 将掩膜转换为布尔数组
        mask_bool = (mask > 128).astype(bool)
        
        # 提取掩膜区域的深度值
        depths = depth_map[mask_bool]
        depths = depths[~np.isnan(depths)]
        depths = depths[depths > 0]
        
        if len(depths) == 0:
            return np.nan
        
        # 使用中位数
        depth_value = np.median(depths)
        
        return float(depth_value)
    
    def _pixel_to_3d(
        self,
        u: int,
        v: int,
        depth: float
    ) -> Tuple[float, float, float]:
        """
        将像素坐标和深度转换为3D坐标（相机坐标系）
        
        Args:
            u: 像素x坐标
            v: 像素y坐标
            depth: 深度值（米）
        
        Returns:
            (x, y, z): 3D坐标（米）
        """
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
        
        # 相机坐标系：x向右，y向下，z向前
        x = (u - cx) * depth / fx
        y = (v - cy) * depth / fy
        z = depth
        
        return x, y, z
    
    def filter_by_depth(
        self,
        objects: List[Dict],
        min_depth: float = 0.1,
        max_depth: float = 10.0
    ) -> List[Dict]:
        """
        根据深度范围过滤障碍物
        
        Args:
            objects: 障碍物列表
            min_depth: 最小深度（米）
            max_depth: 最大深度（米）
        
        Returns:
            过滤后的障碍物列表
        """
        filtered = [
            obj for obj in objects
            if min_depth <= obj['depth'] <= max_depth
        ]
        return filtered

