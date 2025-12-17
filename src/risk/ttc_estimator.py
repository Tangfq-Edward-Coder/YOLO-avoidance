"""
TTC（碰撞时间）估算模块
基于连续帧的目标距离变化和自车速度计算碰撞时间
"""
from __future__ import annotations

from typing import Dict, Optional, List
import numpy as np
import time
from collections import deque


class TTCEstimator:
    """碰撞时间估算器"""
    
    def __init__(
        self,
        ego_speed: float = 0.0,
        history_size: int = 10,
        min_frames_for_ttc: int = 2
    ):
        """
        初始化TTC估算器
        
        Args:
            ego_speed: 自车速度（米/秒），如果为0则使用预设值或从传感器获取
            history_size: 历史记录大小
            min_frames_for_ttc: 计算TTC所需的最少帧数
        """
        self.ego_speed = ego_speed
        self.history_size = history_size
        self.min_frames_for_ttc = min_frames_for_ttc
        
        # 存储每个目标的历史信息
        # key: 目标ID或位置，value: deque of (timestamp, distance, position)
        self.object_history: Dict[str, deque] = {}
        
        # 默认自车速度（如果未提供）
        self.default_ego_speed = 5.0  # 米/秒（约18 km/h，校园环境）
    
    def update_ego_speed(self, speed: float):
        """
        更新自车速度
        
        Args:
            speed: 自车速度（米/秒）
        """
        self.ego_speed = speed
    
    def _generate_object_id(self, obj: Dict) -> str:
        """
        为对象生成唯一ID（基于位置和类别）
        
        Args:
            obj: 障碍物信息
        
        Returns:
            对象ID字符串
        """
        # 使用类别和位置生成ID
        obj_class = obj.get('class', 'unknown')
        bbox = obj.get('bbox', [0, 0, 0, 0])
        # 使用边界框中心作为位置标识
        center_x = (bbox[0] + bbox[2]) / 2 if len(bbox) >= 4 else 0
        center_y = (bbox[1] + bbox[3]) / 2 if len(bbox) >= 4 else 0
        
        # 简化：使用类别和大致位置
        return f"{obj_class}_{int(center_x//50)}_{int(center_y//50)}"
    
    def estimate_ttc(
        self,
        objects: List[Dict],
        current_time: Optional[float] = None
    ) -> List[Dict]:
        """
        估算所有目标的TTC
        
        Args:
            objects: 当前帧检测到的障碍物列表
            current_time: 当前时间戳（秒），如果为None则使用time.time()
        
        Returns:
            带TTC信息的障碍物列表
        """
        if current_time is None:
            current_time = time.time()
        
        # 使用自车速度（如果为0则使用默认值）
        ego_speed = self.ego_speed if self.ego_speed > 0 else self.default_ego_speed
        
        results = []
        
        for obj in objects:
            obj_id = self._generate_object_id(obj)
            distance = obj.get('depth', float('inf'))
            
            # 初始化历史记录
            if obj_id not in self.object_history:
                self.object_history[obj_id] = deque(maxlen=self.history_size)
            
            # 添加当前帧信息
            self.object_history[obj_id].append({
                'timestamp': current_time,
                'distance': distance,
                'position': obj.get('3d_position', [0, 0, 0])
            })
            
            # 计算TTC
            ttc = self._calculate_ttc(obj_id, ego_speed)
            
            # 添加TTC信息到对象
            obj_with_ttc = obj.copy()
            obj_with_ttc['ttc'] = ttc
            obj_with_ttc['ttc_valid'] = ttc is not None and ttc > 0
            
            results.append(obj_with_ttc)
        
        # 清理过期的历史记录（超过一定时间未更新的对象）
        self._cleanup_history(current_time)
        
        return results
    
    def _calculate_ttc(self, obj_id: str, ego_speed: float) -> Optional[float]:
        """
        计算单个目标的TTC
        
        Args:
            obj_id: 目标ID
            ego_speed: 自车速度（米/秒）
        
        Returns:
            TTC值（秒），如果无法计算则返回None
        """
        if obj_id not in self.object_history:
            return None
        
        history = self.object_history[obj_id]
        
        if len(history) < self.min_frames_for_ttc:
            return None
        
        # 获取最近的两帧数据
        recent = list(history)[-self.min_frames_for_ttc:]
        
        if len(recent) < 2:
            return None
        
        # 计算距离变化率
        dt = recent[-1]['timestamp'] - recent[0]['timestamp']
        if dt <= 0:
            return None
        
        dd = recent[-1]['distance'] - recent[0]['distance']
        relative_speed = -dd / dt  # 负号表示距离减小
        
        # 如果相对速度 <= 0，说明目标在远离或静止，TTC无效
        if relative_speed <= 0:
            return None
        
        # 计算TTC: TTC = distance / relative_speed
        current_distance = recent[-1]['distance']
        ttc = current_distance / relative_speed
        
        # 限制TTC范围（避免异常值）
        if ttc < 0 or ttc > 100:  # 最大100秒
            return None
        
        return float(ttc)
    
    def _cleanup_history(self, current_time: float, max_age: float = 2.0):
        """
        清理过期的历史记录
        
        Args:
            current_time: 当前时间戳
            max_age: 最大保留时间（秒）
        """
        expired_ids = []
        for obj_id, history in self.object_history.items():
            if len(history) > 0:
                oldest_time = history[0]['timestamp']
                if current_time - oldest_time > max_age:
                    expired_ids.append(obj_id)
        
        for obj_id in expired_ids:
            del self.object_history[obj_id]
    
    def get_nearest_object_ttc(self, objects_with_ttc: List[Dict]) -> Optional[Dict]:
        """
        获取最近障碍物的TTC
        
        Args:
            objects_with_ttc: 带TTC信息的障碍物列表
        
        Returns:
            最近障碍物的信息（包含TTC），如果没有则返回None
        """
        if not objects_with_ttc:
            return None
        
        # 找到距离最近且TTC有效的对象
        valid_objects = [obj for obj in objects_with_ttc if obj.get('ttc_valid', False)]
        
        if not valid_objects:
            return None
        
        nearest = min(valid_objects, key=lambda x: x.get('depth', float('inf')))
        return nearest
    
    def trigger_brake_alert(self, ttc_value: float, threshold: float = 3.0) -> bool:
        """
        判断是否需要触发紧急刹车警报
        
        Args:
            ttc_value: TTC值（秒）
            threshold: TTC阈值（秒）
        
        Returns:
            是否需要触发警报
        """
        return ttc_value is not None and ttc_value <= threshold

