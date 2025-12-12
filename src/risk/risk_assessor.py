"""
碰撞风险评估模块
根据障碍物距离和位置评估碰撞风险
"""
from __future__ import annotations

from typing import List, Dict
import numpy as np
import yaml


class RiskAssessor:
    """碰撞风险评估器"""
    
    def __init__(self, config_path: str = "configs/system_config.yaml"):
        """
        初始化风险评估器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        risk_config = self.config['risk_assessment']
        
        # 距离阈值
        self.safe_distance = risk_config['safe_distance']
        self.warning_distance = risk_config['warning_distance']
        self.danger_distance = risk_config['danger_distance']
        self.brake_distance = risk_config['brake_distance']
        
        # 风险阈值
        self.risk_threshold = risk_config['risk_threshold']
        
        # 车辆参数（假设）
        self.ego_width = 1.8  # 米
        self.ego_length = 4.5  # 米
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def assess_risk(self, objects: List[Dict]) -> Dict:
        """
        评估碰撞风险
        
        Args:
            objects: 障碍物列表，每个元素包含 'depth', '3d_position' 等信息
        
        Returns:
            风险评估结果:
            {
                'risk_level': 'safe' | 'warning' | 'danger',
                'risk_score': float (0-1),
                'nearest_object': Dict | None,
                'should_brake': bool
            }
        """
        if not objects:
            return {
                'risk_level': 'safe',
                'risk_score': 0.0,
                'nearest_object': None,
                'should_brake': False
            }
        
        # 找到最近的障碍物
        nearest_obj = min(objects, key=lambda x: x['depth'])
        nearest_distance = nearest_obj['depth']
        
        # 计算风险等级
        if nearest_distance <= self.danger_distance:
            risk_level = 'danger'
            risk_score = 1.0 - (nearest_distance / self.danger_distance) * 0.5
        elif nearest_distance <= self.warning_distance:
            risk_level = 'warning'
            risk_score = 0.5 + (self.warning_distance - nearest_distance) / (
                self.warning_distance - self.danger_distance
            ) * 0.3
        elif nearest_distance <= self.safe_distance:
            risk_level = 'warning'
            risk_score = 0.2 + (self.safe_distance - nearest_distance) / (
                self.safe_distance - self.warning_distance
            ) * 0.3
        else:
            risk_level = 'safe'
            risk_score = max(0.0, 0.2 - (nearest_distance - self.safe_distance) * 0.01)
        
        risk_score = np.clip(risk_score, 0.0, 1.0)
        
        # 判断是否需要刹车
        should_brake = (
            nearest_distance <= self.brake_distance or
            risk_score >= self.risk_threshold
        )
        
        return {
            'risk_level': risk_level,
            'risk_score': float(risk_score),
            'nearest_object': nearest_obj,
            'should_brake': should_brake
        }
    
    def assess_object_risk(self, obj: Dict) -> Dict:
        """
        评估单个障碍物的风险
        
        Args:
            obj: 障碍物信息
        
        Returns:
            单个障碍物的风险评估:
            {
                'risk_level': 'safe' | 'warning' | 'danger',
                'risk_score': float (0-1)
            }
        """
        distance = obj['depth']
        
        if distance <= self.danger_distance:
            risk_level = 'danger'
            risk_score = 1.0 - (distance / self.danger_distance) * 0.5
        elif distance <= self.warning_distance:
            risk_level = 'warning'
            risk_score = 0.5 + (self.warning_distance - distance) / (
                self.warning_distance - self.danger_distance
            ) * 0.3
        elif distance <= self.safe_distance:
            risk_level = 'warning'
            risk_score = 0.2 + (self.safe_distance - distance) / (
                self.safe_distance - self.warning_distance
            ) * 0.3
        else:
            risk_level = 'safe'
            risk_score = max(0.0, 0.2 - (distance - self.safe_distance) * 0.01)
        
        risk_score = np.clip(risk_score, 0.0, 1.0)
        
        return {
            'risk_level': risk_level,
            'risk_score': float(risk_score)
        }

