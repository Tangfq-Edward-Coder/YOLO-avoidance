"""
道路风险预警模块
实现中长期风险（低能见度、路面湿滑）和短期风险（弯道、狭窄路段）判断
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, Optional
import yaml


class RoadRiskAssessor:
    """道路风险预警器"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化道路风险预警器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        risk_config = self.config.get('road_risk_assessment', {})
        
        # 中长期风险阈值
        self.low_visibility_brightness_threshold = risk_config.get('low_visibility_brightness_threshold', 80)
        self.low_visibility_contrast_threshold = risk_config.get('low_visibility_contrast_threshold', 30)
        self.wet_road_texture_threshold = risk_config.get('wet_road_texture_threshold', 0.3)
        
        # 短期风险阈值
        self.curve_curvature_threshold = risk_config.get('curve_curvature_threshold', 0.1)
        self.narrow_road_density_threshold = risk_config.get('narrow_road_density_threshold', 0.4)
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def assess_long_term_risks(self, image: np.ndarray) -> Dict[str, bool]:
        """
        评估中长期风险（低能见度、路面湿滑）
        
        Args:
            image: 输入图像（BGR格式）
        
        Returns:
            中长期风险标志位字典:
            {
                'low_visibility': bool,  # 低能见度
                'wet_road': bool         # 路面湿滑
            }
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. 低能见度判断：分析图像整体亮度和对比度
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)  # 对比度指标
        
        low_visibility = (
            mean_brightness < self.low_visibility_brightness_threshold or
            std_brightness < self.low_visibility_contrast_threshold
        )
        
        # 2. 路面湿滑判断：分析纹理特征
        # 使用LBP（Local Binary Pattern）或简单的梯度方差
        # 湿滑路面通常反射更强，纹理变化更平滑
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # 计算路面区域的纹理特征（假设路面在图像下半部分）
        h, w = gray.shape
        road_region = gradient_magnitude[h//2:, :]
        texture_variance = np.var(road_region)
        texture_mean = np.mean(road_region)
        
        # 归一化纹理特征
        normalized_texture = texture_variance / (texture_mean + 1e-6)
        
        wet_road = normalized_texture < self.wet_road_texture_threshold
        
        return {
            'low_visibility': bool(low_visibility),
            'wet_road': bool(wet_road)
        }
    
    def assess_short_term_risks(
        self,
        segmentation_mask: Optional[np.ndarray],
        detected_objects: list
    ) -> Dict[str, bool]:
        """
        评估短期风险（弯道、狭窄路段）
        
        Args:
            segmentation_mask: U-Net分割结果（像素级场景分割图）
            detected_objects: 检测到的障碍物列表
        
        Returns:
            短期风险标志位字典:
            {
                'curve': bool,      # 弯道
                'narrow_road': bool  # 狭窄路段
            }
        """
        curve = False
        narrow_road = False
        
        # 1. 弯道判断：基于场景分割结果的车道线曲率分析
        if segmentation_mask is not None:
            # 假设分割结果中，车道线类别为特定值（需要根据实际模型调整）
            # 这里简化处理：查找图像下半部分的边缘（车道线）
            h, w = segmentation_mask.shape[:2]
            road_region = segmentation_mask[h//2:, :]
            
            # 转换为灰度（如果是彩色）
            if len(road_region.shape) == 3:
                road_gray = cv2.cvtColor(road_region, cv2.COLOR_BGR2GRAY)
            else:
                road_gray = road_region
            
            # 边缘检测
            edges = cv2.Canny(road_gray, 50, 150)
            
            # 使用霍夫变换检测直线
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 0:
                # 计算车道线的平均角度
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    angles.append(angle)
                
                # 如果存在明显的角度变化（非直线），判断为弯道
                angle_variance = np.var(angles)
                if angle_variance > self.curve_curvature_threshold * 100:
                    curve = True
        
        # 2. 狭窄路段判断：基于目标密集度
        if len(detected_objects) > 0:
            # 计算检测框的总面积占图像面积的比例
            image_area = 640 * 480  # 假设图像尺寸
            total_bbox_area = 0
            
            for obj in detected_objects:
                if 'bbox' in obj:
                    x1, y1, x2, y2 = obj['bbox']
                    bbox_area = (x2 - x1) * (y2 - y1)
                    total_bbox_area += bbox_area
            
            density = total_bbox_area / image_area
            narrow_road = density > self.narrow_road_density_threshold
        
        return {
            'curve': bool(curve),
            'narrow_road': bool(narrow_road)
        }
    
    def assess_all_risks(
        self,
        image: np.ndarray,
        segmentation_mask: Optional[np.ndarray] = None,
        detected_objects: list = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        评估所有道路风险
        
        Args:
            image: 输入图像
            segmentation_mask: 场景分割结果（可选）
            detected_objects: 检测到的障碍物列表（可选）
        
        Returns:
            所有风险标志位:
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
        """
        if detected_objects is None:
            detected_objects = []
        
        long_term_risks = self.assess_long_term_risks(image)
        short_term_risks = self.assess_short_term_risks(segmentation_mask, detected_objects)
        
        return {
            'long_term': long_term_risks,
            'short_term': short_term_risks
        }

